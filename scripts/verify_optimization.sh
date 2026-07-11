#!/bin/bash
# MTSCOS 系统优化验证脚本

echo "========================================="
echo "MTSCOS 系统优化验证"
echo "========================================="
echo ""

echo "1. 检查版本文件..."
if [ -f "VERSION" ]; then
    echo "   ✓ VERSION 文件存在"
    VERSION=$(cat VERSION | head -n1)
    echo "   当前版本: $VERSION"
else
    echo "   ✗ VERSION 文件不存在"
fi
echo ""

echo "2. 检查前端主页..."
if [ -f "frontend/index.html" ]; then
    echo "   ✓ frontend/index.html 存在"
    SIZE=$(wc -c < "frontend/index.html")
    echo "   文件大小: $SIZE 字节"
else
    echo "   ✗ frontend/index.html 不存在"
fi
echo ""

echo "3. 检查核心模块..."
MODULES=("core/system.py" "core/database.py" "core/session.py" "core/encryption.py")
for module in "${MODULES[@]}"; do
    if [ -f "$module" ]; then
        echo "   ✓ $module 存在"
    else
        echo "   ✗ $module 不存在"
    fi
done
echo ""

echo "4. 检查AI引擎..."
if [ -d "flask-app/ai_engines" ]; then
    echo "   ✓ AI引擎目录存在"
    ENGINES=$(find flask-app/ai_engines -name "*_engine.py" | wc -l)
    echo "   AI引擎数量: $ENGINES"
else
    echo "   ✗ AI引擎目录不存在"
fi
echo ""

echo "5. 检查优化报告..."
if [ -f "OPTIMIZATION_REPORT.json" ]; then
    echo "   ✓ 优化报告已生成"
    SIZE=$(wc -c < "OPTIMIZATION_REPORT.json")
    echo "   报告大小: $SIZE 字节"
else
    echo "   ✗ 优化报告未生成"
fi
echo ""

echo "6. HTTP服务器状态..."
if curl -s http://localhost:8888 > /dev/null 2>&1; then
    echo "   ✓ HTTP服务器运行中 (端口 8888)"
else
    echo "   ✗ HTTP服务器未运行"
fi
echo ""

echo "7. API服务器状态..."
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo "   ✓ API服务器运行中 (端口 5000)"
else
    echo "   ✗ API服务器未运行"
fi
echo ""

echo "========================================="
echo "验证完成"
echo "========================================="
