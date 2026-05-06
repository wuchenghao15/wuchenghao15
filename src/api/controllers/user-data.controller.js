// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 用户数据管理控制器
 * 处理用户数据的存储、获取和管理
 */

const userDataStorageService = require('../../core/storage/user-data-storage-service');

class UserDataController {
    /**
     * 存储用户数据
     */
    async storeUserData(req, res, next) {
        try {
            const { key, value, options } = req.body;
            const userId = req.user.id;
            
            if (!key || value === undefined) {
                return res.status(400).json({
                    success: false,
                    message: 'Key and value are required'
                });
            }
            
            const result = await userDataStorageService.storeUserData(userId, key, value, options);
            
            res.status(200).json(result);
        } catch (error) {
            console.error('存储用户数据失败:', error);
            res.status(500).json({
                success: false,
                message: '存储用户数据失败'
            });
        }
    }
    
    /**
     * 获取用户数据
     */
    async getUserData(req, res, next) {
        try {
            const { key } = req.body;
            const userId = req.user.id;
            
            if (!key) {
                return res.status(400).json({
                    success: false,
                    message: 'Key is required'
                });
            }
            
            const result = await userDataStorageService.getUserData(userId, key);
            
            res.status(200).json(result);
        } catch (error) {
            console.error('获取用户数据失败:', error);
            res.status(500).json({
                success: false,
                message: '获取用户数据失败'
            });
        }
    }
    
    /**
     * 获取用户数据列表
     */
    async getUserDataList(req, res, next) {
        try {
            const userId = req.user.id;
            const { category, limit, offset } = req.query;
            
            const result = await userDataStorageService.getUserDataList(userId, {
                category,
                limit: parseInt(limit) || 10,
                offset: parseInt(offset) || 0
            });
            
            res.status(200).json(result);
        } catch (error) {
            console.error('获取用户数据列表失败:', error);
            res.status(500).json({
                success: false,
                message: '获取用户数据列表失败'
            });
        }
    }
    
    /**
     * 删除用户数据
     */
    async deleteUserData(req, res, next) {
        try {
            const { key } = req.body;
            const userId = req.user.id;
            
            if (!key) {
                return res.status(400).json({
                    success: false,
                    message: 'Key is required'
                });
            }
            
            const result = await userDataStorageService.deleteUserData(userId, key);
            
            res.status(200).json(result);
        } catch (error) {
            console.error('删除用户数据失败:', error);
            res.status(500).json({
                success: false,
                message: '删除用户数据失败'
            });
        }
    }
    
    /**
     * 获取用户数据统计
     */
    async getUserDataStats(req, res, next) {
        try {
            const userId = req.user.id;
            
            const result = await userDataStorageService.getUserDataStats(userId);
            
            res.status(200).json(result);
        } catch (error) {
            console.error('获取用户数据统计失败:', error);
            res.status(500).json({
                success: false,
                message: '获取用户数据统计失败'
            });
        }
    }
}

module.exports = new UserDataController();
