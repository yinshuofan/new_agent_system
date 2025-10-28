# 智能体系统示例

## interactive_agent.py - 交互式智能体

这是一个完整的、可持久运行的交互式智能体示例。

### 功能特性

- ✅ **持久化运行** - 循环交互，直到用户退出
- ✅ **完整LLM支持** - 使用真实AI模型进行对话
- ✅ **智能体功能** - 记忆、情感、目标管理
- ✅ **交互式界面** - 命令系统和自然对话
- ✅ **状态查看** - 实时查看智能体状态
- ✅ **降级模式** - 无API Key时自动切换到规则模式

### 快速开始

#### 1. 使用规则模式（无需API Key）

```bash
cd examples
python interactive_agent.py --no-llm
```

#### 2. 使用LLM模式（需要API Key）

```bash
# 设置API Key
export OPENAI_API_KEY='your-api-key-here'

# 可选：设置自定义Base URL
export OPENAI_BASE_URL='https://your-custom-endpoint.com/v1'

# 运行
cd examples
python interactive_agent.py
```

### 可用命令

程序运行后，你可以使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/status` | 显示智能体完整状态 |
| `/memory` | 显示最近5条记忆 |
| `/goal` | 交互式添加新目标 |
| `/emotion` | 显示当前情感状态 |
| `/quit` | 退出程序 |

直接输入消息即可与AI对话（无需命令前缀）。

### 使用示例

```
你: 你好
AI: Response to: 你好

你: /status
📊 智能体状态
======================================================================
名称: AI助手
ID: assistant_001
运行状态: 运行中
LLM模式: 规则模式

情感状态: neutral
情感效价: 0.00
唤醒度: 0.00

记忆统计:
  - 事件记忆: 1 条
  - 社交记忆: 0 条

活跃目标: 0 个
======================================================================

你: /memory
💭 最近的记忆
======================================================================

1. 用户对话
   时间: 2025-10-27T...
   详情: 用户: 你好
回复: {'response': 'Response to: 你好'}...

======================================================================

你: /quit
👋 再见！
```

### LLM配置说明

#### OpenAI API

```bash
export OPENAI_API_KEY='sk-...'
```

#### 其他兼容服务（如Azure、自建服务）

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_BASE_URL='https://your-endpoint.com/v1'
```

#### 检查配置

程序启动时会自动检查API Key：
- ✓ 找到API Key → 使用真实AI模型
- ⚠️ 未找到API Key → 自动切换到规则模式

### 智能体功能

#### 1. 记忆系统
- 自动存储所有对话
- 支持记忆检索
- 使用 `/memory` 查看

#### 2. 情感系统
- 实时更新情感状态
- 情感效价和唤醒度
- 使用 `/emotion` 查看

#### 3. 目标管理
- 添加和跟踪目标
- 优先级管理
- 使用 `/goal` 添加新目标

#### 4. 持久化运行
- 循环交互
- Ctrl+C 或 `/quit` 退出
- 自动保存记忆

### 故障排除

#### 问题：ModuleNotFoundError

```bash
# 确保从 examples 目录运行
cd examples
python interactive_agent.py
```

#### 问题：LLM初始化失败

```bash
# 检查API Key是否正确
echo $OPENAI_API_KEY

# 或使用规则模式
python interactive_agent.py --no-llm
```

#### 问题：程序无响应

按 Ctrl+C 可以安全退出程序。

### 技术细节

- **异步架构** - 使用 asyncio 实现高性能
- **事件驱动** - 基于事件总线的模块通信
- **模块化设计** - 6大核心模块（感知、记忆、情感、目标、认知、行为）
- **LLM连接池** - 支持并发请求
- **降级策略** - 无LLM时自动使用规则模式

### 扩展开发

这个示例可以作为你自己项目的起点：

1. **添加自定义命令** - 在 `run()` 方法中添加新的命令处理
2. **集成其他LLM** - 修改 LLM 初始化代码
3. **持久化存储** - 添加数据库支持保存记忆
4. **多智能体** - 创建多个智能体实例进行交互

### 进一步学习

- 查看 `agent_system/core/agent.py` 了解智能体核心实现
- 查看 `agent_system/modules/` 了解各个模块的详细功能
- 查看项目根目录的 README.md 了解系统架构
