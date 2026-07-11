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
        // 用户管理功能
        document.addEventListener('DOMContentLoaded', function() {
            // 绑定用户管理事件
            bindUserManagementEvents();
        });
        function bindUserManagementEvents() {
            // 添加用户按钮
            const addUserBtn = document.getElementById('add-user-btn');
            if (addUserBtn) {
                addUserBtn.addEventListener('click', function() {
                    alert('添加用户功能开发中...');
                });
            }
            // 搜索按钮
            const searchBtn = document.querySelector('.search-btn');
            if (searchBtn) {
                searchBtn.addEventListener('click', function() {
                    performUserSearch();
                });
            }
            // 搜索输入框回车事件
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        performUserSearch();
                    }
                });
            }
            // 筛选按钮
            const filterBtn = document.querySelector('.filter-btn');
            if (filterBtn) {
                filterBtn.addEventListener('click', function() {
                    performUserFilter();
                });
            }
            // 查看用户按钮
            const viewBtns = document.querySelectorAll('.view-btn');
            viewBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    alert('查看用户详情功能开发中...');
                });
            });
            // 编辑用户按钮
            const editBtns = document.querySelectorAll('.edit-btn');
            editBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    alert('编辑用户功能开发中...');
                });
            });
            // 禁用用户按钮
            const disableBtns = document.querySelectorAll('.disable-btn');
            disableBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    if (confirm('确定要禁用该用户吗？')) {
                        alert('用户已禁用');
                        // 这里可以添加实际的禁用逻辑
                    }
                });
            });
            // 启用用户按钮
            const enableBtns = document.querySelectorAll('.enable-btn');
            enableBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    if (confirm('确定要启用该用户吗？')) {
                        alert('用户已启用');
                        // 这里可以添加实际的启用逻辑
                    }
                });
            });
            // 删除用户按钮
            const deleteBtns = document.querySelectorAll('.delete-btn');
            deleteBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    if (confirm('确定要删除该用户吗？此操作不可恢复！')) {
                        alert('用户已删除');
                        // 这里可以添加实际的删除逻辑
                    }
                });
            });
        }
        function performUserSearch() {
            const searchInput = document.querySelector('.search-input');
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            console.log('搜索用户:', searchTerm);
            // 这里可以添加实际的搜索逻辑
        }
        function performUserFilter() {
            const roleFilter = document.querySelector('.role-filter');
            const statusFilter = document.querySelector('.status-filter');
            const role = roleFilter ? roleFilter.value : 'all';
            const status = statusFilter ? statusFilter.value : 'all';
            console.log('筛选用户:', { role, status });
            // 这里可以添加实际的筛选逻辑
        }