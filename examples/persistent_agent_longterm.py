"""
持续运行智能体 - 长期剧情版本
支持1000+天的剧情，完整功能，使用LLM

新特性：
- ✅ 集成长期剧情系统
- ✅ 支持1000+天剧情配置
- ✅ 日常模板自动生成
- ✅ 剧情阶段管理
- ✅ 事件规则引擎
- ✅ 完整的6大模块
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import LongTermStoryEngine
from agent_system.llm.prompt_manager import initialize_prompts
from agent_system.llm import load_llm_config, initialize_llm, get_api_key_status


class LongTermAgentSystem:
    """支持长期剧情的智能体系统"""

    def __init__(self, story_config_path: str):
        self.story_config_path = story_config_path
        self.manager: AgentManager = None
        self.story_engine: LongTermStoryEngine = None
        self.agents: Dict[str, Any] = {}
        self.current_day = 1  # 当前是第几天
        self.current_time = datetime.now()
        self.running = True

    async def initialize(self):
        """初始化系统"""
        print("\n" + "=" * 80)
        print("🚀 长期剧情智能体系统启动中...")
        print("=" * 80)

        # 1. 检查API配置
        print("\n🔑 检查API配置...")
        api_status = get_api_key_status()
        if api_status["configured"]:
            print(f"   ✓ API Key已配置（来源: {api_status['source']}）")
            print(f"   ✓ Key: {api_status['masked_key']}")
            use_llm = True
        else:
            print("\n⚠️  警告：未找到API Key配置！")
            print("   系统将使用模拟响应模式运行。")
            print("\n   要使用真实LLM，请配置API Key：")
            print("   方式1: export OPENAI_API_KEY='your-key'")
            print("   方式2: 编辑 config/llm_config.yaml")
            use_llm = False

        # 2. 初始化LLM
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

        # 4. 加载长期剧情配置
        print("\n📖 加载长期剧情配置...")
        self.story_engine = LongTermStoryEngine.load_from_yaml(self.story_config_path)
        print(f"   ✓ 故事总天数: {self.story_engine.total_days}天")
        print(f"   ✓ 剧情阶段: {len(self.story_engine.story_phases)}个")
        print(f"   ✓ 日常模板: {len(self.story_engine.daily_templates)}个")

        # 显示阶段摘要
        phases = self.story_engine.get_phase_summary()
        for phase in phases['phases']:
            print(f"      - {phase['title']}: 第{phase['day_range'][0]}-{phase['day_range'][1]}天")

        # 5. 创建智能体管理器
        print("\n🤖 创建智能体...")
        self.manager = AgentManager(max_agents=10)

        # 6. 创建主角
        agent = await self.manager.create_agent(
            agent_id="holmes",
            name="Sherlock Holmes",
            config={
                "role": "私家侦探",
                "personality": "聪明绝顶、观察力敏锐、冷静理智",
                "expertise": ["犯罪调查", "逻辑推理", "化学实验"],
                "story_goal": "成为传奇侦探"
            },
            use_llm=use_llm
        )
        self.agents["holmes"] = agent
        print(f"   ✓ {agent.name} (ID: holmes)")

        print(f"\n✅ 系统初始化完成")
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
        print(f"📊 {agent.name} 的状态 - 第{self.current_day}天")
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

        # 今日日程（从长期剧情引擎获取）
        print("\n📅 今日日程:")
        schedule_items = self.story_engine.get_day_schedule(self.current_day, agent_id)
        if schedule_items:
            for item in schedule_items[:5]:  # 显示最多5个
                print(f"   {item.start_time} - {item.activity} @ {item.location}")
        else:
            print("   暂无安排")

        # 当前剧情阶段
        current_phase = self.story_engine._get_current_phase(self.current_day)
        if current_phase:
            print("\n📖 当前剧情阶段:")
            print(f"   阶段: {current_phase.title}")
            print(f"   主题: {current_phase.theme}")
            print(f"   进度: 第{self.current_day}/{current_phase.day_range[1]}天")

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
        else:
            print("   暂无记忆")

        print("\n" + "=" * 80)

    async def advance_day(self, days: int = 1):
        """推进天数"""
        old_day = self.current_day
        self.current_day += days
        self.current_time += timedelta(days=days)

        # 检查是否超出总天数
        if self.current_day > self.story_engine.total_days:
            self.current_day = self.story_engine.total_days
            print(f"\n⚠️  已到达故事最后一天（第{self.story_engine.total_days}天）")

        print(f"\n⏰ 时间推进: 第{old_day}天 → 第{self.current_day}天")
        print(f"   日期: {self.current_time.strftime('%Y-%m-%d')}")

        # 检查是否进入新阶段
        old_phase = self.story_engine._get_current_phase(old_day)
        new_phase = self.story_engine._get_current_phase(self.current_day)

        if old_phase != new_phase and new_phase:
            print(f"\n🎭 进入新剧情阶段：{new_phase.title}")
            print(f"   主题: {new_phase.theme}")

        # 更新智能体感知
        for agent in self.agents.values():
            await agent.perception.perceive_environment({
                "type": "time_change",
                "current_day": self.current_day,
                "current_time": self.current_time.isoformat(),
                "days_advanced": days
            })

    async def show_story_progress(self):
        """显示剧情进度"""
        print("\n" + "=" * 80)
        print("📖 剧情进度总览")
        print("=" * 80)

        print(f"\n⏰ 当前进度: 第{self.current_day}/{self.story_engine.total_days}天")
        print(f"   进度: {(self.current_day/self.story_engine.total_days*100):.1f}%")

        # 当前阶段
        current_phase = self.story_engine._get_current_phase(self.current_day)
        if current_phase:
            start, end = current_phase.day_range
            phase_progress = ((self.current_day - start) / (end - start) * 100)
            print(f"\n📌 当前阶段: {current_phase.title}")
            print(f"   主题: {current_phase.theme}")
            print(f"   范围: 第{start}-{end}天")
            print(f"   阶段进度: {phase_progress:.1f}%")

        # 所有阶段
        print("\n📚 所有剧情阶段:")
        summary = self.story_engine.get_phase_summary()
        for i, phase in enumerate(summary['phases'], 1):
            start, end = phase['day_range']
            status = "✓" if self.current_day > end else ("→" if start <= self.current_day <= end else "○")
            print(f"   {status} {phase['title']}: 第{start}-{end}天 - {phase['theme']}")

    async def show_today_schedule(self, agent_id: str = "holmes"):
        """显示今日完整日程"""
        agent = self.agents.get(agent_id)
        if not agent:
            print(f"❌ 找不到智能体：{agent_id}")
            return

        print("\n" + "=" * 80)
        print(f"📅 {agent.name} - 第{self.current_day}天完整日程")
        print(f"   日期: {self.current_time.strftime('%Y-%m-%d %A')}")
        print("=" * 80)

        schedule_items = self.story_engine.get_day_schedule(self.current_day, agent_id)

        if not schedule_items:
            print("\n   今日无安排")
            return

        print(f"\n   共{len(schedule_items)}项活动:")
        for i, item in enumerate(schedule_items, 1):
            print(f"\n   {i}. {item.start_time} - {item.end_time}")
            print(f"      活动: {item.activity}")
            print(f"      地点: {item.location}")
            if item.description:
                print(f"      说明: {item.description}")
            print(f"      重要性: {'⭐' * int(item.importance * 5)}")

        print("\n" + "=" * 80)

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
                "timestamp": self.current_time.isoformat(),
                "day": self.current_day
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
  /status [角色ID]               - 显示智能体状态

对话命令:
  /chat <角色ID> <消息>          - 与指定智能体对话
  <消息>                         - 与主角对话（快捷方式）

时间控制:
  /day                           - 显示当前天数
  /advance [天数]                - 推进天数（默认1天）
  /jump <天数>                   - 跳转到指定天数

剧情命令:
  /story                         - 显示剧情进度
  /schedule [角色ID]             - 显示今日完整日程
  /phase                         - 显示当前剧情阶段详情

目标管理:
  /goal <角色ID> <目标> [描述]   - 为智能体添加目标

事件触发:
  /event <描述>                  - 触发环境事件
        """)
        print("=" * 80)

    async def run(self):
        """运行主循环"""
        print("\n" + "=" * 80)
        print("🎮 系统已就绪 - 长期剧情模式")
        print("=" * 80)
        print(f"\n当前: 第{self.current_day}天 / 共{self.story_engine.total_days}天")
        print(f"日期: {self.current_time.strftime('%Y-%m-%d')}")
        print(f"活跃角色: {', '.join(agent.name for agent in self.agents.values())}")
        print("\n💡 输入 /help 查看命令帮助")
        print("💡 直接输入消息可与主角对话")
        print("=" * 80)

        default_agent_id = "holmes"

        while self.running:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    parts = user_input.split(None, 2)
                    cmd = parts[0].lower()

                    if cmd == "/help":
                        self.show_help()

                    elif cmd in ["/quit", "/exit"]:
                        print("\n👋 正在关闭系统...")
                        self.running = False

                    elif cmd == "/status":
                        agent_id = parts[1] if len(parts) > 1 else default_agent_id
                        await self.show_agent_status(agent_id)

                    elif cmd == "/chat":
                        if len(parts) < 3:
                            print("❌ 用法: /chat <角色ID> <消息>")
                        else:
                            agent_id = parts[1]
                            message = parts[2]
                            reply = await self.chat_with_agent(agent_id, message)
                            agent_name = self.agents[agent_id].name if agent_id in self.agents else agent_id
                            print(f"\n{agent_name}: {reply}")

                    elif cmd == "/day":
                        print(f"\n⏰ 当前: 第{self.current_day}/{self.story_engine.total_days}天")
                        print(f"   日期: {self.current_time.strftime('%Y-%m-%d %A')}")

                    elif cmd == "/advance":
                        days = int(parts[1]) if len(parts) > 1 else 1
                        await self.advance_day(days)

                    elif cmd == "/jump":
                        if len(parts) < 2:
                            print("❌ 用法: /jump <天数>")
                        else:
                            target_day = int(parts[1])
                            if 1 <= target_day <= self.story_engine.total_days:
                                days_to_advance = target_day - self.current_day
                                if days_to_advance > 0:
                                    await self.advance_day(days_to_advance)
                                elif days_to_advance < 0:
                                    print("⚠️  不能回到过去")
                                else:
                                    print("ℹ️  已经是当前天数")
                            else:
                                print(f"❌ 天数必须在1-{self.story_engine.total_days}之间")

                    elif cmd == "/story":
                        await self.show_story_progress()

                    elif cmd == "/schedule":
                        agent_id = parts[1] if len(parts) > 1 else default_agent_id
                        await self.show_today_schedule(agent_id)

                    elif cmd == "/phase":
                        current_phase = self.story_engine._get_current_phase(self.current_day)
                        if current_phase:
                            print("\n📌 当前剧情阶段详情:")
                            print(f"   标题: {current_phase.title}")
                            print(f"   主题: {current_phase.theme}")
                            print(f"   范围: 第{current_phase.day_range[0]}-{current_phase.day_range[1]}天")
                            if current_phase.description:
                                print(f"   说明: {current_phase.description}")
                        else:
                            print("⚠️  当前不在任何剧情阶段")

                    elif cmd == "/event":
                        if len(parts) < 2:
                            print("❌ 用法: /event <描述>")
                        else:
                            await self.trigger_event("custom", parts[1])

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
                    # 直接对话
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
    print("🤖 长期剧情智能体系统 - 支持1000+天")
    print("=" * 80)

    system = LongTermAgentSystem(
        story_config_path="/home/user/new_agent_system/config/long_term_story_example.yaml"
    )

    try:
        await system.initialize()
        await system.run()
    except Exception as e:
        print(f"\n❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await system.cleanup()

    print("\n" + "=" * 80)
    print("👋 再见！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
