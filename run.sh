#!/bin/bash
# ==========================================
# 术数决策系统 · 一键启动脚本
# ==========================================

echo "========================================="
echo "  术数决策系统 · 启动中..."
echo "========================================="

# 安装依赖
pip install -q flask flask-cors akshare requests beautifulsoup4 lxml 2>/dev/null

# 启动服务
echo ""
echo "服务已启动！"
echo "手机浏览器访问: http://本机IP:5000"
echo "按 Ctrl+C 停止"
echo ""

python app.py