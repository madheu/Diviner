#!/bin/bash
# ==========================================
# 术数决策系统 · 公网分享脚本
# ngrok 已配置你的 authtoken
# ==========================================

echo "========================================="
echo "  术数决策系统 · 公网分享"
echo "========================================="
echo ""

# 清除代理（ngrok 免费版不支持代理）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 启动 Flask 后台
echo "启动决策系统..."
python app.py &
FLASK_PID=$!
sleep 2

# 启动 ngrok
echo "创建公网隧道..."
ngrok http 5000 --log=stdout &
NGROK_PID=$!
sleep 5

# 获取公网地址
PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for t in data.get('tunnels', []):
        print(t.get('public_url', ''))
except: pass
" 2>/dev/null)

if [ -n "$PUBLIC_URL" ]; then
    echo ""
    echo "========================================="
    echo "  ✅ 公网地址: $PUBLIC_URL"
    echo "  把这个链接发给任何人即可！"
    echo "========================================="
else
    echo ""
    echo "⚠️  隧道建立中，请手动查看 ngrok 输出中的 Forwarding 地址"
    echo "   格式类似: https://xxxx.ngrok-free.app -> http://localhost:5000"
fi

echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $FLASK_PID $NGROK_PID 2>/dev/null; exit" INT TERM
wait $FLASK_PID