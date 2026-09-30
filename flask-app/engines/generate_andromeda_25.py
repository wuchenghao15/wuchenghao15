#!/usr/bin/env python3
"""
仙女座 25 星域 · 子系统代码生成器
================================

读下面 CONFIG 里的 25 个星域定义 → 批量产出 ai_xxx_engine.py
每个引擎 ~120 行, 继承 BaseAndromedaSubsystem.
"""
from __future__ import annotations
import os, sys, re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ENGINES_DIR = PROJECT_ROOT / "engines"

# ═══════════════════════════════════════════════════════════
# 25 星域完整定义
# ═══════════════════════════════════════════════════════════
# 格式: (code, icon, cn_name, en_name, desc, modes, employees)
#   code: 英文代号 → 文件名 ai_{code}_engine.py, task_id 前缀
#   modes: [(mode_key, mode_name, icon, mode_desc, prompt_template_str)]
#   employees: [(employee_id, cn_name, type, level, prompt)]

STARS = [
    # ═══ 已有 6 个 (跳过, 不覆盖) ═══
    # 文曲星 / 瑶池 / 梵音 / 繁花 / 混天绫 / 太极

    # ═══ 新 19 个 ═══
    {
        "code": "qianShou", "icon": "🤲", "name": "千手", "en": "Qianshou",
        "desc": "中枢神经元系统 — 统一路由/负载均衡/请求汇聚",
        "db_table": "mt_qianshou_routes", "artifact_dir": "qianshou_artifacts", "ext": "json",
        "daemon": "sys_qianshou",
        "modes": [
            ("route", "智能路由", "🛤️", "根据请求类型分发到对应子系统",
             "分析下面的请求, 决定应该路由到哪个仙女位子系统 (文曲星/瑶池/梵音/繁花/混天绫/太极 等), 给出理由和完整路由方案:\n{topic}"),
            ("compose", "多子系统编排", "🔗", "串联多个子系统完成复杂任务",
             "设计一个多子系统协作流水线, 完成: {topic}\n列出每个环节用哪个子系统 + 输入输出格式"),
            ("broadcast", "广播通知", "📢", "向所有子系统广播状态更新",
             "写一条仙女座全系统广播通知, 主题: {topic}"),
            ("merge", "结果汇聚", "🔀", "聚合多个子系统输出为统一结果",
             "把下面来自多个子系统的输出, 汇聚成一个统一的最终报告:\n{topic}"),
            ("registry", "注册表", "📋", "查看所有子系统状态/能力/健康度",
             "列出仙女座 25 星域所有子系统的能力清单: {topic}"),
        ],
        "employees": [
            ("qs_router", "路由", "Router", 9, "千手中枢路由专家. 快速判断请求类型 → 精准路由到对应子系统. 输出 JSON 格式路由决策."),
            ("qs_compose", "编排", "Composer", 8, "多子系统编排专家. 设计流水线让多个子系统协同完成复杂任务. 输出步骤清单."),
            ("qs_merge", "汇聚", "Merger", 7, "多源结果汇聚专家. 把分散的子系统输出整合成统一、连贯的最终报告."),
        ],
    },
    {
        "code": "ziwei", "icon": "🔮", "name": "紫微", "en": "Ziwei",
        "desc": "预测推演系统 — 趋势预测/风险预警/决策辅助",
        "db_table": "mt_ziwei_tasks", "artifact_dir": "ziwei_artifacts", "ext": "md",
        "daemon": "sys_ziwei",
        "modes": [
            ("forecast", "趋势预测", "📈", "基于历史数据推演未来走势",
             "基于以下信息, 预测未来 3 个月的趋势: {topic}\n给出 5 个关键指标 + 置信度 + 拐点预警"),
            ("risk", "风险预警", "⚠️", "识别潜在风险点 + 应对方案",
             "分析以下场景的潜在风险: {topic}\n列出 Top 5 风险 + 概率 + 影响 + 应对策略"),
            ("decision", "决策辅助", "🧭", "多方案对比 + 推荐最优解",
             "针对下面的决策场景, 给出 3 个可选方案并推荐最优: {topic}\n每个方案的利弊 + 成本 + 风险"),
            ("scenario", "情景模拟", "🎲", "假设性推演 (如 X 发生会怎样)",
             "情景模拟: 假设 {topic}, 会发生什么?\n推演 3 个时间节点 (1天/1周/1月) 的连锁反应"),
            ("backcast", "归因分析", "🔍", "倒推事件根因 (为什么发生)",
             "归因分析: {topic}\n列出 5 个可能的根因, 按可能性排序, 给出验证方法"),
        ],
        "employees": [
            ("zw_tianji", "天机", "Forecaster", 9, "紫微预测大师. 趋势推演精准, 善于从混沌中找出规律."),
            ("zw_fengjiao", "风控", "RiskManager", 8, "风险预警专家. 提前识别黑天鹅事件."),
            ("zw_cehua", "策话", "Strategist", 7, "决策辅助专家. 多方案对比, 给出清晰推荐."),
        ],
    },
    {
        "code": "fuxi", "icon": "🧬", "name": "伏羲", "en": "Fuxi",
        "desc": "数据挖掘系统 — 关联分析/聚类/模式发现",
        "db_table": "mt_fuxi_tasks", "artifact_dir": "fuxi_artifacts", "ext": "md",
        "daemon": "sys_fuxi",
        "modes": [
            ("associate", "关联发现", "🔗", "从海量数据中找隐藏关联",
             "在以下数据中发现隐藏的关联关系: {topic}\n用 -> 表示因果/相关, 给每个关联打分 1-10"),
            ("cluster", "聚类分组", "📊", "自动分组 + 各组特征画像",
             "把下面的数据分成 3-5 组, 每组给出一个标签 + 特征画像: {topic}"),
            ("pattern", "模式挖掘", "🔄", "发现重复模式/周期性/异常",
             "在下面的数据中挖掘模式: 周期性? 重复行为? 异常点? {topic}"),
            ("anomaly", "异常检测", "🚨", "识别离群点 + 可能原因",
             "异常检测: 在 {topic} 中找出异常点 (离群值/突变/不符合模式的), 说明为什么异常"),
            ("profile", "画像生成", "👤", "基于数据生成用户/群体画像",
             "基于以下信息生成画像: {topic}\n用 5 个维度描述 (如年龄/兴趣/行为/偏好/风险)"),
        ],
        "employees": [
            ("fx_bagua", "八卦", "DataMiner", 9, "伏羲八卦数据挖掘大师. 善从混沌数据中发现隐藏规律."),
            ("fx_yinyang", "阴阳", "PatternFinder", 8, "模式发现专家. 周期性/对称性/因果关系一眼看出."),
            ("fx_generation", "生成", "Profiler", 7, "画像生成专家. 用最少的数据勾勒最精准的画像."),
        ],
    },
    {
        "code": "nuwa", "icon": "🌐", "name": "女娲", "en": "Nuwa",
        "desc": "前端UI/UX生成系统 — 页面/组件/设计稿自动生成",
        "db_table": "mt_nuwa_tasks", "artifact_dir": "nuwa_artifacts", "ext": "html",
        "daemon": "sys_nuwa",
        "modes": [
            ("page", "页面生成", "📄", "描述 → 完整 HTML 页面代码",
             "根据需求生成一个完整的单文件 HTML 页面 (含 CSS + JS): {topic}\n要求: 现代化设计, 响应式, 用 Element Plus 风格配色 (#0B0A1E 主色)"),
            ("component", "组件生成", "🧩", "描述 → Vue/React 组件代码",
             "生成一个 Vue 单文件组件: {topic}\n<template>+<script>+<style scoped>"),
            ("design", "设计规范", "🎨", "生成 Element Plus 风格设计 Token",
             "为以下场景生成完整设计 Token (颜色/字体/间距/圆角): {topic}"),
            ("layout", "布局方案", "📐", "同需求 3 种布局方案对比",
             "为 {topic} 给出 3 种布局方案 (侧边栏/顶栏/分栏), 每种的优缺点 + 适用场景"),
            ("css", "CSS 生成", "🎯", "描述 → 纯 CSS 动画/效果代码",
             "生成纯 CSS (无 JS) 实现的效果: {topic}"),
        ],
        "employees": [
            ("nw_niangniang", "娘娘", "PageGen", 9, "女娲造人. 描述到完整页面, 一行代码一行心血."),
            ("nw_fashou", "巧手", "ComponentGen", 8, "组件生成专家. Vue/React 组件, Props/Events/Slots 齐全."),
            ("nw_meiyu", "美玉", "Designer", 7, "设计规范专家. Element Plus Token, 配色精准."),
        ],
    },
    {
        "code": "luban", "icon": "⚙️", "name": "鲁班", "en": "Luban",
        "desc": "硬件/Arduino工程系统 — 电路图/代码/DIY方案",
        "db_table": "mt_luban_tasks", "artifact_dir": "luban_artifacts", "ext": "md",
        "daemon": "sys_luban",
        "modes": [
            ("circuit", "电路设计", "🔌", "需求 → 电路图 + 元件清单",
             "为以下需求设计电路图: {topic}\n给出元件清单 (型号+数量+单价) + 连线说明 + 注意事项"),
            ("firmware", "固件代码", "💾", "功能需求 → Arduino 代码",
             "为以下功能写 Arduino (Uno/Nano) 代码: {topic}\n要求: 中文注释 + 模块化 + 含 setup/loop"),
            ("diy", "DIY方案", "🛠️", "给新手的分步制作指南",
             "写一个新手能跟着做的分步 DIY 指南: {topic}\n每步配文字说明 + 关键代码片段 + 常见坑"),
            ("sensor", "传感器选型", "📡", "需求 → 推荐传感器 + 接线 + 代码",
             "根据测量需求推荐传感器: {topic}\n对比 3 款 (精度/价格/难度/是否推荐) + 接线图描述 + 测试代码"),
            ("troubleshoot", "硬件排障", "🔧", "现象 → 可能原因 + 排查步骤",
             "硬件故障排障: 现象是 {topic}\n列出 5 个可能原因 + 逐步排查流程 + 解决办法"),
        ],
        "employees": [
            ("lb_shifu", "师傅", "CircuitDesigner", 9, "鲁班大师. 电路图 + 代码 + 成本全考虑."),
            ("lb_xiaojiang", "小将", "FirmwareDev", 8, "Arduino 固件专家. 模块化、中文注释、含 setup/loop."),
            ("lb_gongjiang", "工匠", "DIYGuide", 7, "DIY 指南专家. 新手友好, 每步都有图和坑."),
        ],
    },
    {
        "code": "bianque", "icon": "🧪", "name": "扁鹊", "en": "Bianque",
        "desc": "代码诊断修复系统 — Bug定位/性能调优/重构建议",
        "db_table": "mt_bianque_tasks", "artifact_dir": "bianque_artifacts", "ext": "md",
        "daemon": "sys_bianque",
        "modes": [
            ("diagnose", "Bug诊断", "🔍", "报错堆栈 → 根因 + 修复",
             "诊断代码问题: {topic}\n列出可能根因 (按概率) + 修复建议 + 验证方法"),
            ("performance", "性能调优", "⚡", "慢代码 → 优化方案 + 预期提升",
             "为以下慢代码/慢查询提出性能优化: {topic}\n给出 3 个优化点 + 预期提升百分比 + 改后代码"),
            ("refactor", "重构建议", "♻️", "代码坏味道 → 重构方案",
             "对以下代码给出重构建议: {topic}\n识别 3 种坏味道 + 重构方案 + 改后代码片段"),
            ("security", "安全扫描", "🛡️", "代码 → 安全漏洞清单 + 修复",
             "扫描以下代码的安全问题: {topic}\n列出 Top 5 风险 (SQL注入/XSS/硬编码/权限) + 修复代码"),
            ("testgen", "测试生成", "🧪", "函数 → pytest/unittest 测试用例",
             "为以下函数生成单元测试: {topic}\n覆盖正常/边界/异常 3 种情况, 用 pytest"),
        ],
        "employees": [
            ("bq_yi", "医", "BugDoctor", 9, "扁鹊神医. 看一眼代码就知道 Bug 在哪, 药到病除."),
            ("bq_fang", "方", "PerfEngineer", 8, "性能优化专家. 慢代码变快, 快代码变飞."),
            ("bq_jian", "鉴", "CodeReviewer", 7, "代码体检专家. 坏味道一扫光."),
        ],
    },
    {
        "code": "cangjie", "icon": "📚", "name": "仓颉", "en": "Cangjie",
        "desc": "知识/题库系统 — 知识点/题目/解析自动生成",
        "db_table": "mt_cangjie_tasks", "artifact_dir": "cangjie_artifacts", "ext": "md",
        "daemon": "sys_cangjie",
        "modes": [
            ("knowledge", "知识点生成", "💡", "主题 → 结构化知识点",
             "为以下主题生成 5-8 个核心知识点 (含定义/示例/易混点): {topic}"),
            ("question", "出题", "❓", "知识点 → 题目 (选择/填空/问答)",
             "为以下知识点各出 2 道选择题 + 1 道问答题: {topic}\n含选项 + 答案 + 详细解析"),
            ("explain", "解析", "📖", "题目 + 答案 → 详细解析",
             "为以下题目写详细解析: {topic}\n从 3 个角度 (为什么/为什么不/举一反三) 解释"),
            ("outline", "大纲", "📑", "学科 → 完整知识树大纲",
             "为 {topic} 生成完整知识树大纲 (三级目录), 每个叶子节点写一句话说明"),
            ("summary", "总结", "📝", "长文 → 结构化摘要 + 金句",
             "为下面的长文生成 300 字摘要 + 5 个金句: {topic}"),
        ],
        "employees": [
            ("cj_zaoshi", "造字", "KnowledgeBuilder", 9, "仓颉造字. 每个知识点都精准."),
            ("cj_wenda", "问答", "QuestionMaker", 8, "出题专家. 选择/填空/问答样样精通."),
            ("cj_jiexi", "解析", "Explainer", 7, "解析专家. 为什么/为什么不/举一反三."),
        ],
    },
    {
        "code": "houyi", "icon": "🎯", "name": "后羿", "en": "Houyi",
        "desc": "精准搜索/RAG系统 — 语义搜索/知识召回/精准匹配",
        "db_table": "mt_houyi_tasks", "artifact_dir": "houyi_artifacts", "ext": "md",
        "daemon": "sys_houyi",
        "modes": [
            ("search", "语义搜索", "🔍", "查询 → 最相关的知识片段",
             "对以下查询做语义搜索, 返回 Top 5 最相关内容 (含来源 + 相关度 1-10): {topic}"),
            ("deepsearch", "深度搜索", "🕳️", "复杂问题 → 多源深度答案",
             "深度搜索: {topic}\n从 3 个角度 (是什么/为什么/怎么做) 给出完整答案 + 引用来源"),
            ("compare", "对比", "⚖️", "A vs B → 详细对比表 + 选择建议",
             "对比分析: {topic}\n用表格列出 5 个维度的对比 + 各自适用场景 + 推荐选择"),
            ("source", "溯源", "📖", "观点 → 原始出处 + 演变历史",
             "溯源: {topic}\n这个观点最早出自哪里? 怎么演变的? 现在有哪些不同版本?"),
            ("faq", "FAQ生成", "❓", "主题 → 10 个高频问题 + 答案",
             "为 {topic} 生成 10 个用户最常问的问题 + 简洁答案 (每问 ≤30 字)"),
        ],
        "employees": [
            ("hy_she", "射", "SearchMaster", 9, "后羿射日. 搜索精准, 百发百中."),
            ("hy_suan", "算", "Analyst", 8, "对比分析专家. A vs B 一目了然."),
            ("hy_yuan", "源", "Researcher", 7, "溯源专家. 每个观点都有出处."),
        ],
    },
    {
        "code": "zhenwu", "icon": "🛡️", "name": "真武", "en": "Zhenwu",
        "desc": "安全审查系统 — 代码/配置/API 安全扫描",
        "db_table": "mt_zhenwu_tasks", "artifact_dir": "zhenwu_artifacts", "ext": "md",
        "daemon": "sys_zhenwu",
        "modes": [
            ("scan", "安全扫描", "🔍", "代码 → 漏洞清单 + 风险等级",
             "对以下代码做安全扫描: {topic}\n列出所有发现的问题 (SQL注入/XSS/硬编码/权限/加密) + 风险等级 (HIGH/MEDIUM/LOW)"),
            ("config", "配置审计", "⚙️", "系统配置 → 安全建议",
             "审计以下系统配置的安全性: {topic}\n列出 5 个安全加固点 + 推荐配置"),
            ("threat", "威胁建模", "⚠️", "系统架构 → 攻击面分析",
             "对 {topic} 做威胁建模: 列出所有攻击面 + TOP 3 攻击场景 + 防御方案"),
            ("compliance", "合规检查", "📋", "行为 → 法律/隐私合规分析",
             "对以下操作做合规检查 (法律/隐私/数据保护): {topic}\n列出潜在违规点 + 建议"),
            ("hardening", "加固方案", "🔐", "系统 → 安全加固 checklist",
             "为 {topic} 提供安全加固方案: 列出 10 个加固项 + 实施优先级 + 预期收益"),
        ],
        "employees": [
            ("zw_jiangjun", "将军", "SecurityAuditor", 9, "真武将军. 安全扫描, 火眼金睛."),
            ("zw_mishi", "谋士", "ThreatModeler", 8, "威胁建模专家. 攻击面无一遗漏."),
            ("zw_falv", "法吕", "ComplianceChecker", 7, "合规检查专家. 法律/隐私都覆盖."),
        ],
    },
    {
        "code": "guanzhong", "icon": "🏛️", "name": "管仲", "en": "Guanzhong",
        "desc": "治理规范系统 — 规则制定/流程优化/合规检查",
        "db_table": "mt_guanzhong_tasks", "artifact_dir": "guanzhong_artifacts", "ext": "md",
        "daemon": "sys_guanzhong",
        "modes": [
            ("rule", "规则制定", "📜", "场景 → 完整规则条文",
             "为以下场景制定完整的规则/规范: {topic}\n含: 目的/适用范围/条款(5-10)/违规处理/生效日期"),
            ("process", "流程优化", "🔄", "现有流程 → 优化方案",
             "对以下流程提出优化: {topic}\n当前痛点 → 优化建议 → 新流程步骤 → 预期效果"),
            ("checklist", "检查清单", "✅", "领域 → 合规/质量检查清单",
             "为 {topic} 生成一个 20 项的检查清单 (每项 Yes/No + 备注): 覆盖合规/安全/质量/文档"),
            ("policy", "政策解读", "📖", "政策/法规 → 通俗解读 + 影响分析",
             "解读以下政策/法规: {topic}\n用大白话讲清楚 + 对仙女座系统的影响 + 需要调整什么"),
            ("gap", "差距分析", "📊", "现状 vs 目标 → 差距清单 + 行动计划",
             "差距分析: {topic}\n列出 5 个关键差距 + 填平所需时间/成本/资源 + 优先级排序"),
        ],
        "employees": [
            ("gz_xiangguo", "相国", "RuleMaker", 9, "管仲相国. 规则制定, 滴水不漏."),
            ("gz_libian", "利弊", "ProcessOptimizer", 8, "流程优化专家. 去掉冗余, 提升效率."),
            ("gz_jiancha", "检查", "ComplianceAuditor", 7, "检查清单专家. 20 项覆盖所有维度."),
        ],
    },
    {
        "code": "fanli", "icon": "📈", "name": "范蠡", "en": "Fanli",
        "desc": "数据分析系统 — 指标/报表/洞察/建议",
        "db_table": "mt_fanli_tasks", "artifact_dir": "fanli_artifacts", "ext": "md",
        "daemon": "sys_fanli",
        "modes": [
            ("metric", "指标定义", "📊", "业务 → KPI/指标体系",
             "为 {topic} 设计 KPI 指标体系: 3 个一级指标 + 10 个二级指标 + 每个的定义和计算公式"),
            ("insight", "数据洞察", "💡", "数据 → 洞察 + 行动建议",
             "从以下数据中挖掘洞察: {topic}\n给出 5 个数据洞察 + 每个洞察对应的行动建议"),
            ("report", "报告生成", "📋", "数据 → 结构化分析报告",
             "基于以下数据生成结构化分析报告: {topic}\n含: 执行摘要/数据概览/深度分析/趋势/建议"),
            ("dashboard", "看板设计", "🖥️", "需求 → 数据看板布局",
             "为 {topic} 设计数据看板: 列出 8 个关键指标 + 每个指标用什么图 + 刷新频率"),
            ("abtest", "实验设计", "🧪", "假设 → A/B 测试方案",
             "为 {topic} 设计 A/B 测试方案: 假设 + 样本量 + 测试周期 + 判定标准 + 分流方案"),
        ],
        "employees": [
            ("fl_taigong", "太公", "DataAnalyst", 9, "范蠡陶朱公. 数据分析, 决胜千里."),
            ("fl_zhuce", "策略", "MetricsDesigner", 8, "指标设计专家. KPI 体系完整."),
            ("fl_jianbao", "简报", "ReportWriter", 7, "报告写作专家. 简洁有力."),
        ],
    },
    {
        "code": "shennong", "icon": "🌱", "name": "神农", "en": "Shennong",
        "desc": "教育/学习系统 — 课程/教案/学习路径自动生成",
        "db_table": "mt_shennong_tasks", "artifact_dir": "shennong_artifacts", "ext": "md",
        "daemon": "sys_shennong",
        "modes": [
            ("course", "课程设计", "📚", "主题 → 完整课程大纲 (6-10 节)",
             "为 {topic} 设计一个 8 节的课程大纲: 每节标题 + 3 个知识点 + 1 个小练习 + 预计时长"),
            ("lesson", "教案", "📖", "单课 → 详细教案 (目标/内容/互动/作业)",
             "为以下课题写详细教案: {topic}\n含: 教学目标/导入/新授/互动/总结/作业/板书设计"),
            ("path", "学习路径", "🗺️", "起点 → 目标 → 分阶段路径图",
             "从零基础到精通 {topic} 的学习路径: 5 个阶段 + 每个阶段的里程碑 + 推荐资源"),
            ("quiz", "小测验", "📝", "课程 → 5 题小测验 + 答案解析",
             "为 {topic} 生成 5 道随堂小测验: 3 选择 + 2 填空 + 答案 + 解析"),
            ("feedback", "学习反馈", "💬", "答题记录 → 针对性建议",
             "基于以下答题记录给学习反馈: {topic}\n分析薄弱点 + 针对性练习建议 + 鼓励"),
        ],
        "employees": [
            ("sn_yanhuang", "炎黄", "CourseDesigner", 9, "神农尝百草. 课程设计, 因材施教."),
            ("sn_kejia", "教案", "LessonWriter", 8, "教案专家. 导入/新授/互动/总结."),
            ("sn_fuxi", "伏羲", "PathFinder", 7, "学习路径专家. 从零基础到精通."),
        ],
    },
    {
        "code": "pixiu", "icon": "🎪", "name": "貔貅", "en": "Pixiu",
        "desc": "趣味/娱乐系统 — 笑话/故事/互动小游戏",
        "db_table": "mt_pixiu_tasks", "artifact_dir": "pixiu_artifacts", "ext": "md",
        "daemon": "sys_pixiu",
        "modes": [
            ("joke", "段子笑话", "😂", "主题 → 3 个原创笑话",
             "写 3 个关于 {topic} 的原创段子, 短小精悍 (20 字内)"),
            ("story", "故事", "📖", "主题 → 短故事 (300字)",
             "写一个 300 字以内的短故事, 主题是: {topic}"),
            ("game", "小游戏", "🎮", "需求 → 一个 HTML 小游戏代码",
             "生成一个单文件 HTML 小游戏 (纯前端, Canvas + JS), 玩法: {topic}"),
            ("poem", "写诗", "📜", "主题 → 一首七言绝句",
             "写一首七言绝句, 主题是 {topic}, 要求平起首句押韵"),
            ("brainteaser", "脑筋急转弯", "🧠", "主题 → 3 个急转弯 + 答案",
             "出 3 个关于 {topic} 的脑筋急转弯, 答案放在文末"),
        ],
        "employees": [
            ("px_nawang", "魔王", "JokeMaster", 9, "貔貅魔王. 段子信手拈来."),
            ("px_wenyou", "文游", "StoryTeller", 8, "故事大王. 300 字讲一个好故事."),
            ("px_xiaoxi", "小溪", "GameDev", 7, "小游戏开发. Canvas + JS."),
        ],
    },
    {
        "code": "taigong", "icon": "🧙", "name": "太公", "en": "Taigong",
        "desc": "策略规划系统 — 商业/产品/战略方案",
        "db_table": "mt_taigong_tasks", "artifact_dir": "taigong_artifacts", "ext": "md",
        "daemon": "sys_taigong",
        "modes": [
            ("strategy", "战略方案", "🎯", "目标 → 3 种战略 + 推荐",
             "为达成 {topic}, 设计 3 种可选战略方案: 每个的思路/优劣势/资源需求/推荐指数 (1-10)"),
            ("product", "产品规划", "📱", "需求 → MVP + 迭代路线图",
             "为以下产品需求做规划: {topic}\nMVP (最小可行产品) 功能清单 + 3 个月迭代路线图 + 技术选型"),
            ("business", "商业计划", "💼", "创意 → 商业计划要点",
             "为以下创意写商业计划要点: {topic}\n含: 目标用户/价值主张/商业模式/竞争壁垒/里程碑"),
            ("campaign", "营销活动", "📣", "目标 → 3 个活动方案",
             "为 {topic} 设计 3 种营销活动方案: 每个的创意/渠道/预算/预期效果"),
            ("pricing", "定价策略", "💰", "产品 → 3 档定价 + 依据",
             "为 {topic} 设计定价策略: 免费/基础/高级 三档定价 + 每档包含的功能 + 定价依据"),
        ],
        "employees": [
            ("tg_wangjiang", "望将", "Strategist", 9, "太公望. 战略规划, 决胜千里."),
            ("tg_jiangmen", "将门", "ProductManager", 8, "产品专家. MVP + 路线图."),
            ("tg_business", "商业", "BizPlanner", 7, "商业计划专家."),
        ],
    },
    {
        "code": "yinglong", "icon": "🐉", "name": "应龙", "en": "Yinglong",
        "desc": "自动化编排系统 — 任务流水线/定时任务/工作流",
        "db_table": "mt_yinglong_tasks", "artifact_dir": "yinglong_artifacts", "ext": "json",
        "daemon": "sys_yinglong",
        "modes": [
            ("workflow", "工作流设计", "🔄", "目标 → 步骤式工作流 JSON",
             "设计一个工作流来完成: {topic}\n输出 JSON 格式: [{step_id, action, subsystem, input_schema, output_schema, depends_on}]"),
            ("pipeline", "流水线", "🔗", "多步任务 → 编排方案",
             "编排一个多步骤流水线: {topic}\n每步调哪个仙女位子系统 + 输入输出格式 + 条件分支"),
            ("cron", "定时任务", "⏰", "需求 → crontab 配置 + 说明",
             "设计定时任务: {topic}\n给出 crontab 表达式 + 任务脚本 + 日志策略"),
            ("trigger", "触发器", "⚡", "事件 → 触发条件 + 动作",
             "设计触发器: 当 {topic} 发生时, 触发什么动作?\n条件 (threshold/interval/event) + 动作 (调用哪个子系统)"),
            ("monitor", "监控规则", "📡", "指标 → 告警阈值 + 处理流程",
             "设计监控规则: {topic}\n监控哪些指标 + 告警阈值 + 通知方式 + 自动处理流程"),
        ],
        "employees": [
            ("yl_dragon", "应龙", "WorkflowEngineer", 9, "应龙飞龙. 工作流设计, 行云流水."),
            ("yl_paibu", "排布", "PipelineDesigner", 8, "流水线编排专家. 步骤间数据无缝传递."),
            ("yl_dingshi", "定时", "Scheduler", 7, "定时任务专家. crontab 精准."),
        ],
    },
    {
        "code": "xihe", "icon": "🔭", "name": "羲和", "en": "Xihe",
        "desc": "监控巡检系统 — 系统健康/日志分析/瓶颈定位",
        "db_table": "mt_xihe_tasks", "artifact_dir": "xihe_artifacts", "ext": "md",
        "daemon": "sys_xihe",
        "modes": [
            ("health", "健康检查", "💚", "目标系统 → 健康快照 + 评分",
             "为 {topic} 做健康检查: CPU/内存/磁盘/网络/进程/端口 → 每项 OK/WARN/CRIT + 总体评分 0-100"),
            ("loganalyze", "日志分析", "📋", "日志 → 错误分类 + 趋势 + Top N",
             "分析以下日志: {topic}\n错误分类 (按类型) + 最近趋势 (是否恶化) + Top 3 高频错误 + 解决建议"),
            ("bottleneck", "瓶颈定位", "🔍", "慢系统 → 瓶颈定位 + 优化",
             "定位性能瓶颈: {topic}\n从 CPU/IO/网络/DB 锁 4 个角度排查 → 瓶颈在哪里 + 优化方案 + 预期提升"),
            ("capacity", "容量规划", "📈", "当前负载 → 未来 6 个月扩容建议",
             "容量规划: {topic}\n当前使用率 → 增长趋势 → 什么时候需要扩容 → 扩多少 + 成本估算"),
            ("alarm", "告警规则", "🚨", "关键指标 → 告警阈值 + 升级策略",
             "设计告警规则: {topic}\n告警阈值 (WARN/CRIT) + 通知方式 (钉钉/飞书/短信) + 1-3 级升级策略"),
        ],
        "employees": [
            ("xh_sun", "日御", "HealthChecker", 9, "羲和御日. 系统健康, 一查便知."),
            ("xh_chakan", "察看", "LogAnalyzer", 8, "日志分析专家. 错误分类, 趋势判断."),
            ("xh_pinggu", "评估", "CapacityPlanner", 7, "容量规划专家."),
        ],
    },
    {
        "code": "gonggong", "icon": "🌊", "name": "共工", "en": "Gonggong",
        "desc": "资源管理系统 — 算力/存储/带宽/令牌管理",
        "db_table": "mt_gonggong_tasks", "artifact_dir": "gonggong_artifacts", "ext": "md",
        "daemon": "sys_gonggong",
        "modes": [
            ("resource", "资源盘点", "📦", "系统 → 资源使用快照",
             "盘点 {topic} 的资源使用: 算力/GPU/存储/带宽/令牌 → 每项总量/已用/剩余/使用率"),
            ("alloc", "资源分配", "🎲", "需求 → 最优分配方案",
             "为以下需求分配资源: {topic}\n在 5 个子系统间分配算力/存储/令牌 → 每项分到多少 + 依据"),
            ("cleanup", "清理", "🧹", "磁盘/缓存 → 清理方案 + 预计释放",
             "为 {topic} 设计清理方案: 哪些可以删 + 预计释放多少空间 + 风险 + 执行步骤"),
            ("quota", "配额管理", "📊", "用户/子系统 → 配额方案",
             "为 {topic} 设计配额方案: 每个用户/子系统的 token 上限/存储上限/API 调用频率 + 超额处理"),
            ("cost", "成本分析", "💰", "资源 → 月度/年度成本估算",
             "为 {topic} 做成本分析: 月度电费/云服务费/硬件折旧 → 给出降本 3 个建议"),
        ],
        "employees": [
            ("gg_water", "水神", "ResourceManager", 9, "共工水神. 资源调度, 如臂使指."),
            ("gg_panpian", "盘盘", "Allocator", 8, "分配专家. 5 个子系统间最优分配."),
            ("gg_qingli", "清理", "CleanupExpert", 7, "清理方案专家."),
        ],
    },
    {
        "code": "nezha", "icon": "🔔", "name": "哪吒", "en": "Nezha",
        "desc": "通知告警系统 — 多通道通知/告警升级/心跳保活",
        "db_table": "mt_nezha_tasks", "artifact_dir": "nezha_artifacts", "ext": "md",
        "daemon": "sys_nezha",
        "modes": [
            ("notify", "通知设计", "📢", "场景 → 通知模板 + 通道",
             "为以下场景设计通知: {topic}\n每个通知的标题/正文/优先级 (INFO/WARN/CRIT) + 发送通道 (飞书/邮件/短信)"),
            ("escalation", "升级策略", "📈", "告警 → 1-3 级升级流程",
             "设计告警升级策略: {topic}\n1 级 (通知值班) → 10 分钟无响应升级 2 级 (通知组长) → 20 分钟升级 3 级 (通知主管)"),
            ("heartbeat", "心跳方案", "💓", "服务 → 心跳/超时/恢复策略",
             "为 {topic} 设计心跳方案: 心跳间隔 + 超时阈值 + 连续几次失败触发告警 + 恢复后怎么通知"),
            ("channel", "通道配置", "📡", "通道 → 接入 + 鉴权 + 测试",
             "为 {topic} 配置通知通道: 飞书 webhook / SMTP 邮件 / API 调用 → 接入步骤 + 鉴权方式 + 测试代码"),
            ("template", "模板设计", "📝", "类型 → 通知模板 (变量+格式)",
             "为 {topic} 设计 5 个通知模板: 每个含 {{变量}} 占位符 + 示例 + 发送通道"),
        ],
        "employees": [
            ("nz_sanhai", "三太子", "NotifyMaster", 9, "哪吒三太子. 通知设计, 风火轮一般快."),
            ("nz_qiankun", "乾坤", "EscalationDesigner", 8, "升级策略专家. 1/2/3 级清晰."),
            ("nz_jinzhuan", "金转", "ChannelConfig", 7, "通道配置专家."),
        ],
    },
    {
        "code": "yuelao", "icon": "🏮", "name": "月老", "en": "Yuelao",
        "desc": "社交匹配系统 — AI员工组队/专家匹配/资源对接",
        "db_table": "mt_yuelao_tasks", "artifact_dir": "yuelao_artifacts", "ext": "md",
        "daemon": "sys_yuelao",
        "modes": [
            ("match", "智能匹配", "💘", "需求 → 最佳专家/子系统配对",
             "根据以下需求, 匹配最合适的仙女位子系统或 AI 员工: {topic}\n给 Top 3 匹配 + 匹配度 1-10 + 理由"),
            ("team", "组队方案", "👥", "任务 → 最优 3-5 人 AI 团队",
             "为以下任务组一个最优 AI 团队: {topic}\n3-5 个角色 + 每个角色用哪个 AI 员工 (仙女位子系统) + 协作流程"),
            ("network", "社交图谱", "🕸️", "子系统 → 协作关系图",
             "画一张仙女座 25 星域的协作关系图 (哪些子系统常一起工作): {topic}\n列出 Top 5 高频组合 + 一起完成过什么"),
            ("recommend", "推荐", "⭐", "用户 → 可能感兴趣的能力",
             "基于以下用户画像推荐仙女座能力: {topic}\n推荐 Top 5 子系统 + 每个的使用场景"),
            ("pairing", "结对", "🤝", "A + B → 协作方案",
             "设计以下两个仙女位子系统的协作方案: {topic}\nA 输出什么 → B 输入什么 → 中间怎么转换 → 端到端示例"),
        ],
        "employees": [
            ("yl_yue", "月老", "MatchMaker", 9, "月老. 红线一牵, 缘分自然来."),
            ("yl_hongniang", "红娘", "TeamBuilder", 8, "组队专家. 3-5 人 AI 团队, 角色分配精准."),
            ("yl_qianqiu", "千秋", "Networker", 7, "社交图谱专家."),
        ],
    },
]

# ═══════════════════════════════════════════════════════════
# 引擎代码模板
# ═══════════════════════════════════════════════════════════
ENGINE_TEMPLATE = '''#!/usr/bin/env python3
"""
__ICON__ __NAME__ (__EN__) — 仙女座 __DESC__
"""
from __future__ import annotations
import json, os, sys, time, uuid, argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from andromeda_base import BaseAndromedaSubsystem, PROJECT_ROOT, DB_PATH, detect_ollama


class __EN__Engine(BaseAndromedaSubsystem):
    SUBSYSTEM_NAME = "__NAME__"
    SUBSYSTEM_ICON = "__ICON__"
    SUBSYSTEM_DESC = "__DESC__"
    DB_TABLE = "__DB_TABLE__"
    DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS __DB_TABLE__ (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE,
    mode TEXT,
    mode_name TEXT,
    topic TEXT,
    final_text TEXT,
    artifact_path TEXT,
    status TEXT DEFAULT 'pending',
    duration_sec INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    done_at TEXT
);
CREATE INDEX IF NOT EXISTS idx__CODE___status ON __DB_TABLE__(status, created_at);
"""
    ARTIFACT_DIR = "__ARTIFACT_DIR__"
    ARTIFACT_EXT = "__EXT__"
    DAEMON_NAME = "__DAEMON__"
    DAEMON_DUTY = "__DESC__"
    AI_EMPLOYEES = __EMPLOYEES_REPR__

    MODES = __MODES_REPR__

    def write(self, mode: str, topic: str, **kwargs) -> str:
        m = self.MODES.get(mode)
        if not m:
            print(f"  Unknown mode: {mode}"); return ""
        task_id = self.new_task_id(prefix="__PREFIX__")
        print("\\n" + "=" * 55)
        print(f"  {self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME} - {m['icon']} {m['name']}")
        print(f"  task_id: {task_id} · topic: {topic[:50]}")
        print("=" * 55)

        self.db_insert_task(task_id=task_id, mode=mode, mode_name=m["name"],
                             topic=topic, status="generating")
        t0 = time.time()
        print("  Ollama generating...")
        prompt = m["prompt"](topic, kwargs)
        raw = self.ollama_generate(prompt, max_tokens=1024)
        dur = int(time.time() - t0)
        print(f"  Done: {dur}s · {len(raw)} chars")

        artifact = self.save_artifact(task_id, raw, header_lines=[
            f"# {self.SUBSYSTEM_ICON} {self.SUBSYSTEM_NAME} - {m['name']}",
            f"> Topic: {topic[:80]} · {dur}s",
        ])
        self.write_task(task_id, raw, artifact_path=str(artifact), duration_sec=dur)
        print(f"  Artifact: {artifact}")
        return task_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="__ICON__ __NAME__")
    ap.add_argument("mode", nargs="?", choices=list(__EN__Engine.MODES.keys()), default="help")
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--modes", action="store_true")
    ap.add_argument("--list", "-l", type=int, const=5, nargs="?")
    args = ap.parse_args()
    eng = __EN__Engine()
    if args.modes or args.mode == "help":
        print(f"{eng.SUBSYSTEM_ICON} {eng.SUBSYSTEM_NAME} - {len(eng.MODES)} modes:")
        for k,v in eng.MODES.items():
            print(f"  {v['icon']} {k:12s} {v['name']:10s} - {v['desc']}")
    elif args.list:
        for t in eng.db_list_tasks(args.list):
            print(f"  {t['task_id']} [{t.get('status','?')}] {t.get('topic','')[:40]}")
    elif args.topic:
        tid = eng.write(args.mode, args.topic)
        print(f"\\nDone task_id={tid}")
    else:
        ap.print_help()
'''


def generate_engine(star: dict) -> str:
    """生成一个引擎文件的完整 Python 源码"""
    # MODES dict
    modes_lines = []
    for mk, mname, micon, mdesc, mprompt in star["modes"]:
        safe_prompt = mprompt.replace("\n", "\\n").replace('"""', "'''")
        modes_lines.append(f'''    "{mk}": {{
        "name": "{mname}", "icon": "{micon}", "desc": "{mdesc}",
        "prompt": lambda topic, kw: f"""{safe_prompt}"""
    }}''')
    modes_repr = "{\n" + ",\n".join(modes_lines) + "\n    }"

    # AI_EMPLOYEES
    emp_lines = []
    for eid, ename, etype, elevel, eprompt in star["employees"]:
        emp_lines.append(f'        ("{eid}", "{ename}", "{etype}", {elevel}, "{eprompt}")')
    employees_repr = "[\n" + ",\n".join(emp_lines) + "\n    ]"

    src = ENGINE_TEMPLATE
    reps = {
        "__ICON__": star["icon"], "__NAME__": star["name"],
        "__EN__": star["en"], "__DESC__": star["desc"],
        "__DB_TABLE__": star["db_table"], "__CODE__": star["code"],
        "__ARTIFACT_DIR__": star["artifact_dir"], "__EXT__": star["ext"],
        "__DAEMON__": star["daemon"], "__PREFIX__": star["code"][:3],
        "__MODES_REPR__": modes_repr, "__EMPLOYEES_REPR__": employees_repr,
    }
    for token, val in reps.items():
        src = src.replace(token, str(val))
    return src


def main():
    generated = []
    for star in STARS:
        fname = f"ai_{star['code']}_engine.py"
        fpath = ENGINES_DIR / fname
        if fpath.exists():
            print(f"  ⏭️  已存在, 跳过: {fname}")
            continue
        src = generate_engine(star)
        fpath.write_text(src, encoding="utf-8")
        generated.append(fname)
        print(f"  ✅ {fname:35s} {star['icon']} {star['name']}")

    print(f"\n📊 生成: {len(generated)} 个新引擎")
    if generated:
        print(f"💡 下一步: cd engines && python3 ai_xxx_engine.py --modes")


if __name__ == "__main__":
    main()
