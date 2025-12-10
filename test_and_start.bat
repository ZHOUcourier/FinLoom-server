@echo off
chcp 65001 > nul
echo ========================================
echo FinLoom 测试与启动脚本
echo ========================================
echo.

echo [1] 检查后端服务状态...
curl -s http://127.0.0.1:8000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] 后端服务已运行
    echo.
    echo [2] 运行API测试...
    python tests\test_market_apis.py
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo [OK] 所有测试通过!
        echo ========================================
        echo.
        echo 请在浏览器中访问前端: http://localhost:5173
        echo 测试以下功能:
        echo   1. 市场分析页面 - 查看更多按钮
        echo   2. 页面跳转速度 (不应被数据加载阻塞^)
        echo   3. 市场情绪数据显示
        echo.
    ) else (
        echo.
        echo ========================================
        echo [ERROR] 部分测试失败
        echo ========================================
        echo 请查看上方的错误信息
    )
) else (
    echo [ERROR] 后端服务未运行
    echo.
    echo [INFO] 正在启动后端服务...
    echo.
    start "FinLoom Backend" cmd /k "python main.py"
    echo.
    echo [INFO] 请等待后端服务完全启动 (约10-20秒^)
    echo [INFO] 看到 "市场数据预加载完成" 后，再次运行本脚本测试
)

echo.
pause

