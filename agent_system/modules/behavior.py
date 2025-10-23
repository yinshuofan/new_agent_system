"""
行为模块 - 工具执行和行为管理
使用命令模式管理工具集合
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from agent_system.core.base import BehaviorInterface
from agent_system.core.event_bus import EventBus, EventType
from agent_system.tools.base_tools import BaseTool, ToolResult


class BehaviorModule(BehaviorInterface):
    """
    行为模块实现
    管理工具注册、执行和行为历史
    """

    def __init__(self, agent_id: str, event_bus: EventBus):
        super().__init__(agent_id, event_bus)
        # 工具注册表
        self._tools: Dict[str, BaseTool] = {}
        # 行为历史
        self._action_history: List[Dict[str, Any]] = []
        self._max_history = 100
        # 执行策略
        self._retry_enabled = True
        self._max_retries = 3

    async def initialize(self) -> None:
        """初始化行为模块"""
        self._initialized = True

    async def update(self, context: Dict[str, Any]) -> None:
        """
        更新行为模块

        Args:
            context: 上下文信息
        """
        self._mark_updated()
        # 可以在这里实现行为统计分析等

    def get_state(self) -> Dict[str, Any]:
        """获取行为模块状态"""
        return {
            "registered_tools": list(self._tools.keys()),
            "tool_count": len(self._tools),
            "action_history_count": len(self._action_history),
            "last_update": self._last_update.isoformat()
        }

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行行为

        Args:
            action: 行为描述
                - tool_name: 工具名称
                - parameters: 工具参数
                - retry: 是否重试（可选）

        Returns:
            执行结果
        """
        tool_name = action.get("tool_name")
        parameters = action.get("parameters", {})
        retry = action.get("retry", self._retry_enabled)

        if not tool_name:
            return {
                "success": False,
                "error": "Missing tool_name in action"
            }

        if tool_name not in self._tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }

        # 执行工具（带重试）
        tool = self._tools[tool_name]
        result = await self._execute_tool_with_retry(
            tool,
            parameters,
            retry,
            self._max_retries
        )

        # 记录行为历史
        action_record = {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        self._action_history.append(action_record)
        if len(self._action_history) > self._max_history:
            self._action_history.pop(0)

        # 发送事件
        if result.success:
            await self.emit_event(
                EventType.ACTION_EXECUTED,
                {
                    "tool_name": tool_name,
                    "success": True,
                    "execution_time": result.execution_time
                }
            )
        else:
            await self.emit_event(
                EventType.ACTION_FAILED,
                {
                    "tool_name": tool_name,
                    "error": result.error,
                    "parameters": parameters
                }
            )

        return result.model_dump()

    def register_tool(self, tool_name: str, tool_func: BaseTool) -> None:
        """
        注册工具

        Args:
            tool_name: 工具名称
            tool_func: 工具对象（BaseTool实例）
        """
        if not isinstance(tool_func, BaseTool):
            raise TypeError("tool_func must be an instance of BaseTool")

        self._tools[tool_name] = tool_func

    def unregister_tool(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功注销
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        获取可用工具列表

        Returns:
            工具信息列表
        """
        return [tool.get_info() for tool in self._tools.values()]

    def get_action_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取行为历史

        Args:
            limit: 返回数量限制

        Returns:
            行为历史列表
        """
        return self._action_history[-limit:]

    async def batch_execute(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行行为

        Args:
            actions: 行为列表

        Returns:
            执行结果列表
        """
        tasks = [self.execute_action(action) for action in actions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "action_index": i
                })
            else:
                processed_results.append(result)

        return processed_results

    # 私有方法

    async def _execute_tool_with_retry(
        self,
        tool: BaseTool,
        parameters: Dict[str, Any],
        retry: bool,
        max_retries: int
    ) -> ToolResult:
        """
        执行工具（带重试逻辑）

        Args:
            tool: 工具对象
            parameters: 参数
            retry: 是否重试
            max_retries: 最大重试次数

        Returns:
            工具执行结果
        """
        attempts = 0
        last_error = None

        while attempts <= (max_retries if retry else 0):
            try:
                result = await tool.execute(**parameters)

                if result.success:
                    return result

                # 如果失败且允许重试
                if retry and attempts < max_retries:
                    attempts += 1
                    # 指数退避
                    await asyncio.sleep(0.1 * (2 ** attempts))
                    continue
                else:
                    return result

            except Exception as e:
                last_error = str(e)
                if retry and attempts < max_retries:
                    attempts += 1
                    await asyncio.sleep(0.1 * (2 ** attempts))
                    continue
                else:
                    return ToolResult(
                        success=False,
                        error=last_error or "Unknown error"
                    )

        return ToolResult(
            success=False,
            error=last_error or "Max retries exceeded"
        )
