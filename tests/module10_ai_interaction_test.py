# -*- coding: utf-8 -*-
"""
Module 10 AI交互模块测试文件
测试所有组件的功能

使用说明：
---------
1. 快速测试模式（推荐，默认）：
   python tests/module10_ai_interaction_test.py
   - 不加载FIN-R1模型，使用规则引擎
   - 运行时间：约1-2分钟
   - 适合日常开发测试

2. 完整测试模式（可选）：
   修改文件末尾：main(use_fin_r1_model=True)
   - 加载真实FIN-R1模型进行测试
   - 运行时间：约5-10分钟
   - 适合发布前的完整验证

注意：
- 警告信息（do_sample/temperature等）已优化，可以忽略
- 如果仍有警告，是正常的，不影响功能
"""

import sys
from pathlib import Path

# 设置 Windows 控制台 UTF-8 编码支持
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime

from common.logging_system import setup_logger
from module_10_ai_interaction import (
    # 对话历史
    ConversationHistoryManager,
    ConversationRecord,
    # 对话管理
    DialogueManager,
    DialogueState,
    # FIN-R1集成
    FINR1Integration,
    # 意图分类
    IntentClassifier,
    InvestmentHorizon,
    # NLP处理
    NLPProcessor,
    # 参数映射
    ParameterMapper,
    # 推荐引擎
    RecommendationEngine,
    # 需求解析
    RequirementParser,
    # 响应生成
    ResponseGenerator,
    RiskTolerance,
    classify_user_intent,
    create_nlp_processor,
    generate_default_recommendations,
    # 数据库
    get_database_manager,
    map_requirement_to_parameters,
    parse_user_requirement,
)

logger = setup_logger("module10_test")


def test_requirement_parser():
    """测试需求解析器"""
    print("\n========== 测试需求解析器 ==========")

    parser = RequirementParser()

    # 测试用例
    test_cases = [
        "我想投资10万元，风险偏好稳健，投资期限3年",
        "有50万资金，比较保守，不想亏钱",
        "激进投资，追求高收益，能承受30%的回撤",
        "投资100万，中期持有，期望年化收益15%",
    ]

    for i, user_input in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {user_input}")
        try:
            parsed = parser.parse_requirement(user_input)
            print(f"  投资金额: {parsed.investment_amount}")
            print(f"  风险偏好: {parsed.risk_tolerance}")
            print(f"  投资期限: {parsed.investment_horizon}")
            print(f"  投资目标: {[goal.goal_type for goal in parsed.investment_goals]}")
            print(f"  需要澄清: {parsed.clarification_needed}")
            print(f"  置信度: {parsed.confidence_scores}")
        except Exception as e:
            print(f"  ❌ 错误: {e}")

    print("\n✅ 需求解析器测试完成")


def test_nlp_processor():
    """测试NLP处理器"""
    print("\n========== 测试NLP处理器 ==========")

    processor = NLPProcessor()

    test_text = "我想买入平安银行的股票，投资10万元，预期收益15%"

    # 测试分词
    print(f"\n原文: {test_text}")
    tokens = processor.tokenize(test_text)
    print(f"分词结果: {tokens}")

    # 测试实体提取
    entities = processor.extract_entities(test_text)
    print(f"\n提取的实体:")
    for entity in entities:
        print(f"  {entity.entity_type}: {entity.value} -> {entity.normalized_value}")

    # 测试关键词提取
    keywords = processor.extract_keywords(test_text, top_k=5)
    print(f"\n关键词:")
    for word, weight in keywords:
        print(f"  {word}: {weight:.4f}")

    # 测试情感分析
    test_sentiments = [
        "市场走势强劲，看好未来表现",
        "风险太大，不建议买入",
        "市场震荡，观望为主",
    ]
    print(f"\n情感分析:")
    for text in test_sentiments:
        sentiment = processor.analyze_sentiment(text)
        print(f"  {text}")
        print(
            f"    情感: {sentiment.sentiment}, 分数: {sentiment.score:.2f}, 置信度: {sentiment.confidence:.2f}"
        )

    print("\n✅ NLP处理器测试完成")


def test_intent_classifier():
    """测试意图分类器"""
    print("\n========== 测试意图分类器 ==========")

    classifier = IntentClassifier()

    test_cases = [
        "你好",
        "帮我设计一个投资策略",
        "000001的价格是多少",
        "我的收益怎么样",
        "现在应该买还是卖",
        "市场行情如何",
        "帮我回测一下这个策略",
        "确认",
        "不要",
        "再见",
    ]

    print(f"\n意图分类测试:")
    for text in test_cases:
        intent, confidence, entities = classifier.classify(text)
        print(f"  '{text}'")
        print(f"    意图: {intent}, 置信度: {confidence:.2f}, 实体: {entities}")

    print("\n✅ 意图分类器测试完成")


def test_dialogue_manager():
    """测试对话管理器"""
    print("\n========== 测试对话管理器 ==========")

    mgr = DialogueManager()

    # 启动对话
    context = mgr.start_conversation("test_user_001")
    print(f"\n启动对话: {context.session_id}")
    print(f"当前状态: {context.current_state}")

    # 模拟对话流程
    conversation_flow = [
        "你好",
        "我想投资10万元",
        "风险偏好稳健",
        "投资期限3年",
        "确认",
    ]

    print(f"\n对话流程:")
    for user_input in conversation_flow:
        print(f"\n用户: {user_input}")
        result = mgr.process_user_input(context.session_id, user_input)
        print(f"系统: {result['response']}")
        print(f"状态: {result['state']}")
        print(f"意图: {result['intent']}")
        print(f"回合: {result['turn_count']}")

    # 结束对话
    success = mgr.end_conversation(context.session_id)
    print(f"\n对话结束: {'成功' if success else '失败'}")

    print("\n✅ 对话管理器测试完成")


def test_parameter_mapper():
    """测试参数映射器"""
    print("\n========== 测试参数映射器 ==========")

    parser = RequirementParser()
    mapper = ParameterMapper()

    # 解析需求
    user_input = "投资50万，激进型，长期持有，期望年化25%"
    parsed = parser.parse_requirement(user_input)

    # 映射到系统参数
    system_params = mapper.map_to_system_parameters(parsed)

    print(f"\n原始输入: {user_input}")
    print(f"\n系统参数:")
    print(f"  风险参数: {system_params['risk_params']}")
    print(f"  策略参数: {system_params['strategy_params']}")
    print(f"  时间参数: {system_params['horizon_params']}")

    # 映射到不同模块
    print(f"\n映射到各模块:")
    modules = [
        "module_03_ai_models",
        "module_05_risk_management",
        "module_07_optimization",
        "module_09_backtesting",
    ]

    for module_name in modules:
        module_params = mapper.map_to_module_parameters(system_params, module_name)
        print(f"  {module_name}:")
        print(f"    {module_params}")

    # 验证参数
    is_valid, issues = mapper.validate_parameters(system_params)
    print(f"\n参数验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    if issues:
        print(f"  问题: {issues}")

    print("\n✅ 参数映射器测试完成")


def test_response_generator():
    """测试响应生成器"""
    print("\n========== 测试响应生成器 ==========")

    generator = ResponseGenerator(tone="friendly")

    # 测试不同类型的响应
    test_cases = [
        ("greeting", {}),
        (
            "investment_inquiry",
            {
                "risk_level": "稳健型",
                "horizon": "3年",
                "recommendations": "价值投资策略",
            },
        ),
        ("error", {"error_message": "数据获取失败"}),
    ]

    print(f"\n响应生成测试:")
    for intent, entities in test_cases:
        response = generator.generate_response(intent, entities)
        print(f"\n意图: {intent}")
        print(f"响应: {response}")

    # 测试澄清响应
    clarification = generator.generate_clarification_response(
        ["investment_amount", "risk_tolerance"]
    )
    print(f"\n澄清响应:")
    print(clarification)

    # 测试确认响应
    confirmation = generator.generate_confirmation_response(
        "investment",
        {
            "amount": "10万元",
            "strategy": "稳健成长型",
            "risk_level": "中等",
            "expected_return": "15%",
        },
    )
    print(f"\n确认响应:")
    print(confirmation)

    print("\n✅ 响应生成器测试完成")


def test_recommendation_engine():
    """测试推荐引擎"""
    print("\n========== 测试推荐引擎 ==========")

    engine = RecommendationEngine()

    # 测试组合推荐
    user_profile = {
        "risk_tolerance": "moderate",
        "investment_horizon": "long_term",
        "goals": ["wealth_growth"],
        "target_return": 0.15,
    }

    market_conditions = {"trend": "neutral", "volatility": "medium"}

    print(f"\n用户画像: {user_profile}")
    print(f"市场状况: {market_conditions}")

    recommendations = engine.generate_portfolio_recommendations(
        user_profile, market_conditions, num_recommendations=3
    )

    print(f"\n投资组合推荐:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n推荐 {i}: {rec.name}")
        print(f"  描述: {rec.description}")
        print(f"  适合度: {rec.suitability_score:.2f}")
        print(f"  资产配置: {rec.asset_allocation}")
        print(f"  预期收益: {rec.expected_metrics['expected_return']:.2%}")
        print(f"  波动率: {rec.expected_metrics['volatility']:.2%}")
        print(f"  夏普比率: {rec.expected_metrics['sharpe_ratio']:.2f}")
        print(f"  优点: {rec.pros}")
        print(f"  缺点: {rec.cons}")

    print("\n✅ 推荐引擎测试完成")


async def test_fin_r1_integration(use_model=False):
    """测试FIN-R1集成

    Args:
        use_model: 是否使用真实模型（默认False使用规则引擎，快速测试）
    """
    print("\n========== 测试FIN-R1集成 ==========")

    config = {
        "model": {
            "model_path": ".Fin-R1" if use_model else "",
            "device": "cpu",
            "max_length": 2048,
            "temperature": 0.7,
        }
    }

    try:
        if use_model:
            print("正在加载FIN-R1模型（预计1-2分钟）...")
        else:
            print("使用规则引擎模式（快速测试，不加载模型）...")
        fin_r1 = FINR1Integration(config)

        if fin_r1.model is not None:
            print("✅ 模型加载成功")
        else:
            print("⚠️ 模型未加载，使用规则引擎模式")

        user_input = "我是新手投资者，有20万资金，想稳健投资"

        print(f"\n用户输入: {user_input}")
        if use_model:
            print(f"正在调用FIN-R1处理（使用模型生成，预计1-5分钟）...")
        else:
            print(f"正在调用FIN-R1处理（规则引擎模式，快速）...")

        start_time = datetime.now()
        result = await fin_r1.process_request(user_input)
        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ 处理完成（耗时: {duration:.2f}秒）")
        print(f"\n处理结果:")

        parsed = result["parsed_requirement"]
        print(f"  解析的需求:")
        print(f"    - 投资金额: {parsed.get('investment_amount', 'N/A')}")
        print(f"    - 风险偏好: {parsed.get('risk_tolerance', 'N/A')}")
        print(f"    - 投资期限: {parsed.get('investment_horizon', 'N/A')}")

        model_output = result["model_output"]
        print(f"  模型输出:")
        print(f"    - 策略建议: {model_output.get('strategy_recommendation', 'N/A')}")
        print(f"    - 风险评估: {model_output.get('risk_assessment', 'N/A')}")
        print(f"    - 置信度: {model_output.get('confidence_score', 'N/A')}")
        print(f"    - 市场展望: {model_output.get('market_outlook', 'N/A')}")
        print(f"    - 分析方法: {model_output.get('analysis_method', 'N/A')}")

        print(f"  策略参数: {result['strategy_params']}")
        print(f"  风险参数: {result['risk_params']}")

        # 测试数据库保存
        db_manager = get_database_manager("data/test_fin_r1.db")
        req_id = db_manager.save_user_requirement(
            user_id="test_user",
            session_id="test_session",
            raw_input=user_input,
            parsed_data=result["parsed_requirement"],
            system_parameters=result["strategy_params"],
        )
        print(f"\n  数据库保存: 需求ID = {req_id}")

        print("\n✅ FIN-R1集成测试完成")

    except Exception as e:
        print(f"\n❌ FIN-R1测试失败: {e}")
        import traceback

        traceback.print_exc()


def test_conversation_history():
    """测试对话历史管理"""
    print("\n========== 测试对话历史管理 ==========")

    history_mgr = ConversationHistoryManager(
        storage_path=os.path.join("data", "test_conversation_history"), storage_type="sqlite"
    )

    # 创建测试记录
    session_id = "test_session_001"
    user_id = "test_user_001"

    records = [
        ConversationRecord(
            session_id=session_id,
            user_id=user_id,
            turn_id=f"{session_id}_1",
            timestamp=datetime.now(),
            user_input="你好",
            system_response="您好！我是您的智能投资顾问",
            intent="greeting",
            entities={},
            confidence=0.9,
            context_state="greeting",
            metadata={},
        ),
        ConversationRecord(
            session_id=session_id,
            user_id=user_id,
            turn_id=f"{session_id}_2",
            timestamp=datetime.now(),
            user_input="我想投资10万",
            system_response="好的，您想投资10万元。请问您的风险偏好是？",
            intent="create_strategy",
            entities={"investment_amount": 100000},
            confidence=0.85,
            context_state="requirement_gathering",
            metadata={},
        ),
    ]

    # 保存记录
    print(f"\n保存对话记录:")
    for record in records:
        success = history_mgr.save_conversation_turn(record)
        print(f"  回合 {record.turn_id}: {'成功' if success else '失败'}")

    # 查询记录
    print(f"\n查询会话历史:")
    retrieved_records = history_mgr.get_session_history(session_id)
    for record in retrieved_records:
        print(f"  用户: {record.user_input}")
        print(f"  系统: {record.system_response}")
        print(f"  意图: {record.intent} (置信度: {record.confidence})")

    # 获取统计信息
    stats = history_mgr.get_statistics()
    print(f"\n统计信息:")
    print(f"  总对话数: {stats['total_conversations']}")
    print(f"  总回合数: {stats['total_turns']}")

    print("\n✅ 对话历史管理测试完成")


def test_database_manager():
    """测试数据库管理器"""
    print("\n========== 测试数据库管理器 ==========")

    db_manager = get_database_manager("data/test_module10.db")

    # 测试保存用户需求
    print(f"\n测试保存用户需求:")
    requirement_id = db_manager.save_user_requirement(
        user_id="test_user_001",
        session_id="test_session_001",
        raw_input="投资10万，稳健型，3年",
        parsed_data={
            "investment_amount": 100000,
            "risk_tolerance": "moderate",
            "investment_horizon": "medium_term",
        },
        system_parameters={
            "risk_params": {"max_drawdown": 0.15},
            "strategy_params": {"rebalance_frequency": "weekly"},
        },
    )
    print(f"  需求ID: {requirement_id}")

    # 测试保存策略推荐
    print(f"\n测试保存策略推荐:")
    rec_id = db_manager.save_strategy_recommendation(
        user_id="test_user_001",
        session_id="test_session_001",
        requirement_id=requirement_id,
        recommendation_type="portfolio",
        recommendation_data={
            "name": "稳健成长型组合",
            "expected_return": 0.15,
            "volatility": 0.12,
        },
        confidence_score=0.85,
    )
    print(f"  推荐ID: {rec_id}")

    # 测试保存对话会话
    print(f"\n测试保存对话会话:")
    success = db_manager.save_dialogue_session(
        session_id="test_session_001",
        user_id="test_user_001",
        start_time=datetime.now(),
        session_data={"turn_count": 5, "final_state": "completed"},
    )
    print(f"  会话保存: {'成功' if success else '失败'}")

    # 测试保存意图日志
    print(f"\n测试保存意图日志:")
    success = db_manager.save_intent_log(
        session_id="test_session_001",
        turn_id=1,
        user_input="我想投资",
        detected_intent="create_strategy",
        confidence=0.9,
        entities={"investment_amount": 100000},
    )
    print(f"  意图日志保存: {'成功' if success else '失败'}")

    # 测试查询
    print(f"\n测试查询:")
    requirements = db_manager.get_user_requirements(user_id="test_user_001", limit=5)
    print(f"  查询到 {len(requirements)} 条需求记录")

    recommendations = db_manager.get_strategy_recommendations(
        session_id="test_session_001", limit=5
    )
    print(f"  查询到 {len(recommendations)} 条推荐记录")

    # 测试统计信息
    print(f"\n统计信息:")
    stats = db_manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ 数据库管理器测试完成")


def test_complete_workflow():
    """测试完整工作流"""
    print("\n========== 测试完整工作流 ==========")

    # 初始化所有组件
    dialogue_mgr = DialogueManager()
    parser = RequirementParser()
    mapper = ParameterMapper()
    recommender = RecommendationEngine()
    db_manager = get_database_manager("data/test_module10_workflow.db")

    # 1. 启动对话
    print(f"\n1. 启动对话")
    context = dialogue_mgr.start_conversation("workflow_user_001")
    print(f"   会话ID: {context.session_id}")

    # 2. 用户输入
    user_input = "我有100万资金，想投资3-5年，能承受15%的回撤，期望年化收益20%"
    print(f"\n2. 用户输入: {user_input}")

    # 3. 处理对话
    result = dialogue_mgr.process_user_input(context.session_id, user_input)
    print(f"\n3. 对话处理结果:")
    print(f"   响应: {result['response']}")
    print(f"   状态: {result['state']}")

    # 4. 解析需求
    print(f"\n4. 解析投资需求")
    parsed = parser.parse_requirement(user_input)
    print(f"   投资金额: {parsed.investment_amount}")
    print(f"   风险偏好: {parsed.risk_tolerance}")
    print(f"   投资期限: {parsed.investment_horizon}")

    # 5. 映射参数
    print(f"\n5. 映射系统参数")
    system_params = mapper.map_to_system_parameters(parsed)
    print(f"   风险参数: {system_params['risk_params']}")
    print(f"   策略参数: {system_params['strategy_params']}")

    # 6. 保存需求
    print(f"\n6. 保存到数据库")
    requirement_id = db_manager.save_user_requirement(
        user_id="workflow_user_001",
        session_id=context.session_id,
        raw_input=user_input,
        parsed_data=parsed.to_dict(),
        system_parameters=system_params,
    )
    print(f"   需求ID: {requirement_id}")

    # 7. 生成推荐
    print(f"\n7. 生成投资推荐")
    recommendations = recommender.generate_portfolio_recommendations(
        user_profile={
            "risk_tolerance": parsed.risk_tolerance.value
            if parsed.risk_tolerance
            else "moderate",
            "investment_horizon": parsed.investment_horizon.value
            if parsed.investment_horizon
            else "medium_term",
            "target_return": 0.20,
        },
        market_conditions={"trend": "neutral", "volatility": "medium"},
        num_recommendations=2,
    )

    for i, rec in enumerate(recommendations, 1):
        print(f"\n   推荐 {i}: {rec.name}")
        print(f"   适合度: {rec.suitability_score:.2f}")
        print(f"   预期收益: {rec.expected_metrics['expected_return']:.2%}")

        # 保存推荐
        rec_id = db_manager.save_strategy_recommendation(
            user_id="workflow_user_001",
            session_id=context.session_id,
            requirement_id=requirement_id,
            recommendation_type="portfolio",
            recommendation_data={
                "name": rec.name,
                "allocation": rec.asset_allocation,
                "expected_metrics": rec.expected_metrics,
            },
            confidence_score=rec.suitability_score,
        )
        print(f"   推荐ID: {rec_id}")

    # 8. 结束对话
    print(f"\n8. 结束对话")
    dialogue_mgr.end_conversation(context.session_id)

    # 9. 查询统计
    print(f"\n9. 数据库统计")
    stats = db_manager.get_statistics()
    print(f"   总需求数: {stats['total_requirements']}")
    print(f"   总推荐数: {stats['total_recommendations']}")

    print("\n✅ 完整工作流测试完成")


def main(use_fin_r1_model=False):
    """主测试函数

    Args:
        use_fin_r1_model: 是否使用真实FIN-R1模型（默认False，使用规则引擎快速测试）
    """
    print("\n" + "=" * 60)
    print("Module 10 AI交互模块 - 综合测试")
    if not use_fin_r1_model:
        print("模式：快速测试（规则引擎，不加载FIN-R1模型）")
        print("提示：如需测试真实模型，请设置 use_fin_r1_model=True")
    else:
        print("模式：完整测试（包含FIN-R1模型，预计耗时5-10分钟）")
    print("=" * 60)

    try:
        # 运行所有测试
        test_requirement_parser()
        test_nlp_processor()
        test_intent_classifier()
        test_dialogue_manager()
        test_parameter_mapper()
        test_response_generator()
        test_recommendation_engine()

        # FIN-R1测试（异步）
        asyncio.run(test_fin_r1_integration(use_model=use_fin_r1_model))

        test_conversation_history()
        test_database_manager()
        test_complete_workflow()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main(use_fin_r1_model=True)
