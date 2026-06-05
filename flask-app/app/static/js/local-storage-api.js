/**
 * 本地存储API客户端，替代localStorage功能
 * 统一由数据库管理本地数据
 */

class LocalStorageAPI {
    constructor() {
        this.baseUrl = '/api/local-storage';
    }

    /**
     * 设置存储值
     * @param {string} key - 存储键
     * @param {any} value - 存储值
     * @param {number} ttl - 过期时间（毫秒），可选
     * @returns {Promise<boolean>} - 是否成功
     */
    async set(key, value, ttl = null) {
        try {
            const response = await fetch(`${this.baseUrl}/set`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ key, value, ttl })
            });

            const result = await response.json();
            return result.success;
        } catch (error) {
            console.error('设置本地存储失败:', error);
            return false;
        }
    }

    /**
     * 获取存储值
     * @param {string} key - 存储键
     * @returns {Promise<any>} - 存储值
     */
    async get(key) {
        try {
            const response = await fetch(`${this.baseUrl}/get/${encodeURIComponent(key)}`);
            const result = await response.json();
            return result.success ? result.value : null;
        } catch (error) {
            console.error('获取本地存储失败:', error);
            return null;
        }
    }

    /**
     * 删除存储值
     * @param {string} key - 存储键
     * @returns {Promise<boolean>} - 是否成功
     */
    async remove(key) {
        try {
            const response = await fetch(`${this.baseUrl}/remove/${encodeURIComponent(key)}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            return result.success;
        } catch (error) {
            console.error('删除本地存储失败:', error);
            return false;
        }
    }

    /**
     * 清空存储值
     * @returns {Promise<boolean>} - 是否成功
     */
    async clear() {
        try {
            const response = await fetch(`${this.baseUrl}/clear`, {
                method: 'DELETE'
            });

            const result = await response.json();
            return result.success;
        } catch (error) {
            console.error('清空本地存储失败:', error);
            return false;
        }
    }

    /**
     * 获取所有存储值
     * @returns {Promise<object>} - 所有存储值
     */
    async getAll() {
        try {
            const response = await fetch(`${this.baseUrl}/all`);
            const result = await response.json();
            return result.success ? result.values : {};
        } catch (error) {
            console.error('获取所有本地存储失败:', error);
            return {};
        }
    }
}

// 创建全局实例
const localStorageAPI = new LocalStorageAPI();

// 替换全局localStorage对象
if (typeof window !== 'undefined') {
    window.localStorage = {
        setItem: async function(key, value) {
            try {
                const parsedValue = typeof value === 'string' ? JSON.parse(value) : value;
                return await localStorageAPI.set(key, parsedValue);
            } catch (error) {
                console.error('localStorage.setItem失败:', error);
                return false;
            }
        },
        getItem: async function(key) {
            try {
                const value = await localStorageAPI.get(key);
                return JSON.stringify(value);
            } catch (error) {
                console.error('localStorage.getItem失败:', error);
                return null;
            }
        },
        removeItem: async function(key) {
            try {
                return await localStorageAPI.remove(key);
            } catch (error) {
                console.error('localStorage.removeItem失败:', error);
                return false;
            }
        },
        clear: async function() {
            try {
                return await localStorageAPI.clear();
            } catch (error) {
                console.error('localStorage.clear失败:', error);
                return false;
            }
        },
        // 保持与localStorage兼容的其他方法
        key: function(index) {
            console.warn('localStorage.key方法已弃用，请使用localStorageAPI.getAll()');
            return null;
        },
        length: 0
    };
}
