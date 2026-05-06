/**
 * MTSCOS AI 系统 - 缓存模块
 * 用于缓存系统数据，提高性能
 */

class Cache {
    constructor() {
        this.cache = new Map();
        this.defaultTTL = 3600; // 默认过期时间1小时
    }
    
    // 设置缓存项
    set(key, value, ttl = this.defaultTTL) {
        const expiresAt = Date.now() + (ttl * 1000);
        this.cache.set(key, { value, expiresAt });
    }
    
    // 获取缓存项
    get(key) {
        const item = this.cache.get(key);
        if (!item) {
            return null;
        }
        
        // 检查是否过期
        if (Date.now() > item.expiresAt) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    }
    
    // 删除缓存项
    delete(key) {
        return this.cache.delete(key);
    }
    
    // 清空所有缓存
    clear() {
        this.cache.clear();
    }
    
    // 检查缓存项是否存在
    has(key) {
        return this.get(key) !== null;
    }
    
    // 获取缓存大小
    size() {
        // 清理过期项
        this.cleanup();
        return this.cache.size;
    }
    
    // 清理过期缓存项
    cleanup() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now > item.expiresAt) {
                this.cache.delete(key);
            }
        }
    }
}

module.exports = new Cache();
