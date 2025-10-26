"""
快速开始示例
演示如何用最少的代码创建故事智能体并进行交互

使用简化的API，只需几行代码即可创建完整的故事智能体系统
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system.story import create_story_agents


async def main():
    """主函数 - 演示最简单的使用方式"""
    print("=" * 70)
    print("📖 快速开始：福尔摩斯侦探故事")
    print("=" * 70)
    print()

    # 1️⃣ 用一行代码创建所有智能体！
    print("🚀 创建智能体...")
    agents = await create_story_agents(
        story_config_path="/home/user/new_agent_system/config/holmes_story.yaml",
        use_llm=False  # 设置为True可使用真实LLM
    )
    print(f"✓ 创建了 {len(agents)} 个智能体: {list(agents.keys())}")
    print()

    # 2️⃣ 获取智能体
    holmes = agents["holmes"]
    watson = agents["watson"]

    # 3️⃣ 直接对话！
    print("💬 与福尔摩斯对话:")
    print("-" * 70)

    user_message = "你好，福尔摩斯先生！听说你接了一个新案件？"
    print(f"用户: {user_message}")

    reply = await holmes.chat(user_message)
    print(f"福尔摩斯: {reply}")
    print()

    # 4️⃣ 查看智能体状态
    print("📊 智能体状态:")
    print("-" * 70)

    # 获取完整上下文
    context = await holmes.context_manager.get_full_context()

    print(f"角色: {context['identity']['name']}")
    print(f"职业: {context['identity']['role']}")
    print(f"情感: {context['emotion']['primary_emotion']}")

    # 目标
    if context['goals']['goals']:
        print(f"目标: {context['goals']['goals'][0]['title']}")

    # 记忆
    print(f"记忆数量: {context['memories']['count']}")
    if context['memories']['recent']:
        latest = context['memories']['recent'][0]
        print(f"最新记忆: {latest['summary']}")

    print()

    # 5️⃣ 再对话几轮
    print("💬 继续对话:")
    print("-" * 70)

    messages = [
        "能告诉我案件的细节吗？",
        "你觉得谁是嫌疑人？",
        "华生医生现在在做什么？"
    ]

    for msg in messages:
        print(f"\n用户: {msg}")
        reply = await holmes.chat(msg)
        print(f"福尔摩斯: {reply}")

    print()

    # 6️⃣ 查看更新后的记忆
    print("🧠 对话后的记忆:")
    print("-" * 70)

    # 重新获取上下文
    context = await holmes.context_manager.get_full_context()
    print(f"总记忆数: {context['memories']['count']}")

    # 显示最近3条记忆
    for i, mem in enumerate(context['memories']['recent'][:3], 1):
        print(f"{i}. {mem['summary']}")
        if mem.get('event_type') == 'conversation':
            print(f"   类型: 对话")

    print()

    # 7️⃣ 清理
    print("🧹 清理资源...")
    for agent in agents.values():
        await agent.stop()
    print("✓ 完成")
    print()

    print("=" * 70)
    print("✅ 示例完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
