@echo off
echo ========================================
echo   图片查看器 - 环境配置
echo ========================================
echo.

:: 创建conda环境
echo [1/3] 创建conda环境 image_tool ...
conda create -n image_tool python=3.11 -y
if errorlevel 1 (
    echo 环境创建失败！
    pause
    exit /b 1
)

:: 激活环境并安装依赖
echo [2/3] 安装依赖包 ...
call conda activate image_tool
pip install PyQt6 Pillow

echo [3/3] 配置完成！
echo.
echo 使用方法：
echo   conda activate image_tool
echo   python main.py
echo.
pause
