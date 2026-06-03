# -*- coding: utf-8 -*-
import os
import logging
# JSON import removed - using database
import time
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_brain_complete_enhancer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIBrainCompleteEnhancer:
    def __init__(self):
        self.db_path = 'app.db'
        self.enhancement_config = {
            'auto_backup': True,
            'backup_frequency': 'daily',
            'auto_cleanup': True,
            'cleanup_frequency': 'weekly',
            'auto_update': True,
            'update_frequency': 'daily',
            'auto_optimize': True,
            'optimize_frequency': 'weekly',
            'auto_monitor': True,
            'monitor_interval': 60,
            'auto_recover': True
        }

    def run_all_enhancements(self):
        """运行所有AI脑库完善机制"""
        logger.info("=== 开始AI脑库全面自动完善 ===")

        start_time = time.time()

        try:
            # 1. 运行现有完善器
            self._run_existing_enhancers()

            # 2. 完善备份机制
            self._enhance_backup_mechanism()

            # 3. 完善清理机制
            self._enhance_cleanup_mechanism()

            # 4. 完善更新机制
            self._enhance_update_mechanism()

            # 5. 完善优化机制
            self._enhance_optimize_mechanism()

            # 6. 完善监控机制
            self._enhance_monitor_mechanism()

            # 7. 完善恢复机制
            self._enhance_recover_mechanism()

            end_time = time.time()
            logger.info(f"=== AI脑库全面自动完善完成!耗时: {end_time - start_time:.2f}秒 ===")

        except Exception as e:
            logger.error(f"AI脑库自动完善失败: {e}")

    def _run_existing_enhancers(self):
        """运行现有完善器"""
        logger.info("运行现有完善器...")

        # 运行系统规则完善器
        try:
            import ai_rule_enhancer
            enhancer = ai_rule_enhancer.AIRuleEnhancer()
            enhancer.enhance_system_rules()
        except ImportError:
            logger.warning("未找到 ai_rule_enhancer,跳过规则完善")
        except Exception as e:

        # 运行API端口完善器
            import ai_api_enhancer
            enhancer = ai_api_enhancer.AIApiEnhancer()
            enhancer.enhance_ai_api()
        except ImportError:
            logger.warning("未找到 ai_api_enhancer,跳过API端口完善")
        except Exception as e:
        # 运行中间件完善器
            import ai_middleware_enhancer
            enhancer = ai_middleware_enhancer.AIMiddlewareEnhancer()
            enhancer.enhance_ai_middleware()
        except ImportError:
            logger.warning("未找到 ai_middleware_enhancer,跳过中间件完善")
        except Exception as e:
            logger.error(f"中间件完善失败: {e}")

    def _enhance_backup_mechanism(self):
        """完善备份机制"""
        logger.info("完善AI脑库备份机制...")

        # 确保备份目录存在
        backup_dir = 'backups/ai_brain'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"创建备份目录: {backup_dir}")

        # 更新系统配置
        self._update_system_config(
            'ai_brain_backup_config',
            str({
                'enabled': True,
                'backup_dir': backup_dir,
                'keep_backups_days': 30,
                'auto_backup_on_update': True,
                'backup_format': 'sqlite'
            }),
            'json',
            'AI脑库备份配置'
        )

        logger.info("AI脑库备份机制完善完成")

    def _enhance_cleanup_mechanism(self):
        """完善清理机制"""
        logger.info("完善AI脑库清理机制...")

        # 更新系统配置
        self._update_system_config(
            'ai_brain_cleanup_config',
            str({
                'enabled': True,
                'cleanup_frequency': 'weekly',
                'remove_old_questions_days': 90,
                'remove_duplicate_questions': True,
                'optimize_database': True
            }),
            'AI脑库清理配置'
        )

        logger.info("AI脑库清理机制完善完成")

    def _enhance_update_mechanism(self):
        """完善更新机制"""

        # 更新系统配置
        self._update_system_config(
            'ai_brain_update_config',
            str({
                'enabled': True,
                'max_questions_per_update': 20,
                'auto_approve_questions': False,
            }),
            'json',
            'AI脑库更新配置'
        )

        logger.info("AI脑库更新机制完善完成")

    def _enhance_optimize_mechanism(self):
        """完善优化机制"""
        logger.info("完善AI脑库优化机制...")

        self._update_system_config(
            'ai_brain_optimize_config',
            str({
                'enabled': True,
                'optimize_frequency': 'weekly',
                'analyze_question_usage': True,
                'optimize_query_performance': True,
                'compress_database': True,
                'rebuild_indexes': True
            }),

        )
        logger.info("AI脑库优化机制完善完成")

    def _enhance_monitor_mechanism(self):
        """完善监控机制"""
        logger.info("完善AI脑库监控机制...")
        # 更新系统配置
        self._update_system_config(
            'ai_brain_monitor_config',
            str({
                'monitor_interval': 60,
                'monitor_metrics': ['cpu', 'memory', 'disk', 'response_time', 'error_rate'],
                'alert_thresholds': {
                    'memory': 80,
                    'disk': 90,
                    'response_time': 5,
                    'error_rate': 5
                },
                'alert_channels': ['log', 'email']
            }),
            'json',
            'AI脑库监控配置'
        )

    def _enhance_recover_mechanism(self):
        logger.info("完善AI脑库恢复机制...")
        # 更新系统配置
        self._update_system_config(
            'ai_brain_recover_config',
            {
                'enabled': True,
                'auto_recover_on_failure': True,
                'recovery_strategy': 'latest_backup',
                'test_recovery_on_backup': True,
            },
            'json',
            'AI脑库恢复配置'
        )

        logger.info("AI脑库恢复机制完善完成")

    def _update_system_config(self, config_key, config_value, config_type='json', description='', is_active=1):
        """更新系统配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                current_time = datetime.now().isoformat()
                
                # 检查配置是否存在
                cursor.execute("SELECT config_key FROM system_config WHERE config_key = ?", (config_key,))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute('''
                        UPDATE system_config
                        SET config_value = ?, config_type = ?, description = ?, is_active = ?, updated_at = ?
                        WHERE config_key = ?
                    ''', (config_value, config_type, description, is_active, current_time, config_key))
                    logger.info(f"更新系统配置: {config_key} -> {config_value}")
                else:
                    # 创建新配置
                    cursor.execute('''
                        INSERT INTO system_config
                        (config_key, config_value, config_type, description, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (config_key, config_value, config_type, description, is_active, current_time, current_time))
                    logger.info(f"创建系统配置: {config_key} -> {config_value}")
                
                conn.commit()
        except Exception as e:
            logger.error(f"更新系统配置失败: {e}")
    def create_cron_job(self):
        """创建定时任务,定期运行自动完善"""
        logger.info("创建AI脑库自动完善定时任务...")

        # 创建cron脚本
        cron_script_path = os.path.join(os.path.dirname(__file__), 'ai_brain_auto_enhance.sh')
        with open(cron_script_path, 'w') as f:
            f.write('''#!/bin/bash
# AI脑库自动完善定时脚本

cd "$(dirname "$0")"
python3 ai_brain_complete_enhancer.py
''')

        # 设置脚本可执行权限
        os.chmod(cron_script_path, 0o755)

        logger.info(f"创建定时脚本: {cron_script_path}")
        logger.info("请手动将以下内容添加到crontab中,以每天凌晨3点运行自动完善:")
        logger.info(f"0 3 * * * {os.path.abspath(cron_script_path)}")

        logger.info("AI脑库自动完善定时任务创建完成")

    def run(self):
        """执行完整的AI脑库自动完善流程"""
        self.run_all_enhancements()
        self.create_cron_job()

if __name__ == "__main__":
    enhancer = AIBrainCompleteEnhancer()
    enhancer.run()
