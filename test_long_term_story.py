"""
测试长期剧情系统
"""

import asyncio
import sys
sys.path.insert(0, '/home/user/new_agent_system')

from agent_system.story import LongTermStoryEngine
from datetime import datetime


async def test_long_term_story():
    """测试长期剧情系统"""
    print("=" * 80)
    print("测试长期剧情系统")
    print("=" * 80)

    try:
        # 1. 加载配置
        print("\n1. 加载配置...")
        engine = LongTermStoryEngine.load_from_yaml(
            "config/long_term_story_example.yaml"
        )
        print(f"   ✓ 总天数: {engine.total_days}")
        print(f"   ✓ 日常模板数: {len(engine.daily_templates)}")
        print(f"   ✓ 剧情阶段数: {len(engine.story_phases)}")
        print(f"   ✓ 事件规则数: {len(engine.event_rules)}")

        # 2. 测试不同天数的日程生成
        test_days = [1, 50, 100, 200, 500, 1000]
        print("\n2. 测试日程生成:")
        for day in test_days:
            schedule = engine.get_day_schedule(day, "holmes")
            current_phase = engine._get_current_phase(day)
            phase_name = current_phase.title if current_phase else "无阶段"
            print(f"   第{day:4d}天: {len(schedule):2d}个活动 | 阶段: {phase_name}")

        # 3. 显示第1天的详细日程
        print("\n3. 第1天详细日程:")
        schedule = engine.get_day_schedule(1, "holmes")
        for i, item in enumerate(schedule[:10], 1):
            print(f"   {i}. {item.start_time} - {item.activity} @ {item.location}")

        # 4. 显示阶段摘要
        print("\n4. 剧情阶段摘要:")
        summary = engine.get_phase_summary()
        for phase in summary['phases']:
            print(f"   - {phase['title']}: 第{phase['day_range'][0]}-{phase['day_range'][1]}天")
            print(f"     主题: {phase['theme']}")

        # 5. 测试缓存性能
        print("\n5. 测试缓存性能:")
        import time

        # 首次生成（无缓存）
        start = time.time()
        _ = engine.get_day_schedule(500, "holmes")
        first_time = time.time() - start
        print(f"   首次生成第500天: {first_time*1000:.2f}ms")

        # 二次获取（有缓存）
        start = time.time()
        _ = engine.get_day_schedule(500, "holmes")
        cached_time = time.time() - start
        print(f"   缓存获取第500天: {cached_time*1000:.2f}ms")
        print(f"   性能提升: {(first_time/cached_time):.1f}倍")

        print("\n✅ 所有测试通过!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_long_term_story())
    sys.exit(0 if success else 1)
