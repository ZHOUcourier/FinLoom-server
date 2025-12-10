#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库编码问题并重新获取数据
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector


def fix_database_and_reinit():
    """修复数据库编码并重新初始化数据"""
    print("="*60)
    print("修复数据库编码问题")
    print("="*60)
    
    # 数据库路径
    db_path = "data/finloom.db"
    
    # 1. 清空旧的板块数据
    print("\n1. 清空旧的板块数据...")
    try:
        conn = sqlite3.connect(db_path)
        conn.text_factory = str  # 使用UTF-8
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sector_data")
        conn.commit()
        conn.close()
        print("   [OK] 旧数据已清空")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # 2. 获取新的板块数据
    print("\n2. 获取新的板块数据...")
    try:
        collector = ChineseAlternativeDataCollector(rate_limit=0.5)
        sector_df = collector.fetch_sector_performance(indicator="新浪行业")
        
        if sector_df is not None and not sector_df.empty:
            print(f"   获取到 {len(sector_df)} 个板块")
            
            # 显示前3个板块名称
            print("\n   板块列表:")
            for idx in range(min(3, len(sector_df))):
                row = sector_df.iloc[idx]
                name = row.get('板块名称', '')
                change = row.get('涨跌幅', 0)
                print(f"   - {name}: {change}%")
            
            # 3. 使用UTF-8编码保存到数据库
            print("\n3. 保存数据到数据库...")
            conn = sqlite3.connect(db_path)
            conn.text_factory = str  # 确保使用UTF-8
            cursor = conn.cursor()
            
            from datetime import datetime
            now = datetime.now().isoformat()
            today = datetime.now().strftime("%Y-%m-%d")
            
            saved_count = 0
            for _, row in sector_df.iterrows():
                sector_name = str(row.get('板块', ''))
                change_pct = float(row.get('涨跌幅', 0))
                
                if not sector_name:
                    continue
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO sector_data 
                        (sector_name, date, change_pct, company_count, total_volume, total_amount, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sector_name,
                        today,
                        change_pct,
                        int(row.get('公司家数', 0)),
                        int(row.get('总成交量', 0)),
                        int(row.get('总成交额', 0)),
                        now
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"   [WARN] 保存板块 {sector_name} 失败: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"   [OK] 成功保存 {saved_count} 个板块数据")
            
            # 4. 验证保存的数据
            print("\n4. 验证保存的数据...")
            conn = sqlite3.connect(db_path)
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute("SELECT sector_name, change_pct FROM sector_data ORDER BY change_pct DESC LIMIT 3")
            rows = cursor.fetchall()
            conn.close()
            
            print("   数据库中的板块示例:")
            for sector_name, change_pct in rows:
                print(f"   - {sector_name}: {change_pct}%")
            
            print("\n" + "="*60)
            print("[SUCCESS] 数据库编码问题已修复！")
            print("="*60)
            print("\n下一步:")
            print("1. 刷新浏览器页面 (Ctrl + F5)")
            print("2. 查看智能分析页面是否正常显示中文")
            print("="*60)
            
        else:
            print("   [FAIL] 未获取到板块数据")
            
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_database_and_reinit()

