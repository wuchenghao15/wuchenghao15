# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:08
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
# 输出目录
DIST_DIR = os.path.join(ROOT_DIR, 'dist', 'release')
# 源文件目录
MYSTYLE_DIR = os.path.join(ROOT_DIR, 'MyStyle')
MYSCRIPT_DIR = os.path.join(ROOT_DIR, 'MyScript')
MYPAGES_DIR = os.path.join(ROOT_DIR, 'MyPages')
MYDATA_DIR = os.path.join(ROOT_DIR, 'MyData')
MYTOOLS_DIR = os.path.join(ROOT_DIR, 'MyTools')
LOGS_DIR = os.path.join(ROOT_DIR, 'Logs')

# 记录构建日志
BUILD_LOG = os.path.join(ROOT_DIR, 'Logs', f'build_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log')

class Logger:
    """简单的日志记录类"""
    @staticmethod
    def log(message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] {message}'
        print(log_message)
        # 确保日志目录存在
        os.makedirs(os.path.dirname(BUILD_LOG), exist_ok=True)
        # 写入日志文件
        with open(BUILD_LOG, 'a') as f:
            f.write(log_message + '\n')

    def info(message):
        Logger.log(f'INFO: {message}')

    def error(message):
        Logger.log(f'ERROR: {message}')

    def warning(message):
        Logger.log(f'WARNING: {message}')

class BuildTools:
    """构建工具类"""
    def clean():
        """清理输出目录"""
        Logger.info(f'清理输出目录: {DIST_DIR}')
        if os.path.exists(DIST_DIR):
            shutil.rmtree(DIST_DIR)
        Logger.info('清理完成')

    def minify_css(css_content):
        """简单的CSS压缩"""
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
        return css.strip()

    def minify_js(js_content):
        """简单的JavaScript压缩"""
        # 移除多行注释
        js = re.sub(r'\/\*[\s\S]*?\*\/', '', js_content)
        # 移除单行注释，但保留URL中的//
        js = re.sub(r'(?<!http:)\/\/.*$', '', js, flags=re.MULTILINE)
        # 移除多余的空白字符
        js = re.sub(r'\n\s*', '\n', js)
        js = re.sub(r'\s+', ' ', js)
        js = re.sub(r'\s*{\s*', '{', js)
        js = re.sub(r'\s*}\s*', '}', js)
        js = re.sub(r'\s*:\s*', ':', js)
        js = re.sub(r'\s*,\s*', ',', js)
        return js.strip()

    def build_css():
        """构建CSS文件"""
        output_dir = os.path.join(DIST_DIR, 'MyStyle')
        os.makedirs(output_dir, exist_ok=True)

        css_files = [f for f in os.listdir(MYSTYLE_DIR) if f.endswith('.css')]
        Logger.info(f'找到 {len(css_files)} 个CSS文件需要处理')

        for css_file in css_files:
            try:
                input_path = os.path.join(MYSTYLE_DIR, css_file)
                output_path = os.path.join(output_dir, css_file.replace('.css', '.min.css'))

                with open(input_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()

                minified_content = BuildTools.minify_css(css_content)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(minified_content)

                Logger.info(f'CSS文件已压缩: {css_file} -> {os.path.basename(output_path)}')
            except Exception as e:
                Logger.error(f'处理CSS文件 {css_file} 时出错: {str(e)}')

    def build_js():
        """构建JavaScript文件"""
        output_dir = os.path.join(DIST_DIR, 'MyScript')
        os.makedirs(output_dir, exist_ok=True)

        js_files = [f for f in os.listdir(MYSCRIPT_DIR) if f.endswith('.js')]
        Logger.info(f'找到 {len(js_files)} 个JavaScript文件需要处理')

        # 先对原始JS文件进行加密
        Logger.info('开始对JavaScript文件进行加密...')
        encrypt_script = os.path.join(ROOT_DIR, 'encrypt_js.py')
        try:
            subprocess.run(['python3', encrypt_script, '-v'], check=True, cwd=ROOT_DIR)
            Logger.info('JavaScript文件加密完成')
        except subprocess.CalledProcessError as e:
            Logger.error(f'JavaScript文件加密失败: {str(e)}')

        # 然后压缩加密后的JS文件
        for js_file in js_files:
            try:
                output_path = os.path.join(output_dir, js_file.replace('.js', '.min.js'))

                with open(input_path, 'r', encoding='utf-8') as f:
                    js_content = f.read()

                minified_content = BuildTools.minify_js(js_content)

                with open(output_path, 'w', encoding='utf-8') as f:

                Logger.info(f'JavaScript文件已压缩: {js_file} -> {os.path.basename(output_path)}')
                pass
            except Exception as e:
                Logger.error(f'处理JavaScript文件 {js_file} 时出错: {str(e)}')

        """复制HTML文件并更新引用"""
        output_dir = os.path.join(DIST_DIR, 'MyPages')
        os.makedirs(output_dir, exist_ok=True)

        html_files = [f for f in os.listdir(MYPAGES_DIR) if f.endswith('.html')]

            try:
                input_path = os.path.join(MYPAGES_DIR, html_file)
                output_path = os.path.join(output_dir, html_file)

                    html_content = f.read()

                # 更新CSS引用
                updated_content = re.sub(r'(MyStyle\/[^.]+)\.css', r'\1.min.css', html_content)
                # 更新JavaScript引用
                updated_content = re.sub(r'(MyScript\/[^.]+)\.js', r'\1.min.js', updated_content)

                    f.write(updated_content)

                Logger.info(f'HTML文件已复制并更新: {html_file}')
            except Exception as e:
                Logger.error(f'处理HTML文件 {html_file} 时出错: {str(e)}')

        """复制静态资源文件"""
        # 复制MyData目录
        if os.path.exists(MYDATA_DIR):
            shutil.copytree(MYDATA_DIR, os.path.join(DIST_DIR, 'MyData'))
            Logger.info('已复制MyData目录')

        # 复制MyTools目录
        if os.path.exists(MYTOOLS_DIR):
            shutil.copytree(MYTOOLS_DIR, os.path.join(DIST_DIR, 'MyTools'))

        # 复制Logs目录
        if os.path.exists(LOGS_DIR):
            shutil.copytree(LOGS_DIR, os.path.join(DIST_DIR, 'Logs'))
            Logger.info('已复制Logs目录')

    def build():
        """执行完整的构建过程"""
        start_time = time.time()
        Logger.info('开始构建项目...')

        try:
            # 清理输出目录
            BuildTools.clean()

            # 构建CSS文件
            BuildTools.build_css()

            # 构建JavaScript文件（包含加密步骤）
            BuildTools.build_js()

            # 复制并更新HTML文件
            BuildTools.copy_html()

            # 复制静态资源

            # 将加密后的JS文件也复制到部署目录
            Logger.info('正在复制加密后的JavaScript文件到部署目录...')
            for js_file in os.listdir(MYSCRIPT_DIR):
                if js_file.endswith('.js') and not js_file.endswith('.min.js') and not js_file.endswith('.js.bak'):
                    src_path = os.path.join(MYSCRIPT_DIR, js_file)
                    dest_path = os.path.join(DIST_DIR, 'MyScript', js_file)
                    shutil.copy2(src_path, dest_path)
                    Logger.info(f'已复制加密后的JS文件: {js_file}')

            end_time = time.time()
            Logger.info(f'构建完成！耗时: {end_time - start_time:.2f} 秒')
            Logger.info(f'构建结果已保存至: {DIST_DIR}')
            return True
        except Exception as e:
            Logger.error(f'构建过程中出现错误: {str(e)}')
            return False

def main():
    """主函数"""
    # 检查是否具有执行权限
    if not os.access(__file__, os.X_OK):
        Logger.warning('脚本没有执行权限，尝试添加...')
        os.chmod(__file__, 0o755)

    # 执行构建
    success = BuildTools.build()

    if success:
        Logger.info('项目构建成功！')
    else:
        Logger.error('项目构建失败！')
        exit(1)

if __name__ == '__main__':
    main()
