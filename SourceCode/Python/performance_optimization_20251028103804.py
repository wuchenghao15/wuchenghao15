# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:16
#!/usr/bin/env python3
import os
import re
import shutil
import gzip
import time
import subprocess
from datetime import datetime

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# 部署目录
DEPLOY_DIR = os.path.join(ROOT_DIR, 'Deployment', 'deploy_site')

# 日志文件
LOG_FILE = os.path.join(ROOT_DIR, 'Logs', f'performance_optimization_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log')

class Logger:
    """日志记录类"""
    @staticmethod
    def log(message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] [{level}] {message}'
        print(log_message)
        # 确保日志目录存在
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        # 写入日志文件
        with open(LOG_FILE, 'a') as f:
            f.write(log_message + '\n')

    def info(message):
        Logger.log(message, "INFO")

    def error(message):
        Logger.log(message, "ERROR")

    def success(message):
        Logger.log(message, "SUCCESS")

class PerformanceOptimizer:
    """性能优化工具类"""

    def minify_css(css_content):
        """高级CSS压缩"""
        # 移除注释
        css = re.sub(r'\/\*[^*]*\*+(?:[^/*][^*]*\*+)*\/', '', css_content)
        # 移除多余的空白字符
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r'\s*{\s*', '{', css)
        css = re.sub(r'\s*}\s*', '}', css)
        css = re.sub(r'\s*:\s*', ':', css)
        css = re.sub(r'\s*;\s*', ';', css)
        css = re.sub(r'\s*,\s*', ',', css)
        # 移除最后一个分号
        css = re.sub(r';\s*}', '}', css)
        # 压缩颜色值
        css = re.sub(r'#([0-9a-fA-F])\1([0-9a-fA-F])\2([0-9a-fA-F])\3', r'#\1\2\3', css)
        # 移除单位为0的值
        css = re.sub(r'0px|0em|0%|0pt', '0', css)
        return css.strip()

    def minify_js(js_content):
        """高级JavaScript压缩"""
        # 移除多行注释
        js = re.sub(r'\/\*[\s\S]*?\*\/', '', js_content)
        # 移除单行注释，但保留URL中的//
        js = re.sub(r'(?<!http:)\/\/.*$', '', js, flags=re.MULTILINE)
        # 移除多余的空白字符
        js = re.sub(r'\n\s*', '\n', js)
        js = re.sub(r'\s+', ' ', js)
        js = re.sub(r'\s*{\s*', '{', js)
        js = re.sub(r'\s*}\s*', '}', js)
        js = re.sub(r'\s*;\s*', ';', js)
        js = re.sub(r'\s*,\s*', ',', js)
        # 移除空行
        js = re.sub(r'\n\s*\n', '\n', js)
        return js.strip()

    def gzip_compress(file_path):
        """对文件进行gzip压缩"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # 只有当压缩能带来至少10%的空间节省时才压缩
            compressed = gzip.compress(content, compresslevel=9)
            if len(compressed) < len(content) * 0.9:
                gzip_path = file_path + '.gz'
                with open(gzip_path, 'wb') as f:
                    f.write(compressed)
                Logger.info(f'已gzip压缩: {os.path.basename(file_path)} ({len(content)} -> {len(compressed)} 字节)')
                return True
            return False
        except Exception as e:
            Logger.error(f'gzip压缩文件 {file_path} 失败: {str(e)}')
            return False

    def optimize_images(directory):
        """优化图片文件（使用系统工具）"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        optimized_count = 0

            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        # 检查是否已安装图片优化工具
                        if shutil.which('jpegoptim') and file.lower().endswith(('.jpg', '.jpeg')):
                            subprocess.run(['jpegoptim', '--strip-all', '--max=90', file_path], check=True, capture_output=True)
                            optimized_count += 1
                        elif shutil.which('optipng') and file.lower().endswith('.png'):
                            subprocess.run(['optipng', '-o2', file_path], check=True, capture_output=True)
                            optimized_count += 1
                            Logger.info(f'未找到图片优化工具，跳过: {file}')
                    except Exception as e:
                        Logger.error(f'优化图片 {file} 失败: {str(e)}')

        return optimized_count

    def add_caching_headers(html_file):
        """在HTML文件中添加缓存控制meta标签"""
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 检查是否已存在缓存控制meta标签
            if 'http-equiv="Cache-Control"' not in content:
                # 在head标签中添加缓存控制meta标签
                cache_meta = '<meta http-equiv="Cache-Control" content="max-age=31536000, public">\n    <meta http-equiv="Expires" content="Wed, 21 Oct 2027 07:28:00 GMT">'
                updated_content = re.sub(r'<head>\s*', f'<head>\n    {cache_meta}', content, flags=re.MULTILINE)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)

                return True
            return False
        except Exception as e:
            Logger.error(f'添加缓存控制meta标签到 {html_file} 失败: {str(e)}')
            return False

    def add_defer_to_scripts(html_file):
        """为非关键JavaScript添加defer属性"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            updated_content = re.sub(r'<script\s+(?!src="[^"]*anti_hotlink[^"]*"\s*)(?!defer\s*)(?!async\s*)(?=src=)', '<script defer ', content)
            if content != updated_content:
                with open(html_file, 'w', encoding='utf-8') as f:
            return False
        except Exception as e:
            Logger.error(f'为脚本添加defer属性到 {html_file} 失败: {str(e)}')

    def preload_critical_resources(html_file):
        """预加载关键资源"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            critical_css = re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+\.css)"', content)
            critical_js = re.findall(r'<script\s+src="([^"]+\.js)"', content)
            # 创建预加载标签
            preloads = []

            for js in critical_js[:2]:  # 只预加载前2个JS
                    preloads.append(f'<link rel="preload" href="{js}" as="script">')
                updated_content = re.sub(r'<head>\s*', f'<head>\n    {preload_tags}', content, flags=re.MULTILINE)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                Logger.info(f'已添加资源预加载标签: {os.path.basename(html_file)}')
                return True
            return False
        except Exception as e:
            Logger.error(f'添加资源预加载标签到 {html_file} 失败: {str(e)}')
            return False

        """为图片添加懒加载属性"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 为图片添加loading="lazy"属性
            updated_content = re.sub(r'<img\s+(?!loading=)', '<img loading="lazy" ', content)

            if content != updated_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                return True
        except Exception as e:
            Logger.error(f'为图片添加懒加载属性到 {html_file} 失败: {str(e)}')

    def compress_all_resources(deploy_dir):
            'css_files': 0,
            'js_files': 0,
            'compressed_css': 0,
            'compressed_js': 0,
            'html_optimized': 0

        # 遍历部署目录
            for file in files:
                file_path = os.path.join(root, file)
                # 处理CSS文件
                if file.endswith('.css') and not file.endswith('.min.css'):
                    stats['css_files'] += 1
                    try:
                            css_content = f.read()
                        minified = PerformanceOptimizer.minify_css(css_content)
                        min_path = file_path.replace('.css', '.min.css')

                        with open(min_path, 'w', encoding='utf-8') as f:
                            f.write(minified)

                        PerformanceOptimizer.update_resource_refs(root, file, file.replace('.css', '.min.css'))
                        # 对压缩后的文件进行gzip
                        if PerformanceOptimizer.gzip_compress(min_path):

                        stats['compressed_css'] += 1
                    except Exception as e:
                # 处理JavaScript文件
                elif file.endswith('.js') and not file.endswith('.min.js') and 'anti_hotlink.js' not in file:
                    stats['js_files'] += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            js_content = f.read()

                        # 压缩JavaScript
                        minified = PerformanceOptimizer.minify_js(js_content)
                        min_path = file_path.replace('.js', '.min.js')

                        with open(min_path, 'w', encoding='utf-8') as f:
                            f.write(minified)

                        PerformanceOptimizer.update_resource_refs(root, file, file.replace('.js', '.min.js'))
                        # 对压缩后的文件进行gzip
                        if PerformanceOptimizer.gzip_compress(min_path):
                            stats['gzip_files'] += 1

                        stats['compressed_js'] += 1
                    except Exception as e:
                        Logger.error(f'处理JavaScript文件 {file} 失败: {str(e)}')

                # 处理HTML文件
                elif file.endswith('.html'):
                    html_path = file_path

                    # 添加缓存控制
                    PerformanceOptimizer.add_caching_headers(html_path)

                    # 添加defer属性
                    PerformanceOptimizer.add_defer_to_scripts(html_path)
                    # 添加预加载
                    PerformanceOptimizer.preload_critical_resources(html_path)

                    # 添加懒加载
                    PerformanceOptimizer.implement_lazy_loading(html_path)

                    stats['html_optimized'] += 1

        return stats

    def update_resource_refs(directory, old_name, new_name):
        """更新HTML文件中的资源引用"""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    html_path = os.path.join(root, file)
                    try:
                        with open(html_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 更新引用
                        updated_content = content.replace(old_name, new_name)

                        if content != updated_content:
                    except Exception as e:
                        Logger.error(f'更新HTML引用 {html_path} 失败: {str(e)}')

    def create_service_worker(deploy_dir):
        sw_content = '''const CACHE_NAME = 'mtscos-cache-v1';
const STATIC_ASSETS = [
  '/MyPages/index.html',
  '/MyStyle/index.min.css',
  '/MyScript/anti_hotlink.js',
  '/MyScript/auth.min.js',

// 安装Service Worker，预缓存核心资源
self.addEventListener('install', (event) => {
    caches.open(CACHE_NAME).then((cache) => {
    }).then(() => self.skipWaiting())
});

// 激活Service Worker，清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((cacheName) => {
          return cacheName !== CACHE_NAME;
        }).map((cacheName) => {
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // 跳过非GET请求和浏览器扩展请求
  if (event.request.method !== 'GET' || event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // 如果找到缓存，则返回缓存的响应
      if (cachedResponse) {
        return cachedResponse;
      }

      // 否则，从网络获取并缓存结果
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
        }

        // 克隆响应，因为响应流只能使用一次
        const responseToCache = networkResponse.clone();

        // 缓存响应
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // 如果网络请求失败，尝试返回备用响应
        if (event.request.headers.get('accept').includes('text/html')) {
          return caches.match('/MyPages/index.html');
        }
      });
    })
  );
});
'''

        sw_path = os.path.join(deploy_dir, 'service-worker.js')
        try:
            with open(sw_path, 'w', encoding='utf-8') as f:
                f.write(sw_content)
            Logger.success(f'已创建Service Worker: {sw_path}')
            return True
        except Exception as e:
            Logger.error(f'创建Service Worker失败: {str(e)}')
            return False

    def register_service_worker_in_html(html_files):
        """在HTML文件中注册Service Worker"""
        sw_registration = '''    <script>
        // 注册Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                    .then(registration => {
                    })
                    .catch(error => {
                        console.log('Service Worker 注册失败:', error);
                    });
            });
        }
    </script>'''

        for html_file in html_files:
                    content = f.read()

                    # 在关闭的body标签前添加注册代码
                    updated_content = re.sub(r'</body>\s*</html>', f'{sw_registration}\n</body>\n</html>', content)
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

                    Logger.info(f'已在 {os.path.basename(html_file)} 中注册Service Worker')
            except Exception as e:
                Logger.error(f'在 {html_file} 中注册Service Worker失败: {str(e)}')

    def optimize_database_connections():
        """优化数据库连接配置"""
        # 这里可以添加数据库连接池等优化
        return True

    def run_performance_audit():
        """运行性能审计"""
        Logger.info("开始执行项目性能优化...")

        # 压缩所有资源
        stats = PerformanceOptimizer.compress_all_resources(DEPLOY_DIR)

        # 优化图片

        # 创建Service Worker

        # 收集HTML文件并注册Service Worker
        html_files = []
        for root, _, files in os.walk(os.path.join(DEPLOY_DIR, 'MyPages')):
                if file.endswith('.html'):
                    html_files.append(os.path.join(root, file))


        # 优化数据库连接
        PerformanceOptimizer.optimize_database_connections()
        elapsed = end_time - start_time

        Logger.log("="*60, "SUCCESS")
        Logger.log(f"JS文件处理: {stats['compressed_js']}/{stats['js_files']}", "SUCCESS")
        Logger.log(f"Gzip压缩文件: {stats['gzip_files']}", "SUCCESS")
        Logger.log(f"HTML优化文件: {stats['html_optimized']}", "SUCCESS")

        # 创建优化报告文件
        report_path = os.path.join(ROOT_DIR, 'Documentation', 'performance_optimization_report.txt')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n## 优化结果\n")
            f.write(f"- CSS文件处理: {stats['compressed_css']}/{stats['css_files']}\n")
            f.write(f"- JS文件处理: {stats['compressed_js']}/{stats['js_files']}\n")
            f.write(f"- HTML优化文件: {stats['html_optimized']}\n")
            f.write(f"- Service Worker注册: {sw_count}\n")
            f.write(f"- 总耗时: {elapsed:.2f} 秒\n")
            f.write("\n## 优化措施\n")
            f.write("2. Gzip压缩静态资源\n")
            f.write("3. 添加缓存控制meta标签\n")
            f.write("4. 为JavaScript添加defer属性\n")
            f.write("5. 预加载关键资源\n")
            f.write("6. 为图片添加懒加载\n")
            f.write("7. 实现Service Worker缓存\n")
        return stats
if __name__ == "__main__":
    # 运行性能优化
    PerformanceOptimizer.run_performance_audit()
