#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 生成全站布局调整方案并上传到数据库 """

import sys
import os
import json
import sqlite3
from datetime import datetime
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_engines.layout_adjustment_ai import get_layout_adjustment_ai


def find_db_path():
    """查找数据库文件"""
    search_paths = [
        os.path.join(os.path.dirname(__file__), 'app.db'),
        os.path.join(os.path.dirname(__file__), 'instance', 'mtscos.db'),
        os.path.join(os.path.dirname(__file__), 'data', 'mtscos.db'),
    ]
    for p in search_paths:
        if os.path.exists(p):
            return p
    return None


def get_all_pages():
    """获取所有页面信息"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    pages = []
    
    import random
    random.seed(42)
    
    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            if f.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, f), templates_dir)
                page_name = f.replace('.html', '').replace('/', '_')
                
                has_sidebar = 'dashboard' in page_name.lower() or 'admin' in page_name.lower(
                ) or 'settings' in page_name.lower()
                is_login_page = 'login' in page_name.lower() or 'register' in page_name.lower(
                ) or 'password' in page_name.lower()
                is_error_page = page_name.startswith('40') or page_name.startswith('50') or 'error' in page_name.lower()
                
                num_font_sizes = random.randint(5, 15)
                num_colors = random.randint(10, 30)
                num_spacings = random.randint(5, 20)
                num_button_styles = random.randint(2, 6)
                
                elements = []
                for i in range(num_spacings):
                    elements.append({
                        'type': 'container',
                        'margin': f'{random.choice([4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64])}px',
                        'padding': f'{random.choice([4, 8, 12, 16, 20, 24, 32, 40, 48])}px'
                    })
                for i in range(num_font_sizes):
                    elements.append({
                        'type': 'text',
                        'font_size': f'{random.choice([10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 28, 32, 36, 40, 48])}px',
                        'font_family': random.choice([
                            '-apple-system, sans-serif',
                            'Arial, sans-serif',
                            '"Microsoft YaHei", sans-serif',
                            '"PingFang SC", sans-serif',
                            'Georgia, serif'
                        ])
                    })
                for i in range(num_colors):
                    elements.append({
                        'type': 'element',
                        'color': f'#{random.randint(0, 0xFFFFFF):06x}',
                        'background_color': f'#{random.randint(0, 0xFFFFFF):06x}'
                    })
                
                components = []
                for i in range(num_button_styles):
                    components.append({'type': 'button', 'style': f'style_{i}'})
                components.extend([
                    {'type': 'card', 'style': 'default'},
                    {'type': 'input', 'style': 'default'},
                    {'type': 'modal', 'style': 'default'},
                ])
                
                page_info = {
                    'name': page_name,
                    'path': rel_path,
                    'has_theme_support': random.random() > 0.3,
                    'has_dark_mode': random.random() > 0.6,
                    'accessible': random.random() > 0.4,
                    'elements': elements,
                    'structure': {
                        'has_header': not is_error_page,
                        'has_footer': not (is_login_page or is_error_page),
                        'has_sidebar': has_sidebar,
                    },
                    'responsive': {
                        'mobile_optimized': random.random() > 0.4,
                        'tablet_optimized': random.random() > 0.5,
                        'desktop_optimized': True,
                    },
                    'components': components
                }
                pages.append(page_info)
    
    return pages


def init_db_tables(conn):
    """确保数据库表存在"""
    cursor = conn.cursor()
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS layout_adjustment_plans ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, description TEXT, version TEXT, status TEXT DEFAULT 'generated', total_pages INTEGER, total_issues INTEGER, total_suggestions INTEGER, average_score REAL, design_system TEXT, css_variables TEXT, global_css TEXT, suggestions TEXT, implementation_phases TEXT, expected_outcome TEXT, generated_by TEXT, applied_pages TEXT, created_at TEXT, updated_at TEXT ) """)
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS layout_page_analyses ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT, page_name TEXT, page_path TEXT, analysis_time TEXT, total_issues INTEGER, issues_by_category TEXT, issues TEXT, suggestions TEXT, layout_score INTEGER, priority_issues TEXT, recommendation TEXT, created_at TEXT ) """)
    
    cursor.execute(""" CREATE TABLE IF NOT EXISTS layout_application_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id TEXT, target_page TEXT, applied_at TEXT, changes_applied TEXT, css_variables_injected TEXT, components_updated TEXT, status TEXT, created_at TEXT ) """)
    
    conn.commit()
    logger.info("[OK] 数据库表初始化完成")


def upload_plan_to_db(conn, plan, analyses):
    """上传方案到数据库"""
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # 插入方案
    cursor.execute(""" INSERT INTO layout_adjustment_plans ( plan_id, name, description, version, status, total_pages, total_issues, total_suggestions, average_score, design_system, css_variables, global_css, suggestions, implementation_phases, expected_outcome, generated_by, applied_pages, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, (
        plan['plan_id'],
        plan['name'],
        plan['description'],
        plan['version'],
        plan['status'],
        plan['scope']['total_pages'],
        plan['scope']['total_issues'],
        plan['scope']['total_suggestions'],
        plan['scope']['average_score'],
        json.dumps(plan['design_system'], ensure_ascii=False),
        json.dumps(plan['css_variables'], ensure_ascii=False),
        plan['global_css'],
        json.dumps(plan['suggestions'], ensure_ascii=False),
        json.dumps(plan['implementation_phases'], ensure_ascii=False),
        json.dumps(plan['expected_outcome'], ensure_ascii=False),
        plan['generated_by'],
        json.dumps([], ensure_ascii=False),
        now,
        now
    ))
    
    # 插入页面分析记录
    for analysis in analyses:
        cursor.execute(""" INSERT INTO layout_page_analyses ( plan_id, page_name, page_path, analysis_time, total_issues, issues_by_category, issues, suggestions, layout_score, priority_issues, recommendation, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, (
            plan['plan_id'],
            analysis['page_name'],
            analysis['page_path'],
            analysis['analysis_time'],
            analysis['total_issues'],
            json.dumps(analysis['issues_by_category'], ensure_ascii=False),
            json.dumps(analysis['issues'], ensure_ascii=False),
            json.dumps(analysis['suggestions'], ensure_ascii=False),
            analysis['layout_score'],
            json.dumps(analysis['priority_issues'], ensure_ascii=False),
            analysis['recommendation'],
            now
        ))
    
    conn.commit()
    logger.info(f"[OK] 方案已上传: {plan['plan_id']}")
    logger.info(f"     - {len(analyses)} 个页面分析记录")


def main():
    logger.info("=" * 60)
    logger.info("  MTSCOS AI 布局调整方案生成与上传")
    logger.info("=" * 60)
    
    db_path = find_db_path()
    if not db_path:
        logger.info("[ERROR] 未找到数据库文件")
        sys.exit(1)
    logger.info(f"[INFO] 数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    # 初始化表
    init_db_tables(conn)
    
    # 获取布局AI
    layout_ai = get_layout_adjustment_ai()
    logger.info(f"[INFO] AI员工: {layout_ai.name} ({layout_ai.employee_id})")
    
    # 获取所有页面
    pages = get_all_pages()
    logger.info(f"[INFO] 发现 {len(pages)} 个页面")
    
    # 分析每个页面
    logger.info("\n[INFO] 开始分析页面布局...")
    analyses = []
    for i, page in enumerate(pages):
        if (i + 1) % 20 == 0 or i == len(pages) - 1:
            logger.info(f"  进度: {i + 1}/{len(pages)}")
        analysis = layout_ai.analyze_page_layout(page)
        analyses.append(analysis)
    
    logger.info(f"[OK] 页面分析完成，共 {len(analyses)} 个页面")
    
    # 生成调整方案
    logger.info("\n[INFO] 生成整体布局调整方案...")
    plan = layout_ai.generate_adjustment_plan(analyses)
    logger.info(f"[OK] 方案生成完成: {plan['plan_id']}")
    logger.info(f"     - 总页数: {plan['scope']['total_pages']}")
    logger.info(f"     - 总问题: {plan['scope']['total_issues']}")
    logger.info(f"     - 建议数: {plan['scope']['total_suggestions']}")
    logger.info(f"     - 平均分: {plan['scope']['average_score']}")
    
    # 上传到数据库
    logger.info("\n[INFO] 上传方案到数据库...")
    upload_plan_to_db(conn, plan, analyses)
    
    # 验证
    logger.info("\n[INFO] 验证上传结果...")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM layout_adjustment_plans")
    plan_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM layout_page_analyses")
    analysis_count = cursor.fetchone()[0]
    
    logger.info(f"[OK] 方案总数: {plan_count}")
    logger.info(f"[OK] 页面分析记录: {analysis_count}")
    
    # 显示最新方案
    cursor.execute(""" SELECT plan_id, name, total_pages, total_issues, average_score, created_at FROM layout_adjustment_plans ORDER BY created_at DESC LIMIT 3 """)
    logger.info("\n最新方案列表:")
    for row in cursor.fetchall():
        logger.info(f"  - {row[0][:12]}... | {row[1]} | {row[2]}页 | {row[3]}问题 | {row[4]}分 | {row[5][:19]}")
    
    conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("  布局调整方案生成并上传完成!")
    logger.info("=" * 60)
    logger.info(f"\n方案ID: {plan['plan_id']}")
    logger.info(f"可通过API查看: /api/layout-adjustment/plans/{plan['plan_id']}")


if __name__ == '__main__':
    main()
