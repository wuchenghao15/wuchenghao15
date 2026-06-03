/**
 * 用户导航和退出管理模块
 * 统一处理所有页面的返回和退出逻辑
 */

(function() {
    'use strict';
    
    window.UserNavigation = {
        backToLogin: function() {
            if (!confirm('确定要返回登录页面吗？\n\n返回后将清除当前会话，但不会退出登录。')) {
                return;
            }
            
            const sessionData = {
                username: localStorage.getItem('mtcos_username'),
                userGroup: localStorage.getItem('mtcos_userGroup'),
                studentType: localStorage.getItem('mtcos_studentType'),
                grade: localStorage.getItem('mtcos_grade'),
                timestamp: new Date().toISOString()
            };
            
            localStorage.removeItem('mtcos_username');
            localStorage.removeItem('mtcos_userGroup');
            localStorage.removeItem('mtcos_studentType');
            localStorage.removeItem('mtcos_loggedIn');
            
            this.logOperation('back_to_login', sessionData, 'navigation');
            
            window.location.href = '../index.html';
        },
        
        logout: function() {
            const unfinishedExam = this.checkUnfinishedExam();
            const hasUnsavedProgress = this.checkUnsavedProgress();
            
            let message = '确定要退出登录吗？';
            if (unfinishedExam || hasUnsavedProgress) {
                message = '⚠️ 警告：您还有未完成的内容！\n\n';
                if (unfinishedExam) {
                    message += '• 存在未完成的考试\n';
                }
                if (hasUnsavedProgress) {
                    message += '• 存在未保存的答题进度\n';
                }
                message += '\n退出后将不会保存您的进度！';
            }
            
            if (!confirm(message)) {
                return;
            }
            
            const logoutData = {
                username: localStorage.getItem('mtcos_username'),
                userGroup: localStorage.getItem('mtcos_userGroup'),
                reason: unfinishedExam ? 'force_logout_with_unfinished_exam' : 
                       hasUnsavedProgress ? 'force_logout_with_unsaved_progress' : 'normal_logout',
                timestamp: new Date().toISOString()
            };
            
            this.clearAllUserData();
            
            this.logOperation('user_logout', logoutData, 'auth');
            
            alert('已成功退出登录！');
            window.location.href = '../index.html';
        },
        
        goBack: function(targetPage) {
            if (!confirm('确定要返回吗？')) {
                return;
            }
            
            const navigationData = {
                from: window.location.pathname,
                to: targetPage,
                username: localStorage.getItem('mtcos_username'),
                timestamp: new Date().toISOString()
            };
            
            this.logOperation('navigation', navigationData, 'navigation');
            
            if (targetPage) {
                window.location.href = targetPage;
            } else {
                window.history.back();
            }
        },
        
        clearAllUserData: function() {
            const allKeys = Object.keys(localStorage);
            const keysToRemove = allKeys.filter(key => key.startsWith('mtcos_'));
            
            keysToRemove.forEach(key => {
                localStorage.removeItem(key);
            });
            
            sessionStorage.clear();
        },
        
        checkUnfinishedExam: function() {
            const examProgress = localStorage.getItem('mtcos_examProgress');
            if (examProgress) {
                try {
                    const progress = JSON.parse(examProgress);
                    if (progress && progress.isActive && progress.remainingTime > 0) {
                        return true;
                    }
                } catch (e) {
                    console.error('Error parsing exam progress:', e);
                }
            }
            
            const examInterface = document.getElementById('exam-interface');
            if (examInterface && examInterface.style.display !== 'none') {
                return true;
            }
            
            return false;
        },
        
        checkUnsavedProgress: function() {
            const exerciseProgress = localStorage.getItem('mtcos_exerciseProgress');
            if (exerciseProgress) {
                try {
                    const progress = JSON.parse(exerciseProgress);
                    if (progress && Object.keys(progress).length > 0) {
                        return true;
                    }
                } catch (e) {
                    console.error('Error parsing exercise progress:', e);
                }
            }
            return false;
        },
        
        logOperation: function(operation, data, category) {
            try {
                const logData = {
                    operation: operation,
                    category: category,
                    data: data,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                };

                console.log('User Operation:', logData);

                if (typeof fetch === 'function') {
                    fetch('/api/logs', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(logData),
                        keepalive: true
                    }).then(function(response) {
                        if (!response.ok) {
                            console.warn('Log response not ok:', response.status);
                        }
                    }).catch(function(err) {
                        if (err.name !== 'AbortError') {
                            console.warn('Failed to log operation (non-critical):', err.message);
                        }
                    });
                }
            } catch (e) {
                console.warn('Error logging operation (non-critical):', e.message);
            }
        }
    };
    
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.UserNavigation;
    }
})();
