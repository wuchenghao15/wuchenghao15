// JavaScript按需加载工具

/**
 * 按需加载JavaScript文件
 * @param {string} url - 脚本URL
 * @param {Object} options - 加载选项
 * @returns {Promise} - 加载完成的Promise
 */
function loadScript(url, options = {}) {
    return new Promise((resolve, reject) => {
        // 检查脚本是否已加载
        const existingScript = document.querySelector(`script[src="${url}"]`);
        if (existingScript) {
            if (existingScript.dataset.loaded === 'true') {
                resolve(existingScript);
            } else {
                existingScript.addEventListener('load', () => resolve(existingScript));
                existingScript.addEventListener('error', reject);
            }
            return;
        }
        
        // 创建新脚本标签
        const script = document.createElement('script');
        script.src = url;
        script.async = options.async !== false;
        script.defer = options.defer || false;
        
        // 设置脚本属性
        if (options.type) script.type = options.type;
        if (options.charset) script.charset = options.charset;
        if (options.crossOrigin) script.crossOrigin = options.crossOrigin;
        
        // 脚本加载完成事件
        script.addEventListener('load', () => {
            script.dataset.loaded = 'true';
            resolve(script);
        });
        
        // 脚本加载错误事件
        script.addEventListener('error', (error) => {
            console.error(`加载脚本失败: ${url}`, error);
            reject(error);
        });
        
        // 将脚本添加到DOM
        const parent = options.parent || document.head;
        parent.appendChild(script);
    });
}

/**
 * 按需加载CSS文件
 * @param {string} url - CSS URL
 * @param {Object} options - 加载选项
 * @returns {Promise} - 加载完成的Promise
 */
function loadCSS(url, options = {}) {
    return new Promise((resolve, reject) => {
        // 检查CSS是否已加载
        const existingLink = document.querySelector(`link[rel="stylesheet"][href="${url}"]`);
        if (existingLink) {
            resolve(existingLink);
            return;
        }
        
        // 创建新link标签
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.media = options.media || 'all';
        
        // 设置link属性
        if (options.type) link.type = options.type;
        if (options.crossOrigin) link.crossOrigin = options.crossOrigin;
        
        // CSS加载完成事件
        link.addEventListener('load', () => resolve(link));
        
        // CSS加载错误事件
        link.addEventListener('error', (error) => {
            console.error(`加载CSS失败: ${url}`, error);
            reject(error);
        });
        
        // 将link添加到DOM
        const parent = options.parent || document.head;
        parent.appendChild(link);
    });
}

/**
 * 按需加载多个资源
 * @param {Array} resources - 资源列表，每个资源包含type和url
 * @returns {Promise} - 所有资源加载完成的Promise
 */
function loadResources(resources) {
    const promises = resources.map(resource => {
        if (resource.type === 'script') {
            return loadScript(resource.url, resource.options);
        } else if (resource.type === 'css') {
            return loadCSS(resource.url, resource.options);
        }
        return Promise.resolve();
    });
    
    return Promise.all(promises);
}

/**
 * 懒加载模块 - 当元素进入视口时加载资源
 * @param {string|HTMLElement} selector - 元素选择器或DOM元素
 * @param {Array} resources - 要加载的资源列表
 * @param {Object} options - 观察选项
 */
function lazyLoadModule(selector, resources, options = {}) {
    const elements = typeof selector === 'string' 
        ? document.querySelectorAll(selector) 
        : [selector];
    
    if (elements.length === 0) return;
    
    // 默认观察选项
    const observerOptions = {
        root: options.root || null,
        rootMargin: options.rootMargin || '0px',
        threshold: options.threshold || 0.1
    };
    
    // 创建观察者
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // 加载资源
                loadResources(resources).then(() => {
                    if (options.onLoad) {
                        options.onLoad(entry.target);
                    }
                }).catch(error => {
                    console.error('懒加载模块失败:', error);
                });
                
                // 停止观察
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // 观察所有元素
    elements.forEach(element => {
        observer.observe(element);
    });
    
    return observer;
}

// 导出工具函数
if (typeof module !== 'undefined' && module.exports) {
    // Node.js环境
    module.exports = {
        loadScript,
        loadCSS,
        loadResources,
        lazyLoadModule
    };
} else {
    // 浏览器环境
    window.LoadOnDemand = {
        loadScript,
        loadCSS,
        loadResources,
        lazyLoadModule
    };
}