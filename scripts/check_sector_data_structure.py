#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from module_01_data_pipeline.data_acquisition.alternative_data_collector import ChineseAlternativeDataCollector

collector = ChineseAlternativeDataCollector(rate_limit=0.5)
sector_df = collector.fetch_sector_performance(indicator="新浪行业")

print("DataFrame info:")
print(sector_df.info())
print("\n列名:")
print(sector_df.columns.tolist())
print("\n前3行数据:")
print(sector_df.head(3))
print("\n数据类型:")
print(sector_df.dtypes)

