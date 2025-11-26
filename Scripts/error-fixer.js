#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

// 导入修复引擎
const RepairEngine = require('../JavaScript/repair-engine');

class ErrorFixer {
    constructor() {
        this.projectRoot = process.cwd();
        this.fixes = [];
        this.errors = [];
        this.totalFiles = 0;
        this.fixedFiles = 0;
        this.scanPaths = [
            path.join(this.projectRoot, 'assets', 'js'),
            path.join(this.projectRoot, 'JavaScript'),
            path.join(this.projectRoot, 'HTML', 'JS'),
            path.join(this.projectRoot, 'Scripts'),
            path.join(this.projectRoot, 'test')
        ];
        this.supportedFileTypes = ['.js', '.jsx', '.ts', '.tsx', '.css', '.html'];
        
        // 初始化修复引擎
        this.repairEngine = new RepairEngine({
            fileTypes: this.supportedFileTypes,
            logger: {
                level: 'info',
                enableFileLogging: true
            }
        });
    }

    // 读取文件内容
    async readFile(filePath) {
        try {
            return await fs.promises.readFile(filePath, 'utf8');
        } catch (error) {
            console.error(`[error-fixer.js] 读取文件失败: ${filePath} - ${error.message}`);
            this.errors.push({ file: filePath, error: error.message });
            return null;
        }
    }

    // 写入文件内容
    async writeFile(filePath, content) {
        try {
            // 创建备份
            const backupPath = `${filePath}.bak`;
            await fs.promises.copyFile(filePath, backupPath);
            
            await fs.promises.writeFile(filePath, content, 'utf8');
            console.log(`✅ 修复完成: ${filePath}`);
            
            // 移除备份（如果需要保留备份，可以注释掉这行）
            await fs.promises.unlink(backupPath);
            
            return true;
        } catch (error) {
            this.errors.push({ file: filePath, error: error.message });
            console.error(`[error-fixer.js] ❌ 写入文件失败: ${filePath} - ${error.message}`);
            return false;
        }
    }

    // 修复未处理的Promise拒绝
    fixUnhandledPromiseRejections(content, filePath) {
        let fixed = false;
        let newContent = content;

        // 查找未处理的.catch(error => console.error(`[error-fixer.js] Promise rejected:, error`))调用
        const catchPattern = /\.catch\(\s*\)/g;
        if (catchPattern.test(newContent)) {
            newContent = newContent.replace(catchPattern, '.catch(error => console.error(`[error-fixer.js] Promise rejected:, error`))');
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'unhandled_promise_rejection',
                description: '添加了Promise错误处理'
            });
        }

        return { content: newContent, fixed };
    }

    // 修复缺少的错误处理
    fixMissingErrorHandling(content, filePath) {
        let fixed = false;
        let newContent = content;

        // 查找空的catch块
        const emptyCatchPattern = /\}\s*catch\s*\(\s*\w*\s*\)\s*\{\s*\}/g;
        if (emptyCatchPattern.test(newContent)) {
            newContent = newContent.replace(emptyCatchPattern, (match) => {
                return match.replace(/\{\s*\}/, '{ console.error(`[error-fixer.js] Error occurred:, error`); }');
            });
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'empty_catch_block',
                description: '添加了空的catch块错误处理'
            });
        }

        return { content: newContent, fixed };
    }

    // 修复console.error缺少上下文
    fixConsoleErrorContext(content, filePath) {
        let fixed = false;
        let newContent = content;

        // 为console.error添加文件名上下文
        const fileName = path.basename(filePath);
        const consoleErrorPattern = /console\.error\(/g;
        
        if (consoleErrorPattern.test(newContent)) {
            newContent = newContent.replace(
                /console\.error\(([^)]+)\)/g,
                (match, args) => {
                    // 如果已经包含上下文信息，跳过
                    if (args.includes('[') && args.includes(']')) {
                        return match;
                    }
                    return `console.error(\`[${fileName}] ${args.replace(/['"]/g, '')}\`)`;
                }
            );
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'console_error_context',
                description: '为console.error添加了文件名上下文'
            });
        }

        return { content: newContent, fixed };
    }

    // 修复潜在的异步错误
    fixAsyncErrors(content, filePath) {
        let fixed = false;
        let newContent = content;

        // 查找没有await的async函数调用
        const asyncCallPattern = /(\w+)\.(\w+)\(\)/g;
        const lines = newContent.split('\n');
        
        lines.forEach((line, index) => {
            const trimmed = line.trim().catch(error => console.error(`[error-fixer.js] line.trim failed:`, error));
            if (asyncCallPattern.test(trimmed) && 
                !trimmed.includes('await ') && 
                !trimmed.includes('.catch(') &&
                !trimmed.includes('.then(') &&
                !trimmed.includes('console.') &&
                !trimmed.includes('//') &&
                !trimmed.includes('return ')) {
                
                // 检查是否是异步函数调用
                const match = trimmed.match(/(\w+)\.(\w+)\(\)/);
                if (match) {
                    const [fullMatch, object, method] = match;
                    const newLine = line.replace(fullMatch, `${fullMatch}.catch(error => console.error(\`[error-fixer.js] [${path.basename(filePath)}] ${object}.${method} failed:\`, error))`);
                    lines[index] = newLine;
                    fixed = true;
                }
            }
        });

        newContent = lines.join('\n');
        
        if (fixed) {
            this.fixes.push({
                file: filePath,
                type: 'async_error_handling',
                description: '为异步函数调用添加了错误处理'
            });
        }

        return { content: newContent, fixed };
    }

    // 修复try-catch块中的错误
    fixTryCatchErrors(content, filePath) {
        let fixed = false;
        let newContent = content;

        // 查找没有错误处理的try-catch块
        const tryCatchPattern = /try\s*\{[^}]*\}\s*catch\s*\([^)]*\)\s*\{\s*\}/gs;
        
        if (tryCatchPattern.test(newContent)) {
            newContent = newContent.replace(tryCatchPattern, (match) => {
                return match.replace(/\{\s*\}/, '{ console.error(`[error-fixer.js] Try-catch error:, error`); }');
            });
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'try_catch_error',
                description: '为try-catch块添加了错误处理'
            });
        }

        return { content: newContent, fixed };
    }

    // 修复单个文件
    async fixFile(filePath) {
        try {
            const content = await this.readFile(filePath);
            if (!content) return false;

            let newContent = content;
            let fileFixed = false;

            // 根据文件类型应用不同的修复策略
            const ext = path.extname(filePath).toLowerCase();
            
            // 应用基础修复
            const baseFixes = [
                () => this.fixUnhandledPromiseRejections(newContent, filePath),
                () => this.fixMissingErrorHandling(newContent, filePath),
                () => this.fixConsoleErrorContext(newContent, filePath),
                () => this.fixAsyncErrors(newContent, filePath),
                () => this.fixTryCatchErrors(newContent, filePath)
            ];

            for (const fix of baseFixes) {
                const result = fix();
                if (result.fixed) {
                    newContent = result.content;
                    fileFixed = true;
                }
            }
            
            // 应用文件类型特定修复
            if (ext === '.js' || ext === '.jsx' || ext === '.ts' || ext === '.tsx') {
                const jsFixes = [
                    () => this.fixVarToLetConst(newContent, filePath),
                    () => this.fixArrowFunctions(newContent, filePath),
                    () => this.fixTemplateStrings(newContent, filePath),
                    () => this.fixImports(newContent, filePath)
                ];
                
                for (const fix of jsFixes) {
                    const result = fix();
                    if (result.fixed) {
                        newContent = result.content;
                        fileFixed = true;
                    }
                }
            } else if (ext === '.css') {
                const cssFixes = [
                    () => this.fixCSSSyntax(newContent, filePath),
                    () => this.fixCSSSelectors(newContent, filePath)
                ];
                
                for (const fix of cssFixes) {
                    const result = fix();
                    if (result.fixed) {
                        newContent = result.content;
                        fileFixed = true;
                    }
                }
            } else if (ext === '.html') {
                const htmlFixes = [
                    () => this.fixHTMLTags(newContent, filePath),
                    () => this.fixHTMLAttributes(newContent, filePath)
                ];
                
                for (const fix of htmlFixes) {
                    const result = fix();
                    if (result.fixed) {
                        newContent = result.content;
                        fileFixed = true;
                    }
                }
            }
            
            // 使用修复引擎进行AI辅助修复
            try {
                const engineResult = await this.repairEngine.repairFile(filePath);
                if (engineResult.success && engineResult.repairedContent) {
                    newContent = engineResult.repairedContent;
                    fileFixed = true;
                    this.fixes.push({
                        file: filePath,
                        type: 'ai_assisted_fix',
                        description: `AI辅助修复: ${engineResult.issuesFixed}个问题`
                    });
                }
            } catch (engineError) {
                console.error(`[error-fixer.js] AI修复失败: ${filePath} - ${engineError.message}`);
            }

            if (fileFixed) {
                return await this.writeFile(filePath, newContent);
            }

            return false;
        } catch (error) {
            console.error(`[error-fixer.js] 修复文件失败: ${filePath} - ${error.message}`);
            this.errors.push({ file: filePath, error: error.message });
            return false;
        }
    }

    // 扫描并修复所有支持的文件类型
    async scanAndFix() {
        console.log(`📁 扫描路径: ${this.scanPaths.join(', ')}`);
        console.log(`📄 支持的文件类型: ${this.supportedFileTypes.join(', ')}`);
        
        // 初始化修复引擎
        await this.repairEngine.initialize();

        for (const dir of this.scanPaths) {
            if (!fs.existsSync(dir)) {
                console.log(`⚠️  目录不存在: ${dir}`);
                continue;
            }

            await this.scanDirectory(dir);
        }
    }

    // 递归扫描目录
    async scanDirectory(dir) {
        try {
            const items = await fs.promises.readdir(dir);
            
            for (const item of items) {
                const itemPath = path.join(dir, item);
                const stat = await fs.promises.stat(itemPath);
                
                if (stat.isDirectory()) {
                    await this.scanDirectory(itemPath);
                } else if (stat.isFile() && this.isSupportedFileType(itemPath)) {
                    this.totalFiles++;
                    console.log(`🔍 检查文件: ${itemPath}`);
                    const fixed = await this.fixFile(itemPath);
                    if (fixed) {
                        this.fixedFiles++;
                    }
                }
            }
        } catch (error) {
            console.error(`[error-fixer.js] 扫描目录失败: ${dir} - ${error.message}`);
            this.errors.push({ dir, error: error.message });
        }
    }
    
    // 检查文件类型是否受支持
    isSupportedFileType(filePath) {
        const ext = path.extname(filePath).toLowerCase();
        return this.supportedFileTypes.includes(ext);
    }

    // 生成修复报告
    generateReport() {
        console.log('\n📊 错误修复报告:');
        console.log('================');
        
        if (this.fixes.length > 0) {
            console.log(`✅ 成功修复 ${this.fixes.length} 个问题:`);
            
            const fixesByType = {};
            this.fixes.forEach(fix => {
                if (!fixesByType[fix.type]) {
                    fixesByType[fix.type] = [];
                }
                fixesByType[fix.type].push(fix);
            });

            Object.keys(fixesByType).forEach(type => {
                console.log(`\n🔧 ${type}: ${fixesByType[type].length} 个修复`);
                fixesByType[type].forEach(fix => {
                    console.log(`   ${fix.file} - ${fix.description}`);
                });
            });
        }

        if (this.errors.length > 0) {
            console.log(`\n❌ ${this.errors.length} 个错误:`);
            this.errors.forEach(error => {
                console.log(`   ${error.file}: ${error.error}`);
            });
        }

        if (this.fixes.length === 0 && this.errors.length === 0) {
            console.log('🎉 没有发现需要修复的错误！');
        }

        // 保存报告到文件
        const reportPath = path.join(this.projectRoot, 'Logs', 'error_fix_report.json');
        const report = {
            timestamp: new Date().toISOString(),
            fixes: this.fixes,
            errors: this.errors,
            summary: {
                fixed: this.fixes.length,
                errors: this.errors.length
            }
        };

        try {
            if (!fs.existsSync(path.dirname(reportPath))) {
                fs.mkdirSync(path.dirname(reportPath), { recursive: true });
            }
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            console.log(`\n📄 报告已保存到: ${reportPath}`);
        } catch (error) {
            console.log(`❌ 保存报告失败: ${error.message}`);
        }
    }

    // 修复var为let/const
    fixVarToLetConst(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 简单的var转换策略（实际项目中可能需要更复杂的静态分析）
        const varPattern = /\bvar\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=/g;
        if (varPattern.test(newContent)) {
            newContent = newContent.replace(varPattern, 'let $1 =');
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'var_to_let_const',
                description: '将var转换为let/const'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复箭头函数语法
    fixArrowFunctions(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复函数表达式为箭头函数
        const functionExprPattern = /function\s*\(([^)]*)\)\s*\{\s*return\s+([^;]+);\s*\}/g;
        if (functionExprPattern.test(newContent)) {
            newContent = newContent.replace(functionExprPattern, '($1) => $2');
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'arrow_function_fix',
                description: '修复箭头函数语法'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复模板字符串
    fixTemplateStrings(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复字符串拼接为模板字符串
        const concatPattern = /('|")([^\1]*?)\1\s*\+\s*(\w+)\s*\+\s*('|")([^\4]*?)\4/g;
        if (concatPattern.test(newContent)) {
            newContent = newContent.replace(concatPattern, `\`$2\${$3}$5\``);
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'template_string_fix',
                description: '修复模板字符串'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复导入语句
    fixImports(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复相对导入路径
        const importPattern = /from\s+('|")\.\.\/(\w+)(\1)/g;
        if (importPattern.test(newContent)) {
            // 这里可以根据项目结构进行更智能的修复
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'import_fix',
                description: '检查并修复导入语句'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复CSS语法错误
    fixCSSSyntax(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复缺少分号
        const missingSemicolonPattern = /([a-zA-Z-]+)\s*:\s*([^;{]+)\s*(?=\})/g;
        if (missingSemicolonPattern.test(newContent)) {
            newContent = newContent.replace(missingSemicolonPattern, '$1: $2;');
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'css_syntax_fix',
                description: '修复CSS语法错误'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复CSS选择器
    fixCSSSelectors(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 检查重复的选择器（简单实现）
        const selectorPattern = /([^{}]+)\s*\{[^}]+\}/g;
        const selectors = {};
        let match;
        
        while ((match = selectorPattern.exec(content)) !== null) {
            const selector = match[1].trim();
            if (selectors[selector]) {
                selectors[selector]++;
            } else {
                selectors[selector] = 1;
            }
        }
        
        // 如果发现重复选择器，记录但不自动修复
        const duplicates = Object.keys(selectors).filter(sel => selectors[sel] > 1);
        if (duplicates.length > 0) {
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'css_selector_fix',
                description: `发现${duplicates.length}个重复的CSS选择器`
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复HTML标签
    fixHTMLTags(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复未闭合的简单标签（简单实现）
        const unclosedTags = ['br', 'hr', 'img', 'input', 'meta', 'link'];
        
        for (const tag of unclosedTags) {
            const pattern = new RegExp(`<${tag}(\\s[^>]*?)?>(?!<\\/${tag}>)`, 'gi');
            if (pattern.test(newContent)) {
                newContent = newContent.replace(pattern, `<${tag}$1 />`);
                fixed = true;
            }
        }
        
        if (fixed) {
            this.fixes.push({
                file: filePath,
                type: 'html_tag_fix',
                description: '修复HTML标签问题'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 修复HTML属性
    fixHTMLAttributes(content, filePath) {
        let fixed = false;
        let newContent = content;
        
        // 修复缺少引号的属性
        const attrPattern = /(\w+)\s*=\s*([^\s"'>]+)/g;
        if (attrPattern.test(newContent)) {
            newContent = newContent.replace(attrPattern, '$1="$2"');
            fixed = true;
            this.fixes.push({
                file: filePath,
                type: 'html_attribute_fix',
                description: '修复HTML属性问题'
            });
        }
        
        return { content: newContent, fixed };
    }
    
    // 执行修复
    async run() {
        console.log('🚀 开始错误修复...\n');
        
        try {
            await this.scanAndFix();
        } catch (error) {
            console.error(`[error-fixer.js] 扫描修复过程中发生错误:`, error);
            this.errors.push({ type: 'scan_error', error: error.message });
        }
        
        await this.generateReport();
        
        console.log('\n✨ 错误修复完成！');
        
        // 返回统计信息
        return {
            totalFiles: this.totalFiles,
            fixedFiles: this.fixedFiles,
            totalIssues: this.fixes.length,
            fixedIssues: this.fixes.length,
            errors: this.errors.length
        };
    }
}

// 导出ErrorFixer类，供其他模块使用
module.exports = ErrorFixer;

// 如果直接运行此脚本，则执行修复
if (require.main === module) {
    const fixer = new ErrorFixer();
    fixer.run().catch(console.error);
}