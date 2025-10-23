"""
基础工具定义
使用命令模式实现工具系统
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(description="是否成功")
    result: Any = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(0.0, description="执行时间（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class BaseTool(ABC):
    """
    工具基类（命令模式）
    所有工具都继承此类
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description
        }


# 预定义工具示例

class SendMessageTool(BaseTool):
    """发送消息工具"""

    def __init__(self, message_callback):
        super().__init__(
            name="send_message",
            description="向其他智能体或用户发送消息"
        )
        self._message_callback = message_callback

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行发送消息

        Args:
            target_id: 目标ID
            message: 消息内容

        Returns:
            执行结果
        """
        start_time = datetime.now()
        try:
            target_id = kwargs.get("target_id")
            message = kwargs.get("message")

            if not target_id or not message:
                return ToolResult(
                    success=False,
                    error="Missing required parameters: target_id or message"
                )

            # 调用消息回调
            if self._message_callback:
                result = await self._message_callback(target_id, message)
            else:
                result = {"sent": True, "target": target_id}

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )


class UpdateGoalTool(BaseTool):
    """更新目标工具"""

    def __init__(self, goal_module):
        super().__init__(
            name="update_goal",
            description="更新目标进度或状态"
        )
        self._goal_module = goal_module

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行目标更新

        Args:
            goal_id: 目标ID
            progress: 新的进度（可选）
            action: 操作类型（activate/suspend/complete）

        Returns:
            执行结果
        """
        start_time = datetime.now()
        try:
            goal_id = kwargs.get("goal_id")
            progress = kwargs.get("progress")
            action = kwargs.get("action")

            if not goal_id:
                return ToolResult(
                    success=False,
                    error="Missing required parameter: goal_id"
                )

            if progress is not None:
                await self._goal_module.update_goal_progress(goal_id, progress)

            if action == "activate":
                await self._goal_module.activate_goal(goal_id)
            elif action == "suspend":
                await self._goal_module.suspend_goal(goal_id)

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolResult(
                success=True,
                result={"goal_id": goal_id, "updated": True},
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )


class InteractEnvironmentTool(BaseTool):
    """与环境交互工具"""

    def __init__(self, environment_callback):
        super().__init__(
            name="interact_environment",
            description="与环境进行交互"
        )
        self._environment_callback = environment_callback

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行环境交互

        Args:
            action_type: 交互类型
            parameters: 交互参数

        Returns:
            执行结果
        """
        start_time = datetime.now()
        try:
            action_type = kwargs.get("action_type")
            parameters = kwargs.get("parameters", {})

            if not action_type:
                return ToolResult(
                    success=False,
                    error="Missing required parameter: action_type"
                )

            # 调用环境回调
            if self._environment_callback:
                result = await self._environment_callback(action_type, parameters)
            else:
                result = {"action": action_type, "executed": True}

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )


class RetrieveMemoryTool(BaseTool):
    """检索记忆工具"""

    def __init__(self, memory_module):
        super().__init__(
            name="retrieve_memory",
            description="检索相关记忆"
        )
        self._memory_module = memory_module

    async def execute(self, **kwargs) -> ToolResult:
        """
        执行记忆检索

        Args:
            query: 查询条件
            limit: 返回数量限制

        Returns:
            执行结果
        """
        start_time = datetime.now()
        try:
            query = kwargs.get("query", {})
            limit = kwargs.get("limit", 5)

            memories = await self._memory_module.retrieve(query, limit)

            execution_time = (datetime.now() - start_time).total_seconds()

            return ToolResult(
                success=True,
                result={"memories": memories, "count": len(memories)},
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
