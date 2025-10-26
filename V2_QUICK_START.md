# V2 架构快速开始指南

## 🎯 概述

V2 架构是完全重构的智能体系统，具有以下特点：

- **极简 API**：一行代码创建故事智能体
- **自动上下文管理**：ContextManager 自动收集所有模块信息
- **YAML 配置**：声明式定义故事、角色、时间线
- **多天剧情支持**：支持跨天剧情配置
- **完整记忆系统**：对话、事件自动存储和检索
- **情感系统**：根据感知自动更新情感状态

---

## 📦 核心组件

### 1. StoryAgentFactory（故事智能体工厂）

简化智能体创建流程的工厂类。

```python
from agent_system.story import StoryAgentFactory

# 创建工厂
factory = StoryAgentFactory("config/holmes_story.yaml")
await factory.initialize()

# 获取智能体
holmes = factory.get_agent("holmes")
```

### 2. create_story_agents（快速创建函数）

最简单的方式：一行代码创建所有智能体。

```python
from agent_system.story import create_story_agents

# 创建所有智能体
agents = await create_story_agents("config/holmes_story.yaml")

# 使用智能体
holmes = agents["holmes"]
reply = await holmes.chat("你好！")
```

### 3. ContextManager（上下文管理器）

自动收集和格式化所有模块的上下文信息。

```python
# 获取完整上下文
context = await agent.context_manager.get_full_context()

# 上下文包含：
# - identity: 身份信息（角色、性格、专长）
# - emotion: 情感状态
# - schedule: 日程安排
# - memories: 记忆（最近10条）
# - goals: 当前目标
# - relationships: 社交关系
# - environment: 环境感知
```

### 4. StoryLoader（剧情加载器）

从 YAML 文件加载剧情配置。

```python
from agent_system.story import StoryLoader

# 加载配置
story_config = StoryLoader.load_from_file("config/holmes_story.yaml")

# 访问配置
print(story_config.title)  # 故事标题
print(story_config.characters)  # 角色配置
print(story_config.timeline)  # 时间线事件
```

---

## 🚀 快速开始

### 最小示例（5 行代码）

```python
import asyncio
from agent_system.story import create_story_agents

async def main():
    # 1. 创建智能体
    agents = await create_story_agents("config/holmes_story.yaml", use_llm=False)

    # 2. 对话
    holmes = agents["holmes"]
    reply = await holmes.chat("你好！")
    print(reply)

    # 3. 清理
    await holmes.stop()

asyncio.run(main())
```

### 完整示例

参考 `examples/quick_start.py`：

```bash
cd examples
python quick_start.py
```

---

## 📝 YAML 故事配置

### 单天故事配置

```yaml
metadata:
  title: "失踪的蓝宝石项链"
  theme: "侦探推理"
  date: "2025-10-26"

characters:
  holmes:
    name: "Sherlock Holmes"
    role: "私家侦探"
    personality: "聪明绝顶、观察力敏锐"
    expertise: ["犯罪调查", "逻辑推理"]
    story_goal: "调查项链失窃案"

timeline:
  - time: "08:00"
    chapter: 1
    title: "委托求助"
    participants: [holmes, watson, emily]
    description: "委托人来访，描述案情..."

  - time: "10:30"
    chapter: 2
    title: "现场勘查"
    participants: [holmes, watson]
    description: "前往现场调查..."
```

### 多天故事配置

```yaml
metadata:
  title: "连环失窃案调查"
  start_date: "2025-10-26"
  duration_days: 3

multi_day_timeline:
  day_1:
    date: "2025-10-26"
    day_title: "第一天：案发调查"
    events:
      - time: "09:00"
        title: "接到报案"
        # ...

  day_2:
    date: "2025-10-27"
    day_title: "第二天：深入调查"
    events:
      - time: "08:00"
        title: "新线索"
        # ...

story_settings:
  auto_progress_to_next_day: true
  day_transition_time: "22:00"

cross_day_settings:
  auto_save_daily_summary: true
  review_previous_day: true
```

详细配置请参考：
- 单天示例：`config/holmes_story.yaml`
- 多天示例：`config/multi_day_story_example.yaml`
- 多天指南：`MULTI_DAY_STORY_GUIDE.md`

---

## 🔧 高级用法

### 1. 访问智能体上下文

```python
# 获取完整上下文
context = await agent.context_manager.get_full_context(trigger="chat")

# 访问各个部分
print(f"角色: {context['identity']['role']}")
print(f"情感: {context['emotion']['primary_emotion']}")
print(f"记忆数: {context['memories']['count']}")
print(f"当前活动: {context['schedule']['current_activity']}")
```

### 2. 格式化上下文给 LLM

```python
# 获取并格式化
context = await agent.context_manager.get_full_context()
formatted_text = agent.context_manager.format_context_for_llm(context, "chat")

# 发送给 LLM
response = await llm.generate(formatted_text, user_message)
```

### 3. 手动存储记忆

```python
# 存储事件记忆
await agent.memory.store("event", {
    "event_type": "investigation",
    "event_summary": "发现重要线索",
    "event_details": "在现场发现指纹",
    "participants": ["holmes"],
    "timestamp": datetime.now().isoformat()
})

# 检索记忆
memories = await agent.memory.retrieve({
    "memory_type": "event",
    "keywords": ["线索"],
    "participants": ["holmes"]
}, limit=5)
```

### 4. 添加目标

```python
# 添加目标
await agent.add_goal({
    "title": "破案",
    "description": "找出真凶",
    "priority": 1
})

# 获取目标
goals = agent.goal.get_active_goals()
```

### 5. 更新情感

```python
# 处理情感事件
await agent.emotion.process_emotion({
    "type": "discovery",
    "valence": 0.5,  # 正面情感
    "arousal": 0.7,  # 高唤醒
    "intensity": 0.6,
    "description": "发现关键证据"
})

# 获取情感状态
emotion = agent.emotion.get_current_emotion()
print(emotion["primary_emotion"])  # 如：excited
```

---

## 🐛 Bug 修复记录

### V2.1 修复

1. **记忆检索 Bug**（`context_manager.py:169-174`）
   - **问题**：对话记忆存储正常，但检索时访问了不存在的 `content` 键
   - **修复**：直接访问记忆字段，不使用嵌套的 content

2. **情感更新 Bug**（`emotion.py:288-360`）
   - **问题**：用户对话时情感不更新
   - **修复**：增强 `_on_perception_updated` 和 `_on_environment_changed` 事件处理

---

## 📊 与 V1 的区别

| 特性 | V1 | V2 |
|------|----|----|
| 智能体创建 | 手动配置各模块 | 一行代码创建 |
| 上下文管理 | 手动收集 | 自动收集（ContextManager） |
| 故事配置 | Python 代码 | YAML 文件 |
| 多天剧情 | 不支持 | 完整支持 |
| 记忆检索 | 手动调用 | 自动包含在上下文 |
| 情感更新 | 手动触发 | 事件驱动自动更新 |

---

## 📚 示例代码

### 1. 基础对话（`examples/quick_start.py`）

演示最简单的创建和对话流程。

### 2. V2 架构测试（`examples/test_v2_architecture.py`）

测试所有 V2 核心功能：
- StoryLoader
- ContextManager
- 集成测试

### 3. Holmes V2（`examples/holmes_v2.py`）

完整的福尔摩斯互动故事系统，包括：
- 自动时间推进
- 状态查询
- 持续对话
- 剧情追踪

---

## 🎓 学习路径

1. **入门**：运行 `examples/quick_start.py`，理解基本 API
2. **配置**：学习 `config/holmes_story.yaml`，了解如何配置故事
3. **多天剧情**：查看 `MULTI_DAY_STORY_GUIDE.md` 和 `config/multi_day_story_example.yaml`
4. **深入**：阅读 `examples/holmes_v2.py`，学习高级用法
5. **测试**：运行 `examples/test_v2_architecture.py`，验证系统功能

---

## 🔗 相关文档

- [多天剧情配置指南](MULTI_DAY_STORY_GUIDE.md)
- [Holmes 故事配置](config/holmes_story.yaml)
- [多天故事示例](config/multi_day_story_example.yaml)
- [V2 架构测试](examples/test_v2_architecture.py)

---

## ❓ 常见问题

### Q: 如何使用真实的 LLM？

```python
agents = await create_story_agents(
    "config/holmes_story.yaml",
    use_llm=True  # 开启 LLM
)
```

确保在 `config/llm_config.yaml` 中配置了 API key。

### Q: 如何创建自己的故事？

1. 复制 `config/holmes_story.yaml`
2. 修改 metadata、characters、timeline
3. 使用 `create_story_agents("your_story.yaml")` 加载

### Q: 对话记忆会自动保存吗？

是的！使用 `agent.chat()` 时会自动存储对话到记忆系统。

### Q: 如何支持更长时间的剧情？

参考 `MULTI_DAY_STORY_GUIDE.md`，使用 `multi_day_timeline` 配置多天剧情。

---

## 🎉 开始使用

```bash
# 1. 运行快速开始示例
cd examples
python quick_start.py

# 2. 运行完整测试
python test_v2_architecture.py

# 3. 运行 Holmes 互动故事
python holmes_v2.py
```

祝你使用愉快！🚀
