# LLM和剧情系统功能说明

## 新增功能

### 1. LLM调用模块

#### 功能特性
- **多模型支持**：区分快速模型（gpt-3.5-turbo）、精确模型（gpt-4）、推理模型（o1）
- **连接池管理**：自动管理多个OpenAI客户端连接，提高并发性能
- **智能重试**：支持自动重试和错误处理
- **统计功能**：跟踪API调用次数和Token使用

#### 使用方法

```python
from agent_system.llm import initialize_llm, LLMConfig, ModelType

# 初始化LLM
llm_config = LLMConfig(
    api_key="your-openai-api-key",
    max_connections=10,
    timeout=60.0
)
llm_client = await initialize_llm(llm_config)

# 使用不同模型
response = await llm_client.generate_text(
    prompt="你好，请介绍一下自己",
    model_type=ModelType.FAST,  # 或 ACCURATE, REASONING
    temperature=0.7
)
```

### 2. 提示词配置系统

#### 功能特性
- **外部配置**：所有提示词存储在YAML文件中，便于修改
- **模块化管理**：为每个模块提供专门的提示词
- **默认提示词**：内置最简提示词，即使没有配置文件也能工作

#### 配置文件位置
- `config/prompts.yaml`

#### 使用方法

```python
from agent_system.llm.prompt_manager import initialize_prompts

# 加载提示词配置
initialize_prompts("/path/to/prompts.yaml")

# 在模块中使用
prompt = self._prompt_manager.get_prompt(
    "cognition",
    "make_decision",
    situation="...",
    emotion="..."
)
```

### 3. LLM集成到核心模块

#### 认知模块(Cognition)
- **LLM决策策略**：使用LLM进行更智能的决策
- **LLM反思**：通过LLM进行自我反思和总结
- **自动回退**：LLM失败时自动使用规则决策

```python
# 创建启用LLM的智能体
agent = Agent(
    agent_id="agent_001",
    name="Alice",
    use_llm=True  # 启用LLM
)
```

#### 其他模块
虽然示例中主要展示了认知模块，但架构设计支持在以下模块中集成LLM：
- **情感模块**：分析情感触发因素
- **目标模块**：生成合理的目标
- **感知模块**：理解和提取感知信息
- **记忆模块**：智能总结和检索

### 4. 剧情演绎系统

#### 功能特性
- **剧情生成**：使用LLM自动生成剧情，或使用预定义剧情
- **剧情对齐检查**：自动检查智能体行为是否偏离核心剧情
- **剧情推进**：跟踪和管理剧情进度
- **事件生成**：根据当前剧情生成合适的环境事件

#### 剧情模式
- **STRICT**：严格模式 - 紧密遵循剧情
- **GUIDED**：引导模式 - 允许偏离但会引导回归
- **FREE**：自由模式 - 剧情仅作参考

#### 使用方法

```python
from agent_system.story import StoryEngine, StoryMode

# 创建剧情引擎
story_engine = StoryEngine(
    story_mode=StoryMode.GUIDED,
    use_llm=True
)
await story_engine.initialize()

# 生成剧情
characters = [
    {"agent_id": "alice", "name": "Alice", "role": "protagonist"},
    {"agent_id": "bob", "name": "Bob", "role": "sidekick"}
]

# 使用自定义剧情点
custom_plot = [
    "开场：主角接到任务",
    "发展：遇到困难",
    "高潮：克服挑战",
    "结局：任务完成"
]

story = await story_engine.generate_story(
    theme="冒险故事",
    agent_characters=characters,
    custom_plot=custom_plot
)

# 检查行为对齐
alignment = await story_engine.check_action_alignment(
    agent_id="alice",
    action={"type": "explore", "location": "forest"}
)

if not alignment['aligned']:
    print(f"偏离建议: {alignment['suggestion']}")
```

## 运行示例

### 基础LLM示例

```bash
# 设置API Key（必需）
export OPENAI_API_KEY="your-api-key-here"

# 运行示例
python examples/llm_agent_example.py
```

### 剧情演绎示例

```bash
# 设置API Key（可选，不设置则使用规则模式）
export OPENAI_API_KEY="your-api-key-here"

# 运行示例
python examples/story_agent_example.py
```

## 配置说明

### LLM配置

在代码中配置：

```python
llm_config = LLMConfig(
    api_key="your-api-key",
    base_url=None,  # 自定义API地址（可选）
    model_mapping={  # 自定义模型映射（可选）
        ModelType.FAST: "gpt-3.5-turbo",
        ModelType.ACCURATE: "gpt-4",
        ModelType.REASONING: "o1-preview"
    },
    max_connections=10,  # 连接池大小
    timeout=60.0,  # 超时时间（秒）
    max_retries=3  # 最大重试次数
)
```

### 提示词配置

编辑 `config/prompts.yaml`：

```yaml
cognition:
  system: "You are an intelligent agent..."

  make_decision: |
    Analyze the situation and make a decision.

    Situation: {situation}
    Options: {options}

    Provide decision in JSON format...

# 更多模块的提示词...
```

## 架构优势

1. **最少提示词原则**：所有LLM调用都使用简洁的提示词，避免过度工程
2. **架构不变**：LLM功能通过策略模式集成，不改变原有架构
3. **灵活切换**：可以在LLM和规则模式间自由切换
4. **高性能**：连接池管理确保高并发场景下的性能
5. **容错机制**：LLM失败时自动回退到规则模式
6. **可扩展**：易于为其他模块添加LLM支持

## 注意事项

1. **API密钥**：需要有效的OpenAI API密钥
2. **费用**：LLM调用会产生费用，建议使用快速模型进行测试
3. **网络**：需要稳定的网络连接
4. **配额**：注意API调用配额限制
5. **提示词**：可以根据需要自定义提示词以获得更好的效果

## 未来扩展

- 支持更多LLM提供商（Azure OpenAI、Anthropic Claude等）
- 为其他模块（情感、目标、记忆）添加更多LLM功能
- 提示词优化和A/B测试
- 剧情树和分支剧情支持
- 多智能体剧情协作
