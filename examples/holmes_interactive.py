"""
福尔摩斯侦探故事 - 交互式剧情模式
用户可以与福尔摩斯、华生、委托人交互，体验完整的侦探推理过程
"""

import asyncio
import sys
import os
from datetime import datetime, time
from typing import Dict, Optional
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType
from agent_system.llm.prompt_manager import initialize_prompts


class HolmesStorySession:
    """福尔摩斯故事会话管理器"""

    def __init__(self):
        self.manager: Optional[AgentManager] = None
        self.story_engine: Optional[StoryEngine] = None
        self.agents: Dict[str, any] = {}
        self.running = False
        self.current_agent = "holmes"  # 默认与福尔摩斯对话

    async def initialize(self, use_llm: bool = True):
        """初始化故事系统"""
        print("="*70)
        print("🔍 福尔摩斯侦探故事：失踪的家族项链")
        print("="*70)
        print()
        print("正在初始化故事世界...")

        # 创建管理器
        self.manager = AgentManager(max_agents=10)

        # 创建剧情引擎
        self.story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=use_llm,
            deviation_threshold=0.6
        )
        await self.story_engine.initialize()
        print("✓ 剧情引擎已创建")

        # 创建角色
        await self._create_characters(use_llm)

        # 生成剧情
        await self._generate_story()

        print("\n✓ 故事世界初始化完成！")
        print()

    async def _create_characters(self, use_llm: bool):
        """创建故事角色"""
        print("正在创建角色...")

        # 福尔摩斯
        holmes = await self.manager.create_agent(
            agent_id="holmes",
            name="Sherlock Holmes",
            config={
                "role": "detective",
                "personality": "聪明、观察力敏锐、逻辑推理能力强、有时显得冷漠",
                "expertise": "犯罪调查、逻辑推理、化学、小提琴"
            },
            use_llm=use_llm
        )
        holmes.story_engine = self.story_engine
        self.agents["holmes"] = holmes
        print("  ✓ Sherlock Holmes (夏洛克·福尔摩斯) - 私家侦探")

        # 华生
        watson = await self.manager.create_agent(
            agent_id="watson",
            name="Dr. Watson",
            config={
                "role": "assistant",
                "personality": "忠诚、可靠、有医学背景、善于记录",
                "expertise": "医学、协助调查、记录案件"
            },
            use_llm=use_llm
        )
        watson.story_engine = self.story_engine
        self.agents["watson"] = watson
        print("  ✓ Dr. Watson (华生医生) - 福尔摩斯的助手")

        # 委托人
        client = await self.manager.create_agent(
            agent_id="emily",
            name="Emily Wilson",
            config={
                "role": "client",
                "personality": "焦急、担忧、期待、富有",
                "background": "家族项链失踪，价值连城"
            },
            use_llm=use_llm
        )
        client.story_engine = self.story_engine
        self.agents["emily"] = client
        print("  ✓ Emily Wilson (艾米丽·威尔逊) - 委托人")

        # 注册到剧情引擎
        for agent in self.agents.values():
            self.story_engine.register_agent(agent)

        print()

    async def _generate_story(self):
        """生成完整的侦探故事"""
        print("正在生成侦探故事...")

        # 定义详细的剧情点
        plot_points = [
            "08:00 早晨：艾米丽来到贝克街221B，向福尔摩斯求助，声称家族传承的蓝宝石项链在昨晚的宴会后神秘失踪",
            "09:00 接受委托：福尔摩斯和华生详细询问案情，了解宴会宾客名单、项链最后出现的位置和时间",
            "10:30 现场调查：三人前往艾米丽的庄园，福尔摩斯仔细检查项链陈列室，发现几处关键线索",
            "12:00 午餐讨论：在庄园用餐时，福尔摩斯开始推理可能的作案手法和嫌疑人",
            "14:00 访问证人：分别询问管家、女仆和保安，华生记录每个人的证词",
            "15:30 实验验证：福尔摩斯在临时实验室中分析在现场发现的物证",
            "17:00 关键突破：福尔摩斯发现了一个被忽视的细节，案件真相逐渐浮现",
            "18:30 真相揭示：聚集所有相关人员，福尔摩斯推理出项链的真正下落",
            "19:30 找回项链：在福尔摩斯的指引下，项链在一个意想不到的地方被找到",
            "20:00 案件结束：艾米丽感激不尽，福尔摩斯和华生返回贝克街"
        ]

        # 生成剧情大纲
        story_outline = await self.story_engine.generate_story_outline(
            theme="侦探推理：失踪的蓝宝石项链",
            agent_characters=[
                {
                    "agent_id": "holmes",
                    "name": "Sherlock Holmes",
                    "role": "主角侦探，负责推理和破案"
                },
                {
                    "agent_id": "watson",
                    "name": "Dr. Watson",
                    "role": "助手，协助调查和记录"
                },
                {
                    "agent_id": "emily",
                    "name": "Emily Wilson",
                    "role": "委托人，项链失窃的受害者"
                }
            ],
            story_date=datetime.now().strftime("%Y-%m-%d"),
            custom_plot_points=plot_points
        )

        print(f"✓ 故事大纲: {story_outline.title}")
        print(f"  主题: {story_outline.theme}")
        print(f"  剧情点: {len(story_outline.main_plot_points)}个")

        # 为每个角色生成日程
        print("\n正在为角色生成日程...")
        for agent_id, agent in self.agents.items():
            schedule = await self.story_engine.generate_agent_schedule(agent_id, agent)
            print(f"  ✓ {agent.name}: {len(schedule.schedule_items)}个活动")

        print()

    def get_agent_info(self, agent_id: str) -> str:
        """获取角色信息"""
        if agent_id not in self.agents:
            return "未知角色"

        agent = self.agents[agent_id]
        info = f"{agent.name}"

        if agent_id == "holmes":
            info += " 🔍"
        elif agent_id == "watson":
            info += " 📝"
        elif agent_id == "emily":
            info += " 👩"

        return info

    def is_sleeping(self, agent_id: str) -> bool:
        """检查角色是否在睡觉"""
        current_time = datetime.now().time()
        # 22:00-07:00 睡觉时间
        sleep_start = time(22, 0)
        wake_up = time(7, 0)

        if sleep_start > wake_up:
            return current_time >= sleep_start or current_time < wake_up
        else:
            return sleep_start <= current_time < wake_up

    def get_current_activity(self, agent_id: str) -> str:
        """获取角色当前活动"""
        if self.is_sleeping(agent_id):
            return "💤 休息中"

        schedule = self.story_engine.get_agent_schedule(agent_id)
        if schedule:
            current_item = schedule.get_current_activity(datetime.now())
            if current_item:
                return f"{current_item.activity}"
            return "空闲中"

        return "未知"

    async def chat_with_agent(self, agent_id: str, user_message: str) -> str:
        """与指定角色对话"""
        if agent_id not in self.agents:
            return "❌ 该角色不存在"

        agent = self.agents[agent_id]

        # 检查是否在睡觉
        if self.is_sleeping(agent_id):
            return f"💤 {agent.name}现在在休息，请稍后再试。"

        # 让角色感知用户消息
        await agent.perceive_environment({
            "event_type": "user_message",
            "description": f"访客对{agent.name}说: {user_message}",
            "user_input": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # 构建完整上下文
        current_time = datetime.now()
        schedule = self.story_engine.get_agent_schedule(agent_id)

        # 当前活动
        current_activity = "空闲中"
        schedule_summary = ""
        if schedule:
            current_item = schedule.get_current_activity(current_time)
            if current_item:
                current_activity = f"{current_item.activity} - {current_item.description}"

            # 日程摘要
            schedule_summary = "今日任务:\n"
            for item in schedule.schedule_items[:6]:
                status = "✓" if item.status.value == "completed" else "○"
                schedule_summary += f"{status} {item.start_time}: {item.activity}\n"

        # 情感和目标
        emotion = agent.emotion.get_current_emotion()
        goals = agent.goal.get_active_goals()
        goals_text = "\n".join([f"- {g.get('title', 'N/A')}" for g in goals[:3]])

        # 记忆
        memories = await agent.memory.retrieve({"memory_type": "event"}, limit=5)
        memories_text = "\n".join([
            f"- {m.get('content', {}).get('event_summary', '')}"
            for m in memories if m.get('content', {}).get('event_summary')
        ])

        # 角色特性
        role = agent.config.get("role", "")
        personality = agent.config.get("personality", "")

        # 故事中的角色
        story_role = ""
        if self.story_engine._current_outline:
            outline = self.story_engine._current_outline
            story_role = outline.character_roles.get(agent_id, "")
            story_goal = outline.character_goals.get(agent_id, "")
            if story_role:
                story_role = f"剧情角色: {story_role}\n剧情目标: {story_goal}"

        # 构建对话上下文
        context = f"""你是 {agent.name}。

性格: {personality}
职业: {role}
{story_role}

当前时间: {current_time.strftime('%H:%M')}
当前正在做: {current_activity}

{schedule_summary}

你的情绪: {emotion.get('primary_emotion', 'neutral')}
你的目标:
{goals_text}

最近的记忆:
{memories_text}

访客对你说: {user_message}

请以{agent.name}的身份自然地回复访客。要符合你的性格特点，并体现你当前正在做的事情。"""

        # 使用认知模块生成回复
        decision = await agent.cognition.make_decision(
            situation=context,
            emotion=emotion,
            goals=goals,
            memories=memories_text
        )

        # 提取回复
        reply = ""
        if isinstance(decision, dict):
            reasoning = decision.get("reasoning", "")
            if reasoning:
                reply = reasoning
            else:
                reply = f"(思考中...关于{user_message})"
        else:
            reply = "我明白了。"

        # 记录对话
        await agent.memory.store("event", {
            "event_type": "conversation",
            "event_summary": f"与访客对话: {user_message[:30]}",
            "event_details": f"访客: {user_message}\n{agent.name}: {reply}",
            "participants": ["visitor", agent_id],
            "timestamp": current_time.isoformat()
        })

        return reply

    async def show_status(self):
        """显示所有角色状态"""
        print("\n" + "="*70)
        print("📊 当前状态")
        print("="*70)

        for agent_id, agent in self.agents.items():
            activity = self.get_current_activity(agent_id)
            emotion = agent.emotion.get_current_emotion()

            print(f"\n{self.get_agent_info(agent_id)}")
            print(f"  当前活动: {activity}")
            print(f"  情绪: {emotion.get('primary_emotion', 'neutral')}")

        print("\n" + "="*70 + "\n")

    async def show_schedule(self, agent_id: str):
        """显示指定角色的日程"""
        if agent_id not in self.agents:
            print("❌ 该角色不存在")
            return

        agent = self.agents[agent_id]
        schedule = self.story_engine.get_agent_schedule(agent_id)

        print(f"\n📅 {agent.name}的日程")
        print("-"*70)
        if schedule:
            print(schedule.get_summary())
        else:
            print("暂无日程")
        print("-"*70 + "\n")

    async def cleanup(self):
        """清理资源"""
        if self.manager:
            await self.manager.stop_all()


async def main():
    """主函数"""
    # 初始化LLM
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

    # 加载提示词
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    if os.path.exists(prompts_path):
        initialize_prompts(prompts_path)

    # 创建故事会话
    session = HolmesStorySession()
    await session.initialize(use_llm=use_llm)

    # 显示欢迎信息
    print("="*70)
    print("🎭 欢迎来到福尔摩斯的世界！")
    print("="*70)
    print()
    print("故事背景：")
    print("  艾米丽·威尔逊家族传承的蓝宝石项链在昨晚的宴会后神秘失踪。")
    print("  她来到贝克街221B，请求大侦探福尔摩斯帮助找回项链。")
    print()
    print("可用角色：")
    print("  1. holmes  - Sherlock Holmes (夏洛克·福尔摩斯) 🔍")
    print("  2. watson  - Dr. Watson (华生医生) 📝")
    print("  3. emily   - Emily Wilson (艾米丽·威尔逊) 👩")
    print()
    print("命令：")
    print("  @<角色ID> <消息>  - 与指定角色对话，例如: @holmes 你好")
    print("  /status          - 查看所有角色状态")
    print("  /schedule <角色>  - 查看角色日程")
    print("  /help            - 显示帮助")
    print("  /quit            - 退出")
    print()
    print("提示：直接输入消息默认与福尔摩斯对话")
    print("="*70)
    print()

    session.running = True
    current_agent = "holmes"

    # 主循环
    while session.running:
        try:
            # 显示提示符
            prompt_name = session.get_agent_info(current_agent)
            user_input = input(f"\n💬 你 -> {prompt_name}: ").strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith('/'):
                cmd_parts = user_input.split()
                cmd = cmd_parts[0].lower()

                if cmd == '/quit':
                    print("\n👋 感谢参与！再见！")
                    session.running = False
                    break

                elif cmd == '/status':
                    await session.show_status()

                elif cmd == '/schedule':
                    agent_id = cmd_parts[1] if len(cmd_parts) > 1 else current_agent
                    await session.show_schedule(agent_id)

                elif cmd == '/help':
                    print("\n可用命令：")
                    print("  @<角色ID> <消息>  - 与指定角色对话")
                    print("  /status          - 查看所有角色状态")
                    print("  /schedule <角色>  - 查看角色日程")
                    print("  /help            - 显示帮助")
                    print("  /quit            - 退出")
                    print()

                else:
                    print(f"❌ 未知命令: {cmd}")

            # 处理角色切换
            elif user_input.startswith('@'):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("❌ 格式错误，使用: @<角色ID> <消息>")
                    continue

                target_agent = parts[0][1:].lower()  # 去掉@
                message = parts[1]

                if target_agent not in session.agents:
                    print(f"❌ 角色 '{target_agent}' 不存在")
                    print("可用角色: holmes, watson, emily")
                    continue

                current_agent = target_agent
                reply = await session.chat_with_agent(current_agent, message)
                print(f"\n🤖 {session.get_agent_info(current_agent)}: {reply}")

            # 普通对话（与当前角色）
            else:
                reply = await session.chat_with_agent(current_agent, user_input)
                print(f"\n🤖 {session.get_agent_info(current_agent)}: {reply}")

        except KeyboardInterrupt:
            print("\n\n收到中断信号...")
            session.running = False
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    # 清理
    await session.cleanup()
    print("\n✓ 故事会话已结束\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
