"""
LLM配置加载器
从配置文件或环境变量加载LLM配置
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

from agent_system.llm.llm_client import LLMConfig, ModelType


def load_llm_config(config_path: Optional[str] = None) -> LLMConfig:
    """
    加载LLM配置

    优先级：
    1. 环境变量 OPENAI_API_KEY
    2. 配置文件中的 api_key
    3. 如果都没有，抛出错误

    Args:
        config_path: 配置文件路径（默认为 config/llm_config.yaml）

    Returns:
        LLMConfig 对象

    Raises:
        ValueError: 如果找不到API key
    """
    # 默认配置路径
    if config_path is None:
        config_path = "/home/user/new_agent_system/config/llm_config.yaml"

    # 默认值
    api_key = None
    base_url = None
    model_mapping = {
        ModelType.FAST: "gpt-3.5-turbo",
        ModelType.ACCURATE: "gpt-4",
        ModelType.REASONING: "o1-preview"
    }
    max_connections = 10
    timeout = 60.0
    max_retries = 3

    # 1. 尝试从配置文件加载
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if config_data and 'openai' in config_data:
                openai_config = config_data['openai']

                # API key
                if 'api_key' in openai_config:
                    api_key = openai_config['api_key']

                # Base URL
                if 'base_url' in openai_config:
                    base_url = openai_config['base_url']

                # 模型映射
                if 'models' in openai_config:
                    models = openai_config['models']
                    if 'fast' in models:
                        model_mapping[ModelType.FAST] = models['fast']
                    if 'accurate' in models:
                        model_mapping[ModelType.ACCURATE] = models['accurate']
                    if 'reasoning' in models:
                        model_mapping[ModelType.REASONING] = models['reasoning']

                # 连接池配置
                if 'connection_pool' in openai_config:
                    pool_config = openai_config['connection_pool']
                    max_connections = pool_config.get('max_connections', max_connections)
                    timeout = pool_config.get('timeout', timeout)
                    max_retries = pool_config.get('max_retries', max_retries)

        except Exception as e:
            print(f"⚠️  警告：无法加载配置文件 {config_path}: {e}")

    # 2. 环境变量优先
    env_api_key = os.getenv('OPENAI_API_KEY')
    if env_api_key:
        api_key = env_api_key

    env_base_url = os.getenv('OPENAI_BASE_URL')
    if env_base_url:
        base_url = env_base_url

    # 3. 验证API key
    if not api_key or api_key == "your-openai-api-key-here":
        raise ValueError(
            "未找到有效的 OpenAI API Key！\n"
            "请通过以下方式之一配置：\n"
            "1. 设置环境变量：export OPENAI_API_KEY='your-key'\n"
            f"2. 在配置文件中设置：{config_path}\n"
        )

    # 创建配置对象
    return LLMConfig(
        api_key=api_key,
        base_url=base_url,
        model_mapping=model_mapping,
        max_connections=max_connections,
        timeout=timeout,
        max_retries=max_retries
    )


def get_api_key_status() -> Dict[str, Any]:
    """
    检查API key配置状态

    Returns:
        状态信息字典
    """
    status = {
        "configured": False,
        "source": None,
        "masked_key": None
    }

    # 检查环境变量
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        status["configured"] = True
        status["source"] = "environment_variable"
        status["masked_key"] = f"{env_key[:8]}...{env_key[-4:]}" if len(env_key) > 12 else "***"
        return status

    # 检查配置文件
    config_path = "/home/user/new_agent_system/config/llm_config.yaml"
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if config_data and 'openai' in config_data:
                api_key = config_data['openai'].get('api_key')
                if api_key and api_key != "your-openai-api-key-here":
                    status["configured"] = True
                    status["source"] = "config_file"
                    status["masked_key"] = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
                    return status
        except:
            pass

    return status
