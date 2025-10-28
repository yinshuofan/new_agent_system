"""
剧情演绎系统 - 使用配置文件的LLM版本
支持从 config/llm_config.yaml 读取配置
"""

import asyncio
import sys
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent, AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType


class StoryWithLLM:
    """使用LLM的剧情演绎系统"""

    def __init__(self):
        self.manager = None
        self.story_engine = None
        self.agents: Dict[str, Agent] = {}
        self.running = False
        self.current_chapter = 1
        self.llm_config = None

    def load_llm_config(self):
        """从配置文件加载LLM配置"""
        config_path = Path(__file__).parent.parent / "config" / "llm_config.yaml"

        if not config_path.exists():
            print(f"⚠️  配置文件不存在: {config_path}")
            print(f"   请创建配置文件或使用 --no-llm 模式")
            return None

        print(f"📋 加载配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        active_config_name = config.get('active', 'doubao')
        active_config = config.get(active_config_name)

        if not active_config:
            print(f"⚠️  配置 '{active_config_name}' 不存在")
            return None

        print(f"   使用配置: {active_config_name}")
        print(f"   Base URL: {active_config.get('base_url')}")
        print(f"   模型: {active_config.get('models', {}).get('fast')}")

        return LLMConfig(
            api_key=active_config['api_key'],
            base_url=active_config.get('base_url'),
            model_mapping={
                ModelType.FAST: active_config['models']['fast'],
                ModelType.ACCURATE: active_config['models']['accurate'],
                ModelType.REASONING: active_config['models']['reasoning']
            },
            max_connections=active_config.get('max_connections', 5),
            timeout=active_config.get('timeout', 60.0)
        )

    async def initialize(self):
        """初始化系统"""
        print("=" * 70)
        print("🎭 剧情演绎系统 - LLM版本")
        print("=" * 70)
        print()

        # 加载配置
        print("🔑 加载LLM配置...")
        self.llm_config = self.load_llm_config()

        if self.llm_config:
            print("   ✓ 配置加载成功")
            try:
                print("   正在初始化LLM...")
                await initialize_llm(self.llm_config)
                print("   ✓ LLM初始化成功")
                print("   📡 将使用真实AI生成剧情和对话")
                use_llm = True
            except Exception as e:
                print(f"   ⚠️  LLM初始化失败: {e}")
                print(f"   💡 将使用规则模式运行")
                use_llm = False
        else:
            print("   ⚠️  未能加载配置")
            print("   💡 将使用规则模式运行")
            use_llm = False
        print()

        # 创建剧情引擎
        print("📖 创建剧情引擎...")
        self.story_engine = StoryEngine(
            story_mode=StoryMode.GUIDED,
            use_llm=use_llm
        )
        await self.story_engine.initialize()
        print("   ✓ 剧情引擎已创建")
        print()

        # 创建智能体管理器
        print("🤖 创建智能体管理器...")
        self.manager = AgentManager()
        print("   ✓ 管理器已创建")
        print()

        return use_llm

    async def create_story(self, use_llm: bool):
        """创建剧情"""
        print("=" * 70)
        print("📝 创建剧情")
        print("=" * 70)
        print()

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
            }
        ]

        print(f"主题: {theme}")
        print(f"角色数: {len(characters)}")
        print()

        # 生成剧情
        print("🎬 生成剧情...")
        custom_plot = [
            "案发现场：豪宅中发现盗窃案",
            "调查线索：收集证据和询问证人",
            "发现关键线索：找到重要证据",
            "对峙：与嫌疑人智力较量",
            "真相大白：揭示案件真相"
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
                    "expertise": char["expertise"]
                },
                use_llm=use_llm
            )
            self.agents[char["agent_id"]] = agent
            print(f"   ✓ {char['name']} 已创建")

        print()

    async def show_story(self):
        """显示剧情"""
        story = self.story_engine.get_current_story()
        print("\n" + "=" * 70)
        print("📖 剧情状态")
        print("=" * 70)
        print(f"标题: {story.title}")
        print(f"当前章节: {story.current_plot_index + 1}/{len(story.plot_points)}")
        print()

        current_plot = self.story_engine.get_current_plot_point()
        if current_plot:
            print(f"▶ 当前: {current_plot}")
        print("=" * 70 + "\n")

    async def advance_story(self):
        """推进剧情"""
        if self.story_engine.advance_plot():
            self.current_chapter += 1
            new_plot = self.story_engine.get_current_plot_point()
            print(f"\n⏩ 进入第 {self.current_chapter} 章")
            print(f"📖 {new_plot}\n")
            return True
        return False

    async def chat_with_agent(self, agent_id: str, message: str):
        """与角色对话"""
        if agent_id not in self.agents:
            print(f"❌ 角色 {agent_id} 不存在")
            return

        agent = self.agents[agent_id]
        print(f"\n💬 你: {message}")

        response = await agent.receive_message(
            sender_id="user",
            message=message,
            metadata={}
        )

        print(f"🎭 {agent.name}: {response}\n")

    async def run(self):
        """运行系统"""
        use_llm = await self.initialize()
        await self.create_story(use_llm)
        await self.show_story()

        print("=" * 70)
        print("🎮 系统已就绪")
        print("=" * 70)
        print("命令:")
        print("  /story   - 显示剧情")
        print("  /advance - 推进剧情")
        print("  /talk <角色> <消息> - 对话 (例: /talk holmes 你好)")
        print("  /quit    - 退出")
        print("=" * 70)
        print()

        self.running = True
        while self.running:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\n👋 再见！")
                    break
                elif user_input == "/story":
                    await self.show_story()
                elif user_input == "/advance":
                    if not await self.advance_story():
                        print("⚠️  剧情已结束\n")
                elif user_input.startswith("/talk "):
                    parts = user_input.split(maxsplit=2)
                    if len(parts) < 3:
                        print("用法: /talk <角色> <消息>\n")
                    else:
                        await self.chat_with_agent(parts[1], parts[2])
                else:
                    print("未知命令。输入 /quit 退出\n")

            except KeyboardInterrupt:
                print("\n\n👋 退出中...")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")

        # 清理
        for agent in self.agents.values():
            await agent.stop()


async def main():
    system = StoryWithLLM()
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
