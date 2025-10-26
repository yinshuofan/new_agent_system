# 快速开始指南 - V2新架构

## 🎯 30秒快速开始

```bash
# 1. 运行测试验证系统
uv run python examples/test_v2_architecture.py

# 2. 运行福尔摩斯交互故事
uv run python examples/holmes_v2.py
```

---

## 📖 完整使用示例

### 1. 基于YAML创建自己的故事

#### 步骤1：创建故事配置文件 `my_story.yaml`

```yaml
metadata:
  title: "我的故事"
  theme: "冒险"
  date: "2025-10-26"

characters:
  hero:
    name: "勇者"
    role: "冒险家"
    personality: "勇敢、正直"
    story_goal: "拯救世界"

  companion:
    name: "伙伴"
    role: "助手"
    personality: "聪明、机智"
    story_goal: "协助勇者"

timeline:
  - time: "09:00"
    chapter: 1
    title: "冒险开始"
    location: "村庄"
    participants: [hero, companion]
    description: "冒险的开始..."

  - time: "12:00"
    chapter: 2
    title: "遇到挑战"
    location: "森林"
    participants: [hero, companion]
    description: "遇到了怪物..."
```

#### 步骤2：创建运行脚本

```python
from agent_system import AgentManager
from agent_system.story import StoryLoader, StoryEngine, StoryMode

async def main():
    # 1. 加载配置
    story_config = StoryLoader.load_from_file("my_story.yaml")

    # 2. 创建剧情引擎
    engine = StoryEngine(story_mode=StoryMode.GUIDED, use_llm=False)
    await engine.initialize()

    # 3. 生成剧情大纲
    outline = StoryLoader.create_story_outline_from_config(story_config)
    engine._current_outline = outline

    # 4. 创建角色
    manager = AgentManager()
    for char_id, char_config in story_config.characters.items():
        agent = await manager.create_agent(
            agent_id=char_id,
            name=char_config["name"],
            config=char_config,
            use_llm=False
        )
        engine.register_agent(agent)
        agent.story_engine = engine

        # 5. 生成日程
        schedule = StoryLoader.generate_schedule_from_config(story_config, char_id)
        engine._agent_schedules[char_id] = schedule

    # 6. 开始互动！
    hero = manager._agents["hero"]

    # 使用ContextManager获取完整上下文
    context = await hero.context_manager.get_full_context()
    print(hero.context_manager.format_context_for_llm(context, "chat"))

asyncio.run(main())
```

---

### 2. 使用ContextManager增强对话

```python
# 获取完整上下文
context = await agent.context_manager.get_full_context()

# 查看上下文内容
print(f"当前活动: {context['schedule']['current_activity']}")
print(f"情感状态: {context['emotion']['primary_emotion']}")
print(f"目标数量: {context['goals']['count']}")

# 格式化为LLM输入
formatted = agent.context_manager.format_context_for_llm(context, "chat")

# 发送给认知模块
decision = await agent.cognition.make_decision(
    situation=formatted + "\n\n用户问：你好吗？",
    emotion=context['emotion'],
    goals=context['goals']['goals'],
    memories=""
)
```

---

### 3. 查看和操作日程

```python
# 获取日程
schedule = story_engine.get_agent_schedule("hero")

# 查看当前活动
current = schedule.get_current_activity(datetime.now())
if current:
    print(f"当前: {current.activity}")
    print(f"描述: {current.description}")

# 查看所有活动
for item in schedule.schedule_items:
    status = "✓" if item.status.value == "completed" else "○"
    print(f"{status} {item.start_time}: {item.activity}")

# 修改日程
await story_engine.modify_schedule(
    agent_id="hero",
    schedule_id=item.schedule_id,
    updates={"activity": "新活动"},
    reason="用户修改"
)
```

---

## 🔧 核心API参考

### ContextManager

```python
# 创建（Agent自动创建）
context_manager = agent.context_manager

# 获取完整上下文
context = await context_manager.get_full_context(trigger="chat")

# 格式化上下文
formatted = context_manager.format_context_for_llm(context, purpose="chat")
```

**返回的context包含**:
- `identity` - 角色信息（role, personality, expertise）
- `schedule` - 日程信息（current_activity, today_summary）
- `emotion` - 情感状态（primary_emotion, valence, arousal）
- `goals` - 目标列表（active goals）
- `memories` - 最近记忆（recent memories）
- `story` - 故事角色（role, goal）

---

### StoryLoader

```python
# 加载YAML配置
story_config = StoryLoader.load_from_file("story.yaml")

# 生成剧情大纲
outline = StoryLoader.create_story_outline_from_config(story_config)

# 生成角色日程
schedule = StoryLoader.generate_schedule_from_config(story_config, "agent_id")

# 访问配置
char_config = story_config.get_character_config("hero")
current_event = story_config.get_current_event(datetime.now())
next_event = story_config.get_next_event(datetime.now())
```

---

## 💡 最佳实践

### 1. 对话时使用完整上下文

```python
async def chat(agent, user_message):
    # ✅ 好的做法
    context = await agent.context_manager.get_full_context()
    formatted = agent.context_manager.format_context_for_llm(context, "chat")
    full_prompt = formatted + f"\n\n用户: {user_message}"

    # ❌ 不好的做法
    prompt = f"用户: {user_message}"  # AI不知道自己的状态
```

### 2. 剧情定义在YAML中

```yaml
# ✅ 好的做法 - 配置文件
timeline:
  - time: "09:00"
    title: "开始"
    description: "详细描述..."

# ❌ 不好的做法 - 硬编码
# plot_points = ["09:00 开始"]
```

### 3. 检查上下文可用性

```python
if context['schedule']['has_schedule']:
    activity = context['schedule']['current_activity']
    print(f"当前: {activity['activity']}")

if context['emotion']['available']:
    emotion = context['emotion']['primary_emotion']
    print(f"情绪: {emotion}")
```

---

## 🎭 福尔摩斯示例使用

```bash
# 运行福尔摩斯V2
uv run python examples/holmes_v2.py

# 对话示例
💬 你: 福尔摩斯先生，案件进展如何？
🤖 Sherlock Holmes: （会根据当前调查进度回复）

💬 你: @watson 你的看法？
🤖 Dr. Watson: （切换到华生）

# 查看状态
💬 你: /status
📊 显示所有角色的当前状态

# 查看日程
💬 你: /schedule holmes
📅 显示福尔摩斯的完整日程

# 查看剧情
💬 你: /story
📖 显示当前章节和进度

# 查看完整上下文
💬 你: /context holmes
📋 显示福尔摩斯的所有状态信息
```

---

## 📊 与旧架构对比

| 功能 | 旧架构 | V2新架构 |
|------|--------|----------|
| 上下文管理 | 手动拼接 | ContextManager自动 |
| 剧情定义 | Python代码 | YAML配置 |
| 对话质量 | AI不知状态 | AI完全感知 |
| 配置难度 | 需改代码 | 编辑YAML |
| 可维护性 | 中等 | 优秀 |
| 代码行数 | - | +2000行 |

---

## ❓ 常见问题

### Q: 如何添加新角色？

在YAML中添加：
```yaml
characters:
  new_character:
    name: "新角色"
    role: "角色定位"
    personality: "性格特点"
```

### Q: 如何修改剧情？

编辑YAML中的timeline部分：
```yaml
timeline:
  - time: "10:00"
    title: "新事件"
    description: "描述..."
```

### Q: 如何让AI知道更多信息？

ContextManager自动收集所有信息，无需手动配置。

### Q: 支持多语言吗？

支持！YAML和提示词都可以用中文或英文。

---

## 🚀 下一步

1. **试运行测试**: `uv run python examples/test_v2_architecture.py`
2. **体验福尔摩斯**: `uv run python examples/holmes_v2.py`
3. **创建自己的故事**: 复制`holmes_story.yaml`并修改
4. **阅读完整文档**: 查看`ITERATION_COMPLETE.md`

---

## 📚 相关文档

- `ITERATION_COMPLETE.md` - 完整的三次迭代文档
- `ITERATION_SUMMARY.md` - 迭代总结
- `examples/README_HOLMES.md` - 福尔摩斯使用指南
- `config/holmes_story.yaml` - 完整的剧情配置示例

---

**Happy Coding! 🎉**
