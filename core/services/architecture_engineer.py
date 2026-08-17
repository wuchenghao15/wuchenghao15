#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构工程师AI员工 - 优化精简MTSCOS系统文件架构
"""
import os
import shutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('architecture_engineer')


class ArchitectureEngineer:
    """架构工程师AI员工"""

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.actions_taken = []
        self.recommendations = []
        self.organized = False

    def analyze_structure(self):
        """分析当前项目结构"""
        logger.info("=" * 70)
        logger.info("架构工程师: 开始分析MTSCOS系统文件架构")
        logger.info("=" * 70)

        structure = {
            'root_files': [],
            'root_dirs': [],
            'temp_files': [],
            'log_files': [],
            'md_docs': [],
            'sql_files': [],
            'json_files': [],
            'csv_files': [],
            'txt_files': [],
        }

        skip_dirs = {'venv', '.git', '__pycache__', 'node_modules', '.pytest_cache'}

        for item in os.listdir(self.base_dir):
            full_path = os.path.join(self.base_dir, item)

            if os.path.isfile(full_path):
                structure['root_files'].append(item)
                name_lower = item.lower()

                if any(p in name_lower for p in ['log_', '_log', 'temp_', '_temp']):
                    structure['log_files'].append(item)
                elif name_lower.startswith('log_') or 'fix' in name_lower:
                    structure['temp_files'].append(item)
                elif item.endswith('.md'):
                    structure['md_docs'].append(item)
                elif item.endswith('.sql'):
                    structure['sql_files'].append(item)
                elif item.endswith('.json'):
                    structure['json_files'].append(item)
                elif item.endswith('.csv'):
                    structure['csv_files'].append(item)
                elif item.endswith('.txt'):
                    structure['txt_files'].append(item)
            elif os.path.isdir(full_path) and item not in skip_dirs:
                structure['root_dirs'].append(item)

        logger.info(f"根目录文件数: {len(structure['root_files'])}")
        logger.info(f"根目录目录数: {len(structure['root_dirs'])}")
        logger.info(f"  - 临时日志文件: {len(structure['log_files'])}")
        logger.info(f"  - 临时修复文件: {len(structure['temp_files'])}")
        logger.info(f"  - 文档文件(.md): {len(structure['md_docs'])}")
        logger.info(f"  - SQL文件: {len(structure['sql_files'])}")
        logger.info(f"  - JSON文件: {len(structure['json_files'])}")
        logger.info(f"  - CSV文件: {len(structure['csv_files'])}")
        logger.info(f"  - TXT文件: {len(structure['txt_files'])}")

        return structure

    def organize_logs(self, structure):
        """整理日志文件到 logs/ 目录"""
        logs_dir = os.path.join(self.base_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        moved = 0
        for log_file in structure['log_files'] + structure['txt_files']:
            src = os.path.join(self.base_dir, log_file)
            dst = os.path.join(logs_dir, log_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {log_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个日志/文本文件到 logs/")
            self.actions_taken.append(f"移动 {moved} 个日志/文本文件到 logs/")
        return moved

    def organize_sql(self, structure):
        """整理SQL文件到 database/sql/ 目录"""
        sql_dir = os.path.join(self.base_dir, 'database', 'sql')
        os.makedirs(sql_dir, exist_ok=True)

        moved = 0
        for sql_file in structure['sql_files']:
            src = os.path.join(self.base_dir, sql_file)
            dst = os.path.join(sql_dir, sql_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {sql_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个SQL文件到 database/sql/")
            self.actions_taken.append(f"移动 {moved} 个SQL文件到 database/sql/")
        return moved

    def organize_json_data(self, structure):
        """整理JSON数据文件到 database/json/ 目录"""
        json_dir = os.path.join(self.base_dir, 'database', 'json')
        os.makedirs(json_dir, exist_ok=True)

        moved = 0
        for json_file in structure['json_files']:
            if json_file in ['package.json', 'tsconfig.json', '.eslintrc.json']:
                continue

            src = os.path.join(self.base_dir, json_file)
            dst = os.path.join(json_dir, json_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {json_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个JSON数据文件到 database/json/")
            self.actions_taken.append(f"移动 {moved} 个JSON数据文件到 database/json/")
        return moved

    def organize_csv(self, structure):
        """整理CSV文件到 database/csv/ 目录"""
        csv_dir = os.path.join(self.base_dir, 'database', 'csv')
        os.makedirs(csv_dir, exist_ok=True)

        moved = 0
        for csv_file in structure['csv_files']:
            src = os.path.join(self.base_dir, csv_file)
            dst = os.path.join(csv_dir, csv_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {csv_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个CSV文件到 database/csv/")
            self.actions_taken.append(f"移动 {moved} 个CSV文件到 database/csv/")
        return moved

    def organize_temp_files(self, structure):
        """整理临时修复文件到 archive/ 目录"""
        archive_dir = os.path.join(self.base_dir, 'archive', 'temp_scripts')
        os.makedirs(archive_dir, exist_ok=True)

        moved = 0
        for temp_file in structure['temp_files']:
            src = os.path.join(self.base_dir, temp_file)
            dst = os.path.join(archive_dir, temp_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {temp_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个临时脚本到 archive/temp_scripts/")
            self.actions_taken.append(f"移动 {moved} 个临时脚本到 archive/temp_scripts/")
        return moved

    def organize_documentation(self, structure):
        """整理文档文件到 docs/ 目录"""
        docs_dir = os.path.join(self.base_dir, 'docs')
        os.makedirs(docs_dir, exist_ok=True)

        moved = 0
        for md_file in structure['md_docs']:
            if md_file in ['README.md']:
                continue

            src = os.path.join(self.base_dir, md_file)
            dst = os.path.join(docs_dir, md_file)
            if os.path.exists(src):
                try:
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                        moved += 1
                except Exception as e:
                    logger.warning(f"移动 {md_file} 失败: {e}")

        if moved > 0:
            logger.info(f"✓ 移动 {moved} 个文档到 docs/")
            self.actions_taken.append(f"移动 {moved} 个文档到 docs/")
        return moved

    def generate_structure_report(self):
        """生成架构优化报告"""
        report_path = os.path.join(self.base_dir, 'ARCHITECTURE_REPORT.md')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# MTSCOS系统架构优化报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"AI员工: 架构工程师 (ArchitectureEngineer)\n\n")
            f.write("## 执行的优化操作\n\n")
            for action in self.actions_taken:
                f.write(f"- ✓ {action}\n")
            f.write("\n## 推荐的目录结构\n\n")
            f.write("```\n")
            f.write("flask-app/\n")
            f.write("├── app/                    # Flask应用核心\n")
            f.write("│   ├── api/              # API蓝图\n")
            f.write("│   ├── services/         # 业务服务\n")
            f.write("│   ├── models/           # 数据模型\n")
            f.write("│   ├── views/            # 视图层\n")
            f.write("│   ├── utils/            # 工具类\n")
            f.write("│   ├── middlewares/      # 中间件\n")
            f.write("│   ├── config/           # 配置\n")
            f.write("│   └── drivers/          # 驱动\n")
            f.write("├── ai_engines/           # AI引擎\n")
            f.write("├── database/             # 数据库文件\n")
            f.write("│   ├── sql/             # SQL脚本\n")
            f.write("│   ├── json/            # JSON数据\n")
            f.write("│   └── csv/             # CSV数据\n")
            f.write("├── logs/                 # 日志文件\n")
            f.write("├── docs/                 # 项目文档\n")
            f.write("├── archive/              # 归档\n")
            f.write("│   └── temp_scripts/    # 临时脚本\n")
            f.write("├── static/               # 静态资源\n")
            f.write("├── templates/            # 模板\n")
            f.write("├── app.py                # 主入口\n")
            f.write("├── app.db                # 数据库\n")
            f.write("└── README.md             # 主说明\n")
            f.write("```\n")
            f.write("\n## 进一步优化建议\n\n")
            for rec in self.recommendations:
                f.write(f"- {rec}\n")

        logger.info(f"✓ 架构报告已保存: {report_path}")
        return report_path

    def run_optimization(self):
        """执行完整的架构优化"""
        logger.info("开始MTSCOS系统架构优化...")

        structure = self.analyze_structure()

        self.organize_logs(structure)
        self.organize_sql(structure)
        self.organize_json_data(structure)
        self.organize_csv(structure)
        self.organize_temp_files(structure)
        self.organize_documentation(structure)

        self.recommendations = [
            "将 settings/ 目录合并到 app/config/",
            "将 tasks/ 目录整合到 app/services/",
            "将 shadow_export/ 移入 archive/",
            "为所有Python文件添加统一的文档字符串",
            "使用 .env 文件统一管理环境变量",
            "建立 CI/CD 流程自动运行代码质量检查",
        ]

        report_path = self.generate_structure_report()
        self.organized = True

        logger.info("=" * 70)
        logger.info(f"架构优化完成! 共执行 {len(self.actions_taken)} 项操作")
        logger.info(f"报告文件: {report_path}")
        logger.info("=" * 70)

        return {
            'success': True,
            'actions': self.actions_taken,
            'recommendations': self.recommendations,
            'report_path': report_path
        }


if __name__ == '__main__':
    engineer = ArchitectureEngineer()
    result = engineer.run_optimization()
    print(f"\n优化完成: {result['success']}")
    print(f"执行操作数: {len(result['actions'])}")
    for action in result['actions']:
        print(f"  - {action}")
