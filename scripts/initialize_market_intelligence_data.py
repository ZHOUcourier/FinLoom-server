#!/usr/bin/env python3
"""
初始化智能分析页面所需的市场数据
包括：板块分析、市场情绪、技术指标、市场资讯
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logging_system import setup_logger
from module_01_data_pipeline.data_pipeline_coordinator import (
    get_data_pipeline_coordinator,
)

logger = setup_logger("initialize_market_intelligence")


async def initialize_data():
    """初始化所有市场情报数据"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 开始初始化智能分析页面数据")
        logger.info("=" * 60)

        # 获取协调器
        coordinator = get_data_pipeline_coordinator()

        logger.info("\n📊 1/4 - 获取板块分析数据...")
        sector_result = await coordinator.fetch_sector_analysis_data()
        if sector_result.get("success"):
            logger.info(f"✅ 板块分析数据初始化成功: {sector_result.get('count', 0)} 个板块")
        else:
            logger.error(
                f"❌ 板块分析数据初始化失败: {sector_result.get('message', 'Unknown error')}"
            )

        logger.info("\n💭 2/4 - 获取市场情绪数据...")
        sentiment_result = await coordinator.fetch_market_sentiment_data()
        if sentiment_result.get("success"):
            data = sentiment_result.get("data", {})
            logger.info(
                f"✅ 市场情绪数据初始化成功: 恐慌贪婪指数={data.get('fear_greed_index', 0)}"
            )
        else:
            logger.error(
                f"❌ 市场情绪数据初始化失败: {sentiment_result.get('message', 'Unknown error')}"
            )

        logger.info("\n📈 3/4 - 获取技术指标数据...")
        indicators_result = await coordinator.fetch_technical_indicators_data()
        if indicators_result.get("success"):
            logger.info(
                f"✅ 技术指标数据初始化成功: {indicators_result.get('count', 0)} 个指标"
            )
        else:
            logger.error(
                f"❌ 技术指标数据初始化失败: {indicators_result.get('message', 'Unknown error')}"
            )

        logger.info("\n📰 4/4 - 获取市场资讯数据...")
        news_result = await coordinator.fetch_market_news_data(limit=20)
        if news_result.get("success"):
            logger.info(
                f"✅ 市场资讯数据初始化成功: {news_result.get('count', 0)} 条资讯"
            )
        else:
            logger.error(
                f"❌ 市场资讯数据初始化失败: {news_result.get('message', 'Unknown error')}"
            )

        logger.info("\n" + "=" * 60)
        logger.info("🎉 智能分析页面数据初始化完成")
        logger.info("=" * 60)

        # 统计结果
        success_count = sum(
            [
                sector_result.get("success", False),
                sentiment_result.get("success", False),
                indicators_result.get("success", False),
                news_result.get("success", False),
            ]
        )

        logger.info(f"\n📊 初始化结果: {success_count}/4 成功")

        if success_count == 4:
            logger.info("✅ 所有数据初始化成功！")
            return True
        elif success_count > 0:
            logger.warning(f"⚠️  部分数据初始化成功 ({success_count}/4)")
            return True
        else:
            logger.error("❌ 所有数据初始化失败")
            return False

    except Exception as e:
        logger.error(f"❌ 初始化过程发生错误: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数"""
    try:
        # 运行异步初始化
        success = asyncio.run(initialize_data())

        if success:
            print("\n✅ 数据初始化成功！现在可以访问智能分析页面查看数据。")
            sys.exit(0)
        else:
            print("\n❌ 数据初始化失败，请检查日志文件获取详细信息。")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断初始化")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

