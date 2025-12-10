#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 05 风险管理模块测试
测试投资组合风险评估、仓位管理、止损策略等功能

运行前请确保激活conda环境:
conda activate study
"""

import os
import sys

# 设置 Windows 控制台 UTF-8 编码支持
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# 导入Module 01和02用于获取真实数据
from module_01_data_pipeline import AkshareDataCollector, get_database_manager
from module_02_feature_engineering import TechnicalIndicators

# 导入Module 05组件
from module_05_risk_management import (
    ExposureConfig,
    # 仓位管理
    KellyCriterion,
    KellyResult,
    # 风险分析
    PortfolioRiskAnalyzer,
    RiskConfig,
    # 数据库
    RiskDatabaseManager,
    RiskExposureAnalyzer,
    # 止损管理
    StopLossConfig,
    StopLossManager,
    VaRCalculator,
    VaRConfig,
    get_risk_database_manager,
)


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_data_preparation():
    """测试1: 准备测试数据（从Module 01和02获取真实数据）"""
    print_section("测试1: 准备测试数据")

    try:
        # 使用Module 01获取真实股票数据
        collector = AkshareDataCollector(rate_limit=0.3)
        db_manager = get_database_manager()

        symbols = ["000001", "600036", "000858"]  # 平安银行、招商银行、五粮液
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")

        print(f"\n获取股票数据: {symbols}")
        print(f"时间范围: {start_date} 至 {end_date}")

        stock_data = {}
        returns_data = {}

        for symbol in symbols:
            try:
                # 获取历史数据
                data = collector.fetch_stock_history(symbol, start_date, end_date)

                if not data.empty and len(data) > 20:
                    stock_data[symbol] = data

                    # 计算收益率
                    returns = data["close"].pct_change().dropna()
                    returns_data[symbol] = returns

                    print(f"✓ {symbol}: {len(data)} 条记录, 收益率: {len(returns)} 条")
                else:
                    print(f"✗ {symbol}: 数据不足")

            except Exception as e:
                print(f"✗ {symbol}: 获取失败 - {e}")

        if len(stock_data) < 2:
            print("\n❌ 可用数据不足，需要至少2只股票")
            return None, None

        # 创建收益率DataFrame
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()

        print(f"\n✅ 数据准备完成:")
        print(f"  股票数量: {len(stock_data)}")
        print(f"  收益率数据点: {len(returns_df)}")
        print(f"  收益率统计:")
        print(returns_df.describe())

        return stock_data, returns_df

    except Exception as e:
        print(f"\n❌ 数据准备失败: {e}")
        import traceback

        traceback.print_exc()
        return None, None


def test_portfolio_risk_analyzer(stock_data, returns_df):
    """测试2: 投资组合风险分析"""
    print_section("测试2: 投资组合风险分析")

    try:
        # 创建投资组合
        symbols = list(stock_data.keys())
        portfolio = {}

        # 等权重分配
        weight = 1.0 / len(symbols)
        for i, symbol in enumerate(symbols):
            last_price = stock_data[symbol]["close"].iloc[-1]
            portfolio[symbol] = {
                "weight": weight,
                "shares": 1000,
                "cost": last_price * 0.95,  # 假设成本价比当前价低5%
            }

        print("\n投资组合配置:")
        for symbol, pos in portfolio.items():
            print(
                f"  {symbol}: 权重={pos['weight']:.2%}, 股数={pos['shares']}, 成本={pos['cost']:.2f}"
            )

        # 创建风险分析器
        config = RiskConfig(
            confidence_level=0.95,
            time_horizon=1,
            calculation_method="historical",
            rolling_window=252,
        )

        analyzer = PortfolioRiskAnalyzer(config)

        # 分析风险
        print("\n正在分析投资组合风险...")
        risk_metrics = analyzer.analyze_portfolio_risk(portfolio, returns_df)

        print("\n风险分析结果:")
        print(
            f"  VaR (95%): {risk_metrics['var_95']:.4f} ({risk_metrics['var_95'] * 100:.2f}%)"
        )
        print(
            f"  VaR (99%): {risk_metrics['var_99']:.4f} ({risk_metrics['var_99'] * 100:.2f}%)"
        )
        print(
            f"  CVaR (95%): {risk_metrics['cvar_95']:.4f} ({risk_metrics['cvar_95'] * 100:.2f}%)"
        )
        print(
            f"  CVaR (99%): {risk_metrics['cvar_99']:.4f} ({risk_metrics['cvar_99'] * 100:.2f}%)"
        )
        print(
            f"  最大回撤: {risk_metrics['max_drawdown']:.4f} ({risk_metrics['max_drawdown'] * 100:.2f}%)"
        )
        print(f"  夏普比率: {risk_metrics['sharpe_ratio']:.3f}")
        print(f"  索提诺比率: {risk_metrics['sortino_ratio']:.3f}")
        print(
            f"  年化波动率: {risk_metrics['volatility']:.4f} ({risk_metrics['volatility'] * 100:.2f}%)"
        )
        print(f"  相关性风险: {risk_metrics['correlation_risk']:.4f}")
        print(f"  集中度风险: {risk_metrics['concentration_risk']:.4f}")

        # 测试各个方法
        print("\n测试不同VaR计算方法:")
        portfolio_returns = (
            returns_df * [portfolio[s]["weight"] for s in returns_df.columns]
        ).sum(axis=1)

        var_hist = analyzer.calculate_var(portfolio_returns, 0.95)
        print(f"  历史模拟法 VaR: {var_hist:.4f}")

        analyzer.config.calculation_method = "parametric"
        var_param = analyzer.calculate_var(portfolio_returns, 0.95)
        print(f"  参数法 VaR: {var_param:.4f}")

        analyzer.config.calculation_method = "monte_carlo"
        var_mc = analyzer.calculate_var(portfolio_returns, 0.95)
        print(f"  蒙特卡洛法 VaR: {var_mc:.4f}")

        print("\n✅ 投资组合风险分析测试通过")
        return True, portfolio, risk_metrics

    except Exception as e:
        print(f"\n❌ 投资组合风险分析测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None, None


def test_var_calculator(returns_df):
    """测试3: VaR计算器"""
    print_section("测试3: VaR计算器")

    try:
        # 测试历史模拟法
        print("\n测试历史模拟法:")
        var_calc_hist = VaRCalculator(method="historical", confidence_level=0.95)

        for symbol in returns_df.columns:
            returns = returns_df[symbol]
            var = var_calc_hist.historical_var(returns)
            cvar = var_calc_hist.conditional_var(returns)

            print(f"  {symbol}:")
            print(f"    VaR: {var:.4f} ({var * 100:.2f}%)")
            print(f"    CVaR: {cvar:.4f} ({cvar * 100:.2f}%)")

        # 测试参数法
        print("\n测试参数法:")
        var_calc_param = VaRCalculator(method="parametric", confidence_level=0.95)

        symbol = returns_df.columns[0]
        returns = returns_df[symbol]
        var_param = var_calc_param.parametric_var(returns)
        print(f"  {symbol} 参数法 VaR: {var_param:.4f}")

        # 测试蒙特卡洛法
        print("\n测试蒙特卡洛法:")
        var_calc_mc = VaRCalculator(method="monte_carlo", confidence_level=0.95)
        var_mc = var_calc_mc.monte_carlo_var(returns, n_simulations=1000)
        print(f"  {symbol} 蒙特卡洛法 VaR: {var_mc:.4f}")

        # 测试投资组合VaR
        print("\n测试投资组合VaR:")
        weights = np.array([1.0 / len(returns_df.columns)] * len(returns_df.columns))
        portfolio_var = var_calc_hist.calculate_portfolio_var(returns_df, weights)
        print(f"  投资组合 VaR: {portfolio_var['var']:.4f}")
        print(f"  投资组合 CVaR: {portfolio_var['cvar']:.4f}")

        print("\n✅ VaR计算器测试通过")
        return True

    except Exception as e:
        print(f"\n❌ VaR计算器测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_kelly_criterion(returns_df):
    """测试4: 凯利准则仓位管理"""
    print_section("测试4: 凯利准则仓位管理")

    try:
        kelly = KellyCriterion(max_kelly_fraction=0.25, min_kelly_fraction=0.01)

        print("\n计算各股票的凯利仓位:")
        for symbol in returns_df.columns:
            returns = returns_df[symbol]

            # 计算凯利分数
            kelly_result = kelly.calculate_kelly_fraction(returns)

            print(f"\n  {symbol}:")
            print(
                f"    凯利分数: {kelly_result.kelly_fraction:.4f} ({kelly_result.kelly_fraction * 100:.2f}%)"
            )
            print(f"    推荐仓位: {kelly_result.recommended_position:.4f}")
            print(f"    胜率: {kelly_result.win_rate:.2%}")
            print(f"    平均盈利: {kelly_result.avg_win:.4f}")
            print(f"    平均亏损: {kelly_result.avg_loss:.4f}")
            print(f"    夏普比率: {kelly_result.sharpe_ratio:.3f}")
            print(f"    置信度: {kelly_result.confidence:.2%}")

        # 测试仓位计算
        print("\n测试仓位大小计算:")
        account_value = 1000000  # 100万账户
        signal_strength = 0.8
        volatility = returns_df.iloc[:, 0].std()

        position_size = kelly.calculate_position_size(
            account_value=account_value,
            signal_strength=signal_strength,
            volatility=volatility,
            returns=returns_df.iloc[:, 0],
        )

        print(f"  账户价值: {account_value:,.0f}元")
        print(f"  信号强度: {signal_strength:.2f}")
        print(
            f"  建议仓位: {position_size:,.0f}元 ({position_size / account_value:.2%})"
        )

        # 测试投资组合优化
        print("\n测试投资组合凯利优化:")
        optimal_weights = kelly.optimize_portfolio_kelly(returns_df)

        print("  优化后的权重:")
        for symbol, weight in optimal_weights.items():
            print(f"    {symbol}: {weight:.4f} ({weight * 100:.2f}%)")

        print("\n✅ 凯利准则测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 凯利准则测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_stop_loss_manager(stock_data):
    """测试5: 止损管理"""
    print_section("测试5: 止损管理")

    try:
        # 使用Module 02计算ATR
        calculator = TechnicalIndicators()

        print("\n计算止损价格:")

        config = StopLossConfig(
            method="atr", atr_multiplier=2.0, max_loss_percent=0.05, trailing_stop=True
        )

        stop_loss_mgr = StopLossManager(config)

        for symbol, data in stock_data.items():
            # 计算ATR
            atr_series = calculator.calculate_atr(
                data["high"], data["low"], data["close"], period=14
            )

            current_atr = atr_series.iloc[-1] if len(atr_series) > 0 else None
            entry_price = data["close"].iloc[-30]  # 30天前的入场价
            current_price = data["close"].iloc[-1]

            # 计算止损
            stop_loss = stop_loss_mgr.calculate_stop_loss(
                entry_price=entry_price,
                current_price=current_price,
                atr=current_atr,
                position_type="long",
            )

            print(f"\n  {symbol}:")
            print(f"    入场价: {entry_price:.2f}")
            print(f"    当前价: {current_price:.2f}")
            print(f"    ATR: {current_atr:.4f}" if current_atr else "    ATR: N/A")
            print(f"    止损价: {stop_loss.stop_price:.2f}")
            print(
                f"    最大损失: {stop_loss.max_loss:.2f}元 ({stop_loss.max_loss_percent:.2%})"
            )
            print(f"    止损类型: {stop_loss.stop_type}")

            # 检查是否触发
            triggered = stop_loss_mgr.check_stop_triggered(
                current_price, stop_loss.stop_price, "long"
            )
            print(f"    止损触发: {'是' if triggered else '否'}")

        # 测试不同止损方法
        print("\n测试不同止损方法:")
        symbol = list(stock_data.keys())[0]
        data = stock_data[symbol]
        entry_price = data["close"].iloc[-30]
        current_price = data["close"].iloc[-1]

        methods = ["fixed", "percent", "atr"]
        for method in methods:
            config_test = StopLossConfig(
                method=method, max_loss_percent=0.05, atr_multiplier=2.0
            )
            mgr_test = StopLossManager(config_test)

            atr = calculator.calculate_atr(
                data["high"], data["low"], data["close"], period=14
            ).iloc[-1]
            result = mgr_test.calculate_stop_loss(
                entry_price, current_price, atr, "long"
            )

            print(
                f"  {method.upper()}: 止损价={result.stop_price:.2f}, 最大损失={result.max_loss_percent:.2%}"
            )

        print("\n✅ 止损管理测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 止损管理测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_database_operations(portfolio, risk_metrics):
    """测试6: 数据库操作"""
    print_section("测试6: 数据库操作")

    try:
        # 获取数据库管理器
        risk_db = get_risk_database_manager()

        portfolio_id = "test_portfolio"
        timestamp = datetime.now()

        # 保存投资组合风险
        print("\n保存投资组合风险数据...")
        success = risk_db.save_portfolio_risk(portfolio_id, risk_metrics, timestamp)
        print(f"  {'✓' if success else '✗'} 投资组合风险数据保存")

        # 保存止损记录
        print("\n保存止损记录...")
        for symbol in portfolio.keys():
            success = risk_db.save_stop_loss(
                symbol=symbol,
                entry_price=portfolio[symbol]["cost"],
                stop_price=portfolio[symbol]["cost"] * 0.95,
                max_loss=portfolio[symbol]["cost"] * 0.05,
                max_loss_percent=0.05,
                stop_type="atr",
                reason="ATR-based stop loss",
                timestamp=timestamp,
            )
            print(f"  {'✓' if success else '✗'} {symbol} 止损记录保存")

        # 保存风险敞口
        print("\n保存风险敞口...")
        exposure = {
            "total_exposure": 1.0,
            "effective_leverage": 1.0,
            "sector_concentration": 0.3,
            "violations": [],
        }
        success = risk_db.save_exposure_analysis(portfolio_id, exposure, timestamp)
        print(f"  {'✓' if success else '✗'} 风险敞口数据保存")

        # 保存压力测试结果
        print("\n保存压力测试结果...")
        stress_result = {
            "expected_loss": -0.05,
            "max_loss": -0.15,
            "loss_probability": 0.25,
            "scenario": "market_crash",
        }
        success = risk_db.save_stress_test_result(
            portfolio_id, "2015_crash", stress_result, timestamp
        )
        print(f"  {'✓' if success else '✗'} 压力测试结果保存")

        # 查询数据
        print("\n查询历史数据...")

        # 查询风险历史
        risk_history = risk_db.get_portfolio_risk_history(portfolio_id)
        print(f"  风险历史记录: {len(risk_history)} 条")

        # 查询止损历史
        stop_loss_history = risk_db.get_stop_loss_history()
        print(f"  止损历史记录: {len(stop_loss_history)} 条")

        # 查询压力测试历史
        stress_history = risk_db.get_stress_test_history(portfolio_id)
        print(f"  压力测试历史: {len(stress_history)} 条")

        # 数据库统计
        print("\n数据库统计信息:")
        stats = risk_db.get_database_stats()
        for key, value in stats.items():
            if "size" in key:
                print(f"  {key}: {value:.2f} MB")
            else:
                print(f"  {key}: {value}")

        print("\n✅ 数据库操作测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 数据库操作测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("  Module 05 风险管理模块 - 综合测试")
    print("=" * 80)
    print(f"\n测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")

    # 测试结果统计
    results = {
        "数据准备": False,
        "投资组合风险分析": False,
        "VaR计算器": False,
        "凯利准则": False,
        "止损管理": False,
        "数据库操作": False,
    }

    # 测试1: 准备数据
    stock_data, returns_df = test_data_preparation()
    if stock_data is not None and returns_df is not None:
        results["数据准备"] = True

        # 测试2: 投资组合风险分析
        success, portfolio, risk_metrics = test_portfolio_risk_analyzer(
            stock_data, returns_df
        )
        results["投资组合风险分析"] = success

        # 测试3: VaR计算器
        results["VaR计算器"] = test_var_calculator(returns_df)

        # 测试4: 凯利准则
        results["凯利准则"] = test_kelly_criterion(returns_df)

        # 测试5: 止损管理
        results["止损管理"] = test_stop_loss_manager(stock_data)

        # 测试6: 数据库操作
        if portfolio and risk_metrics:
            results["数据库操作"] = test_database_operations(portfolio, risk_metrics)

    # 输出测试总结
    print_section("测试总结")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print("\n测试结果:")
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总测试数: {total_tests}")
    print(f"通过数: {passed_tests}")
    print(f"失败数: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests / total_tests * 100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！Module 05 风险管理模块运行正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit(main())
