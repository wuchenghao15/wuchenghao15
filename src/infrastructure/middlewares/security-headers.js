// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * 安全头部中间件
 * 添加安全相关的HTTP头部
 */
;
const securityHeaders = () => {
    return (req, res, next) => {
        // 设置安全头部
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-XSS-Protection', '1; mode=block');
        res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
        res.setHeader('Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'");
        res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
        res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
        
        // 继续处理请求
        next();
    };
};
;
module.exports = securityHeaders;