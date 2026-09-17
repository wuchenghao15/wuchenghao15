"""
综合测试：新解决方案的入库质量、合并/新建、并发性能、检索精度
"""

import asyncio
import os
import time
from typing import List, Dict

# 环境配置
os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
os.environ["MFLOW_EPISODIC_ENABLED"] = "true"
os.environ["MFLOW_EPISODIC_ENABLE_FACET_POINTS"] = "true"
os.environ["MFLOW_EPISODIC_POINT_REFINER"] = "true"
os.environ["MFLOW_EPISODIC_RETRIEVER_MODE"] = "bundle"  # 使用新的 bundle 模式


# 20条测试事件（设计为有合并场景）
TEST_EVENTS = [
    # ========== 智能客服项目（多批次合并测试）==========
    {
        "id": "智能客服项目",
        "batch": 1,
        "content": """【智能客服系统立项会议纪要】
日期：2025年10月15日
参会人员：张三（产品经理）、李四（技术负责人）、王五（运营总监）

会议决议：
1. 项目背景：当前人工客服成本每月约50万元，响应时间平均8分钟
2. 项目目标：部署智能客服系统，预计降低成本60%，响应时间降至30秒内
3. 技术方案：采用GPT-4o-mini作为对话引擎，Kuzu作为知识图谱存储
4. 预算批准：总投资40万元，包含软件授权、开发、部署、培训
5. 时间节点：11月底完成开发，12月上线试运行""",
    },
    {
        "id": "智能客服项目",
        "batch": 2,
        "content": """【智能客服系统开发进展周报】
日期：2025年11月20日
报告人：李四

本周进展：
1. 对话引擎集成完成，GPT-4o-mini API对接成功
2. 知识库导入：已导入产品FAQ共1500条，常见问题200个
3. 意图识别准确率达到92%，情感分析功能上线
4. 存在问题：复杂多轮对话场景准确率仅75%，需优化
5. 下周计划：优化上下文管理，引入RAG检索增强""",
    },
    {
        "id": "智能客服项目",
        "batch": 3,
        "content": """【智能客服系统上线总结报告】
日期：2025年12月25日

上线成果：
1. 12月10日正式上线，运行稳定
2. 日均处理咨询量3000+，峰值5000+
3. 响应时间：平均1.2秒，99%请求在3秒内完成
4. 客户满意度：从原来的78%提升至91%
5. 成本节省：人工客服减少5人，月节省约30万元

技术指标：
- 意图识别准确率：96%
- 问题解决率：85%
- 转人工率：15%""",
    },
    # ========== 数据中台项目 ==========
    {
        "id": "数据中台项目",
        "batch": 1,
        "content": """【数据中台建设方案评审会】
日期：2025年9月5日

项目概述：
1. 目标：构建企业级数据中台，统一数据资产管理
2. 现状：各业务系统数据孤岛，重复建设严重
3. 架构：采用湖仓一体架构，Databricks + Delta Lake
4. 预算：总投资180万元，分两期实施
5. 收益预期：数据复用率提升200%，报表产出效率提升5倍""",
    },
    {
        "id": "数据中台项目",
        "batch": 2,
        "content": """【数据中台一期验收报告】
日期：2025年12月20日

验收结论：一期建设目标达成，验收通过

完成内容：
1. 数据湖存储：已接入12个业务系统，数据量达50TB
2. 数据治理：建立元数据管理、数据质量规则2000+条
3. 自助分析：上线数据集市，支持SQL和拖拽式分析
4. 数据服务：API网关日调用量达100万次

遗留问题：实时数据同步延迟约5分钟，二期需优化""",
    },
    # ========== 员工培训计划 ==========
    {
        "id": "员工培训计划",
        "batch": 1,
        "content": """【2026年度员工培训计划】

培训目标：
1. 全员覆盖率达到100%，人均培训时长不低于40小时
2. 重点技能：AI应用、数据分析、项目管理

培训安排：
- Q1：AI基础与应用培训，覆盖全员（线上课程+实操）
- Q2：数据分析能力提升，针对产品、运营岗位
- Q3：项目管理认证培训，针对PM和技术骨干
- Q4：领导力发展计划，针对管理层

预算：培训经费50万元，外部讲师费用20万元""",
    },
    # ========== 办公自动化升级 ==========
    {
        "id": "办公自动化项目",
        "batch": 1,
        "content": """【办公自动化系统升级方案】

升级背景：
- 现有OA系统使用8年，界面老旧，移动端体验差
- 流程审批效率低，平均审批周期3天

升级方案：
1. 采用飞书/钉钉集成方案
2. 迁移现有流程200+个
3. 新增AI智能审批功能
4. 统一消息通知平台

时间计划：
- 2026年1月：需求调研和方案设计
- 2026年2-3月：系统开发和数据迁移
- 2026年4月：试运行和全员培训

预算：软件订阅费30万/年，实施费用15万""",
    },
    # ========== 安全合规项目 ==========
    {
        "id": "安全合规项目",
        "batch": 1,
        "content": """【信息安全等保测评会议】
日期：2025年11月10日

测评结果：
1. 本次测评等级：等保二级
2. 总体得分：82分（达标线70分）
3. 发现问题：
   - 高危漏洞3个：SQL注入、XSS跨站、未授权访问
   - 中危漏洞12个：弱密码策略、日志不完整等
   
整改要求：
- 高危问题须在30天内完成整改
- 中危问题须在60天内完成整改
- 整改完成后提交复测申请""",
    },
    {
        "id": "安全合规项目",
        "batch": 2,
        "content": """【安全整改完成报告】
日期：2025年12月15日

整改情况：
1. 高危漏洞：3个全部修复完成
   - SQL注入：参数化查询改造
   - XSS跨站：输入输出过滤
   - 未授权访问：权限校验加固
   
2. 中危漏洞：12个修复完成11个
   - 密码策略加强（8位以上，含特殊字符）
   - 日志系统升级（全量审计日志）
   - 遗留1个需等待系统升级窗口

复测申请已提交，预计1月中旬完成复测""",
    },
    # ========== 新产品发布 ==========
    {
        "id": "新产品发布",
        "batch": 1,
        "content": """【智能助手APP发布会总结】
日期：2025年12月1日
地点：公司总部发布厅

发布内容：
1. 产品名称：小智AI助手
2. 核心功能：
   - 智能问答：支持多领域知识问答
   - 语音交互：支持语音输入和播报
   - 个性化推荐：基于用户习惯的内容推荐
   
市场目标：
- 首月下载量目标：100万次
- 日活用户目标：30万
- 用户留存率目标：40%（7日留存）

发布会现场：媒体到场50+家，直播观看量20万""",
    },
    # ========== 供应链优化 ==========
    {
        "id": "供应链优化",
        "batch": 1,
        "content": """【供应链数字化转型项目启动会】
日期：2025年10月1日

项目目标：
1. 库存周转率提升30%
2. 采购成本降低15%
3. 交付准时率达到98%

技术方案：
- 部署智能预测系统，使用时序模型预测需求
- 上线供应商协同平台，实现信息实时共享
- 建设智能仓储系统，AGV机器人自动拣货

投资预算：总投资300万元，预计18个月回本""",
    },
    # ========== 客户成功案例 ==========
    {
        "id": "客户成功案例",
        "batch": 1,
        "content": """【标杆客户案例：某银行智能风控项目】

客户背景：某城市商业银行，资产规模2000亿

项目内容：
1. 部署智能风控系统，实时评估贷款风险
2. 采用机器学习模型，特征维度3000+
3. 对接央行征信、工商数据、司法数据

项目成果：
- 审批效率：从3天缩短至2小时
- 坏账率：从1.8%降至0.9%
- 业务量：月放款量增长50%

客户评价："系统上线后，我们的零售贷款业务实现了质的飞跃。"
——银行零售业务总监 陈总""",
    },
    # ========== 研发效能提升 ==========
    {
        "id": "研发效能提升",
        "batch": 1,
        "content": """【DevOps平台建设项目总结】
日期：2025年11月30日

建设成果：
1. CI/CD流水线：支持一键部署，日均构建1000+次
2. 自动化测试：单元测试覆盖率从30%提升至80%
3. 容器化改造：95%应用完成容器化
4. 监控告警：全链路追踪，MTTR从4小时降至30分钟

效能指标：
- 发布频率：从每月1次提升至每周3次
- 变更失败率：从15%降至3%
- 开发满意度：从65分提升至88分""",
    },
    # ========== 市场营销活动 ==========
    {
        "id": "双十一营销活动",
        "batch": 1,
        "content": """【2025双十一营销活动复盘】

活动数据：
1. GMV：1.2亿元，同比增长35%
2. 订单量：50万单，客单价240元
3. 新客占比：28%，新客成本降低20%

营销策略：
- 预售期：会员专属折扣，锁定老客
- 爆发期：限时秒杀+满减券
- 返场期：清仓促销+赠品

渠道分析：
- 直播带货：贡献30% GMV
- 私域社群：贡献25% GMV
- 公域投放：ROI达到1:5""",
    },
    # ========== 技术架构升级 ==========
    {
        "id": "微服务架构升级",
        "batch": 1,
        "content": """【核心系统微服务化改造项目】

改造背景：
- 原单体应用代码量100万行，维护困难
- 发布风险高，需要全量回归测试
- 扩展性差，高峰期频繁宕机

改造方案：
1. 拆分为30+微服务，按业务域划分
2. 引入服务网格Istio，实现流量治理
3. 数据库分库分表，支持水平扩展

改造成果：
- 系统可用性：从99.5%提升至99.99%
- 发布效率：单个服务可独立发布
- 扩容速度：从2小时缩短至5分钟""",
    },
    # ========== 人才招聘 ==========
    {
        "id": "人才招聘计划",
        "batch": 1,
        "content": """【2026年人才招聘计划】

招聘需求：
1. 技术研发：50人
   - 高级开发工程师：20人
   - AI算法工程师：15人
   - 测试工程师：15人
   
2. 产品运营：20人
   - 产品经理：10人
   - 运营专员：10人

3. 职能支持：10人

招聘渠道：
- 校园招聘：40%（985/211为主）
- 社会招聘：50%（猎头+招聘网站）
- 内推：10%（内推奖金5000元）

预算：招聘费用200万元，平均获取成本2.5万/人""",
    },
    # ========== 财务报告 ==========
    {
        "id": "财务季度报告",
        "batch": 1,
        "content": """【2025年Q4财务报告摘要】

营收情况：
- Q4营收：8000万元，同比增长25%
- 全年营收：2.8亿元，超额完成年度目标（2.5亿）

利润分析：
- 毛利率：65%，同比提升3个百分点
- 净利润：1800万元，净利率22.5%

成本结构：
- 人力成本：45%
- 销售费用：20%
- 研发投入：18%
- 管理费用：12%
- 其他：5%""",
    },
    # ========== 合作伙伴 ==========
    {
        "id": "战略合作签约",
        "batch": 1,
        "content": """【战略合作签约仪式】
日期：2025年12月10日

合作伙伴：华为云

合作内容：
1. 联合解决方案：共同打造行业AI解决方案
2. 市场拓展：华为云作为首选云服务商
3. 技术支持：获得华为技术专家支持
4. 资源共享：共享客户资源和市场渠道

合作期限：3年

商业目标：
- 年度联合销售额：5000万元
- 联合客户数：50家
- 认证解决方案：3个""",
    },
    # ========== 用户反馈 ==========
    {
        "id": "用户反馈分析",
        "batch": 1,
        "content": """【Q4用户反馈分析报告】

反馈数量：共收集用户反馈2000条

正面反馈（60%）：
- 产品功能强大，解决实际问题
- 响应速度快，用户体验好
- 技术支持专业，问题解决及时

改进建议（30%）：
- 希望增加移动端功能
- 部分界面操作复杂，建议简化
- 报价偏高，希望有更灵活的套餐

负面反馈（10%）：
- 系统偶尔卡顿
- 某些功能文档不完善

NPS评分：45（行业平均30）""",
    },
]


async def main():
    import m_flow
    from m_flow.api.v1.search import RecallMode

    print("=" * 80)
    print("新解决方案综合测试")
    print("=" * 80)

    # ==================== 1. 清空数据库 ====================
    print("\n[1] 清空数据库...")
    try:
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)
        print("    ✅ 数据库已清空")
    except Exception as e:
        print(f"    ⚠️  清空警告: {e}")

    # ==================== 2. 分批写入（测试合并/新建）====================
    print("\n[2] 分批写入20条事件...")

    # 按 batch 分组
    batches: Dict[int, List[dict]] = {}
    for event in TEST_EVENTS:
        batch_num = event.get("batch", 1)
        if batch_num not in batches:
            batches[batch_num] = []
        batches[batch_num].append(event)

    total_start = time.time()

    for batch_num in sorted(batches.keys()):
        events = batches[batch_num]
        print(f"\n    Batch {batch_num}: {len(events)} 条事件")

        batch_start = time.time()

        for event in events:
            event_id = event["id"]
            content = event["content"]

            # 使用 event_id 作为文档名，使得相同 event_id 的内容能被路由到同一个 episode
            await m_flow.add(content, dataset_name=f"episode_{event_id}")

        # 运行 memorize
        await m_flow.memorize()

        batch_elapsed = time.time() - batch_start
        print(f"        耗时: {batch_elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\n    总耗时: {total_elapsed:.1f}s")

    # ==================== 3. 检查入库质量 ====================
    print("\n[3] 检查入库质量...")

    # 初始化计数变量
    episode_count = 0
    facet_count = 0
    point_count = 0
    entity_count = 0

    try:
        from m_flow.adapters.graph import get_graph_provider

        graph_engine = await get_graph_provider()

        # 统计 Episode
        result = await graph_engine.query("MATCH (n:Node) WHERE n.properties.type = 'Episode' RETURN count(n) as cnt")
        episode_count = result[0]["cnt"] if result else 0

        # 统计 Facet
        result = await graph_engine.query("MATCH (n:Node) WHERE n.properties.type = 'Facet' RETURN count(n) as cnt")
        facet_count = result[0]["cnt"] if result else 0

        # 统计 FacetPoint
        result = await graph_engine.query(
            "MATCH (n:Node) WHERE n.properties.type = 'FacetPoint' RETURN count(n) as cnt"
        )
        point_count = result[0]["cnt"] if result else 0

        # 统计 Entity
        result = await graph_engine.query("MATCH (n:Node) WHERE n.properties.type = 'Entity' RETURN count(n) as cnt")
        entity_count = result[0]["cnt"] if result else 0

        print(f"    Episodes: {episode_count}")
        print(f"    Facets: {facet_count}")
        print(f"    FacetPoints: {point_count}")
        print(f"    Entities: {entity_count}")

        # 检查合并效果（智能客服项目应该只有1个episode，但有3批内容）
        result = await graph_engine.query("""
            MATCH (n:Node) 
            WHERE n.properties.type = 'Episode' 
            RETURN n.properties.name as name, n.properties.summary as summary
            LIMIT 5
        """)

        print("\n    前5个 Episodes:")
        for r in result:
            name = r.get("name", "")[:50]
            summary = (r.get("summary") or "")[:80]
            print(f"      - {name}: {summary}...")

        # 检查 FacetPoints 质量
        result = await graph_engine.query("""
            MATCH (n:Node) 
            WHERE n.properties.type = 'FacetPoint' 
            RETURN n.properties.search_text as search_text
            LIMIT 10
        """)

        print("\n    前10个 FacetPoints:")
        for r in result:
            st = r.get("search_text", "")[:60]
            print(f"      - {st}")

    except Exception as e:
        print(f"    ⚠️  质量检查异常: {e}")
        import traceback

        traceback.print_exc()

    # ==================== 4. 检索精度测试 ====================
    print("\n[4] 检索精度测试...")

    test_queries = [
        # 具体数值查询
        ("智能客服系统的投资成本是多少？", ["40万"]),
        ("数据中台的预算是多少？", ["180万"]),
        ("双十一GMV是多少？", ["1.2亿"]),
        ("员工培训预算多少？", ["50万", "培训"]),
        # 技术方案查询
        ("智能客服用了什么技术？", ["GPT-4o", "Kuzu"]),
        ("数据中台采用什么架构？", ["湖仓一体", "Databricks", "Delta Lake"]),
        ("DevOps平台有什么成果？", ["CI/CD", "容器化"]),
        # 效果指标查询
        ("智能客服上线后效果如何？", ["响应时间", "满意度", "成本"]),
        ("安全测评发现了什么问题？", ["SQL注入", "XSS", "漏洞"]),
        ("微服务改造的效果？", ["可用性", "99.99%"]),
        # 时间相关查询
        ("智能客服什么时候上线的？", ["12月", "上线"]),
        ("等保测评是什么时候？", ["11月"]),
        # 综合查询
        ("有哪些和AI相关的项目？", ["智能客服", "AI", "GPT"]),
        ("财务状况怎么样？", ["营收", "利润", "8000万"]),
    ]

    passed = 0
    failed = 0

    for query, expected_keywords in test_queries:
        try:
            results = await m_flow.search(query_type=RecallMode.EPISODIC, query_text=query)

            # 检查前3个结果中是否包含期望的关键词
            top_results_text = ""
            for r in results[:3]:
                if hasattr(r, "payload"):
                    payload = r.payload
                    if isinstance(payload, dict):
                        for v in payload.values():
                            top_results_text += str(v) + " "
                    else:
                        top_results_text += str(payload) + " "
                else:
                    top_results_text += str(r) + " "

            # 检查是否命中
            hits = [kw for kw in expected_keywords if kw in top_results_text]
            hit_ratio = len(hits) / len(expected_keywords)

            if hit_ratio >= 0.5:  # 至少命中一半关键词
                print(f'    ✅ "{query[:30]}..." - 命中 {len(hits)}/{len(expected_keywords)}')
                passed += 1
            else:
                print(
                    f'    ❌ "{query[:30]}..." - 命中 {len(hits)}/{len(expected_keywords)}, 期望: {expected_keywords}'
                )
                failed += 1

        except Exception as e:
            print(f'    ❌ "{query[:30]}..." - 错误: {e}')
            failed += 1

    # ==================== 5. 总结 ====================
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    print(f"""
    📊 入库统计:
       - Episodes: {episode_count} (预期: ~15-17，因为有合并)
       - Facets: {facet_count}
       - FacetPoints: {point_count}
       - Entities: {entity_count}
       - 总耗时: {total_elapsed:.1f}s
    
    🎯 检索精度:
       - 通过: {passed}/{passed + failed} ({100 * passed // (passed + failed)}%)
       - 失败: {failed}/{passed + failed}
    """)

    if episode_count < 20:
        print(f"    ✅ 合并生效：20条事件生成了 {episode_count} 个 Episodes")

    if point_count > 0:
        print(f"    ✅ FacetPoint 新方案生效：共生成 {point_count} 个细粒度点")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
