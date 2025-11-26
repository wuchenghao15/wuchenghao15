/**
 * MTSCOS 规则管理API
 * 提供规则的CRUD操作和管理功能
 */

class RuleManagementAPI {
    constructor() {
        this.baseUrl = '/api/rules';
        this.ruleEngine = window.ruleEngine;
    }

    /**
     * 获取所有规则
     */
    async getAllRules() {
        try {
            const rules = this.ruleEngine.getAllRules();
            return {
                success: true,
                data: rules,
                total: rules.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 根据分类获取规则
     */
    async getRulesByCategory(category) {
        try {
            const allRules = this.ruleEngine.getAllRules();
            const categoryRules = allRules.filter(rule => rule.category === category);
            
            return {
                success: true,
                data: categoryRules,
                total: categoryRules.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取单个规则
     */
    async getRule(ruleId) {
        try {
            const rule = this.ruleEngine.getRule(ruleId);
            
            if (!rule) {
                return {
                    success: false,
                    error: '规则不存在'
                };
            }
            
            return {
                success: true,
                data: rule
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 创建新规则
     */
    async createRule(ruleData) {
        try {
            // 验证规则数据
            const validation = this.validateRuleData(ruleData);
            if (!validation.valid) {
                return {
                    success: false,
                    error: '规则数据验证失败',
                    details: validation.errors
                };
            }

            // 检查规则ID是否已存在
            if (this.ruleEngine.getRule(ruleData.id)) {
                return {
                    success: false,
                    error: '规则ID已存在'
                };
            }

            // 添加规则
            this.ruleEngine.addRule(ruleData);
            
            // 保存到配置文件
            await this.saveRulesToFile();
            
            return {
                success: true,
                data: ruleData,
                message: '规则创建成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 更新规则
     */
    async updateRule(ruleId, updateData) {
        try {
            // 验证更新数据
            if (updateData.id && updateData.id !== ruleId) {
                return {
                    success: false,
                    error: '不允许修改规则ID'
                };
            }

            const validation = this.validateRuleData(updateData);
            if (!validation.valid) {
                return {
                    success: false,
                    error: '规则数据验证失败',
                    details: validation.errors
                };
            }

            // 更新规则
            const success = this.ruleEngine.updateRule(ruleId, updateData);
            
            if (!success) {
                return {
                    success: false,
                    error: '规则不存在'
                };
            }
            
            // 保存到配置文件
            await this.saveRulesToFile();
            
            return {
                success: true,
                data: this.ruleEngine.getRule(ruleId),
                message: '规则更新成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 删除规则
     */
    async deleteRule(ruleId) {
        try {
            const rule = this.ruleEngine.getRule(ruleId);
            
            if (!rule) {
                return {
                    success: false,
                    error: '规则不存在'
                };
            }

            // 删除规则
            const success = this.ruleEngine.removeRule(ruleId);
            
            if (!success) {
                return {
                    success: false,
                    error: '删除规则失败'
                };
            }
            
            // 保存到配置文件
            await this.saveRulesToFile();
            
            return {
                success: true,
                message: '规则删除成功'
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 启用/禁用规则
     */
    async toggleRule(ruleId, enabled) {
        try {
            const success = this.ruleEngine.toggleRule(ruleId, enabled);
            
            if (!success) {
                return {
                    success: false,
                    error: '规则不存在'
                };
            }
            
            // 保存到配置文件
            await this.saveRulesToFile();
            
            return {
                success: true,
                message: `规则已${enabled ? '启用' : '禁用'}`
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 批量操作规则
     */
    async batchOperation(operation, ruleIds, data = {}) {
        try {
            const results = [];
            
            for (const ruleId of ruleIds) {
                let result;
                
                switch (operation) {
                    case 'enable':
                        result = await this.toggleRule(ruleId, true);
                        break;
                    case 'disable':
                        result = await this.toggleRule(ruleId, false);
                        break;
                    case 'delete':
                        result = await this.deleteRule(ruleId);
                        break;
                    case 'update':
                        result = await this.updateRule(ruleId, data);
                        break;
                    default:
                        result = {
                            success: false,
                            error: '未知操作类型'
                        };
                }
                
                results.push({
                    ruleId,
                    ...result
                });
            }
            
            return {
                success: true,
                data: results,
                summary: {
                    total: ruleIds.length,
                    successful: results.filter(r => r.success).length,
                    failed: results.filter(r => !r.success).length
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取规则执行统计
     */
    async getRuleStatistics(ruleId) {
        try {
            const stats = this.ruleEngine.getRuleStatistics(ruleId);
            
            if (!stats.rule) {
                return {
                    success: false,
                    error: '规则不存在'
                };
            }
            
            return {
                success: true,
                data: stats
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取所有规则统计
     */
    async getAllRuleStatistics() {
        try {
            const allRules = this.ruleEngine.getAllRules();
            const statistics = {};
            
            allRules.forEach(rule => {
                statistics[rule.id] = this.ruleEngine.getRuleStatistics(rule.id);
            });
            
            return {
                success: true,
                data: statistics
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 测试规则
     */
    async testRule(ruleData, testData) {
        try {
            // 创建临时规则实例进行测试
            const tempRuleId = 'temp_test_rule';
            const tempRule = {
                ...ruleData,
                id: tempRuleId,
                enabled: true
            };
            
            this.ruleEngine.addRule(tempRule);
            
            // 模拟测试事件
            const eventType = testData.eventType || 'test_event';
            await this.ruleEngine.handleEvent(eventType, testData);
            
            // 获取测试结果
            const stats = this.ruleEngine.getRuleStatistics(tempRuleId);
            
            // 清理临时规则
            this.ruleEngine.removeRule(tempRuleId);
            
            return {
                success: true,
                data: {
                    executed: stats.executionCount > 0,
                    statistics: stats
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 导入规则
     */
    async importRules(rulesData) {
        try {
            const results = [];
            
            for (const ruleData of rulesData) {
                const result = await this.createRule(ruleData);
                results.push({
                    ruleId: ruleData.id,
                    ...result
                });
            }
            
            return {
                success: true,
                data: results,
                summary: {
                    total: rulesData.length,
                    imported: results.filter(r => r.success).length,
                    failed: results.filter(r => !r.success).length
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 导出规则
     */
    async exportRules(ruleIds = null) {
        try {
            let rules;
            
            if (ruleIds) {
                // 导出指定规则
                rules = [];
                for (const ruleId of ruleIds) {
                    const rule = this.ruleEngine.getRule(ruleId);
                    if (rule) {
                        rules.push(rule);
                    }
                }
            } else {
                // 导出所有规则
                rules = this.ruleEngine.getAllRules();
            }
            
            return {
                success: true,
                data: {
                    rules: rules,
                    exportTime: new Date().toISOString(),
                    version: '1.0.0'
                }
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取规则模板
     */
    async getRuleTemplates() {
        try {
            const templates = {
                security: [
                    {
                        name: '登录失败锁定',
                        description: '连续登录失败后锁定账户',
                        template: {
                            id: 'SEC_TEMPLATE_001',
                            name: '登录失败锁定',
                            description: '连续登录失败N次后锁定账户',
                            category: '安全规则',
                            enabled: true,
                            priority: 'high',
                            conditions: {
                                eventType: 'login_failed',
                                count: 5,
                                timeWindow: '30m'
                            },
                            actions: [
                                {
                                    type: 'lock_account',
                                    parameters: {
                                        duration: '30m',
                                        reason: '多次登录失败'
                                    }
                                }
                            ],
                            mechanism: 'account_security'
                        }
                    }
                ],
                performance: [
                    {
                        name: '缓存清理',
                        description: '缓存大小超过阈值时自动清理',
                        template: {
                            id: 'PERF_TEMPLATE_001',
                            name: '缓存清理规则',
                            description: '缓存超过指定大小时自动清理',
                            category: '性能规则',
                            enabled: true,
                            priority: 'medium',
                            conditions: {
                                eventType: 'cache_check',
                                cacheSize: '100MB'
                            },
                            actions: [
                                {
                                    type: 'clean_cache',
                                    parameters: {
                                        target: 'all',
                                        keepRecent: '24h'
                                    }
                                }
                            ],
                            mechanism: 'cache_manager'
                        }
                    }
                ],
                backup: [
                    {
                        name: '定时备份',
                        description: '按计划执行数据备份',
                        template: {
                            id: 'BAK_TEMPLATE_001',
                            name: '定时备份规则',
                            description: '按计划执行系统数据备份',
                            category: '备份规则',
                            enabled: true,
                            priority: 'high',
                            conditions: {
                                eventType: 'scheduled_task',
                                schedule: '0 2 * * *',
                                timezone: 'Asia/Shanghai'
                            },
                            actions: [
                                {
                                    type: 'backup',
                                    parameters: {
                                        type: 'full',
                                        destination: '/Backups',
                                        compression: true
                                    }
                                }
                            ],
                            mechanism: 'backup_manager'
                        }
                    }
                ]
            };
            
            return {
                success: true,
                data: templates
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 验证规则数据
     */
    validateRuleData(ruleData) {
        const errors = [];
        
        // 必填字段验证
        if (!ruleData.id) errors.push('规则ID不能为空');
        if (!ruleData.name) errors.push('规则名称不能为空');
        if (!ruleData.description) errors.push('规则描述不能为空');
        if (!ruleData.category) errors.push('规则分类不能为空');
        if (!ruleData.mechanism) errors.push('执行机制不能为空');
        
        // 条件验证
        if (!ruleData.conditions || Object.keys(ruleData.conditions).length === 0) {
            errors.push('规则条件不能为空');
        }
        
        // 动作验证
        if (!ruleData.actions || ruleData.actions.length === 0) {
            errors.push('规则动作不能为空');
        } else {
            ruleData.actions.forEach((action, index) => {
                if (!action.type) errors.push(`动作${index + 1}类型不能为空`);
            });
        }
        
        // 优先级验证
        if (ruleData.priority && !['high', 'medium', 'low'].includes(ruleData.priority)) {
            errors.push('优先级必须是high、medium或low');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * 保存规则到文件
     */
    async saveRulesToFile() {
        try {
            const allRules = this.ruleEngine.getAllRules();
            
            // 按分类组织规则
            const categories = {};
            allRules.forEach(rule => {
                if (!categories[rule.category]) {
                    categories[rule.category] = {
                        name: rule.category,
                        description: `${rule.category}相关规则`,
                        rules: []
                    };
                }
                categories[rule.category].rules.push(rule);
            });
            
            // 构建完整的规则配置
            const systemRules = {
                systemRules: {
                    version: '1.0.0',
                    lastUpdated: new Date().toISOString(),
                    categories: categories,
                    mechanisms: this.getMechanismsConfig()
                }
            };
            
            // 这里应该调用后端API保存文件
            console.log('保存规则配置到文件:', systemRules);
            
            return true;
        } catch (error) {
            console.error('保存规则文件失败:', error);
            throw error;
        }
    }

    /**
     * 获取机制配置
     */
    getMechanismsConfig() {
        const mechanisms = {};
        
        // 获取所有机制配置
        if (this.ruleEngine && this.ruleEngine.mechanisms) {
            this.ruleEngine.mechanisms.forEach((mechanism, id) => {
                mechanisms[id] = {
                    name: mechanism.name,
                    description: mechanism.description,
                    type: mechanism.type,
                    enabled: mechanism.enabled
                };
            });
        }
        
        return mechanisms;
    }

    /**
     * 搜索规则
     */
    async searchRules(query, filters = {}) {
        try {
            const allRules = this.ruleEngine.getAllRules();
            let filteredRules = allRules;
            
            // 应用过滤器
            if (filters.category) {
                filteredRules = filteredRules.filter(rule => rule.category === filters.category);
            }
            
            if (filters.priority) {
                filteredRules = filteredRules.filter(rule => rule.priority === filters.priority);
            }
            
            if (filters.enabled !== undefined) {
                filteredRules = filteredRules.filter(rule => rule.enabled === filters.enabled);
            }
            
            if (filters.mechanism) {
                filteredRules = filteredRules.filter(rule => rule.mechanism === filters.mechanism);
            }
            
            // 应用搜索查询
            if (query) {
                const searchQuery = query.toLowerCase();
                filteredRules = filteredRules.filter(rule => 
                    rule.name.toLowerCase().includes(searchQuery) ||
                    rule.description.toLowerCase().includes(searchQuery) ||
                    rule.id.toLowerCase().includes(searchQuery)
                );
            }
            
            return {
                success: true,
                data: filteredRules,
                total: filteredRules.length
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// 创建全局API实例
window.ruleManagementAPI = new RuleManagementAPI();

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RuleManagementAPI;
}