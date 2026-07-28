#!/usr/bin/env python3
"""测试MTSCOS AI网页"""

from playwright.sync_api import sync_playwright
import time

def test_mtscos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 监听console日志
        page.on('console', lambda msg: logger.info(f'[Console] {msg.type}: {msg.text}'))
        
        # 监听页面错误
        page.on('pageerror', lambda err: logger.info(f'[Page Error] {err}'))
        
        logger.info("正在访问 http://localhost:8888/...")
        
        try:
            # 设置超时时间
            page.set_default_timeout(10000)
            
            # 访问页面
            response = page.goto('http://localhost:8888/', wait_until='domcontentloaded')
            
            logger.info(f"响应状态: {response.status}")
            logger.info(f"响应URL: {response.url}")
            
            # 等待页面加载
            time.sleep(2)
            
            # 获取页面标题
            title = page.title()
            logger.info(f"页面标题: {title}")
            
            # 截图
            page.screenshot(path='/tmp/mtscos_test.png', full_page=True)
            logger.info("截图保存到: /tmp/mtscos_test.png")
            
            # 获取页面内容长度
            content = page.content()
            logger.info(f"页面内容长度: {len(content)} 字符")
            
            # 检查是否有错误
            if response.status == 200:
                logger.info("✅ 页面加载成功!")
            else:
                logger.info(f"❌ 页面加载失败: HTTP {response.status}")
                
        except Exception as e:
            logger.info(f"❌ 测试错误: {e}")
            
        finally:
            browser.close()
            logger.info("测试完成")

if __name__ == '__main__':
    test_mtscos()