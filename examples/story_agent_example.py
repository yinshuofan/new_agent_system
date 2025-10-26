"""
剧情演绎示例
演示智能体如何在剧情中进行角色扮演
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig
from agent_system.llm.prompt_manager import initialize_prompts
from agent_system.models.goal_models import GoalPriority


async def main():
    """主函数"""
    print("=== 剧情演绎示例 ===\n")

    # 1. 初始化LLM（可选）
    print("1. 初始化系统...")
    api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    use_llm = api_key != "demo-key"

    if use_llm:
        try:
            llm_config = LLMConfig(api_key=api_key, max_connections=5)
            await initialize_llm(llm_config)
            print("   LLM已初始化")
        except:
            use_llm = False
            print("   LLM初始化失败，使用无LLM模式")

    # 加载提示词
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    if os.path.exists(prompts_path):
        initialize_prompts(prompts_path)
    print()

    # 2. 创建剧情引擎
    print("2. 创建剧情引擎...")
    story_engine = StoryEngine(
        story_mode=StoryMode.GUIDED,
        use_llm=use_llm
    )
    await story_engine.initialize()
    print("   剧情引擎已创建\n")

    # 3. 生成剧情
    print("3. 生成剧情...")

    # 定义角色
    characters = [
        {"agent_id": "detective", "name": "夏洛克", "role": "侦探"},
        {"agent_id": "assistant", "name": "华生", "role": "助手"},
        {"agent_id": "suspect", "name": "莫里亚蒂", "role": "嫌疑人"}
    ]

    # 使用自定义剧情点
    custom_plot = [
        "案发现场：在伦敦的一座豪宅中发现了一起神秘的盗窃案",
        "调查线索：侦探和助手开始收集证据和询问证人",
        "发现关键线索：找到了指向嫌疑人的重要证据",
        "对峙：侦探与嫌疑人进行智力较量",
        "真相大白：揭示案件的真相并抓获罪犯"
    ]

    story = await story_engine.generate_story(
        theme="悬疑推理：伦敦盗窃案",
        agent_characters=characters,
        custom_plot=custom_plot
    )

    print(f"   剧情标题: {story.title}")
    print(f"   背景设定: {story.setting}")
    print(f"   剧情点数: {len(story.plot_points)}")
    print(f"   当前剧情: {story_engine.get_current_plot_point()}\n")

    # 4. 创建智能体管理器和智能体
    print("4. 创建智能体...")
    manager = AgentManager(max_agents=10)

    # 创建侦探
    detective = await manager.create_agent(
        agent_id="detective",
        name="夏洛克",
        config={"role": "detective"},
        use_llm=use_llm
    )

    # 创建助手
    assistant = await manager.create_agent(
        agent_id="assistant",
        name="华生",
        config={"role": "assistant"},
        use_llm=use_llm
    )

    print("   智能体已创建\n")

    # 5. 为智能体设置基于剧情的初始目标
    print("5. 设置剧情目标...")

    # 侦探的目标
    await detective.add_goal({
        "title": "侦破盗窃案",
        "description": "调查伦敦豪宅盗窃案，找出真相",
        "priority": GoalPriority.CRITICAL.value
    })

    # 助手的目标
    await assistant.add_goal({
        "title": "协助侦探",
        "description": "帮助夏洛克收集证据和分析线索",
        "priority": GoalPriority.HIGH.value
    })

    print("   目标已设置\n")

    # 6. 模拟剧情推进
    print("6. 模拟剧情推进...\n")

    for plot_index in range(min(3, len(story.plot_points))):
        print(f"   【第{plot_index + 1}幕】{story.plot_points[plot_index]}")
        print()

        # 模拟环境事件
        if plot_index == 0:
            # 第一幕：案发
            env_data = {
                "location": "豪宅大厅",
                "time": "晚上10点",
                "description": "发现保险箱被撬开，珠宝失窃"
            }
            await manager.broadcast_environment_update(env_data)

            # 侦探进行决策
            decision = await detective.cognition.make_decision({
                "situation": "刚到达案发现场，需要开始调查",
                "options": [
                    {"type": "examine_scene", "location": "crime_scene"},
                    {"type": "interview_witness", "person": "butler"},
                    {"type": "check_security", "system": "cameras"}
                ]
            })

            print(f"   夏洛克的行动: {decision['action']['type']}")
            print(f"   推理: {decision['reasoning']}\n")

            # 检查行为是否符合剧情
            alignment = await story_engine.check_action_alignment(
                "detective",
                decision['action']
            )
            print(f"   剧情对齐度: {'符合' if alignment['aligned'] else '偏离'}")
            if alignment['suggestion']:
                print(f"   建议: {alignment['suggestion']}\n")

        elif plot_index == 1:
            # 第二幕：调查
            # 华生协助调查
            decision = await assistant.cognition.make_decision({
                "situation": "协助夏洛克调查，需要收集证据",
                "options": [
                    {"type": "search_room", "room": "study"},
                    {"type": "take_photos", "subject": "evidence"},
                    {"type": "record_notes", "about": "timeline"}
                ]
            })

            print(f"   华生的行动: {decision['action']['type']}")
            print(f"   推理: {decision['reasoning']}\n")

        # 推进到下一个剧情点
        if plot_index < len(story.plot_points) - 1:
            story_engine.advance_plot()
            print(f"   -> 剧情推进到: {story_engine.get_current_plot_point()}\n")

        print("-" * 60 + "\n")

    # 7. 智能体间对话
    print("7. 智能体间对话...")
    response = await manager.send_message(
        sender_id="detective",
        target_id="assistant",
        message="华生，我发现了一个重要线索，嫌疑人可能是内部人员。"
    )
    print(f"   夏洛克 -> 华生")
    print(f"   华生的回应: {response}\n")

    # 8. 生成下一个剧情事件
    print("8. 生成下一个剧情事件...")
    next_event = await story_engine.generate_next_event(
        current_situation="侦探们正在调查，已经找到了一些线索",
        agent_states={
            "detective": {"investigating": True},
            "assistant": {"assisting": True}
        }
    )
    print(f"   事件类型: {next_event['event_type']}")
    print(f"   描述: {next_event['description']}\n")

    # 9. 停止所有智能体
    print("9. 停止所有智能体...")
    await manager.stop_all()
    print("   所有智能体已停止\n")

    print("=== 剧情演绎示例完成 ===")
    print("\n提示：")
    print("- 设置OPENAI_API_KEY环境变量以启用LLM增强功能")
    print("- LLM会使剧情生成和智能体决策更加智能和自然")
    print("- 剧情引擎会自动检查智能体行为是否偏离核心剧情")


if __name__ == "__main__":
    asyncio.run(main())
