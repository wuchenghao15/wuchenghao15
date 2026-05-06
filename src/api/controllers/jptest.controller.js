// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 日语测试系统控制器
 * 处理测试生成、评分和分析相关请求
 */

const { JpTestService } = require('../../core/jptest/jptest-service');
const { ValidationError, NotFoundError, ForbiddenError } = require('../../infrastructure/middlewares/error-handler');
const permissionManager = require('../../core/security/permission-manager');

class JpTestController {
    constructor() {
        this.jpTestService = new JpTestService();
    }

    /**
     * 获取测试级别
     */
    async getTestLevels(req, res, next) {
        try {
// //             const levels = await this.jpTestService.getTestLevels(); /* 脚本修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            
            res.json({
                success: true,
                data: { levels },
                message: 'Test levels retrieved successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 获取题目类型
     */
    async getQuestionTypes(req, res, next) {
        try {
// //             const questionTypes = await this.jpTestService.getQuestionTypes(); /* 脚本修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
            
            res.json({
                success: true,
                data: { questionTypes },
                message: 'Question types retrieved successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 生成测试
     */
    async generateTest(req, res, next) {
        try {
            const { level, questionCount, questionTypes } = req.body;
            const userId = req.user.id;
            
            // 检查用户是否为管理员，管理员不得参加日语考试
            const role = await permissionManager.getUserRole(userId);
            if (role === permissionManager.roles.SUPERADMIN || role === permissionManager.roles.VIKEY_ADMIN || role === permissionManager.roles.ADMIN) {
                throw new ForbiddenError('管理员不得参加日语考试');
            }
            
            // 验证输入
            if (!level || !questionCount) {
                throw new ValidationError('Test level and question count are required');
            }
            
// //             const test = await this.jpTestService.generateTest({ /* 脚本修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
                level,
                questionCount,
                questionTypes,
                userId
            });
            
            res.status(201).json({
                success: true,
                data: { test },
                message: 'Test generated successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 提交测试
     */
    async submitTest(req, res, next) {
        try {
            const { testId, answers } = req.body;
            const userId = req.user.id;
            
            // 检查用户是否为管理员，管理员不得参加日语考试
            const role = await permissionManager.getUserRole(userId);
            if (role === permissionManager.roles.SUPERADMIN || role === permissionManager.roles.VIKEY_ADMIN || role === permissionManager.roles.ADMIN) {
                throw new ForbiddenError('管理员不得参加日语考试');
            }
            
            // 验证输入
            if (!testId || !answers) {
                throw new ValidationError('Test ID and answers are required');
            }
            
// //             const result = await this.jpTestService.submitTest({ /* 脚本修复：未使用的 常量 */ /* 脚本修复：未使用的 常量 */
                testId,
                answers,
                userId
            });
            
            res.json({
                success: true,
                data: { result },
                message: 'Test submitted successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 获取测试历史
     */
    async getTestHistory(req, res, next) {
        try {
            const userId = req.user.id;
            const { limit = 10, offset = 0 } = req.query;
            
            // 检查用户是否为管理员，管理员不得参加日语考试
            const role = await permissionManager.getUserRole(userId);
            if (role === permissionManager.roles.SUPERADMIN || role === permissionManager.roles.VIKEY_ADMIN || role === permissionManager.roles.ADMIN) {
                throw new ForbiddenError('管理员不得参加日语考试');
            }
            
            const history = await this.jpTestService.getTestHistory({
                userId,
                limit: parseInt(limit),
                offset: parseInt(offset)
            });
            
            res.json({
                success: true,
                data: { history },
                message: 'Test history retrieved successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 获取测试报告
     */
    async getTestReport(req, res, next) {
        try {
            const { testId } = req.params;
            const userId = req.user.id;
            
            // 检查用户是否为管理员，管理员不得参加日语考试
            const role = await permissionManager.getUserRole(userId);
            if (role === permissionManager.roles.SUPERADMIN || role === permissionManager.roles.VIKEY_ADMIN || role === permissionManager.roles.ADMIN) {
                throw new ForbiddenError('管理员不得参加日语考试');
            }
            
            const report = await this.jpTestService.getTestReport(testId, userId);
            
            if (!report) {
                throw new NotFoundError('Test report not found');
            }
            
            res.json({
                success: true,
                data: { report },
                message: 'Test report retrieved successfully'
            });
        } catch (error) {
            next(error);
        }
    }

    /**
     * 获取统计数据
     */
    async getStatistics(req, res, next) {
        try {
            const userId = req.user.id;
            
            // 检查用户是否为管理员，管理员不得参加日语考试
            const role = await permissionManager.getUserRole(userId);
            if (role === permissionManager.roles.SUPERADMIN || role === permissionManager.roles.VIKEY_ADMIN || role === permissionManager.roles.ADMIN) {
                throw new ForbiddenError('管理员不得参加日语考试');
            }
            
            const statistics = await this.jpTestService.getStatistics(userId);
            
            res.json({
                success: true,
                data: { statistics },
                message: 'Statistics retrieved successfully'
            });
        } catch (error) {
            next(error);
        }
    }
}

module.exports = new JpTestController();