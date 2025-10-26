"""
持续运行的交互式智能体示例
- 智能体根据日程自主运行（睡觉时暂停）
- 用户可以随时与智能体对话
- 简单的命令行交互界面
"""

import asyncio
import sys
import os
from datetime import datetime, time
from typing import Optional
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType
from agent_system.llm.prompt_manager import initialize_prompts


class InteractiveAgent:
    """交互式智能体包装器"""

    def __init__(self, agent, story_engine: Optional[StoryEngine] = None):
        self.agent = agent
        self.story_engine = story_engine
        self.running = False
        self.user_messages = asyncio.Queue()
        self.sleep_start_time = time(22, 0)  # 22:00开始睡觉
        self.wake_up_time = time(7, 0)      # 07:00起床

    def is_sleeping(self) -> bool:
        """检查智能体是否在睡觉"""
        current_time = datetime.now().time()

        # 跨午夜的睡眠时间处理
        if self.sleep_start_time > self.wake_up_time:
            # 例如 22:00 - 07:00
            return current_time >= self.sleep_start_time or current_time < self.wake_up_time
        else:
            # 例如 01:00 - 08:00
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

    async def chat(self, user_message: str) -> str:
        """
        与智能体聊天

        Args:
            user_message: 用户消息

        Returns:
            智能体回复
        """
        # 如果智能体在睡觉，返回睡眠提示
        if self.is_sleeping():
            return "💤 抱歉，我现在在睡觉。请在早上7点后再找我聊天。"

        # 将用户消息作为环境事件让智能体感知
        perception_event = {
            "event_type": "user_message",
            "description": f"用户说: {user_message}",
            "user_input": user_message,
            "timestamp": datetime.now().isoformat()
        }

        await self.agent.perceive_environment(perception_event)

        # 使用认知模块生成回复
        situation = f"用户向你说: {user_message}"
        emotion = self.agent.emotion.get_current_emotion()
        goals = self.agent.goal.get_active_goals()

        # 获取相关记忆
        memories = await self.agent.memory.retrieve(
            {"memory_type": "event"},
            limit=3
        )
        memory_context = "\n".join([
            m.get("content", {}).get("event_summary", "")
            for m in memories
        ])

        # 让认知模块决策如何回复
        decision = await self.agent.cognition.make_decision(
            situation=situation,
            emotion=emotion,
            goals=goals,
            memories=memory_context
        )

        # 提取回复（简化版本）
        if isinstance(decision, dict):
            action = decision.get("action", {})
            reasoning = decision.get("reasoning", "")

            # 构建回复
            reply = reasoning if reasoning else f"我理解了: {user_message}"
        else:
            reply = "我在思考你说的话..."

        # 记录对话到记忆
        await self.agent.memory.store("event", {
            "event_type": "conversation",
            "event_summary": f"与用户对话: {user_message[:20]}...",
            "event_details": f"用户: {user_message}\n我: {reply}",
            "participants": ["user", self.agent.agent_id],
            "timestamp": datetime.now().isoformat()
        })

        return reply


async def user_input_handler(interactive_agent: InteractiveAgent):
    """
    处理用户输入（在单独的线程中运行）
    """
    loop = asyncio.get_event_loop()

    while interactive_agent.running:
        try:
            # 在线程池中运行输入（避免阻塞事件循环）
            user_input = await loop.run_in_executor(None, input)

            if not user_input.strip():
                continue

            # 解析命令
            if user_input.startswith('/'):
                await handle_command(interactive_agent, user_input)
            else:
                # 普通聊天消息
                reply = await interactive_agent.chat(user_input)
                print(f"\n🤖 {interactive_agent.agent.name}: {reply}\n")
                print_prompt()

        except EOFError:
            break
        except Exception as e:
            print(f"\n❌ 输入处理错误: {e}\n")
            print_prompt()


async def handle_command(interactive_agent: InteractiveAgent, command: str):
    """处理命令"""
    cmd = command.strip().lower()

    if cmd == '/help':
        print("\n" + "="*60)
        print("可用命令：")
        print("  /help      - 显示帮助")
        print("  /status    - 查看智能体状态")
        print("  /schedule  - 查看今日日程")
        print("  /emotion   - 查看情感状态")
        print("  /goals     - 查看当前目标")
        print("  /memory    - 查看最近记忆")
        print("  /quit      - 退出程序")
        print("\n直接输入文字即可与智能体聊天")
        print("="*60 + "\n")

    elif cmd == '/status':
        activity = interactive_agent.get_current_activity()
        emotion = interactive_agent.agent.emotion.get_current_emotion()
        print(f"\n📊 智能体状态")
        print(f"  名称: {interactive_agent.agent.name}")
        print(f"  当前活动: {activity}")
        print(f"  情感: {emotion.get('primary_emotion', 'neutral')}")
        print(f"  效价: {emotion.get('valence', 0):.2f}")
        print(f"  唤醒度: {emotion.get('arousal', 0):.2f}\n")

    elif cmd == '/schedule':
        if interactive_agent.story_engine:
            schedule = interactive_agent.story_engine.get_agent_schedule(
                interactive_agent.agent.agent_id
            )
            if schedule:
                print(f"\n📅 今日日程 ({schedule.date})")
                print("-" * 60)
                print(schedule.get_summary())
                print("-" * 60 + "\n")
            else:
                print("\n⚠️  暂无日程安排\n")
        else:
            print("\n⚠️  未启用剧情系统\n")

    elif cmd == '/emotion':
        emotion = interactive_agent.agent.emotion.get_current_emotion()
        print(f"\n💭 情感状态")
        print(f"  主要情绪: {emotion.get('primary_emotion', 'neutral')}")
        print(f"  效价 (Valence): {emotion.get('valence', 0):.2f}")
        print(f"  唤醒度 (Arousal): {emotion.get('arousal', 0):.2f}")
        print(f"  支配度 (Dominance): {emotion.get('dominance', 0):.2f}\n")

    elif cmd == '/goals':
        goals = interactive_agent.agent.goal.get_active_goals()
        print(f"\n🎯 当前目标 ({len(goals)}个)")
        if goals:
            for i, goal in enumerate(goals, 1):
                print(f"  {i}. {goal.get('title', 'N/A')}")
                print(f"     优先级: {goal.get('priority', 'N/A')}")
                print(f"     进度: {goal.get('progress', 0)*100:.0f}%")
        else:
            print("  暂无活跃目标")
        print()

    elif cmd == '/memory':
        memories = await interactive_agent.agent.memory.retrieve(
            {"memory_type": "event"},
            limit=5
        )
        print(f"\n🧠 最近记忆 ({len(memories)}条)")
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", {})
            summary = content.get("event_summary", "N/A")
            print(f"  {i}. {summary}")
        print()

    elif cmd == '/quit':
        print("\n👋 再见！正在关闭智能体...\n")
        interactive_agent.running = False

    else:
        print(f"\n❌ 未知命令: {command}")
        print("输入 /help 查看可用命令\n")

    if cmd != '/quit':
        print_prompt()


def print_prompt():
    """打印输入提示"""
    print("💬 你: ", end="", flush=True)


async def agent_background_loop(interactive_agent: InteractiveAgent):
    """
    智能体后台循环
    定期检查日程、处理事件等
    """
    check_interval = 60  # 每60秒检查一次

    while interactive_agent.running:
        try:
            # 如果在睡觉，跳过处理
            if not interactive_agent.is_sleeping():
                # 定期触发智能体tick
                await interactive_agent.agent.process_tick()

                # 如果有剧情引擎，检查偏离
                if interactive_agent.story_engine:
                    await interactive_agent.story_engine.check_and_correct_deviation()

            # 等待下一个检查周期
            await asyncio.sleep(check_interval)

        except Exception as e:
            print(f"\n⚠️  后台处理错误: {e}")
            await asyncio.sleep(check_interval)


async def main():
    """主函数"""
    print("="*70)
    print("🤖 交互式智能体系统")
    print("="*70)
    print()

    # ========== 1. 初始化LLM ==========
    print("正在初始化...")

    api_key = os.getenv("OPENAI_API_KEY", "cd8b23c5-45f1-48a8-9009-e1ba7f592cfe")
    base_url = "https://ark.cn-beijing.volces.com/api/v3"
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
            print("✓ LLM已初始化")
        except Exception as e:
            use_llm = False
            print(f"⚠️  LLM初始化失败: {e}")
            print("将使用规则模式运行")
    else:
        print("✓ 使用规则模式")

    # 加载提示词
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    if os.path.exists(prompts_path):
        initialize_prompts(prompts_path)
        print("✓ 提示词已加载")

    # ========== 2. 创建智能体 ==========
    manager = AgentManager(max_agents=5)

    agent = await manager.create_agent(
        agent_id="alice",
        name="Alice",
        config={"role": "helpful_assistant"},
        use_llm=use_llm
    )

    print(f"✓ 智能体 '{agent.name}' 已创建")

    # ========== 3. 创建剧情和日程（可选） ==========
    story_engine = None
    enable_story = input("\n是否启用剧情模式？(y/n): ").strip().lower() == 'y'

    if enable_story:
        story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=use_llm,
            deviation_threshold=0.6
        )
        await story_engine.initialize()
        story_engine.register_agent(agent)
        agent.story_engine = story_engine

        # 生成简单日程
        print("正在生成日程...")
        await story_engine.generate_story_outline(
            theme="日常生活",
            agent_characters=[
                {"agent_id": "alice", "name": "Alice", "role": "智能助手"}
            ],
            custom_plot_points=[
                "08:00 起床，开始新的一天",
                "12:00 午餐时间，休息放松",
                "15:00 下午活动，处理任务",
                "18:00 晚餐时间",
                "22:00 准备休息，结束一天"
            ]
        )

        await story_engine.generate_agent_schedule("alice", agent)
        print("✓ 日程已生成")

    # ========== 4. 创建交互式包装器 ==========
    interactive_agent = InteractiveAgent(agent, story_engine)
    interactive_agent.running = True

    # ========== 5. 显示欢迎信息 ==========
    print("\n" + "="*70)
    print(f"✨ 欢迎！我是 {agent.name}，很高兴认识你！")
    print("="*70)
    print()
    print("💡 提示:")
    print("  - 直接输入文字与我聊天")
    print("  - 输入 /help 查看所有命令")
    print("  - 输入 /quit 退出程序")
    print()

    if enable_story:
        activity = interactive_agent.get_current_activity()
        print(f"📋 我现在正在: {activity}")
        print("⏰ 我的作息时间: 07:00起床, 22:00睡觉")
        print()

    print_prompt()

    # ========== 6. 启动后台循环和用户输入处理 ==========
    try:
        # 同时运行后台循环和用户输入处理
        await asyncio.gather(
            agent_background_loop(interactive_agent),
            user_input_handler(interactive_agent)
        )
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在关闭...")
    finally:
        # 清理
        interactive_agent.running = False
        await manager.stop_all()
        print("\n👋 智能体已关闭。再见！\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
