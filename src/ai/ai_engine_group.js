/**
 * AI引擎组管理模块
 * 负责统一调配管理母AI，自动适配合适的子AI，并实现母AI监控系统
 */

const winston = require('winston');
const crypto = require('crypto');
const AIManager = require('./ai_manager');
const AIAutomaticExpansion = require('./ai_automatic_expansion');

// 配置日志
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({
            filename: `${process.env.LOG_DIR || './Logs'}/ai_engine_group.log`,
            maxsize: 5242880,
            maxFiles: 5
        }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

// AI引擎组状态
const ENGINE_GROUP_STATUS = {
    IDLE: 'idle',
    RUNNING: 'running',
    PAUSED: 'paused',
    ERROR: 'error'
};

/**
 * AI引擎组类
 * 负责统一调配管理母AI，自动适配合适的子AI，并实现母AI监控系统
 */
class AIEngineGroup {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = `AI_Engine_Group_${Date.now()}`;
        this.status = ENGINE_GROUP_STATUS.IDLE;
        this.aiManager = new AIManager();
        this.motherAIs = new Map(); // 母AI映射
        this.projects = new Map(); // 项目映射
        this.featureLibrary = new Map(); // 特征库映射
        this.automaticExpansion = null; // AI自动拓展系统
        this.createdAt = new Date();
        this.updatedAt = new Date();
        
        this.initEngineGroup();
    }
    
    /**
     * 初始化AI引擎组
     */
    initEngineGroup() {
        logger.info(`初始化AI引擎组: ${this.name}`);
        
        // 从AI管理器中获取主AI作为母AI
        this.initializeMotherAIs();
        
        // 启动监控系统
        this.startMonitoring();
        
        // 初始化AI自动拓展系统
        this.initializeAutomaticExpansion();
        
        this.status = ENGINE_GROUP_STATUS.RUNNING;
        logger.info(`AI引擎组 ${this.name} 初始化完成，状态: ${this.status}`);
    }
    
    /**
     * 初始化AI自动拓展系统
     */
    initializeAutomaticExpansion() {
        logger.info('初始化AI自动拓展系统');
        this.automaticExpansion = new AIAutomaticExpansion(this);
        logger.info('AI自动拓展系统初始化完成');
    }
    
    /**
     * 初始化母AI
     */
    initializeMotherAIs() {
        const mainAIs = this.aiManager.mainAIIds
            .map(id => this.aiManager.aiInstances.get(id))
            .filter(Boolean);
        
        mainAIs.forEach(ai => {
            this.motherAIs.set(ai.id, {
                ai: ai,
                status: 'active',
                subordinateCount: ai.subordinateIds.length,
                monitoredProjects: new Set(),
                lastActiveAt: new Date()
            });
            logger.info(`添加母AI: ${ai.name} (${ai.role}) 到引擎组`);
        });
    }
    
    /**
     * 启动监控系统
     */
    startMonitoring() {
        // 每30秒检查一次母AI和子AI状态
        setInterval(() => {
            this.monitorMotherAIs();
            this.monitorSubAIs();
        }, 30000);
        
        logger.info('AI引擎组监控系统已启动');
    }
    
    /**
     * 监控母AI状态
     */
    monitorMotherAIs() {
        logger.info('开始监控母AI状态');
        
        this.motherAIs.forEach((motherAIInfo, motherAIId) => {
            const motherAI = motherAIInfo.ai;
            
            // 检查母AI状态
            if (motherAI.status === 'error') {
                logger.warning(`母AI ${motherAI.name} 状态异常，正在重启`);
                this.restartMotherAI(motherAIId);
            }
            
            // 更新母AI活跃时间
            motherAIInfo.lastActiveAt = new Date();
            motherAIInfo.subordinateCount = motherAI.subordinateIds.length;
        });
    }
    
    /**
     * 监控子AI状态
     */
    monitorSubAIs() {
        logger.info('开始监控子AI状态');
        
        this.motherAIs.forEach((motherAIInfo) => {
            const motherAI = motherAIInfo.ai;
            
            motherAI.subordinateIds.forEach(subordinateId => {
                const subAI = this.aiManager.aiInstances.get(subordinateId);
                if (subAI) {
                    // 检查子AI状态
                    if (subAI.status === 'error') {
                        logger.warning(`子AI ${subAI.name} 状态异常，正在通知母AI ${motherAI.name} 处理`);
                        this.notifyMotherAISubAIError(motherAI, subAI);
                    }
                }
            });
        });
    }
    
    /**
     * 重启母AI
     * @param {string} motherAIId - 母AI ID
     */
    restartMotherAI(motherAIId) {
        const motherAIInfo = this.motherAIs.get(motherAIId);
        if (motherAIInfo) {
            const motherAI = motherAIInfo.ai;
            
            try {
                logger.info(`正在重启母AI: ${motherAI.name}`);
                // 重置母AI状态
                motherAI.status = 'idle';
                motherAI.deploymentStatus = 'running';
                motherAIInfo.status = 'active';
                
                logger.info(`母AI ${motherAI.name} 重启成功`);
            } catch (error) {
                logger.error(`母AI ${motherAI.name} 重启失败: ${error.message}`);
                motherAIInfo.status = 'error';
            }
        }
    }
    
    /**
     * 通知母AI子AI出错
     * @param {AIInstance} motherAI - 母AI实例
     * @param {AIInstance} subAI - 子AI实例
     */
    notifyMotherAISubAIError(motherAI, subAI) {
        logger.info(`母AI ${motherAI.name} 正在处理子AI ${subAI.name} 的错误`);
        
        // 这里可以添加更复杂的错误处理逻辑
        // 例如：重启子AI、替换子AI、或者调整子AI分配
        
        // 简单实现：重启子AI
        try {
            subAI.status = 'idle';
            subAI.deploymentStatus = 'running';
            logger.info(`子AI ${subAI.name} 已重启`);
        } catch (error) {
            logger.error(`子AI ${subAI.name} 重启失败: ${error.message}`);
            // 如果重启失败，可以考虑替换子AI
            this.replaceSubAI(motherAI, subAI.id);
        }
    }
    
    /**
     * 替换子AI
     * @param {AIInstance} motherAI - 母AI实例
     * @param {string} subAIId - 子AI ID
     */
    replaceSubAI(motherAI, subAIId) {
        logger.info(`母AI ${motherAI.name} 正在替换子AI: ${subAIId}`);
        
        // 移除旧子AI
        motherAI.removeSubordinate(subAIId);
        this.aiManager.removeAIInstance(subAIId);
        
        // 创建新子AI
        const newSubAI = this.aiManager.createSubAIForMainAI(motherAI);
        if (newSubAI) {
            motherAI.addSubordinate(newSubAI.id);
            newSubAI.setSupervisor(motherAI.id);
            logger.info(`母AI ${motherAI.name} 成功替换子AI，新子AI: ${newSubAI.name}`);
        }
    }
    
    /**
     * 根据项目功能自动适配合适的子AI
     * @param {Object} projectInfo - 项目信息
     * @returns {Object} - 适配结果
     */
    autoAdaptSubAIs(projectInfo) {
        logger.info(`开始根据项目 ${projectInfo.name || '未知项目'} 自动适配合适的子AI`);
        
        // 分析项目功能需求
        const requirements = this.analyzeProjectRequirements(projectInfo);
        
        // 生成优化任务，自动分配子AI监管
        const tasks = this.aiManager.generateTasks(requirements);
        
        // 获取为该项目分配的子AI
        const assignedSubAIs = this.getAssignedSubAIs(requirements);
        
        // 深度绑定子AI到项目
        this.bindSubAIsToProject(assignedSubAIs, projectInfo);
        
        const result = {
            success: true,
            message: `已根据项目功能适配 ${assignedSubAIs.length} 个子AI`,
            requirements: requirements,
            assignedSubAIs: assignedSubAIs.map(ai => ({
                id: ai.id,
                name: ai.name,
                role: ai.role,
                group: ai.group
            })),
            tasks: tasks.length
        };
        
        logger.info(`项目 ${projectInfo.name || '未知项目'} 子AI适配完成: ${JSON.stringify(result)}`);
        return result;
    }
    
    /**
     * 分析项目功能需求
     * @param {Object} projectInfo - 项目信息
     * @returns {Object} - 项目需求
     */
    analyzeProjectRequirements(projectInfo) {
        const requirements = {};
        
        // 根据项目类型确定需求
        switch (projectInfo.type) {
            case 'web':
                requirements.前端优化 = true;
                requirements.后端优化 = true;
                requirements.性能优化 = true;
                requirements.安全优化 = true;
                requirements.客户端异常处理 = true;
                requirements.日志优化 = true;
                break;
            case 'mobile':
                requirements.前端优化 = true;
                requirements.性能优化 = true;
                requirements.安全优化 = true;
                requirements.客户端异常处理 = true;
                break;
            case 'data':
                requirements.功能优化 = true;
                requirements.性能优化 = true;
                requirements.数据库优化 = true;
                requirements.日志优化 = true;
                break;
            default:
                requirements.功能优化 = true;
                requirements.性能优化 = true;
                requirements.安全优化 = true;
        }
        
        // 根据项目技术栈确定需求
        if (projectInfo.techStack) {
            if (projectInfo.techStack.includes('react') || projectInfo.techStack.includes('vue')) {
                requirements.前端优化 = true;
            }
            if (projectInfo.techStack.includes('node.js') || projectInfo.techStack.includes('python')) {
                requirements.后端优化 = true;
            }
            if (projectInfo.techStack.includes('mysql') || projectInfo.techStack.includes('mongodb')) {
                requirements.数据库优化 = true;
            }
        }
        
        // 根据项目规模确定需求
        if (projectInfo.size === 'large' || projectInfo.size === 'xlarge') {
            requirements.性能优化 = true;
            requirements.管理优化 = true;
            requirements.日志优化 = true;
        }
        
        return requirements;
    }
    
    /**
     * 获取为项目分配的子AI
     * @param {Object} requirements - 项目需求
     * @returns {Array} - 子AI列表
     */
    getAssignedSubAIs(requirements) {
        const requiredRoles = this.aiManager.parseRequirementsToRoles(requirements);
        const subAIs = [];
        
        requiredRoles.forEach(role => {
            // 找到对应角色的母AI
            const motherAI = this.aiManager.findMainAIByRole(role);
            if (motherAI) {
                // 获取该母AI的子AI
                const motherAISubAIs = motherAI.subordinateIds
                    .map(id => this.aiManager.aiInstances.get(id))
                    .filter(Boolean);
                
                subAIs.push(...motherAISubAIs);
            }
        });
        
        return [...new Set(subAIs)]; // 去重
    }
    
    /**
     * 深度绑定子AI到项目
     * @param {Array} subAIs - 子AI列表
     * @param {Object} projectInfo - 项目信息
     */
    bindSubAIsToProject(subAIs, projectInfo) {
        logger.info(`开始将 ${subAIs.length} 个子AI深度绑定到项目 ${projectInfo.name || '未知项目'}`);
        
        subAIs.forEach(ai => {
            // 适配AI到项目
            ai.adaptToProject(projectInfo);
            
            // 添加项目到AI的关联
            if (!ai.assignedProjects) ai.assignedProjects = new Set();
            ai.assignedProjects.add(projectInfo.id || projectInfo.name);
            
            // 更新母AI的监控项目
            const motherAIInfo = this.motherAIs.get(ai.supervisorId);
            if (motherAIInfo) {
                motherAIInfo.monitoredProjects.add(projectInfo.id || projectInfo.name);
            }
            
            logger.info(`子AI ${ai.name} 已深度绑定到项目 ${projectInfo.name || '未知项目'}`);
        });
    }
    
    /**
     * 注册项目到AI引擎组
     * @param {Object} projectInfo - 项目信息
     * @returns {Object} - 注册结果
     */
    registerProject(projectInfo) {
        const projectId = projectInfo.id || `project_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
        const project = {
            ...projectInfo,
            id: projectId,
            registeredAt: new Date(),
            updatedAt: new Date(),
            status: 'active',
            assignedAIs: new Set()
        };
        
        this.projects.set(projectId, project);
        
        // 自动适配子AI
        const adaptationResult = this.autoAdaptSubAIs(project);
        
        // 添加分配的AI到项目
        adaptationResult.assignedSubAIs.forEach(ai => {
            project.assignedAIs.add(ai.id);
        });
        
        logger.info(`项目 ${project.name || '未知项目'} 已成功注册到AI引擎组，ID: ${projectId}`);
        
        return {
            success: true,
            projectId: projectId,
            adaptationResult: adaptationResult
        };
    }
    
    /**
     * 上报特征库到AI引擎组
     * @param {Object} featureData - 特征数据
     * @returns {Object} - 上报结果
     */
    reportFeatureLibrary(featureData) {
        const featureId = `feature_${Date.now()}_${crypto.randomUUID().slice(0, 8)}`;
        const feature = {
            ...featureData,
            id: featureId,
            reportedAt: new Date(),
            status: 'pending'
        };
        
        this.featureLibrary.set(featureId, feature);
        
        // 通知母AI处理新特征
        this.notifyMotherAIsNewFeature(feature);
        
        logger.info(`特征库已上报到AI引擎组，ID: ${featureId}`);
        
        return {
            success: true,
            featureId: featureId,
            message: '特征库上报成功，已通知母AI处理'
        };
    }
    
    /**
     * 通知母AI处理新特征
     * @param {Object} feature - 特征数据
     */
    notifyMotherAIsNewFeature(feature) {
        this.motherAIs.forEach((motherAIInfo) => {
            const motherAI = motherAIInfo.ai;
            logger.info(`通知母AI ${motherAI.name} 处理新特征: ${feature.id}`);
            
            // 这里可以添加更复杂的特征处理逻辑
            // 例如：根据特征类型分配给特定的母AI
            
            // 简单实现：标记特征为已处理
            feature.status = 'processed';
            feature.processedBy = motherAI.id;
            feature.processedAt = new Date();
        });
    }
    
    /**
     * 获取AI引擎组状态
     * @returns {Object} - 引擎组状态
     */
    getStatus() {
        const systemStatus = this.aiManager.getSystemStatus();
        
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            motherAICount: this.motherAIs.size,
            totalAICount: systemStatus.totalAI,
            projectCount: this.projects.size,
            featureLibraryCount: this.featureLibrary.size,
            systemStatus: systemStatus,
            createdAt: this.createdAt,
            updatedAt: this.updatedAt
        };
    }
    
    /**
     * 获取母AI状态
     * @returns {Array} - 母AI状态列表
     */
    getMotherAIStatus() {
        return Array.from(this.motherAIs.values()).map(motherAIInfo => {
            const ai = motherAIInfo.ai;
            return {
                id: ai.id,
                name: ai.name,
                role: ai.role,
                status: motherAIInfo.status,
                subordinateCount: motherAIInfo.subordinateCount,
                monitoredProjectCount: motherAIInfo.monitoredProjects.size,
                lastActiveAt: motherAIInfo.lastActiveAt,
                aiStatus: ai.status
            };
        });
    }
    
    /**
     * 获取项目列表
     * @returns {Array} - 项目列表
     */
    getProjects() {
        return Array.from(this.projects.values()).map(project => ({
            ...project,
            assignedAICount: project.assignedAIs.size
        }));
    }
    
    /**
     * 获取特征库列表
     * @returns {Array} - 特征库列表
     */
    getFeatureLibrary() {
        return Array.from(this.featureLibrary.values());
    }
    
    /**
     * 暂停AI引擎组
     * @returns {Object} - 暂停结果
     */
    pause() {
        this.status = ENGINE_GROUP_STATUS.PAUSED;
        logger.info(`AI引擎组 ${this.name} 已暂停`);
        return {
            success: true,
            message: `AI引擎组 ${this.name} 已暂停`
        };
    }
    
    /**
     * 恢复AI引擎组
     * @returns {Object} - 恢复结果
     */
    resume() {
        this.status = ENGINE_GROUP_STATUS.RUNNING;
        logger.info(`AI引擎组 ${this.name} 已恢复运行`);
        return {
            success: true,
            message: `AI引擎组 ${this.name} 已恢复运行`
        };
    }
    
    /**
     * 停止AI引擎组
     * @returns {Object} - 停止结果
     */
    stop() {
        this.status = ENGINE_GROUP_STATUS.IDLE;
        logger.info(`AI引擎组 ${this.name} 已停止`);
        return {
            success: true,
            message: `AI引擎组 ${this.name} 已停止`
        };
    }
    
    /**
     * 获取AI自动拓展系统状态
     * @returns {Object} - 自动拓展系统状态
     */
    getAutomaticExpansionStatus() {
        if (this.automaticExpansion) {
            return this.automaticExpansion.getStatus();
        }
        return null;
    }
    
    /**
     * 手动触发AI自动拓展循环
     * @returns {Promise<Object>} - 拓展循环结果
     */
    async triggerExpansionCycle() {
        if (this.automaticExpansion) {
            return await this.automaticExpansion.triggerExpansionCycle();
        }
        logger.warning('AI自动拓展系统未初始化，无法触发拓展循环');
        return null;
    }
    
    /**
     * 获取AI自动拓展历史
     * @returns {Array} - 拓展历史列表
     */
    getExpansionHistory() {
        if (this.automaticExpansion) {
            return this.automaticExpansion.getImprovementHistory();
        }
        return [];
    }
}

// 导出AI引擎组类
module.exports = AIEngineGroup;
