# -*- coding: utf-8 -*-
# 上次更新: 2025-10-26 16:53:25
#!/usr/bin/env python3

"""
自动整理CSS和JavaScript文件，删除冗余备份，并修复HTML页面问题
功能：
1. 整理CSS文件到对应的分类目录
2. 整理JavaScript文件到对应的分类目录
3. 删除冗余的带时间戳的备份文件
4. 修复HTML页面中的UI问题
"""
import os
import re
import shutil
# JSON import removed - using database
from datetime import datetime
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("css_js_organize.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CSSJSOrganizer:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.source_code_dir = os.path.join(self.project_root, "SourceCode")
        self.css_dir = os.path.join(self.source_code_dir, "CSS")
        self.js_dir = os.path.join(self.source_code_dir, "JavaScript")
        self.html_dir = os.path.join(self.project_root, "html")

        # 创建分类目录
        self.css_categories = {
            "通用样式": os.path.join(self.css_dir, "通用样式"),
            "页面样式": os.path.join(self.css_dir, "页面样式"),
            "组件样式": os.path.join(self.css_dir, "组件样式"),
            "第三方库": os.path.join(self.css_dir, "第三方库")
        }

        self.js_categories = {
            "核心脚本": os.path.join(self.js_dir, "核心脚本"),
            "页面脚本": os.path.join(self.js_dir, "页面脚本"),
            "加密脚本": os.path.join(self.js_dir, "加密脚本"),
            "工具函数": os.path.join(self.js_dir, "工具函数")
        }

        self.stats = {
            "total_files_processed": 0,
            "css_files_organized": 0,
            "js_files_organized": 0,
            "redundant_files_deleted": 0,
            "html_files_fixed": 0,
            "errors": 0
        }

        self.css_file_mapping = {
            "main.css": "通用样式",
            "index.css": "页面样式",
            "login-styles.css": "页面样式",
            "403.css": "页面样式",
            "404.css": "页面样式",
            "Update.css": "页面样式",
            "dashboard.css": "页面样式",
            "register.css": "页面样式",
            "password_reset.css": "页面样式",
            "font-awesome.min.css": "第三方库",
            "arduino.css": "页面样式",
            "company.css": "页面样式",
            "contact.css": "页面样式",
            "documentation.css": "页面样式",
            "faq.css": "页面样式",
            "features.css": "页面样式",
            "footer.css": "组件样式",
            "history.css": "页面样式",
            "news.css": "页面样式",
            "security.css": "页面样式",
            "server.css": "页面样式",
            "service_monitor.css": "页面样式",
            "settings.css": "页面样式",
            "solutions.css": "页面样式",
            "support.css": "页面样式",
            "team.css": "页面样式",
            "terms.css": "页面样式"
        }

            "anti_hotlink.js": "核心脚本",
            "check_links.js": "核心脚本",
            "login-script.js": "页面脚本",
            "error_handler.js": "工具函数",
            "load_footer.js": "工具函数",
            "redirect.js": "工具函数",
            "client.js": "核心脚本",
            "index.js": "页面脚本",
            "decrypt_helper.js": "工具函数"
        }

        """创建所有必要的目录"""
        try:
            # 创建CSS分类目录
            for dir_path in self.css_categories.values():
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"创建目录: {dir_path}")

            # 创建JS分类目录
            for dir_path in self.js_categories.values():
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"创建目录: {dir_path}")

            return True
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            return False
    def is_redundant_file(self, filename):
        """检查文件是否为冗余的带时间戳备份"""
        # 匹配格式: filename_YYYYMMDDHHMMSS.ext
        pattern = r'^(.+)_\d{14}\.(css|js)$'
        return bool(re.match(pattern, filename))

    def organize_css_files(self):
        """整理CSS文件"""
        try:
            css_files = [f for f in os.listdir(self.css_dir)
                        if f.endswith('.css') and os.path.isfile(os.path.join(self.css_dir, f))]

            for css_file in css_files:
                css_path = os.path.join(self.css_dir, css_file)

                # 处理冗余文件
                if self.is_redundant_file(css_file):
                    os.remove(css_path)
                    logger.info(f"删除冗余CSS文件: {css_file}")
                    self.stats["redundant_files_deleted"] += 1
                    continue

                # 确定分类
                category = self.css_file_mapping.get(css_file, "其他样式")
                if category == "其他样式" and "encrypted" in css_file:
                    category = "加密样式"

                # 确保分类目录存在
                if category not in self.css_categories:
                    self.css_categories[category] = os.path.join(self.css_dir, category)
                    os.makedirs(self.css_categories[category], exist_ok=True)

                # 移动文件
                dest_path = os.path.join(self.css_categories[category], css_file)
                if css_path != dest_path:
                    shutil.move(css_path, dest_path)
                    logger.info(f"移动CSS文件: {css_file} -> {category}")
                    self.stats["css_files_organized"] += 1

        except Exception as e:
            logger.error(f"整理CSS文件失败: {str(e)}")
            self.stats["errors"] += 1

    def organize_js_files(self):
        """整理JavaScript文件"""
        try:
            js_files = [f for f in os.listdir(self.js_dir)
                        if f.endswith('.js') and os.path.isfile(os.path.join(self.js_dir, f))]
            for js_file in js_files:
                js_path = os.path.join(self.js_dir, js_file)
                # 处理冗余文件
                if self.is_redundant_file(js_file):
                    os.remove(js_path)
                    logger.info(f"删除冗余JS文件: {js_file}")
                    self.stats["redundant_files_deleted"] += 1
                    continue

                # 确定分类
                if "encrypted" in js_file:
                    category = "加密脚本"
                    category = self.js_file_mapping.get(js_file, "其他脚本")

                if category not in self.js_categories:
                    self.js_categories[category] = os.path.join(self.js_dir, category)
                    os.makedirs(self.js_categories[category], exist_ok=True)

                dest_path = os.path.join(self.js_categories[category], js_file)
                    shutil.move(js_path, dest_path)
                    logger.info(f"移动JS文件: {js_file} -> {category}")

        except Exception as e:
            logger.error(f"整理JS文件失败: {str(e)}")
            self.stats["errors"] += 1

    def fix_html_issues(self):
        try:
            index_html_path = os.path.join(self.html_dir, "index.html")
            if not os.path.exists(index_html_path):
                logger.warning(f"HTML文件不存在: {index_html_path}")

                content = f.read()
            # 1. 修复h2标题：将"欢迎回来"改为"MTSCOS 登入系统"
            content = re.sub(r'<h2 class="form-title">欢迎回来</h2>',
                           '<h2 class="form-title">MTSCOS 登入系统</h2>',
                           content)
            logger.info("已修改h2标题为'MTSCOS 登入系统'")

            # 2. 删除指定的span元素
            content = re.sub(r'<span class="feature-text">智能数据库配置与优化</span>',
                           '',
                           content)
            logger.info("已删除智能数据库配置与优化的span元素")

            # 3. 优化button样式（通过添加更具体的CSS类）
            # 为social-button添加优化样式类
            content = re.sub(r'<button type="button" class="social-button">',
                           '<button type="button" class="social-button optimized-social-btn">',
                           content)
            logger.info("已优化社交登录按钮样式")

            # 保存修改后的HTML文件
            with open(index_html_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 添加优化的CSS到login-styles.css
            self.add_optimized_css()

            self.stats["html_files_fixed"] += 1
            logger.info(f"已修复HTML文件: {index_html_path}")

        except Exception as e:
            logger.error(f"修复HTML文件失败: {str(e)}")

    def add_optimized_css(self):
        """添加优化的CSS样式到login-styles.css"""
        try:
            # 查找login-styles.css的位置
            login_css_path = None
                if "login-styles.css" in files:

            if not login_css_path:
                login_css_path = os.path.join(self.css_categories["页面样式"], "login-styles.css")

            optimized_css = '''
/* 优化的社交登录按钮样式 */
.optimized-social-btn {
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: all 0.5s ease;
}

    left: 100%;
}

    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

    font-size: 18px;
    transition: transform 0.3s ease;
}

    transform: scale(1.1);
}

.social-login {
    align-items: center;
    justify-content: center;
}

    min-height: 40px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-primary);
}
'''
            # 检查文件是否存在，如果存在则追加样式
            if os.path.exists(login_css_path):
                with open(login_css_path, 'a', encoding='utf-8') as f:
                    f.write(optimized_css)
                logger.info(f"已添加优化CSS到: {login_css_path}")
            else:
                # 如果文件不存在，创建它
                with open(login_css_path, 'w', encoding='utf-8') as f:
                    f.write(optimized_css)
                logger.info(f"已创建并添加优化CSS到: {login_css_path}")

        except Exception as e:
            logger.error(f"添加优化CSS失败: {str(e)}")
            self.stats["errors"] += 1

    def create_report(self):
        """创建整理报告"""
        try:
            report = {
                "整理时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "统计信息": self.stats,
                "CSS分类目录": list(self.css_categories.keys()),
                "JS分类目录": list(self.js_categories.keys())
            }

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"整理报告已生成: {report_path}")
            return report

            self.stats["errors"] += 1
            return None

    def run(self):
        """运行整理流程"""

        # 1. 创建目录

        # 2. 整理CSS文件
        logger.info("开始整理CSS文件...")
        self.organize_css_files()

        logger.info("开始整理JavaScript文件...")
        self.organize_js_files()

        # 4. 修复HTML问题
        logger.info("开始修复HTML页面问题...")

        # 5. 生成报告
        report = self.create_report()

        logger.info("整理完成!")
        logger.info(f"总共处理文件: {self.stats['total_files_processed']}")
        logger.info(f"JS文件整理: {self.stats['js_files_organized']}")
        logger.info(f"删除冗余文件: {self.stats['redundant_files_deleted']}")
        logger.info(f"修复HTML文件: {self.stats['html_files_fixed']}")
        logger.info(f"错误数量: {self.stats['errors']}")

        return report

if __name__ == "__main__":
    organizer = CSSJSOrganizer()
    organizer.run()
