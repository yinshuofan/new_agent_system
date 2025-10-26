"""
测试chat上下文修复
验证AI是否知道自己的日程和状态
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm.prompt_manager import initialize_prompts
from datetime import datetime


async def test_chat_context():
    """测试对话上下文"""
    print("="*70)
    print("测试AI对话上下文感知")
    print("="*70)
    print()

    # 初始化
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    initialize_prompts(prompts_path)
    print("✓ 提示词已加载")

    # 创建管理器和智能体
    manager = AgentManager(max_agents=5)
    agent = await manager.create_agent(
        agent_id="test_agent",
        name="TestBot",
        config={"role": "测试助手", "personality": "友好、乐于助人"},
        use_llm=False
    )
    print(f"✓ 智能体 '{agent.name}' 已创建")

    # 创建剧情引擎
    story_engine = StoryEngine(
        story_mode=StoryMode.GUIDED,
        use_llm=False,
        deviation_threshold=0.6
    )
    await story_engine.initialize()
    story_engine.register_agent(agent)
    agent.story_engine = story_engine
    print("✓ 剧情引擎已创建")

    # 生成日程
    await story_engine.generate_story_outline(
        theme="测试一天",
        agent_characters=[
            {"agent_id": "test_agent", "name": "TestBot", "role": "测试员"}
        ],
        custom_plot_points=[
            "08:00 起床并准备新的一天",
            "12:00 午餐时间",
            "15:00 下午工作",
            "18:00 晚餐时间",
            "22:00 准备休息"
        ]
    )
    await story_engine.generate_agent_schedule("test_agent", agent)
    print("✓ 日程已生成")

    # 测试获取上下文
    print("\n" + "-"*70)
    print("测试上下文构建:")
    print("-"*70)

    schedule = story_engine.get_agent_schedule("test_agent")
    print(f"1. 日程项数: {len(schedule.schedule_items)}")

    current_item = schedule.get_current_activity(datetime.now())
    if current_item:
        print(f"2. 当前活动: {current_item.activity}")
    else:
        print("2. 当前活动: 无")

    emotion = agent.emotion.get_current_emotion()
    print(f"3. 情绪状态: {emotion.get('primary_emotion', 'neutral')}")

    goals = agent.goal.get_active_goals()
    print(f"4. 活跃目标数: {len(goals)}")

    # 添加一个测试目标
    await agent.add_goal({
        "title": "完成测试",
        "description": "验证上下文功能",
        "priority": 1  # 1=HIGH, 2=MEDIUM, 3=LOW, 4=OPTIONAL
    })
    goals = agent.goal.get_active_goals()
    print(f"5. 添加目标后: {len(goals)}个目标")

    # 测试对话（模拟）
    print("\n测试对话上下文构建:")

    # 构建完整上下文（模拟chat方法中的逻辑）
    current_time = datetime.now()
    schedule_context = ""
    if schedule:
        current_item = schedule.get_current_activity(current_time)
        if current_item:
            schedule_context = f"我现在正在: {current_item.activity}"
        else:
            schedule_context = "我现在空闲中"

        schedule_context += f"\n今天的日程:\n"
        for item in schedule.schedule_items[:3]:
            status = "✓" if item.status.value == "completed" else "○"
            schedule_context += f"  {status} {item.start_time}: {item.activity}\n"

    print(f"\n日程上下文:\n{schedule_context}")

    role = agent.config.get("role", "")
    personality = agent.config.get("personality", "")
    print(f"\n角色信息: {role}")
    print(f"性格特点: {personality}")

    goals_text = "\n".join([f"  - {g.get('title', 'N/A')}" for g in goals])
    print(f"\n目标列表:\n{goals_text}")

    print("\n" + "-"*70)
    print("✓ 上下文构建测试完成")
    print("-"*70)
    print()

    # 清理
    await manager.stop_all()
    print("✓ 测试完成\n")


if __name__ == "__main__":
    asyncio.run(test_chat_context())
