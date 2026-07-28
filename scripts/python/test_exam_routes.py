#!/usr/bin/env python3
"""
考试系统路由验证脚本
验证所有考试相关路由是否正确注册
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_exam_routes():
    """测试考试系统路由"""
    logger.info("=" * 80)
    logger.info("考试系统路由验证")
    logger.info("=" * 80)
    
    exam_routes = []
    for rule in app.url_map.iter_rules():
        if 'exam' in str(rule).lower():
            exam_routes.append({
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']])
            })
    
    logger.info(f"\n发现 {len(exam_routes)} 个考试相关路由:\n")
    
    for route in sorted(exam_routes, key=lambda x: x['rule']):
        logger.info(f"  {route['rule']}")
        logger.info(f"    -> endpoint: {route['endpoint']}")
        logger.info(f"    -> methods: {', '.join(route['methods'])}")
        logger.info()
    
    # 验证关键路由
    required_routes = [
        '/api/exam/exams',
        '/api/exam/exams/<exam_id>',
        '/api/exam/exams/<exam_id>/questions',
        '/api/exam/questions/<question_id>',
        '/api/exam/papers/<paper_id>',
        '/api/exam/papers/<paper_id>/start',
        '/api/exam/papers/<paper_id>/answer',
        '/api/exam/papers/<paper_id>/submit',
        '/api/exam/results/<paper_id>',
        '/api/exam/results/user/<user_id>',
        '/api/exam/audio/generate',
        '/api/exam/stats/exam/system',
        '/api/exam/stats/exam/activity',
        '/exam_system',
        '/exam_center',
        '/exam_page/<exam_id>',
        '/exam_results',
        '/exam_history'
    ]
    
    logger.info("=" * 80)
    logger.info("关键路由验证")
    logger.info("=" * 80)
    
    all_rules = [str(rule) for rule in app.url_map.iter_rules()]
    missing_routes = []
    
    for req_route in required_routes:
        if req_route in all_rules:
            logger.info(f"✓ {req_route}")
        else:
            logger.info(f"✗ {req_route} - 缺失")
            missing_routes.append(req_route)
    
    if missing_routes:
        logger.info(f"\n⚠️  发现 {len(missing_routes)} 个缺失路由")
    else:
        logger.info("\n✓ 所有关键路由已注册")
    
    return len(missing_routes) == 0

if __name__ == '__main__':
    success = test_exam_routes()
    sys.exit(0 if success else 1)
