# -*- coding: utf-8 -*-
""" 第8轮功能验证脚本 验证：智能学习诊断引擎、智能知识库引擎、AI课堂互动引擎 """
import os
import sys
import json
import requests

BASE_URL = "http://127.0.0.1:8888"

# 登录获取session
def login():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': f'{BASE_URL}/login',
        'X-Requested-With': 'XMLHttpRequest'
    })
    # 先访问登录页获取cookie
    session.get(f"{BASE_URL}/login")
    # 登录
    resp = session.post(f"{BASE_URL}/auth/login",
                       json={'username': 'admin', 'password': 'admin123'},
                       allow_redirects=False)
    logger.info(f"登录状态: {resp.status_code}, {resp.json() if resp.headers.get('content-type', '').startswith('application/json') else resp.text[:100]}")
    return session

# 智能学习诊断引擎测试
def test_diagnosis_engine(session):
    logger.info("\n" + "=" * 60)
    logger.info("🔍 智能学习诊断引擎测试")
    logger.info("=" * 60)
    results = []

    # 1. 更新掌握度
    logger.info("\n1. 更新知识点掌握度...")
    try:
        resp = session.post(f"{BASE_URL}/api/diagnosis/update_mastery",
                          json={'student_id': 's001', 'subject': '数学',
                                'knowledge_point': '一元一次方程', 'correct': True,
                                'time_spent': 120, 'chapter': '第三章'})
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 更新成功: {data.get('new_score', 0):.1f}分, {data.get('level', '')}")
        results.append(('diagnosis/update_mastery', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/update_mastery', False))

    # 2. 获取掌握度
    logger.info("\n2. 获取学生掌握度...")
    try:
        resp = session.get(f"{BASE_URL}/api/diagnosis/mastery/s001?subject=数学")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('subject_count', 0)}个学科, {data.get('total_points', 0)}个知识点")
        results.append(('diagnosis/mastery', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/mastery', False))

    # 3. 创建诊断测试
    logger.info("\n3. 创建诊断测试...")
    try:
        resp = session.post(f"{BASE_URL}/api/diagnosis/create_test",
                          json={'student_id': 's001', 'subject': '数学',
                                'test_type': 'adaptive', 'num_questions': 5})
        data = resp.json()
        ok = data.get('success', False)
        test_id = data.get('test_id', '')
        logger.info(f"   ✅ 成功: test_id={test_id}, {data.get('num_questions', 0)}题")
        results.append(('diagnosis/create_test', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/create_test', False))
        test_id = None

    # 4. 提交测试
    logger.info("\n4. 提交诊断测试...")
    if test_id:
        try:
            resp = session.post(f"{BASE_URL}/api/diagnosis/submit_test",
                              json={'test_id': test_id,
                                    'answers': [{'question_id': 'q1', 'answer': 'A', 'correct': True,
                                    'time_spent': 30}],
                                    'duration': 180})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: 得分={data.get('score', 0)}")
            results.append(('diagnosis/submit_test', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('diagnosis/submit_test', False))
    else:
        logger.info("   ⏭️  跳过（无test_id）")
        results.append(('diagnosis/submit_test', False))

    # 5. 生成诊断报告
    logger.info("\n5. 生成学生诊断报告...")
    try:
        resp = session.post(f"{BASE_URL}/api/diagnosis/generate_report",
                          json={'student_id': 's001', 'subject': '数学', 'report_type': 'full'})
        data = resp.json()
        ok = data.get('success', False)
        report_id = data.get('report_id', '')
        logger.info(f"   ✅ 成功: report_id={report_id}")
        results.append(('diagnosis/generate_report', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/generate_report', False))

    # 6. 列出报告
    logger.info("\n6. 列出诊断报告...")
    try:
        resp = session.get(f"{BASE_URL}/api/diagnosis/reports/s001?limit=5")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('count', 0)}份报告")
        results.append(('diagnosis/reports', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/reports', False))

    # 7. 班级诊断报告
    logger.info("\n7. 生成班级诊断报告...")
    try:
        resp = session.post(f"{BASE_URL}/api/diagnosis/class_report",
                          json={'class_id': 'class1', 'subject': '数学', 'period': 'month'})
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: class_avg={data.get('class_avg_score', 0):.1f}")
        results.append(('diagnosis/class_report', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/class_report', False))

    # 8. 统计信息
    logger.info("\n8. 诊断引擎统计...")
    try:
        resp = session.get(f"{BASE_URL}/api/diagnosis/statistics")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total_mastery_records', 0)}条掌握记录, "
              f"{data.get('total_tests', 0)}次测试, {data.get('total_reports', 0)}份报告")
        results.append(('diagnosis/statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('diagnosis/statistics', False))

    return results


# 智能知识库引擎测试
def test_knowledge_engine(session):
    logger.info("\n" + "=" * 60)
    logger.info("📚 智能知识库引擎测试")
    logger.info("=" * 60)
    results = []

    # 1. 添加知识条目
    logger.info("\n1. 添加知识条目...")
    try:
        resp = session.post(f"{BASE_URL}/api/knowledge/entry",
                          json={'title': '一元一次方程', 'content': '一元一次方程指只含有一个未知数、未知数的最高次数为1且两边都为整式的等式。',
                                'knowledge_type': 'concept', 'subject': '数学',
                                'summary': '一元一次方程的基本概念', 'grade': '初一',
                                'chapter': '第三章', 'section': '第一节',
                                'importance': 'core', 'difficulty': 'easy',
                                'tags': ['方程', '代数', '一元一次']})
        data = resp.json()
        ok = data.get('success', False)
        entry_id = data.get('entry_id', '')
        logger.info(f"   ✅ 成功: entry_id={entry_id}")
        results.append(('knowledge/add_entry', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/add_entry', False))
        entry_id = None

    # 2. 获取知识条目
    logger.info("\n2. 获取知识条目...")
    if entry_id:
        try:
            resp = session.get(f"{BASE_URL}/api/knowledge/entry/{entry_id}")
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: {data.get('entry', {}).get('title', '')}")
            results.append(('knowledge/get_entry', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('knowledge/get_entry', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('knowledge/get_entry', False))

    # 3. 列出知识条目
    logger.info("\n3. 列出知识条目...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/list?subject=数学&limit=10")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total', 0)}条")
        results.append(('knowledge/list', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/list', False))

    # 4. 搜索知识库
    logger.info("\n4. 搜索知识库...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/search?q=方程&subject=数学")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total', 0)}条结果")
        results.append(('knowledge/search', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/search', False))

    # 5. 添加分类
    logger.info("\n5. 添加知识分类...")
    try:
        resp = session.post(f"{BASE_URL}/api/knowledge/category",
                          json={'name': '代数基础', 'subject': '数学',
                                'description': '代数学科基础知识点分类'})
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: category_id={data.get('category_id', '')}")
        results.append(('knowledge/add_category', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/add_category', False))

    # 6. 列出分类
    logger.info("\n6. 列出知识分类...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/categories?subject=数学")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('count', 0)}个分类")
        results.append(('knowledge/categories', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/categories', False))

    # 7. 记录学习
    logger.info("\n7. 记录学习行为...")
    if entry_id:
        try:
            resp = session.post(f"{BASE_URL}/api/knowledge/learn",
                              json={'entry_id': entry_id, 'action': 'learn',
                                    'duration': 180, 'understanding_score': 85,
                                    'note': '理解了基本概念'})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: log_id={data.get('log_id', '')}")
            results.append(('knowledge/learn', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('knowledge/learn', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('knowledge/learn', False))

    # 8. 学习进度
    logger.info("\n8. 获取学习进度...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/progress/test_user?subject=数学")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total_entries', 0)}条, 已学{data.get('learned_count', 0)}条")
        results.append(('knowledge/progress', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/progress', False))

    # 9. 知识图谱
    logger.info("\n9. 获取知识图谱...")
    if entry_id:
        try:
            resp = session.get(f"{BASE_URL}/api/knowledge/graph/{entry_id}?depth=2")
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: {len(data.get('nodes', []))}个节点, {len(data.get('edges', []))}条边")
            results.append(('knowledge/graph', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('knowledge/graph', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('knowledge/graph', False))

    # 10. 知识类型
    logger.info("\n10. 获取知识类型...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/types")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {len(data.get('types', {}))}种类型")
        results.append(('knowledge/types', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/types', False))

    # 11. 统计信息
    logger.info("\n11. 知识库统计...")
    try:
        resp = session.get(f"{BASE_URL}/api/knowledge/statistics")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total_entries', 0)}条知识, "
              f"{data.get('total_categories', 0)}个分类, {data.get('total_learn_logs', 0)}条学习记录")
        results.append(('knowledge/statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('knowledge/statistics', False))

    return results


# AI课堂互动引擎测试
def test_classroom_engine(session):
    logger.info("\n" + "=" * 60)
    logger.info("🎓 AI课堂互动引擎测试")
    logger.info("=" * 60)
    results = []

    # 1. 创建活动
    logger.info("\n1. 创建课堂活动...")
    try:
        resp = session.post(f"{BASE_URL}/api/classroom/create",
                          json={'activity_type': 'quiz', 'title': '数学随堂测验',
                                'class_id': 'class1', 'subject': '数学',
                                'description': '第三章一元一次方程小测'})
        data = resp.json()
        ok = data.get('success', False)
        activity_id = data.get('activity_id', '')
        logger.info(f"   ✅ 成功: activity_id={activity_id}")
        results.append(('classroom/create', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/create', False))
        activity_id = None

    # 2. 添加题目
    logger.info("\n2. 添加题目...")
    if activity_id:
        try:
            resp = session.post(f"{BASE_URL}/api/classroom/question",
                              json={'activity_id': activity_id,
                                    'question_type': 'single_choice',
                                    'content': '一元一次方程 2x+3=7 的解是？',
                                    'options': ['x=1', 'x=2', 'x=3', 'x=4'],
                                    'correct_answer': 'x=2',
                                    'points': 10, 'time_limit': 30, 'sort_order': 1})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: question_id={data.get('question_id', '')}")
            results.append(('classroom/add_question', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/add_question', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/add_question', False))

    # 3. 开始活动
    logger.info("\n3. 开始活动...")
    if activity_id:
        try:
            resp = session.post(f"{BASE_URL}/api/classroom/start",
                              json={'activity_id': activity_id})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: status={data.get('status', '')}")
            results.append(('classroom/start', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/start', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/start', False))

    # 4. 获取活动详情
    logger.info("\n4. 获取活动详情...")
    if activity_id:
        try:
            resp = session.get(f"{BASE_URL}/api/classroom/{activity_id}")
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: {data.get('activity', {}).get('title', '')}")
            results.append(('classroom/get_activity', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/get_activity', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/get_activity', False))

    # 5. 列出活动
    logger.info("\n5. 列出活动...")
    try:
        resp = session.get(f"{BASE_URL}/api/classroom/list?status=active")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('count', 0)}个活动")
        results.append(('classroom/list', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/list', False))

    # 6. 随机点名
    logger.info("\n6. 随机点名...")
    if activity_id:
        try:
            students = [f"s{i:03d}" for i in range(1, 31)]
            resp = session.post(f"{BASE_URL}/api/classroom/random_pick",
                              json={'activity_id': activity_id,
                                    'student_ids': students, 'count': 3})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: 选中{len(data.get('selected', []))}人")
            results.append(('classroom/random_pick', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/random_pick', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/random_pick', False))

    # 7. 创建分组
    logger.info("\n7. 创建分组...")
    if activity_id:
        try:
            students = [f"s{i:03d}" for i in range(1, 25)]
            resp = session.post(f"{BASE_URL}/api/classroom/groups",
                              json={'activity_id': activity_id,
                                    'student_ids': students,
                                    'group_count': 4, 'strategy': 'random'})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: {len(data.get('groups', []))}个小组")
            results.append(('classroom/groups', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/groups', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/groups', False))

    # 8. 奖励积分
    logger.info("\n8. 奖励积分...")
    try:
        resp = session.post(f"{BASE_URL}/api/classroom/award_points",
                          json={'student_id': 's001', 'points': 10,
                                'reason': '课堂表现积极', 'activity_id': activity_id,
                                'class_id': 'class1'})
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: point_id={data.get('point_id', '')}")
        results.append(('classroom/award_points', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/award_points', False))

    # 9. 学生积分
    logger.info("\n9. 学生积分查询...")
    try:
        resp = session.get(f"{BASE_URL}/api/classroom/points/s001")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: 总积分={data.get('total_points', 0)}")
        results.append(('classroom/points', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/points', False))

    # 10. 结束活动
    logger.info("\n10. 结束活动...")
    if activity_id:
        try:
            resp = session.post(f"{BASE_URL}/api/classroom/end",
                              json={'activity_id': activity_id})
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: 时长={data.get('duration', 0)}秒, 参与{data.get('participants', 0)}人")
            results.append(('classroom/end', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/end', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/end', False))

    # 11. 活动结果
    logger.info("\n11. 活动结果统计...")
    if activity_id:
        try:
            resp = session.get(f"{BASE_URL}/api/classroom/results/{activity_id}")
            data = resp.json()
            ok = data.get('success', False)
            logger.info(f"   ✅ 成功: {data.get('total_participants', 0)}人参与, 平均分={data.get('avg_score', 0):.1f}")
            results.append(('classroom/results', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('classroom/results', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('classroom/results', False))

    # 12. 活动类型
    logger.info("\n12. 活动类型列表...")
    try:
        resp = session.get(f"{BASE_URL}/api/classroom/activity_types")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {len(data.get('types', {}))}种活动类型")
        results.append(('classroom/activity_types', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/activity_types', False))

    # 13. 统计信息
    logger.info("\n13. 课堂互动统计...")
    try:
        resp = session.get(f"{BASE_URL}/api/classroom/statistics")
        data = resp.json()
        ok = data.get('success', False)
        logger.info(f"   ✅ 成功: {data.get('total_activities', 0)}个活动, "
              f"{data.get('total_participations', 0)}次参与, {data.get('total_templates', 0)}个模板")
        results.append(('classroom/statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('classroom/statistics', False))

    return results


def main():
    logger.info("🚀 第8轮功能验证 - 智能学习诊断 / 智能知识库 / AI课堂互动")
    logger.info("=" * 60)

    session = login()

    all_results = []
    all_results += test_diagnosis_engine(session)
    all_results += test_knowledge_engine(session)
    all_results += test_classroom_engine(session)

    # 统计
    passed = sum(1 for _, ok in all_results if ok)
    total = len(all_results)
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 验证结果：{passed}/{total} 通过 ({passed/total*100:.1f}%)")
    logger.info("=" * 60)

    if passed < total:
        logger.info("\n❌ 失败的测试:")
        for name, ok in all_results:
            if not ok:
                logger.info(f"   - {name}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
