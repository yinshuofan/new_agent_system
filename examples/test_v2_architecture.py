"""
测试V2架构
验证：
1. ContextManager功能
2. StoryLoader功能
3. YAML配置加载
4. 完整流程
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryLoader
from agent_system.llm.prompt_manager import initialize_prompts
from datetime import datetime


async def test_story_loader():
    """测试剧情加载器"""
    print("="*70)
    print("测试 StoryLoader")
    print("="*70)
    print()

    # 加载配置
    config_path = "/home/user/new_agent_system/config/holmes_story.yaml"
    print(f"📖 加载配置: {config_path}")

    try:
        story_config = StoryLoader.load_from_file(config_path)
        print("✓ 配置加载成功")
        print(f"  标题: {story_config.title}")
        print(f"  主题: {story_config.theme}")
        print(f"  角色数: {len(story_config.characters)}")
        print(f"  事件数: {len(story_config.timeline)}")
        print()

        # 测试角色配置
        print("👥 角色信息:")
        for char_id, char_data in story_config.characters.items():
            print(f"  - {char_id}: {char_data.get('name')} ({char_data.get('role')})")
        print()

        # 测试时间线
        print("📅 前3个事件:")
        for event in story_config.timeline[:3]:
            print(f"  - {event.get('time')} {event.get('title')}")
        print()

        # 测试剧情大纲生成
        print("📝 生成剧情大纲...")
        outline = StoryLoader.create_story_outline_from_config(story_config)
        print(f"✓ 大纲标题: {outline.title}")
        print(f"✓ 剧情点数: {len(outline.main_plot_points)}")
        print()

        # 测试日程生成
        print("📅 生成角色日程...")
        schedule = StoryLoader.generate_schedule_from_config(story_config, "holmes")
        print(f"✓ 福尔摩斯日程: {len(schedule.schedule_items)}个活动")
        for item in schedule.schedule_items[:3]:
            print(f"  - {item.start_time}: {item.activity}")
        print()

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_manager():
    """测试上下文管理器"""
    print("="*70)
    print("测试 ContextManager")
    print("="*70)
    print()

    # 初始化提示词
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    initialize_prompts(prompts_path)

    # 创建智能体
    manager = AgentManager(max_agents=5)
    agent = await manager.create_agent(
        agent_id="test_agent",
        name="TestBot",
        config={
            "role": "测试助手",
            "personality": "友好、乐于助人",
            "expertise": ["测试", "调试"]
        },
        use_llm=False
    )

    print(f"✓ 智能体 '{agent.name}' 已创建")
    print(f"✓ ContextManager 已初始化: {agent.context_manager is not None}")
    print()

    # 获取完整上下文
    print("📋 获取完整上下文...")
    context = await agent.context_manager.get_full_context(trigger="test")
    print(f"✓ 上下文包含的键:")
    for key in context.keys():
        print(f"  - {key}")
    print()

    # 格式化上下文
    print("📝 格式化上下文为LLM文本...")
    formatted = agent.context_manager.format_context_for_llm(context, "chat")
    print("✓ 格式化完成，前200字符:")
    print(formatted[:200])
    print("...")
    print()

    # 添加一些数据后再次测试
    print("📝 添加目标和记忆后再次测试...")
    await agent.add_goal({
        "title": "完成测试",
        "description": "测试上下文管理器",
        "priority": 1
    })

    await agent.memory.store("event", {
        "event_type": "test",
        "event_summary": "测试事件1",
        "event_details": "这是一个测试事件",
        "timestamp": datetime.now().isoformat()
    })

    # 再次获取上下文
    context2 = await agent.context_manager.get_full_context(trigger="test2")
    print(f"✓ 目标数: {context2['goals']['count']}")
    print(f"✓ 记忆数: {context2['memories']['count']}")
    print()

    await manager.stop_all()
    return True


async def test_integration():
    """集成测试"""
    print("="*70)
    print("集成测试")
    print("="*70)
    print()

    print("📖 加载剧情配置...")
    config_path = "/home/user/new_agent_system/config/holmes_story.yaml"
    story_config = StoryLoader.load_from_file(config_path)
    print("✓ 配置已加载")
    print()

    print("👥 创建智能体...")
    manager = AgentManager(max_agents=5)

    holmes = await manager.create_agent(
        agent_id="holmes",
        name="Sherlock Holmes",
        config=story_config.get_character_config("holmes"),
        use_llm=False
    )
    print("✓ 福尔摩斯已创建")
    print()

    print("📋 测试上下文获取...")
    context = await holmes.context_manager.get_full_context()
    print(f"✓ 角色: {context['identity']['role']}")
    print(f"✓ 性格: {context['identity']['personality'][:50]}...")
    print()

    print("📝 格式化上下文...")
    formatted = holmes.context_manager.format_context_for_llm(context, "chat")
    lines = formatted.split('\n')
    print("前10行:")
    for line in lines[:10]:
        print(f"  {line}")
    print()

    await manager.stop_all()
    return True


async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("V2架构测试套件")
    print("="*70)
    print()

    results = []

    # 测试1: StoryLoader
    print("\n【测试1】StoryLoader")
    result1 = await test_story_loader()
    results.append(("StoryLoader", result1))

    # 测试2: ContextManager
    print("\n【测试2】ContextManager")
    result2 = await test_context_manager()
    results.append(("ContextManager", result2))

    # 测试3: 集成测试
    print("\n【测试3】集成测试")
    result3 = await test_integration()
    results.append(("Integration", result3))

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    print()

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")
    print()


if __name__ == "__main__":
    asyncio.run(main())
