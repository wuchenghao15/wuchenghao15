/**
 * MTSCOS AI System - 脑库管理器
 * 版本: 1.0.0
 * 描述: 统一管理脑库数据库，为AI提供知识检索和学习的接口
 */

class BrainManager {
    constructor(brainDatabase) {
        this.brain = brainDatabase;
        this.cache = new Map();
        this.cacheTTL = 5 * 60 * 1000; // 5分钟缓存
        this.init();
    }
    
    async init() {
        // 等待脑库数据库就绪
        await this.waitForReady();
        
        // 预加载常用数据到缓存
        await this.preloadCache();
        
        console.log('✅ 脑库管理器初始化成功');
    }
    
    async waitForReady() {
        if (this.brain.isReady) return;
        
        return new Promise((resolve) => {
            document.addEventListener('mtscos:brain:ready', resolve, { once: true });
        });
    }
    
    async preloadCache() {
        try {
            const cases = await this.brain.getAllFixCases();
            this.setCache('fixCases', cases);
            
            const practices = await this.brain.getAllBestPractices();
            this.setCache('bestPractices', practices);
            
            const patterns = await this.brain.getAllTechPatterns();
            this.setCache('techPatterns', patterns);
            
            const errors = await this.brain.getAllErrorSolutions();
            this.setCache('errorSolutions', errors);
            
            console.log('📚 脑库缓存预加载完成');
        } catch (error) {
            console.error('❌ 脑库缓存预加载失败:', error);
        }
    }
    
    // ==================== 缓存管理 ====================
    
    setCache(key, value) {
        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }
    
    getCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        // 检查是否过期
        if (Date.now() - cached.timestamp > this.cacheTTL) {
            this.cache.delete(key);
            return null;
        }
        
        return cached.value;
    }
    
    clearCache() {
        this.cache.clear();
    }
    
    // ==================== 查询接口 ====================
    
    async getFixCase(id) {
        return await this.brain.getFixCase(id);
    }
    
    async getAllFixCases() {
        const cached = this.getCache('fixCases');
        if (cached) return cached;
        
        const cases = await this.brain.getAllFixCases();
        this.setCache('fixCases', cases);
        return cases;
    }
    
    async getBestPractice(id) {
        return await this.brain.getBestPractice(id);
    }
    
    async getAllBestPractices() {
        const cached = this.getCache('bestPractices');
        if (cached) return cached;
        
        const practices = await this.brain.getAllBestPractices();
        this.setCache('bestPractices', practices);
        return practices;
    }
    
    async getTechPattern(id) {
        return await this.brain.getTechPattern(id);
    }
    
    async getAllTechPatterns() {
        const cached = this.getCache('techPatterns');
        if (cached) return cached;
        
        const patterns = await this.brain.getAllTechPatterns();
        this.setCache('techPatterns', patterns);
        return patterns;
    }
    
    async getErrorSolution(id) {
        return await this.brain.getErrorSolution(id);
    }
    
    async getAllErrorSolutions() {
        const cached = this.getCache('errorSolutions');
        if (cached) return cached;
        
        const errors = await this.brain.getAllErrorSolutions();
        this.setCache('errorSolutions', errors);
        return errors;
    }
    
    // ==================== 智能检索 ====================
    
    async search(query) {
        const results = await this.brain.searchBrain(query);
        
        // 智能排序
        results.sort((a, b) => {
            // 优先匹配标题
            const aTitle = (a.title || '').toLowerCase();
            const bTitle = (b.title || '').toLowerCase();
            const queryLower = query.toLowerCase();
            
            if (aTitle.includes(queryLower) && !bTitle.includes(queryLower)) return -1;
            if (bTitle.includes(queryLower) && !aTitle.includes(queryLower)) return 1;
            
            // 按相关性排序
            const aRelevance = this.calculateRelevance(a, query);
            const bRelevance = this.calculateRelevance(b, query);
            return bRelevance - aRelevance;
        });
        
        return results;
    }
    
    calculateRelevance(item, query) {
        const queryLower = query.toLowerCase();
        const itemStr = JSON.stringify(item).toLowerCase();
        
        let score = 0;
        
        // 标题匹配
        if ((item.title || '').toLowerCase().includes(queryLower)) score += 10;
        
        // 标签匹配
        if ((item.tags || []).some(tag => tag.includes(queryLower))) score += 5;
        
        // 描述匹配
        if ((item.description || '').toLowerCase().includes(queryLower)) score += 3;
        
        // 内容匹配
        const matches = (itemStr.match(new RegExp(queryLower, 'g')) || []).length;
        score += matches;
        
        return score;
    }
    
    // ==================== 问题诊断 ====================
    
    async diagnoseError(errorMessage) {
        // 1. 首先尝试精确匹配错误ID
        const errorId = errorMessage.split(':')[0];
        const errorCase = await this.getErrorSolution(errorId);
        if (errorCase) {
            return {
                matched: true,
                type: 'exact',
                solution: errorCase
            };
        }
        
        // 2. 模糊搜索错误信息
        const allErrors = await this.getAllErrorSolutions();
        const matches = allErrors.filter(e => 
            e.error.toLowerCase().includes(errorMessage.toLowerCase()) ||
            errorMessage.toLowerCase().includes(e.error.toLowerCase())
        );
        
        if (matches.length > 0) {
            return {
                matched: true,
                type: 'fuzzy',
                solutions: matches
            };
        }
        
        // 3. 根据关键词搜索相关修复案例
        const keywords = this.extractKeywords(errorMessage);
        const relatedCases = await this.search(keywords.join(' '));
        
        return {
            matched: false,
            type: 'related',
            suggestions: relatedCases.slice(0, 5)
        };
    }
    
    extractKeywords(message) {
        // 提取关键错误词
        const stopWords = ['error', 'typeerror', 'syntaxerror', 'cannot', 'read', 'property', 'undefined', 'is', 'not', 'a'];
        const words = message.toLowerCase().split(/\s+/);
        
        return words
            .filter(w => w.length > 3)
            .filter(w => !stopWords.includes(w))
            .slice(0, 5);
    }
    
    // ==================== 学习推荐 ====================
    
    async recommendLearning(category) {
        const materials = await this.brain.getAll('learning_materials');
        
        if (category) {
            return materials.filter(m => 
                m.category === category || 
                (m.tags || []).includes(category)
            );
        }
        
        return materials;
    }
    
    async getRelatedBestPractices(category) {
        const practices = await this.getAllBestPractices();
        return practices.filter(p => p.category === category);
    }
    
    async getRelatedPatterns(patternType) {
        const patterns = await this.getAllTechPatterns();
        return patterns.filter(p => p.category === patternType);
    }
    
    // ==================== 导出接口 ====================
    
    async exportKnowledge() {
        const data = await this.brain.exportBrain();
        
        // 触发导出事件
        document.dispatchEvent(new CustomEvent('mtscos:brain:exported', {
            detail: data
        }));
        
        return data;
    }
    
    async getStats() {
        return await this.brain.getStats();
    }
    
    // ==================== 健康检查 ====================
    
    async healthCheck() {
        return {
            status: 'ok',
            cacheSize: this.cache.size,
            cacheTTL: this.cacheTTL,
            brainReady: this.brain.isReady,
            ...await this.getStats()
        };
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrainManager;
}
