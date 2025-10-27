# 智能体系统架构全面梳理

## 📊 系统架构概览

### 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agent (智能体核心)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              EventBus (事件总线 - 观察者模式)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↕                                  │
│  ┌────────────┬────────────┬────────────┬────────────┐         │
│  │ Perception │   Memory   │  Emotion   │    Goal    │         │
│  │   感知模块   │   记忆模块  │  情感模块   │   目标模块  │         │
│  └────────────┴────────────┴────────────┴────────────┘         │
│                              ↕                                  │
│  ┌──────────────────────┬──────────────────────────┐          │
│  │   Cognition (认知)    │     Behavior (行为)       │          │
│  │    决策与推理中心       │      行为执行模块          │          │
│  └──────────────────────┴──────────────────────────┘          │
│                              ↕                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ContextManager (上下文管理器 - 自动聚合)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
        ┌────────────────────────────────────────┐
        │    StoryEngine (剧情引擎 - 可选)       │
        │  - 剧情大纲管理                         │
        │  - 日程调度                             │
        │  - 偏离检测                             │
        └────────────────────────────────────────┘
```

---

## 🔄 事件系统详解

### 事件类型 (EventType)

| 事件类型 | 值 | 触发时机 | 说明 |
|---------|---|---------|------|
| **感知相关** |
| PERCEPTION_UPDATED | perception_updated | 感知到新信息时 | 环境信息更新 |
| ENVIRONMENT_CHANGED | environment_changed | 环境发生变化时 | 环境状态改变 |
| **记忆相关** |
| MEMORY_CREATED | memory_created | 创建新记忆时 | 事件或社交记忆创建 |
| MEMORY_RETRIEVED | memory_retrieved | 检索记忆时 | 记忆被查询 |
| **情感相关** |
| EMOTION_CHANGED | emotion_changed | 情感状态改变时 | 情感维度变化 |
| MOOD_SHIFTED | mood_shifted | 心情转换时 | 整体心情变化 |
| **目标相关** |
| GOAL_CREATED | goal_created | 创建新目标时 | 添加新目标 |
| GOAL_UPDATED | goal_updated | 目标更新时 | 目标进度/状态变化 |
| GOAL_COMPLETED | goal_completed | 目标完成时 | 目标达成 |
| **认知相关** |
| DECISION_MADE | decision_made | 做出决策时 | 认知模块决策完成 |
| REFLECTION_COMPLETED | reflection_completed | 反思完成时 | 自我反思结束 |
| **行为相关** |
| ACTION_EXECUTED | action_executed | 执行行为时 | 行为成功执行 |
| ACTION_FAILED | action_failed | 行为失败时 | 行为执行失败 |
| **系统相关** |
| PERIODIC_TRIGGER | periodic_trigger | 定时触发 | 周期性事件 |

### 事件流向图

```
用户输入 / 环境变化
        ↓
  [Perception Module]
        ↓ PERCEPTION_UPDATED
        ├→ [Memory Module] → MEMORY_CREATED
        ├→ [Emotion Module] → EMOTION_CHANGED
        └→ [Cognition Module]
                ↓ DECISION_MADE
          [Behavior Module]
                ↓ ACTION_EXECUTED / ACTION_FAILED
          [Goal Module] → GOAL_UPDATED / GOAL_COMPLETED
                ↓ GOAL_COMPLETED
          [Emotion Module] → EMOTION_CHANGED
```

---

## 📦 模块详解

### 1. Perception Module (感知模块)

**职责：** 接收和处理外部信息

**订阅事件：**
- `ENVIRONMENT_CHANGED` - 响应环境变化

**发布事件：**
- `PERCEPTION_UPDATED` - 通知其他模块新感知

**核心方法：**
```python
async def perceive_environment(data: Dict) -> None
    # 感知环境信息，发布 PERCEPTION_UPDATED
```

**依赖关系：**
- 独立模块，最上游
- 被其他所有模块依赖（通过事件）

**事件数据格式：**
```python
{
    "perception": {
        "type": "message" / "observation" / "event",
        "source": "user" / "environment",
        "content": {...},
        "timestamp": "..."
    }
}
```

---

### 2. Memory Module (记忆模块)

**职责：** 存储和检索事件记忆与社交记忆

**订阅事件：**
- `PERCEPTION_UPDATED` - 自动记录重要感知
- `ACTION_EXECUTED` - 记录行为历史

**发布事件：**
- `MEMORY_CREATED` - 创建新记忆时
- `MEMORY_RETRIEVED` - 检索记忆时

**核心方法：**
```python
async def store(memory_type: str, content: Dict) -> str
    # 存储记忆，发布 MEMORY_CREATED

async def retrieve(query: Dict, limit: int) -> List[Dict]
    # 检索记忆，发布 MEMORY_RETRIEVED
```

**数据结构：**
```python
EventMemory:
    - memory_id
    - event_type
    - event_summary
    - event_details
    - participants
    - timestamp
    - importance (0-1)
    - tags

SocialMemory:
    - memory_id
    - target_agent_id
    - relationship_strength
    - interaction_count
    - shared_experiences
```

**索引机制：**
- `_event_index`: {tag -> [memory_ids]}
- `_participant_index`: {participant -> [memory_ids]}
- `_social_index`: {agent_id -> memory_id}

---

### 3. Emotion Module (情感模块)

**职责：** 管理情感状态，响应各种刺激

**订阅事件：**
- `GOAL_COMPLETED` - 目标完成触发正面情感
- `GOAL_UPDATED` - 目标更新影响情感
- `PERCEPTION_UPDATED` - 感知触发情感（如用户消息）
- `MEMORY_CREATED` - 记忆创建可能影响情感
- `ENVIRONMENT_CHANGED` - 环境变化触发情感
- `ACTION_FAILED` - 行为失败触发负面情感

**发布事件：**
- `EMOTION_CHANGED` - 情感状态改变
- `MOOD_SHIFTED` - 心情转换

**情感模型 (PAD模型)：**
```python
{
    "valence": float,      # 效价 (-1到1, 负面到正面)
    "arousal": float,      # 唤醒度 (-1到1, 低到高)
    "dominance": float,    # 支配度 (-1到1, 弱到强)
    "primary_emotion": str # 主要情感标签
}
```

**情感映射：**
| Valence | Arousal | Dominance | Emotion |
|---------|---------|-----------|---------|
| + | + | + | happy |
| + | - | + | calm |
| + | + | - | excited |
| - | + | - | angry |
| - | - | - | sad |
| - | + | + | anxious |

**核心方法：**
```python
async def process_emotion(stimulus: Dict) -> None
    # 处理情感刺激，更新状态
    # 刺激类型：achievement, failure, social_interaction, etc.
```

---

### 4. Goal Module (目标模块)

**职责：** 管理目标的创建、更新、完成

**订阅事件：**
- `ACTION_EXECUTED` - 行为执行可能推进目标
- `MEMORY_CREATED` - 记忆创建可能触发目标

**发布事件：**
- `GOAL_CREATED` - 创建新目标
- `GOAL_UPDATED` - 目标更新（进度、优先级等）
- `GOAL_COMPLETED` - 目标完成

**目标数据结构：**
```python
Goal:
    - goal_id
    - title
    - description
    - priority (1-5)
    - status: ACTIVE / PAUSED / COMPLETED / FAILED
    - progress (0-100)
    - created_at
    - deadline (optional)
    - parent_goal_id (optional, 用于子目标)
```

**核心方法：**
```python
async def add_goal(goal_data: Dict) -> str
    # 添加目标，发布 GOAL_CREATED

async def update_goal(goal_id: str, updates: Dict) -> None
    # 更新目标，发布 GOAL_UPDATED

async def complete_goal(goal_id: str) -> None
    # 完成目标，发布 GOAL_COMPLETED
```

---

### 5. Cognition Module (认知模块)

**职责：** 决策中心，整合所有信息进行推理

**订阅事件：**
- `PERCEPTION_UPDATED` - 接收新感知
- `EMOTION_CHANGED` - 考虑情感状态
- `GOAL_UPDATED` - 了解目标变化
- `MEMORY_RETRIEVED` - 利用检索的记忆

**发布事件：**
- `DECISION_MADE` - 做出决策
- `REFLECTION_COMPLETED` - 反思完成

**决策策略：**
1. **reactive** (反应式) - 基于规则快速响应
2. **deliberative** (深思式) - LLM推理决策
3. **hybrid** (混合式) - 结合两者

**核心方法：**
```python
async def decide(context: Dict) -> Dict
    # 做出决策，发布 DECISION_MADE
    # 返回：{action, params, reasoning}

async def reflect(context: Dict) -> Dict
    # 自我反思，发布 REFLECTION_COMPLETED
```

**决策流程：**
```
1. 收集上下文 (ContextManager)
2. 评估当前状态 (情感、目标、记忆)
3. 生成候选行为
4. 评估候选行为
5. 选择最优行为
6. 发布决策事件
```

---

### 6. Behavior Module (行为模块)

**职责：** 执行具体行为

**订阅事件：**
- （通常不订阅，由Cognition模块直接调用）

**发布事件：**
- `ACTION_EXECUTED` - 行为执行成功
- `ACTION_FAILED` - 行为执行失败

**工具系统：**
```python
registered_tools: Dict[str, Tool]
    - send_message: 发送消息
    - update_goal: 更新目标
    - interact_environment: 环境交互
    - retrieve_memory: 检索记忆
```

**核心方法：**
```python
async def execute_action(action: str, params: Dict) -> Any
    # 执行行为，发布 ACTION_EXECUTED 或 ACTION_FAILED
```

---

### 7. Context Manager (上下文管理器)

**职责：** 自动聚合所有模块信息，提供统一上下文

**核心特性：**
- **自动收集**：从所有模块收集最新状态
- **格式化输出**：为LLM格式化上下文
- **按需生成**：支持不同触发场景

**收集的信息：**
```python
{
    "identity": {          # 身份信息
        "agent_id": str,
        "name": str,
        "role": str,
        "personality": str,
        "expertise": List[str]
    },
    "current_state": {     # 当前状态
        "running": bool,
        "created_at": str
    },
    "emotion": {           # 情感状态
        "primary_emotion": str,
        "valence": float,
        "arousal": float,
        "dominance": float
    },
    "memories": {          # 记忆
        "count": int,
        "recent": List[Dict]  # 最近10条
    },
    "goals": {             # 目标
        "count": int,
        "goals": List[Dict]   # 最多5个
    },
    "relationships": {     # 社交关系
        "count": int,
        "recent": List[Dict]
    },
    "perception": {        # 感知
        "last_perceived": Dict
    }
}
```

**核心方法：**
```python
async def get_full_context(trigger: str = None) -> Dict
    # 获取完整上下文

def format_context_for_llm(context: Dict, task: str) -> str
    # 格式化给LLM的文本
```

---

## 🔄 模块交互流程

### 场景1：用户发送消息

```
1. 用户输入 "你好"
   ↓
2. Agent.chat("你好")
   ↓
3. Perception.perceive_environment({type: "message", content: "你好"})
   ↓ 发布 PERCEPTION_UPDATED
   ↓
4. 并行触发：
   ├→ Memory 自动记录感知
   ├→ Emotion 处理用户消息情感 (valence: +0.3, arousal: +0.4)
   └→ Cognition 接收到感知事件
   ↓
5. Cognition.decide()
   - 通过 ContextManager 获取完整上下文
   - 调用 LLM 生成回复
   - 发布 DECISION_MADE
   ↓
6. Behavior.execute_action("send_message", {text: "你好！..."})
   ↓ 发布 ACTION_EXECUTED
   ↓
7. Memory 记录对话到记忆
   ↓ 发布 MEMORY_CREATED
   ↓
8. Goal 检查是否推进目标
   ↓ 可能发布 GOAL_UPDATED
   ↓
9. Emotion 根据目标更新调整情感
   ↓ 可能发布 EMOTION_CHANGED
```

### 场景2：目标完成

```
1. Goal.complete_goal("goal_123")
   ↓ 发布 GOAL_COMPLETED
   ↓
2. 并行触发：
   ├→ Emotion 处理成就情感 (valence: +0.7, arousal: +0.6)
   │  ↓ 发布 EMOTION_CHANGED
   │  ↓
   └→ Memory 记录目标完成事件
      ↓ 发布 MEMORY_CREATED
```

### 场景3：环境变化

```
1. 外部触发环境事件 "突然下雨"
   ↓ 发布 ENVIRONMENT_CHANGED
   ↓
2. 并行触发：
   ├→ Perception 更新感知
   │  ↓ 发布 PERCEPTION_UPDATED
   │  ↓
   └→ Emotion 处理环境变化情感
      ↓ 发布 EMOTION_CHANGED
      ↓
3. Cognition 收到感知更新
   - 评估是否需要采取行动
   - 可能调整当前计划
```

---

## 🧩 模块依赖关系

### 依赖层次（从底层到高层）

```
Level 1 (基础层):
    EventBus (事件总线)

Level 2 (感知和存储层):
    ├─ Perception (感知)
    └─ Memory (记忆)

Level 3 (状态层):
    ├─ Emotion (情感)
    └─ Goal (目标)

Level 4 (决策层):
    Cognition (认知)

Level 5 (执行层):
    Behavior (行为)

Level 6 (聚合层):
    ContextManager (上下文管理)
```

### 模块间通信矩阵

|  | Perception | Memory | Emotion | Goal | Cognition | Behavior |
|---|---|---|---|---|---|---|
| **Perception** | - | → | → | - | → | - |
| **Memory** | ← | - | - | - | → | ← |
| **Emotion** | ← | ← | - | ← | → | ← |
| **Goal** | - | ← | → | - | → | ← |
| **Cognition** | ← | ← | ← | ← | - | → |
| **Behavior** | - | → | → | → | ← | - |

**图例：**
- `→` : 通过事件发送信息
- `←` : 订阅并接收事件
- `-` : 无直接通信

---

## 🎯 关键设计模式

### 1. 观察者模式 (Observer Pattern)

**实现：** EventBus

**优势：**
- 模块解耦
- 易于扩展
- 支持异步

**示例：**
```python
# 订阅
self.subscribe_event(EventType.PERCEPTION_UPDATED, self._on_perception)

# 发布
await self.emit_event(EventType.PERCEPTION_UPDATED, data)
```

### 2. 策略模式 (Strategy Pattern)

**实现：** Cognition 的决策策略

**支持的策略：**
- ReactiveCognition - 反应式
- DeliberativeCognition - 深思式（LLM）
- HybridCognition - 混合式

### 3. 工具模式 (Tool Pattern)

**实现：** Behavior 的工具系统

**工具注册：**
```python
behavior.register_tool("send_message", SendMessageTool())
behavior.register_tool("retrieve_memory", RetrieveMemoryTool())
```

### 4. 单例模式 (Singleton Pattern)

**实现：** LLM连接池、提示词管理器

**优势：**
- 资源共享
- 全局访问
- 连接复用

---

## 💡 关键设计决策

### 1. 为什么使用事件驱动架构？

**优势：**
- ✅ **模块解耦**：模块之间不直接依赖
- ✅ **易于扩展**：新增模块只需订阅相关事件
- ✅ **并发处理**：事件可以并行处理
- ✅ **历史追踪**：事件历史可用于调试

**劣势：**
- ⚠️ **调试困难**：事件流可能复杂
- ⚠️ **性能开销**：事件分发有开销
- ⚠️ **顺序控制**：异步事件顺序难以保证

### 2. 为什么需要 ContextManager？

**背景：** 在V1版本中，每个模块需要手动收集上下文，代码重复且容易遗漏。

**解决方案：**
- 自动从所有模块收集信息
- 统一格式化输出
- 减少重复代码

**效果：**
- 代码减少 70%
- 上下文始终完整
- 易于维护

### 3. 为什么情感模块订阅这么多事件？

**原因：** 情感是对所有刺激的响应

**设计理念：**
- 目标完成 → 快乐
- 行为失败 → 沮丧
- 用户消息 → 社交情感
- 环境变化 → 适应性情感

这符合心理学的情感理论。

---

## 🔧 扩展指南

### 如何添加新模块？

1. **继承 BaseModule**
   ```python
   from agent_system.core.base import BaseModule

   class NewModule(BaseModule):
       async def initialize(self):
           # 订阅事件
           self.subscribe_event(EventType.X, self._handler)

       async def update(self, context):
           # 周期性更新逻辑
           pass
   ```

2. **在 Agent 中注册**
   ```python
   self.new_module = NewModule(agent_id, event_bus)
   await self.new_module.initialize()
   ```

3. **更新 ContextManager**
   ```python
   async def _get_new_module_context(self):
       return self.agent.new_module.get_state()
   ```

### 如何添加新事件？

1. **在 EventType 中添加**
   ```python
   class EventType(Enum):
       NEW_EVENT = "new_event"
   ```

2. **发布事件**
   ```python
   await self.emit_event(EventType.NEW_EVENT, {"data": "..."})
   ```

3. **订阅事件**
   ```python
   self.subscribe_event(EventType.NEW_EVENT, self._on_new_event)
   ```

---

## 📈 性能特性

### 事件处理性能

- **并发执行**：同一事件的所有订阅者并行处理
- **异步IO**：不阻塞主线程
- **异常隔离**：单个订阅者失败不影响其他

### 内存管理

- **事件历史限制**：最多保留1000条
- **记忆容量管理**：超出限制自动删除低重要性记忆
- **记忆遗忘机制**：基于时间和重要性自动遗忘

### 连接池优化

- **LLM连接池**：复用连接，提高并发
- **最大连接数**：10（可配置）
- **超时重试**：3次重试机制

---

## 🎯 总结

### 系统特点

✅ **模块化**：6大核心模块，职责清晰
✅ **事件驱动**：观察者模式，低耦合
✅ **异步架构**：高性能，支持并发
✅ **上下文自动化**：ContextManager 自动聚合
✅ **可扩展**：易于添加新模块和事件
✅ **LLM集成**：认知模块支持多种LLM

### 数据流总结

```
外部输入
  ↓
Perception (感知)
  ↓
Memory (存储) + Emotion (响应)
  ↓
Cognition (决策) ← ContextManager (聚合)
  ↓
Behavior (执行)
  ↓
Goal (更新) → Emotion (反馈)
```

### 下一步优化方向

1. **性能优化**：事件过滤、批量处理
2. **持久化**：保存/加载会话
3. **分布式**：多智能体协作
4. **可观测性**：事件追踪、性能监控
