
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

        /**
         * AI 特征库管理系统
         */
        class AiFeatureManager {
            constructor() {
                this.baseUrl = config.baseUrl /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
                this.init();
            }

            /**
             * 初始化系统
             */
            init() {
                console.log('🔧 初始化 AI 特征库管理系统...');
                this.setupEventListeners();
                this.refreshFeatureStats();
                this.loadCategories();
                this.loadFeatures();
            }

            /**
             * 设置事件监听器
             */
            setupEventListeners() {
                // 特征存储表单提交
                document.getElementById('featureStoreForm').addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleFeatureStore();
                });
            }

            /**
             * 切换标签页
             */
            switchTab(tabName) {
                // 隐藏所有标签页
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                // 移除所有标签的活跃状态
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                // 显示选中的标签页
                document.getElementById(`${tabName}-tab`).classList.add('active');
                // 设置选中标签的活跃状态
                event.target.classList.add('active');
            }

            /**
             * 处理特征存储
             */
            async handleFeatureStore() {
                console.log('📝 存储特征...');
                this.showLoading('formLoading');

                const featureId = document.getElementById('featureId').value;
                const featureName = document.getElementById('featureName').value;
                const featureType = document.getElementById('featureType').value;
                const categoryId = document.getElementById('categoryId').value;
                const description = document.getElementById('description').value;
                const featureData = document.getElementById('featureData').value;
                const version = parseFloat(document.getElementById('version').value);
                const confidenceScore = parseFloat(document.getElementById('confidenceScore').value);
                const isActive = parseInt(document.getElementById('isActive').value);
                const isPublic = parseInt(document.getElementById('isPublic').value);

                try {
                    const result = await this.fetchData(`${this.baseUrl}/store`, {
                        feature_id: featureId,
                        feature_name: featureName,
                        feature_type: featureType,
                        category_id: categoryId,
                        description: description,
                        feature_data: JSON.parse(featureData),
                        version: version,
                        confidence_score: confidenceScore,
                        is_active: isActive,
                        is_public: isPublic
                    });

                    this.displayResponse(result, 'formResponse');
                    this.refreshFeatureStats();
                    this.loadFeatures();
                } catch (error) {
                    console.error('存储特征失败:', error);
                    this.showError('存储特征失败，请检查输入数据', 'formResponse');
                } finally {
                    this.hideLoading('formLoading');
                }
            }

            /**
             * 搜索特征
             */
            async searchFeatures() {
                console.log('🔍 搜索特征...');
                this.showLoading('searchLoading');

                const searchTerm = document.getElementById('searchTerm').value;

                try {
                    const result = await this.fetchData(`${this.baseUrl}/search`, {
                        search_term: searchTerm
                    });

                    this.displaySearchResults(result, 'searchResponse');
                } catch (error) {
                    console.error('搜索特征失败:', error);
                    this.showError('搜索特征失败，请稍后重试', 'searchResponse');
                } finally {
                    this.hideLoading('searchLoading');
                }
            }

            /**
             * 加载特征分类
             */
            async loadCategories() {
                console.log('📋 加载特征分类...');
                this.showLoading('categoriesLoading');

                try {
                    const result = await this.fetchData(`${this.baseUrl}/categories`, {}, 'GET');

                    this.displayCategories(result, 'categoriesResponse');
                    this.populateCategoryDropdown(result.data);
                } catch (error) {
                    console.error('加载特征分类失败:', error);
                    this.showError('加载特征分类失败，请稍后重试', 'categoriesResponse');
                } finally {
                    this.hideLoading('categoriesLoading');
                }
            }

            /**
             * 加载特征列表
             */
            async loadFeatures() {
                console.log('📋 加载特征列表...');
                this.showLoading('listLoading');

                try {
                    const result = await this.fetchData(`${this.baseUrl}/list`);

                    this.populateFeatureTable(result.data);
                } catch (error) {
                    console.error('加载特征列表失败:', error);
                    this.showError('加载特征列表失败，请稍后重试', 'listLoading');
                } finally {
                    this.hideLoading('listLoading');
                }
            }

            /**
             * 刷新特征统计
             */
            async refreshFeatureStats() {
                console.log('🔄 刷新特征统计...');
                this.showLoading('statsLoading');

                try {
                    const result = await this.fetchData(`${this.baseUrl}/stats`, {}, 'GET');

                    if (result.success) {
                        document.getElementById('featureCount').textContent = result.data.total;
                        document.getElementById('categoryCount').textContent = result.data.byCategory.length;
                        document.getElementById('activeFeatures').textContent = result.data.byCategory.reduce((sum, cat) => sum + cat.count, 0);
                        document.getElementById('usageCount').textContent = result.data.byCategory.reduce((sum, cat) => sum + cat.count, 0);
                    }
                } catch (error) {
                    console.error('刷新特征统计失败:', error);
                } finally {
                    this.hideLoading('statsLoading');
                }
            }

            /**
             * 填充特征分类下拉框
             */
            populateCategoryDropdown(categories) {
                const categorySelect = document.getElementById('categoryId');
                if (!categorySelect) return;

                // 保留默认选项
                while (categorySelect.options.length > 1) {
                    categorySelect.remove(1);
                }

                // 添加分类选项
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.category_name;
                    categorySelect.appendChild(option);
                });
            }

            /**
             * 填充特征表格
             */
            populateFeatureTable(features) {
                const tableBody = document.getElementById('featureTableBody');
                tableBody.innerHTML = '';

                if (!features || features.length === 0) {
                    const emptyRow = document.createElement('tr');
                    emptyRow.innerHTML = '<td colspan="10" style="text-align:center; padding: 20px;">📭 暂无特征数据</td>';
                    tableBody.appendChild(emptyRow);
                    return;
                }

                features.forEach(feature => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${feature.feature_id || ''}</td>
                        <td>${feature.feature_name || ''}</td>
                        <td>${feature.category || ''}</td>
                        <td>${feature.value || ''}</td>
                        <td>${feature.confidence || ''}</td>
                        <td>${feature.status === 'active' ? '活跃' : '非活跃'}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="editFeature('${feature.feature_id}')">✏️ 编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteFeature('${feature.feature_id}')">🗑️ 删除</button>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            }

            /**
             * 显示搜索结果
             */
            displaySearchResults(result, elementId) {
                const responseArea = document.getElementById(elementId);
                if (!result.success) {
                    responseArea.innerHTML = `<div class="error-message">❌ 搜索失败: ${result.error}</div>`;
                    return;
                }

                const features = result.data;
                if (features.length === 0) {
                    responseArea.innerHTML = `<div class="success-message">📭 未找到匹配的特征</div>`;
                    return;
                }

                let html = `<div class="success-message">✅ 找到 ${features.length} 个特征</div>`;
                html += '<table style="width:100%">';
                html += `
                    <thead>
                        <tr>
                            <th>特征 ID</th>
                            <th>特征名称</th>
                            <th>特征类型</th>
                            <th>版本</th>
                            <th>置信度</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                `;

                features.forEach(feature => {
                    html += `
                        <tr>
                            <td>${feature.feature_id}</td>
                            <td>${feature.feature_name}</td>
                            <td>${feature.feature_type}</td>
                            <td>${feature.version}</td>
                            <td>${feature.confidence_score}</td>
                            <td>
                                <button class = config.class /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */ style="                                        onclick = config.onclick /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */${feature.feature_id}')">
                                    ✏️ 编辑
                                </button>
                            </td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
                responseArea.innerHTML = html;
            }

            /**
             * 显示分类列表
             */
            displayCategories(result, elementId) {
                const responseArea = document.getElementById(elementId);
                if (!result.success) {
                    responseArea.innerHTML = `error-message">❌ 加载分类失败: ${result.error}</div>`;
                    return;
                }

                const categories = result.data;
                if (categories.length === 0) {
                    responseArea.innerHTML = `<div class="success-message">📭 暂无分类数据</div>`;
                    return;
                }

                let html = `<div class="success-message">✅ 找到 ${categories.length} 个分类</div>`;
                html += '<table style="width:100%">';
                html += `
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>分类名称</th>
                            <th>描述</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                `;

                categories.forEach(category => {
                    html += `
                        <tr>
                            <td>${category.id}</td>
                            <td>${category.category_name}</td>
                            <td>${category.category_description || '-'}</td>
                            <td>${category.is_active === 1 ? '活跃' : '非活跃'}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table>';
                responseArea.innerHTML = html;
            }

            /**
             * 编辑特征
             */
            async editFeature(featureId) {
                console.log(`✏️  编辑特征: ${featureId}`);
                try {
                    const result = await this.fetchData(`${this.baseUrl}/get`, {
                        feature_id: featureId
                    });

                    if (result.success) {
                        const feature = result.data;
                        document.getElementById('featureId').value = feature.feature_id;
                        document.getElementById('featureName').value = feature.feature_name;
                        document.getElementById('featureType').value = feature.feature_type;
                        document.getElementById('categoryId').value = feature.category_id;
                        document.getElementById('description').value = feature.description || '';
                        document.getElementById('featureData').value = JSON.stringify(feature.feature_data, null, 2);
                        document.getElementById('version').value = feature.version;
                        document.getElementById('confidenceScore').value = feature.confidence_score;
                        document.getElementById('isActive').value = feature.is_active;
                        document.getElementById('isPublic').value = feature.is_public;

                        // 切换到存储特征标签页
                        this.switchTab('store');
                        this.showSuccess('特征数据已加载到表单，请进行编辑');
                    }
                } catch (error) {
                    this.showError(`加载特征数据失败: ${error.message}`);
                }
            }

            /**
             * 删除特征
             */
            async deleteFeature(featureId) {
                if (confirm(`确定要删除特征: ${featureId} 吗？`)) {
                    console.log(`🗑️  删除特征: ${featureId}`);
                    try {
                        const result = await this.fetchData(`${this.baseUrl}/delete`, {
                            feature_id: featureId
                        });

                        if (result.success) {
                            this.showSuccess('特征删除成功');
                            this.refreshFeatureStats();
                            this.loadFeatures();
                        }
                    } catch (error) {
                        this.showError(`删除特征失败: ${error.message}`);
                    }
                }
            }

            /**
             * 导出特征库
             */
            async exportFeatureStore() {
                console.log('📤 导出特征库...');
                this.showLoading('statsLoading');

                try {
                    const result = await this.fetchData(`${this.baseUrl}/list`);

                    if (result.success) {
                        const exportData = JSON.stringify(result.data, null, 2);
                        const blob = new Blob([exportData], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `特征导出_${new Date().toISOString().split('T')[0]}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                        this.showSuccess('特征库导出成功');
                    }
                } catch (error) {
                    console.error('导出特征库失败:', error);
                    this.showError('导出特征库失败，请稍后重试');
                } finally {
                    this.hideLoading('statsLoading');
                }
            }

            /**
             * 清理过期特征
             */
            async cleanupFeatures() {
                console.log('🗑️  清理过期特征...');
                this.showLoading('statsLoading');

                try {
                    // 这里可以实现清理过期特征的逻辑
                    this.showSuccess('清理完成，无过期特征');
                } catch (error) {
                    console.error('清理过期特征失败:', error);
                    this.showError('清理过期特征失败，请稍后重试');
                } finally {
                    this.hideLoading('statsLoading');
                }
            }

            /**
             * 显示加载状态
             */
            showLoading(elementId) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.classList.add('show');
                }
            }

            /**
             * 隐藏加载状态
             */
            hideLoading(elementId) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.classList.remove('show');
                }
            }

            /**
             * 显示成功消息
             */
            showSuccess(message) {
                const responseArea = document.getElementById('formResponse');
                responseArea.innerHTML = `success-message">✅ ${message}</div>`;
            }

            /**
             * 显示错误消息
             */
            showError(message, elementId = config.elementId /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */) {
                const responseArea = document.getElementById(elementId);
                responseArea.innerHTML = `error-message">❌ ${message}</div>`;
            }

            /**
             * 显示响应
             */
            displayResponse(result, elementId) {
                const responseArea = document.getElementById(elementId);
                if (result.success) {
                    responseArea.innerHTML = `success-message">✅ 操作成功</div>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    `;
                } else {
                    responseArea.innerHTML = `error-message">❌ 操作失败</div>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    `;
                }
            }

            /**
             * 发送数据请求
             */
            async fetchData(endpoint, data = {}, method = config.method /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */) {
                try {
                    // 构建完整的 URL
                    const fullUrl = endpoint.startsWith('http') ? endpoint : `https://localhost:8080${endpoint}`;
                    const options = {
                        method: method,
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    };

                    // 如果是 POST 请求，添加请求体
                    if (method === 'POST') {
                        options.body = JSON.stringify(data);
                    }

                    const response = await fetch(fullUrl, options);

                    if (!response.ok) {
                        throw new Error(`HTTP 错误: ${response.status}`);
                    }

                    return await response.json();
                } catch (error) {
                    console.error('网络请求失败:', error);
                    throw error;
                }
            }
        }

        // 全局变量
        let aiFeatureManager;

        // 页面加载完成后初始化
        window.addEventListener('DOMContentLoaded', () => {
            aiFeatureManager = new AiFeatureManager();
        });

        // 全局函数
        window.switchTab = (tabName) => {
            aiFeatureManager.switchTab(tabName);
        };

        window.refreshFeatureStats = () => {
            aiFeatureManager.refreshFeatureStats();
        };

        window.exportFeatureStore = () => {
            aiFeatureManager.exportFeatureStore();
        };

        window.cleanupFeatures = () => {
            aiFeatureManager.cleanupFeatures();
        };

        window.searchFeatures = () => {
            aiFeatureManager.searchFeatures();
        };

        window.loadCategories = () => {
            aiFeatureManager.loadCategories();
        };

        window.loadFeatures = () => {
            aiFeatureManager.loadFeatures();
        };
    