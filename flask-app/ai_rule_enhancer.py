# -*- coding: utf-8 -*-
import sqlite3
# JSON import removed - using database
import logging
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_rule_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIRuleEnhancer:
    def __init__(self):
        self.db_path = 'app.db'
        self.required_rules = self._define_required_rules()

    def _define_required_rules(self):
        """定义系统必须的规则"""
        return {
            # 系统安全规则
            'system_security_protection': {
                'value': str({
                    'enabled': True,
                    'protection_level': 'medium',
                    'auto_recover': True,
                    'backup_frequency': 'daily',
                    'log_retention_days': 30
                }),
                'type': 'json',
                'description': '系统安全保护配置，包括自动恢复、备份频率和日志保留策略',
                'is_active': 1
            },
            # AI脑库规则
            'ai_brain_auto_update': {
                    'enabled': True,
                    'max_questions_per_update': 20,
                    'languages': ['japanese', 'english']
                }),
                'type': 'json',
                'is_active': 1
            # 考试生成规则
            'exam_generator_config': {
                    'max_questions_per_exam': 50,
                        'medium': 50,
                        'hard': 20
                    },
                    'question_types': ['multiple_choice', 'true_false', 'short_answer', 'essay']
                }),
                'type': 'json',
                'description': '考试生成器配置，控制试卷难度分布和题型比例',
                'is_active': 1
            # 用户管理规则
                    'auto_approve_new_users': False,
                    'password_expiry_days': 90,
                    'max_login_attempts': 5,
                }),
                'type': 'json',
                'is_active': 1
            },
            'data_cleanup_rules': {
                    'enabled': True,
                    'cleanup_frequency': 'weekly',
                    'remove_old_test_results_days': 365,
                }),
                'type': 'json',
                'description': '数据清理规则，自动清理过期数据和临时文件',
            },
            # AI考试评分规则
            'ai_exam_scoring': {
                    'max_response_time_seconds': 30,
                    'enable_feedback': True
                }),
                'is_active': 1
            },
            # 系统日志规则
            'system_logging_rules': {
                    'log_level': 'info',
                    'max_log_file_size_mb': 100
                }),
                'type': 'json',
                'description': '系统日志规则，控制日志级别和存储方式',
        }

    def connect_db(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)
    def get_all_rules(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT config_key, config_value, config_type, description, is_active FROM system_config;')
        rules = cursor.fetchall()
        return {rule[0]: {
            'type': rule[2],
            'description': rule[3],
            'is_active': rule[4]
        } for rule in rules}

        """创建新规则"""
        conn = self.connect_db()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO system_config
            (config_key, config_value, config_type, description, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            config_key,
            rule_data['value'],
            rule_data['type'],
            rule_data['is_active'],
            current_time,
            current_time
        ))

        conn.commit()
        conn.close()
        logger.info(f"创建新规则: {config_key} - {rule_data['description']}")

    def update_rule(self, config_key, rule_data):
        """更新现有规则"""
        conn = self.connect_db()
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()

        cursor.execute('''
            UPDATE system_config
            SET config_value = ?, config_type = ?, description = ?, is_active = ?, updated_at = ?
            WHERE config_key = ?
        ''', (
            rule_data['value'],
            rule_data['type'],
            rule_data['description'],
            rule_data['is_active'],
            current_time,
            config_key
        ))

        conn.commit()
        conn.close()
        logger.info(f"更新规则: {config_key} - {rule_data['description']}")

    def enhance_system_rules(self):
        """完善系统规则"""
        logger.info("开始AI自动完善系统规则...")

        # 获取现有规则
        existing_rules = self.get_all_rules()
        logger.info(f"当前系统共有 {len(existing_rules)} 条规则")

        # 检查并完善规则
        created_count = 0
        updated_count = 0

        for rule_key, rule_data in self.required_rules.items():
            if rule_key not in existing_rules:
                # 创建缺失的规则
                self.create_rule(rule_key, rule_data)
            else:
                # 更新现有规则（如果需要）
                if existing_rule['is_active'] != rule_data['is_active'] or existing_rule['description'] != rule_data['description']:
                    self.update_rule(rule_key, rule_data)
                    updated_count += 1


        self._check_redundant_rules(existing_rules)
        # 验证所有规则的完整性

        """检查冗余规则"""
        for rule_key in existing_rules:
            if rule_key not in self.required_rules and 'fix_log' not in rule_key and 'approach' not in rule_key:
                redundant_rules.append(rule_key)

            logger.warning(f"发现可能的冗余规则: {', '.join(redundant_rules)}")
        else:
            logger.info("没有发现冗余规则")

    def _validate_rules(self):
        """验证规则的完整性和有效性"""
        logger.info("开始验证系统规则...")

        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT config_key, config_value, config_type FROM system_config WHERE is_active=1;')
        active_rules = cursor.fetchall()
        conn.close()

        valid_count = 0
        invalid_rules = []

        for rule in active_rules:
            config_key, config_value, config_type = rule
            if config_type == 'json':
                try:
                    eval(config_value)
                    valid_count += 1
                except json.JSONDecodeError:
                    invalid_rules.append(config_key)
            else:
                valid_count += 1

        if invalid_rules:
            logger.error(f"发现无效规则: {', '.join(invalid_rules)}")
        else:
            logger.info(f"所有 {valid_count} 条激活规则验证通过")

    def run(self):
        """执行AI规则完善流程"""
        self.enhance_system_rules()

if __name__ == "__main__":
    enhancer = AIRuleEnhancer()
    enhancer.run()
