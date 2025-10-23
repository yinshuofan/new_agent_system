# 智能体系统 (Agent System)

一个基于Python的模块化智能体框架，支持高并发运行多个智能体实例。

## 系统架构

本系统实现了一个完整的智能体架构，包含以下六大核心模块：

### 核心模块

1. **感知模块 (Perception)** - 负责收集环境信息
   - 处理外部刺激
   - 接收其他智能体消息
   - 感知环境变化

2. **记忆模块 (Memory)** - 管理智能体记忆
   - 事件记忆：存储个人经历
   - 社交记忆：管理与他人的关系
   - 记忆检索和遗忘机制

3. **情感模块 (Emotion)** - 管理情感状态
   - 基于维度模型（效价、唤醒度、支配度）
   - 支持基本情感类型
   - 情感衰减和心境管理

4. **目标与需求模块 (Goal)** - 管理目标和需求
   - 目标创建和更新
   - 需求管理（基于马斯洛需求层次）
   - 目标优先级和进度跟踪

5. **认知模块 (Cognition)** - 核心决策逻辑
   - 整合所有模块信息
   - 决策制定
   - 自我反思

6. **行为模块 (Behavior)** - 工具执行
   - 工具注册和管理
   - 行为执行（支持重试）
   - 批量操作

### 系统特性

- **事件总线 (Event Bus)** - 模块间通信使用观察者模式
- **定时触发器 (Scheduler)** - 支持智能体定期自动更新
- **高并发支持 (Agent Manager)** - 一个服务可运行多个智能体实例
- **异步架构** - 全异步设计，支持高性能并发

## 安装

```bash
# 克隆仓库
git clone <repository_url>
cd new_agent_system

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 单智能体示例

```python
import asyncio
from agent_system import Agent
from agent_system.models.goal_models import GoalPriority

async def main():
    # 创建智能体
    agent = Agent(
        agent_id="agent_001",
        name="Alice",
        config={"max_memories": 500}
    )

    # 启动智能体
    await agent.start()

    # 添加目标
    goal_id = await agent.add_goal({
        "title": "学习Python",
        "priority": GoalPriority.HIGH.value
    })

    # 接收消息
    response = await agent.receive_message(
        sender_id="user",
        message="你好！"
    )

    # 停止智能体
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 多智能体示例

```python
import asyncio
from agent_system import AgentManager

async def main():
    # 创建管理器
    manager = AgentManager(max_agents=10)

    # 创建多个智能体
    alice = await manager.create_agent("alice", "Alice")
    bob = await manager.create_agent("bob", "Bob")

    # 智能体间通信
    response = await manager.send_message(
        sender_id="alice",
        target_id="bob",
        message="你好Bob！"
    )

    # 广播消息
    responses = await manager.broadcast_message(
        sender_id="alice",
        message="大家好！"
    )

    # 停止所有智能体
    await manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
```

## 运行示例

```bash
# 运行单智能体示例
python examples/simple_agent.py

# 运行多智能体示例
python examples/multi_agent.py
```

## 设计模式

本系统采用了多种设计模式：

1. **观察者模式** - 事件总线实现模块间通信
2. **策略模式** - 支持自定义决策策略
3. **命令模式** - 工具系统实现
4. **工厂模式** - 记忆和目标对象创建
5. **单例模式** - 全局管理器（可选）

## 扩展性

### 自定义决策策略

```python
async def custom_decision_strategy(context, cognition_module):
    # 自定义决策逻辑
    # 例如：集成LLM进行决策
    return {
        "action": {"type": "custom_action"},
        "reasoning": "Custom reasoning",
        "confidence": 0.9
    }

# 设置自定义策略
agent.cognition.set_decision_strategy(custom_decision_strategy)
```

### 自定义工具

```python
from agent_system.tools.base_tools import BaseTool, ToolResult

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__("custom_tool", "自定义工具")

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return ToolResult(success=True, result={"data": "result"})

# 注册工具
agent.behavior.register_tool("custom_tool", CustomTool())
```

## 配置

配置文件示例见 `config/agent_config.yaml`

## 目录结构

```
new_agent_system/
├── agent_system/           # 核心代码
│   ├── core/              # 核心类
│   │   ├── agent.py       # Agent核心类
│   │   ├── base.py        # 基础接口
│   │   └── event_bus.py   # 事件总线
│   ├── modules/           # 各功能模块
│   │   ├── perception.py
│   │   ├── memory.py
│   │   ├── emotion.py
│   │   ├── goal.py
│   │   ├── cognition.py
│   │   └── behavior.py
│   ├── models/            # 数据模型
│   ├── tools/             # 工具定义
│   ├── scheduler/         # 调度器
│   └── manager/           # 管理器
├── examples/              # 示例代码
├── config/                # 配置文件
└── tests/                 # 测试代码
```

## 性能特性

- **异步并发** - 全异步架构，支持高并发
- **事件驱动** - 基于事件总线的松耦合设计
- **模块化** - 各模块独立，易于扩展和维护
- **可扩展** - 支持自定义决策策略、工具和触发器

## 适用场景

- 多智能体模拟
- 虚拟角色系统
- 游戏NPC
- 对话系统
- 自动化任务执行
- 分布式智能体系统

## License

MIT License

## 贡献

欢迎提交Issue和Pull Request！
