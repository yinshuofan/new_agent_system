"""
LLM智能体示例
演示如何使用LLM增强的智能体
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system import Agent
from agent_system.llm import initialize_llm, LLMConfig, ModelType
from agent_system.llm.prompt_manager import initialize_prompts
from agent_system.models.goal_models import GoalPriority


async def main():
    """主函数"""
    print("=== LLM增强智能体示例 ===\n")

    # 1. 初始化LLM（需要配置API Key）
    print("1. 初始化LLM...")
    print("   注意：需要设置环境变量 OPENAI_API_KEY")

    api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

    if api_key == "your-api-key-here":
        print("   警告：未设置OPENAI_API_KEY，将使用无LLM模式演示\n")
        use_llm_mode = False
    else:
        try:
            llm_config = LLMConfig(
                api_key=api_key,
                max_connections=5
            )
            llm_client = await initialize_llm(llm_config)
            print("   LLM客户端已初始化\n")
            use_llm_mode = True
        except Exception as e:
            print(f"   LLM初始化失败: {e}")
            print("   将使用无LLM模式\n")
            use_llm_mode = False

    # 2. 初始化提示词管理器
    print("2. 加载提示词配置...")
    prompts_path = "/home/user/new_agent_system/config/prompts.yaml"
    if os.path.exists(prompts_path):
        initialize_prompts(prompts_path)
        print("   提示词配置已加载\n")
    else:
        print("   使用默认提示词\n")

    # 3. 创建使用LLM的智能体
    print("3. 创建智能体（启用LLM）...")
    agent = Agent(
        agent_id="agent_alice",
        name="Alice",
        config={"max_memories": 500},
        use_llm=use_llm_mode
    )
    await agent.start()
    print(f"   智能体 '{agent.name}' 已启动\n")

    # 4. 添加目标
    print("4. 添加目标...")
    goal_id = await agent.add_goal({
        "title": "学习人工智能",
        "description": "深入了解人工智能的原理和应用",
        "priority": GoalPriority.HIGH.value
    })
    await agent.goal.activate_goal(goal_id)
    print(f"   目标已添加并激活: {goal_id}\n")

    # 5. 添加记忆
    print("5. 添加事件记忆...")
    memory_id = await agent.memory.store("event", {
        "event_summary": "参加AI研讨会",
        "event_details": "今天参加了一个关于大语言模型的研讨会，学到了很多新知识",
        "participants": ["Alice", "Professor Smith"],
        "emotion_valence": 0.8,
        "emotion_arousal": 0.7,
        "importance": 0.9,
        "tags": ["AI", "学习", "研讨会"],
        "related_goals": [goal_id]
    })
    print(f"   记忆已存储: {memory_id}\n")

    # 6. 使用认知模块进行决策（使用LLM）
    print("6. 使用认知模块进行决策...")

    decision_context = {
        "situation": "有人询问关于人工智能的问题",
        "options": [
            {"type": "answer_question", "topic": "AI"},
            {"type": "suggest_resources", "topic": "AI"},
            {"type": "share_experience", "topic": "workshop"}
        ]
    }

    decision = await agent.cognition.make_decision(decision_context)
    print(f"   决策结果:")
    print(f"     - 行为: {decision['action']}")
    print(f"     - 推理: {decision['reasoning']}")
    print(f"     - 置信度: {decision['confidence']}\n")

    # 7. 模拟接收消息并响应
    print("7. 接收并响应消息...")
    response = await agent.receive_message(
        sender_id="user_bob",
        message="Alice，你对大语言模型有什么看法？",
        metadata={"type": "question"}
    )
    print(f"   响应: {response}\n")

    # 8. 执行反思
    print("8. 执行自我反思...")
    reflection = await agent.cognition.reflect()
    print(f"   反思结果:")
    print(f"     - 洞察: {reflection.get('insights', [])}")
    print(f"     - 调整: {reflection.get('adjustments', [])}\n")

    # 9. 查看情感状态
    print("9. 查看情感状态...")
    emotion = agent.emotion.get_current_emotion()
    print(f"   当前情感: {emotion.get('primary_emotion')}")
    print(f"   情感效价: {emotion.get('valence'):.2f}")
    print(f"   唤醒度: {emotion.get('arousal'):.2f}\n")

    # 10. 显示LLM统计（如果使用了LLM）
    if use_llm_mode:
        print("10. LLM调用统计...")
        from agent_system.llm import get_llm_client
        llm_client = get_llm_client()
        if llm_client:
            stats = llm_client.get_stats()
            print(f"    - 总调用次数: {stats['call_count']}")
            print(f"    - 总Token数: {stats['total_tokens']}\n")

    # 11. 停止智能体
    print("11. 停止智能体...")
    await agent.stop()
    print("    智能体已停止\n")

    print("=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
