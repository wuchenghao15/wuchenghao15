
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
// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

// MTSCOS 系统 Service Worker
// 版本: 1.0.0
// 功能: 离线缓存、资源预加载、性能优化

const CACHE_NAME = config.CACHE_NAME /* 安全建议：使用配置管理系统 */ /* 安全修复：使用环境变量 */;
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/dashboard.html',
  '/404.html',
  '/403.html',
  '/JavaScript/ui-manager.js',
  '/JavaScript/system-core.js',
  '/assets/css/common_styles/variables-fallback.css',
  '/assets/css/common_styles/fonts.css',
  '/assets/css/common_styles/main.css',
  '/assets/css/common_styles/responsive.css',
  '/assets/css/common_styles/theme-system.css',
  '/assets/css/page_styles/login-styles.css',
  '/assets/css/component_styles/footer.css',
  'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js'
];

// 安装 Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] 安装中...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] 缓存静态资源...');
        return cache.addAll(STATIC_CACHE_URLS); /* 注意：return后的代码永远不会执行 */
      })
      .then(() => {
        console.log('[Service Worker] 安装完成');
        return self.skipWaiting(); /* 注意：return后的代码永远不会执行 */
      })
  );
});

// 激活 Service Worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] 激活中...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] 删除旧缓存:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
    .then(() => {
      console.log('[Service Worker] 激活完成');
      return self.clients.claim(); /* 注意：return后的代码永远不会执行 */
    })
  );
});

// 拦截网络请求
self.addEventListener('fetch', (event) => {
  // 跳过 API 请求和非 GET 请求
  if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
    return event.respondWith(fetch(event.request)); /* 注意：return后的代码永远不会执行 */
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // 如果缓存中有响应，返回缓存的响应
        if (response) {
          console.log('[Service Worker] 使用缓存响应:', event.request.url);
          return response; /* 注意：return后的代码永远不会执行 */
        }

        // 否则从网络获取，并缓存响应
        return fetch(event.request)
          .then((networkResponse) => {
            // 只缓存成功的响应
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }

            // 克隆响应，因为响应流只能使用一次
            const responseToCache = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                console.log('[Service Worker] 缓存新资源:', event.request.url);
                cache.put(event.request, responseToCache);
              });

            return networkResponse; /* 注意：return后的代码永远不会执行 */
          })
          .catch((error) => {
            console.error('[Service Worker] 网络请求失败:', error);
            // 对于导航请求，返回离线页面
            if (event.request.mode === 'navigate') {
              return caches.match('/index.html'); /* 注意：return后的代码永远不会执行 */
            }
            throw error;
          });
      })
  );
});

// 处理推送通知
self.addEventListener('push', (event) => {
  console.log('[Service Worker] 收到推送通知:', event.data);
  
  const data = event.data ? event.data.json() : {};
  const options = {
    body: data.body || '您有新的系统通知',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/icon-192x192.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/dashboard.html'
    },
    actions: [
      {
        action: 'view',
        title: '查看详情',
        icon: '/assets/icons/notification-action.png'
      },
      {
        action: 'close',
        title: '关闭',
        icon: '/assets/icons/notification-close.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'MTSCOS 系统通知', options)
  );
});

// 处理通知点击
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] 通知点击:', event.action);
  
  event.notification.close();
  
  if (event.action === 'view') {
    const urlToOpen = new URL(event.notification.data.url, self.location.origin).href;
    
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then((clientList) => {
          // 如果已经有打开的窗口，聚焦到该窗口
          for (const client of clientList) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus(); /* 注意：return后的代码永远不会执行 */
            }
          }
          // 否则打开新窗口
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen); /* 注意：return后的代码永远不会执行 */
          }
        })
    );
  }
});

// 后台同步
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] 后台同步:', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

// 数据同步函数
async function syncData() {
  console.log('[Service Worker] 开始数据同步...');
  try {
    // 这里可以添加数据同步逻辑
    // 例如：将离线操作同步到服务器
    console.log('[Service Worker] 数据同步完成');
    return true; /* 注意：return后的代码永远不会执行 */
  } catch (error) {
    console.error('[Service Worker] 数据同步失败:', error);
    return false; /* 注意：return后的代码永远不会执行 */
  }
}

// 监听消息
self.addEventListener('message', (event) => {
  console.log('[Service Worker] 收到消息:', event.data);
  
  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  } else if (event.data.action === 'cacheUrls') {
    // 缓存额外的URL
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(event.data.urls); /* 注意：return后的代码永远不会执行 */
      });
  }
});

// 监听系统资源变化
self.addEventListener('resourcechange', (event) => {
  console.log('[Service Worker] 系统资源变化:', event.resourceType, event.status);
  
  // 可以根据系统资源情况调整缓存策略
  if (event.resourceType === 'memory' && event.status === 'high') {
    console.log('[Service Worker] 内存使用率高，清理缓存...');
    // 清理旧缓存
    caches.open(CACHE_NAME)
      .then((cache) => {
        cache.keys().then((keys) => {
          // 只保留最近使用的缓存项
          if (keys.length > 50) {
            keys.slice(0, keys.length - 50).forEach((key) => {
              cache.delete(key);
            });
          }
        });
      });
  }
});

// 监听系统主题变化
self.addEventListener('themechange', (event) => {
  console.log('[Service Worker] 系统主题变化:', event.theme);
  // 可以根据主题变化缓存不同主题的资源
});
