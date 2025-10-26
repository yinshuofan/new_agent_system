"""
LLM调用模块
支持多种模型类型和连接池管理
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None


class ModelType(Enum):
    """模型类型"""
    FAST = "fast"  # 快速模型（如gpt-3.5-turbo）
    ACCURATE = "accurate"  # 精确模型（如gpt-4）
    REASONING = "reasoning"  # 推理模型（如o1）


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str
    base_url: Optional[str] = None
    model_mapping: Optional[Dict[ModelType, str]] = None
    max_connections: int = 10
    timeout: float = 60.0
    max_retries: int = 3


class LLMConnectionPool:
    """
    LLM连接池
    管理多个OpenAI客户端实例以提高并发性能
    """

    def __init__(self, config: LLMConfig):
        """
        初始化连接池

        Args:
            config: LLM配置
        """
        if AsyncOpenAI is None:
            raise ImportError("openai library not installed. Run: pip install openai")

        self.config = config
        self._clients: List[AsyncOpenAI] = []
        self._available_clients: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._initialized = False

        # 默认模型映射
        self._model_mapping = config.model_mapping or {
            ModelType.FAST: "gpt-3.5-turbo",
            ModelType.ACCURATE: "gpt-4",
            ModelType.REASONING: "o1-preview"
        }

    async def initialize(self) -> None:
        """初始化连接池"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            # 创建客户端实例
            for _ in range(self.config.max_connections):
                client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries
                )
                self._clients.append(client)
                await self._available_clients.put(client)

            self._initialized = True

    async def acquire(self) -> AsyncOpenAI:
        """
        获取一个客户端

        Returns:
            OpenAI客户端实例
        """
        if not self._initialized:
            await self.initialize()

        return await self._available_clients.get()

    async def release(self, client: AsyncOpenAI) -> None:
        """
        释放客户端回连接池

        Args:
            client: OpenAI客户端实例
        """
        await self._available_clients.put(client)

    def get_model_name(self, model_type: ModelType) -> str:
        """
        获取模型名称

        Args:
            model_type: 模型类型

        Returns:
            模型名称
        """
        return self._model_mapping.get(model_type, self._model_mapping[ModelType.FAST])

    async def close(self) -> None:
        """关闭连接池"""
        async with self._lock:
            for client in self._clients:
                await client.close()
            self._clients.clear()
            # 清空队列
            while not self._available_clients.empty():
                try:
                    self._available_clients.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self._initialized = False


class LLMClient:
    """
    LLM客户端
    提供统一的LLM调用接口
    """

    def __init__(self, connection_pool: LLMConnectionPool):
        """
        初始化LLM客户端

        Args:
            connection_pool: 连接池实例
        """
        self.pool = connection_pool
        self._call_count = 0
        self._total_tokens = 0

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_type: ModelType = ModelType.FAST,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        聊天补全

        Args:
            messages: 消息列表
            model_type: 模型类型
            temperature: 温度参数
            max_tokens: 最大token数
            json_mode: 是否使用JSON模式
            **kwargs: 其他参数

        Returns:
            LLM响应
        """
        client = await self.pool.acquire()
        try:
            model_name = self.pool.get_model_name(model_type)

            # 构建请求参数
            params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            if json_mode:
                params["response_format"] = {"type": "json_object"}

            # 调用API
            response = await client.chat.completions.create(**params)

            # 统计
            self._call_count += 1
            if hasattr(response, 'usage'):
                self._total_tokens += response.usage.total_tokens

            # 解析响应
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
                },
                "finish_reason": response.choices[0].finish_reason
            }

            return result

        finally:
            await self.pool.release(client)

    async def generate_text(
        self,
        prompt: str,
        model_type: ModelType = ModelType.FAST,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        生成文本（简化接口）

        Args:
            prompt: 用户提示
            model_type: 模型类型
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response["content"]

    async def generate_json(
        self,
        prompt: str,
        model_type: ModelType = ModelType.FAST,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成JSON格式响应

        Args:
            prompt: 用户提示
            model_type: 模型类型
            system_prompt: 系统提示
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            解析后的JSON对象
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.chat_completion(
            messages=messages,
            model_type=model_type,
            temperature=temperature,
            json_mode=True,
            **kwargs
        )

        try:
            return json.loads(response["content"])
        except json.JSONDecodeError:
            # 如果解析失败，返回原始内容
            return {"content": response["content"], "parse_error": True}

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "call_count": self._call_count,
            "total_tokens": self._total_tokens
        }


# 全局LLM客户端管理
_global_pool: Optional[LLMConnectionPool] = None
_global_client: Optional[LLMClient] = None


async def initialize_llm(config: LLMConfig) -> LLMClient:
    """
    初始化全局LLM客户端

    Args:
        config: LLM配置

    Returns:
        LLM客户端实例
    """
    global _global_pool, _global_client

    _global_pool = LLMConnectionPool(config)
    await _global_pool.initialize()
    _global_client = LLMClient(_global_pool)

    return _global_client


def get_llm_client() -> Optional[LLMClient]:
    """获取全局LLM客户端"""
    return _global_client


async def close_llm() -> None:
    """关闭全局LLM连接"""
    global _global_pool, _global_client

    if _global_pool:
        await _global_pool.close()
        _global_pool = None
        _global_client = None
