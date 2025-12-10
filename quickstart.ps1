# FinLoom 快速启动脚本 (PowerShell 版本)
# 功能：检查环境、构建前端、启动服务

# 设置 UTF-8 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   FinLoom 量化投资引擎 - 快速启动" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 第一步：环境检查
# ============================================================
Write-Host "[步骤 1/5] 检查运行环境..." -ForegroundColor Yellow
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[成功] Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 Python" -ForegroundColor Red
    Write-Host "请先安装 Python 3.8+: https://www.python.org/downloads/"
    pause
    exit 1
}

# 检查 Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[成功] Node.js 已安装: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 Node.js" -ForegroundColor Red
    Write-Host "请先安装 Node.js: https://nodejs.org/"
    pause
    exit 1
}

# 检查 npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "[成功] npm 已安装: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 npm" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""

# ============================================================
# 第二步：检查 Python 依赖
# ============================================================
Write-Host "[步骤 2/5] 检查 Python 依赖..." -ForegroundColor Yellow
Write-Host ""

$needInstall = $false

# 检查关键包
try {
    python -c "import fastapi" 2>&1 | Out-Null
} catch {
    $needInstall = $true
}

try {
    python -c "import uvicorn" 2>&1 | Out-Null
} catch {
    $needInstall = $true
}

if ($needInstall) {
    Write-Host "[进行中] 安装 Python 依赖包..." -ForegroundColor Yellow
    Write-Host ""
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[警告] 某些依赖包安装失败，继续运行..." -ForegroundColor Yellow
    } else {
        Write-Host "[成功] Python 依赖安装完成" -ForegroundColor Green
    }
} else {
    Write-Host "[成功] Python 核心依赖已安装，跳过安装步骤" -ForegroundColor Green
}

Write-Host ""

# ============================================================
# 第三步：构建前端
# ============================================================
Write-Host "[步骤 3/5] 构建 Vue3 前端..." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path "web-vue")) {
    Write-Host "[错误] 前端目录 web-vue 不存在" -ForegroundColor Red
    pause
    exit 1
}

Set-Location web-vue

# 检查 package.json
if (-not (Test-Path "package.json")) {
    Write-Host "[错误] package.json 不存在" -ForegroundColor Red
    Set-Location ..
    pause
    exit 1
}

# 安装前端依赖
Write-Host "[进行中] 检查前端依赖..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "[进行中] 首次运行，安装前端依赖（可能需要 3-5 分钟）..." -ForegroundColor Yellow
    Write-Host ""
    npm install --registry=https://registry.npmmirror.com
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 前端依赖安装失败" -ForegroundColor Red
        Set-Location ..
        pause
        exit 1
    }
    Write-Host "[成功] 前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[成功] 前端依赖已存在" -ForegroundColor Green
}

Write-Host ""

# 构建生产版本
Write-Host "[进行中] 构建前端生产版本（可能需要 1-2 分钟）..." -ForegroundColor Yellow
Write-Host ""
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 前端构建失败" -ForegroundColor Red
    Set-Location ..
    pause
    exit 1
}

# 检查构建产物
if (-not (Test-Path "..\web\dist\index.html")) {
    Write-Host "[错误] 构建产物不存在" -ForegroundColor Red
    Set-Location ..
    pause
    exit 1
}

Write-Host "[成功] 前端构建完成！" -ForegroundColor Green
Write-Host "构建产物位置: web\dist\" -ForegroundColor Gray
Write-Host ""

Set-Location ..

# ============================================================
# 第四步：检查端口占用
# ============================================================
Write-Host "[步骤 4/5] 检查端口占用..." -ForegroundColor Yellow
Write-Host ""

$port = 8000
$tcpConnection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($tcpConnection) {
    Write-Host "[警告] 端口 $port 已被占用" -ForegroundColor Yellow
    Write-Host "如果是 FinLoom 旧进程，将尝试继续..." -ForegroundColor Yellow
} else {
    Write-Host "[成功] 端口 $port 可用" -ForegroundColor Green
}

Write-Host ""

# ============================================================
# 第五步：启动后端服务
# ============================================================
Write-Host "[步骤 5/5] 启动 FinLoom 后端服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "启动信息：" -ForegroundColor Cyan
Write-Host "- 服务地址: http://localhost:$port" -ForegroundColor Green
Write-Host "- 前端界面: http://localhost:$port" -ForegroundColor Green
Write-Host "- API文档: http://localhost:$port/docs" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[提示] 服务启动后会自动打开浏览器" -ForegroundColor Yellow
Write-Host "[提示] 按 Ctrl+C 可停止服务" -ForegroundColor Yellow
Write-Host ""

# 延迟5秒后打开浏览器
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:8000"
} | Out-Null

# 启动主程序
Write-Host "[启动中] 正在启动 FinLoom 服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

python main.py

# 如果服务异常退出
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "=====================================" -ForegroundColor Red
    Write-Host "[错误] 服务启动失败" -ForegroundColor Red
    Write-Host "=====================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因："
    Write-Host "1. 端口 $port 被占用"
    Write-Host "2. 依赖包未正确安装"
    Write-Host "3. 配置文件错误"
    Write-Host ""
    Write-Host "请查看上方的错误信息进行排查"
    Write-Host ""
    pause
    exit 1
}

# 正常退出
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "FinLoom 服务已停止" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""




