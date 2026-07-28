#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cdnjs本地化脚本
将所有cdnjs调用替换为本地资源
"""

import os
import re
import urllib.request
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
FONT_AWESOME_DIR = os.path.join(STATIC_DIR, 'font-awesome')
CSS_DIR = os.path.join(FONT_AWESOME_DIR, 'css')
WEBFONTS_DIR = os.path.join(FONT_AWESOME_DIR, 'webfonts')

CDNJS_PATTERNS = {
    'font-awesome': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        'local_path': '/static/font-awesome/css/all.min.css',
        'fonts': [
            'fa-solid-900.woff2',
            'fa-solid-900.ttf',
            'fa-regular-400.woff2',
            'fa-regular-400.ttf',
            'fa-brands-400.woff2',
            'fa-brands-400.ttf'
        ]
    }
}

def download_file(url, save_path):
    """下载文件"""
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urllib.request.urlretrieve(url, save_path)
        logger.info(f"✓ 下载成功: {os.path.basename(save_path)}")
        return True
    except Exception as e:
        logger.info(f"✗ 下载失败 {url}: {e}")
        return False

def download_font_awesome():
    """下载Font Awesome资源"""
    logger.info("\n=== 下载 Font Awesome 6.4.0 ===")
    
    css_url = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
    css_path = os.path.join(CSS_DIR, 'all.min.css')
    download_file(css_url, css_path)
    
    logger.info("\n=== 下载字体文件 ===")
    fonts_base_url = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/'
    for font in CDNJS_PATTERNS['font-awesome']['fonts']:
        font_url = fonts_base_url + font
        font_path = os.path.join(WEBFONTS_DIR, font)
        download_file(font_url, font_path)

def fix_font_awesome_css():
    """修复Font Awesome CSS中的字体引用路径"""
    css_path = os.path.join(CSS_DIR, 'all.min.css')
    if not os.path.exists(css_path):
        logger.info("✗ CSS文件不存在")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换字体引用路径
    old_pattern = r'https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.4\.0/webfonts/'
    new_pattern = '../webfonts/'
    content = re.sub(old_pattern, new_pattern, content)
    
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✓ 修复Font Awesome CSS字体路径")
    return True

def update_html_files():
    """更新HTML文件中的cdnjs引用"""
    templates_dir = os.path.join(BASE_DIR, 'templates')
    cdn_url = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
    local_url = '/static/font-awesome/css/all.min.css'
    
    html_files = []
    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            if f.endswith('.html'):
                html_files.append(os.path.join(root, f))
    
    updated_count = 0
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if cdn_url in content:
                content = content.replace(cdn_url, local_url)
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_count += 1
                logger.info(f"✓ 更新: {os.path.relpath(html_file, BASE_DIR)}")
        except Exception as e:
            logger.info(f"✗ 无法更新 {html_file}: {e}")
    
    logger.info(f"\n✓ 共更新 {updated_count} 个HTML文件")
    return True

def update_font_awesome_src():
    """更新src目录中的Font Awesome CSS"""
    src_css_path = os.path.join(BASE_DIR, 'src', 'html', 'assets', 'font-awesome', 'css', 'all.min.css')
    if os.path.exists(src_css_path):
        with open(src_css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        old_pattern = r'https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/6\.5\.1/webfonts/'
        new_pattern = '../webfonts/'
        content = re.sub(old_pattern, new_pattern, content)
        
        with open(src_css_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✓ 更新src目录中的Font Awesome CSS")
    else:
        logger.info("✗ src目录中的Font Awesome CSS不存在")

def verify_localization():
    """验证本地化是否成功"""
    logger.info("\n=== 验证本地化 ===")
    
    # 检查静态文件
    css_path = os.path.join(CSS_DIR, 'all.min.css')
    if os.path.exists(css_path):
        logger.info(f"✓ CSS文件存在: {os.path.getsize(css_path)} bytes")
    else:
        logger.info("✗ CSS文件不存在")
    
    # 检查字体文件
    font_count = 0
    for font in CDNJS_PATTERNS['font-awesome']['fonts']:
        font_path = os.path.join(WEBFONTS_DIR, font)
        if os.path.exists(font_path):
            font_count += 1
            logger.info(f"✓ 字体文件存在: {font} ({os.path.getsize(font_path)} bytes)")
    
    if font_count == len(CDNJS_PATTERNS['font-awesome']['fonts']):
        logger.info("✓ 所有字体文件下载完成")
    else:
        logger.info(f"✗ 缺少 {len(CDNJS_PATTERNS['font-awesome']['fonts']) - font_count} 个字体文件")
    
    # 检查是否还有cdnjs引用
    templates_dir = os.path.join(BASE_DIR, 'templates')
    cdn_count = 0
    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            if f.endswith('.html'):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                    if 'cdnjs.cloudflare.com' in file.read():
                        cdn_count += 1
    
    if cdn_count == 0:
        logger.info("✓ 所有HTML文件中的cdnjs引用已替换")
    else:
        logger.info(f"✗ 还有 {cdn_count} 个HTML文件包含cdnjs引用")

def main():
    """主流程"""
    logger.info("=" * 60)
    logger.info("cdnjs本地化脚本")
    logger.info("=" * 60)
    
    logger.info("\n步骤1: 创建静态目录结构")
    os.makedirs(CSS_DIR, exist_ok=True)
    os.makedirs(WEBFONTS_DIR, exist_ok=True)
    logger.info("✓ 目录结构创建完成")
    
    logger.info("\n步骤2: 下载Font Awesome资源")
    download_font_awesome()
    
    logger.info("\n步骤3: 修复CSS字体路径")
    fix_font_awesome_css()
    
    logger.info("\n步骤4: 更新HTML文件")
    update_html_files()
    
    logger.info("\n步骤5: 更新src目录CSS")
    update_font_awesome_src()
    
    logger.info("\n步骤6: 验证本地化")
    verify_localization()
    
    logger.info("\n" + "=" * 60)
    logger.info("cdnjs本地化完成！")
    logger.info("=" * 60)

if __name__ == '__main__':
    main()