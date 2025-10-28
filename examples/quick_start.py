"""
智能体系统 - 快速开始示例
这是一个最简单的示例，演示如何创建和使用智能体
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent


async def main():
    print("=" * 60)
    print("智能体系统 - 快速开始")
    print("=" * 60)
    print()

    # 1. 创建智能体
    print("1. 创建智能体...")
    agent = Agent(
        agent_id="agent_001",
        name="助手",
        config={}
    )
    await agent.start()
    print(f"   ✓ 智能体 '{agent.name}' 已创建并启动")
    print()

    # 2. 发送消息
    print("2. 与智能体对话...")
    response = await agent.receive_message(
        sender_id="user",
        message="你好！",
        metadata={}
    )
    print(f"   用户: 你好！")
    print(f"   智能体: {response}")
    print()

    # 3. 查看智能体状态
    print("3. 查看智能体状态...")
    status = agent.get_status()
    print(f"   运行状态: {status['running']}")
    print(f"   智能体ID: {status['agent_id']}")
    print(f"   名称: {status['name']}")
    print()

    # 4. 查看情感状态
    print("4. 查看情感状态...")
    emotion = agent.emotion.get_current_emotion()
    print(f"   当前情感: {emotion.get('primary_emotion', 'neutral')}")
    print(f"   情感效价: {emotion.get('valence', 0.0):.2f}")
    print()

    # 5. 添加目标
    print("5. 添加目标...")
    goal_id = await agent.add_goal({
        "title": "学习使用智能体系统",
        "description": "了解智能体的基本功能",
        "priority": 2  # 1=低, 2=中, 3=高
    })
    print(f"   ✓ 目标已添加 (ID: {goal_id[:8]}...)")
    print()

    # 6. 查看目标
    print("6. 查看活跃目标...")
    goals = agent.goal.get_active_goals()
    print(f"   活跃目标数: {len(goals)}")
    if goals:
        for goal in goals:
            print(f"   - {goal.title} (优先级: {goal.priority})")
    print()

    # 7. 存储记忆
    print("7. 存储记忆...")
    await agent.memory.store("event", {
        "event_summary": "与用户对话",
        "event_details": f"用户说：你好！ 回复：{response}",
        "participants": ["user", agent.agent_id],
        "importance": 0.5
    })
    print(f"   ✓ 事件记忆已存储")
    print()

    # 8. 查看记忆统计
    print("8. 查看记忆统计...")
    status = agent.get_status()
    mem_stats = status['modules']['memory']
    print(f"   事件记忆数: {mem_stats.get('event_memories_count', 0)}")
    print(f"   社交记忆数: {mem_stats.get('social_memories_count', 0)}")
    print()

    # 9. 停止智能体
    print("9. 停止智能体...")
    await agent.stop()
    print(f"   ✓ 智能体已停止")
    print()

    print("=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
