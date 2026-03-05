@echo off
chcp 65001 >nul
title A股小市值股票筛选系统 - 部署脚本

echo ==========================================
echo A股小市值股票筛选系统 - 部署脚本
echo ==========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('python --version') do echo ✅ Python版本: %%a
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未找到Node.js，如需部署到Vercel请先安装
) else (
    for /f "tokens=*" %%a in ('node --version') do echo ✅ Node.js版本: %%a
)

:menu
echo.
echo 请选择操作：
echo 1) 本地测试运行
echo 2) 部署到Vercel
echo 3) 手动执行筛选
echo 4) 安装依赖
echo 5) 退出
echo.

set /p choice=请输入选项 [1-5]: 

if "%choice%"=="1" goto local_test
if "%choice%"=="2" goto deploy_vercel
if "%choice%"=="3" goto run_screening
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto exit_script

echo ❌ 无效选项，请重新选择
goto menu

:local_test
echo.
echo 🚀 启动本地测试服务器...

if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate
pip install -r requirements.txt -q

echo ✅ 依赖安装完成
echo 🌐 启动服务器，访问 http://localhost:8000
echo 按 Ctrl+C 停止服务器
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
goto menu

:deploy_vercel
echo.
echo 🚀 开始部署到Vercel...

vercel --version >nul 2>&1
if errorlevel 1 (
    echo 正在安装Vercel CLI...
    npm install -g vercel
)

echo.
echo 请选择部署方式：
echo 1) 预览部署 ^(preview^)
echo 2) 生产部署 ^(production^)
set /p deploy_choice=请选择 [1-2]: 

if "%deploy_choice%"=="2" (
    echo 🚀 执行生产部署...
    vercel --prod
) else (
    echo 🚀 执行预览部署...
    vercel
)

echo.
echo ✅ 部署完成！
pause
goto menu

:run_screening
echo.
echo 🚀 开始执行股票筛选...

call venv\Scripts\activate 2>nul

python scheduler.py --run-now

echo.
echo ✅ 筛选完成！
pause
goto menu

:install_deps
echo.
echo 📦 安装依赖...

if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ 依赖安装完成！
pause
goto menu

:exit_script
echo.
echo 👋 再见！
timeout /t 2 >nul
exit /b 0