"""
福尔摩斯侦探故事 V2.0 - 新架构版本
基于优化后的架构：
- 使用ContextManager统一管理上下文
- 使用YAML配置文件定义剧情
- 剧情自动推进
- 支持用户随时对话
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import AgentManager
from agent_system.story import StoryEngine, StoryMode, StoryLoader
from agent_system.llm import initialize_llm, LLMConfig, ModelType
from agent_system.llm.prompt_manager import initialize_prompts


class HolmesStoryV2:
    """福尔摩斯故事V2 - 基于新架构"""

    def __init__(self, story_config_path: str, use_llm: bool = False):
        self.story_config_path = story_config_path
        self.use_llm = use_llm

        self.manager: Optional[AgentManager] = None
        self.story_engine: Optional[StoryEngine] = None
        self.story_config = None
        self.agents: Dict = {}
        self.current_agent_id = "holmes"
        self.running = False

    async def initialize(self):
        """初始化故事系统"""
        print("="*70)
        print("🔍 福尔摩斯侦探故事 V2.0")
        print("="*70)
        print()

        # 1. 加载剧情配置
        print("📖 加载剧情配置...")
        self.story_config = StoryLoader.load_from_file(self.story_config_path)
        print(f"✓ 故事: {self.story_config.title}")
        print(f"✓ 主题: {self.story_config.theme}")
        print(f"✓ 角色: {len(self.story_config.characters)}个")
        print(f"✓ 章节: {len(self.story_config.timeline)}个")
        print()

        # 2. 创建管理器
        self.manager = AgentManager(max_agents=10)

        # 3. 创建剧情引擎
        self.story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=self.use_llm,
            deviation_threshold=self.story_config.deviation_threshold
        )
        await self.story_engine.initialize()

        # 4. 从配置创建剧情大纲
        print("📝 生成剧情大纲...")
        story_outline = StoryLoader.create_story_outline_from_config(self.story_config)
        self.story_engine._current_outline = story_outline
        print(f"✓ 剧情大纲已生成")
        print()

        # 5. 创建角色
        print("👥 创建角色...")
        for char_id, char_config in self.story_config.characters.items():
            agent = await self.manager.create_agent(
                agent_id=char_id,
                name=char_config.get("name", char_id),
                config={
                    "role": char_config.get("role", ""),
                    "personality": char_config.get("personality", ""),
                    "expertise": char_config.get("expertise", []),
                    "background": char_config.get("background", "")
                },
                use_llm=self.use_llm
            )

            # 注册到剧情引擎
            self.story_engine.register_agent(agent)
            agent.story_engine = self.story_engine

            self.agents[char_id] = agent
            display_name = char_config.get("display_name", char_config.get("name", char_id))
            print(f"  ✓ {display_name} ({char_config.get('role', '')})")

        print()

        # 6. 生成角色日程
        print("📅 生成角色日程...")
        for char_id in self.agents.keys():
            schedule = StoryLoader.generate_schedule_from_config(
                self.story_config,
                char_id
            )
            self.story_engine._agent_schedules[char_id] = schedule
            print(f"  ✓ {self.agents[char_id].name}: {len(schedule.schedule_items)}个活动")

        print()
        print("✓ 故事世界初始化完成！")
        print()

    def show_welcome(self):
        """显示欢迎信息"""
        print("="*70)
        print("🎭 欢迎进入福尔摩斯的世界！")
        print("="*70)
        print()
        print("📖 故事背景：")
        print(f"  {self.story_config.metadata.get('theme', '')}")
        print()
        print("👥 可用角色：")
        for char_id, char_config in self.story_config.characters.items():
            emoji = {"holmes": "🔍", "watson": "📝", "emily": "👩"}.get(char_id, "👤")
            display_name = char_config.get("display_name", char_config.get("name", ""))
            role = char_config.get("role", "")
            print(f"  {emoji} {char_id} - {display_name} ({role})")
        print()
        print("⌨️  命令：")
        print("  @<角色ID> <消息>  - 与指定角色对话")
        print("  /status            - 查看所有角色状态")
        print("  /schedule <角色>   - 查看角色日程")
        print("  /story             - 查看剧情进度")
        print("  /context <角色>    - 查看角色完整上下文")
        print("  /help              - 显示帮助")
        print("  /quit              - 退出")
        print()
        print("💡 提示：直接输入消息默认与福尔摩斯对话")
        print("="*70)
        print()

    async def chat_with_agent(self, agent_id: str, message: str) -> str:
        """
        与角色对话 - 使用新的ContextManager

        Args:
            agent_id: 角色ID
            message: 用户消息

        Returns:
            角色回复
        """
        if agent_id not in self.agents:
            return f"❌ 角色 '{agent_id}' 不存在"

        agent = self.agents[agent_id]

        # 1. 让角色感知用户消息
        await agent.perceive_environment({
            "event_type": "user_message",
            "description": f"用户说: {message}",
            "user_input": message,
            "timestamp": datetime.now().isoformat()
        })

        # 2. 使用ContextManager获取完整上下文
        full_context = await agent.context_manager.get_full_context(trigger=f"user_chat: {message}")

        # 3. 格式化上下文为LLM友好的格式
        context_text = agent.context_manager.format_context_for_llm(full_context, "chat")

        # 4. 添加用户消息
        context_text += f"\n\n## 用户消息\n{message}\n\n"
        context_text += "请以角色身份自然回复用户。要符合你的性格特点，并体现你当前的状态和正在做的事情。"

        # 5. 使用认知模块生成回复
        decision = await agent.cognition.make_decision(
            situation=context_text,
            emotion=full_context.get("emotion", {}),
            goals=full_context.get("goals", {}).get("goals", []),
            memories=str(full_context.get("memories", {}))
        )

        # 6. 提取回复
        reply = ""
        if isinstance(decision, dict):
            reasoning = decision.get("reasoning", "")
            if reasoning:
                reply = reasoning
            else:
                reply = f"（我在思考关于'{message}'...）"
        else:
            reply = "让我想想..."

        # 7. 记录对话到记忆
        await agent.memory.store("event", {
            "event_type": "conversation",
            "event_summary": f"与用户对话: {message[:30]}",
            "event_details": f"用户: {message}\n{agent.name}: {reply}",
            "participants": ["user", agent_id],
            "timestamp": datetime.now().isoformat()
        })

        return reply

    async def show_status(self):
        """显示所有角色状态"""
        print("\n" + "="*70)
        print("📊 当前状态")
        print("="*70)

        for agent_id, agent in self.agents.items():
            # 获取完整上下文
            context = await agent.context_manager.get_full_context()

            print(f"\n{agent.name}:")

            # 当前活动
            schedule = context.get("schedule", {})
            if schedule.get("current_activity"):
                activity = schedule["current_activity"]
                print(f"  📋 {activity['activity']}")
                print(f"      {activity['description']}")
            else:
                print(f"  🕐 空闲中")

            # 情感
            emotion = context.get("emotion", {})
            if emotion.get("available"):
                print(f"  💭 {emotion['primary_emotion']}")

        print("\n" + "="*70 + "\n")

    async def show_schedule(self, agent_id: str):
        """显示角色日程"""
        if agent_id not in self.agents:
            print(f"❌ 角色 '{agent_id}' 不存在")
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

    async def show_story_progress(self):
        """显示剧情进度"""
        print("\n" + "="*70)
        print("📖 剧情进度")
        print("="*70)

        current_time = datetime.now()
        current_event = self.story_config.get_current_event(current_time)
        next_event = self.story_config.get_next_event(current_time)

        if current_event:
            print(f"\n当前章节: 第{current_event.get('chapter', '?')}章")
            print(f"标题: {current_event.get('title', '')}")
            print(f"时间: {current_event.get('time', '')}")
            print(f"地点: {current_event.get('location', '')}")

        if next_event:
            print(f"\n下一章节: 第{next_event.get('chapter', '?')}章")
            print(f"标题: {next_event.get('title', '')}")
            print(f"时间: {next_event.get('time', '')}")

        print("\n" + "="*70 + "\n")

    async def show_full_context(self, agent_id: str):
        """显示角色完整上下文"""
        if agent_id not in self.agents:
            print(f"❌ 角色 '{agent_id}' 不存在")
            return

        agent = self.agents[agent_id]
        context = await agent.context_manager.get_full_context()
        formatted = agent.context_manager.format_context_for_llm(context)

        print("\n" + "="*70)
        print(f"📋 {agent.name} 的完整上下文")
        print("="*70)
        print(formatted)
        print("="*70 + "\n")

    async def run(self):
        """运行主循环"""
        self.show_welcome()
        self.running = True

        while self.running:
            try:
                # 显示提示符
                agent_name = self.agents[self.current_agent_id].name
                char_config = self.story_config.get_character_config(self.current_agent_id)
                display_name = char_config.get("display_name", agent_name)
                emoji = {"holmes": "🔍", "watson": "📝", "emily": "👩"}.get(self.current_agent_id, "👤")

                user_input = input(f"\n💬 你 -> {display_name} {emoji}: ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith('/'):
                    await self.handle_command(user_input)

                # 处理角色切换
                elif user_input.startswith('@'):
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("❌ 格式错误，使用: @<角色ID> <消息>")
                        continue

                    target_agent = parts[0][1:].lower()
                    message = parts[1]

                    if target_agent not in self.agents:
                        print(f"❌ 角色 '{target_agent}' 不存在")
                        print(f"可用角色: {', '.join(self.agents.keys())}")
                        continue

                    self.current_agent_id = target_agent
                    reply = await self.chat_with_agent(target_agent, message)

                    char_config = self.story_config.get_character_config(target_agent)
                    display_name = char_config.get("display_name", self.agents[target_agent].name)
                    emoji = {"holmes": "🔍", "watson": "📝", "emily": "👩"}.get(target_agent, "👤")
                    print(f"\n🤖 {display_name} {emoji}: {reply}")

                # 普通对话
                else:
                    reply = await self.chat_with_agent(self.current_agent_id, user_input)

                    char_config = self.story_config.get_character_config(self.current_agent_id)
                    display_name = char_config.get("display_name", self.agents[self.current_agent_id].name)
                    emoji = {"holmes": "🔍", "watson": "📝", "emily": "👩"}.get(self.current_agent_id, "👤")
                    print(f"\n🤖 {display_name} {emoji}: {reply}")

            except KeyboardInterrupt:
                print("\n\n收到中断信号...")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                import traceback
                traceback.print_exc()

    async def handle_command(self, command: str):
        """处理命令"""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == '/quit':
            print("\n👋 感谢体验！再见！")
            self.running = False

        elif cmd == '/status':
            await self.show_status()

        elif cmd == '/schedule':
            agent_id = parts[1] if len(parts) > 1 else self.current_agent_id
            await self.show_schedule(agent_id)

        elif cmd == '/story':
            await self.show_story_progress()

        elif cmd == '/context':
            agent_id = parts[1] if len(parts) > 1 else self.current_agent_id
            await self.show_full_context(agent_id)

        elif cmd == '/help':
            print("\n可用命令：")
            print("  @<角色ID> <消息>  - 与指定角色对话")
            print("  /status            - 查看所有角色状态")
            print("  /schedule <角色>   - 查看角色日程")
            print("  /story             - 查看剧情进度")
            print("  /context <角色>    - 查看角色完整上下文")
            print("  /help              - 显示帮助")
            print("  /quit              - 退出")
            print()

        else:
            print(f"❌ 未知命令: {cmd}")

    async def cleanup(self):
        """清理资源"""
        if self.manager:
            await self.manager.stop_all()


async def main():
    """主函数"""
    # 初始化LLM（可选）
    api_key = os.getenv("OPENAI_API_KEY", "")
    use_llm = bool(api_key and api_key != "demo-key")

    if use_llm:
        try:
            llm_config = LLMConfig(
                api_key=api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                model_mapping={
                    ModelType.FAST: "doubao-seed-1-6-251015",
                    ModelType.ACCURATE: "doubao-seed-1-6-251015",
                    ModelType.REASONING: "doubao-seed-1-6-251015"
                }
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

    # 剧情配置文件路径
    story_config_path = "/home/user/new_agent_system/config/holmes_story.yaml"

    # 创建并运行故事
    story = HolmesStoryV2(story_config_path, use_llm=use_llm)

    try:
        await story.initialize()
        await story.run()
    finally:
        await story.cleanup()
        print("\n✓ 故事会话已结束\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
