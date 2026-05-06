/**
 * AI特征库管理模块
 * 用于管理和上报系统中的AI特征
 */

const fs = require('fs');
const path = require('path');

// 特征库数据文件路径
const FEATURE_DB_PATH = path.join(__dirname, '../../../src/data/error-feature-db.json');

class AIFeatureLibrary {
    constructor() {
        this.features = [];
        this.modelFeatures = new Map();
        this.categoryFeatures = new Map();
        this.loadFeatures();
        this.initModelFeatures();
    }

    /**
     * 加载特征库数据
     */
    loadFeatures() {
        try {
            const data = fs.readFileSync(FEATURE_DB_PATH, 'utf8');
            this.features = JSON.parse(data);
            console.log(`✅ 成功加载 ${this.features.length} 个特征`);
        } catch (error) {
            console.error('❌ 加载特征库失败:', error);
            this.features = [];
        }
    }

    /**
     * 初始化模型特征映射
     */
    initModelFeatures() {
        // 初始化模型特征映射
        const defaultModels = [
            'model_deepseek',
            'model_chatgpt',
            'model_qwen',
            'model_doubao',
            'model_volcano',
            'model_tencent',
            'model_ali',
            'model_xiaomi',
            'model_apple',
            'model_afu'
        ];

        defaultModels.forEach(model => {
            this.modelFeatures.set(model, [
                'algorithm-design',
                'data-structures',
                'system-design',
                'logical-reasoning'
            ]);
        });

        // 根据特征库数据更新模型特征
        this.features.forEach(feature => {
            if (feature.aiId && feature.aiName) {
                const modelId = `model_${feature.aiName.toLowerCase().replace(/\s+/g, '_')}`;
                if (!this.modelFeatures.has(modelId)) {
                    this.modelFeatures.set(modelId, []);
                }
                const features = this.modelFeatures.get(modelId);
                if (!features.includes(feature.type)) {
                    features.push(feature.type);
                    this.modelFeatures.set(modelId, features);
                }
            }
        });
    }

    /**
     * 获取指定模型的特征
     * @param {string} modelId 模型ID
     * @returns {Array} 特征列表
     */
    getModelFeatures(modelId) {
        return this.modelFeatures.get(modelId) || [];
    }

    /**
     * 添加特征到模型
     * @param {string} modelId 模型ID
     * @param {Array} features 特征列表
     */
    addModelFeatures(modelId, features) {
        if (!this.modelFeatures.has(modelId)) {
            this.modelFeatures.set(modelId, []);
        }
        const existingFeatures = this.modelFeatures.get(modelId);
        const newFeatures = [...new Set([...existingFeatures, ...features])];
        this.modelFeatures.set(modelId, newFeatures);
    }

    /**
     * 获取所有特征
     * @returns {Array} 特征列表
     */
    getAllFeatures() {
        return this.features;
    }

    /**
     * 获取特征统计信息
     * @returns {Object} 统计信息
     */
    getStatistics() {
        const stats = {
            totalCategories: 0,
            totalFeatures: this.features.length,
            totalModelMappings: this.modelFeatures.size,
            featuresPerCategory: {},
            featuresPerModel: {}
        };

        // 按类别统计特征
        this.features.forEach(feature => {
            const category = feature.type || 'unknown';
            stats.featuresPerCategory[category] = (stats.featuresPerCategory[category] || 0) + 1;
        });
        stats.totalCategories = Object.keys(stats.featuresPerCategory).length;

        // 按模型统计特征
        this.modelFeatures.forEach((features, model) => {
            stats.featuresPerModel[model] = features.length;
        });

        return stats;
    }

    /**
     * 上报特征库到中央服务器
     * @returns {Promise<boolean>} 上报结果
     */
    async reportFeatureLibrary() {
        try {
            // 这里应该实现真正的上报逻辑，例如调用API
            // 目前模拟上报成功
            console.log('📤 正在上报特征库...');
            console.log(`📊 上报内容：`);
            console.log(`   - 总特征数：${this.features.length}`);
            console.log(`   - 总模型数：${this.modelFeatures.size}`);
            console.log(`   - 总类别数：${Object.keys(this.getStatistics().featuresPerCategory).length}`);
            console.log('✅ 特征库上报成功！');
            return true;
        } catch (error) {
            console.error('❌ 特征库上报失败:', error);
            return false;
        }
    }

    /**
     * 保存特征库到文件
     */
    saveFeatureLibrary() {
        try {
            fs.writeFileSync(FEATURE_DB_PATH, JSON.stringify(this.features, null, 2));
            console.log('💾 特征库已保存到文件');
        } catch (error) {
            console.error('❌ 保存特征库失败:', error);
        }
    }

    /**
     * 添加新特征
     * @param {Object} feature 特征对象
     */
    addFeature(feature) {
        const newFeature = {
            id: `feature_${Date.now()}`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            status: 'active',
            version: '1.0.0',
            ...feature
        };
        this.features.push(newFeature);
        this.saveFeatureLibrary();
        return newFeature;
    }

    /**
     * 更新特征
     * @param {string} featureId 特征ID
     * @param {Object} updates 更新内容
     */
    updateFeature(featureId, updates) {
        const featureIndex = this.features.findIndex(f => f.id === featureId);
        if (featureIndex !== -1) {
            this.features[featureIndex] = {
                ...this.features[featureIndex],
                ...updates,
                updatedAt: new Date().toISOString()
            };
            this.saveFeatureLibrary();
            return this.features[featureIndex];
        }
        return null;
    }

    /**
     * 根据类型获取特征
     * @param {string} type 特征类型
     * @returns {Array} 特征列表
     */
    getFeaturesByType(type) {
        return this.features.filter(feature => feature.type === type);
    }

    /**
     * 根据AI ID获取特征
     * @param {string} aiId AI ID
     * @returns {Array} 特征列表
     */
    getFeaturesByAIId(aiId) {
        return this.features.filter(feature => feature.aiId === aiId);
    }
}

// 导出单例实例
const aiFeatureLibrary = new AIFeatureLibrary();
module.exports = aiFeatureLibrary;