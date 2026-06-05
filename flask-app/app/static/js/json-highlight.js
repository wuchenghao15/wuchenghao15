/**
 * JSON语法高亮功能
 * 为pre标签中的JSON内容添加语法高亮
 */

(function() {
    'use strict';

    /**
     * 为JSON字符串添加语法高亮
     * @param {string} jsonString - 原始JSON字符串
     * @returns {string} - 带有HTML标记的高亮JSON字符串
     */
    function highlightJSON(jsonString) {
        try {
            // 解析JSON以确保格式正确
            const parsed = JSON.parse(jsonString);
            
            // 重新序列化并添加缩进
            const formatted = JSON.stringify(parsed, null, 2);
            
            // 语法高亮处理
            return formatted
                // 高亮键名
                .replace(/"([\w_\-]+)":/g, '<span class="json-key">"$1"</span>:')
                // 高亮字符串值
                .replace(/: "([^"]*)",?/g, ': <span class="json-string">"$1"</span>,')
                .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
                // 高亮数字
                .replace(/: (\d+\.?\d*),?/g, ': <span class="json-number">$1</span>,')
                // 高亮布尔值
                .replace(/: (true|false),?/g, ': <span class="json-boolean">$1</span>,')
                // 高亮null
                .replace(/: null,?/g, ': <span class="json-null">null</span>,')
                // 高亮错误信息
                .replace(/"error": <span class="json-string">"([^"]*)"<\/span>/g, '<span class="json-key">"error"</span>: <span class="json-string json-error">"$1"</span>');
        } catch (e) {
            // 如果JSON格式错误，返回原始字符串
            console.warn('Invalid JSON format for highlighting:', e);
            return jsonString;
        }
    }

    /**
     * 处理所有pre标签，为JSON内容添加高亮
     */
    function processPreTags() {
        const preElements = document.querySelectorAll('pre');
        
        preElements.forEach(pre => {
            // 检查是否包含JSON内容
            const textContent = pre.textContent;
            if (textContent.trim().startsWith('{') && textContent.trim().endsWith('}') ||
                textContent.trim().startsWith('[') && textContent.trim().endsWith(']')) {
                
                // 检查是否已经处理过
                if (!pre.classList.contains('json-highlighted')) {
                    try {
                        // 添加高亮处理
                        const highlighted = highlightJSON(textContent);
                        const code = document.createElement('code');
                        code.innerHTML = highlighted;
                        
                        // 替换内容
                        pre.innerHTML = '';
                        pre.appendChild(code);
                        
                        // 添加处理标记
                        pre.classList.add('json-highlighted');
                        
                        // 添加复制按钮
                        addCopyButton(pre);
                    } catch (e) {
                        console.error('Error processing pre tag:', e);
                    }
                }
            }
        });
    }

    /**
     * 为pre标签添加复制按钮
     * @param {HTMLElement} pre - pre元素
     */
    function addCopyButton(pre) {
        const copyButton = document.createElement('button');
        copyButton.textContent = '复制';
        copyButton.className = 'json-copy-btn';
        copyButton.title = '复制JSON内容';
        
        // 按钮样式
        copyButton.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 6px 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 10;
        `;
        
        // 悬停显示按钮
        pre.style.position = 'relative';
        pre.addEventListener('mouseenter', () => {
            copyButton.style.opacity = '1';
        });
        pre.addEventListener('mouseleave', () => {
            copyButton.style.opacity = '0';
        });
        
        // 复制功能
        copyButton.addEventListener('click', () => {
            const textContent = pre.textContent;
            navigator.clipboard.writeText(textContent).then(() => {
                copyButton.textContent = '已复制!';
                setTimeout(() => {
                    copyButton.textContent = '复制';
                }, 2000);
            }).catch(err => {
                console.error('复制失败:', err);
                copyButton.textContent = '复制失败';
                setTimeout(() => {
                    copyButton.textContent = '复制';
                }, 2000);
            });
        });
        
        pre.appendChild(copyButton);
    }

    /**
     * 初始化函数
     */
    function init() {
        // 页面加载完成后处理
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', processPreTags);
        } else {
            processPreTags();
        }
        
        // 监听动态内容变化
        const observer = new MutationObserver(processPreTags);
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 初始化
    init();

})();
