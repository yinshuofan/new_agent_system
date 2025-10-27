# 超长期剧情配置方案

## 问题分析

### 当前配置方式的局限性

**现有方式（multi_day_timeline）：**
```yaml
multi_day_timeline:
  day_1:
    events:
      - time: "09:00"
        title: "事件1"
      - time: "10:00"
        title: "事件2"
  day_2:
    events: [...]
  day_3:
    events: [...]
```

**问题：**
1. ❌ **可扩展性差**：配置100天需要100个day_N配置块
2. ❌ **维护困难**：几千天的配置文件将达到数万行
3. ❌ **缺乏灵活性**：无法根据智能体行为动态调整剧情
4. ❌ **重复内容多**：日常重复活动需要每天重写

---

## 解决方案：混合式剧情配置系统

### 设计思路

支持**三层配置结构**：
1. **长期大纲层**（Long-term Outline）：定义整体故事弧线
2. **规则模板层**（Rule Templates）：定义日常活动模式
3. **动态生成层**（Dynamic Generation）：LLM实时生成具体内容

---

## 方案一：规则驱动 + 模板系统

适用于：日常生活模拟、长期RPG、社交模拟

### 配置结构

```yaml
metadata:
  title: "现代生活模拟"
  start_date: "2025-01-01"
  duration_days: 1000  # 支持1000天！

# 1. 日常活动模板
daily_templates:
  weekday_routine:
    applicable_days: [1, 2, 3, 4, 5]  # 周一到周五
    events:
      - time: "07:00"
        activity: "wake_up"
        location: "home"
      - time: "08:00-12:00"
        activity: "work"
        location: "office"
      - time: "12:00-13:00"
        activity: "lunch"
        location: "restaurant"
      - time: "13:00-18:00"
        activity: "work"
        location: "office"
      - time: "19:00-22:00"
        activity: "free_time"
        location: "home"

  weekend_routine:
    applicable_days: [6, 7]  # 周六周日
    events:
      - time: "09:00"
        activity: "wake_up"
      - time: "10:00-18:00"
        activity: "leisure"
      - time: "19:00-22:00"
        activity: "free_time"

# 2. 故事阶段（覆盖日常模板）
story_phases:
  phase_1:
    day_range: [1, 100]
    theme: "新人入职"
    key_events:
      - trigger_day: 1
        event: "first_day_at_work"
      - trigger_day: 7
        event: "first_week_review"
      - trigger_day: 30
        event: "monthly_evaluation"

  phase_2:
    day_range: [101, 300]
    theme: "职场成长"
    key_events:
      - trigger_day: 150
        event: "promotion_opportunity"
      - trigger_day: 200
        event: "major_project"

  phase_3:
    day_range: [301, 1000]
    theme: "事业巅峰"
    random_events:
      - event: "business_trip"
        probability: 0.1  # 10%概率
      - event: "important_meeting"
        probability: 0.2

# 3. 动态事件规则
event_generation_rules:
  social_events:
    frequency: "weekly"
    types: ["party", "gathering", "date"]

  work_events:
    frequency: "daily"
    types: ["meeting", "deadline", "collaboration"]

  random_encounters:
    probability: 0.05  # 每天5%概率
    types: ["chance_meeting", "accident", "opportunity"]

# 4. LLM生成配置
llm_generation:
  enabled: true
  generate_on_demand: true  # 按需生成，而非预生成
  context_window: 7  # 考虑过去7天的上下文
```

### 优势

- ✅ **高度压缩**：1000天配置仅需几百行
- ✅ **易于维护**：修改模板即可影响所有相关日期
- ✅ **灵活性强**：规则组合产生丰富变化
- ✅ **可扩展**：轻松扩展到10000天

---

## 方案二：LLM动态生成系统

适用于：开放世界、动态剧情、玩家驱动的故事

### 配置结构

```yaml
metadata:
  title: "开放世界冒险"
  start_date: "2025-01-01"
  mode: "dynamic"  # 动态模式
  max_duration_days: 10000  # 理论上限

# 世界设定
world_setting:
  genre: "fantasy_adventure"
  world_state:
    location: "大陆中心"
    era: "魔法时代"
    conflicts: ["王国战争", "魔物入侵"]

# 角色目标
character_goals:
  protagonist:
    long_term_goal: "成为传奇冒险者"
    milestones:
      - "到达Lv 10"
      - "击败第一个Boss"
      - "建立公会"
      - "拯救王国"

# 剧情生成策略
story_generation:
  strategy: "milestone_driven"  # 里程碑驱动

  daily_content:
    method: "llm_generate"
    prompt_template: |
      基于以下信息生成今天的剧情：
      - 当前日期：{current_day}
      - 角色状态：{character_state}
      - 最近7天事件：{recent_events}
      - 下一个里程碑：{next_milestone}

      生成3-5个今日事件，包括时间、地点、内容。

  event_types:
    - type: "main_quest"
      frequency: "milestone_based"
    - type: "side_quest"
      frequency: "random"
      probability: 0.3
    - type: "daily_life"
      frequency: "always"

# 缓存策略（性能优化）
caching:
  pregenerate_days: 7  # 提前生成7天
  cache_generated_content: true
  regenerate_on_deviation: true  # 剧情偏离时重新生成
```

### 优势

- ✅ **无限扩展**：理论上支持任意天数
- ✅ **高度动态**：根据玩家行为实时调整
- ✅ **零预配置**：只需世界设定，无需详细剧本
- ✅ **智能连贯**：LLM保证剧情连贯性

---

## 方案三：混合式系统（推荐）

结合方案一和方案二的优点

### 配置结构

```yaml
metadata:
  title: "侦探事务所模拟"
  start_date: "2025-01-01"
  duration_days: 365
  mode: "hybrid"  # 混合模式

# 基础日常（模板）
daily_routines:
  detective_daily:
    events:
      - time_range: "08:00-09:00"
        activity: "morning_preparation"
        template: true
      - time_range: "09:00-18:00"
        activity: "office_hours"
        template: true
        dynamic_content: "case_work"  # 动态内容插入点
      - time_range: "18:00-22:00"
        activity: "evening_free"
        template: true

# 案件系统（规则生成）
case_system:
  case_frequency: "weekly"  # 每周一个案件

  case_templates:
    - type: "theft"
      duration_days: [3, 7]  # 3-7天
      difficulty: "medium"

    - type: "murder"
      duration_days: [7, 14]
      difficulty: "hard"

    - type: "missing_person"
      duration_days: [5, 10]
      difficulty: "medium"

  case_generation:
    method: "llm"
    prompt: "生成一个{type}案件，持续{duration}天"

# 长期剧情线（手动配置关键节点）
story_arcs:
  arc_1:
    title: "神秘组织浮现"
    day_range: [1, 100]
    key_moments:
      - day: 1
        event: "接手事务所"
      - day: 30
        event: "发现可疑线索"
      - day: 100
        event: "初次接触神秘组织"

  arc_2:
    title: "深入调查"
    day_range: [101, 250]
    key_moments:
      - day: 150
        event: "重大突破"
      - day: 250
        event: "揭露部分真相"

  arc_3:
    title: "最终对决"
    day_range: [251, 365]
    key_moments:
      - day: 300
        event: "准备行动"
      - day: 365
        event: "大结局"

# 动态填充规则
dynamic_filling:
  enabled: true
  fill_method: "llm_on_demand"

  # 当到达某一天时，基于以下上下文生成内容
  generation_context:
    - recent_events: 14  # 最近14天
    - character_state: true
    - story_arc_progress: true
    - active_cases: true
```

### 实现逻辑

```python
class HybridStoryEngine:
    def get_day_schedule(self, day_number: int):
        # 1. 加载日常模板
        schedule = self.load_daily_routine(day_number)

        # 2. 检查是否有关键剧情节点
        key_event = self.get_key_event(day_number)
        if key_event:
            schedule.insert_event(key_event)

        # 3. 检查活跃案件
        active_cases = self.get_active_cases(day_number)
        for case in active_cases:
            case_events = self.generate_case_events(case, day_number)
            schedule.merge_events(case_events)

        # 4. LLM填充动态内容
        if self.config.dynamic_filling.enabled:
            context = self.build_context(day_number)
            dynamic_events = self.llm_generate_events(context)
            schedule.merge_events(dynamic_events)

        return schedule
```

---

## 性能对比

| 方案 | 1000天配置大小 | 维护难度 | 灵活性 | 性能消耗 |
|------|---------------|---------|--------|---------|
| 当前方式 | ~50,000行 | 极高 | 低 | 低 |
| 规则驱动 | ~500行 | 低 | 中 | 低 |
| LLM动态 | ~200行 | 极低 | 极高 | 高（可缓存） |
| 混合式 | ~800行 | 低 | 高 | 中 |

---

## 推荐实施方案

### 短期（立即可用）：优化现有系统
- 添加日常模板支持
- 允许引用和复用事件块

### 中期（1-2周）：规则驱动系统
- 实现 daily_templates
- 实现 story_phases
- 实现事件规则引擎

### 长期（1个月）：完整混合系统
- LLM动态生成
- 智能缓存机制
- 上下文感知的剧情调整

---

## 结论

### 问题答案：当前配置方式能否支持几百/几千天？

**简短答案：❌ 不能**

当前的 multi_day_timeline 配置方式：
- **理论上可以**：通过复制粘贴写几千个 day_N 块
- **实际上不可行**：配置文件将达到数十万行，完全无法维护

### 推荐方案

使用 **混合式系统（方案三）**：
- ✅ 支持 1000+ 天剧情
- ✅ 配置文件仅需 500-1000 行
- ✅ 易于维护和扩展
- ✅ 兼顾性能和灵活性

下一步我将实现这个系统的核心功能。
