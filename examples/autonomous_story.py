"""
自主运行剧情系统
- 智能体自主执行行动（不需要用户触发）
- 自动推进剧情
- 完整的上下文注入
- 用户可随时介入交流
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import Dict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent, AgentManager
from agent_system.story import StoryEngine, StoryMode
from agent_system.llm import initialize_llm, LLMConfig, ModelType, get_llm_client


class AutonomousStorySystem:
    """自主运行的剧情系统"""

    def __init__(self):
        self.manager = None
        self.story_engine = None
        self.agents: Dict[str, Agent] = {}
        self.llm_client = None
        self.use_llm = False

        # 自主运行控制
        self.running = False
        self.autonomous_enabled = True
        self.action_interval = 5  # 每5秒执行一次自主行动
        self.current_chapter = 1

        # 用户输入队列
        self.user_input_queue = asyncio.Queue()

    def load_config(self):
        """加载LLM配置"""
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
        """初始化系统"""
        print("=" * 70)
        print("🎭 自主运行剧情系统")
        print("=" * 70)
        print()

        # 初始化LLM
        config = self.load_config()
        if config:
            try:
                await initialize_llm(config)
                self.llm_client = get_llm_client()
                self.use_llm = True
                print("✓ LLM初始化成功")
            except Exception as e:
                print(f"⚠️  LLM初始化失败: {e}")
                self.use_llm = False
        else:
            self.use_llm = False
        print()

        # 创建系统组件
        self.story_engine = StoryEngine(StoryMode.GUIDED, self.use_llm)
        await self.story_engine.initialize()
        self.manager = AgentManager()

    async def create_story(self):
        """创建剧情和角色"""
        print("📖 创建剧情...")

        theme = "悬疑推理：伦敦盗窃案"
        plot_points = [
            "案发：珍贵珠宝在豪宅中被盗",
            "调查：侦探抵达现场开始调查",
            "线索：发现可疑痕迹和证人证言",
            "推理：分析证据，锁定嫌疑人",
            "真相：揭露真凶和完整作案过程"
        ]

        characters = [
            {
                "agent_id": "holmes",
                "name": "福尔摩斯",
                "role": "私家侦探",
                "personality": "聪明、观察力敏锐、逻辑性强",
                "actions": ["检查现场", "询问证人", "分析证据", "推理案情"]
            },
            {
                "agent_id": "watson",
                "name": "华生",
                "role": "助手",
                "personality": "忠诚、细心、善于记录",
                "actions": ["协助调查", "记录发现", "询问周围", "提供意见"]
            }
        ]

        story = await self.story_engine.generate_story(
            theme=theme,
            agent_characters=[{"agent_id": c["agent_id"], "name": c["name"], "role": c["role"]}
                            for c in characters],
            custom_plot=plot_points
        )

        # 创建角色
        for char in characters:
            agent = await self.manager.create_agent(
                agent_id=char["agent_id"],
                name=char["name"],
                config={
                    "role": char["role"],
                    "personality": char["personality"],
                    "possible_actions": char["actions"],
                    "story_context": f"{theme} - {story.plot_points[0]}"
                },
                use_llm=self.use_llm
            )
            self.agents[char["agent_id"]] = agent

        print(f"✓ 剧情《{story.title}》已创建")
        print(f"✓ 角色: {', '.join([c['name'] for c in characters])}")
        print()

    async def agent_autonomous_action(self, agent_id: str):
        """智能体执行自主行动"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        story = self.story_engine.get_current_story()
        current_plot = self.story_engine.get_current_plot_point()

        # 获取可能的行动
        possible_actions = agent.config.get("possible_actions", ["思考", "观察"])

        # 如果有LLM，让AI决定行动
        if self.use_llm and self.llm_client:
            context_prompt = f"""你是{agent.name}，{agent.config.get('role')}。
性格：{agent.config.get('personality')}

当前剧情：{story.title}
当前章节（第{story.current_plot_index + 1}章）：{current_plot}

可选行动：{', '.join(possible_actions)}

根据当前剧情，你会采取什么行动？从可选行动中选择一个，并简单说明理由（1句话）。
格式：行动：[选择的行动] - 理由：[简短理由]
"""
            try:
                response = await self.llm_client.generate_text(
                    prompt=context_prompt,
                    model_type=ModelType.FAST,
                    temperature=0.8,
                    max_tokens=100
                )
                action_text = response.strip()
            except:
                # 降级：随机选择
                import random
                action = random.choice(possible_actions)
                action_text = f"{action}中..."
        else:
            # 规则模式：根据章节选择行动
            import random
            action = random.choice(possible_actions)
            action_text = f"{action}中..."

        # 显示行动
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🎬 {agent.name}: {action_text}")

        # 存储行动记忆
        await agent.memory.store("event", {
            "event_summary": f"{agent.name}的行动",
            "event_details": action_text,
            "participants": [agent_id],
            "importance": 0.7
        })

        # 检查是否应该推进剧情
        # 每个角色行动2次后推进
        memories = await agent.memory.retrieve({"memory_type": "event"}, limit=10)
        if len(memories) >= 4:  # 两个角色各行动2次
            await self.advance_story()

    async def advance_story(self):
        """推进剧情"""
        if self.story_engine.advance_plot():
            self.current_chapter += 1
            plot = self.story_engine.get_current_plot_point()

            print("\n" + "=" * 70)
            print(f"📖 剧情推进！进入第 {self.current_chapter} 章")
            print(f"▶ {plot}")
            print("=" * 70 + "\n")

            # 更新所有角色的剧情上下文
            for agent in self.agents.values():
                agent.config["story_context"] = plot

            return True
        return False

    async def chat_with_agent(self, agent_id: str, message: str):
        """与角色对话"""
        if agent_id not in self.agents:
            print(f"❌ 角色 {agent_id} 不存在")
            return

        agent = self.agents[agent_id]
        story = self.story_engine.get_current_story()
        current_plot = self.story_engine.get_current_plot_point()

        if self.use_llm and self.llm_client:
            context_prompt = f"""你是{agent.name}，{agent.config.get('role')}。
性格：{agent.config.get('personality')}

当前剧情：{story.title}
当前章节（第{story.current_plot_index + 1}章）：{current_plot}

请以角色身份回复用户，保持性格特点。回复要简洁（1-2句话）。

用户问：{message}
"""
            try:
                response = await self.llm_client.generate_text(
                    prompt=context_prompt,
                    model_type=ModelType.FAST,
                    temperature=0.8,
                    max_tokens=150
                )
            except:
                response = f"（作为{agent.name}）{message}"
        else:
            response = f"（我是{agent.name}，正在{current_plot}）收到：{message}"

        print(f"💬 你 → {agent.name}: {message}")
        print(f"🎭 {agent.name}: {response}")
        print()

    def show_status(self):
        """显示状态"""
        story = self.story_engine.get_current_story()
        print("\n" + "=" * 70)
        print(f"📖 {story.title}")
        print(f"章节: 第 {story.current_plot_index + 1}/{len(story.plot_points)} 章")
        print(f"▶ {self.story_engine.get_current_plot_point()}")
        print(f"自主运行: {'✓ 开启' if self.autonomous_enabled else '✗ 暂停'}")
        print("=" * 70 + "\n")

    async def autonomous_loop(self):
        """自主运行循环"""
        agent_ids = list(self.agents.keys())
        agent_index = 0

        while self.running:
            if self.autonomous_enabled:
                # 轮流让每个智能体执行行动
                agent_id = agent_ids[agent_index]
                await self.agent_autonomous_action(agent_id)

                agent_index = (agent_index + 1) % len(agent_ids)

                # 等待间隔
                await asyncio.sleep(self.action_interval)
            else:
                # 暂停时短暂等待
                await asyncio.sleep(0.5)

    async def input_loop(self):
        """用户输入循环"""
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # 异步读取用户输入
                user_input = await loop.run_in_executor(None, input, "> ")
                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    print("\n👋 退出中...\n")
                    self.running = False
                    break

                elif user_input == "/pause":
                    self.autonomous_enabled = False
                    print("⏸️  已暂停自主运行\n")

                elif user_input == "/resume":
                    self.autonomous_enabled = True
                    print("▶️  已恢复自主运行\n")

                elif user_input == "/status":
                    self.show_status()

                elif user_input.startswith("@"):
                    # @角色 消息
                    parts = user_input[1:].split(maxsplit=1)
                    if len(parts) == 2:
                        await self.chat_with_agent(parts[0], parts[1])
                    else:
                        print("用法: @角色 消息\n")

                else:
                    # 默认与福尔摩斯对话
                    await self.chat_with_agent("holmes", user_input)

            except EOFError:
                break
            except Exception as e:
                print(f"错误: {e}\n")

    async def run(self):
        """运行系统"""
        await self.initialize()
        await self.create_story()

        print("=" * 70)
        print("🎮 系统启动")
        print("=" * 70)
        print()
        print("🤖 智能体将自主执行行动")
        print(f"⏱️  行动间隔: {self.action_interval}秒")
        print()
        print("💡 命令:")
        print("  /pause   - 暂停自主运行")
        print("  /resume  - 恢复自主运行")
        print("  /status  - 查看状态")
        print("  /quit    - 退出")
        print()
        print("💡 对话:")
        print("  直接输入 - 与福尔摩斯对话")
        print("  @watson 消息 - 与华生对话")
        print("=" * 70)
        print()

        self.show_status()

        self.running = True

        # 创建并发任务
        autonomous_task = asyncio.create_task(self.autonomous_loop())
        input_task = asyncio.create_task(self.input_loop())

        # 等待任意任务完成
        done, pending = await asyncio.wait(
            [autonomous_task, input_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # 取消未完成的任务
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # 清理
        print("\n🧹 清理资源...")
        for agent in self.agents.values():
            await agent.stop()
        print("✓ 完成\n")


async def main():
    system = AutonomousStorySystem()
    await system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已退出\n")
