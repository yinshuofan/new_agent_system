"""
完整的剧情演绎系统 - 修复版
- 修复回复格式显示
- 支持直接对话
- 完整的剧情和角色上下文注入
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent, AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType, get_llm_client


class StorySystemFixed:
    """修复版剧情系统"""

    def __init__(self):
        self.manager = None
        self.story_engine = None
        self.agents: Dict[str, Agent] = {}
        self.llm_client = None
        self.use_llm = False
        self.current_chapter = 1

    def load_config(self):
        """加载配置"""
        config_path = Path(__file__).parent.parent / "config" / "llm_config.yaml"
        if not config_path.exists():
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        active = config.get('active', 'doubao')
        cfg = config.get(active)
        if not cfg:
            return None

        return LLMConfig(
            api_key=cfg['api_key'],
            base_url=cfg.get('base_url'),
            model_mapping={
                ModelType.FAST: cfg['models']['fast'],
                ModelType.ACCURATE: cfg['models']['accurate'],
                ModelType.REASONING: cfg['models']['reasoning']
            },
            max_connections=cfg.get('max_connections', 5),
            timeout=cfg.get('timeout', 60.0)
        )

    async def initialize(self):
        """初始化"""
        print("=" * 70)
        print("🎭 剧情演绎系统 - 完整版")
        print("=" * 70)
        print()

        # 初始化LLM
        config = self.load_config()
        if config:
            try:
                await initialize_llm(config)
                self.llm_client = get_llm_client()
                self.use_llm = True
                print("✓ LLM初始化成功 - 将使用AI生成对话")
            except Exception as e:
                print(f"⚠️  LLM初始化失败: {e}")
                print("   将使用规则模式")
                self.use_llm = False
        else:
            print("⚠️  未找到配置，使用规则模式")
            self.use_llm = False
        print()

        # 创建剧情引擎和管理器
        self.story_engine = StoryEngine(StoryMode.GUIDED, self.use_llm)
        await self.story_engine.initialize()
        self.manager = AgentManager()

    async def create_story(self):
        """创建剧情和角色"""
        # 定义剧情
        theme = "悬疑推理：伦敦盗窃案"
        plot_points = [
            "案发现场：豪宅中发现珍贵珠宝被盗",
            "调查线索：询问证人，检查现场",
            "发现线索：找到可疑痕迹",
            "推理：分析证据，锁定嫌疑人",
            "真相大白：揭露真凶和作案手法"
        ]

        # 生成剧情
        characters = [
            {"agent_id": "holmes", "name": "夏洛克·福尔摩斯", "role": "私家侦探"},
            {"agent_id": "watson", "name": "华生医生", "role": "医生兼助手"}
        ]

        story = await self.story_engine.generate_story(
            theme=theme,
            agent_characters=characters,
            custom_plot=plot_points
        )

        # 创建角色
        for char in characters:
            agent = await self.manager.create_agent(
                agent_id=char["agent_id"],
                name=char["name"],
                config={
                    "role": char["role"],
                    "personality": "聪明、观察力敏锐" if "holmes" in char["agent_id"] else "忠诚、细心",
                    "story_role": char["role"],
                    "story_background": f"你正在调查{theme}"
                },
                use_llm=self.use_llm
            )
            self.agents[char["agent_id"]] = agent

        print(f"✓ 剧情《{story.title}》已创建")
        print(f"✓ 角色: {', '.join([c['name'] for c in characters])}")
        print()

    async def chat_with_agent(self, agent_id: str, message: str):
        """与角色对话 - 包含完整上下文"""
        if agent_id not in self.agents:
            print(f"❌ 角色 '{agent_id}' 不存在")
            return

        agent = self.agents[agent_id]

        # 构建完整上下文
        story = self.story_engine.get_current_story()
        current_plot = self.story_engine.get_current_plot_point()

        # 获取agent的配置
        config = agent.config

        # 如果使用LLM，生成有上下文的回复
        if self.use_llm and self.llm_client:
            context_prompt = f"""你是{agent.name}，{config.get('role', '角色')}。
你的性格：{config.get('personality', '未设定')}

当前剧情：{story.title}
剧情背景：{story.background}
当前章节（第{story.current_plot_index + 1}章）：{current_plot}

请以{agent.name}的身份，结合当前剧情背景，回复用户的问题。
保持角色的性格和语言风格。回复要简洁（1-2句话）。

用户问：{message}
"""

            try:
                response_text = await self.llm_client.generate_text(
                    prompt=context_prompt,
                    model_type=ModelType.FAST,
                    temperature=0.8,
                    max_tokens=150
                )
            except Exception as e:
                response_text = f"（作为{agent.name}）我收到了你的消息：{message}"
        else:
            # 规则模式回复
            response_text = f"（我是{agent.name}，正在{current_plot}中）收到消息：{message}"

        print(f"💬 你: {message}")
        print(f"🎭 {agent.name}: {response_text}")
        print()

        # 存储对话记忆
        await agent.memory.store("event", {
            "event_summary": "对话",
            "event_details": f"用户: {message}\n{agent.name}: {response_text}",
            "participants": ["user", agent_id],
            "importance": 0.6
        })

    def show_story(self):
        """显示剧情"""
        story = self.story_engine.get_current_story()
        print("\n" + "=" * 70)
        print(f"📖 {story.title}")
        print("=" * 70)
        print(f"第 {story.current_plot_index + 1}/{len(story.plot_points)} 章")
        print(f"▶ {self.story_engine.get_current_plot_point()}")
        print("=" * 70 + "\n")

    async def advance(self):
        """推进剧情"""
        if self.story_engine.advance_plot():
            self.current_chapter += 1
            plot = self.story_engine.get_current_plot_point()
            print(f"\n⏩ 第 {self.current_chapter} 章: {plot}\n")
            return True
        print("\n⚠️  剧情已结束\n")
        return False

    async def run(self):
        """运行系统"""
        await self.initialize()
        await self.create_story()
        self.show_story()

        print("=" * 70)
        print("命令:")
        print("  /story   - 显示剧情状态")
        print("  /advance - 推进到下一章")
        print("  /quit    - 退出")
        print()
        print("💡 直接输入 @角色 消息 即可对话")
        print("   例如: @holmes 你发现什么线索了吗？")
        print("=" * 70)
        print()

        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\n👋 再见！\n")
                    break
                elif user_input == "/story":
                    self.show_story()
                elif user_input == "/advance":
                    await self.advance()
                elif user_input.startswith("@"):
                    # @角色 消息
                    parts = user_input[1:].split(maxsplit=1)
                    if len(parts) == 2:
                        agent_id, message = parts
                        await self.chat_with_agent(agent_id, message)
                    else:
                        print("用法: @角色 消息\n")
                else:
                    # 默认与福尔摩斯对话
                    await self.chat_with_agent("holmes", user_input)

            except KeyboardInterrupt:
                print("\n\n👋 退出\n")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")

        # 清理
        for agent in self.agents.values():
            await agent.stop()


async def main():
    system = StorySystemFixed()
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
