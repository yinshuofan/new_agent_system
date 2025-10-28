"""
使用框架的自主运行系统
充分利用框架的核心功能：
- Agent.process_tick() 周期更新
- CognitionModule.make_decision() 决策
- BehaviorModule.execute_action() 执行工具
- EventBus 事件系统
- 完整的6大模块协同
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent, AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType, get_llm_client
from agent_system.tools.base_tools import BaseTool, ToolResult


# 定义剧情相关的工具
class InvestigateSceneTool(BaseTool):
    """检查现场工具"""
    def __init__(self):
        super().__init__(
            name="investigate_scene",
            description="检查案发现场，寻找线索",
            
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            result={"action": "检查现场", "finding": "发现了可疑的脚印和纤维"},
            result={"message": "仔细检查了现场，发现了一些可疑痕迹"
        )


class InterviewWitnessTool(BaseTool):
    """询问证人工具"""
    def __init__(self):
        super().__init__(
            name="interview_witness",
            description="询问目击证人",
            
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            result={"action": "询问证人", "testimony": "证人提供了关键线索"},
            result={"message": "询问了在场证人，获得了有价值的信息"
        )


class AnalyzeEvidenceTool(BaseTool):
    """分析证据工具"""
    def __init__(self):
        super().__init__(
            name="analyze_evidence",
            description="分析收集到的证据",
            
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            result={"action": "分析证据", "conclusion": "证据指向特定嫌疑人"},
            result={"message": "对证据进行了详细分析，得出了初步结论"
        )


class RecordFindingsTool(BaseTool):
    """记录发现工具"""
    def __init__(self):
        super().__init__(
            name="record_findings",
            description="记录调查发现",
            
        )

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            result={"action": "记录发现", "notes": "详细记录了所有线索"},
            result={"message": "认真记录了所有重要发现"
        )


class FrameworkAutonomousSystem:
    """使用框架的自主运行系统"""

    def __init__(self):
        self.manager = None
        self.story_engine = None
        self.agents: Dict[str, Agent] = {}
        self.llm_client = None
        self.use_llm = False
        self.running = False
        self.tick_interval = 5  # 5秒一次tick
        self.action_count = 0

    def load_config(self):
        """加载配置"""
        config_path = Path(__file__).parent.parent / "config" / "llm_config.yaml"
        if not config_path.exists():
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        active = config.get('active', 'doubao')
        cfg = config.get(active)
        if not cfg:
            return None

        return LLMConfig(
            api_key=cfg['api_key'],
            base_url=cfg.get('base_url'),
            model_mapping={
                ModelType.FAST: cfg['models']['fast'],
                ModelType.ACCURATE: cfg['models']['accurate'],
                ModelType.REASONING: cfg['models']['reasoning']
            },
            max_connections=cfg.get('max_connections', 5),
            timeout=cfg.get('timeout', 60.0)
        )

    async def initialize(self):
        """初始化系统"""
        print("=" * 70)
        print("🎭 使用框架的自主运行系统")
        print("=" * 70)
        print()

        # 初始化LLM
        config = self.load_config()
        if config:
            try:
                await initialize_llm(config)
                self.llm_client = get_llm_client()
                self.use_llm = True
                print("✓ LLM初始化成功")
            except Exception as e:
                print(f"⚠️  LLM初始化失败: {e}")
                self.use_llm = False
        print()

        # 创建组件
        self.story_engine = StoryEngine(StoryMode.GUIDED, self.use_llm)
        await self.story_engine.initialize()
        self.manager = AgentManager()

    async def create_story_and_agents(self):
        """创建剧情和智能体"""
        print("📖 创建剧情和角色...")

        # 生成剧情
        theme = "悬疑推理：伦敦盗窃案"
        plot_points = [
            "案发：珍贵珠宝在豪宅中被盗",
            "调查：侦探开始调查现场",
            "线索：发现关键证据",
            "推理：分析并锁定嫌疑人",
            "真相：揭露真凶"
        ]

        characters = [
            {"agent_id": "holmes", "name": "福尔摩斯", "role": "侦探"},
            {"agent_id": "watson", "name": "华生", "role": "助手"}
        ]

        story = await self.story_engine.generate_story(
            theme=theme,
            agent_characters=characters,
            custom_plot=plot_points
        )

        # 创建智能体并注册工具
        for char in characters:
            agent = await self.manager.create_agent(
                agent_id=char["agent_id"],
                name=char["name"],
                config={
                    "role": char["role"],
                    "story_context": story.plot_points[0]
                },
                use_llm=self.use_llm
            )

            # 注册工具到BehaviorModule
            if char["agent_id"] == "holmes":
                agent.behavior.register_tool(InvestigateSceneTool())
                agent.behavior.register_tool(InterviewWitnessTool())
                agent.behavior.register_tool(AnalyzeEvidenceTool())
            else:  # watson
                agent.behavior.register_tool(RecordFindingsTool())
                agent.behavior.register_tool(InterviewWitnessTool())

            # 添加初始目标
            await agent.add_goal({
                "title": f"协助调查{theme}",
                "description": story.plot_points[0],
                "priority": 3
            })

            self.agents[char["agent_id"]] = agent

        print(f"✓ 剧情《{story.title}》已创建")
        print(f"✓ 角色和工具已注册")
        print()

    async def agent_autonomous_tick(self, agent_id: str):
        """智能体自主tick - 使用框架的process_tick"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]

        # 1. 调用框架的process_tick - 更新所有模块
        await agent.process_tick()

        # 2. 让认知模块做决策 - 使用框架的make_decision
        story = self.story_engine.get_current_story()
        current_plot = self.story_engine.get_current_plot_point()

        # 获取可用工具
        available_tools = list(agent.behavior._tools.keys())

        decision_context = {
            "situation": f"当前剧情：{current_plot}。你需要采取行动推进调查。",
            "options": [{"type": "use_tool", "tool": tool} for tool in available_tools],
            "story_context": current_plot
        }

        # 使用框架的决策系统
        decision = await agent.cognition.make_decision(decision_context)

        # 3. 执行决策 - 使用框架的execute_action
        if decision.get("action"):
            action = decision["action"]

            # 如果决策是使用工具
            if "tool" in action or available_tools:
                # 选择一个工具执行
                import random
                tool_name = action.get("tool", random.choice(available_tools))

                # 使用框架的BehaviorModule执行工具
                result = await agent.behavior.execute_action({
                    "tool_name": tool_name,
                    "parameters": {}
                })

                if result.get("success"):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🎬 {agent.name}: {result.get('message', tool_name)}")

                    # 存储行动记忆 - 使用框架的记忆系统
                    await agent.memory.store("event", {
                        "event_summary": f"{agent.name}的行动",
                        "event_details": result.get("message", ""),
                        "participants": [agent_id],
                        "importance": 0.7
                    })

                    self.action_count += 1

        # 4. 检查是否推进剧情
        if self.action_count >= 4:
            await self.advance_story()
            self.action_count = 0

    async def advance_story(self):
        """推进剧情"""
        if self.story_engine.advance_plot():
            plot = self.story_engine.get_current_plot_point()
            print("\n" + "=" * 70)
            print(f"📖 剧情推进！")
            print(f"▶ {plot}")
            print("=" * 70 + "\n")

            # 更新所有智能体的上下文
            for agent in self.agents.values():
                agent.config["story_context"] = plot
                # 更新目标
                goals = agent.goal.get_active_goals()
                if goals:
                    await agent.goal.update_goal(goals[0].goal_id, {"description": plot})

    async def chat_with_agent(self, agent_id: str, message: str):
        """与智能体对话"""
        if agent_id not in self.agents:
            print(f"❌ 未知角色: {agent_id}")
            return

        agent = self.agents[agent_id]

        # 使用框架的receive_message
        response = await agent.receive_message(
            sender_id="user",
            result={"message": message,
            metaresult={}
        )

        print(f"💬 你 → {agent.name}: {message}")
        print(f"🎭 {agent.name}: {response.get('response', '...')}")
        print()

    async def autonomous_loop(self):
        """自主运行循环 - 使用框架的tick机制"""
        agent_ids = list(self.agents.keys())
        agent_index = 0

        while self.running:
            # 轮流tick每个智能体
            agent_id = agent_ids[agent_index]
            await self.agent_autonomous_tick(agent_id)

            agent_index = (agent_index + 1) % len(agent_ids)
            await asyncio.sleep(self.tick_interval)

    async def input_loop(self):
        """用户输入循环"""
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                user_input = await loop.run_in_executor(None, input, "> ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\n👋 退出\n")
                    self.running = False
                    break
                elif user_input.startswith("@"):
                    parts = user_input[1:].split(maxsplit=1)
                    if len(parts) == 2:
                        await self.chat_with_agent(parts[0], parts[1])
                else:
                    await self.chat_with_agent("holmes", user_input)

            except (EOFError, KeyboardInterrupt):
                break

    async def run(self):
        """运行系统"""
        await self.initialize()
        await self.create_story_and_agents()

        print("=" * 70)
        print("🎮 系统启动 - 使用框架核心功能")
        print("=" * 70)
        print("✓ Agent.process_tick() - 周期更新")
        print("✓ CognitionModule.make_decision() - 智能决策")
        print("✓ BehaviorModule.execute_action() - 执行工具")
        print("✓ MemoryModule.store() - 存储记忆")
        print("✓ EventBus - 事件驱动")
        print("=" * 70)
        print()

        self.running = True

        # 并发运行
        autonomous_task = asyncio.create_task(self.autonomous_loop())
        input_task = asyncio.create_task(self.input_loop())

        done, pending = await asyncio.wait(
            [autonomous_task, input_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # 清理
        for agent in self.agents.values():
            await agent.stop()


async def main():
    system = FrameworkAutonomousSystem()
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
