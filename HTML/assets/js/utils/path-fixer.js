#!/usr/bin/env node

/**
 * MTSCOS 路径修复工具
 * 自动更新所有HTML文件中的CSS和JS引用路径
 */

const fs = require('fs');
const path = require('path');

class PathFixer {
    constructor() {
        this.projectRoot = process.cwd();
        this.htmlDir = path.join(this.projectRoot, 'HTML');
        this.assetsDir = path.join(this.projectRoot, 'assets');
        this.backupDir = path.join(this.projectRoot, 'Backups', 'path_fix_backup');
        
        // 路径映射表
        this.pathMappings = {
            // CSS路径映射
            '../CSS/common_styles/': '/assets/css/common_styles/',
            '../CSS/page_styles/': '/assets/css/page_styles/',
            '../CSS/component_styles/': '/assets/css/component_styles/',
            '../CSS/other_styles/': '/assets/css/other_styles/',
            '../CSS/': '/assets/css/',
            '../CSS/': '/assets/css/',
            
            // JavaScript路径映射
            '../JavaScript/': '/assets/js/',
            '../Encrypted_JS/': '/assets/js/',
            '../JS/': '/assets/js/',
            '../JavaScript/': '/assets/js/',
            'Encrypted_JS/': '/assets/js/',
            'JS/': '/assets/js/',
            '../HTML/JS/': '/assets/js/',
            
            // HTML内嵌CSS路径
            '../HTML/css/': '/assets/css/',
        };
        
        // 文件扩展名映射
        this.extensionMappings = {
            '.css': '/assets/css/',
            '.js': '/assets/js/'
        };
    }
    
    // 创建备份
    createBackup() {
        if (!fs.existsSync(this.backupDir)) {
            fs.mkdirSync(this.backupDir, { recursive: true });
        }
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = path.join(this.backupDir, `backup_${timestamp}`);
        
        console.log(`📦 创建备份到: ${backupPath}`);
        this.copyDir(this.htmlDir, backupPath);
    }
    
    // 复制目录
    copyDir(src, dest) {
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }
        
        const entries = fs.readdirSync(src, { withFileTypes: true });
        
        for (const entry of entries) {
            const srcPath = path.join(src, entry.name);
            const destPath = path.join(dest, entry.name);
            
            if (entry.isDirectory()) {
                this.copyDir(srcPath, destPath);
            } else {
                fs.copyFileSync(srcPath, destPath);
            }
        }
    }
    
    // 获取所有HTML文件
    getHtmlFiles() {
        const htmlFiles = [];
        
        function scanDir(dir) {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    scanDir(fullPath);
                } else if (entry.name.endsWith('.html')) {
                    htmlFiles.push(fullPath);
                }
            }
        }
        
        if (fs.existsSync(this.htmlDir)) {
            scanDir(this.htmlDir);
        }
        
        return htmlFiles;
    }
    
    // 修复单个文件
    fixFile(filePath) {
        console.log(`🔧 修复文件: ${path.relative(this.projectRoot, filePath)}`);
        
        let content = fs.readFileSync(filePath, 'utf8');
        let modified = false;
        
        // 应用路径映射
        for (const [oldPath, newPath] of Object.entries(this.pathMappings)) {
            const regex = new RegExp(this.escapeRegex(oldPath), 'g');
            if (regex.test(content)) {
                content = content.replace(regex, newPath);
                modified = true;
                console.log(`  ✅ ${oldPath} → ${newPath}`);
            }
        }
        
        // 修复相对路径引用
        content = this.fixRelativePaths(content);
        
        // 修复HTML内嵌样式和脚本
        content = this.fixInlineResources(content);
        
        if (modified) {
            fs.writeFileSync(filePath, content, 'utf8');
            console.log(`  💾 文件已更新`);
        } else {
            console.log(`  ℹ️  无需修改`);
        }
        
        return modified;
    }
    
    // 修复相对路径
    fixRelativePaths(content) {
        // 修复href属性中的CSS路径
        content = content.replace(
            /href=["']\.\.\/[^"']*\.css["']/g,
            match => {
                const oldPath = match.match(/href=["']([^"']+)["']/)[1];
                const fileName = path.basename(oldPath);
                return `href="/assets/css/${fileName}"`;
            }
        );
        
        // 修复src属性中的JS路径
        content = content.replace(
            /src=["']\.\.\/[^"']*\.js["']/g,
            match => {
                const oldPath = match.match(/src=["']([^"']+)["']/)[1];
                const fileName = path.basename(oldPath);
                return `src="/assets/js/${fileName}"`;
            }
        );
        
        return content;
    }
    
    // 修复内嵌资源
    fixInlineResources(content) {
        // 修复内嵌CSS中的url()引用
        content = content.replace(
            /url\(["']?\.\.\/[^"')]*["']?\)/g,
            match => {
                const innerPath = match.match(/url\(["']?([^"')]*?)["']?\)/)[1];
                if (innerPath.includes('.css') || innerPath.includes('.js')) {
                    const fileName = path.basename(innerPath);
                    if (innerPath.endsWith('.css')) {
                        return `url("/assets/css/${fileName}")`;
                    } else if (innerPath.endsWith('.js')) {
                        return `url("/assets/js/${fileName}")`;
                    }
                }
                return match;
            }
        );
        
        return content;
    }
    
    // 转义正则表达式特殊字符
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    // 生成资源映射报告
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            fixedFiles: [],
            pathMappings: this.pathMappings,
            totalFiles: 0,
            modifiedFiles: 0
        };
        
        const htmlFiles = this.getHtmlFiles();
        report.totalFiles = htmlFiles.length;
        
        for (const filePath of htmlFiles) {
            const relativePath = path.relative(this.projectRoot, filePath);
            const content = fs.readFileSync(filePath, 'utf8');
            
            // 检查是否包含需要修复的路径
            let needsFix = false;
            for (const oldPath of Object.keys(this.pathMappings)) {
                if (content.includes(oldPath)) {
                    needsFix = true;
                    break;
                }
            }
            
            if (needsFix) {
                report.fixedFiles.push(relativePath);
                report.modifiedFiles++;
            }
        }
        
        const reportPath = path.join(this.projectRoot, 'Reports', 'path_fix_report.json');
        if (!fs.existsSync(path.dirname(reportPath))) {
            fs.mkdirSync(path.dirname(reportPath), { recursive: true });
        }
        
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
        console.log(`📊 报告已生成: ${reportPath}`);
        
        return report;
    }
    
    // 执行修复
    async run() {
        console.log('🚀 开始MTSCOS路径修复...\n');
        
        // 创建备份
        this.createBackup();
        
        // 生成报告
        const report = this.generateReport();
        
        // 获取所有HTML文件
        const htmlFiles = this.getHtmlFiles();
        console.log(`\n📄 找到 ${htmlFiles.length} 个HTML文件\n`);
        
        // 修复每个文件
        let modifiedCount = 0;
        for (const filePath of htmlFiles) {
            if (this.fixFile(filePath)) {
                modifiedCount++;
            }
        }
        
        console.log(`\n✨ 路径修复完成！`);
        console.log(`📊 总文件数: ${htmlFiles.length}`);
        console.log(`🔧 修改文件数: ${modifiedCount}`);
        console.log(`📦 备份位置: ${this.backupDir}`);
        
        return report;
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    const fixer = new PathFixer();
    fixer.run().catch(console.error);
}

module.exports = PathFixer;