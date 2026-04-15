/**
 * 自动修复路径引用脚本
 * 无需用户交互，自动修复项目中的路径引用问题
 */

const fs = require('fs');
const path = require('path');
const { getAIAutoFixInstance } = require('../src/core/ai/ai-auto-fix');

class AutoPathFixer {
    constructor() {
        this.aiAutoFix = getAIAutoFixInstance();
        this.logger = {
            info: (...args) => console.log('[AutoPathFixer] INFO:', ...args),
            warn: (...args) => console.warn('[AutoPathFixer] WARN:', ...args),
            error: (...args) => console.error('[AutoPathFixer] ERROR:', ...args)
        };
        this.supportedFileTypes = ['.js', '.html'];
        this.issuesFixed = 0;
        this.filesFixed = 0;
    }
    
    /**
     * 修复单个文件中的路径问题
     * @param {string} filePath - 文件路径
     */
    async fixFile(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            let fixedContent = content;
            let issuesInFile = 0;
            
            // 修复HTML目录大小写问题
            if (fixedContent.includes('../HTML/') || fixedContent.includes('./HTML/') || fixedContent.includes('/HTML/')) {
                fixedContent = fixedContent.replace(/\.\.\/HTML\//g, '../html/')
                                         .replace(/\.\/HTML\//g, './html/')
                                         .replace(/\/HTML\//g, '/html/');
                issuesInFile++;
            }
            
            // 修复Configs目录大小写问题
            if (fixedContent.includes('../Configs/') || fixedContent.includes('./Configs/') || fixedContent.includes('/Configs/')) {
                fixedContent = fixedContent.replace(/\.\.\/Configs\//g, '../config/')
                                         .replace(/\.\/Configs\//g, './config/')
                                         .replace(/\/Configs\//g, '/config/');
                issuesInFile++;
            }
            
            // 修复Javascript目录大小写问题
            if (fixedContent.includes('../Javascript/') || fixedContent.includes('./Javascript/') || fixedContent.includes('/Javascript/')) {
                fixedContent = fixedContent.replace(/\.\.\/Javascript\//g, '../javascript/')
                                         .replace(/\.\/Javascript\//g, './javascript/')
                                         .replace(/\/Javascript\//g, '/javascript/');
                issuesInFile++;
            }
            
            // 修复字符串拼接路径问题
            const stringConcatPattern = /__dirname\s*\+\s*['"]([^'"]+)['"]/g;
            let match;
            const concatMatches = [...fixedContent.matchAll(stringConcatPattern)];
            if (concatMatches.length > 0) {
                for (const m of concatMatches) {
                    const fullMatch = m[0];
                    const pathPart = m[1];
                    const fixedPath = `path.join(__dirname, '${pathPart}')`;
                    fixedContent = fixedContent.replace(fullMatch, fixedPath);
                    issuesInFile++;
                }
            }
            
            // 修复不存在的local-deepseek-model引用
            if (fixedContent.includes('local-deepseek-model')) {
                const localModelPattern = /require\(['"]([^'"]*?local-deepseek-model[^'"]*?)['"]\)/g;
                fixedContent = fixedContent.replace(localModelPattern, '// const LocalDeepSeekModel = require(\'$1\'); // 暂时移除，文件不存在');
                issuesInFile++;
            }
            
            // 如果有修复，保存文件
            if (issuesInFile > 0) {
                fs.writeFileSync(filePath, fixedContent, 'utf8');
                this.filesFixed++;
                this.issuesFixed += issuesInFile;
                this.logger.info(`成功修复文件: ${filePath}，修复了 ${issuesInFile} 个问题`);
            }
        } catch (error) {
            this.logger.error(`修复文件 ${filePath} 时出错:`, error);
        }
    }
    
    /**
     * 修复目录中的所有文件
     * @param {string} dirPath - 目录路径
     */
    async fixDirectory(dirPath) {
        this.logger.info(`开始修复目录: ${dirPath}`);
        
        const files = fs.readdirSync(dirPath);
        
        for (const file of files) {
            const filePath = path.join(dirPath, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                // 跳过node_modules和.git目录
                if (file === 'node_modules' || file === '.git' || file === 'node_modules' || file === 'Logs' || file === 'storage') {
                    continue;
                }
                await this.fixDirectory(filePath);
            } else {
                // 检查文件类型
                const ext = path.extname(file);
                if (this.supportedFileTypes.includes(ext)) {
                    await this.fixFile(filePath);
                }
            }
        }
    }
    
    /**
     * 使用AI修复复杂路径问题
     * @param {string} filePath - 文件路径
     */
    async aiFixComplexPathIssues(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            
            // 检查是否有复杂路径问题
            if (content.includes('../../../deploy-package/')) {
                this.logger.info(`使用AI修复复杂路径问题: ${filePath}`);
                
                const aiResult = await this.aiAutoFix.fixSpecificIssue(
                    '修复跨目录引用问题，不应直接引用deploy-package目录下的文件',
                    content,
                    { taskType: 'code' }
                );
                
                // 处理AI返回结果，确保是字符串
                const fixedContent = typeof aiResult === 'object' && aiResult.response ? aiResult.response : aiResult;
                
                if (fixedContent && typeof fixedContent === 'string' && fixedContent !== content) {
                    fs.writeFileSync(filePath, fixedContent, 'utf8');
                    this.filesFixed++;
                    this.issuesFixed++;
                    this.logger.info(`AI成功修复复杂路径问题: ${filePath}`);
                }
            }
        } catch (error) {
            this.logger.error(`AI修复文件 ${filePath} 时出错:`, error);
        }
    }
    
    /**
     * 执行修复
     */
    async execute() {
        const startTime = Date.now();
        this.logger.info('开始自动修复路径引用问题...');
        
        // 修复src目录
        await this.fixDirectory(path.join(__dirname, '..', 'src'));
        
        // 修复deploy-package目录
        await this.fixDirectory(path.join(__dirname, '..', 'deploy-package'));
        
        // 使用AI修复复杂路径问题
        const complexFiles = [
            path.join(__dirname, '..', 'src/core/ai/ai-auto-fix.js')
        ];
        
        for (const file of complexFiles) {
            await this.aiFixComplexPathIssues(file);
        }
        
        const endTime = Date.now();
        const duration = (endTime - startTime) / 1000;
        
        this.logger.info(`\n修复完成！`);
        this.logger.info(`修复文件数: ${this.filesFixed}`);
        this.logger.info(`修复问题数: ${this.issuesFixed}`);
        this.logger.info(`耗时: ${duration.toFixed(2)} 秒`);
        this.logger.info('路径引用修复完成！');
    }
}

// 执行修复
const autoPathFixer = new AutoPathFixer();
autoPathFixer.execute().catch(error => {
    console.error('自动修复失败:', error);
    process.exit(1);
});
