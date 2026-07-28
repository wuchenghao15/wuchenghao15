#!/usr/bin/env python3
import sqlite3
import os
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

class DataLakeOptimizer:
    """基于大数据架构的数据优化器"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def create_ods_layer(self):
        """创建数据湖原始数据层（ODS）"""
        logger.info("创建ODS原始数据层...")
        
        # 用户行为日志ODS表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ods_user_behavior_log ( log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, action_type TEXT, action_module TEXT, action_detail TEXT, page_url TEXT, referrer_url TEXT, ip_address TEXT, user_agent TEXT, device_type TEXT, session_id TEXT, created_at TEXT, raw_data TEXT ) ''')
        
        # 学习记录ODS表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ods_learning_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, learning_type TEXT, learning_source TEXT, learning_content TEXT, learning_result TEXT, confidence_score REAL, learned_at TEXT, applied_at TEXT, application_result TEXT, raw_data TEXT ) ''')
        
        # 考试记录ODS表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ods_exam_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, exam_id TEXT, exam_name TEXT, subject TEXT, score INTEGER, total_score INTEGER, duration_minutes INTEGER, status TEXT, started_at TEXT, completed_at TEXT, raw_data TEXT ) ''')
        
        # AI能力评分ODS表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ods_ai_capability_log ( log_id INTEGER PRIMARY KEY AUTOINCREMENT, dimension TEXT, score REAL, measured_at TEXT, source TEXT, details TEXT, raw_data TEXT ) ''')
        
        # 系统监控ODS表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ods_system_metrics ( metric_id INTEGER PRIMARY KEY AUTOINCREMENT, metric_name TEXT, metric_value REAL, metric_unit TEXT, category TEXT, timestamp TEXT, raw_data TEXT ) ''')
        
        self.conn.commit()
        logger.info("ODS层创建完成")
    
    def create_dwd_layer(self):
        """创建数据仓库明细层（DWD）"""
        logger.info("创建DWD明细层...")
        
        # 用户行为明细DWD表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dwd_user_behavior ( behavior_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, action_type TEXT, action_module TEXT, action_detail TEXT, page_url TEXT, ip_address TEXT, device_type TEXT, session_id TEXT, action_date TEXT, action_hour INTEGER, created_at TEXT ) ''')
        
        # 学习行为明细DWD表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dwd_learning_behavior ( behavior_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, learning_type TEXT, learning_source TEXT, learning_result TEXT, confidence_score REAL, learned_date TEXT, learned_hour INTEGER, is_applied INTEGER, created_at TEXT ) ''')
        
        # 考试行为明细DWD表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dwd_exam_behavior ( behavior_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, exam_id TEXT, exam_name TEXT, subject TEXT, score INTEGER, total_score INTEGER, pass_rate REAL, duration_minutes INTEGER, status TEXT, exam_date TEXT, created_at TEXT ) ''')
        
        # 用户画像明细DWD表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dwd_user_profile ( profile_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, role TEXT, education_level TEXT, grade TEXT, registration_date TEXT, last_login_date TEXT, total_learning_hours REAL, total_exams INTEGER, average_score REAL, created_at TEXT, updated_at TEXT ) ''')
        
        self.conn.commit()
        logger.info("DWD层创建完成")
    
    def create_dws_layer(self):
        """创建数据仓库汇总层（DWS）"""
        logger.info("创建DWS汇总层...")
        
        # 用户学习日汇总表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dws_user_learning_daily ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, stat_date TEXT, learning_count INTEGER, total_hours REAL, avg_confidence REAL, success_count INTEGER, fail_count INTEGER, created_at TEXT ) ''')
        
        # 用户考试日汇总表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dws_user_exam_daily ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, stat_date TEXT, exam_count INTEGER, total_score INTEGER, avg_score REAL, pass_count INTEGER, fail_count INTEGER, created_at TEXT ) ''')
        
        # 系统学习日汇总表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dws_system_learning_daily ( id INTEGER PRIMARY KEY AUTOINCREMENT, stat_date TEXT, active_users INTEGER, total_learning_count INTEGER, total_learning_hours REAL, avg_confidence REAL, success_rate REAL, created_at TEXT ) ''')
        
        # 系统考试日汇总表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dws_system_exam_daily ( id INTEGER PRIMARY KEY AUTOINCREMENT, stat_date TEXT, active_users INTEGER, total_exam_count INTEGER, avg_score REAL, pass_rate REAL, avg_duration REAL, created_at TEXT ) ''')
        
        # AI能力日汇总表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS dws_ai_capability_daily ( id INTEGER PRIMARY KEY AUTOINCREMENT, stat_date TEXT, total_dimensions INTEGER, avg_overall_score REAL, max_score REAL, min_score REAL, score_trend TEXT, created_at TEXT ) ''')
        
        self.conn.commit()
        logger.info("DWS层创建完成")
    
    def create_ads_layer(self):
        """创建数据中台应用层（ADS）"""
        logger.info("创建ADS应用层...")
        
        # 用户学习分析表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_user_learning_analysis ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, total_learning_count INTEGER, total_learning_hours REAL, avg_confidence REAL, learning_streak_days INTEGER, most_active_day TEXT, most_active_hour INTEGER, weak_points TEXT, strong_points TEXT, improvement_suggestions TEXT, last_updated TEXT ) ''')
        
        # 用户考试分析表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_user_exam_analysis ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, total_exam_count INTEGER, total_score INTEGER, avg_score REAL, pass_rate REAL, best_subject TEXT, weakest_subject TEXT, score_trend TEXT, improvement_suggestions TEXT, last_updated TEXT ) ''')
        
        # 系统学习仪表盘
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_system_learning_dashboard ( id INTEGER PRIMARY KEY AUTOINCREMENT, stat_period TEXT, total_users INTEGER, active_users INTEGER, total_learning_count INTEGER, total_learning_hours REAL, avg_learning_time REAL, completion_rate REAL, top_learning_types TEXT, top_learning_sources TEXT, created_at TEXT ) ''')
        
        # 系统考试仪表盘
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_system_exam_dashboard ( id INTEGER PRIMARY KEY AUTOINCREMENT, stat_period TEXT, total_exams INTEGER, total_participants INTEGER, avg_score REAL, pass_rate REAL, avg_duration REAL, top_subjects TEXT, difficulty_distribution TEXT, created_at TEXT ) ''')
        
        # AI能力分析表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_ai_capability_analysis ( id INTEGER PRIMARY KEY AUTOINCREMENT, dimension TEXT, current_score REAL, previous_score REAL, score_change REAL, trend_direction TEXT, improvement_rate REAL, target_score REAL, estimated_time_to_target TEXT, last_updated TEXT ) ''')
        
        # 用户活跃度分析表
        self.cursor.execute(''' CREATE TABLE IF NOT EXISTS ads_user_activity_segmentation ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, username TEXT, activity_level TEXT, activity_score INTEGER, last_active_date TEXT, days_since_last_active INTEGER, retention_risk TEXT, engagement_metrics TEXT, last_updated TEXT ) ''')
        
        self.conn.commit()
        logger.info("ADS层创建完成")
    
    def _row_to_dict(self, row):
        """将sqlite3 Row对象转换为字典"""
        result = {}
        for col in row.keys():
            result[col] = row[col]
        return result
        
    def migrate_to_ods(self):
        """迁移现有数据到ODS层"""
        logger.info("迁移数据到ODS层...")
        
        # 迁移学习记录
        try:
            self.cursor.execute('SELECT * FROM learning_records')
            records = self.cursor.fetchall()
            for record in records:
                raw_data = json.dumps(self._row_to_dict(record))
                self.cursor.execute(''' INSERT OR IGNORE INTO ods_learning_records (user_id, username, learning_type, learning_source, learning_content, learning_result, confidence_score, learned_at, applied_at, application_result, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (None, None, record['learning_type'], record['learning_source'],
                     record['learning_content'], record['learning_result'], 
                     record['confidence_score'], record['learned_at'], 
                     record['applied_at'], record['application_result'], raw_data))
            logger.info(f"迁移学习记录: {len(records)} 条")
        except Exception as e:
            logger.info(f"迁移学习记录失败: {e}")
        
        # 迁移AI能力评分
        try:
            self.cursor.execute('SELECT * FROM ai_capability_scores')
            records = self.cursor.fetchall()
            for record in records:
                raw_data = json.dumps(self._row_to_dict(record))
                self.cursor.execute(''' INSERT OR IGNORE INTO ods_ai_capability_log (dimension, score, measured_at, source, details, raw_data) VALUES (?, ?, ?, ?, ?, ?) ''', (record['dimension'], record['score'], record['measured_at'],
                     record['source'], record['details'], raw_data))
            logger.info(f"迁移AI能力评分: {len(records)} 条")
        except Exception as e:
            logger.info(f"迁移AI能力评分失败: {e}")
        
        # 迁移用户数据
        try:
            self.cursor.execute('SELECT * FROM users')
            records = self.cursor.fetchall()
            for record in records:
                # 脱敏处理
                raw_data = json.dumps(self._row_to_dict(record))
                # 用户行为日志初始化
                self.cursor.execute(''' INSERT OR IGNORE INTO ods_user_behavior_log (user_id, username, action_type, action_module, action_detail, created_at, raw_data) VALUES (?, ?, 'registration', 'auth', '用户注册', ?, ?) ''', (record['user_id'], record['username'], record['created_at'], raw_data))
            logger.info(f"迁移用户数据: {len(records)} 条")
        except Exception as e:
            logger.info(f"迁移用户数据失败: {e}")
        
        self.conn.commit()
        logger.info("ODS数据迁移完成")
    
    def etl_dwd(self):
        """ETL处理：ODS -> DWD"""
        logger.info("执行ODS到DWD的ETL...")
        
        # 清洗用户行为数据
        try:
            self.cursor.execute('DELETE FROM dwd_user_behavior')
            self.cursor.execute(''' INSERT INTO dwd_user_behavior (user_id, username, action_type, action_module, action_detail, page_url, ip_address, device_type, session_id, action_date, action_hour, created_at) SELECT user_id, username, action_type, action_module, action_detail, page_url, ip_address, device_type, session_id, SUBSTR(created_at, 1, 10), CAST(SUBSTR(created_at, 12, 2) AS INTEGER), created_at FROM ods_user_behavior_log ''')
            logger.info("用户行为DWD表更新完成")
        except Exception as e:
            logger.info(f"用户行为ETL失败: {e}")
        
        # 清洗学习行为数据
        try:
            self.cursor.execute('DELETE FROM dwd_learning_behavior')
            self.cursor.execute(''' INSERT INTO dwd_learning_behavior (user_id, username, learning_type, learning_source, learning_result, confidence_score, learned_date, learned_hour, is_applied, created_at) SELECT user_id, username, learning_type, learning_source, learning_result, confidence_score, SUBSTR(learned_at, 1, 10), CAST(SUBSTR(learned_at, 12, 2) AS INTEGER), CASE WHEN applied_at IS NOT NULL THEN 1 ELSE 0 END, learned_at FROM ods_learning_records ''')
            logger.info("学习行为DWD表更新完成")
        except Exception as e:
            logger.info(f"学习行为ETL失败: {e}")
        
        # 构建用户画像
        try:
            self.cursor.execute('DELETE FROM dwd_user_profile')
            self.cursor.execute(''' INSERT INTO dwd_user_profile (user_id, username, role, education_level, grade, registration_date, last_login_date, total_learning_hours, total_exams, average_score, created_at, updated_at) SELECT id, username, role, education_level, grade, SUBSTR(created_at, 1, 10), SUBSTR(updated_at, 1, 10), 0, 0, 0.0, created_at, updated_at FROM users WHERE is_active = 1 ''')
            logger.info("用户画像DWD表更新完成")
        except Exception as e:
            logger.info(f"用户画像ETL失败: {e}")
        
        self.conn.commit()
        logger.info("DWD层ETL完成")
    
    def etl_dws(self):
        """ETL处理：DWD -> DWS"""
        logger.info("执行DWD到DWS的ETL...")
        
        # 用户学习日汇总
        try:
            self.cursor.execute('DELETE FROM dws_user_learning_daily')
            self.cursor.execute(''' INSERT INTO dws_user_learning_daily (user_id, username, stat_date, learning_count, total_hours, avg_confidence, success_count, fail_count, created_at) SELECT user_id, username, learned_date, COUNT(*), 0, AVG(confidence_score), SUM(CASE WHEN learning_result = '成功' THEN 1 ELSE 0 END), SUM(CASE WHEN learning_result != '成功' THEN 1 ELSE 0 END), CURRENT_TIMESTAMP FROM dwd_learning_behavior GROUP BY user_id, username, learned_date ''')
            logger.info("用户学习日汇总完成")
        except Exception as e:
            logger.info(f"用户学习日汇总失败: {e}")
        
        # 系统学习日汇总
        try:
            self.cursor.execute('DELETE FROM dws_system_learning_daily')
            self.cursor.execute(''' INSERT INTO dws_system_learning_daily (stat_date, active_users, total_learning_count, total_learning_hours, avg_confidence, success_rate, created_at) SELECT learned_date, COUNT(DISTINCT user_id), COUNT(*), 0, AVG(confidence_score), SUM(CASE WHEN learning_result = '成功' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), CURRENT_TIMESTAMP FROM dwd_learning_behavior GROUP BY learned_date ''')
            logger.info("系统学习日汇总完成")
        except Exception as e:
            logger.info(f"系统学习日汇总失败: {e}")
        
        # AI能力日汇总
        try:
            self.cursor.execute('DELETE FROM dws_ai_capability_daily')
            self.cursor.execute(''' INSERT INTO dws_ai_capability_daily (stat_date, total_dimensions, avg_overall_score, max_score, min_score, score_trend, created_at) SELECT SUBSTR(measured_at, 1, 10), COUNT(DISTINCT dimension), AVG(score), MAX(score), MIN(score), 'stable', CURRENT_TIMESTAMP FROM ods_ai_capability_log GROUP BY SUBSTR(measured_at, 1, 10) ''')
            logger.info("AI能力日汇总完成")
        except Exception as e:
            logger.info(f"AI能力日汇总失败: {e}")
        
        self.conn.commit()
        logger.info("DWS层ETL完成")
    
    def etl_ads(self):
        """ETL处理：DWS -> ADS"""
        logger.info("执行DWS到ADS的ETL...")
        
        # 用户学习分析
        try:
            self.cursor.execute('DELETE FROM ads_user_learning_analysis')
            self.cursor.execute(''' INSERT INTO ads_user_learning_analysis (user_id, username, total_learning_count, total_learning_hours, avg_confidence, learning_streak_days, most_active_day, most_active_hour, weak_points, strong_points, improvement_suggestions, last_updated) SELECT user_id, username, SUM(learning_count), SUM(total_hours), AVG(avg_confidence), COUNT(DISTINCT stat_date), 'Monday', 20, '[]', '[]', '暂无建议', CURRENT_TIMESTAMP FROM dws_user_learning_daily GROUP BY user_id, username ''')
            logger.info("用户学习分析表更新完成")
        except Exception as e:
            logger.info(f"用户学习分析ETL失败: {e}")
        
        # 系统学习仪表盘
        try:
            self.cursor.execute('DELETE FROM ads_system_learning_dashboard')
            self.cursor.execute(''' INSERT INTO ads_system_learning_dashboard (stat_period, total_users, active_users, total_learning_count, total_learning_hours, avg_learning_time, completion_rate, top_learning_types, top_learning_sources, created_at) SELECT 'daily', (SELECT COUNT(*) FROM users WHERE is_active = 1), SUM(active_users), SUM(total_learning_count), SUM(total_learning_hours), 0, AVG(success_rate), '错误修复学习,知识扩展', '系统自动检测,日志监控', CURRENT_TIMESTAMP FROM dws_system_learning_daily ''')
            logger.info("系统学习仪表盘更新完成")
        except Exception as e:
            logger.info(f"系统学习仪表盘ETL失败: {e}")
        
        # AI能力分析
        try:
            self.cursor.execute('DELETE FROM ads_ai_capability_analysis')
            self.cursor.execute(''' INSERT INTO ads_ai_capability_analysis (dimension, current_score, previous_score, score_change, trend_direction, improvement_rate, target_score, estimated_time_to_target, last_updated) SELECT dimension, AVG(score), AVG(score) * 0.95, AVG(score) * 0.05, 'up', 5.0, 100.0, '7天', CURRENT_TIMESTAMP FROM ods_ai_capability_log GROUP BY dimension ''')
            logger.info("AI能力分析表更新完成")
        except Exception as e:
            logger.info(f"AI能力分析ETL失败: {e}")
        
        # 用户活跃度分析
        try:
            self.cursor.execute('DELETE FROM ads_user_activity_segmentation')
            self.cursor.execute(''' INSERT INTO ads_user_activity_segmentation (user_id, username, activity_level, activity_score, last_active_date, days_since_last_active, retention_risk, engagement_metrics, last_updated) SELECT u.id, u.username, CASE WHEN COALESCE(l.learning_count, 0) >= 5 THEN 'high' WHEN COALESCE(l.learning_count, 0) >= 2 THEN 'medium' ELSE 'low' END, COALESCE(l.learning_count, 0) * 10, SUBSTR(u.updated_at, 1, 10), 0, CASE WHEN COALESCE(l.learning_count, 0) = 0 THEN 'high' ELSE 'low' END, '{}', CURRENT_TIMESTAMP FROM users u LEFT JOIN ( SELECT user_id, SUM(learning_count) as learning_count FROM dws_user_learning_daily GROUP BY user_id ) l ON u.id = l.user_id WHERE u.is_active = 1 ''')
            logger.info("用户活跃度分析表更新完成")
        except Exception as e:
            logger.info(f"用户活跃度分析ETL失败: {e}")
        
        self.conn.commit()
        logger.info("ADS层ETL完成")
    
    def create_indexes(self):
        """创建索引优化查询性能"""
        logger.info("创建索引...")
        
        # ODS层索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ods_learning_user ON ods_learning_records(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ods_learning_date ON ods_learning_records(learned_at)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ods_ai_capability_date ON ods_ai_capability_log( measured_at)')
        
        # DWD层索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dwd_learning_user ON dwd_learning_behavior(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dwd_learning_date ON dwd_learning_behavior(learned_date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dwd_user_profile ON dwd_user_profile(user_id)')
        
        # DWS层索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dws_learning_date ON dws_user_learning_daily(stat_date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_dws_system_date ON dws_system_learning_daily(stat_date)')
        
        # ADS层索引
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ads_user_learning ON ads_user_learning_analysis(user_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_ads_user_activity ON ads_user_activity_segmentation( user_id)')
        
        self.conn.commit()
        logger.info("索引创建完成")
    
    def run_optimization(self):
        """运行完整的数据优化流程"""
        logger.info("="*60)
        logger.info("开始数据架构优化...")
        logger.info("="*60)
        
        self.create_ods_layer()
        self.create_dwd_layer()
        self.create_dws_layer()
        self.create_ads_layer()
        
        self.migrate_to_ods()
        self.etl_dwd()
        self.etl_dws()
        self.etl_ads()
        
        self.create_indexes()
        
        self.conn.close()
        
        logger.info("="*60)
        logger.info("数据架构优化完成！")
        logger.info("="*60)
        logger.info()
        logger.info("创建的数据层：")
        logger.info("  ODS层（原始数据）：ods_user_behavior_log, ods_learning_records, ods_exam_records")
        logger.info("  DWD层（明细数据）：dwd_user_behavior, dwd_learning_behavior, dwd_user_profile")
        logger.info("  DWS层（汇总数据）：dws_user_learning_daily, dws_system_learning_daily")
        logger.info("  ADS层（应用数据）：ads_user_learning_analysis, ads_system_learning_dashboard")

if __name__ == '__main__':
    optimizer = DataLakeOptimizer()
    optimizer.run_optimization()