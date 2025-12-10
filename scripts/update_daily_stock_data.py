"""
每日股票数据更新脚本
只更新最新一天的数据，避免重复获取历史数据
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.logging_system import setup_logger
from module_01_data_pipeline.storage_management.cached_data_manager import get_cached_data_manager

logger = setup_logger("update_daily_stock_data")


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           FinLoom 每日数据更新工具                            ║
║                                                              ║
║  本工具将从AKshare获取最新一天的股票数据                      ║
║  建议每天收盘后运行一次，保持数据最新                        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"当前时间: {current_time}")
    print("="*60)
    
    # 获取缓存管理器
    cache_manager = get_cached_data_manager()
    
    # 显示当前数据库统计
    print("\n📊 当前数据库统计:")
    stats = cache_manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("开始更新最新数据...")
    print("="*60 + "\n")
    
    # 更新最新数据
    cache_manager.update_latest_data()
    
    # 更新板块数据
    print("\n更新板块数据...")
    cache_manager.get_sector_data(force_update=True)
    
    print("\n" + "="*60)
    print("✅ 每日数据更新完成！")
    print("="*60)
    
    # 显示更新后的统计
    print("\n📊 更新后数据库统计:")
    stats = cache_manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n")


if __name__ == "__main__":
    main()






