#!/bin/bash
# 🎬 MTSCOS AI 系统自动化演示脚本
# Automated Demo Script for MTSCOS AI System

echo "🎬 MTSCOS AI 系统功能演示"
echo "================================"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查系统状态
echo "📡 1. 检查系统状态..."
STATUS=$(curl -s http://localhost:8888/api/health)
if echo "$STATUS" | grep -q "healthy"; then
    echo "   ✅ 系统运行正常"
    echo "$STATUS" | python3 -m json.tool
else
    echo "   ❌ 系统未运行，请先启动服务"
    echo "   启动命令: cd flask-app && python3 app.py"
fi

echo ""
echo "🔐 2. 检查Git仓库状态..."
GIT_STATUS=$(curl -s http://localhost:8888/api/git/status)
if echo "$GIT_STATUS" | grep -q "is_git_repo"; then
    echo "   ✅ Git仓库已初始化"
    echo "$GIT_STATUS" | python3 -m json.tool
else
    echo "   ⚠️ Git仓库未初始化或不在Git仓库目录"
fi

echo ""
echo "🤖 3. 运行AI员工批量修复..."
echo "   开始时间: $(date '+%H:%M:%S')"
FIX_RESULT=$(curl -s -X POST http://localhost:8888/api/ai/batch_fix \
  -H "Content-Type: application/json" \
  -d '{"fix_types":["template","route"]}')
echo "$FIX_RESULT" | python3 -m json.tool
echo "   结束时间: $(date '+%H:%M:%S')"

echo ""
echo "📊 4. 查看AI员工列表..."
EMPLOYEES=$(curl -s http://localhost:8888/api/ai/employees)
echo "$EMPLOYEES" | python3 -m json.tool

echo ""
echo "🛠️ 5. 查看路由统计..."
ROUTES=$(curl -s http://localhost:8888/api/routes/list)
ROUTE_COUNT=$(echo "$ROUTES" | python3 -c "import json, sys; data=json.load(sys.stdin); print(len(data['routes']))" 2>/dev/null || echo "0")
echo "   路由总数: $ROUTE_COUNT"

echo ""
echo "📈 6. 查看最近修复报告..."
REPORTS=$(curl -s http://localhost:8888/api/ai/fix_report)
if echo "$REPORTS" | grep -q "reports"; then
    echo "   ✅ 已上报的修复记录:"
    echo "$REPORTS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
reports = data.get('reports', [])
print(f'   总报告数: {len(reports)}')
if reports:
    print('   最新5条报告:')
    for i, r in enumerate(reports[:5], 1):
        status = '✅' if r.get('fixed') else '⚠️'
        print(f'   {i}. {status} {r[\"employee_name\"]} - {r[\"issue_type\"]}')
"
else
    echo "   ⚠️ 暂无修复报告"
fi

echo ""
echo "💾 7. Git操作历史..."
HISTORY=$(curl -s http://localhost:8888/api/git/history)
if echo "$HISTORY" | grep -q "history"; then
    echo "   最新操作记录:"
    echo "$HISTORY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
history = data.get('history', [])
print(f'   总操作数: {len(history)}')
if history:
    for i, h in enumerate(history[:3], 1):
        status = '✅' if h.get('success') else '❌'
        print(f'   {i}. {status} {h[\"operation\"]} - {h[\"description\"]}')
"
else
    echo "   ⚠️ 暂无操作历史"
fi

echo ""
echo "================================"
echo "✅ 演示完成！"
echo "================================"
echo ""
echo "🌐 访问地址:"
echo "   • 主站:          http://localhost:8888"
echo "   • 超级管理员:    http://localhost:8888/super_admin_dashboard"
echo "   • 管理后台:      http://localhost:8888/admin_app"
echo "   • API文档:       http://localhost:8888/api/docs"
echo ""
echo "🔐 登录凭据:"
echo "   • 硬件管理员:    wuchenghao15 / LoghinMe.1988"
echo "   • 超级管理员:    admin / password"
echo "   • 教师:          teacher / password"
echo "   • 学生:          student / password"
echo ""