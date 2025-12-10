#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试市场数据API的功能
"""

import sys
from pathlib import Path

# 设置 Windows 控制台 UTF-8 编码支持
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests


BASE_URL = "http://127.0.0.1:8000/api"


def test_api(endpoint, description):
    """测试单个API"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"端点: {endpoint}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("成功!")
            
            # 打印数据结构
            if isinstance(data, dict):
                for key in data.keys():
                    value = data[key]
                    if isinstance(value, list):
                        print(f"  - {key}: {len(value)} 条数据")
                    elif isinstance(value, dict):
                        print(f"  - {key}: {len(value)} 个字段")
                    else:
                        print(f"  - {key}: {value}")
            return True
        else:
            print(f"失败: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("连接失败: 后端服务未运行")
        print("请先运行: python main.py")
        return False
    except requests.exceptions.Timeout:
        print("超时 (15秒)")
        return False
    except Exception as e:
        print(f"异常: {str(e)[:200]}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("市场数据API测试")
    print("="*60)
    
    tests = [
        ("/v1/market/indices", "市场指数数据"),
        ("/v1/market/hot-stocks", "热门股票数据"),
        ("/v1/market/sector-analysis", "板块分析数据"),
        ("/v1/market/market-sentiment", "市场情绪数据"),
        ("/v1/market/technical-indicators", "技术指标数据"),
        ("/v1/market/market-news?limit=10", "市场资讯数据 (前10条)"),
    ]
    
    results = []
    for endpoint, description in tests:
        result = test_api(endpoint, description)
        results.append((description, result))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for desc, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {desc}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n所有测试通过!")
        return 0
    else:
        print(f"\n{total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

