"""
多智能体示例
演示如何使用AgentManager管理多个智能体
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.models.goal_models import GoalPriority


async def main():
    """主函数"""
    print("=== 多智能体系统示例 ===\n")

    # 1. 创建智能体管理器
    print("1. 创建智能体管理器...")
    manager = AgentManager(max_agents=10)
    print(f"   管理器已创建，最大智能体数: 10\n")

    # 2. 创建多个智能体
    print("2. 创建多个智能体...")
    agents = []

    # 创建Alice
    alice = await manager.create_agent(
        agent_id="alice",
        name="Alice",
        config={"max_memories": 500}
    )
    agents.append(alice)
    print("   - Alice 已创建并启动")

    # 创建Bob
    bob = await manager.create_agent(
        agent_id="bob",
        name="Bob",
        config={"max_memories": 500}
    )
    agents.append(bob)
    print("   - Bob 已创建并启动")

    # 创建Charlie
    charlie = await manager.create_agent(
        agent_id="charlie",
        name="Charlie",
        config={"max_memories": 500}
    )
    agents.append(charlie)
    print("   - Charlie 已创建并启动\n")

    # 3. 为每个智能体添加目标
    print("3. 为智能体添加目标...")
    await alice.add_goal({
        "title": "完成项目报告",
        "description": "在本周内完成项目进度报告",
        "priority": GoalPriority.HIGH.value
    })
    print("   - Alice: 完成项目报告")

    await bob.add_goal({
        "title": "组织团队会议",
        "description": "安排下周的团队会议",
        "priority": GoalPriority.MEDIUM.value
    })
    print("   - Bob: 组织团队会议")

    await charlie.add_goal({
        "title": "代码审查",
        "description": "审查团队成员的代码提交",
        "priority": GoalPriority.MEDIUM.value
    })
    print("   - Charlie: 代码审查\n")

    # 4. 智能体间通信
    print("4. 智能体间通信...")

    # Alice 向 Bob 发送消息
    print("   Alice -> Bob: '嗨Bob，项目报告需要你的数据'")
    response = await manager.send_message(
        sender_id="alice",
        target_id="bob",
        message="嗨Bob，项目报告需要你的数据"
    )
    print(f"   Bob 的响应: {response.get('response', response)}\n")

    # 5. 广播消息
    print("5. Alice 向所有人广播消息...")
    responses = await manager.broadcast_message(
        sender_id="alice",
        message="大家好！下午3点开会讨论项目进展。"
    )
    print(f"   收到 {len(responses)} 个响应")
    for agent_id, response in responses.items():
        print(f"   - {agent_id}: {response.get('acknowledged', 'No response')}\n")

    # 6. 广播环境更新
    print("6. 广播环境更新...")
    await manager.broadcast_environment_update({
        "event": "meeting_scheduled",
        "time": "15:00",
        "location": "会议室A"
    })
    print("   所有智能体已感知到环境变化\n")

    # 7. 查看管理器状态
    print("7. 查看管理器状态...")
    status = manager.get_status()
    print(f"   智能体数量: {status['agent_count']}")
    print(f"   总消息路由数: {status['stats']['total_messages_routed']}")
    print(f"   智能体列表:")
    for agent_id, agent_info in status['agents'].items():
        print(f"     - {agent_id}: {agent_info['name']} (运行中: {agent_info['running']})\n")

    # 8. 获取详细状态（包含所有智能体的详细信息）
    print("8. 查看各智能体详细状态...")
    detailed_status = manager.get_detailed_status()
    for agent_id, agent_status in detailed_status['agents'].items():
        print(f"   {agent_id} ({agent_status['name']}):")
        modules = agent_status['modules']
        print(f"     - 活跃目标: {len(modules['goal']['active_goals'])}")
        print(f"     - 事件记忆: {modules['memory']['event_memories_count']}")
        print(f"     - 当前情感: {modules['emotion']['current_emotion']['primary_emotion']}")
        print()

    # 9. 模拟运行一段时间
    print("9. 模拟运行一段时间（5秒）...")
    print("   （在实际应用中，调度器会自动触发定期更新）")
    await asyncio.sleep(5)
    print("   运行完成\n")

    # 10. 停止所有智能体
    print("10. 停止所有智能体...")
    await manager.stop_all()
    print("   所有智能体已停止\n")

    print("=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
