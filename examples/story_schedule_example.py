"""
剧情日程演绎完整示例
展示完整的剧情演绎功能：
1. 生成剧情大纲
2. 生成角色日程
3. 日程修改和偏离检测
4. 自动修正和记忆记录
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType
from agent_system.llm.prompt_manager import initialize_prompts
from datetime import datetime


async def main():
    """主函数"""
    print("=" * 70)
    print("剧情日程演绎完整示例")
    print("=" * 70)
    print()

    # ========== 1. 初始化LLM ==========
    print("【步骤1】初始化LLM系统...")

    # 使用提供的Doubao配置
    api_key = "cd8b23c5-45f1-48a8-9009-e1ba7f592cfe"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"

    # 也可以使用环境变量覆盖
    api_key = os.getenv("OPENAI_API_KEY", api_key)
    use_llm = api_key and api_key != "demo-key"

    if use_llm:
        try:
            llm_config = LLMConfig(
                api_key=api_key,
                base_url=base_url,
                model_mapping={
                    ModelType.FAST: "doubao-seed-1-6-251015",
                    ModelType.ACCURATE: "doubao-seed-1-6-251015",
                    ModelType.REASONING: "doubao-seed-1-6-251015"
                },
                max_connections=5,
                timeout=60.0
            )
            await initialize_llm(llm_config)
            print("✓ LLM已成功初始化（使用Doubao模型）")
        except Exception as e:
            use_llm = False
            print(f"✗ LLM初始化失败: {e}")
            print("  将使用规则模式运行")
    else:
        print("✓ 使用规则模式（无LLM）")

    # 加载提示词配置
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    if os.path.exists(prompts_path):
        initialize_prompts(prompts_path)
        print("✓ 提示词配置已加载")
    print()

    # ========== 2. 创建剧情引擎 ==========
    print("【步骤2】创建剧情引擎...")
    story_engine = StoryEngine(
        story_mode=StoryMode.GUIDED,
        use_llm=use_llm,
        deviation_threshold=0.6  # 对齐度低于0.6时触发修正
    )
    await story_engine.initialize()
    print("✓ 剧情引擎已创建（引导模式）")
    print()

    # ========== 3. 生成剧情大纲 ==========
    print("【步骤3】生成剧情大纲...")

    # 定义角色
    characters = [
        {"agent_id": "detective", "name": "夏洛克", "role": "私家侦探"},
        {"agent_id": "assistant", "name": "华生", "role": "医生助手"},
        {"agent_id": "client", "name": "艾米丽", "role": "委托人"}
    ]

    # 使用自定义剧情点
    custom_plot_points = [
        "08:00 早晨：侦探办公室，艾米丽前来委托调查丢失的家族项链",
        "10:00 调查开始：侦探和助手前往案发现场，收集初步线索",
        "14:00 深入调查：访问证人，分析物证，发现可疑之处",
        "16:00 关键突破：找到隐藏线索，锁定嫌疑目标",
        "18:00 真相大白：揭示真相，找回项链，委托人表示感谢"
    ]

    story_outline = await story_engine.generate_story_outline(
        theme="侦探推理：失踪的家族项链",
        agent_characters=characters,
        story_date="2025-10-26",
        custom_plot_points=custom_plot_points
    )

    print(f"✓ 剧情大纲已生成")
    print(f"  标题: {story_outline.title}")
    print(f"  主题: {story_outline.theme}")
    print(f"  背景: {story_outline.setting}")
    print(f"  剧情点数: {len(story_outline.main_plot_points)}")
    print(f"  角色数: {len(story_outline.character_roles)}")
    print()

    # ========== 4. 创建智能体 ==========
    print("【步骤4】创建智能体...")
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

    # 创建委托人
    client = await manager.create_agent(
        agent_id="client",
        name="艾米丽",
        config={"role": "client"},
        use_llm=use_llm
    )

    print(f"✓ 已创建3个智能体")
    print()

    # ========== 5. 注册智能体到剧情引擎 ==========
    print("【步骤5】注册智能体到剧情引擎...")
    story_engine.register_agent(detective)
    story_engine.register_agent(assistant)
    story_engine.register_agent(client)

    # 将story_engine附加到每个agent，以便scheduler可以访问
    detective.story_engine = story_engine
    assistant.story_engine = story_engine
    client.story_engine = story_engine

    print("✓ 所有智能体已注册")
    print()

    # ========== 6. 生成角色日程 ==========
    print("【步骤6】生成角色日程...")

    # 为每个角色生成日程
    detective_schedule = await story_engine.generate_agent_schedule("detective", detective)
    print(f"✓ 侦探日程已生成（{len(detective_schedule.schedule_items)}个活动）")
    print(f"  整体对齐度: {detective_schedule.overall_alignment:.2f}")

    assistant_schedule = await story_engine.generate_agent_schedule("assistant", assistant)
    print(f"✓ 助手日程已生成（{len(assistant_schedule.schedule_items)}个活动）")
    print(f"  整体对齐度: {assistant_schedule.overall_alignment:.2f}")

    client_schedule = await story_engine.generate_agent_schedule("client", client)
    print(f"✓ 委托人日程已生成（{len(client_schedule.schedule_items)}个活动）")
    print(f"  整体对齐度: {client_schedule.overall_alignment:.2f}")
    print()

    # ========== 7. 显示日程详情 ==========
    print("【步骤7】查看侦探的日程...")
    print("-" * 70)
    print(detective_schedule.get_summary())
    print("-" * 70)
    print()

    # ========== 8. 查询当前活动 ==========
    print("【步骤8】查询当前活动...")
    current_time = datetime.now()

    for agent_id in ["detective", "assistant", "client"]:
        current_activity = story_engine.get_current_activity(agent_id)
        if current_activity:
            print(f"  {agent_id}: {current_activity}")
        else:
            print(f"  {agent_id}: 无当前活动")
    print()

    # ========== 9. 模拟日程修改（导致偏离） ==========
    print("【步骤9】模拟日程修改（测试偏离检测）...")

    # 修改侦探的某个日程，使其偏离剧情
    if len(detective_schedule.schedule_items) > 0:
        first_schedule = detective_schedule.schedule_items[0]
        print(f"  原始活动: {first_schedule.activity}")
        print(f"  原始对齐度: {first_schedule.story_alignment_score:.2f}")

        # 修改为一个偏离剧情的活动
        await story_engine.modify_schedule(
            agent_id="detective",
            schedule_id=first_schedule.schedule_id,
            updates={
                "activity": "去咖啡馆休闲",
                "description": "放松心情，享受午后时光",
                "story_alignment_score": 0.3  # 低对齐度
            },
            reason="智能体自主选择休闲活动"
        )

        print(f"  修改后活动: 去咖啡馆休闲")
        print(f"  修改后对齐度: 0.30")

        # 获取更新后的日程
        updated_schedule = story_engine.get_agent_schedule("detective")
        print(f"  整体对齐度: {updated_schedule.overall_alignment:.2f}")

        if updated_schedule.deviation_warnings:
            print(f"  偏离警告: {len(updated_schedule.deviation_warnings)}条")
            for warning in updated_schedule.deviation_warnings:
                print(f"    - {warning}")
    print()

    # ========== 10. 检查并修正偏离 ==========
    print("【步骤10】检查并修正偏离...")
    deviation_events = await story_engine.check_and_correct_deviation()

    if deviation_events:
        print(f"✓ 检测到{len(deviation_events)}个偏离，已触发修正事件：")
        for event in deviation_events:
            print(f"  - 智能体: {event['agent_id']}")
            print(f"    事件: {event['event']['description']}")
            print(f"    引导: {event['event']['guidance']}")
    else:
        print("✓ 所有智能体行为正常，无需修正")
    print()

    # ========== 11. 标记部分活动完成 ==========
    print("【步骤11】标记部分活动完成...")
    if len(detective_schedule.schedule_items) >= 2:
        # 标记前两个活动为完成
        for i in range(min(2, len(detective_schedule.schedule_items))):
            schedule_id = detective_schedule.schedule_items[i].schedule_id
            story_engine.mark_schedule_completed("detective", schedule_id)
        print(f"✓ 已标记侦探的前2个活动为完成")
    print()

    # ========== 12. 记录到记忆 ==========
    print("【步骤12】记录日程到记忆...")
    await story_engine.record_to_memory("detective")
    await story_engine.record_to_memory("assistant")
    await story_engine.record_to_memory("client")
    print("✓ 已完成的日程活动已记录到记忆系统")
    print()

    # ========== 13. 查看记忆 ==========
    print("【步骤13】查看侦探的记忆...")
    memories = await detective.memory.retrieve({"memory_type": "event"}, limit=5)
    if memories:
        print(f"✓ 检索到{len(memories)}条事件记忆：")
        for mem in memories:
            content = mem.get("content", {})
            print(f"  - {content.get('event_summary', 'N/A')}")
    else:
        print("  暂无记忆记录")
    print()

    # ========== 14. 测试scheduler自动运行（可选） ==========
    print("【步骤14】测试自动调度（5分钟触发）...")
    print("  注意：scheduler会每5分钟自动检查偏离并记录记忆")
    print("  在实际使用中，只需启动agent，scheduler会自动运行")
    print("  scheduler由AgentManager管理，包含以下触发器：")
    print("    - agent_update: 5分钟触发，更新所有模块")
    print("    - environment_check: 2分钟触发，检查环境")
    print("    - goal_evaluation: 10分钟触发，评估目标")
    print("    - story_narrative_check: 5分钟触发，检查剧情偏离并记录记忆")
    print()

    # ========== 15. 完整流程总结 ==========
    print("=" * 70)
    print("【完整流程总结】")
    print("=" * 70)
    print("1. ✓ 初始化LLM系统（Doubao）")
    print("2. ✓ 创建剧情引擎（引导模式）")
    print("3. ✓ 生成剧情大纲（主题+剧情点）")
    print("4. ✓ 创建智能体（侦探、助手、委托人）")
    print("5. ✓ 生成角色日程（基于cognition决策）")
    print("6. ✓ 查询当前活动")
    print("7. ✓ 日程修改功能")
    print("8. ✓ 偏离检测与修正")
    print("9. ✓ 记录到记忆系统")
    print("10. ✓ 自动调度（每5分钟）")
    print()
    print("【关键功能验证】")
    print(f"- 剧情生成: {story_outline.title}")
    print(f"- 日程生成: {len(detective_schedule.schedule_items) + len(assistant_schedule.schedule_items) + len(client_schedule.schedule_items)}个活动")
    print(f"- 偏离检测: {'已触发' if deviation_events else '无偏离'}")
    print(f"- 记忆记录: {len(memories) if memories else 0}条")
    print()

    # ========== 16. 停止所有智能体 ==========
    print("【步骤15】停止所有智能体...")
    await manager.stop_all()
    print("✓ 所有智能体已停止")
    print()

    print("=" * 70)
    print("剧情日程演绎示例完成")
    print("=" * 70)
    print()
    print("提示：")
    print("- 本示例展示了完整的剧情演绎流程")
    print("- 使用了Doubao LLM进行智能生成")
    print("- scheduler会自动每5分钟检查偏离和记录记忆")
    print("- 可以通过story_engine.get_current_activity()查询智能体当前在做什么")


if __name__ == "__main__":
    asyncio.run(main())
