# 交互式智能体使用指南

## 概述

`interactive_agent.py` 提供了一个能够持续运行的交互式智能体系统，支持：

- ✅ 智能体根据日程自主运行
- ✅ 睡眠时间管理（晚上22:00-早上7:00不活动）
- ✅ 用户随时与智能体对话
- ✅ 简单的命令行交互界面

## 快速开始

### 1. 运行交互式智能体

```bash
uv run python examples/interactive_agent.py
```

### 2. 选择模式

启动时会询问是否启用剧情模式：
- 输入 `y` - 启用剧情模式，智能体会有日程安排
- 输入 `n` - 纯聊天模式，无日程

### 3. 与智能体交互

直接输入文字即可与智能体聊天：

```
💬 你: 你好！
🤖 Alice: 你好！很高兴见到你...
```

## 可用命令

在交互界面中，可以使用以下命令：

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助信息 |
| `/status` | 查看智能体当前状态 |
| `/schedule` | 查看今日日程安排 |
| `/emotion` | 查看智能体情感状态 |
| `/goals` | 查看当前目标 |
| `/memory` | 查看最近记忆 |
| `/quit` | 退出程序 |

## 功能特性

### 1. 睡眠管理

智能体有作息时间：
- **起床时间**: 07:00
- **睡觉时间**: 22:00

在睡眠时间段内：
- 智能体不会处理后台任务
- 用户聊天会收到"正在睡觉"的提示
- 可以通过修改代码自定义睡眠时间

```python
self.sleep_start_time = time(22, 0)  # 22:00开始睡觉
self.wake_up_time = time(7, 0)       # 07:00起床
```

### 2. 日程系统

启用剧情模式后，智能体会有完整的日程安排：
- 查看当前正在做什么
- 自动根据时间切换活动
- 记录活动到记忆中

### 3. 对话记忆

所有对话都会被记录到智能体记忆中：
- 使用 `/memory` 查看对话历史
- 智能体会根据历史对话做出更连贯的回复

### 4. 情感系统

智能体具有情感状态：
- 使用 `/emotion` 查看当前情绪
- 对话会影响智能体的情感
- 情感会影响智能体的回复风格

## 示例对话

```
💬 你: 早上好！
🤖 Alice: 早上好！新的一天开始了，今天天气不错呢！

💬 你: /status
📊 智能体状态
  名称: Alice
  当前活动: 📋 起床，开始新的一天
  情感: neutral
  效价: 0.00
  唤醒度: 0.50

💬 你: 你今天有什么计划？
🤖 Alice: 让我看看我的日程...今天我会...

💬 你: /schedule
📅 今日日程 (2025-10-26)
------------------------------------------------------------
今天共有5个活动:
○ 09:00-10:00: 起床，开始新的一天
○ 12:00-13:00: 午餐时间，休息放松
...
```

## 自定义配置

### 修改睡眠时间

编辑 `interactive_agent.py` 中的 `InteractiveAgent.__init__`:

```python
self.sleep_start_time = time(23, 0)  # 改为23:00睡觉
self.wake_up_time = time(6, 0)       # 改为06:00起床
```

### 修改后台检查间隔

编辑 `agent_background_loop` 函数：

```python
check_interval = 30  # 改为每30秒检查一次
```

### 自定义LLM配置

修改 `main` 函数中的LLM配置：

```python
llm_config = LLMConfig(
    api_key="your_api_key",
    base_url="your_base_url",
    model_mapping={
        ModelType.FAST: "your_fast_model",
        ModelType.ACCURATE: "your_accurate_model",
        ModelType.REASONING: "your_reasoning_model"
    }
)
```

## 退出程序

有两种方式退出：

1. 使用命令: `/quit`
2. 按 `Ctrl+C` 中断程序

## 技术说明

### 架构

- **异步处理**: 使用 asyncio 同时处理后台任务和用户输入
- **非阻塞输入**: 用户输入在线程池中执行，不阻塞事件循环
- **模块化设计**: InteractiveAgent 类封装了所有交互逻辑

### 后台循环

智能体在后台每60秒执行一次：
1. 检查是否在睡觉
2. 如果醒着，触发 `process_tick()`
3. 检查日程偏离（如果启用剧情模式）

### 对话处理

用户消息处理流程：
1. 将消息作为环境事件让智能体感知
2. 使用认知模块生成回复
3. 记录对话到记忆系统

## 故障排除

### 问题：智能体不回复

**解决方案**:
- 检查智能体是否在睡觉时间
- 使用 `/status` 查看状态
- 查看控制台是否有错误信息

### 问题：LLM调用失败

**解决方案**:
- 检查API密钥是否正确
- 检查网络连接
- 系统会自动降级到规则模式

### 问题：日程不显示

**解决方案**:
- 确保启动时选择了剧情模式 (y)
- 使用 `/schedule` 查看日程

## 进阶使用

### 集成到其他系统

```python
from examples.interactive_agent import InteractiveAgent

# 创建你的智能体
agent = await manager.create_agent(...)

# 创建交互式包装器
interactive = InteractiveAgent(agent, story_engine)

# 发送消息
reply = await interactive.chat("Hello!")
```

### 自定义命令

在 `handle_command` 函数中添加新命令：

```python
elif cmd == '/your_command':
    # 你的自定义逻辑
    print("执行自定义命令")
```

## 更多示例

- `story_schedule_example.py` - 完整的剧情日程演绎示例
- `test_interactive.py` - 交互式功能测试示例
