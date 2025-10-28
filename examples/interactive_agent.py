"""
交互式智能体示例
- 持久化运行
- 完整LLM功能
- 交互式对话
- 完整的智能体功能（记忆、情感、目标）
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_system import Agent
from agent_system.llm import initialize_llm, get_llm_client, LLMConfig


class InteractiveAgent:
    """交互式智能体系统"""

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.agent = None
        self.running = False

    async def initialize(self):
        """初始化系统"""
        print("=" * 70)
        print("🤖 交互式智能体系统")
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
                    print("   📡 使用真实AI模型进行对话")
                except Exception as e:
                    print(f"   ⚠️ LLM初始化失败: {e}")
                    print("   💡 将使用规则模式运行")
                    self.use_llm = False
            else:
                print("   ⚠️ 未找到API Key")
                print("   💡 设置方法: export OPENAI_API_KEY='your-key'")
                print("   💡 将使用规则模式运行")
                self.use_llm = False
            print()

        # 创建智能体
        print("🤖 创建智能体...")
        self.agent = Agent(
            agent_id="assistant_001",
            name="AI助手",
            config={
                "max_memories": 1000,
                "role": "智能助手",
                "personality": "友好、乐于助人、善于倾听",
                "expertise": ["对话交流", "信息检索", "问题解答"]
            },
            use_llm=self.use_llm
        )
        await self.agent.start()
        print(f"   ✓ 智能体 '{self.agent.name}' 已创建")
        print()

        # 设置初始目标
        print("🎯 设置初始目标...")
        await self.agent.add_goal({
            "title": "提供优质服务",
            "description": "帮助用户解决问题，提供有价值的信息",
            "priority": 3
        })
        print("   ✓ 目标已设置")
        print()

    async def show_status(self):
        """显示智能体状态"""
        print("\n" + "=" * 70)
        print("📊 智能体状态")
        print("=" * 70)

        status = self.agent.get_status()
        emotion = self.agent.emotion.get_current_emotion()
        goals = self.agent.goal.get_active_goals()

        print(f"名称: {status['name']}")
        print(f"ID: {status['agent_id']}")
        print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"LLM模式: {'真实AI' if self.use_llm else '规则模式'}")
        print()

        print(f"情感状态: {emotion.get('primary_emotion', 'neutral')}")
        print(f"情感效价: {emotion.get('valence', 0.0):.2f}")
        print(f"唤醒度: {emotion.get('arousal', 0.0):.2f}")
        print()

        mem_stats = status['modules']['memory']
        print(f"记忆统计:")
        print(f"  - 事件记忆: {mem_stats.get('event_memories_count', 0)} 条")
        print(f"  - 社交记忆: {mem_stats.get('social_memories_count', 0)} 条")
        print()

        print(f"活跃目标: {len(goals)} 个")
        for goal in goals[:3]:  # 只显示前3个
            print(f"  - {goal.title} (优先级: {goal.priority})")

        print("=" * 70 + "\n")

    async def show_help(self):
        """显示帮助信息"""
        print("\n" + "=" * 70)
        print("💡 命令帮助")
        print("=" * 70)
        print("/help     - 显示此帮助信息")
        print("/status   - 显示智能体状态")
        print("/memory   - 显示最近的记忆")
        print("/goal     - 添加新目标")
        print("/emotion  - 显示情感状态")
        print("/quit     - 退出程序")
        print()
        print("直接输入消息即可与AI对话")
        print("=" * 70 + "\n")

    async def show_memories(self):
        """显示最近的记忆"""
        print("\n" + "=" * 70)
        print("💭 最近的记忆")
        print("=" * 70)

        memories = await self.agent.memory.retrieve({
            "memory_type": "event"
        }, limit=5)

        if not memories:
            print("暂无记忆")
        else:
            for i, mem in enumerate(memories, 1):
                print(f"\n{i}. {mem.get('event_summary', '无标题')}")
                print(f"   时间: {mem.get('timestamp', '未知')}")
                print(f"   详情: {mem.get('event_details', '无详情')[:50]}...")

        print("\n" + "=" * 70 + "\n")

    async def add_goal_interactive(self):
        """交互式添加目标"""
        print("\n添加新目标:")
        title = input("目标标题: ").strip()
        if not title:
            print("❌ 目标标题不能为空")
            return

        description = input("目标描述: ").strip()
        priority_input = input("优先级 (1=低, 2=中, 3=高) [2]: ").strip()

        try:
            priority = int(priority_input) if priority_input else 2
            if priority not in [1, 2, 3]:
                priority = 2
        except:
            priority = 2

        goal_id = await self.agent.add_goal({
            "title": title,
            "description": description,
            "priority": priority
        })

        print(f"✓ 目标已添加 (ID: {goal_id[:8]}...)\n")

    async def chat(self, message: str):
        """与智能体对话"""
        # 发送消息
        response = await self.agent.receive_message(
            sender_id="user",
            message=message,
            metadata={"timestamp": datetime.now().isoformat()}
        )

        # 存储对话记忆
        await self.agent.memory.store("event", {
            "event_summary": "用户对话",
            "event_details": f"用户: {message}\n回复: {response}",
            "participants": ["user", self.agent.agent_id],
            "importance": 0.6
        })

        return response

    async def run(self):
        """运行交互式循环"""
        await self.initialize()

        print("=" * 70)
        print("🎮 系统已就绪")
        print("=" * 70)
        print("💡 输入 /help 查看可用命令")
        print("💡 直接输入消息开始对话")
        print("💡 输入 /quit 退出程序")
        print("=" * 70)
        print()

        self.running = True

        while self.running:
            try:
                # 获取用户输入
                user_input = input("你: ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith("/"):
                    command = user_input.lower()

                    if command == "/quit":
                        print("\n👋 再见！")
                        self.running = False
                        break
                    elif command == "/help":
                        await self.show_help()
                    elif command == "/status":
                        await self.show_status()
                    elif command == "/memory":
                        await self.show_memories()
                    elif command == "/goal":
                        await self.add_goal_interactive()
                    elif command == "/emotion":
                        emotion = self.agent.emotion.get_current_emotion()
                        print(f"\n😊 当前情感: {emotion.get('primary_emotion', 'neutral')}")
                        print(f"   效价: {emotion.get('valence', 0.0):.2f}")
                        print(f"   唤醒: {emotion.get('arousal', 0.0):.2f}\n")
                    else:
                        print(f"❌ 未知命令: {command}")
                        print("💡 输入 /help 查看可用命令\n")

                    continue

                # 普通对话
                print("AI: ", end="", flush=True)
                response = await self.chat(user_input)
                print(f"{response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 收到中断信号，正在退出...")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")

        # 清理
        print("\n🧹 清理资源...")
        await self.agent.stop()
        print("✓ 完成\n")


async def main():
    """主函数"""
    # 检查是否要使用LLM
    use_llm = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-llm":
        use_llm = False

    agent_system = InteractiveAgent(use_llm=use_llm)
    await agent_system.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已退出")
