"""
使用改进框架的简单自主运行示例
展示新的高层API如何让框架变得简单易用
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig
import os


class SimpleAutonomousStory:
    """简单的自主剧情系统 - 使用框架的高层API"""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.story_engine = None
        self.agents = {}
        self.running = False
        self.paused = False
        self.action_count = 0

    async def initialize(self):
        """初始化系统"""
        print("=" * 70)
        print("🎭 简单自主剧情系统 - 使用改进的框架")
        print("=" * 70)
        print()

        # 初始化LLM
        if self.use_llm:
            print("🔑 检查LLM配置...")
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                print("   ✓ 找到API Key，正在初始化LLM...")
                try:
                    await initialize_llm(LLMConfig(
                        api_key=api_key,
                        base_url=os.environ.get("OPENAI_BASE_URL"),
                        max_connections=5,
                        timeout=60.0
                    ))
                    print("   ✓ LLM初始化成功")
                except Exception as e:
                    print(f"   ⚠️ LLM初始化失败: {e}")
                    print("   💡 将使用规则模式")
                    self.use_llm = False
            else:
                print("   ⚠️ 未找到API Key，使用规则模式")
                self.use_llm = False
            print()

        # 创建剧情引擎
        print("📖 创建剧情...")
        self.story_engine = StoryEngine(story_mode=StoryMode.GUIDED, use_llm=False)
        await self.story_engine.initialize()

        # 预设简单剧情
        story = await self.story_engine.generate_story(
            theme="伦敦盗窃案调查",
            agent_characters=[
                {"agent_id": "holmes", "name": "福尔摩斯", "role": "侦探"},
                {"agent_id": "watson", "name": "华生", "role": "助手"}
            ],
            custom_plot=[
                "案发现场：豪宅中发现神秘盗窃案",
                "调查：侦探开始调查并收集证据",
                "发现线索：找到关键线索",
                "破案：真相大白"
            ]
        )
        print(f"   ✓ 剧情已创建: {story.title}")
        print()

        # 创建智能体 - 使用新的简化配置
        print("👥 创建角色...")

        # 福尔摩斯
        holmes = Agent(
            agent_id="holmes",
            name="福尔摩斯",
            config={
                "role": "私家侦探",
                "personality": "聪明、冷静、观察力敏锐",
                "possible_actions": ["检查现场", "询问证人", "分析证据", "推理案情"]
            },
            use_llm=self.use_llm
        )
        await holmes.start()
        self.agents["holmes"] = holmes
        print("   ✓ 福尔摩斯已创建")

        # 华生
        watson = Agent(
            agent_id="watson",
            name="华生",
            config={
                "role": "医生助手",
                "personality": "忠诚、细心、勇敢",
                "possible_actions": ["协助调查", "记录发现", "询问周围", "提供意见"]
            },
            use_llm=self.use_llm
        )
        await watson.start()
        self.agents["watson"] = watson
        print("   ✓ 华生已创建")
        print()

    async def autonomous_loop(self):
        """自主运行循环"""
        agent_ids = list(self.agents.keys())
        agent_index = 0

        while self.running:
            await asyncio.sleep(5)  # 每5秒一次行动

            if self.paused:
                continue

            # 获取当前剧情
            story = self.story_engine.get_current_story()
            current_plot = self.story_engine.get_current_plot_point()

            # 轮流让智能体行动
            agent_id = agent_ids[agent_index]
            agent = self.agents[agent_id]

            # 使用框架的新高层API - perform_autonomous_action
            result = await agent.perform_autonomous_action(
                context={
                    "situation": f"当前剧情：{current_plot}",
                    "story_context": f"{story.title} - 第{story.current_plot_index + 1}章：{current_plot}"
                }
            )

            # 显示行动
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🎬 {result['agent_name']}: {result['action']}")

            self.action_count += 1

            # 每4个行动推进剧情
            if self.action_count >= 4:
                self.action_count = 0
                if self.story_engine.advance_plot():
                    new_plot = self.story_engine.get_current_plot_point()
                    print()
                    print("=" * 70)
                    print(f"📖 剧情推进！进入第 {story.current_plot_index + 1} 章")
                    print(f"▶ {new_plot}")
                    print("=" * 70)
                    print()

            # 切换到下一个智能体
            agent_index = (agent_index + 1) % len(agent_ids)

    async def user_input_loop(self):
        """用户输入循环"""
        print("=" * 70)
        print("🎮 系统已就绪！")
        print("=" * 70)
        print("💡 命令：")
        print("   /pause  - 暂停自主运行")
        print("   /resume - 恢复自主运行")
        print("   /status - 查看剧情状态")
        print("   /quit   - 退出")
        print()
        print("💡 直接输入消息可与福尔摩斯对话")
        print("💡 @watson 开头可与华生对话")
        print("=" * 70)
        print()

        while self.running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )
                user_input = user_input.strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith("/"):
                    if user_input == "/quit":
                        print("\n👋 再见！")
                        self.running = False
                        break
                    elif user_input == "/pause":
                        self.paused = True
                        print("⏸️ 已暂停自主运行\n")
                    elif user_input == "/resume":
                        self.paused = False
                        print("▶️ 已恢复自主运行\n")
                    elif user_input == "/status":
                        story = self.story_engine.get_current_story()
                        current_plot = self.story_engine.get_current_plot_point()
                        print(f"\n📖 当前剧情: {story.title}")
                        print(f"📍 第{story.current_plot_index + 1}章: {current_plot}")
                        print(f"🔢 行动计数: {self.action_count}/4\n")
                    continue

                # 处理对话 - 使用框架的新高层API - chat
                target_agent = "holmes"
                message = user_input

                if user_input.startswith("@watson"):
                    target_agent = "watson"
                    message = user_input[7:].strip()
                elif user_input.startswith("@holmes"):
                    target_agent = "holmes"
                    message = user_input[7:].strip()

                agent = self.agents[target_agent]
                story = self.story_engine.get_current_story()
                current_plot = self.story_engine.get_current_plot_point()

                print(f"💬 你 → {agent.name}: {message}")

                # 使用框架的新chat方法 - 自动处理上下文和返回纯文本
                response = await agent.chat(
                    message,
                    context={
                        "story_context": f"剧情：{story.title}\n当前章节（第{story.current_plot_index + 1}章）：{current_plot}"
                    }
                )

                print(f"🎭 {agent.name}: {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 收到中断信号")
                self.running = False
                break
            except Exception as e:
                print(f"❌ 错误: {e}\n")

    async def run(self):
        """运行系统"""
        await self.initialize()

        self.running = True

        # 并发运行自主循环和用户输入循环
        await asyncio.gather(
            self.autonomous_loop(),
            self.user_input_loop()
        )

        # 清理
        print("\n🧹 清理资源...")
        for agent in self.agents.values():
            await agent.stop()
        print("✓ 完成\n")


async def main():
    """主函数"""
    use_llm = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-llm":
        use_llm = False

    system = SimpleAutonomousStory(use_llm=use_llm)
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已退出")
