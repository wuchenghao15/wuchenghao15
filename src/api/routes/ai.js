/**
 * AI API路由
 * 处理AI相关的API请求
 */

const express = require('express');
const router = express.Router();
const aiAutoFixService = require('../../core/ai/ai-auto-fix-service');
const authMiddleware = require('../../core/middleware/auth-middleware');
const permissionManager = require('../../core/security/permission-manager');

// AI管理权限中间件
const aiManagementPermission = permissionManager.requirePermission(
    permissionManager.permissions.SYSTEM_CONFIG,
    permissionManager.permissionLevels.MODIFY
);

// 获取AI系统状态
router.get('/status', 
    authMiddleware.requireAuth,
    async (req, res, next) => {
        try {
            res.json({
                success: true,
                data: {
                    status: 'running',
                    services: {
                        autoFix: 'active',
                        questionGenerator: 'active',
                        modelManager: 'active'
                    }
                },
                message: 'AI系统状态获取成功'
            });
        } catch (error) {
            next(error);
        }
    }
);

// 检测代码问题
router.post('/detect-issues', 
    authMiddleware.requireAuth,
    async (req, res, next) => {
        try {
            const { code, filePath } = req.body;
            const issues = await aiAutoFixService.detectIssues(code, filePath);
            
            res.json({
                success: true,
                data: { issues },
                message: '代码问题检测成功'
            });
        } catch (error) {
            next(error);
        }
    }
);

// 修复代码问题
router.post('/fix-issues', 
    authMiddleware.requireAuth,
    async (req, res, next) => {
        try {
            const { code, issues, filePath } = req.body;
            const fixedCode = await aiAutoFixService.fixIssues(code, issues, filePath);
            
            res.json({
                success: true,
                data: { fixedCode },
                message: '代码问题修复成功'
            });
        } catch (error) {
            next(error);
        }
    }
);

// 修复文件
router.post('/fix-file', 
    authMiddleware.requireAuth,
    aiManagementPermission,
    async (req, res, next) => {
        try {
            const { filePath } = req.body;
            const result = await aiAutoFixService.fixFile(filePath);
            
            res.json({
                success: result.success,
                data: result,
                message: result.success ? '文件修复成功' : '文件修复失败'
            });
        } catch (error) {
            next(error);
        }
    }
);

// 修复目录
router.post('/fix-directory', 
    authMiddleware.requireAuth,
    aiManagementPermission,
    async (req, res, next) => {
        try {
            const { directoryPath, fileExtensions } = req.body;
            const results = await aiAutoFixService.fixDirectory(directoryPath, fileExtensions);
            const report = aiAutoFixService.generateFixReport(results);
            
            res.json({
                success: true,
                data: report,
                message: '目录修复成功'
            });
        } catch (error) {
            next(error);
        }
    }
);

// 获取AI修复报告
router.post('/fix-report', 
    authMiddleware.requireAuth,
    aiManagementPermission,
    async (req, res, next) => {
        try {
            const { results } = req.body;
            const report = aiAutoFixService.generateFixReport(results);
            
            res.json({
                success: true,
                data: report,
                message: '修复报告生成成功'
            });
        } catch (error) {
            next(error);
        }
    }
);

module.exports = router;
