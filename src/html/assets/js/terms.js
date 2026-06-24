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
        // 协议同意逻辑
// // //         const agreeTermsCheckbox = document.getElementById('agreeTerms');   
// // //         const continueBtn = document.getElementById('continueBtn');   
        // 监听复选框变化
        agreeTermsCheckbox.addEventListener('change', function() {
            continueBtn.disabled = !this.checked;
        });
        // 继续注册按钮点击事件
        continueBtn.addEventListener('click', function() {
            if (agreeTermsCheckbox.checked) { {
} /* 代码质量修复：添加花括号 */
                // 存储同意状态到localStorage
                localStorage.setItem('termsAgreed', 'true');
                // 跳转到注册页面
                window.location.href = config.href  ;
            }
        });