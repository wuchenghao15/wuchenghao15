# -*- coding: utf-8 -*-
import sqlite3
from contextlib import contextmanager
import json
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_api_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIApiEnhancer:
    def __init__(self):
        self.db_path = 'app.db'
        self.api_config = {
            'main_port': 8888,
            'api_prefix': '/api',
            'ai_brain_prefix': '/api/ai-brain',
            'api_timeout': 30,
            'api_rate_limit': 100,
            'enable_cors': True
        }

    def connect_db(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)

    def update_system_config(self, config_key, config_value, config_type='json', description='', is_active=1):
        """更新系统配置"""
        conn = self.connect_db()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        cursor.execute('SELECT id FROM system_config WHERE config_key = ?;', (config_key,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE system_config
                SET config_value = ?, config_type = ?, description = ?, is_active = ?, updated_at = ?
                WHERE config_key = ?
            ''', (config_value, config_type, description, is_active, current_time, config_key))
            logger.info(f"更新系统配置: {config_key} -> {config_value}")
        else:
            cursor.execute('''
                INSERT INTO system_config
                (config_key, config_value, config_type, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (config_key, config_value, config_type, description, is_active, current_time, current_time))
            logger.info(f"创建系统配置: {config_key} -> {config_value}")

        conn.commit()
        conn.close()

    def create_ai_api_blueprint(self):
        """创建AI API蓝图文件"""
        api_blueprint_path = 'app/blueprints/ai_brain_api.py'
        api_blueprint_dir = os.path.dirname(api_blueprint_path)

        if not os.path.exists(api_blueprint_dir):
            os.makedirs(api_blueprint_dir)
            logger.info(f"创建目录: {api_blueprint_dir}")

        blueprint_content = '''from flask import Blueprint, request, jsonify
from app.models.questions import Question
from app.models.system_config import SystemConfig
from app.ai.brain_updater import AIBrainUpdater
from app.ai.exam_generator import ExamGenerator
from app.utils.security import require_permission

ai_brain_api = Blueprint('ai_brain_api', __name__)

@ai_brain_api.route('/')
def ai_brain_root():
    """AI脑库API根路径"""
    return jsonify({
        'message': 'AI Brain API',
        'version': '1.0',
        'endpoints': [
            '/api/ai-brain/questions',
            '/api/ai-brain/generate-questions',
            '/api/ai-brain/exam',
            '/api/ai-brain/status'
        ]
    })

@ai_brain_api.route('/questions')
def get_questions():
    """获取AI脑库题库"""
    subject = request.args.get('subject', 'japanese')
    difficulty = request.args.get('difficulty', 'all')
    question_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 10, type=int)

    questions = Question.get_questions(subject, difficulty, question_type, limit)

    return jsonify({
        'count': len(questions),
        'difficulty': difficulty,
        'type': question_type,
        'questions': questions
    })

@ai_brain_api.route('/generate-questions', methods=['POST'])
def generate_questions():
    """AI生成新问题"""
    data = request.get_json() or {}
    subject = data.get('subject', 'japanese')
    difficulty = data.get('difficulty', 'medium')
    question_type = data.get('type', 'multiple_choice')
    count = data.get('count', 5)

    updater = AIBrainUpdater()
    new_questions = updater.generate_questions(subject, difficulty, question_type, count)

    return jsonify({
        'message': 'Questions generated successfully',
        'questions': new_questions
    })

@ai_brain_api.route('/exam', methods=['POST'])
def generate_exam():
    """生成考试"""
    user_preferences = request.get_json() or {}

    generator = ExamGenerator()
    exam = generator.generate_personalized_exam(user_preferences)

    return jsonify(exam)

@ai_brain_api.route('/status')
def get_ai_brain_status():
    """获取AI脑库状态"""
    config = SystemConfig.get_all_configs()

    total_questions = Question.get_question_count()
    japanese_questions = Question.get_question_count('japanese')
    english_questions = Question.get_question_count('english')

    return jsonify({
        'status': 'active',
        'total_questions': total_questions,
        'japanese_questions': japanese_questions,
        'english_questions': english_questions,
        'config': {c.config_key: c.config_value for c in config}
    })
'''

        with open(api_blueprint_path, 'w') as f:
            f.write(blueprint_content)

    def update_app_init(self):
        """更新app/__init__.py文件,注册AI API蓝图"""
        app_init_path = 'app/__init__.py'

        if not os.path.exists(app_init_path):
            logger.error(f"文件不存在: {app_init_path}")
            return False

        with open(app_init_path, 'r') as f:
            content = f.read()

        if 'from app.blueprints.ai_brain_api import ai_brain_api' in content and 'app.register_blueprint(ai_brain_api' in content:
            logger.info("AI API蓝图已注册,跳过更新")
            return True

        updated_content = content

        if 'from app.blueprints.ai_brain_api import ai_brain_api' not in content:
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import') or line.startswith('from'):
                    import_index = i
                else:
                    break

            lines.insert(import_index + 1, 'from app.blueprints.ai_brain_api import ai_brain_api')
            updated_content = '\n'.join(lines)

        if 'app.register_blueprint(ai_brain_api' not in updated_content:
            lines = updated_content.split('\n')
            return_index = -1
            for i, line in enumerate(reversed(lines)):
                if 'return app' in line:
                    return_index = len(lines) - 1 - i
                    break

            if return_index != -1:
                lines.insert(return_index, '    # 注册AI脑库API蓝图')
                lines.insert(return_index + 1, '    app.register_blueprint(ai_brain_api, url_prefix="/api/ai-brain")')
                updated_content = '\n'.join(lines)

        with open(app_init_path, 'w') as f:
            f.write(updated_content)

        logger.info(f"更新app/__init__.py文件,注册AI API蓝图")
        return True

    def create_api_service_file(self):
        """创建API服务配置文件"""
        api_service_path = 'app/services/api_service.py'
        api_service_dir = os.path.dirname(api_service_path)

        if not os.path.exists(api_service_dir):
            os.makedirs(api_service_dir)
            logger.info(f"创建目录: {api_service_dir}")

        service_content = '''# -*- coding: utf-8 -*-
import json
import sys

class APIService:

    @staticmethod
    def get_api_config():
        """获取API配置"""
        config = {
            'main_port': 8888,
            'ai_brain_prefix': '/api/ai-brain',
            'api_rate_limit': 100,
        }
        return config

    @staticmethod
    def get_ai_brain_endpoints():
        """获取AI脑库API端点列表"""
        config = APIService.get_api_config()
        return [
            f"{config['ai_brain_prefix']}/",
            f"{config['ai_brain_prefix']}/questions",
            f"{config['ai_brain_prefix']}/generate-questions",
            f"{config['ai_brain_prefix']}/exam",
            f"{config['ai_brain_prefix']}/status"
        ]

    @staticmethod
    def validate_api_request(request):
        """验证API请求"""
        return True
'''

        with open(api_service_path, 'w') as f:
            f.write(service_content)
        logger.info(f"创建API服务配置文件: {api_service_path}")

    def enhance_ai_api(self):
        """完善AI API配置"""
        logger.info("开始AI API端口自动完善...")

        self.update_system_config(
            'api_config',
            str(self.api_config),
            'json',
            'API配置信息',
            1
        )
        self.create_ai_api_blueprint()

        self.update_app_init()

        self.create_api_service_file()

        self._validate_api_config()

        logger.info("AI API端口自动完善完成!")

    def _validate_api_config(self):
        """验证API配置"""
        logger.info("验证API配置...")

        app_init_path = 'app/__init__.py'
        if os.path.exists(app_init_path):
            with open(app_init_path, 'r') as f:
                content = f.read()
                if 'ai_brain_api' in content and 'register_blueprint' in content:
                    logger.info("✓ AI API蓝图已成功注册")
                else:
                    logger.error("✗ AI API蓝图注册失败")

        blueprint_path = 'app/blueprints/ai_brain_api.py'
        if os.path.exists(blueprint_path):
            logger.info("✓ AI API蓝图文件已创建")
        else:
            logger.error("✗ AI API蓝图文件创建失败")

        service_path = 'app/services/api_service.py'
        if os.path.exists(service_path):
            logger.info("✓ API服务配置文件已创建")
        else:
            logger.error("✗ API服务配置文件创建失败")

    def run(self):
        """执行AI API完善流程"""
        self.enhance_ai_api()

if __name__ == "__main__":
    enhancer = AIApiEnhancer()
    enhancer.run()
