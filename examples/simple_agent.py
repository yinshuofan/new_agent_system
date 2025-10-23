"""
简单智能体示例
演示如何创建和使用单个智能体
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import Agent
from agent_system.models.goal_models import GoalPriority, NeedType
from agent_system.models.emotion_models import BasicEmotion
from agent_system.scheduler.trigger import AgentScheduler


async def main():
    """主函数"""
    print("=== 智能体系统示例 ===\n")

    # 1. 创建智能体
    print("1. 创建智能体...")
    agent = Agent(
        agent_id="agent_001",
        name="Alice",
        config={
            "max_memories": 500
        }
    )

    # 启动智能体
    await agent.start()
    print(f"   智能体 '{agent.name}' 已启动\n")

    # 2. 设置初始目标
    print("2. 添加目标...")
    goal_id = await agent.add_goal({
        "title": "学习Python编程",
        "description": "通过学习和实践掌握Python编程技能",
        "priority": GoalPriority.HIGH.value,
        "related_needs": [NeedType.SELF_ACTUALIZATION.value]
    })
    print(f"   目标已添加，ID: {goal_id}\n")

    # 3. 激活目标
    await agent.goal.activate_goal(goal_id)
    print("   目标已激活\n")

    # 4. 模拟接收消息
    print("3. 模拟接收消息...")
    response = await agent.receive_message(
        sender_id="user_001",
        message="你好，Alice！今天学习进展如何？",
        metadata={"type": "greeting"}
    )
    print(f"   智能体响应: {response}\n")

    # 5. 添加记忆
    print("4. 添加事件记忆...")
    memory_id = await agent.memory.store("event", {
        "event_summary": "学习了Python基础语法",
        "event_details": "今天学习了变量、数据类型、控制流等基础知识",
        "participants": ["Alice"],
        "emotion_valence": 0.7,
        "emotion_arousal": 0.6,
        "importance": 0.8,
        "tags": ["学习", "Python", "编程"],
        "related_goals": [goal_id]
    })
    print(f"   记忆已存储，ID: {memory_id}\n")

    # 6. 检索记忆
    print("5. 检索相关记忆...")
    memories = await agent.memory.retrieve({
        "keywords": ["Python"],
        "memory_type": "event"
    }, limit=3)
    print(f"   检索到 {len(memories)} 条记忆\n")

    # 7. 更新目标进度
    print("6. 更新目标进度...")
    await agent.goal.update_goal_progress(goal_id, 0.3)
    print("   目标进度: 30%\n")

    # 8. 查看情感状态
    print("7. 查看情感状态...")
    emotion = agent.emotion.get_current_emotion()
    print(f"   当前情感: {emotion.get('primary_emotion')}")
    print(f"   情感效价: {emotion.get('valence'):.2f}")
    print(f"   唤醒度: {emotion.get('arousal'):.2f}\n")

    # 9. 查看智能体完整状态
    print("8. 查看智能体状态...")
    status = agent.get_status()
    print(f"   运行状态: {status['running']}")
    print(f"   活跃目标数: {len(status['modules']['goal']['active_goals'])}")
    print(f"   事件记忆数: {status['modules']['memory']['event_memories_count']}")
    print(f"   社交记忆数: {status['modules']['memory']['social_memories_count']}\n")

    # 10. 模拟环境变化
    print("9. 模拟环境变化...")
    await agent.perceive_environment({
        "time": "morning",
        "weather": "sunny",
        "location": "home"
    })
    print("   环境感知已更新\n")

    # 11. 处理一次tick（更新所有模块）
    print("10. 执行一次tick更新...")
    await agent.process_tick()
    print("   所有模块已更新\n")

    # 12. 停止智能体
    print("11. 停止智能体...")
    await agent.stop()
    print("   智能体已停止\n")

    print("=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
