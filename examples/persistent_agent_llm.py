"""
完整的持续运行智能体示例
使用真实LLM，展示所有核心功能，支持持续交互

功能：
- ✅ 真实LLM对话
- ✅ 完整的记忆系统
- ✅ 情感状态追踪
- ✅ 目标管理
- ✅ 时间推进和剧情演绎
- ✅ 持续运行，直到用户退出
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryLoader, StoryEngine, StoryMode
from agent_system.llm.prompt_manager import initialize_prompts
from agent_system.llm import load_llm_config, initialize_llm, get_api_key_status


class PersistentAgentSystem:
    """持续运行的智能体系统"""

    def __init__(self, story_config_path: str):
        self.story_config_path = story_config_path
        self.manager: AgentManager = None
        self.story_engine: StoryEngine = None
        self.story_config = None
        self.agents: Dict[str, Any] = {}
        self.current_time = datetime.now()
        self.running = True

    async def initialize(self):
        """初始化系统"""
        print("\n" + "=" * 80)
        print("🚀 智能体系统启动中...")
        print("=" * 80)

        # 1. 检查API key配置
        print("\n🔑 检查API配置...")
        api_status = get_api_key_status()
        if api_status["configured"]:
            print(f"   ✓ API Key已配置（来源: {api_status['source']}）")
            print(f"   ✓ Key: {api_status['masked_key']}")
        else:
            print("\n⚠️  警告：未找到API Key配置！")
            print("   系统将使用模拟响应模式运行。")
            print("\n   要使用真实LLM，请配置API Key：")
            print("   方式1: export OPENAI_API_KEY='your-key'")
            print("   方式2: 编辑 config/llm_config.yaml")
            use_llm = False
        else:
            use_llm = True

        # 2. 初始化LLM（如果已配置）
        if use_llm:
            try:
                print("\n🤖 初始化LLM连接...")
                llm_config = load_llm_config()
                await initialize_llm(llm_config)
                print("   ✓ LLM连接成功")
            except Exception as e:
                print(f"   ❌ LLM初始化失败: {e}")
                print("   切换到模拟响应模式")
                use_llm = False

        # 3. 初始化提示词
        print("\n📝 加载提示词配置...")
        initialize_prompts("/home/user/new_agent_system/config/prompts.yaml")

        # 4. 加载故事配置
        print("📖 加载故事配置...")
        self.story_config = StoryLoader.load_from_file(self.story_config_path)
        print(f"   故事：{self.story_config.title}")
        print(f"   主题：{self.story_config.theme}")

        # 5. 创建智能体管理器
        print("\n🤖 创建智能体...")
        self.manager = AgentManager(max_agents=10)

        # 6. 创建故事引擎
        self.story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=use_llm
        )
        await self.story_engine.initialize()

        # 7. 创建所有角色
        character_count = 0
        for char_id, char_config in self.story_config.characters.items():
            agent = await self.manager.create_agent(
                agent_id=char_id,
                name=char_config.get("name", char_id),
                config=char_config,
                use_llm=use_llm
            )

            # 注册到故事引擎
            self.story_engine.register_agent(agent)

            # 加载剧情大纲
            outline = StoryLoader.create_story_outline_from_config(self.story_config)
            self.story_engine._current_outline = outline

            # 生成并加载日程
            schedule = StoryLoader.generate_schedule_from_config(
                self.story_config,
                char_id
            )
            self.story_engine._agent_schedules[char_id] = schedule

            self.agents[char_id] = agent
            character_count += 1
            print(f"   ✓ {agent.name} (ID: {char_id})")

        print(f"\n✅ 成功创建 {character_count} 个智能体")
        if use_llm:
            print(f"💡 使用真实 LLM: OpenAI GPT")
        else:
            print(f"💡 使用模拟响应模式（无需API Key）")

    async def chat_with_agent(self, agent_id: str, message: str) -> str:
        """与智能体对话"""
        agent = self.agents.get(agent_id)
        if not agent:
            return f"❌ 找不到智能体：{agent_id}"

        print(f"\n💭 {agent.name} 正在思考...")

        try:
            reply = await agent.chat(message)
            return reply
        except Exception as e:
            return f"❌ 对话错误：{str(e)}"

    async def show_agent_status(self, agent_id: str):
        """显示智能体状态"""
        agent = self.agents.get(agent_id)
        if not agent:
            print(f"❌ 找不到智能体：{agent_id}")
            return

        print("\n" + "=" * 80)
        print(f"📊 {agent.name} 的状态")
        print("=" * 80)

        # 获取完整上下文
        context = await agent.context_manager.get_full_context()

        # 身份信息
        print("\n👤 身份信息:")
        identity = context['identity']
        print(f"   角色: {identity['role']}")
        print(f"   性格: {identity['personality']}")
        if identity.get('expertise'):
            print(f"   专长: {', '.join(identity['expertise'])}")

        # 情感状态
        print("\n💗 情感状态:")
        emotion = context['emotion']
        print(f"   主要情感: {emotion['primary_emotion']}")
        print(f"   情绪值: V={emotion['valence']:.2f}, A={emotion['arousal']:.2f}, D={emotion['dominance']:.2f}")

        # 当前活动
        print("\n📅 当前活动:")
        schedule = self.story_engine.get_agent_schedule(agent_id)
        if schedule:
            current = schedule.get_current_activity(self.current_time)
            if current:
                print(f"   {current.activity}")
                print(f"   时间: {current.start_time} - {current.end_time}")
                print(f"   地点: {current.location}")
                print(f"   描述: {current.description}")
            else:
                print("   暂无安排")

        # 目标
        print("\n🎯 当前目标:")
        goals = context['goals']['goals']
        if goals:
            for i, goal in enumerate(goals[:3], 1):
                print(f"   {i}. {goal['title']} (优先级: {goal['priority']}, 进度: {goal['progress']}%)")
        else:
            print("   暂无目标")

        # 记忆
        print("\n🧠 最近记忆:")
        memories = context['memories']['recent']
        if memories:
            for i, mem in enumerate(memories[:5], 1):
                print(f"   {i}. {mem['summary']}")
                if mem.get('event_type'):
                    print(f"      类型: {mem['event_type']}")
        else:
            print("   暂无记忆")

        print("\n" + "=" * 80)

    async def show_all_status(self):
        """显示所有智能体的简要状态"""
        print("\n" + "=" * 80)
        print("📊 系统状态总览")
        print("=" * 80)

        print(f"\n⏰ 当前时间: {self.current_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"🤖 智能体数量: {len(self.agents)}")

        for agent_id, agent in self.agents.items():
            context = await agent.context_manager.get_full_context()
            emotion = context['emotion']['primary_emotion']
            memory_count = context['memories']['count']

            # 获取当前活动
            schedule = self.story_engine.get_agent_schedule(agent_id)
            current_activity = "休息中"
            if schedule:
                current = schedule.get_current_activity(self.current_time)
                if current:
                    current_activity = current.activity

            print(f"\n   {agent.name}:")
            print(f"      状态: {emotion} | 活动: {current_activity} | 记忆: {memory_count}条")

    async def advance_time(self, hours: int = 1):
        """推进时间"""
        self.current_time += timedelta(hours=hours)
        print(f"\n⏰ 时间推进到: {self.current_time.strftime('%Y-%m-%d %H:%M')}")

        # 更新所有智能体的感知
        for agent in self.agents.values():
            await agent.perception.perceive_environment({
                "type": "time_change",
                "current_time": self.current_time.isoformat(),
                "time_advanced": hours
            })

    async def show_story_progress(self):
        """显示剧情进度"""
        print("\n" + "=" * 80)
        print("📖 剧情进度")
        print("=" * 80)

        outline = self.story_engine._current_outline
        if outline:
            print(f"\n故事: {outline.story_title}")
            print(f"主题: {outline.theme}")

            print("\n章节进度:")
            for i, chapter in enumerate(outline.chapters[:5], 1):
                print(f"   {i}. {chapter.title}")
                print(f"      时间: {chapter.time_range}")
                if chapter.key_events:
                    print(f"      关键事件: {', '.join(chapter.key_events[:3])}")

        # 显示各角色的日程进度
        print("\n角色日程:")
        for agent_id in self.agents.keys():
            schedule = self.story_engine.get_agent_schedule(agent_id)
            if schedule:
                completed = sum(1 for item in schedule.schedule_items if item.status.value == "completed")
                total = len(schedule.schedule_items)
                print(f"   {self.agents[agent_id].name}: {completed}/{total} 活动已完成")

    async def add_goal_to_agent(self, agent_id: str, goal_title: str, goal_desc: str):
        """给智能体添加目标"""
        agent = self.agents.get(agent_id)
        if not agent:
            print(f"❌ 找不到智能体：{agent_id}")
            return

        await agent.add_goal({
            "title": goal_title,
            "description": goal_desc,
            "priority": 1,
            "progress": 0
        })
        print(f"✅ 已为 {agent.name} 添加目标：{goal_title}")

    async def trigger_event(self, event_type: str, description: str):
        """触发环境事件"""
        print(f"\n⚡ 触发事件：{description}")

        for agent in self.agents.values():
            await agent.perception.perceive_environment({
                "type": "event",
                "event_type": event_type,
                "description": description,
                "timestamp": self.current_time.isoformat()
            })

    def show_help(self):
        """显示帮助信息"""
        print("\n" + "=" * 80)
        print("📖 命令帮助")
        print("=" * 80)
        print("""
基础命令:
  /help                          - 显示此帮助信息
  /quit 或 /exit                 - 退出系统
  /status                        - 显示所有智能体状态总览
  /status <角色ID>               - 显示指定智能体详细状态
  /list                          - 列出所有智能体

对话命令:
  /chat <角色ID> <消息>          - 与指定智能体对话
  例: /chat holmes 你好，最近怎么样？

时间控制:
  /time                          - 显示当前时间
  /advance <小时数>              - 推进时间（默认1小时）
  例: /advance 2

剧情命令:
  /story                         - 显示剧情进度
  /event <事件描述>              - 触发环境事件
  例: /event 突然下起了大雨

目标管理:
  /goal <角色ID> <目标> <描述>   - 为智能体添加目标
  例: /goal holmes 调查案件 收集证据

直接对话:
  <消息>                         - 与第一个智能体对话（快捷方式）
        """)
        print("=" * 80)

    async def run(self):
        """运行主循环"""
        # 显示欢迎信息
        print("\n" + "=" * 80)
        print("🎮 智能体系统已就绪")
        print("=" * 80)
        print(f"\n当前时间: {self.current_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"活跃角色: {', '.join(agent.name for agent in self.agents.values())}")
        print("\n💡 输入 /help 查看命令帮助")
        print("💡 直接输入消息可与第一个智能体对话")
        print("=" * 80)

        # 获取第一个智能体（用于快捷对话）
        default_agent_id = list(self.agents.keys())[0] if self.agents else None

        # 主循环
        while self.running:
            try:
                # 获取用户输入
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith("/"):
                    parts = user_input.split(None, 2)
                    cmd = parts[0].lower()

                    # 帮助
                    if cmd == "/help":
                        self.show_help()

                    # 退出
                    elif cmd in ["/quit", "/exit"]:
                        print("\n👋 正在关闭系统...")
                        self.running = False

                    # 列出智能体
                    elif cmd == "/list":
                        print("\n🤖 智能体列表:")
                        for agent_id, agent in self.agents.items():
                            print(f"   - {agent_id}: {agent.name}")

                    # 状态查询
                    elif cmd == "/status":
                        if len(parts) > 1:
                            await self.show_agent_status(parts[1])
                        else:
                            await self.show_all_status()

                    # 对话
                    elif cmd == "/chat":
                        if len(parts) < 3:
                            print("❌ 用法: /chat <角色ID> <消息>")
                        else:
                            agent_id = parts[1]
                            message = parts[2]
                            reply = await self.chat_with_agent(agent_id, message)
                            agent_name = self.agents[agent_id].name if agent_id in self.agents else agent_id
                            print(f"\n{agent_name}: {reply}")

                    # 时间控制
                    elif cmd == "/time":
                        print(f"\n⏰ 当前时间: {self.current_time.strftime('%Y-%m-%d %H:%M')}")

                    elif cmd == "/advance":
                        hours = int(parts[1]) if len(parts) > 1 else 1
                        await self.advance_time(hours)

                    # 剧情
                    elif cmd == "/story":
                        await self.show_story_progress()

                    # 事件触发
                    elif cmd == "/event":
                        if len(parts) < 2:
                            print("❌ 用法: /event <事件描述>")
                        else:
                            await self.trigger_event("custom", parts[1])

                    # 目标管理
                    elif cmd == "/goal":
                        if len(parts) < 3:
                            print("❌ 用法: /goal <角色ID> <目标标题> [描述]")
                        else:
                            agent_id = parts[1]
                            goal_parts = parts[2].split(None, 1)
                            goal_title = goal_parts[0]
                            goal_desc = goal_parts[1] if len(goal_parts) > 1 else ""
                            await self.add_goal_to_agent(agent_id, goal_title, goal_desc)

                    else:
                        print(f"❌ 未知命令: {cmd}")
                        print("💡 输入 /help 查看可用命令")

                else:
                    # 直接对话（使用默认智能体）
                    if default_agent_id:
                        reply = await self.chat_with_agent(default_agent_id, user_input)
                        agent_name = self.agents[default_agent_id].name
                        print(f"\n{agent_name}: {reply}")
                    else:
                        print("❌ 没有可用的智能体")

            except KeyboardInterrupt:
                print("\n\n👋 正在关闭系统...")
                self.running = False
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")
                import traceback
                traceback.print_exc()

    async def cleanup(self):
        """清理资源"""
        print("\n🧹 清理资源...")
        if self.manager:
            await self.manager.stop_all()
        print("✅ 清理完成")


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🤖 完整智能体系统 - LLM驱动")
    print("=" * 80)

    # 创建系统
    system = PersistentAgentSystem(
        story_config_path="/home/user/new_agent_system/config/holmes_story.yaml"
    )

    try:
        # 初始化
        await system.initialize()

        # 运行主循环
        await system.run()

    except Exception as e:
        print(f"\n❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        await system.cleanup()

    print("\n" + "=" * 80)
    print("👋 再见！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
