# -*- coding: utf-8 -*-
import os
# JSON import removed - using database
from app.utils.logging import logger
from app.ai.code_analyzer import ai_code_analyzer

class AIAutoCompletionService:
    """AI自动补充服务，用于自动分析项目并补充缺失功能"""

    def __init__(self):
        self.analyzer = ai_code_analyzer
        self.project_root = self.analyzer.project_root

    def auto_complete_project(self):
        """自动补充项目功能"""
        logger.info("开始自动补充项目功能")

        # 1. 分析项目
        analysis_report = self.analyzer.analyze_project()

        # 2. 生成补充代码
        generated_code = self._generate_supplement_code(analysis_report['missing_features'])

        # 3. 应用补充代码到项目
        applied_files = self._apply_supplement_code(generated_code)

        # 4. 生成完成报告
        completion_report = {
            'timestamp': analysis_report['timestamp'],
            'missing_features': analysis_report['missing_features'],
            'generated_code': generated_code,
            'applied_files': applied_files,
            'optimization_suggestions': analysis_report['optimization_suggestions']
        }

        logger.info(f"自动补充项目功能完成，应用了 {len(applied_files)} 个文件")

        # 保存完成报告
        self._save_completion_report(completion_report)

        return completion_report

    def _generate_supplement_code(self, missing_features):
        """根据缺失功能生成补充代码"""
        generated_code = []

        for feature in missing_features:
            logger.info(f"为缺失功能生成代码: {feature['description']}")

            # 生成对应功能的代码
            code = self.analyzer.generate_missing_code(feature)
            if code:
                generated_code.append({
                    'feature': feature,
                    'code': code
                })

        return generated_code

    def _apply_supplement_code(self, generated_code):
        """将生成的代码应用到项目中"""
        applied_files = []

        for item in generated_code:
            feature = item['feature']
            code = item['code']

            directory = code['directory']
            files = code['files']

            # 确保目标目录存在
            dir_path = os.path.join(self.project_root, directory)
            os.makedirs(dir_path, exist_ok=True)

            # 写入文件
            for file in files:
                file_path = os.path.join(dir_path, file['name'])

                # 检查文件是否已存在
                if os.path.exists(file_path):
                    logger.info(f"文件已存在，跳过: {file_path}")
                    continue

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file['content'])

                applied_files.append({
                    'path': file_path,
                    'feature_type': feature['type']
                logger.info(f"已创建文件: {file_path}")

        return applied_files

    def _save_completion_report(self, report):
        """保存完成报告到文件"""
        report_path = os.path.join(self.project_root, 'ai_completion_report.json')

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"自动补充报告已保存到: {report_path}")

    def get_completion_report(self):
        """获取最近的自动补充报告"""
        report_path = os.path.join(self.project_root, 'ai_completion_report.json')

            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return None

    def apply_optimization_suggestions(self, suggestions):
        """应用优化建议"""
        logger.info(f"开始应用 {len(suggestions)} 个优化建议")

        applied_suggestions = []

        for suggestion in suggestions:
            # 根据建议类型执行不同的优化
            if suggestion['type'] == 'code_organization':
                # 代码组织优化建议
                logger.info(f"代码组织优化建议: {suggestion['description']}")
                applied_suggestions.append(suggestion)
            elif suggestion['type'] == 'code_cleanup':
                # 代码清理建议
                logger.info(f"代码清理建议: {suggestion['description']}")
                applied_suggestions.append(suggestion)

        logger.info(f"应用了 {len(applied_suggestions)} 个优化建议")

# 初始化AI自动补充服务
ai_auto_completion_service = AIAutoCompletionService()
