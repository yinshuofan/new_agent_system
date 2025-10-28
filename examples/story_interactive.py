"""
剧情演绎系统 - 交互式示例
- 完整的剧情系统
- 多智能体角色扮演
- 剧情推进和事件触发
- LLM驱动的动态剧情
- 交互式控制
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent, AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig


class StoryInteractiveSystem:
    """交互式剧情演绎系统"""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.manager = None
        self.story_engine = None
        self.agents: Dict[str, Agent] = {}
        self.running = False
        self.current_chapter = 1

    async def initialize(self):
        """初始化系统"""
        print("=" * 70)
        print("🎭 剧情演绎系统")
        print("=" * 70)
        print()

        # 检查并初始化LLM
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
                    print("   📡 使用AI生成动态剧情")
                except Exception as e:
                    print(f"   ⚠️ LLM初始化失败: {e}")
                    print("   💡 将使用预设剧情模式")
                    self.use_llm = False
            else:
                print("   ⚠️ 未找到API Key")
                print("   💡 设置方法: export OPENAI_API_KEY='your-key'")
                print("   💡 将使用预设剧情模式")
                self.use_llm = False
            print()

        # 创建剧情引擎
        print("📖 创建剧情引擎...")
        self.story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=self.use_llm
        )
        await self.story_engine.initialize()
        print("   ✓ 剧情引擎已创建")
        print()

        # 创建智能体管理器
        print("🤖 创建智能体管理器...")
        self.manager = AgentManager()
        print("   ✓ 管理器已创建")
        print()

    async def create_story(self):
        """创建剧情"""
        print("=" * 70)
        print("📝 创建剧情")
        print("=" * 70)
        print()

        # 预设剧情：侦探故事
        theme = "悬疑推理：伦敦盗窃案"

        # 定义角色
        characters = [
            {
                "agent_id": "holmes",
                "name": "夏洛克·福尔摩斯",
                "role": "侦探",
                "personality": "聪明、冷静、观察力敏锐",
                "expertise": ["推理", "观察", "化学"]
            },
            {
                "agent_id": "watson",
                "name": "华生医生",
                "role": "助手",
                "personality": "忠诚、勇敢、细心",
                "expertise": ["医学", "记录", "协助"]
            },
            {
                "agent_id": "inspector",
                "name": "雷斯垂德探长",
                "role": "警探",
                "personality": "正直、严谨、经验丰富",
                "expertise": ["调查", "审讯", "组织"]
            }
        ]

        print(f"主题: {theme}")
        print(f"角色数: {len(characters)}")
        for char in characters:
            print(f"  - {char['name']} ({char['role']})")
        print()

        # 生成剧情
        print("🎬 生成剧情...")

        # 预设剧情点
        custom_plot = [
            "案发现场：在伦敦的一座豪宅中发现了一起神秘的盗窃案",
            "调查线索：侦探和助手开始收集证据和询问证人",
            "发现关键线索：找到了指向嫌疑人的重要证据",
            "对峙：侦探与嫌疑人进行智力较量",
            "真相大白：揭示案件的真相和作案手法"
        ]

        story = await self.story_engine.generate_story(
            theme=theme,
            agent_characters=[{
                "agent_id": c["agent_id"],
                "name": c["name"],
                "role": c["role"]
            } for c in characters],
            custom_plot=custom_plot
        )

        print(f"   ✓ 剧情已生成")
        print(f"   标题: {story.title}")
        print(f"   剧情点数: {len(story.plot_points)}")
        print()

        # 创建智能体角色
        print("👥 创建角色...")
        for char in characters:
            agent = await self.manager.create_agent(
                agent_id=char["agent_id"],
                name=char["name"],
                config={
                    "role": char["role"],
                    "personality": char["personality"],
                    "expertise": char["expertise"],
                    "max_memories": 500
                },
                use_llm=self.use_llm
            )
            self.agents[char["agent_id"]] = agent

            # 设置剧情目标
            await agent.add_goal({
                "title": story.initial_goals.get(char["agent_id"], "参与剧情"),
                "description": f"在{story.title}中扮演{char['role']}",
                "priority": 3
            })

            print(f"   ✓ {char['name']} 已创建")

        print()
        print("=" * 70)
        print("✅ 剧情和角色创建完成")
        print("=" * 70)
        print()

    async def show_story_status(self):
        """显示剧情状态"""
        story = self.story_engine.get_current_story()
        if not story:
            print("⚠️ 当前没有活跃的剧情")
            return

        print("\n" + "=" * 70)
        print("📖 剧情状态")
        print("=" * 70)
        print(f"标题: {story.title}")
        print(f"背景: {story.background}")
        print(f"当前章节: {story.current_plot_index + 1}/{len(story.plot_points)}")
        print()

        current_plot = self.story_engine.get_current_plot_point()
        if current_plot:
            print(f"当前剧情点:")
            print(f"  {current_plot}")
        print()

        print(f"所有剧情点:")
        for i, plot in enumerate(story.plot_points):
            marker = "▶" if i == story.current_plot_index else "○"
            status = "进行中" if i == story.current_plot_index else ("已完成" if i < story.current_plot_index else "未开始")
            print(f"  {marker} 第{i+1}章: {plot} [{status}]")

        print("=" * 70 + "\n")

    async def show_agents_status(self):
        """显示所有角色状态"""
        print("\n" + "=" * 70)
        print("👥 角色状态")
        print("=" * 70)

        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            emotion = agent.emotion.get_current_emotion()
            goals = agent.goal.get_active_goals()
            mem_stats = status['modules']['memory']

            print(f"\n🎭 {status['name']} ({agent_id})")
            print(f"   状态: {'运行中' if status['running'] else '已停止'}")
            print(f"   情感: {emotion.get('primary_emotion', 'neutral')} (效价: {emotion.get('valence', 0.0):.2f})")
            print(f"   记忆: {mem_stats.get('event_memories_count', 0)} 条事件")
            print(f"   目标: {len(goals)} 个活跃")

        print("=" * 70 + "\n")

    async def advance_story(self):
        """推进剧情"""
        print("\n" + "-" * 70)
        print("⏩ 推进剧情...")

        if self.story_engine.advance_plot():
            new_plot = self.story_engine.get_current_plot_point()
            self.current_chapter += 1
            print(f"✓ 进入第 {self.current_chapter} 章")
            print(f"📖 {new_plot}")

            # 为所有角色添加记忆
            for agent in self.agents.values():
                await agent.memory.store("event", {
                    "event_summary": f"剧情推进到第{self.current_chapter}章",
                    "event_details": new_plot,
                    "participants": list(self.agents.keys()),
                    "importance": 0.8
                })

            print("-" * 70 + "\n")
            return True
        else:
            print("⚠️ 剧情已结束")
            print("-" * 70 + "\n")
            return False

    async def agent_act(self, agent_id: str, action_description: str):
        """让角色执行行动"""
        if agent_id not in self.agents:
            print(f"❌ 角色 {agent_id} 不存在")
            return

        agent = self.agents[agent_id]
        print(f"\n🎬 {agent.name} 执行行动: {action_description}")

        # 检查行动是否符合剧情
        alignment = await self.story_engine.check_action_alignment(
            agent_id,
            {"description": action_description, "type": "action"}
        )

        if alignment.get("aligned", True):
            print(f"   ✓ 行动符合剧情")
        else:
            deviation = alignment.get("deviation_level", 0)
            print(f"   ⚠️ 行动偏离剧情 (偏离度: {deviation:.2f})")
            if alignment.get("suggestion"):
                print(f"   💡 建议: {alignment['suggestion']}")

        # 存储行动记忆
        await agent.memory.store("event", {
            "event_summary": f"{agent.name}的行动",
            "event_details": action_description,
            "participants": [agent_id],
            "importance": 0.6
        })

        print()

    async def character_dialogue(self, agent_id: str, message: str):
        """角色对话"""
        if agent_id not in self.agents:
            print(f"❌ 角色 {agent_id} 不存在")
            return

        agent = self.agents[agent_id]
        print(f"\n💬 你对 {agent.name} 说: {message}")

        # 发送消息
        response = await agent.receive_message(
            sender_id="narrator",
            message=message,
            metadata={"type": "dialogue"}
        )

        print(f"🎭 {agent.name}: {response}")
        print()

    async def show_help(self):
        """显示帮助"""
        print("\n" + "=" * 70)
        print("💡 命令帮助")
        print("=" * 70)
        print()
        print("剧情控制:")
        print("  /story          - 显示剧情状态")
        print("  /advance        - 推进到下一章")
        print("  /status         - 显示所有角色状态")
        print()
        print("角色交互:")
        print("  /talk <角色> <消息>  - 与角色对话")
        print("    示例: /talk holmes 有什么发现吗？")
        print()
        print("  /act <角色> <行动>   - 让角色执行行动")
        print("    示例: /act watson 检查现场")
        print()
        print("系统:")
        print("  /help           - 显示此帮助")
        print("  /quit           - 退出程序")
        print()
        print("角色代码:")
        for agent_id, agent in self.agents.items():
            print(f"  {agent_id:12} - {agent.name}")
        print("=" * 70 + "\n")

    async def run(self):
        """运行交互式系统"""
        await self.initialize()
        await self.create_story()

        # 显示初始状态
        await self.show_story_status()

        print("=" * 70)
        print("🎮 系统已就绪")
        print("=" * 70)
        print("💡 输入 /help 查看命令帮助")
        print("💡 输入 /story 查看剧情")
        print("💡 输入 /advance 推进剧情")
        print("=" * 70)
        print()

        self.running = True

        while self.running:
            try:
                # 获取用户输入
                user_input = input("> ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=2)
                    command = parts[0].lower()

                    if command == "/quit":
                        print("\n👋 结束剧情，再见！")
                        self.running = False
                        break

                    elif command == "/help":
                        await self.show_help()

                    elif command == "/story":
                        await self.show_story_status()

                    elif command == "/status":
                        await self.show_agents_status()

                    elif command == "/advance":
                        if not await self.advance_story():
                            print("🎬 剧情已结束！所有章节都已完成。")

                    elif command == "/talk":
                        if len(parts) < 3:
                            print("❌ 用法: /talk <角色> <消息>")
                        else:
                            agent_id = parts[1]
                            message = parts[2]
                            await self.character_dialogue(agent_id, message)

                    elif command == "/act":
                        if len(parts) < 3:
                            print("❌ 用法: /act <角色> <行动>")
                        else:
                            agent_id = parts[1]
                            action = parts[2]
                            await self.agent_act(agent_id, action)

                    else:
                        print(f"❌ 未知命令: {command}")
                        print("💡 输入 /help 查看可用命令\n")

                    continue

                # 直接输入视为旁白
                print(f"📢 旁白: {user_input}\n")

            except KeyboardInterrupt:
                print("\n\n👋 收到中断信号，正在退出...")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")

        # 清理
        print("\n🧹 清理资源...")
        for agent in self.agents.values():
            await agent.stop()
        print("✓ 完成\n")


async def main():
    """主函数"""
    # 检查是否要使用LLM
    use_llm = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-llm":
        use_llm = False

    story_system = StoryInteractiveSystem(use_llm=use_llm)
    await story_system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已退出")
