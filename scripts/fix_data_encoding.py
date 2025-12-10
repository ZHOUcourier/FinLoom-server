#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库编码问题 - 重新获取数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector
from module_01_data_pipeline.data_acquisition.akshare_collector import AkshareDataCollector
from module_01_data_pipeline.storage_management.database_manager import get_database_manager


def main():
    print("="*60)
    print("正在修复数据编码问题...")
    print("="*60)
    
    db_manager = get_database_manager()
    
    # 1. 板块数据
    print("\n1. 获取板块数据...")
    try:
        collector = ChineseAlternativeDataCollector(rate_limit=0.5)
        sector_data = collector.fetch_sector_performance(indicator="新浪行业")
        
        if sector_data is not None and not sector_data.empty:
            print(f"   获取到 {len(sector_data)} 个板块")
            
            # 显示前3个
            for idx, row in sector_data.head(3).iterrows():
                name = row.get('板块名称', '')
                change = row.get('涨跌幅', 0)
                print(f"   - {name}: {change}%")
            
            # 保存
            if db_manager.save_sector_data(sector_data):
                print("   [OK] 板块数据保存成功")
            else:
                print("   [FAIL] 板块数据保存失败")
        else:
            print("   [FAIL] 未获取到数据")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 2. 新闻数据
    print("\n2. 获取新闻数据...")
    try:
        collector = ChineseAlternativeDataCollector(rate_limit=0.5)
        news_data = collector.fetch_financial_news(limit=20)
        
        if news_data is not None and not news_data.empty:
            print(f"   获取到 {len(news_data)} 条新闻")
            
            # 显示第一条标题
            if len(news_data) > 0:
                title = news_data.iloc[0].get('title', '')
                print(f"   示例: {title[:50]}...")
            
            # 保存
            if db_manager.save_news_data(news_data):
                print("   [OK] 新闻数据保存成功")
            else:
                print("   [FAIL] 新闻数据保存失败")
        else:
            print("   [FAIL] 未获取到数据")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 3. 上证指数数据
    print("\n3. 获取上证指数数据...")
    try:
        collector = AkshareDataCollector(rate_limit=0.5)
        index_data = collector.fetch_stock_history(
            symbol="sh000001",
            start_date="20240101",
            end_date="20251013"
        )
        
        if index_data is not None and not index_data.empty:
            print(f"   获取到 {len(index_data)} 天数据")
            
            # 保存
            if db_manager.save_stock_prices("sh000001", index_data):
                print("   [OK] 上证指数数据保存成功")
            else:
                print("   [FAIL] 上证指数数据保存失败")
        else:
            print("   [FAIL] 未获取到数据")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    print("\n" + "="*60)
    print("数据修复完成！")
    print("="*60)
    print("\n提示：")
    print("1. 刷新浏览器页面")
    print("2. 查看智能分析页面是否显示数据")
    print("="*60)


if __name__ == "__main__":
    main()

