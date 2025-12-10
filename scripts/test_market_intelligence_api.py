#!/usr/bin/env python3
"""
测试市场情报API
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_apis():
    """测试所有API"""
    print("=" * 60)
    print("测试市场情报API")
    print("=" * 60)

    from module_01_data_pipeline.data_pipeline_coordinator import (
        get_data_pipeline_coordinator,
    )

    coordinator = get_data_pipeline_coordinator()

    # 1. 测试板块分析
    print("\n1. 测试板块分析API...")
    result = await coordinator.fetch_sector_analysis_data()
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   数据量: {len(result.get('data', []))} 个板块")
        if result.get('data'):
            print(f"   示例: {result['data'][0]}")
    else:
        print(f"   错误: {result.get('message')}")

    # 2. 测试市场情绪
    print("\n2. 测试市场情绪API...")
    result = await coordinator.fetch_market_sentiment_data()
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        data = result.get('data', {})
        print(f"   恐慌贪婪指数: {data.get('fear_greed_index')}")
        print(f"   上涨股票: {data.get('advancing_stocks')}")
        print(f"   下跌股票: {data.get('declining_stocks')}")
    else:
        print(f"   错误: {result.get('message')}")

    # 3. 测试技术指标
    print("\n3. 测试技术指标API...")
    result = await coordinator.fetch_technical_indicators_data()
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   数据量: {len(result.get('data', []))} 个指标")
        if result.get('data'):
            for indicator in result['data']:
                print(f"   - {indicator['name']}: {indicator['value']} ({indicator['signal']})")
    else:
        print(f"   错误: {result.get('message')}")

    # 4. 测试市场资讯
    print("\n4. 测试市场资讯API...")
    result = await coordinator.fetch_market_news_data(limit=5)
    print(f"   成功: {result.get('success')}")
    if result.get('success'):
        print(f"   数据量: {len(result.get('data', []))} 条资讯")
        if result.get('data'):
            print(f"   示例: {result['data'][0]['title']}")
    else:
        print(f"   错误: {result.get('message')}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_apis())

