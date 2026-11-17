@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -X utf8 app.py --open
if errorlevel 1 (
  echo.
  echo 启动未完成。请查看上方错误；依赖安装方式见“开始使用.md”。
  pause
)
