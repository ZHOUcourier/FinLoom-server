#!/bin/bash

# ================================
# FinLoom 快速启动脚本 (Linux/macOS)
# ================================
# 功能：
# 1. 检查运行环境（Python & Node.js）
# 2. 安装 Python 依赖
# 3. 构建 Vue3 前端
# 4. 启动后端服务
# 5. 自动打开浏览器

set -e  # 遇到错误立即退出（除非特殊处理）

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 端口配置
PORT=8000

# 打印标题
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}=====================================${NC}"
    echo -e "${CYAN}${BOLD}   FinLoom 量化投资引擎 - 快速启动${NC}"
    echo -e "${CYAN}${BOLD}=====================================${NC}"
    echo ""
}

# 打印步骤标题
print_step() {
    echo ""
    echo -e "${BLUE}${BOLD}[步骤 $1] $2${NC}"
    echo ""
}

# 打印成功信息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印警告信息
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 打印错误信息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 打印信息
print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# 开始执行
print_header

# ============================================================
# 第一步：环境检查
# ============================================================
print_step "1/5" "检查运行环境..."

# 检查 Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "未检测到 Python"
    echo "请先安装 Python 3.8+: https://www.python.org/downloads/"
    exit 1
fi

# 优先使用 python3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_success "Python 已安装: $PYTHON_VERSION"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    print_error "未检测到 Node.js"
    echo "请先安装 Node.js: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js 已安装: $NODE_VERSION"

# 检查 npm
if ! command -v npm &> /dev/null; then
    print_error "未检测到 npm"
    exit 1
fi

NPM_VERSION=$(npm --version)
print_success "npm 已安装: v$NPM_VERSION"

# ============================================================
# 第二步：安装/更新 Python 依赖
# ============================================================
print_step "2/5" "检查 Python 依赖..."

if [ ! -f "requirements.txt" ]; then
    print_warning "requirements.txt 不存在，跳过依赖安装"
else
    # 检查是否需要安装依赖
    NEED_INSTALL=0
    
    # 检查几个关键包
    if ! $PYTHON_CMD -c "import fastapi" &> /dev/null; then
        NEED_INSTALL=1
    fi
    
    if ! $PYTHON_CMD -c "import uvicorn" &> /dev/null; then
        NEED_INSTALL=1
    fi
    
    if [ $NEED_INSTALL -eq 1 ]; then
        print_info "安装 Python 依赖包（首次运行可能需要较长时间）..."
        echo ""
        
        # 升级 pip
        $PYTHON_CMD -m pip install --upgrade pip || true
        
        # 安装依赖
        $PYTHON_CMD -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple || {
            print_warning "某些依赖包安装失败，继续运行..."
            echo "如遇到问题，请手动运行: pip install -r requirements.txt"
        }
        
        print_success "Python 依赖安装完成"
    else
        print_success "Python 核心依赖已安装，跳过安装步骤"
    fi
fi

# ============================================================
# 第三步：构建前端
# ============================================================
print_step "3/5" "构建 Vue3 前端..."

if [ ! -d "web-vue" ]; then
    print_error "前端目录 web-vue 不存在"
    exit 1
fi

cd web-vue

# 检查 package.json
if [ ! -f "package.json" ]; then
    print_error "package.json 不存在"
    cd ..
    exit 1
fi

# 安装前端依赖
print_info "检查前端依赖..."
if [ ! -d "node_modules" ]; then
    print_info "首次运行，安装前端依赖（可能需要 3-5 分钟）..."
    echo ""
    npm install --registry=https://registry.npmmirror.com || {
        print_error "前端依赖安装失败"
        cd ..
        exit 1
    }
    print_success "前端依赖安装完成"
else
    print_success "前端依赖已存在"
fi

# 构建生产版本
echo ""
print_info "构建前端生产版本（可能需要 1-2 分钟）..."
echo ""
npm run build || {
    print_error "前端构建失败"
    cd ..
    exit 1
}

# 检查构建产物
if [ ! -f "../web/dist/index.html" ]; then
    print_error "构建产物不存在"
    cd ..
    exit 1
fi

print_success "前端构建完成！"
print_info "构建产物位置: web/dist/"

cd ..

# ============================================================
# 第四步：检查端口占用
# ============================================================
print_step "4/5" "检查端口占用..."

# 检查端口是否被占用
if command -v lsof &> /dev/null; then
    # macOS/Linux with lsof
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $PORT 已被占用"
        echo "如果是 FinLoom 旧进程，将尝试继续..."
    else
        print_success "端口 $PORT 可用"
    fi
elif command -v netstat &> /dev/null; then
    # Linux with netstat
    if netstat -tuln | grep -q ":$PORT "; then
        print_warning "端口 $PORT 已被占用"
        echo "如果是 FinLoom 旧进程，将尝试继续..."
    else
        print_success "端口 $PORT 可用"
    fi
else
    print_info "无法检查端口占用状态（缺少 lsof 或 netstat）"
fi

# ============================================================
# 第五步：启动后端服务
# ============================================================
print_step "5/5" "启动 FinLoom 后端服务..."

echo ""
echo -e "${CYAN}${BOLD}=====================================${NC}"
echo -e "${CYAN}${BOLD}启动信息：${NC}"
echo -e "${CYAN}- 服务地址: ${GREEN}http://localhost:$PORT${NC}"
echo -e "${CYAN}- 前端界面: ${GREEN}http://localhost:$PORT${NC}"
echo -e "${CYAN}- API文档: ${GREEN}http://localhost:$PORT/docs${NC}"
echo -e "${CYAN}${BOLD}=====================================${NC}"
echo ""
echo -e "${YELLOW}[提示] 服务启动后会自动打开浏览器${NC}"
echo -e "${YELLOW}[提示] 按 Ctrl+C 可停止服务${NC}"
echo ""

# 在后台启动浏览器（延迟5秒等待服务启动）
(sleep 5 && {
    if command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "http://localhost:$PORT" &> /dev/null
    elif command -v open &> /dev/null; then
        # macOS
        open "http://localhost:$PORT"
    fi
}) &

# 启动主程序
print_info "正在启动 FinLoom 服务器..."
echo ""
echo -e "${CYAN}${BOLD}======================================${NC}"
echo ""

# 设置陷阱以便优雅退出
trap 'echo ""; echo ""; echo -e "${CYAN}${BOLD}=====================================${NC}"; echo -e "${YELLOW}FinLoom 服务已停止${NC}"; echo -e "${CYAN}${BOLD}=====================================${NC}"; echo ""; exit 0' INT TERM

# 启动服务
$PYTHON_CMD main.py || {
    echo ""
    echo -e "${RED}${BOLD}=====================================${NC}"
    echo -e "${RED}${BOLD}[错误] 服务启动失败${NC}"
    echo -e "${RED}${BOLD}=====================================${NC}"
    echo ""
    echo "可能的原因："
    echo "1. 端口 $PORT 被占用"
    echo "2. 依赖包未正确安装"
    echo "3. 配置文件错误"
    echo ""
    echo "请查看上方的错误信息进行排查"
    echo ""
    exit 1
}







