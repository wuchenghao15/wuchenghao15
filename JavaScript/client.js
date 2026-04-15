// 客户端JavaScript

// HTTP错误处理函数
function fetchErrorHandler(response) {
    if (!response.ok) {
        if (response.status === 404) {
            console.error('资源未找到 (404)');
            // 可以在这里添加重定向到404页面的逻辑
            // window.location.href = '/HTML/404.html';
        } else if (response.status === 403) {
            console.error('访问被拒绝 (403)');
            // 可以在这里添加重定向到403页面的逻辑
            // window.location.href = '/HTML/403.html';
        } else {
            console.error('HTTP错误: ' + response.status);
        };

        throw new Error('HTTP错误: ' + response.status);
    };

    return response;
};


// 覆盖原生fetch以添加错误处理
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments)
        .then(fetchErrorHandler);
};
const testButton = document.getElementById('testButton');
const resultDiv = document.getElementById('result');

testButton.addEventListener('click', async () => {
    try {
        resultDiv.textContent = '正在连接...';
        resultDiv.className = '';

        const response = await fetch('/api/status');
        const data = await response.json();

        resultDiv.textContent = ;
        resultDiv.className = 'success';
    } catch (error) {
        resultDiv.textContent = ;
        resultDiv.className = 'error';
    }
});
