# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI特征库管理器,用于管理特征库的日常操作
"""

import os
import json
import time
from datetime import datetime
import threading

from app.utils.logging import logger
from app.utils.db import db_manager
from app.ai.ai_engine_integrator import ai_engine_integrator
import logging
import sys

class FeatureLibraryManager:
    """AI特征库管理器"""

    def __init__(self):
        self.feature_library_table = "ai_feature_library"
        self.auto_extract_interval = 3600
        self.auto_extract_thread = None
        self.is_running = True
        self.feature_lock = threading.Lock()

    def start_auto_extract(self):
        """启动自动特征提取线程"""
        if not self.auto_extract_thread or not self.auto_extract_thread.is_alive():
            self.auto_extract_thread = threading.Thread(target=self._auto_extract_loop, daemon=True)
            self.auto_extract_thread.start()
            logger.info("特征库自动提取线程已启动")

    def stop_auto_extract(self):
        """停止自动特征提取线程"""
        self.is_running = False
        if self.auto_extract_thread and self.auto_extract_thread.is_alive():
            self.auto_extract_thread.join()
            logger.info("特征库自动提取线程已停止")

    def _auto_extract_loop(self):
        """自动特征提取循环"""
        while self.is_running:
            time.sleep(self.auto_extract_interval)
            self.auto_extract_features()

    def auto_extract_features(self, data_source="system_logs"):
        """自动从数据源提取特征"""
        logger.info(f"开始从{data_source}自动提取特征...")

        try:
            if data_source == "system_logs":
                features = self._extract_from_logs()
            elif data_source == "user_behavior":
                features = self._extract_from_user_behavior()
            elif data_source == "system_metrics":
                features = self._extract_from_system_metrics()
            else:
                features = []

            for feature in features:
                self.add_feature(feature)

            logger.info(f"从{data_source}自动提取特征完成,共提取{len(features)}个特征")
            return features
        except Exception as e:
            logger.error(f"自动提取特征失败: {str(e)}")
            return []

    def _extract_from_logs(self):
        """从日志中提取特征"""
        return []

    def _extract_from_user_behavior(self):
        """从用户行为中提取特征"""
        return []

    def _extract_from_system_metrics(self):
        """从系统指标中提取特征"""
        return []

    def add_feature(self, feature_data):
        """添加特征到特征库"""
        with self.feature_lock:
            try:
                feature_id = f"feature-{int(time.time()*1000)}"

                tags = str(feature_data.get("tags", [])) if feature_data.get("tags") else None
                resolution = str(feature_data.get("resolution", {})) if feature_data.get("resolution") else None

                insert_sql = f"""
                INSERT INTO {self.feature_library_table} (
                    feature_id, title, description, feature_type, status, priority, tags,
                    resolved_at, resolved_by, resolution, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                resolved_at = feature_data.get("resolved_at") if feature_data.get("resolved_at") else None

                db_manager.execute(insert_sql, (
                    feature_id, feature_data.get("title"), feature_data.get("description"),
                    feature_data.get("feature_type", "general"), feature_data.get("status", "active"),
                    feature_data.get("priority", 0), tags, resolved_at, feature_data.get("resolved_by"),
                    resolution, feature_data.get("confidence_score", 0.5)
                ))

                logger.info(f"成功添加特征: {feature_data.get('title')}")
                return feature_id
            except Exception as e:
                logger.error(f"添加特征失败: {str(e)}")
                return None

    def get_feature(self, feature_id):
        """根据特征ID获取特征"""
        try:
            select_sql = f"SELECT * FROM {self.feature_library_table} WHERE feature_id = ?"
            result = db_manager.fetch_one(select_sql, (feature_id,))

            if result:
                feature = dict(result)
                if feature.get("tags"):
                    feature["tags"] = eval(feature["tags"])
                if feature.get("resolution"):
                    feature["resolution"] = eval(feature["resolution"])
                return feature
            return None
        except Exception as e:
            logger.error(f"获取特征失败: {str(e)}")
            return None

    def get_features(self, status=None, feature_type=None, limit=100):
        """获取特征列表"""
        try:
            where_clause = []
            where_params = []

            if status:
                where_clause.append("status = ?")
                where_params.append(status)

            if feature_type:
                where_clause.append("feature_type = ?")
                where_params.append(feature_type)

            where_sql = " AND ".join(where_clause) if where_clause else "1=1"
            select_sql = f"SELECT * FROM {self.feature_library_table} WHERE {where_sql} ORDER BY created_at DESC LIMIT ?"

            results = db_manager.fetch_all(select_sql, where_params + [limit])

            features = []
            for result in results:
                feature = dict(result)
                if feature.get("tags"):
                    feature["tags"] = eval(feature["tags"])
                if feature.get("resolution"):
                    feature["resolution"] = eval(feature["resolution"])
                features.append(feature)

            return features
        except Exception as e:
            logger.error(f"获取特征列表失败: {str(e)}")
            return []

    def update_feature(self, feature_id, updates):
        """更新特征"""
        try:
            set_clause = []
            params = []
            for key, value in updates.items():
                set_clause.append(f"{key} = ?")
                params.append(value)

            params.append(feature_id)
            update_sql = f"UPDATE {self.feature_library_table} SET {', '.join(set_clause)} WHERE feature_id = ?"
            db_manager.execute(update_sql, params)
            logger.info(f"特征 {feature_id} 更新成功")
            return True
        except Exception as e:
            logger.error(f"更新特征失败: {str(e)}")
            return False

    def analyze_feature(self, feature_id):
        """分析特征: 使用AI引擎评估特征的重要性和影响"""
        logger.info(f"开始分析特征: {feature_id}")
        try:
            feature = self.get_feature(feature_id)
            if not feature:
                logger.error(f"特征不存在: {feature_id}")
                return None

            prompt = f"请分析以下系统特征的重要性和影响:\n\n特征标题:{feature['title']}\n特征描述:{feature['description']}\n特征类型:{feature['feature_type']}\n特征状态:{feature['status']}\n\n请从以下几个方面进行分析:\n1. 特征的重要性评分(0-1,保留两位小数)\n2. 特征对系统的影响范围\n3. 特征的优先级建议\n4. 特征的解决建议\n\n请按照清晰的格式返回分析结果."

            response = ai_engine_integrator.call_engine("zhipu", prompt)
            if response and response.get("code") == 0:
                analysis = response.get("data", {}).get("response", "")

                self.update_feature(feature_id, {
                    "analysis": analysis,
                    "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                logger.info(f"特征分析完成: {feature_id}")
                return analysis
            return None
        except Exception as e:
            logger.error(f"分析特征失败: {str(e)}")
            return None

    def get_feature_statistics(self):
        """获取特征库统计信息"""
        try:
            status_stats_sql = f"SELECT status, COUNT(*) as count FROM {self.feature_library_table} GROUP BY status"
            status_stats = db_manager.fetch_all(status_stats_sql)

            type_stats_sql = f"SELECT feature_type, COUNT(*) as count FROM {self.feature_library_table} GROUP BY feature_type"
            type_stats = db_manager.fetch_all(type_stats_sql)

            total_sql = f"SELECT COUNT(*) as total FROM {self.feature_library_table}"
            total = db_manager.fetch_one(total_sql)['total']

            return {
                'total': total,
                'by_status': {row['status']: row['count'] for row in status_stats},
                'by_type': {row['feature_type']: row['count'] for row in type_stats}
            }
        except Exception as e:
            logger.error(f"获取特征统计失败: {str(e)}")
            return {}
