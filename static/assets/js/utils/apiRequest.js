/**
 * 统一 API 请求封装
 * 提供标准化的请求、错误处理和响应解析
 */
const ApiRequest = (function() {
    const DEFAULT_TIMEOUT = 30000;
    let _toastContainer = null;

    function _ensureToastContainer() {
        if (!_toastContainer) {
            _toastContainer = document.createElement('div');
            _toastContainer.id = 'api-toast-container';
            _toastContainer.style.cssText = 'position:fixed;top:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:10px;';
            document.body.appendChild(_toastContainer);
        }
        return _toastContainer;
    }

    function showToast(message, type = 'info', duration = 3000) {
        const container = _ensureToastContainer();
        const toast = document.createElement('div');
        const bgColors = {
            success: 'linear-gradient(135deg, #10b981, #059669)',
            error: 'linear-gradient(135deg, #ef4444, #dc2626)',
            warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
            info: 'linear-gradient(135deg, #3b82f6, #2563eb)'
        };
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        toast.style.cssText = `
            background: ${bgColors[type] || bgColors.info};
            color: white;
            padding: 14px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            font-size: 14px;
            font-weight: 500;
            min-width: 250px;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
            cursor: pointer;
        `;
        toast.innerHTML = `<span style="font-size:18px;">${icons[type] || icons.info}</span><span>${message}</span>`;

        const style = document.getElementById('api-toast-style');
        if (!style) {
            const s = document.createElement('style');
            s.id = 'api-toast-style';
            s.textContent = `
                @keyframes slideIn { from { transform: translateX(120%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
                @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(120%); opacity: 0; } }
            `;
            document.head.appendChild(s);
        }

        container.appendChild(toast);
        toast.addEventListener('click', () => remove());

        let timer = null;
        function remove() {
            if (timer) clearTimeout(timer);
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }
        timer = setTimeout(remove, duration);
    }

    function _getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    function _handleResponse(response) {
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            return response.json().then(data => {
                if (!response.ok) {
                    const error = new Error(data.message || data.error || `请求失败 (${response.status})`);
                    error.status = response.status;
                    error.data = data;
                    throw error;
                }
                return data;
            });
        }
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            throw error;
        }
        return response.text();
    }

    function request(url, options = {}) {
        const {
            method = 'GET',
            data = null,
            headers = {},
            timeout = DEFAULT_TIMEOUT,
            showErrorToast = true,
            showSuccessToast = false,
            successMessage = '',
            credentials = 'same-origin'
        } = options;

        const config = {
            method,
            credentials,
            headers: {
                'Accept': 'application/json',
                ...headers
            }
        };

        const csrfToken = _getCsrfToken();
        if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }

        if (data !== null) {
            if (data instanceof FormData) {
                config.body = data;
            } else {
                config.headers['Content-Type'] = 'application/json';
                config.body = JSON.stringify(data);
            }
        }

        const controller = new AbortController();
        config.signal = controller.signal;
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        return fetch(url, config)
            .then(_handleResponse)
            .then(result => {
                if (showSuccessToast && result && result.success) {
                    showToast(successMessage || result.message || '操作成功', 'success');
                }
                return result;
            })
            .catch(error => {
                if (error.name === 'AbortError') {
                    error = new Error('请求超时，请检查网络后重试');
                    error.code = 'TIMEOUT';
                }
                if (showErrorToast) {
                    showToast(error.message || '网络错误，请重试', 'error');
                }
                throw error;
            })
            .finally(() => {
                clearTimeout(timeoutId);
            });
    }

    return {
        request,
        showToast,
        get: (url, options = {}) => request(url, { ...options, method: 'GET' }),
        post: (url, data, options = {}) => request(url, { ...options, method: 'POST', data }),
        put: (url, data, options = {}) => request(url, { ...options, method: 'PUT', data }),
        delete: (url, options = {}) => request(url, { ...options, method: 'DELETE' }),
        patch: (url, data, options = {}) => request(url, { ...options, method: 'PATCH', data })
    };
})();

if (typeof window !== "undefined") {
    window.ApiRequest = ApiRequest;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiRequest;
}
