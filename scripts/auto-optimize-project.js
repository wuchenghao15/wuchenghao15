/**
 * 项目自动优化脚本
 * 功能：
 * 1. 合并重复项
 * 2. 删除冗余
 * 3. 修复错误异常
 * 4. 将异常错误特征上传到特征数据库
 * 5. 将优化举措上传到数据库
 */

const fs = require('fs');
const path = require('path');
const { AIManager } = require('../src/ai/ai_manager');
const { DataAPI } = require('../src/database/db');

/**
 * 项目自动优化类
 */
class ProjectAutoOptimizer {
    constructor() {
        this.logger = {
            info: (message) => console.log(`[INFO] ${message}`),
            error: (message) => console.error(`[ERROR] ${message}`),
            warn: (message) => console.warn(`[WARN] ${message}`)
        };
        this.optimizationResults = [];
        this.errorFeatures = [];
    }

    /**
     * 开始自动优化
     */
    async startOptimization() {
        this.logger.info('开始项目自动优化...');
        
        try {
            // 1. 执行各种优化任务
            await this.optimizeConfigurationFiles();
            await this.optimizeAIInstances();
            await this.optimizeTaskScheduling();
            await this.fixErrorExceptions();
            
            // 2. 上传异常特征到数据库
            await this.uploadErrorFeatures();
            
            // 3. 上传优化举措到数据库
            await this.uploadOptimizationMeasures();
            
            this.logger.info('项目自动优化完成！');
            this.logger.info(`优化结果：共 ${this.optimizationResults.length} 项优化，${this.errorFeatures.length} 个异常特征`);
            
            return {
                success: true,
                optimizationCount: this.optimizationResults.length,
                errorFeatureCount: this.errorFeatures.length,
                results: this.optimizationResults
            };
        } catch (error) {
            this.logger.error('项目自动优化失败:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 优化配置文件
     */
    async optimizeConfigurationFiles() {
        this.logger.info('优化配置文件...');
        
        const configFiles = [
            { path: 'src/config/ai-models.json', type: 'ai_models' },
            { path: 'src/config/ai-roles.json', type: 'ai_roles' },
            { path: 'src/config/ai-groups.json', type: 'ai_groups' }
        ];
        
        for (const configFile of configFiles) {
            await this.optimizeConfigFile(configFile);
        }
    }

    /**
     * 优化单个配置文件
     * @param {Object} configFile - 配置文件信息
     */
    async optimizeConfigFile(configFile) {
        const fullPath = path.join(__dirname, '..', configFile.path);
        
        try {
            if (fs.existsSync(fullPath)) {
                const configData = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
                
                // 合并重复项
                const optimizedData = this.mergeDuplicates(configData, configFile.type);
                
                // 删除冗余
                const cleanedData = this.removeRedundancy(optimizedData, configFile.type);
                
                // 检查是否有变化
                if (JSON.stringify(configData) !== JSON.stringify(cleanedData)) {
                    // 保存优化后的配置
                    fs.writeFileSync(fullPath, JSON.stringify(cleanedData, null, 2));
                    
                    this.optimizationResults.push({
                        type: 'config_optimization',
                        file: configFile.path,
                        action: 'merged_duplicates_and_removed_redundancy',
                        timestamp: new Date().toISOString()
                    });
                    
                    this.logger.info(`优化了配置文件: ${configFile.path}`);
                }
            }
        } catch (error) {
            this.logger.error(`优化配置文件失败: ${configFile.path}`, error);
            this.errorFeatures.push({
                type: 'config_error',
                file: configFile.path,
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 合并重复项
     * @param {Object} data - 配置数据
     * @param {string} type - 配置类型
     */
    mergeDuplicates(data, type) {
        switch (type) {
            case 'ai_models':
                // 合并重复的AI模型
                if (data.models) {
                    const uniqueModels = [];
                    const modelIds = new Set();
                    
                    data.models.forEach(model => {
                        if (!modelIds.has(model.id)) {
                            modelIds.add(model.id);
                            uniqueModels.push(model);
                        }
                    });
                    
                    data.models = uniqueModels;
                }
                break;
                
            case 'ai_roles':
            case 'ai_groups':
                // 合并重复的角色或组
                if (data.items) {
                    const uniqueItems = [];
                    const itemIds = new Set();
                    
                    data.items.forEach(item => {
                        if (!itemIds.has(item.id)) {
                            itemIds.add(item.id);
                            uniqueItems.push(item);
                        }
                    });
                    
                    data.items = uniqueItems;
                }
                break;
        }
        
        return data;
    }

    /**
     * 删除冗余
     * @param {Object} data - 配置数据
     * @param {string} type - 配置类型
     */
    removeRedundancy(data, type) {
        switch (type) {
            case 'ai_models':
                // 删除冗余的AI模型配置
                if (data.models) {
                    data.models = data.models.map(model => {
                        // 移除空的或未使用的配置
                        const cleanedModel = { ...model };
                        if (cleanedModel.capabilities && cleanedModel.capabilities.length === 0) {
                            delete cleanedModel.capabilities;
                        }
                        if (cleanedModel.performance && Object.values(cleanedModel.performance).length === 0) {
                            delete cleanedModel.performance;
                        }
                        return cleanedModel;
                    });
                }
                break;
        }
        
        return data;
    }

    /**
     * 优化AI实例
     */
    async optimizeAIInstances() {
        this.logger.info('优化AI实例...');
        
        try {
            // 使用AI管理器获取所有AI实例
            const aiInstances = AIManager.aiInstances;
            
            // 检测并移除重复的AI实例
            const uniqueAIIds = new Set();
            const duplicateAIs = [];
            
            for (const [id, ai] of aiInstances.entries()) {
                if (uniqueAIIds.has(ai.name)) {
                    duplicateAIs.push(id);
                } else {
                    uniqueAIIds.add(ai.name);
                }
            }
            
            // 移除重复的AI实例
            for (const aiId of duplicateAIs) {
                AIManager.aiInstances.delete(aiId);
                this.optimizationResults.push({
                    type: 'ai_instance_optimization',
                    action: 'removed_duplicate',
                    aiId: aiId,
                    timestamp: new Date().toISOString()
                });
            }
            
            if (duplicateAIs.length > 0) {
                this.logger.info(`移除了 ${duplicateAIs.length} 个重复的AI实例`);
            }
        } catch (error) {
            this.logger.error('优化AI实例失败:', error);
            this.errorFeatures.push({
                type: 'ai_instance_error',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 优化任务调度
     */
    async optimizeTaskScheduling() {
        this.logger.info('优化任务调度...');
        
        try {
            // 检查任务队列
            const taskQueue = AIManager.taskQueue;
            const tasks = AIManager.tasks;
            
            // 移除无效任务
            const validTasks = taskQueue.filter(taskId => tasks.has(taskId));
            
            if (validTasks.length !== taskQueue.length) {
                AIManager.taskQueue = validTasks;
                this.optimizationResults.push({
                    type: 'task_scheduling_optimization',
                    action: 'removed_invalid_tasks',
                    removedCount: taskQueue.length - validTasks.length,
                    timestamp: new Date().toISOString()
                });
                this.logger.info(`移除了 ${taskQueue.length - validTasks.length} 个无效任务`);
            }
        } catch (error) {
            this.logger.error('优化任务调度失败:', error);
            this.errorFeatures.push({
                type: 'task_scheduling_error',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 修复错误异常
     */
    async fixErrorExceptions() {
        this.logger.info('修复错误异常...');
        
        try {
            // 模拟修复一些常见错误
            // 1. 检查端口配置
            const portConfig = await DataAPI.getConfig('server.ports') || {};
            if (!portConfig.http || !portConfig.https) {
                const fixedConfig = {
                    http: 8080,
                    https: 8443,
                    ...portConfig
                };
                await DataAPI.setConfig('server.ports', fixedConfig, 'json', '服务器端口配置');
                
                this.optimizationResults.push({
                    type: 'error_fix',
                    action: 'fixed_port_config',
                    oldConfig: portConfig,
                    newConfig: fixedConfig,
                    timestamp: new Date().toISOString()
                });
                
                this.logger.info('修复了端口配置');
            }
            
            // 2. 检查AI引擎配置
            const aiEngineConfig = await DataAPI.getConfig('ai.engine') || {};
            if (!aiEngineConfig.enabled) {
                aiEngineConfig.enabled = true;
                await DataAPI.setConfig('ai.engine', aiEngineConfig, 'json', 'AI引擎配置');
                
                this.optimizationResults.push({
                    type: 'error_fix',
                    action: 'enabled_ai_engine',
                    timestamp: new Date().toISOString()
                });
                
                this.logger.info('启用了AI引擎');
            }
        } catch (error) {
            this.logger.error('修复错误异常失败:', error);
            this.errorFeatures.push({
                type: 'error_fix_failure',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 上传异常特征到数据库
     */
    async uploadErrorFeatures() {
        this.logger.info('上传异常特征到数据库...');
        
        try {
            for (const errorFeature of this.errorFeatures) {
                // 上传到特征数据库
                await DataAPI.setConfig(
                    `error.feature.${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    errorFeature,
                    'json',
                    '异常错误特征'
                );
            }
            
            if (this.errorFeatures.length > 0) {
                this.logger.info(`上传了 ${this.errorFeatures.length} 个异常特征到数据库`);
            }
        } catch (error) {
            this.logger.error('上传异常特征失败:', error);
        }
    }

    /**
     * 上传优化举措到数据库
     */
    async uploadOptimizationMeasures() {
        this.logger.info('上传优化举措到数据库...');
        
        try {
            for (const optimization of this.optimizationResults) {
                // 上传到优化举措数据库
                await DataAPI.setConfig(
                    `optimization.${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    optimization,
                    'json',
                    '优化举措'
                );
            }
            
            if (this.optimizationResults.length > 0) {
                this.logger.info(`上传了 ${this.optimizationResults.length} 个优化举措到数据库`);
            }
        } catch (error) {
            this.logger.error('上传优化举措失败:', error);
        }
    }
}

// 执行自动优化
const optimizer = new ProjectAutoOptimizer();
optimizer.startOptimization()
    .then(result => {
        if (result.success) {
            console.log('✅ 项目自动优化成功完成！');
            console.log(`📊 优化结果：`);
            console.log(`   - 共优化：${result.optimizationCount} 项`);
            console.log(`   - 异常特征：${result.errorFeatureCount} 个`);
        } else {
            console.error('❌ 项目自动优化失败:', result.error);
        }
    })
    .catch(error => {
        console.error('❌ 项目自动优化发生未捕获错误:', error);
    });
