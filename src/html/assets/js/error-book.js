// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
// 兼容性检查和回退方案
(function() {
    'use strict';
    // 检查Array.includes支持
    if (!Array.prototype.includes) {
        Array.prototype.includes = function(searchElement, fromIndex) {
            fromIndex = parseInt(fromIndex) || 0;
            for (let i = fromIndex; i < this.length; i++) {
                if (this[i] === searchElement) {
                    return true;
                }
            }
            return false;
        };
    }
})();
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            initializeErrorBook();
        });
        // 初始化错题本
        function initializeErrorBook() {
            if (window.errorBookManager) {
                updateStatistics();
                updateErrorList();
                updateAISuggestions();
                setupEventListeners();
            } else {
                setTimeout(initializeErrorBook, 100);
            }
        }
        // 更新统计信息
        function updateStatistics() {
            const stats = window.errorBookManager.getStatistics();
            const totalErrors = stats.totalErrors;
            document.getElementById('total-errors').textContent = totalErrors;
            // 最易错题类型
            const errorTypes = Object.entries(stats.errorsByType);
            if (errorTypes.length > 0) {
                const mostErrorType = errorTypes.sort((a, b) => b[1] - a[1])[0];
                document.getElementById('most-error-type').textContent = `${mostErrorType[0]} (${mostErrorType[1]}题)`;
            } else {
                document.getElementById('most-error-type').textContent = '-';
            }
            // 最易错题级别
            const errorLevels = Object.entries(stats.errorsByLevel);
            if (errorLevels.length > 0) {
                const mostErrorLevel = errorLevels.sort((a, b) => b[1] - a[1])[0];
                document.getElementById('most-error-level').textContent = `${mostErrorLevel[0]} (${mostErrorLevel[1]}题)`;
            } else {
                document.getElementById('most-error-level').textContent = '-';
            }
            // 已复习次数
            const reviewCount = stats.errorList.reduce((sum, error) => sum + error.reviewCount, 0);
            document.getElementById('review-count').textContent = reviewCount;
        }
        // 更新AI建议
        function updateAISuggestions() {
            const suggestions = window.errorBookManager.generateAISuggestions();
            const suggestionsList = document.getElementById('suggestions-list');
            if (suggestions.suggestions.length > 0) {
                suggestionsList.innerHTML = '';
                suggestions.suggestions.forEach(suggestion => {
                    const suggestionItem = document.createElement('div');
                    suggestionItem.className = 'suggestion-item';
                    suggestionItem.innerHTML = `
                        <span class="suggestion-priority priority-${suggestion.priority}">${suggestion.priority === 'high' ? '高' : suggestion.priority === 'medium' ? '中' : '低'}</span>
                        ${suggestion.content}
                    `;
                    suggestionsList.appendChild(suggestionItem);
                });
            } else {
                suggestionsList.innerHTML = `
                    <div class="empty-state">
                        <i>📈</i>
                        <h3>暂无分析数据</h3>
                        <p>完成一些练习后，AI将为您提供个性化分析和建议</p>
                    </div>
                `;
            }
        }
        // 更新错题列表
        function updateErrorList(filter = 'all') {
            const allErrors = window.errorBookManager.getAllErrors();
            const errorList = document.getElementById('error-list');
            if (allErrors.length === 0) {
                errorList.innerHTML = `
                    <div class="empty-state">
                        <i>📚</i>
                        <h3>暂无错题记录</h3>
                        <p>完成练习后，错题将自动添加到这里</p>
                    </div>
                `;
                return;
            }
            // 过滤错题
            let filteredErrors = allErrors;
            if (filter !== 'all') {
                filteredErrors = allErrors.filter(error => 
                    error.type === filter || error.level === filter
                );
            }
            if (filteredErrors.length === 0) {
                errorList.innerHTML = `
                    <div class="empty-state">
                        <i>🔍</i>
                        <h3>没有符合条件的错题</h3>
                        <p>尝试选择其他过滤条件</p>
                    </div>
                `;
                return;
            }
            // 渲染错题列表
            errorList.innerHTML = filteredErrors.map(error => {
                const optionsHtml = error.options.map((option, index) => {
                    let className = 'option';
                    if (index === error.userAnswer) className += ' user-answer';
                    if (index === error.correctAnswer) className += ' correct-answer';
                    return `
                        <div class="${className}">
                            ${String.fromCharCode(65 + index)}. ${option}
                        </div>
                    `;
                }).join('');
                const tagsHtml = error.tags.map(tag => `<span class="tag">${tag}</span>`).join('');
                return `
                    <div class="error-item" data-type="${error.type}" data-level="${error.level}">
                        <div class="error-header">
                            <div class="error-meta">
                                <span>📋 ${error.type}</span>
                                <span>🎯 ${error.level}</span>
                                <span>📅 ${new Date(error.recordedAt).toLocaleDateString()}</span>
                                <span>🔄 复习 ${error.reviewCount} 次</span>
                            </div>
                        </div>
                        <div class="error-question">${error.question}</div>
                        <div class="error-options">${optionsHtml}</div>
                        ${error.tags.length > 0 ? `<div class="tags-container">${tagsHtml}</div>` : ''}
                        <div class="error-explanation">
                            <strong>解析：</strong>${error.explanation}
                        </div>
                        <div class="error-actions">
                            <button class="btn btn-success" onclick="markAsReviewed('${error.id}')">标记为已复习</button>
                            <button class="btn btn-danger" onclick="deleteError('${error.id}')">删除</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
        // 设置事件监听器
        function setupEventListeners() {
            // 过滤按钮
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    updateErrorList(this.dataset.filter);
                });
            });
            // 导出按钮
            document.getElementById('export-btn').addEventListener('click', function() {
                window.errorBookManager.exportErrorBook();
            });
            // 刷新按钮
            document.getElementById('refresh-btn').addEventListener('click', function() {
                updateStatistics();
                updateErrorList();
                updateAISuggestions();
                alert('数据已刷新');
            });
            // 清空按钮
            document.getElementById('clear-btn').addEventListener('click', function() {
                if (confirm('确定要清空错题本吗？此操作不可恢复。')) {
                    window.errorBookManager.clearErrorBook();
                    updateStatistics();
                    updateErrorList();
                    updateAISuggestions();
                    alert('错题本已清空');
                }
            });
            // 监听错题添加事件
            window.addEventListener('error_added', function() {
                updateStatistics();
                updateErrorList();
                updateAISuggestions();
            });
        }
        // 标记为已复习
        function markAsReviewed(errorId) {
            if (window.errorBookManager.markAsReviewed(errorId)) {
                updateStatistics();
                updateErrorList();
                alert('已标记为已复习');
            }
        }
        // 删除错题
        function deleteError(errorId) {
            if (confirm('确定要删除这道错题吗？')) {
                if (window.errorBookManager.deleteError(errorId)) {
                    updateStatistics();
                    updateErrorList();
                    updateAISuggestions();
                    alert('错题已删除');
                }
            }
        }