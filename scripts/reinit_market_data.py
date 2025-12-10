#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化市场数据（修复编码问题）
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from module_01_data_pipeline.data_acquisition.akshare_collector import AkshareDataCollector
from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector
from module_01_data_pipeline.storage_management.database_manager import get_database_manager
from common.logging_system import setup_logger

logger = setup_logger("reinit_market_data")


async def reinit_sector_data():
    """重新初始化板块数据"""
    print("\n" + "="*60)
    print("1. 重新获取板块数据...")
    print("="*60)
    
    collector = ChineseAlternativeDataCollector(rate_limit=0.5)
    db_manager = get_database_manager()
    
    try:
        # 获取板块数据
        print("正在从akshare获取板块数据...")
        sector_data = collector.fetch_sector_performance(indicator="新浪行业")
        
        if sector_data and not sector_data.empty:
            print(f"[OK] 获取到 {len(sector_data)} 个板块数据")
            
            # 显示前几个板块名称（验证编码）
            print("\n板块示例：")
            for idx, row in sector_data.head(5).iterrows():
                sector_name = row.get('板块名称', row.get('sector_name', ''))
                change = row.get('涨跌幅', row.get('change_pct', 0))
                print(f"  - {sector_name}: {change}%")
            
            # 保存到数据库
            print("\n正在保存到数据库...")
            success = db_manager.save_sector_data(sector_data)
            
            if success:
                print("[OK] 板块数据保存成功！")
                return True
            else:
                print("[FAIL] 板块数据保存失败")
                return False
        else:
            print("[FAIL] 未获取到板块数据")
            return False
            
    except Exception as e:
        print(f"[FAIL] 板块数据初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def reinit_news_data():
    """重新初始化新闻数据"""
    print("\n" + "="*60)
    print("2. 重新获取新闻数据...")
    print("="*60)
    
    collector = ChineseAlternativeDataCollector(rate_limit=0.5)
    db_manager = get_database_manager()
    
    try:
        # 获取新闻数据
        print("正在从数据源获取新闻...")
        news_data = collector.fetch_financial_news(limit=20)
        
        if news_data and not news_data.empty:
            print(f"✅ 获取到 {len(news_data)} 条新闻")
            
            # 显示前几条新闻标题（验证编码）
            print("\n新闻示例：")
            for idx, row in news_data.head(3).iterrows():
                title = row.get('title', row.get('标题', ''))
                print(f"  - {title}")
            
            # 保存到数据库
            print("\n正在保存到数据库...")
            success = db_manager.save_news_data(news_data)
            
            if success:
                print("✅ 新闻数据保存成功！")
                return True
            else:
                print("❌ 新闻数据保存失败")
                return False
        else:
            print("❌ 未获取到新闻数据")
            return False
            
    except Exception as e:
        print(f"❌ 新闻数据初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def reinit_index_data():
    """重新初始化上证指数数据"""
    print("\n" + "="*60)
    print("3. 重新获取上证指数数据...")
    print("="*60)
    
    collector = AkshareDataCollector(rate_limit=0.5)
    db_manager = get_database_manager()
    
    try:
        # 获取上证指数历史数据（最近100个交易日）
        print("正在从akshare获取上证指数数据...")
        index_data = await collector.fetch_stock_data(
            symbol="sh000001",
            period="100"  # 最近100个交易日
        )
        
        if index_data and not index_data.empty:
            print(f"✅ 获取到 {len(index_data)} 天的指数数据")
            
            # 保存到数据库
            print("正在保存到数据库...")
            success = db_manager.save_stock_prices("sh000001", index_data)
            
            if success:
                print("✅ 上证指数数据保存成功！")
                return True
            else:
                print("❌ 上证指数数据保存失败")
                return False
        else:
            print("❌ 未获取到上证指数数据")
            return False
            
    except Exception as e:
        print(f"❌ 上证指数数据初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("重新初始化市场数据（修复编码问题）")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 板块数据
    result = await reinit_sector_data()
    results.append(("板块数据", result))
    
    # 2. 新闻数据
    result = await reinit_news_data()
    results.append(("新闻数据", result))
    
    # 3. 上证指数数据
    result = await reinit_index_data()
    results.append(("上证指数数据", result))
    
    # 总结
    print("\n" + "="*60)
    print("初始化结果总结")
    print("="*60)
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {success_count}/{total_count} 成功")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if success_count == total_count:
        print("\n✅ 所有数据初始化成功！现在可以刷新前端页面查看数据。")
    else:
        print("\n⚠️ 部分数据初始化失败，请检查错误信息。")


if __name__ == "__main__":
    asyncio.run(main())
