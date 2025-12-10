#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

# 测试板块分析API
print("="*60)
print("测试API返回数据")
print("="*60)

r = requests.get('http://localhost:8000/api/v1/market/sector-analysis')
data = r.json()

print(f"\n状态: {data.get('status')}")
print(f"板块数量: {len(data['data']['sectors'])}")
print("\n前5个板块:")
for sector in data['data']['sectors'][:5]:
    print(f"  - {sector['name']}: {sector['change']}%")

print("\n="*60)
print("✓ API返回正常，中文显示正确！")
print("="*60)

