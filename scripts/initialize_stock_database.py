"""
股票数据库初始化脚本
从AKshare获取历史数据并保存到本地数据库
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from common.logging_system import setup_logger
from module_01_data_pipeline.data_acquisition.akshare_collector import AkshareDataCollector
from module_01_data_pipeline.storage_management.database_manager import DatabaseManager

logger = setup_logger("initialize_stock_database")


class StockDatabaseInitializer:
    """股票数据库初始化器"""
    
    def __init__(self, years_back: int = 20):
        """
        初始化
        
        Args:
            years_back: 获取多少年的历史数据
        """
        self.years_back = years_back
        self.collector = AkshareDataCollector(rate_limit=0.5)
        self.db_manager = DatabaseManager()
        
        # 计算日期范围
        self.end_date = datetime.now().strftime("%Y%m%d")
        self.start_date = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y%m%d")
        
        logger.info(f"初始化数据范围: {self.start_date} 至 {self.end_date}")
    
    def initialize_all_data(self):
        """初始化所有数据"""
        logger.info("=" * 60)
        logger.info("开始初始化股票数据库")
        logger.info("=" * 60)
        
        # 1. 获取并保存股票列表
        self.initialize_stock_list()
        
        # 2. 获取并保存主要股票的历史数据
        self.initialize_stock_history()
        
        # 3. 获取并保存宏观数据
        self.initialize_macro_data()
        
        # 4. 获取并保存板块数据
        self.initialize_sector_data()
        
        logger.info("=" * 60)
        logger.info("数据库初始化完成！")
        logger.info("=" * 60)
        
        # 显示统计信息
        self.show_statistics()
    
    def initialize_stock_list(self):
        """初始化股票列表"""
        logger.info("\n[1/4] 正在获取股票列表...")
        
        try:
            stock_list = self.collector.fetch_stock_list("A股")
            
            if stock_list.empty:
                logger.warning("获取股票列表为空")
                return
            
            logger.info(f"获取到 {len(stock_list)} 只股票")
            
            # 保存股票基本信息
            count = 0
            for _, row in stock_list.iterrows():
                try:
                    symbol = row.get('代码', row.get('symbol', ''))
                    name = row.get('名称', row.get('name', ''))
                    
                    if not symbol or not name:
                        continue
                    
                    self.db_manager.save_stock_info(
                        symbol=str(symbol),
                        name=str(name),
                        sector=row.get('行业', None),
                        industry=row.get('细分行业', None)
                    )
                    count += 1
                    
                    if count % 100 == 0:
                        logger.info(f"已保存 {count} 只股票基本信息")
                        
                except Exception as e:
                    logger.error(f"保存股票信息失败: {e}")
                    continue
            
            logger.info(f"✅ 股票列表初始化完成，共保存 {count} 只股票")
            
        except Exception as e:
            logger.error(f"初始化股票列表失败: {e}")
    
    def initialize_stock_history(self, max_stocks: int = 50):
        """
        初始化主要股票的历史数据
        
        Args:
            max_stocks: 最多获取多少只股票（避免时间过长）
        """
        logger.info(f"\n[2/4] 正在获取前 {max_stocks} 只股票的历史数据...")
        
        try:
            # 获取热门股票代码
            popular_stocks = [
                "000001",  # 平安银行
                "000002",  # 万科A
                "600000",  # 浦发银行
                "600036",  # 招商银行
                "600519",  # 贵州茅台
                "601398",  # 工商银行
                "601857",  # 中国石油
                "601988",  # 中国银行
                "000858",  # 五粮液
                "600276",  # 恒瑞医药
            ]
            
            # 也可以从数据库获取股票列表
            # all_symbols = self.db_manager.get_symbols_list()
            # if all_symbols:
            #     popular_stocks.extend(all_symbols[:max_stocks - len(popular_stocks)])
            
            count = 0
            for symbol in popular_stocks[:max_stocks]:
                try:
                    logger.info(f"正在获取 {symbol} 的历史数据...")
                    
                    # 获取历史数据
                    df = self.collector.fetch_stock_history(
                        symbol=symbol,
                        start_date=self.start_date,
                        end_date=self.end_date,
                        period="daily",
                        adjust="qfq"
                    )
                    
                    if not df.empty:
                        # 标准化列名
                        df = self._standardize_columns(df)
                        
                        # 保存到数据库
                        success = self.db_manager.save_stock_prices(symbol, df)
                        
                        if success:
                            count += 1
                            logger.info(f"✅ {symbol}: 保存了 {len(df)} 条记录")
                        else:
                            logger.warning(f"⚠️ {symbol}: 保存失败")
                    else:
                        logger.warning(f"⚠️ {symbol}: 没有数据")
                    
                except Exception as e:
                    logger.error(f"获取 {symbol} 数据失败: {e}")
                    continue
            
            logger.info(f"✅ 股票历史数据初始化完成，共保存 {count} 只股票")
            
        except Exception as e:
            logger.error(f"初始化股票历史数据失败: {e}")
    
    def initialize_macro_data(self):
        """初始化宏观经济数据"""
        logger.info("\n[3/4] 正在获取宏观经济数据...")
        
        try:
            from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector
            
            alt_collector = ChineseAlternativeDataCollector(rate_limit=0.5)
            
            # 获取GDP、CPI、PMI数据
            macro_data = alt_collector.fetch_macro_economic_data("all")
            
            if macro_data:
                count = 0
                for indicator, df in macro_data.items():
                    if not df.empty:
                        success = self.db_manager.save_macro_data(indicator, df)
                        if success:
                            count += 1
                            logger.info(f"✅ {indicator}: 保存了 {len(df)} 条记录")
                
                logger.info(f"✅ 宏观数据初始化完成，共保存 {count} 个指标")
            else:
                logger.warning("未获取到宏观数据")
                
        except Exception as e:
            logger.error(f"初始化宏观数据失败: {e}")
    
    def initialize_sector_data(self):
        """初始化板块数据"""
        logger.info("\n[4/4] 正在获取板块数据...")
        
        try:
            from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector
            
            alt_collector = ChineseAlternativeDataCollector(rate_limit=0.5)
            
            # 获取最新板块数据
            sector_df = alt_collector.fetch_sector_performance()
            
            if not sector_df.empty:
                today = datetime.now().strftime("%Y-%m-%d")
                success = self.db_manager.save_sector_data(sector_df, date=today)
                
                if success:
                    logger.info(f"✅ 板块数据初始化完成，保存了 {len(sector_df)} 个板块")
                else:
                    logger.warning("保存板块数据失败")
            else:
                logger.warning("未获取到板块数据")
                
        except Exception as e:
            logger.error(f"初始化板块数据失败: {e}")
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame列名"""
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_change',
            '涨跌额': 'change',
            '换手率': 'turnover_rate',
        }
        
        df = df.copy()
        df.rename(columns=column_mapping, inplace=True)
        
        return df
    
    def show_statistics(self):
        """显示数据库统计信息"""
        logger.info("\n数据库统计信息:")
        stats = self.db_manager.get_database_stats()
        
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")


def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           FinLoom 股票数据库初始化工具                        ║
║                                                              ║
║  本工具将从AKshare获取历史数据并保存到本地数据库              ║
║  这样可以避免每次都从网络获取数据，提高系统性能              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 询问用户
    years = input("请输入要获取多少年的历史数据 (默认: 20年): ").strip()
    if not years:
        years = 20
    else:
        try:
            years = int(years)
        except ValueError:
            print("输入无效，使用默认值 20年")
            years = 20
    
    print(f"\n开始初始化 {years} 年的历史数据...")
    print("提示：初始化可能需要较长时间，请耐心等待...\n")
    
    # 开始初始化
    initializer = StockDatabaseInitializer(years_back=years)
    initializer.initialize_all_data()
    
    print("\n" + "="*60)
    print("✅ 数据库初始化完成！")
    print("="*60)
    print("\n现在系统将优先使用本地数据，大幅提升性能！")
    print("每天只需要更新最新的数据即可。\n")


if __name__ == "__main__":
    main()






