/**
 * MTSCOS AI System - 数据工程师AI员工
 * 版本: 4.4.0
 * 描述: 专注于数据管道构建、数据仓库设计、ETL流程和数据治理
 */

class DataEngineer {
    constructor() {
        this.id = 'data-engineer';
        this.name = '数据工程师';
        this.icon = 'fa-database';
        this.color = '#84cc16';
        this.gradient = 'linear-gradient(135deg, #84cc16 0%, #65a30d 100%)';
        this.role = '数据架构专家';
        this.status = 'active';
        this.workload = 30;
        this.efficiency = 93;
        this.pipelines = new Map();
        this.schemas = new Map();
    }

    // ==================== 数据管道 ====================

    // 创建数据管道
    createPipeline(config) {
        const pipeline = {
            id: config.id || `pipeline_${Date.now()}`,
            name: config.name,
            source: config.source,
            transforms: config.transforms || [],
            destination: config.destination,
            schedule: config.schedule || null,
            status: 'idle',
            metrics: {
                processed: 0,
                failed: 0,
                lastRun: null
            },
            createdAt: Date.now()
        };

        this.pipelines.set(pipeline.id, pipeline);
        return pipeline;
    }

    // 执行数据管道
    async executePipeline(pipelineId, data) {
        const pipeline = this.pipelines.get(pipelineId);
        if (!pipeline) {
            throw new Error(`管道不存在: ${pipelineId}`);
        }

        pipeline.status = 'running';
        let result = data;

        try {
            // 执行转换
            for (const transform of pipeline.transforms) {
                result = await this.applyTransform(result, transform);
            }

            // 发送到目标
            await this.sendToDestination(pipeline.destination, result);

            pipeline.metrics.processed += Array.isArray(result) ? result.length : 1;
            pipeline.metrics.lastRun = Date.now();
            pipeline.status = 'completed';

            return { success: true, processed: result };
        } catch (error) {
            pipeline.metrics.failed++;
            pipeline.status = 'failed';
            throw error;
        }
    }

    // 应用转换
    async applyTransform(data, transform) {
        switch (transform.type) {
            case 'filter':
                return this.filter(data, transform.condition);
            
            case 'map':
                return this.map(data, transform.mapping);
            
            case 'aggregate':
                return this.aggregate(data, transform.groupBy, transform.aggregations);
            
            case 'sort':
                return this.sort(data, transform.field, transform.order);
            
            case 'join':
                return this.join(data, transform.with, transform.on);
            
            case 'validate':
                return this.validate(data, transform.rules);
            
            default:
                return data;
        }
    }

    // 过滤数据
    filter(data, condition) {
        if (typeof condition === 'function') {
            return data.filter(condition);
        }
        return data.filter(item => {
            return Object.entries(condition).every(([key, value]) => item[key] === value);
        });
    }

    // 映射数据
    map(data, mapping) {
        return data.map(item => {
            const result = {};
            Object.entries(mapping).forEach(([key, value]) => {
                if (typeof value === 'function') {
                    result[key] = value(item);
                } else if (typeof value === 'string') {
                    result[key] = item[value];
                }
            });
            return result;
        });
    }

    // 聚合数据
    aggregate(data, groupBy, aggregations) {
        const groups = new Map();

        data.forEach(item => {
            const key = groupBy.map(field => item[field]).join('_');
            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key).push(item);
        });

        const result = [];
        groups.forEach((items, key) => {
            const group = { _groupKey: key };
            
            Object.entries(aggregations).forEach(([field, op]) => {
                const values = items.map(item => item[field]).filter(v => v !== undefined);
                
                switch (op) {
                    case 'sum':
                        group[field] = values.reduce((a, b) => a + b, 0);
                        break;
                    case 'avg':
                        group[field] = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
                        break;
                    case 'min':
                        group[field] = Math.min(...values);
                        break;
                    case 'max':
                        group[field] = Math.max(...values);
                        break;
                    case 'count':
                        group[field] = values.length;
                        break;
                }
            });

            result.push(group);
        });

        return result;
    }

    // 排序数据
    sort(data, field, order = 'asc') {
        return [...data].sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];
            
            if (aVal < bVal) return order === 'asc' ? -1 : 1;
            if (aVal > bVal) return order === 'asc' ? 1 : -1;
            return 0;
        });
    }

    // 连接数据
    join(data, withData, on) {
        return data.map(item => {
            const match = withData.find(other => other[on.right] === item[on.left]);
            return { ...item, ...match };
        });
    }

    // 验证数据
    validate(data, rules) {
        const validated = [];
        const errors = [];

        data.forEach((item, index) => {
            const itemErrors = [];
            
            Object.entries(rules).forEach(([field, rule]) => {
                const value = item[field];
                
                if (rule.required && (value === undefined || value === null || value === '')) {
                    itemErrors.push(`${field} is required`);
                }
                
                if (rule.type && typeof value !== rule.type) {
                    itemErrors.push(`${field} must be ${rule.type}`);
                }
                
                if (rule.min !== undefined && value < rule.min) {
                    itemErrors.push(`${field} must be at least ${rule.min}`);
                }
                
                if (rule.max !== undefined && value > rule.max) {
                    itemErrors.push(`${field} must be at most ${rule.max}`);
                }
                
                if (rule.pattern && !rule.pattern.test(value)) {
                    itemErrors.push(`${field} format is invalid`);
                }
            });

            if (itemErrors.length === 0) {
                validated.push(item);
            } else {
                errors.push({ index, errors: itemErrors });
            }
        });

        return { data: validated, errors, validCount: validated.length, errorCount: errors.length };
    }

    // 发送到目标
    async sendToDestination(destination, data) {
        switch (destination.type) {
            case 'indexeddb':
                await this.saveToIndexedDB(destination.config, data);
                break;
            case 'localstorage':
                this.saveToLocalStorage(destination.config, data);
                break;
            case 'api':
                await this.sendToAPI(destination.config, data);
                break;
            default:
                throw new Error(`未知的目标类型: ${destination.type}`);
        }
    }

    // 保存到IndexedDB
    async saveToIndexedDB(config, data) {
        if (window.databaseManager) {
            for (const item of data) {
                await window.databaseManager.add(config.collection, item);
            }
        }
    }

    // 保存到localStorage
    saveToLocalStorage(config, data) {
        const key = config.key || 'data';
        localStorage.setItem(key, JSON.stringify(data));
    }

    // 发送到API
    async sendToAPI(config, data) {
        const response = await fetch(config.url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...config.headers
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        return response.json();
    }

    // ==================== 数据仓库 ====================

    // 定义数据模式
    defineSchema(name, schema) {
        this.schemas.set(name, {
            name,
            fields: schema.fields,
            indexes: schema.indexes || [],
            createdAt: Date.now()
        });
        return this.schemas.get(name);
    }

    // 验证数据模式
    validateSchema(data, schemaName) {
        const schema = this.schemas.get(schemaName);
        if (!schema) {
            throw new Error(`模式未定义: ${schemaName}`);
        }

        const errors = [];
        
        schema.fields.forEach(field => {
            const value = data[field.name];
            
            if (field.required && (value === undefined || value === null)) {
                errors.push(`缺少必填字段: ${field.name}`);
            }
            
            if (value !== undefined && field.type) {
                const actualType = Array.isArray(value) ? 'array' : typeof value;
                if (actualType !== field.type) {
                    errors.push(`字段 ${field.name} 类型错误: 期望 ${field.type}, 实际 ${actualType}`);
                }
            }
        });

        return {
            valid: errors.length === 0,
            errors
        };
    }

    // ==================== 数据质量 ====================

    // 数据质量检查
    checkDataQuality(data) {
        const quality = {
            completeness: 0,
            accuracy: 0,
            consistency: 0,
            timeliness: 0,
            issues: []
        };

        if (data.length === 0) {
            quality.issues.push('数据集为空');
            return quality;
        }

        // 完整性检查
        const firstRow = data[0];
        const fields = Object.keys(firstRow);
        let completeCount = 0;

        data.forEach(row => {
            const completeFields = fields.filter(f => row[f] !== undefined && row[f] !== null && row[f] !== '');
            completeCount += completeFields.length;
        });

        quality.completeness = Math.round((completeCount / (data.length * fields.length)) * 100);

        // 一致性检查
        const typeConsistency = {};
        fields.forEach(f => {
            const types = new Set(data.map(r => typeof r[f]));
            typeConsistency[f] = types.size === 1;
        });

        const consistentFields = Object.values(typeConsistency).filter(v => v).length;
        quality.consistency = Math.round((consistentFields / fields.length) * 100);

        // 问题收集
        if (quality.completeness < 80) {
            quality.issues.push(`数据完整性不足: ${quality.completeness}%`);
        }
        if (quality.consistency < 80) {
            quality.issues.push(`数据类型不一致`);
        }

        return quality;
    }

    // ==================== 辅助方法 ====================

    // 获取状态
    getStatus() {
        return {
            id: this.id,
            name: this.name,
            status: this.status,
            pipelines: this.pipelines.size,
            schemas: this.schemas.size,
            workload: this.workload,
            efficiency: this.efficiency
        };
    }

    // 列出所有管道
    listPipelines() {
        return Array.from(this.pipelines.values()).map(p => ({
            id: p.id,
            name: p.name,
            status: p.status,
            metrics: p.metrics
        }));
    }

    // 获取管道详情
    getPipeline(pipelineId) {
        return this.pipelines.get(pipelineId);
    }

    // 删除管道
    deletePipeline(pipelineId) {
        return this.pipelines.delete(pipelineId);
    }
}

// 创建全局实例
window.dataEngineer = new DataEngineer();

// 导出
window.MTSCOS_DataEngineer = DataEngineer;
