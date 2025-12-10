@echo off
chcp 65001 >nul 2>&1
REM ================================
REM FinLoom 快速启动脚本 (Windows)
REM ================================

setlocal enabledelayedexpansion

echo.
echo =====================================
echo    FinLoom 量化投资引擎 - 快速启动
echo =====================================
echo.

REM 记录开始时间
set START_TIME=%TIME%

REM ============================================================
REM 第一步：环境检查
REM ============================================================
echo [步骤 1/5] 检查运行环境...
echo.

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到 Python
    echo 请先安装 Python 3.8+: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] Python 已安装: %PYTHON_VERSION%

REM 检查 Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到 Node.js
    echo 请先安装 Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo [成功] Node.js 已安装: %NODE_VERSION%

REM 检查 npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到 npm
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
echo [成功] npm 已安装: v%NPM_VERSION%
echo.

REM ============================================================
REM 第二步：设置虚拟环境并安装依赖
REM ============================================================
echo [步骤 2/5] 设置虚拟环境...
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\python.exe" (
    echo [成功] 虚拟环境已存在
    set PYTHON_EXE=.venv\Scripts\python.exe
    set PIP_EXE=.venv\Scripts\pip.exe
) else (
    echo [进行中] 创建虚拟环境...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
    set PYTHON_EXE=.venv\Scripts\python.exe
    set PIP_EXE=.venv\Scripts\pip.exe
)

echo [信息] 使用虚拟环境Python: %PYTHON_EXE%
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat

echo [步骤 2.1/5] 检查 Python 依赖...
echo.

if not exist "requirements.txt" (
    echo [警告] requirements.txt 不存在，跳过依赖安装
    goto :SKIP_PIP_INSTALL
)

REM 检查是否需要安装依赖
set NEED_INSTALL=0

REM 检查几个关键包
%PYTHON_EXE% -c "import fastapi" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set NEED_INSTALL=1
)

%PYTHON_EXE% -c "import uvicorn" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set NEED_INSTALL=1
)

if %NEED_INSTALL%==1 (
    echo [进行中] 安装 Python 依赖包（首次运行可能需要较长时间）...
    echo.
    %PYTHON_EXE% -m pip install --upgrade pip
    %PIP_EXE% install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if %ERRORLEVEL% neq 0 (
        echo [警告] 某些依赖包安装失败，继续运行...
        echo 如遇到问题，请手动运行: pip install -r requirements.txt
        echo.
    ) else (
        echo [成功] Python 依赖安装完成
        echo.
    )
) else (
    echo [成功] Python 核心依赖已安装，跳过安装步骤
    echo.
)

:SKIP_PIP_INSTALL

REM ============================================================
REM 第三步：构建前端
REM ============================================================
echo [步骤 3/5] 构建 Vue3 前端...
echo.

if not exist "web-vue" (
    echo [错误] 前端目录 web-vue 不存在
    pause
    exit /b 1
)

cd web-vue

REM 检查 package.json
if not exist "package.json" (
    echo [错误] package.json 不存在
    cd ..
    pause
    exit /b 1
)

REM 安装前端依赖
echo [进行中] 检查前端依赖...
if not exist "node_modules" (
    echo [进行中] 首次运行，安装前端依赖（可能需要 3-5 分钟）...
    echo.
    call npm install --registry=https://registry.npmmirror.com
    if %ERRORLEVEL% neq 0 (
        echo [错误] 前端依赖安装失败
        cd ..
        pause
        exit /b 1
    )
    echo [成功] 前端依赖安装完成
    echo.
) else (
    echo [成功] 前端依赖已存在
    echo.
)

REM 构建生产版本
echo [进行中] 构建前端生产版本（可能需要 1-2 分钟）...
echo.
call npm run build

if %ERRORLEVEL% neq 0 (
    echo [错误] 前端构建失败
    cd ..
    pause
    exit /b 1
)

REM 检查构建产物
if not exist "..\web\dist\index.html" (
    echo [错误] 构建产物不存在
    cd ..
    pause
    exit /b 1
)

echo [成功] 前端构建完成！
echo 构建产物位置: web\dist\
echo.

cd ..

REM ============================================================
REM 第四步：检查端口占用
REM ============================================================
echo [步骤 4/5] 检查端口占用...
echo.

REM 确保虚拟环境变量在此处可用
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
)

set PORT=8000

REM 检查端口是否被占用
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [警告] 端口 %PORT% 已被占用
    echo 如果是 FinLoom 旧进程，将尝试继续...
    echo.
) else (
    echo [成功] 端口 %PORT% 可用
    echo.
)

REM ============================================================
REM 第五步：启动后端服务
REM ============================================================
echo [步骤 5/5] 启动 FinLoom 后端服务...
echo.
echo =====================================
echo 启动信息：
echo - 服务地址: http://localhost:%PORT%
echo - 前端界面: http://localhost:%PORT%
echo - API文档: http://localhost:%PORT%/docs
echo =====================================
echo.
echo [提示] 服务启动后会自动打开浏览器
echo [提示] 按 Ctrl+C 可停止服务
echo.

REM 等待几秒让用户看到信息
timeout /t 3 /nobreak >nul

REM 在后台启动浏览器（延迟5秒等待服务启动）
start /b cmd /c "timeout /t 5 /nobreak >nul 2>&1 && start http://localhost:%PORT%"

REM 启动 FastAPI 服务
echo [启动中] 正在启动 FinLoom 服务器...
echo.
echo ======================================
echo.

REM 启动主程序（使用虚拟环境）
%PYTHON_EXE% main.py

REM 如果服务异常退出
if %ERRORLEVEL% neq 0 (
    echo.
    echo =====================================
    echo [错误] 服务启动失败
    echo =====================================
    echo.
    echo 可能的原因：
    echo 1. 端口 %PORT% 被占用
    echo 2. 依赖包未正确安装
    echo 3. 配置文件错误
    echo.
    echo 请查看上方的错误信息进行排查
    echo.
    pause
    exit /b 1
)

REM 正常退出
echo.
echo =====================================
echo FinLoom 服务已停止
echo =====================================
echo.
pause
