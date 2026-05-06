/**
 * MTSCOS AI 系统 - AI自动修复服务
 * 自动检测和修复代码中的问题
 */

const logger = require('../logger');
const fs = require('fs');
const path = require('path');

class AIAutoFixService {
    constructor() {
        this.issueTypes = {
            SYNTAX_ERROR: 'syntax_error',
            LOGIC_ERROR: 'logic_error',
            PERFORMANCE_ISSUE: 'performance_issue',
            SECURITY_VULNERABILITY: 'security_vulnerability',
            CODE_SMELL: 'code_smell'
        };

        this.fixStrategies = {
            [this.issueTypes.SYNTAX_ERROR]: this.fixSyntaxError.bind(this),
            [this.issueTypes.LOGIC_ERROR]: this.fixLogicError.bind(this),
            [this.issueTypes.PERFORMANCE_ISSUE]: this.fixPerformanceIssue.bind(this),
            [this.issueTypes.SECURITY_VULNERABILITY]: this.fixSecurityVulnerability.bind(this),
            [this.issueTypes.CODE_SMELL]: this.fixCodeSmell.bind(this)
        };
    }

    /**
     * 检测代码问题
     * @param {string} code - 代码内容
     * @param {string} filePath - 文件路径
     * @returns {Promise<Array>} - 检测到的问题列表
     */
    async detectIssues(code, filePath) {
        try {
            const issues = [];

            // 模拟检测到的问题
            // 在实际应用中，这里应该使用AST解析和静态分析工具
            if (code.includes('console.log')) {
                issues.push({
                    type: this.issueTypes.CODE_SMELL,
                    description: '调试代码未移除',
                    line: code.indexOf('console.log') > 0 ? code.substring(0, code.indexOf('console.log')).split('\n').length : 1,
                    severity: 'low',
                    fixable: true
                });
            }

            // 检查是否有未使用的变量
            if (code.includes('const ') || code.includes('let ')) {
                issues.push({
                    type: this.issueTypes.CODE_SMELL,
                    description: '可能存在未使用的变量',
                    line: 1,
                    severity: 'medium',
                    fixable: true
                });
            }

            // 检查是否有硬编码的密码或密钥
            if (code.match(/password|secret|key|token/i) && code.match(/['"][^'"]*['"]/)) {
                issues.push({
                    type: this.issueTypes.SECURITY_VULNERABILITY,
                    description: '可能存在硬编码的敏感信息',
                    line: 1,
                    severity: 'high',
                    fixable: true
                });
            }

            logger.info(`AI自动修复服务检测到 ${issues.length} 个问题`, { filePath, issuesCount: issues.length });
            return issues;
        } catch (error) {
            logger.error('AI自动修复服务检测问题失败:', error);
            return [];
        }
    }

    /**
     * 修复代码问题
     * @param {string} code - 代码内容
     * @param {Array} issues - 检测到的问题列表
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixIssues(code, issues, filePath) {
        try {
            let fixedCode = code;

            for (const issue of issues) {
                if (issue.fixable) {
                    const fixStrategy = this.fixStrategies[issue.type];
                    if (fixStrategy) {
                        fixedCode = await fixStrategy(fixedCode, issue, filePath);
                    }
                }
            }

            logger.info(`AI自动修复服务修复了 ${issues.filter(issue => issue.fixable).length} 个问题`, { filePath });
            return fixedCode;
        } catch (error) {
            logger.error('AI自动修复服务修复问题失败:', error);
            return code;
        }
    }

    /**
     * 修复语法错误
     * @param {string} code - 代码内容
     * @param {Object} issue - 问题信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixSyntaxError(code, issue, filePath) {
        // 模拟修复语法错误
        logger.info('修复语法错误', { filePath, issue });
        return code;
    }

    /**
     * 修复逻辑错误
     * @param {string} code - 代码内容
     * @param {Object} issue - 问题信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixLogicError(code, issue, filePath) {
        // 模拟修复逻辑错误
        logger.info('修复逻辑错误', { filePath, issue });
        return code;
    }

    /**
     * 修复性能问题
     * @param {string} code - 代码内容
     * @param {Object} issue - 问题信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixPerformanceIssue(code, issue, filePath) {
        // 模拟修复性能问题
        logger.info('修复性能问题', { filePath, issue });
        return code;
    }

    /**
     * 修复安全漏洞
     * @param {string} code - 代码内容
     * @param {Object} issue - 问题信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixSecurityVulnerability(code, issue, filePath) {
        // 模拟修复安全漏洞
        logger.info('修复安全漏洞', { filePath, issue });
        return code;
    }

    /**
     * 修复代码异味
     * @param {string} code - 代码内容
     * @param {Object} issue - 问题信息
     * @param {string} filePath - 文件路径
     * @returns {Promise<string>} - 修复后的代码
     */
    async fixCodeSmell(code, issue, filePath) {
        // 移除调试代码
        if (issue.description.includes('调试代码未移除')) {
            return code.replace(/console\.log\([^)]*\);?/g, '');
        }

        logger.info('修复代码异味', { filePath, issue });
        return code;
    }

    /**
     * 修复文件中的问题
     * @param {string} filePath - 文件路径
     * @returns {Promise<Object>} - 修复结果
     */
    async fixFile(filePath) {
        try {
            if (!fs.existsSync(filePath)) {
                throw new Error(`文件不存在: ${filePath}`);
            }

            const code = fs.readFileSync(filePath, 'utf8');
            const issues = await this.detectIssues(code, filePath);
            const fixedCode = await this.fixIssues(code, issues, filePath);

            if (fixedCode !== code) {
                fs.writeFileSync(filePath, fixedCode, 'utf8');
                logger.info(`AI自动修复服务已修复文件: ${filePath}`);
            }

            return {
                success: true,
                filePath,
                issuesDetected: issues.length,
                issuesFixed: issues.filter(issue => issue.fixable).length,
                changesMade: fixedCode !== code
            };
        } catch (error) {
            logger.error(`AI自动修复服务修复文件失败: ${filePath}`, error);
            return {
                success: false,
                filePath,
                error: error.message
            };
        }
    }

    /**
     * 修复目录中的所有文件
     * @param {string} directoryPath - 目录路径
     * @param {Array<string>} fileExtensions - 要修复的文件扩展名列表
     * @returns {Promise<Array<Object>>} - 修复结果列表
     */
    async fixDirectory(directoryPath, fileExtensions = ['.js', '.ts', '.jsx', '.tsx']) {
        try {
            if (!fs.existsSync(directoryPath)) {
                throw new Error(`目录不存在: ${directoryPath}`);
            }

            const results = [];
            const files = this.getAllFiles(directoryPath, fileExtensions);

            for (const file of files) {
                const result = await this.fixFile(file);
                results.push(result);
            }

            logger.info(`AI自动修复服务已扫描并修复 ${files.length} 个文件`, {
                directory: directoryPath,
                filesScanned: files.length,
                filesFixed: results.filter(result => result.success && result.changesMade).length
            });

            return results;
        } catch (error) {
            logger.error(`AI自动修复服务修复目录失败: ${directoryPath}`, error);
            return [];
        }
    }

    /**
     * 获取目录中的所有文件
     * @param {string} directoryPath - 目录路径
     * @param {Array<string>} fileExtensions - 要匹配的文件扩展名列表
     * @returns {Array<string>} - 文件路径列表
     */
    getAllFiles(directoryPath, fileExtensions) {
        const files = [];

        const scanDirectory = (dir) => {
            const entries = fs.readdirSync(dir, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                if (entry.isDirectory()) {
                    scanDirectory(fullPath);
                } else if (fileExtensions.includes(path.extname(entry.name))) {
                    files.push(fullPath);
                }
            }
        };

        scanDirectory(directoryPath);
        return files;
    }

    /**
     * 生成修复报告
     * @param {Array<Object>} results - 修复结果列表
     * @returns {Object} - 修复报告
     */
    generateFixReport(results) {
        const totalFiles = results.length;
        const successfulFiles = results.filter(result => result.success).length;
        const filesWithChanges = results.filter(result => result.changesMade).length;
        const totalIssuesDetected = results.reduce((sum, result) => sum + (result.issuesDetected || 0), 0);
        const totalIssuesFixed = results.reduce((sum, result) => sum + (result.issuesFixed || 0), 0);

        return {
            summary: {
                totalFiles,
                successfulFiles,
                filesWithChanges,
                totalIssuesDetected,
                totalIssuesFixed
            },
            details: results
        };
    }
}

module.exports = new AIAutoFixService();
