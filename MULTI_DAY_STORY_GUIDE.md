# 多天剧情配置方案

## 方案说明

这个配置允许定义跨越多天的剧情，每天都有独立的时间线和事件。

## 配置格式

### 1. 基础结构

```yaml
metadata:
  title: "故事标题"
  theme: "故事主题"
  start_date: "2025-10-26"  # 开始日期
  duration_days: 3           # 持续天数

# 角色定义（所有天共享）
characters:
  hero:
    name: "主角"
    role: "角色"
    # ...

# 多天时间线
multi_day_timeline:
  # 第一天
  day_1:
    date: "2025-10-26"
    title: "第一天：开始"
    events:
      - time: "09:00"
        title: "事件1"
        # ...

  # 第二天
  day_2:
    date: "2025-10-27"
    title: "第二天：发展"
    events:
      - time: "09:00"
        title: "事件2"
        # ...

# 故事设置
story_settings:
  auto_progress_to_next_day: true  # 自动推进到下一天
  day_transition_time: "22:00"     # 转天时间
```

### 2. 使用相对日期

```yaml
multi_day_timeline:
  day_1:
    date_offset: 0  # 从start_date开始
    title: "第一天"
    events: [...]

  day_2:
    date_offset: 1  # start_date + 1天
    title: "第二天"
    events: [...]
```

### 3. 条件分支（可选）

```yaml
multi_day_timeline:
  day_2:
    date_offset: 1
    conditions:
      - if: "day_1.event_completed['find_clue']"
        then: "day_2_path_a"
        else: "day_2_path_b"
```

## 完整示例

见 `config/multi_day_story_example.yaml`
