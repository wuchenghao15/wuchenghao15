@echo off
REM ViKey Native Module Installation Script for Windows
REM 用于安装和构建基于官方ViKey库的Node.js原生扩展

echo ==========================================
echo ViKey Native Module Installation Script
echo ==========================================

REM 获取脚本目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set VIKEY_DIR=%PROJECT_ROOT%\JavaScript\vikey-native

echo 项目根目录: %PROJECT_ROOT%
echo ViKey模块目录: %VIKEY_DIR%

REM 检查ViKey目录是否存在
if not exist "%VIKEY_DIR%" (
    echo 错误: ViKey模块目录不存在: %VIKEY_DIR%
    pause
    exit /b 1
)

REM 进入ViKey模块目录
cd /d "%VIKEY_DIR%"

REM 检查package.json是否存在
if not exist "package.json" (
    echo 错误: package.json文件不存在
    pause
    exit /b 1
)

REM 检查binding.gyp是否存在
if not exist "binding.gyp" (
    echo 错误: binding.gyp文件不存在
    pause
    exit /b 1
)

REM 检查源文件是否存在
if not exist "src\vikey_native.cpp" (
    echo 错误: C++源文件不存在
    pause
    exit /b 1
)

echo.
echo 步骤1: 检查Node.js和npm...
node --version
npm --version

if %errorlevel% neq 0 (
    echo 错误: Node.js或npm未正确安装
    pause
    exit /b 1
)

echo.
echo 步骤2: 安装依赖包...
call npm install

if %errorlevel% neq 0 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 步骤3: 检查ViKey官方库文件...

REM 检查ViKey官方库文件是否存在
set VIKEY_LIB_DIR=%PROJECT_ROOT%\ViKey
if not exist "%VIKEY_LIB_DIR%" (
    echo 警告: ViKey官方库目录不存在: %VIKEY_LIB_DIR%
    echo 请确保以下文件存在于ViKey目录中:
    echo   - vikey.h ^(头文件^)
    echo   - vikey.lib ^(库文件^)
    echo   - vikey.dll ^(动态链接库^)
    echo.
    echo 继续构建，但可能需要手动配置库文件路径...
) else (
    echo ViKey库目录: %VIKEY_LIB_DIR%
    
    if exist "%VIKEY_LIB_DIR%\vikey.h" (
        echo ✓ 找到 vikey.h
    ) else (
        echo ✗ 缺少 vikey.h
    )
    
    if exist "%VIKEY_LIB_DIR%\vikey.lib" (
        echo ✓ 找到 vikey.lib
    ) else (
        echo ✗ 缺少 vikey.lib
    )
    
    if exist "%VIKEY_LIB_DIR%\vikey.dll" (
        echo ✓ 找到 vikey.dll
    ) else (
        echo ✗ 缺少 vikey.dll
    )
)

echo.
echo 步骤4: 构建原生模块...

REM 检查是否安装了Visual Studio Build Tools
where msbuild >nul 2>nul
if %errorlevel% neq 0 (
    echo 警告: 未找到MSBuild，可能缺少Visual Studio Build Tools
    echo 请安装Visual Studio Build Tools或Visual Studio
    echo.
)

REM 使用node-gyp构建
echo 开始构建ViKey原生模块...
call npx node-gyp rebuild

if %errorlevel% equ 0 (
    echo.
    echo ✓ ViKey原生模块构建成功!
    echo 生成的文件位置:
    if exist "build\Release\vikey_native.node" (
        echo ✓ build\Release\vikey_native.node
    ) else (
        echo ✗ 未找到vikey_native.node文件
    )
    
) else (
    echo.
    echo ✗ ViKey原生模块构建失败
    echo 请检查以下内容:
    echo 1. 是否安装了Visual Studio Build Tools
    echo 2. 是否安装了Python 2.7或3.x
    echo 3. ViKey官方库文件是否正确放置
    echo 4. binding.gyp配置是否正确
    echo 5. 环境变量PATH是否包含必要的工具
    echo.
    echo 尝试显示详细错误信息...
    call npx node-gyp rebuild --verbose
    pause
    exit /b 1
)

echo.
echo 步骤5: 运行测试...

REM 检查是否有测试文件
if exist "test.js" (
    echo 运行测试脚本...
    node test.js
    
    if %errorlevel% equ 0 (
        echo ✓ 测试通过
    ) else (
        echo ✗ 测试失败，但这可能是由于缺少ViKey设备导致的
    )
) else (
    echo 未找到测试文件
)

echo.
echo ==========================================
echo 安装脚本执行完成
echo ==========================================

REM 显示使用说明
echo.
echo 使用说明:
echo 1. 确保ViKey官方库文件^(vikey.h, vikey.lib, vikey.dll^)已正确放置
echo 2. 原生模块已成功构建并可以使用
echo 3. WebSocket服务器会自动检测并使用原生模块
echo 4. 如果原生模块不可用，服务器将回退到模拟模式
echo.

REM 显示文件结构
echo 当前文件结构:
dir /b /s *.js *.cpp *.json *.gyp 2>nul

echo.
echo 安装完成!
echo.
pause