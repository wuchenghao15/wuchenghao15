# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建设计师AI员工
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_designer_ai():
    """创建设计师AI员工"""
    db_path = "app.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        designer_ai = {
            "ai_name": "designer_ai",
            "instance_id": "designer_ai",
            "collection_id": "main_ai_ensemble",
            "ai_type": "designer",
            "name": "设计师AI",
            "description": "负责项目所有的设计、前端排版和视觉设计工作",
            "functions": str([
                "web_design",
                "ui_ux_design",
                "frontend_layout",
                "color_scheme_design",
                "typography_design",
                "responsive_design",
                "visual_identity_design"
            ]),
            "responsibilities": str([
                "网页设计",
                "用户界面和用户体验设计",
                "前端页面布局",
                "配色方案设计",
                "排版设计",
                "响应式设计",
                "视觉识别系统设计"
            ]),
            "config": str({
                "design_style": "modern_minimalist",
                "color_palette": ["#667eea", "#764ba2", "#3b82f6", "#f093fb"],
                "primary_font": "Segoe UI",
                "secondary_font": "Tahoma",
                "responsive_breakpoints": [768, 1024, 1440]
            }),
            "status": "active",
            "bound_user": "admin"
        }

        sql = """
        INSERT OR REPLACE INTO ai_instances
        (ai_name, instance_id, collection_id, ai_type, name, description,
         functions, responsibilities, status, config, bound_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        params = (
            designer_ai["ai_name"],
            designer_ai["instance_id"],
            designer_ai["collection_id"],
            designer_ai["ai_type"],
            designer_ai["name"],
            designer_ai["description"],
            designer_ai["functions"],
            designer_ai["responsibilities"],
            designer_ai["status"],
            designer_ai["config"],
            designer_ai["bound_user"]
        )

        cursor.execute(sql, params)
        conn.commit()

        print("设计师AI员工创建成功!")
        print(f"AI名称: {designer_ai['name']}")
        print(f"类型: {designer_ai['ai_type']}")
        print(f"状态: {designer_ai['status']}")

        conn.close()
        return True

    except Exception as e:
        print(f"创建设计师AI失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    create_designer_ai()
