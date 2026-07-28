# -*- coding: utf-8 -*-
"""
第8轮功能验证脚本 - 直接调用引擎（不通过HTTP）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_diagnosis_engine():
    logger.info("\n" + "=" * 60)
    logger.info("🔍 智能学习诊断引擎测试")
    logger.info("=" * 60)
    results = []

    from ai_engines.learning_diagnosis_engine import learning_diagnosis_engine

    # 1. 更新掌握度
    logger.info("\n1. 更新知识点掌握度...")
    try:
        r = learning_diagnosis_engine.update_mastery(
            student_id='s001', subject='数学',
            knowledge_point='一元一次方程', correct=True,
            time_spent=120, chapter='第三章')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} 分数: {r.get('new_score', 0):.1f}, 等级: {r.get('level', '')}")
        results.append(('update_mastery', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('update_mastery', False))

    # 多次更新以积累数据
    for i, correct in enumerate([True, True, False, True, True]):
        learning_diagnosis_engine.update_mastery(
            student_id='s001', subject='数学',
            knowledge_point='一元一次方程', correct=correct,
            time_spent=60 + i * 10)

    # 2. 获取掌握度
    logger.info("\n2. 获取学生掌握度...")
    try:
        r = learning_diagnosis_engine.get_student_mastery('s001', '数学')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('subject_count', 0)}个学科, {r.get('total_points', 0)}个知识点")
        results.append(('get_student_mastery', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_student_mastery', False))

    # 3. 创建诊断测试
    logger.info("\n3. 创建诊断测试...")
    try:
        r = learning_diagnosis_engine.create_diagnosis_test(
            student_id='s001', subject='数学',
            test_type='adaptive', num_questions=5)
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} test_id={r.get('test_id', '')}, {r.get('num_questions', 0)}题")
        results.append(('create_diagnosis_test', ok))
        test_id = r.get('test_id', '')
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('create_diagnosis_test', False))
        test_id = ''

    # 4. 提交诊断测试
    logger.info("\n4. 提交诊断测试...")
    if test_id:
        try:
            r = learning_diagnosis_engine.submit_diagnosis_test(
                test_id=test_id,
                answers=[{'question_id': f'q{i}', 'answer': 'A', 'correct': i < 3, 'time_spent': 30} for i in range(5)],
                duration=180)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} 得分={r.get('score', 0)}")
            results.append(('submit_diagnosis_test', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('submit_diagnosis_test', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('submit_diagnosis_test', False))

    # 5. 生成学生诊断报告
    logger.info("\n5. 生成学生诊断报告...")
    try:
        r = learning_diagnosis_engine.generate_student_report(
            student_id='s001', subject='数学', report_type='full')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} report_id={r.get('report_id', '')}")
        results.append(('generate_student_report', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('generate_student_report', False))

    # 6. 列出报告
    logger.info("\n6. 列出诊断报告...")
    try:
        r = learning_diagnosis_engine.list_reports('s001', limit=5)
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('count', 0)}份报告")
        results.append(('list_reports', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('list_reports', False))

    # 7. 班级诊断报告
    logger.info("\n7. 生成班级诊断报告...")
    try:
        r = learning_diagnosis_engine.generate_class_report(
            class_id='class1', subject='数学', period='month')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} 班级均分={r.get('class_avg_score', 0):.1f}")
        results.append(('generate_class_report', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('generate_class_report', False))

    # 8. 统计信息
    logger.info("\n8. 诊断引擎统计...")
    try:
        r = learning_diagnosis_engine.get_statistics()
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total_mastery_records', 0)}条掌握记录, "
              f"{r.get('total_tests', 0)}次测试, {r.get('total_reports', 0)}份报告")
        results.append(('get_statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_statistics', False))

    return results


def test_knowledge_engine():
    logger.info("\n" + "=" * 60)
    logger.info("📚 智能知识库引擎测试")
    logger.info("=" * 60)
    results = []

    from ai_engines.knowledge_base_engine import knowledge_base_engine

    # 1. 添加知识条目
    logger.info("\n1. 添加知识条目...")
    try:
        r = knowledge_base_engine.add_entry(
            title='一元一次方程',
            content='一元一次方程指只含有一个未知数、未知数的最高次数为1且两边都为整式的等式。',
            knowledge_type='concept', subject='数学',
            summary='一元一次方程的基本概念', grade='初一',
            chapter='第三章', section='第一节',
            importance='core', difficulty='easy',
            tags=['方程', '代数', '一元一次'],
            author_id='admin')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} entry_id={r.get('entry_id', '')}")
        results.append(('add_entry', ok))
        entry_id = r.get('entry_id', '')
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('add_entry', False))
        entry_id = ''

    # 2. 获取知识条目
    logger.info("\n2. 获取知识条目...")
    if entry_id:
        try:
            r = knowledge_base_engine.get_entry(entry_id, 'user1')
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} {r.get('entry', {}).get('title', '')}")
            results.append(('get_entry', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('get_entry', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('get_entry', False))

    # 3. 列出知识条目
    logger.info("\n3. 列出知识条目...")
    try:
        r = knowledge_base_engine.list_entries(subject='数学', limit=10)
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total', 0)}条")
        results.append(('list_entries', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('list_entries', False))

    # 4. 搜索知识库
    logger.info("\n4. 搜索知识库...")
    try:
        r = knowledge_base_engine.search('方程', subject='数学')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total', 0)}条结果")
        results.append(('search', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('search', False))

    # 5. 添加分类
    logger.info("\n5. 添加知识分类...")
    try:
        r = knowledge_base_engine.add_category(
            name='代数基础', subject='数学', description='代数学科基础知识点分类')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} category_id={r.get('category_id', '')}")
        results.append(('add_category', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('add_category', False))

    # 6. 列出分类
    logger.info("\n6. 列出知识分类...")
    try:
        r = knowledge_base_engine.list_categories(subject='数学')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('count', 0)}个分类")
        results.append(('list_categories', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('list_categories', False))

    # 7. 记录学习
    logger.info("\n7. 记录学习行为...")
    if entry_id:
        try:
            r = knowledge_base_engine.record_learning(
                user_id='user1', entry_id=entry_id,
                action='learn', duration=180,
                understanding_score=85, note='理解了基本概念')
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} log_id={r.get('log_id', '')}")
            results.append(('record_learning', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('record_learning', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('record_learning', False))

    # 8. 学习进度
    logger.info("\n8. 获取学习进度...")
    try:
        r = knowledge_base_engine.get_user_learning_progress('user1', subject='数学')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total_entries', 0)}条, 已学{r.get('learned_count', 0)}条")
        results.append(('get_user_learning_progress', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_user_learning_progress', False))

    # 9. 知识图谱
    logger.info("\n9. 获取知识图谱...")
    if entry_id:
        try:
            r = knowledge_base_engine.get_knowledge_graph(entry_id, depth=2)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} {len(r.get('nodes', []))}个节点, {len(r.get('edges', []))}条边")
            results.append(('get_knowledge_graph', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('get_knowledge_graph', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('get_knowledge_graph', False))

    # 10. 知识类型
    logger.info("\n10. 获取知识类型...")
    try:
        r = knowledge_base_engine.get_knowledge_types()
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {len(r.get('types', {}))}种类型")
        results.append(('get_knowledge_types', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_knowledge_types', False))

    # 11. 统计信息
    logger.info("\n11. 知识库统计...")
    try:
        r = knowledge_base_engine.get_statistics()
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total_entries', 0)}条知识, "
              f"{r.get('total_categories', 0)}个分类, {r.get('total_learn_logs', 0)}条学习记录")
        results.append(('get_statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_statistics', False))

    return results


def test_classroom_engine():
    logger.info("\n" + "=" * 60)
    logger.info("🎓 AI课堂互动引擎测试")
    logger.info("=" * 60)
    results = []

    from ai_engines.classroom_interaction_engine import classroom_interaction_engine

    # 1. 创建活动
    logger.info("\n1. 创建课堂活动...")
    try:
        r = classroom_interaction_engine.create_activity(
            teacher_id='teacher1', activity_type='quiz',
            title='数学随堂测验', class_id='class1', subject='数学',
            description='第三章一元一次方程小测')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} activity_id={r.get('activity_id', '')}")
        results.append(('create_activity', ok))
        activity_id = r.get('activity_id', '')
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('create_activity', False))
        activity_id = ''

    # 2. 添加题目
    logger.info("\n2. 添加题目...")
    if activity_id:
        try:
            r = classroom_interaction_engine.add_question(
                activity_id=activity_id,
                question_type='single_choice',
                content='一元一次方程 2x+3=7 的解是？',
                options=['x=1', 'x=2', 'x=3', 'x=4'],
                correct_answer='x=2',
                points=10, time_limit=30, sort_order=1)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} question_id={r.get('question_id', '')}")
            results.append(('add_question', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('add_question', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('add_question', False))

    # 3. 开始活动
    logger.info("\n3. 开始活动...")
    if activity_id:
        try:
            r = classroom_interaction_engine.start_activity(activity_id)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} status={r.get('status', '')}")
            results.append(('start_activity', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('start_activity', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('start_activity', False))

    # 4. 获取活动详情
    logger.info("\n4. 获取活动详情...")
    if activity_id:
        try:
            r = classroom_interaction_engine.get_activity(activity_id)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} {r.get('activity', {}).get('title', '')}")
            results.append(('get_activity', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('get_activity', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('get_activity', False))

    # 5. 列出活动
    logger.info("\n5. 列出活动...")
    try:
        r = classroom_interaction_engine.list_activities(status='active')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('count', 0)}个活动")
        results.append(('list_activities', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('list_activities', False))

    # 6. 随机点名
    logger.info("\n6. 随机点名...")
    if activity_id:
        try:
            students = [f"s{i:03d}" for i in range(1, 31)]
            r = classroom_interaction_engine.random_pick(
                activity_id=activity_id, student_ids=students, count=3)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} 选中{len(r.get('selected', []))}人")
            results.append(('random_pick', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('random_pick', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('random_pick', False))

    # 7. 创建分组
    logger.info("\n7. 创建分组...")
    if activity_id:
        try:
            students = [f"s{i:03d}" for i in range(1, 25)]
            r = classroom_interaction_engine.create_groups(
                activity_id=activity_id, student_ids=students,
                group_count=4, strategy='random')
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} {len(r.get('groups', []))}个小组")
            results.append(('create_groups', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('create_groups', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('create_groups', False))

    # 8. 奖励积分
    logger.info("\n8. 奖励积分...")
    try:
        r = classroom_interaction_engine.award_points(
            student_id='s001', points=10,
            reason='课堂表现积极', activity_id=activity_id,
            class_id='class1', awarded_by='teacher1')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} point_id={r.get('point_id', '')}")
        results.append(('award_points', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('award_points', False))

    # 9. 学生积分
    logger.info("\n9. 学生积分查询...")
    try:
        r = classroom_interaction_engine.get_student_points('s001')
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} 总积分={r.get('total_points', 0)}")
        results.append(('get_student_points', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_student_points', False))

    # 10. 结束活动
    logger.info("\n10. 结束活动...")
    if activity_id:
        try:
            r = classroom_interaction_engine.end_activity(activity_id)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} 时长={r.get('duration', 0)}秒, 参与{r.get('participants', 0)}人")
            results.append(('end_activity', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('end_activity', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('end_activity', False))

    # 11. 活动结果
    logger.info("\n11. 活动结果统计...")
    if activity_id:
        try:
            r = classroom_interaction_engine.get_activity_results(activity_id)
            ok = r.get('success', False)
            logger.info(f"   {'✅' if ok else '❌'} {r.get('total_participants', 0)}人参与, 平均分={r.get('avg_score', 0):.1f}")
            results.append(('get_activity_results', ok))
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            results.append(('get_activity_results', False))
    else:
        logger.info("   ⏭️  跳过")
        results.append(('get_activity_results', False))

    # 12. 活动类型
    logger.info("\n12. 活动类型列表...")
    try:
        r = classroom_interaction_engine.get_activity_types()
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {len(r.get('types', {}))}种活动类型")
        results.append(('get_activity_types', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_activity_types', False))

    # 13. 统计信息
    logger.info("\n13. 课堂互动统计...")
    try:
        r = classroom_interaction_engine.get_statistics()
        ok = r.get('success', False)
        logger.info(f"   {'✅' if ok else '❌'} {r.get('total_activities', 0)}个活动, "
              f"{r.get('total_participations', 0)}次参与, {r.get('total_templates', 0)}个模板")
        results.append(('get_statistics', ok))
    except Exception as e:
        logger.info(f"   ❌ 失败: {e}")
        results.append(('get_statistics', False))

    return results


def main():
    logger.info("🚀 第8轮功能验证 - 智能学习诊断 / 智能知识库 / AI课堂互动")
    logger.info("=" * 60)

    all_results = []
    all_results += [('diagnosis/' + n, ok) for n, ok in test_diagnosis_engine()]
    all_results += [('knowledge/' + n, ok) for n, ok in test_knowledge_engine()]
    all_results += [('classroom/' + n, ok) for n, ok in test_classroom_engine()]

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
