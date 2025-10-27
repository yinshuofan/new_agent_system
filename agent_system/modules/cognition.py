"""
认知模块 - 核心决策和思考逻辑
作为智能体的"大脑"，整合所有模块信息进行决策
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from agent_system.core.base import CognitionInterface
from agent_system.core.event_bus import EventBus, EventType
from agent_system.llm import get_llm_client, ModelType
from agent_system.llm.prompt_manager import get_prompt_manager


class CognitionModule(CognitionInterface):
    """
    认知模块实现
    整合感知、记忆、情感、目标等信息进行决策
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        decision_strategy: Optional[Callable] = None,
        use_llm: bool = True
    ):
        super().__init__(agent_id, event_bus)
        # LLM配置
        self._use_llm = use_llm
        self._llm_client = None
        self._prompt_manager = None

        # 决策策略（可注入自定义策略，如LLM决策）
        if decision_strategy:
            self._decision_strategy = decision_strategy
        elif use_llm:
            self._decision_strategy = self._llm_decision_strategy
        else:
            self._decision_strategy = self._default_decision_strategy

        # 认知状态（相当于"提示词/内存"）
        self._cognitive_state: Dict[str, Any] = {}
        # 决策历史
        self._decision_history: List[Dict[str, Any]] = []
        self._max_history = 50
        # 反思配置
        self._reflection_enabled = True
        self._reflection_interval = 10  # 每10次决策进行一次反思

    async def initialize(self) -> None:
        """初始化认知模块"""
        self._initialized = True

        # 初始化LLM客户端
        if self._use_llm:
            self._llm_client = get_llm_client()
            self._prompt_manager = get_prompt_manager()

        # 初始化认知状态
        self._cognitive_state = {
            "identity": {
                "agent_id": self.agent_id,
                "role": "general_agent",
                "personality": {}
            },
            "current_context": {
                "perception": {},
                "emotion": {},
                "active_goals": [],
                "recent_memories": []
            },
            "reasoning_trace": [],
            "last_reflection": None
        }

        # 订阅相关事件以更新认知状态
        self.subscribe_event(EventType.PERCEPTION_UPDATED, self._on_perception_updated)
        self.subscribe_event(EventType.EMOTION_CHANGED, self._on_emotion_changed)
        self.subscribe_event(EventType.GOAL_UPDATED, self._on_goal_updated)
        self.subscribe_event(EventType.MEMORY_RETRIEVED, self._on_memory_retrieved)

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新认知模块

        Args:
            context: 上下文信息
        """
        self._mark_updated()

        # 更新认知状态
        if "perception" in context:
            self._cognitive_state["current_context"]["perception"] = context["perception"]

        if "emotion" in context:
            self._cognitive_state["current_context"]["emotion"] = context["emotion"]

        if "goals" in context:
            self._cognitive_state["current_context"]["active_goals"] = context["goals"]

        # 定期反思
        if self._reflection_enabled:
            if len(self._decision_history) % self._reflection_interval == 0:
                await self.reflect()

    def get_state(self) -> Dict[str, Any]:
        """获取认知模块状态"""
        return {
            "cognitive_state": self._cognitive_state,
            "decision_count": len(self._decision_history),
            "last_reflection": self._cognitive_state.get("last_reflection"),
            "last_update": self._last_update.isoformat()
        }

    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出决策

        Args:
            context: 决策上下文
                - situation: 当前情况描述
                - options: 可选行为列表（可选）
                - urgency: 紧急程度（可选）

        Returns:
            决策结果
                - action: 决定的行为
                - reasoning: 推理过程
                - confidence: 置信度
        """
        # 收集所有相关信息
        decision_context = self._build_decision_context(context)

        # 使用决策策略
        decision = await self._decision_strategy(decision_context, self)

        # 记录决策
        decision_record = {
            "context": context,
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        }
        self._decision_history.append(decision_record)
        if len(self._decision_history) > self._max_history:
            self._decision_history.pop(0)

        # 更新推理轨迹
        if "reasoning" in decision:
            self._cognitive_state["reasoning_trace"].append({
                "timestamp": datetime.now().isoformat(),
                "reasoning": decision["reasoning"]
            })
            # 保留最近的推理
            if len(self._cognitive_state["reasoning_trace"]) > 10:
                self._cognitive_state["reasoning_trace"].pop(0)

        # 发送决策事件
        await self.emit_event(
            EventType.DECISION_MADE,
            {
                "decision": decision,
                "context_summary": context.get("situation", "")
            }
        )

        return decision

    async def decide(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出决策（make_decision的别名，提供更简洁的接口）

        Args:
            context: 决策上下文

        Returns:
            决策结果
        """
        return await self.make_decision(context)

    async def reflect(self) -> Dict[str, Any]:
        """
        自我反思
        分析最近的行为和决策，提取经验教训

        Returns:
            反思结果
        """
        # 收集反思材料
        recent_decisions = self._decision_history[-self._reflection_interval:]
        current_state = self._cognitive_state["current_context"]

        # 构建反思上下文
        reflection_context = {
            "recent_decisions": recent_decisions,
            "current_emotion": current_state.get("emotion", {}),
            "active_goals": current_state.get("active_goals", []),
            "decision_count": len(self._decision_history)
        }

        # 执行反思（这里是简化版，实际可以使用LLM）
        reflection_result = await self._perform_reflection(reflection_context)

        # 更新认知状态
        self._cognitive_state["last_reflection"] = {
            "timestamp": datetime.now().isoformat(),
            "insights": reflection_result.get("insights", []),
            "adjustments": reflection_result.get("adjustments", [])
        }

        # 发送反思事件
        await self.emit_event(
            EventType.REFLECTION_COMPLETED,
            {
                "reflection": reflection_result,
                "decisions_analyzed": len(recent_decisions)
            }
        )

        return reflection_result

    def set_decision_strategy(self, strategy: Callable) -> None:
        """
        设置决策策略

        Args:
            strategy: 决策策略函数
        """
        self._decision_strategy = strategy

    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取决策历史

        Args:
            limit: 返回数量限制

        Returns:
            决策历史列表
        """
        return self._decision_history[-limit:]

    def get_cognitive_state(self) -> Dict[str, Any]:
        """获取完整的认知状态"""
        return self._cognitive_state.copy()

    def update_identity(self, identity_updates: Dict[str, Any]) -> None:
        """
        更新身份信息

        Args:
            identity_updates: 身份更新
        """
        self._cognitive_state["identity"].update(identity_updates)

    # 私有方法

    def _build_decision_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建完整的决策上下文

        Args:
            context: 输入上下文

        Returns:
            完整的决策上下文
        """
        return {
            # 当前情况
            "situation": context.get("situation", ""),
            "options": context.get("options", []),
            "urgency": context.get("urgency", 0.5),

            # 内部状态
            "identity": self._cognitive_state["identity"],
            "current_perception": self._cognitive_state["current_context"]["perception"],
            "current_emotion": self._cognitive_state["current_context"]["emotion"],
            "active_goals": self._cognitive_state["current_context"]["active_goals"],
            "recent_memories": self._cognitive_state["current_context"]["recent_memories"],

            # 历史
            "recent_decisions": self._decision_history[-5:],
            "reasoning_trace": self._cognitive_state["reasoning_trace"][-3:]
        }

    async def _default_decision_strategy(
        self,
        context: Dict[str, Any],
        cognition_module: 'CognitionModule'
    ) -> Dict[str, Any]:
        """
        默认决策策略（简单的规则基础决策）

        Args:
            context: 决策上下文
            cognition_module: 认知模块实例

        Returns:
            决策结果
        """
        # 简化的决策逻辑
        options = context.get("options", [])
        active_goals = context.get("active_goals", [])
        emotion = context.get("current_emotion", {})

        # 如果有可选项，选择第一个
        if options:
            selected_action = options[0]
        else:
            # 如果有活跃目标，朝目标努力
            if active_goals:
                selected_action = {
                    "type": "work_on_goal",
                    "goal_id": active_goals[0].get("goal_id")
                }
            else:
                # 默认行为：观察和等待
                selected_action = {
                    "type": "observe",
                    "parameters": {}
                }

        return {
            "action": selected_action,
            "reasoning": "Default rule-based decision",
            "confidence": 0.6
        }

    async def _perform_reflection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行反思

        Args:
            context: 反思上下文

        Returns:
            反思结果
        """
        # 如果使用LLM，调用LLM反思
        if self._use_llm and self._llm_client:
            return await self._llm_reflection(context)

        # 简化的反思逻辑
        recent_decisions = context.get("recent_decisions", [])
        current_emotion = context.get("current_emotion", {})

        insights = []
        adjustments = []

        # 分析决策成功率
        successful_decisions = sum(
            1 for d in recent_decisions
            if d.get("decision", {}).get("confidence", 0) > 0.7
        )
        success_rate = successful_decisions / len(recent_decisions) if recent_decisions else 0

        if success_rate < 0.5:
            insights.append("Recent decision quality is low, need to improve decision making")
            adjustments.append("Consider gathering more information before deciding")

        # 分析情感状态
        valence = current_emotion.get("valence", 0)
        if valence < -0.5:
            insights.append("Current emotional state is negative")
            adjustments.append("Focus on goals that can improve mood")

        return {
            "insights": insights,
            "adjustments": adjustments,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        }

    async def _llm_decision_strategy(
        self,
        context: Dict[str, Any],
        cognition_module: 'CognitionModule'
    ) -> Dict[str, Any]:
        """
        LLM决策策略

        Args:
            context: 决策上下文
            cognition_module: 认知模块实例

        Returns:
            决策结果
        """
        if not self._llm_client:
            return await self._default_decision_strategy(context, cognition_module)

        try:
            # 构建提示词
            system_prompt = self._prompt_manager.get_prompt("cognition", "system")

            # 格式化上下文
            situation = context.get("situation", "")
            emotion = str(context.get("current_emotion", {}))
            goals = str(context.get("active_goals", []))[:500]  # 限制长度
            memories = str(context.get("recent_memories", []))[:500]

            user_prompt = self._prompt_manager.get_prompt(
                "cognition",
                "make_decision",
                situation=situation,
                emotion=emotion,
                goals=goals,
                memories=memories
            )

            # 调用LLM
            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.7
            )

            # 解析响应
            if "parse_error" not in response:
                return {
                    "action": response.get("action", {"type": "observe"}),
                    "reasoning": response.get("reasoning", "LLM decision"),
                    "confidence": float(response.get("confidence", 0.7))
                }
            else:
                # 解析失败，使用默认策略
                return await self._default_decision_strategy(context, cognition_module)

        except Exception as e:
            print(f"LLM decision error: {e}")
            return await self._default_decision_strategy(context, cognition_module)

    async def _llm_reflection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM反思

        Args:
            context: 反思上下文

        Returns:
            反思结果
        """
        try:
            # 构建提示词
            system_prompt = self._prompt_manager.get_prompt("cognition", "system")

            recent_decisions = str(context.get("recent_decisions", []))[:1000]
            current_state = str(context)[:1000]

            user_prompt = self._prompt_manager.get_prompt(
                "cognition",
                "reflect",
                recent_decisions=recent_decisions,
                current_state=current_state
            )

            # 调用LLM
            response = await self._llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_type=ModelType.FAST,
                temperature=0.7
            )

            # 解析响应
            if "parse_error" not in response:
                return {
                    "insights": response.get("insights", []),
                    "adjustments": response.get("adjustments", []),
                    "success_rate": float(response.get("success_rate", 0.5)),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 解析失败，使用默认反思
                return await self._perform_reflection(context)

        except Exception as e:
            print(f"LLM reflection error: {e}")
            # 回退到默认反思
            recent_decisions = context.get("recent_decisions", [])
            return {
                "insights": ["LLM reflection failed, using fallback"],
                "adjustments": [],
                "success_rate": 0.5,
                "timestamp": datetime.now().isoformat()
            }

    # 事件处理器

    async def _on_perception_updated(self, event) -> None:
        """感知更新事件处理"""
        perception_data = event.data.get("perception", {})
        self._cognitive_state["current_context"]["perception"] = perception_data

    async def _on_emotion_changed(self, event) -> None:
        """情感变化事件处理"""
        emotion_data = event.data.get("emotion", {})
        self._cognitive_state["current_context"]["emotion"] = emotion_data

    async def _on_goal_updated(self, event) -> None:
        """目标更新事件处理"""
        # 可以在这里更新活跃目标列表
        pass

    async def _on_memory_retrieved(self, event) -> None:
        """记忆检索事件处理"""
        # 可以将检索到的记忆加入当前上下文
        pass
