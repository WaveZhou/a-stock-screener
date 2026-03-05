#!/bin/bash

# A股小市值股票筛选系统 - 部署脚本

echo "=========================================="
echo "A股小市值股票筛选系统 - 部署脚本"
echo "=========================================="

# 检查是否安装了必要的工具
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ 未安装 $1，请先安装"
        return 1
    else
        echo "✅ $1 已安装"
        return 0
    fi
}

# 显示菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 本地测试运行"
    echo "2) 部署到Vercel"
    echo "3) 手动执行筛选"
    echo "4) 安装依赖"
    echo "5) 退出"
    echo ""
}

# 本地测试
local_test() {
    echo ""
    echo "🚀 启动本地测试服务器..."
    
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    echo "✅ 依赖安装完成"
    echo "🌐 启动服务器，访问 http://localhost:8000"
    echo "按 Ctrl+C 停止服务器"
    echo ""
    
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# 部署到Vercel
deploy_vercel() {
    echo ""
    echo "🚀 开始部署到Vercel..."
    
    if ! check_command "vercel"; then
        echo "正在安装Vercel CLI..."
        npm install -g vercel
    fi
    
    echo ""
    echo "请选择部署方式："
    echo "1) 预览部署 (preview)"
    echo "2) 生产部署 (production)"
    read -p "请选择 [1-2]: " deploy_choice
    
    if [ "$deploy_choice" = "2" ]; then
        echo "🚀 执行生产部署..."
        vercel --prod
    else
        echo "🚀 执行预览部署..."
        vercel
    fi
    
    echo ""
    echo "✅ 部署完成！"
}

# 手动执行筛选
run_screening() {
    echo ""
    echo "🚀 开始执行股票筛选..."
    
    source venv/bin/activate 2>/dev/null || echo "使用系统Python环境"
    
    python scheduler.py --run-now
    
    echo ""
    echo "✅ 筛选完成！"
}

# 安装依赖
install_deps() {
    echo ""
    echo "📦 安装依赖..."
    
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo ""
    echo "✅ 依赖安装完成！"
}

# 主程序
main() {
    # 检查Python
    if ! check_command "python3" && ! check_command "python"; then
        echo "❌ 需要安装Python 3.8+"
        exit 1
    fi
    
    # 检查Node.js（用于Vercel）
    check_command "node" || echo "⚠️ 如需部署到Vercel，请安装Node.js"
    
    while true; do
        show_menu
        read -p "请输入选项 [1-5]: " choice
        
        case $choice in
            1)
                local_test
                ;;
            2)
                deploy_vercel
                ;;
            3)
                run_screening
                ;;
            4)
                install_deps
                ;;
            5)
                echo "👋 再见！"
                exit 0
                ;;
            *)
                echo "❌ 无效选项，请重新选择"
                ;;
        esac
    done
}

# 运行主程序
main