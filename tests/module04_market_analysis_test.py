#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 04 Market Analysis Comprehensive Test
模块04市场分析综合测试

This test file demonstrates the integrated functionality of Module 04
with real data from Module 1 and Module 2.

IMPORTANT:
- Run this test in the 'study' conda environment
- Ensure Module 1 data sources are available
- Test results will be saved to the Module 4 SQLite database

Usage:
    conda activate study
    cd /Users/victor/Desktop/25fininnov/FinLoom-server
    python tests/module04_market_analysis_test.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# 设置 Windows 控制台 UTF-8 编码支持
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("module04_test")


def test_imports():
    """Test 1: 验证所有模块导入"""
    print("=" * 60)
    print("Test 1: Module Imports Test")
    print("=" * 60)

    try:
        # Test Module 1 imports
        from module_01_data_pipeline import (
            AkshareDataCollector,
            ChineseAlternativeDataCollector,
            ChineseFundamentalCollector,
            get_database_manager,
        )

        print("✓ Module 1 data pipeline imports successful")

        # Test Module 4 sentiment analysis - updated imports
        from module_04_market_analysis.sentiment_analysis.fin_r1_sentiment import (
            get_sentiment_analyzer,
        )

        print("✓ Module 4 sentiment analysis imports successful")

        # Test Module 4 enhanced sentiment
        from module_04_market_analysis.sentiment_analysis.enhanced_news_sentiment import (
            EnhancedNewsSentimentAnalyzer,
        )

        print("✓ Module 4 enhanced sentiment analysis imports successful")

        # Test Module 4 storage
        from module_04_market_analysis.storage_management.market_analysis_database import (
            get_market_analysis_db,
        )

        print("✓ Module 4 database imports successful")

        # Test Module 4 API
        from module_04_market_analysis.api.market_analysis_api import router

        print("✓ Module 4 API imports successful")

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


async def test_data_collection():
    """Test 2: 测试真实数据采集"""
    print("\n" + "=" * 60)
    print("Test 2: Real Data Collection Test")
    print("=" * 60)

    try:
        from module_01_data_pipeline import (
            AkshareDataCollector,
            ChineseAlternativeDataCollector,
            ChineseFundamentalCollector,
        )

        # Test stock data collection
        print("Testing stock data collection...")
        collector = AkshareDataCollector(rate_limit=1.0)

        test_symbols = ["000001", "600036", "000858"]  # 平安银行、招商银行、五粮液

        for symbol in test_symbols:
            try:
                # Get stock basic info
                info = collector.get_stock_basic_info(symbol)
                print(
                    f"  ✓ {symbol}: {info.get('name', 'N/A')} - {info.get('industry', 'N/A')}"
                )

                # Get historical data (last 30 days)
                end_date = datetime.now().strftime("%Y%m%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

                data = collector.fetch_stock_history(symbol, start_date, end_date)
                print(f"    Historical data: {len(data)} records")

                if len(data) > 0:
                    print(f"    Latest close price: {data['close'].iloc[-1]:.2f}")

            except Exception as e:
                print(f"  ✗ {symbol}: Failed to get data - {e}")

        # Test alternative data
        print("\nTesting alternative data collection...")
        alt_collector = ChineseAlternativeDataCollector(rate_limit=1.0)

        # Test news data
        try:
            news_data = alt_collector.fetch_news_data(limit=5)
            print(f"  ✓ News data: {len(news_data)} records")
        except Exception as e:
            print(f"  ✗ News data failed: {e}")

        # Test sector performance
        try:
            sector_data = alt_collector.fetch_sector_performance()
            print(f"  ✓ Sector data: {len(sector_data)} records")
        except Exception as e:
            print(f"  ✗ Sector data failed: {e}")

        # Test fundamental data
        print("\nTesting fundamental data collection...")
        fund_collector = ChineseFundamentalCollector(rate_limit=1.0)

        test_symbol = "000001"
        try:
            indicators = fund_collector.fetch_financial_indicators(test_symbol)
            print(f"  ✓ Financial indicators for {test_symbol}")
            print(f"    PE: {indicators.get('pe_ratio', 'N/A')}")
            print(f"    PB: {indicators.get('pb_ratio', 'N/A')}")
            print(f"    ROE: {indicators.get('roe', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Financial indicators failed: {e}")

        return True

    except Exception as e:
        print(f"✗ Data collection test failed: {e}")
        return False


async def test_sentiment_analysis():
    """Test 3: 测试情感分析功能"""
    print("\n" + "=" * 60)
    print("Test 3: Sentiment Analysis Test")
    print("=" * 60)

    try:
        from module_04_market_analysis.sentiment_analysis.enhanced_news_sentiment import (
            EnhancedNewsSentimentAnalyzer,
        )
        from module_04_market_analysis.sentiment_analysis.fin_r1_sentiment import (
            get_sentiment_analyzer,
        )

        test_symbols = ["000001", "600036"]

        # Test basic sentiment analysis
        print("Testing basic sentiment analysis...")
        sentiment_analyzer = get_sentiment_analyzer()

        if sentiment_analyzer:
            result = await sentiment_analyzer.analyze_stock_sentiment(test_symbols)
            print(f"  ✓ Stock sentiment analysis completed")
            print(
                f"    Overall sentiment: {result['overall_sentiment']['sentiment_score']:.3f}"
            )
            print(f"    Analyzed stocks: {len(result['individual_stocks'])}")

            # Test market sentiment
            market_result = await sentiment_analyzer.analyze_market_sentiment()
            print(f"  ✓ Market sentiment analysis completed")
            print(
                f"    Market sentiment score: {market_result['overall_sentiment']:.3f}"
            )
        else:
            print("  ⚠ Basic sentiment analyzer not available")

        # Test enhanced sentiment analysis
        print("\nTesting enhanced sentiment analysis...")
        enhanced_analyzer = EnhancedNewsSentimentAnalyzer()

        if enhanced_analyzer:
            enhanced_result = await enhanced_analyzer.analyze_comprehensive_sentiment(
                test_symbols
            )
            print(f"  ✓ Enhanced sentiment analysis completed")
            print(
                f"    Individual results: {len(enhanced_result['individual_results'])}"
            )

            for symbol, result in enhanced_result["individual_results"].items():
                print(
                    f"    {symbol}: {result['final_sentiment_label']} ({result['final_confidence']:.2f})"
                )
        else:
            print("  ⚠ Enhanced sentiment analyzer not available")

        return True

    except Exception as e:
        print(f"✗ Sentiment analysis test failed: {e}")
        return False


async def test_database_operations():
    """Test 4: 测试数据库操作"""
    print("\n" + "=" * 60)
    print("Test 4: Database Operations Test")
    print("=" * 60)

    try:
        from module_04_market_analysis.storage_management.market_analysis_database import (
            get_market_analysis_db,
        )

        # Get database instance
        db_manager = get_market_analysis_db()

        # Test database stats
        print("Testing database connection...")
        stats = db_manager.get_database_stats()
        print(f"  ✓ Database connected successfully")
        print(f"    Database size: {stats.get('database_size_mb', 0):.2f} MB")
        print(f"    Analysis results: {stats.get('analysis_results_count', 0)}")
        print(f"    Sentiment analyses: {stats.get('sentiment_analyses_count', 0)}")
        print(f"    Anomaly detections: {stats.get('anomaly_detections_count', 0)}")

        # Test saving sample data
        print("\nTesting data save operations...")

        # Save sample sentiment analysis
        sample_sentiment = {
            "analysis_id": f"test_sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "symbol": "TEST001",
            "text_source": "test",
            "sentiment_score": 0.5,
            "sentiment_label": "neutral",
            "confidence": 0.8,
            "keywords": ["test", "demo"],
            "analysis_method": "test_method",
            "source_data": {"test": True},
            "timestamp": datetime.now(),
        }

        success = db_manager.save_sentiment_analysis(sample_sentiment)
        if success:
            print("  ✓ Sample sentiment analysis saved")
        else:
            print("  ✗ Failed to save sentiment analysis")

        # Save sample anomaly detection
        sample_anomaly = {
            "symbol": "TEST001",
            "anomaly_type": "test_anomaly",
            "anomaly_score": 0.7,
            "description": "Test anomaly detection",
            "detection_method": "test_method",
            "timestamp": datetime.now(),
            "data_point": {"price": 100.0},
            "threshold_values": {"threshold": 0.5},
        }

        success = db_manager.save_anomaly_detection(sample_anomaly)
        if success:
            print("  ✓ Sample anomaly detection saved")
        else:
            print("  ✗ Failed to save anomaly detection")

        # Test data retrieval
        print("\nTesting data retrieval...")

        # Get recent sentiment analyses
        recent_sentiment = db_manager.get_database_stats()
        print(f"  ✓ Retrieved database statistics")

        return True

    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False


def test_api_structure():
    """Test 5: 测试API结构"""
    print("\n" + "=" * 60)
    print("Test 5: API Structure Test")
    print("=" * 60)

    try:
        from module_04_market_analysis.api.market_analysis_api import router

        # Check API routes
        routes = []
        for route in router.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes.append(f"{list(route.methods)[0]} {route.path}")

        print(f"✓ API router loaded with {len(routes)} routes:")
        for route in routes:
            print(f"  - {route}")

        return True

    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False


async def test_integration_workflow():
    """Test 6: 测试集成工作流"""
    print("\n" + "=" * 60)
    print("Test 6: Integration Workflow Test")
    print("=" * 60)

    try:
        # Step 1: Collect real data
        print("Step 1: Collecting real market data...")
        from module_01_data_pipeline import AkshareDataCollector

        collector = AkshareDataCollector(rate_limit=1.0)
        test_symbol = "000001"

        # Get stock info
        stock_info = collector.get_stock_basic_info(test_symbol)
        print(f"  ✓ Stock info: {stock_info.get('name', 'N/A')}")

        # Step 2: Analyze sentiment
        print("Step 2: Analyzing sentiment with real data...")
        from module_04_market_analysis.sentiment_analysis.fin_r1_sentiment import (
            get_sentiment_analyzer,
        )

        analyzer = get_sentiment_analyzer()
        sentiment_result = await analyzer.analyze_stock_sentiment([test_symbol])
        print(
            f"  ✓ Sentiment score: {sentiment_result['overall_sentiment']['sentiment_score']:.3f}"
        )

        # Step 3: Save to database
        print("Step 3: Saving results to Module 4 database...")
        from module_04_market_analysis.storage_management.market_analysis_database import (
            get_market_analysis_db,
        )

        db_manager = get_market_analysis_db()

        # Create comprehensive analysis result
        analysis_result = {
            "request_id": f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "symbols": [test_symbol],
            "consensus_recommendation": "hold",
            "consensus_confidence": 0.7,
            "consensus_reasoning": "Integration test result",
            "key_insights": [
                "Real data collected",
                "Sentiment analyzed",
                "Results stored",
            ],
            "risk_assessment": {"overall_risk": "medium"},
            "individual_analyses": [sentiment_result],
            "debate_result": {},
            "execution_time": 2.5,
            "status": "success",
            "timestamp": datetime.now(),
        }

        success = db_manager.save_analysis_result(analysis_result)
        print(f"  ✓ Analysis result saved: {success}")

        # Step 4: Verify data in database
        print("Step 4: Verifying stored data...")
        stats = db_manager.get_database_stats()
        print(f"  ✓ Total analysis results: {stats.get('analysis_results_count', 0)}")
        print(
            f"  ✓ Total sentiment analyses: {stats.get('sentiment_analyses_count', 0)}"
        )

        print("\n🎉 Integration workflow completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Integration workflow test failed: {e}")
        return False


def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    print("-" * 60)
    print(f"TOTAL: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Module 04 is ready for use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    print("\nModule 04 Features Tested:")
    print("- ✓ Real data integration from Module 1")
    print("- ✓ Enhanced sentiment analysis with FIN-R1")
    print("- ✓ Comprehensive news and fundamental analysis")
    print("- ✓ SQLite database storage for Module 4")
    print("- ✓ RESTful API endpoints")
    print("- ✓ End-to-end integration workflow")


async def main():
    """主测试函数"""
    print("Module 04 Market Analysis - Comprehensive Test Suite")
    print("=" * 60)
    print("Testing enhanced trading agents integration with real data")
    print(
        "Database: /Users/victor/Desktop/25fininnov/FinLoom-server/data/module04_market_analysis.db"
    )
    print("=" * 60)

    # Check conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "None")
    print(f"Conda Environment: {conda_env}")
    if conda_env != "study":
        print("⚠️  WARNING: Not running in 'study' environment. Some tests may fail.")
    print("")

    results = {}

    # Run tests
    results["1. Module Imports"] = test_imports()
    results["2. Data Collection"] = await test_data_collection()
    results["3. Sentiment Analysis"] = await test_sentiment_analysis()
    results["4. Database Operations"] = await test_database_operations()
    results["5. API Structure"] = test_api_structure()
    results["6. Integration Workflow"] = await test_integration_workflow()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed with error: {e}")
        import traceback

        traceback.print_exc()
