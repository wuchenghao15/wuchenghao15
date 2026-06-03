#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上报登录跳转问题给AI员工处理,并上报特征库
"""

import os
import time
from app.utils.logging import logger
from app.ai.ai_ensemble import AIEnsemble
from app.config import Config


class LoginRedirectIssueReporter:
    def __init__(self):
        self.ai_ensemble = AIEnsemble()
        self.api_base_url = f"http://localhost:{Config.PORT}" if hasattr(Config, 'PORT') else "http://localhost:8888"

    def report_issue(self):
        """上报登录跳转问题给AI员工处理"""
        logger.info("开始上报登录跳转问题给AI员工...")

        issue_data = {
            "issue_id": f"issue_{int(time.time())}_{hash('login_redirect')}",
            "issue_type": "bug",
            "title": "index 显示登录成功 没有跳转",
            "description": "用户登录成功后,停留在首页(index),没有自动跳转到预期页面",
            "severity": "medium",
            "status": "pending",
            "reported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reported_by": "system",
            "feature_affected": "authentication",
            "location": {
                "file": "app/views/main.py",
                "function": "index",
                "line": 20
            },
            "expected_behavior": "用户登录成功后,应该自动跳转到combined_test页面",
            "actual_behavior": "用户登录成功后,停留在首页",
            "environment": {
                "app_version": "1.0.0",
                "python_version": "3.8+",
                "flask_version": "2.0+",
                "database": "SQLite"
            }
        }
        logger.info(f"收集到的问题信息: {str(issue_data)}")

        try:
            result = self.ai_ensemble.dispatch_task("bug_fix", issue_data)
            logger.info(f"AI员工任务调度结果: {str(result)}")
            self.report_to_feature_library(issue_data)
            return {
                "success": True,
                "message": "登录跳转问题已成功上报给AI员工处理",
                "issue_id": issue_data["issue_id"],
                "ai_result": result
            }
        except Exception as e:
            logger.error(f"上报问题给AI员工时发生错误: {str(e)}")
            return {
                "success": False,
                "message": f"上报问题给AI员工时发生错误: {str(e)}"
            }

    def report_to_feature_library(self, issue_data):
        """将问题特征上报到特征库"""
        logger.info("开始上报特征库...")

        feature_data = {
            "feature_id": f"feature_{int(time.time())}_{hash('login_redirect_feature')}",
            "type": "bug",
            "title": issue_data["title"],
            "description": issue_data["description"],
            "severity": issue_data["severity"],
            "feature_category": "authentication",
            "affected_functionality": "login_redirect",
            "location": issue_data["location"],
            "issue_details": issue_data,
            "reported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "root_cause": "index路由没有检查用户登录状态,导致已登录用户仍停留在首页",
            "suggested_fix": "修改index路由,添加登录状态检查,已登录用户自动重定向到combined_test页面",
            "expected_impact": "提高用户体验,确保登录流程完整性"
        }

        try:
            feature_library_path = "feature_library.json"
            if os.path.exists(feature_library_path):
                with open(feature_library_path, 'r', encoding='utf-8') as f:
                    import json
                    feature_library = json.load(f)
            else:
                feature_library = {
                    "version": "1.0.0",
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "features": []
                }

            feature_library["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            feature_library["features"].append(feature_data)

            with open(feature_library_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(feature_library, f, ensure_ascii=False, indent=2)

            logger.info(f"特征库上报成功,特征ID: {feature_data['feature_id']}")
            logger.info(f"特征库已保存到: {feature_library_path}")

            return {
                "success": True,
                "message": "特征库上报成功",
                "feature_id": feature_data["feature_id"]
            }
        except Exception as e:
            logger.error(f"上报特征库时发生错误: {str(e)}")
            return {
                "success": False,
                "message": f"上报特征库时发生错误: {str(e)}"
            }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    reporter = LoginRedirectIssueReporter()
    result = reporter.report_issue()
    print(str(result))
