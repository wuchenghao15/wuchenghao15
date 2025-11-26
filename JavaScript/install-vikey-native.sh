#!/bin/bash

# HardwareKey Native Module Installation Script
# 用于安装和构建基于官方HardwareKey库的Node.js原生扩展

echo "=========================================="
echo "HardwareKey Native Module Installation Script"
echo "=========================================="

# 检查当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VIKEY_DIR="$PROJECT_ROOT/JavaScript/hardwareKey-native"

echo "项目根目录: $PROJECT_ROOT"
echo "HardwareKey模块目录: $VIKEY_DIR"

# 检查HardwareKey目录是否存在
if [ ! -d "$VIKEY_DIR" ]; then
    echo "错误: HardwareKey模块目录不存在: $VIKEY_DIR"
    exit 1
fi

# 进入HardwareKey模块目录
cd "$VIKEY_DIR"

# 检查package.json是否存在
if [ ! -f "package.json" ]; then
    echo "错误: package.json文件不存在"
    exit 1
fi

# 检查binding.gyp是否存在
if [ ! -f "binding.gyp" ]; then
    echo "错误: binding.gyp文件不存在"
    exit 1
fi

# 检查源文件是否存在
if [ ! -f "src/hardwareKey_native.cpp" ]; then
    echo "错误: C++源文件不存在"
    exit 1
fi

echo ""
echo "步骤1: 检查Node.js和npm..."
node --version
npm --version

if [ $? -ne 0 ]; then
    echo "错误: Node.js或npm未正确安装"
    exit 1
fi

echo ""
echo "步骤2: 安装依赖包..."
npm install

if [ $? -ne 0 ]; then
    echo "错误: 依赖包安装失败"
    exit 1
fi

echo ""
echo "步骤3: 检查HardwareKey官方库文件..."

# 检查HardwareKey官方库文件是否存在
VIKEY_LIB_DIR="$PROJECT_ROOT/HardwareKey"
if [ ! -d "$VIKEY_LIB_DIR" ]; then
    echo "警告: HardwareKey官方库目录不存在: $VIKEY_LIB_DIR"
    echo "请确保以下文件存在于HardwareKey目录中:"
    echo "  - hardwareKey.h (头文件)"
    echo "  - hardwareKey.lib (库文件)"
    echo "  - hardwareKey.dll (动态链接库)"
    echo ""
    echo "继续构建，但可能需要在Windows环境下进行编译..."
else
    echo "HardwareKey库目录: $VIKEY_LIB_DIR"
    
    if [ -f "$VIKEY_LIB_DIR/hardwareKey.h" ]; then
        echo "✓ 找到 hardwareKey.h"
    else
        echo "✗ 缺少 hardwareKey.h"
    fi
    
    if [ -f "$VIKEY_LIB_DIR/hardwareKey.lib" ]; then
        echo "✓ 找到 hardwareKey.lib"
    else
        echo "✗ 缺少 hardwareKey.lib"
    fi
    
    if [ -f "$VIKEY_LIB_DIR/hardwareKey.dll" ]; then
        echo "✓ 找到 hardwareKey.dll"
    else
        echo "✗ 缺少 hardwareKey.dll"
    fi
fi

echo ""
echo "步骤4: 构建原生模块..."

# 检查是否为Windows环境
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "检测到Windows环境，开始构建..."
    
    # 使用node-gyp构建
    npx node-gyp rebuild
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ HardwareKey原生模块构建成功!"
        echo "生成的文件位置:"
        ls -la build/Release/hardwareKey_native.node 2>/dev/null || echo "未找到hardwareKey_native.node文件"
        
    else
        echo ""
        echo "✗ HardwareKey原生模块构建失败"
        echo "请检查以下内容:"
        echo "1. 是否安装了Visual Studio Build Tools"
        echo "2. 是否安装了Python 2.7或3.x"
        echo "3. HardwareKey官方库文件是否正确放置"
        echo "4. binding.gyp配置是否正确"
        exit 1
    fi
    
else
    echo "当前环境: $OSTYPE"
    echo "警告: HardwareKey原生模块需要在Windows环境下构建"
    echo "当前构建可能无法生成可用的模块"
    echo ""
    echo "尝试构建（用于语法检查）..."
    
    # 尝试构建（可能失败）
    npx node-gyp rebuild --verbose
    
    if [ $? -eq 0 ]; then
        echo "✓ 构建完成（但可能无法在非Windows环境运行）"
    else
        echo "✗ 构建失败，这在非Windows环境下是正常的"
        echo "请在Windows环境下重新运行此脚本"
    fi
fi

echo ""
echo "步骤5: 运行测试..."

# 检查是否有测试文件
if [ -f "test.js" ]; then
    echo "运行测试脚本..."
    node test.js
    
    if [ $? -eq 0 ]; then
        echo "✓ 测试通过"
    else
        echo "✗ 测试失败，但这可能是由于缺少HardwareKey设备导致的"
    fi
else
    echo "未找到测试文件"
fi

echo ""
echo "=========================================="
echo "安装脚本执行完成"
echo "=========================================="

# 显示使用说明
echo ""
echo "使用说明:"
echo "1. 确保HardwareKey官方库文件(hardwareKey.h, hardwareKey.lib, hardwareKey.dll)已正确放置"
echo "2. 在Windows环境下构建以获得完整的原生模块支持"
echo "3. WebSocket服务器会自动检测并使用原生模块（如果可用）"
echo "4. 如果原生模块不可用，服务器将回退到模拟模式"
echo ""

# 显示文件结构
echo "当前文件结构:"
tree -L 3 "$VIKEY_DIR" 2>/dev/null || find "$VIKEY_DIR" -type f -name "*.js" -o -name "*.cpp" -o -name "*.json" -o -name "*.gyp" | sort

echo ""
echo "安装完成!"