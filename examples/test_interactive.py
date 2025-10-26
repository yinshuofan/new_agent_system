"""
测试交互式智能体的基本功能
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm.prompt_manager import initialize_prompts
from datetime import time


class InteractiveAgent:
    """交互式智能体包装器"""

    def __init__(self, agent, story_engine=None):
        self.agent = agent
        self.story_engine = story_engine
        self.running = False
        self.sleep_start_time = time(22, 0)
        self.wake_up_time = time(7, 0)

    def is_sleeping(self) -> bool:
        """检查智能体是否在睡觉"""
        from datetime import datetime
        current_time = datetime.now().time()
        if self.sleep_start_time > self.wake_up_time:
            return current_time >= self.sleep_start_time or current_time < self.wake_up_time
        else:
            return self.sleep_start_time <= current_time < self.wake_up_time

    def get_current_activity(self) -> str:
        """获取当前活动"""
        if self.is_sleeping():
            return "💤 睡觉中"

        if self.story_engine:
            activity = self.story_engine.get_current_activity(self.agent.agent_id)
            if activity:
                return f"📋 {activity}"

        return "🕐 空闲中"


async def test_basic_functionality():
    """测试基本功能"""
    print("="*70)
    print("测试交互式智能体基本功能")
    print("="*70)
    print()

    # 初始化提示词
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    initialize_prompts(prompts_path)
    print("✓ 提示词已加载")

    # 创建智能体
    manager = AgentManager(max_agents=5)
    agent = await manager.create_agent(
        agent_id="test_agent",
        name="TestAgent",
        config={},
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
    print("✓ 剧情引擎已创建")

    # 生成日程
    await story_engine.generate_story_outline(
        theme="日常测试",
        agent_characters=[
            {"agent_id": "test_agent", "name": "TestAgent", "role": "测试员"}
        ],
        custom_plot_points=[
            "08:00 起床测试",
            "12:00 午餐测试",
            "18:00 晚餐测试",
            "22:00 睡觉测试"
        ]
    )
    print("✓ 剧情大纲已生成")

    await story_engine.generate_agent_schedule("test_agent", agent)
    print("✓ 日程已生成")

    # 创建交互式包装器
    interactive_agent = InteractiveAgent(agent, story_engine)
    print("✓ 交互式包装器已创建")

    # 测试功能
    print("\n" + "-"*70)
    print("测试功能:")
    print(f"1. 当前是否睡觉: {interactive_agent.is_sleeping()}")
    print(f"2. 当前活动: {interactive_agent.get_current_activity()}")

    schedule = story_engine.get_agent_schedule("test_agent")
    if schedule:
        print(f"3. 日程项数: {len(schedule.schedule_items)}")
        print(f"4. 整体对齐度: {schedule.overall_alignment:.2f}")

    print("-"*70)
    print()

    # 清理
    await manager.stop_all()
    print("✓ 测试完成\n")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
