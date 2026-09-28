"""
仙女座星系子系统 — 阶梯课程内容生成引擎

三大角色 (复用 employee_registry):
  andromeda_teacher    → 阶梯初级 (elementary)
  andromeda_professor  → 阶梯中级 (intermediate)
  andromeda_scholar    → 阶梯高级 (advanced)

产出:
  Series (课程系列) + Episode (单集脚本 + 合规审查)

flow_id: galaxy_content_engine
version: v23.0.0
依赖: galaxy_db + galaxy_compliance + andromeda_auto_evolution._ollama_chat
"""
import json
import os
import re
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engines import galaxy_db as gdb
from engines import galaxy_compliance as gcomp


# ============================================================
# 阶梯模板 (三大角色 × 三个难度)
# ============================================================

ROLE_TEMPLATES = {
    'andromeda_teacher': {
        'title': '数字教师',
        'level': 'elementary',
        'duration_range': (15, 30),  # 秒
        'audience': '零基础入门',
        'style': '亲切、类比、循序渐进',
        'script_template': """你是一位{audience}的数字教师。请用亲切的类比方式讲解"{topic}"。

要求:
1. 时长 {duration} 秒左右 (抖音短视频标准)
2. 语言口语化, 避免术语
3. 开头 3 秒必须抓住注意力 (钩子句)
4. 结尾留一个互动问题
5. 绝对不能出现广告法极限词 (最、第一、唯一、100%、完美等)
6. 如果引用知识点, 必须标注来源出处

输出 JSON:
{{"hook": "开头钩子句", "content": "主体讲解 (200-300字)", "cta": "结尾互动", "duration": {duration}}}""",
    },
    'andromeda_professor': {
        'title': '数字教授',
        'level': 'intermediate',
        'duration_range': (30, 60),
        'audience': '已有基础的进阶学习者',
        'style': '严谨、结构化、有实例',
        'script_template': """你是一位{audience}的数字教授。请结构化讲解"{topic}"。

要求:
1. 时长 {duration} 秒左右
2. 用 3 分结构 (概念 → 实例 → 应用)
3. 包含 1-2 个具体代码/数学/实验实例
4. 明确指出易错点
5. 绝对不能出现广告法极限词 (最、第一、唯一、100%、完美等)
6. 学术内容注明参考来源

输出 JSON:
{{"hook": "开头钩子", "concept": "概念", "example": "实例", "pitfall": "易错点", "cta": "延伸方向", "duration": {duration}}}""",
    },
    'andromeda_scholar': {
        'title': '数字学者',
        'level': 'advanced',
        'duration_range': (60, 90),
        'audience': '前沿研究者/深度学习者',
        'style': '深度、论文级、前沿视角',
        'script_template': """你是一位{audience}的数字学者。请以前沿视角综述"{topic}"。

要求:
1. 时长 {duration} 秒左右
2. 包含: 研究现状 → 关键突破 → 未来方向
3. 引用 1-2 篇代表性论文/成果 (标注出处)
4. 指出 2-3 个尚未解决的开放问题
5. 绝对不能出现广告法极限词 (最、第一、唯一、100%、完美等)

输出 JSON:
{{"hook": "前沿钩子", "landscape": "研究现状", "breakthrough": "关键突破", "open_questions": "开放问题", "cta": "学术延伸", "references": ["来源1", "来源2"], "duration": {duration}}}""",
    },
}


# ============================================================
# 调用 LLM (优先复用现有 _ollama_chat, fallback 本地推理)
# ============================================================

def _call_llm(prompt: str, system: str = '你是仙女座星系的数字教师。') -> Optional[str]:
    """
    调用 LLM 生成脚本, 优先级:
      1. andromeda_auto_evolution._ollama_chat (有 Ollama 时)
      2. ai_local_inference_engine (本地推理)
      3. 本地 fallback 模板填充 (保证不挂)
    """
    # 1. 尝试 Ollama
    try:
        from engines.andromeda_auto_evolution import _ollama_chat
        resp = _ollama_chat(prompt, system=system)
        if resp:
            return resp
    except Exception:
        pass

    # 2. 尝试本地推理引擎
    try:
        from engines.ai_local_inference_engine import local_infer
        resp = local_infer(prompt, system=system)
        if resp:
            return resp
    except Exception:
        pass

    # 3. Fallback: 返回提示
    return json.dumps({"hook": "本期内容正在制作中", "content": "敬请期待", "duration": 15})


# ============================================================
# 主入口: 生成阶梯系列
# ============================================================

def generate_series(title: str, topic: str, subject: str,
                    role_type: str = 'andromeda_professor',
                    episode_count: int = 5,
                    employee_id: str = None) -> Dict:
    """
    生成一个阶梯课程系列:
      1. 建 series
      2. 逐集生成脚本 (LLM)
      3. 每集过合规审查 Pipeline
      4. 写入 DB, 返回结果
    """
    import logging
    logger = logging.getLogger('galaxy_content')

    # 初始化 DB
    gdb.ensure_galaxy_tables()

    # 校验角色
    if role_type not in ROLE_TEMPLATES:
        raise ValueError(f"未知 role_type: {role_type}, 有效值: {list(ROLE_TEMPLATES.keys())}")

    tmpl = ROLE_TEMPLATES[role_type]

    # 1. 建系列
    sid = gdb.create_series(
        title=title,
        level=tmpl['level'],
        subject=subject,
        role_type=role_type,
        description=f"【{tmpl['title']}】{tmpl['audience']}·{topic}",
        employee_id=employee_id,
    )
    logger.info(f"[GALAXY] 🆕 Series 创建: {sid} ({title})")

    results = {'series_id': sid, 'episodes': [], 'summary': {'pass': 0, 'review': 0, 'block': 0}}

    # 2. 逐集生成
    for i in range(1, episode_count + 1):
        episode_title = f"{topic} — Part {i}/{episode_count}"
        duration = (tmpl['duration_range'][0] + tmpl['duration_range'][1]) // 2

        # 生成脚本
        prompt = tmpl['script_template'].format(
            topic=topic,
            audience=tmpl['audience'],
            duration=duration,
        )
        script_raw = _call_llm(prompt, system=f"你是仙女座星系的{tmpl['title']}。{tmpl['style']}。")

        # 解析 JSON (容错)
        script_text = ''
        try:
            start = script_raw.find('{')
            end = script_raw.rfind('}') + 1
            if start >= 0 and end > start:
                obj = json.loads(script_raw[start:end])
                # 拼成完整脚本文本 (用于合规审查)
                script_text = json.dumps(obj, ensure_ascii=False)
            else:
                script_text = script_raw
        except (json.JSONDecodeError, TypeError):
            script_text = script_raw

        # 3. 快速预检 (极限词/红线/隐私 — 300ms 内)
        quick_ok, quick_blockers = gcomp.quick_precheck(script_text)

        # 4. 写入 episode
        eid = gdb.create_episode(sid, i, episode_title, script=script_text)

        episode_result = {
            'episode_id': eid,
            'episode_no': i,
            'title': episode_title,
            'quick_ok': quick_ok,
            'quick_blockers': quick_blockers,
        }

        if not quick_ok:
            # 快速预检 BLOCK → 跳过全量审查, 直接标记 BLOCK
            gdb.update_episode_status(eid, 'blocked', compliance_pass=0)
            episode_result['compliance_overall'] = 'BLOCK'
            results['summary']['block'] += 1
        else:
            # 5. 全量 Pipeline (C1~C7)
            full_result = gcomp.run_compliance_pipeline(
                content_id=eid,
                content_type='script',
                text=script_text,
                source_type='self_generated',
            )
            episode_result['compliance_overall'] = full_result['overall']
            episode_result['compliance_detail'] = {
                k: v['result'] for k, v in full_result['checks'].items()
            }

            if full_result['overall'] == 'PASS':
                gdb.update_episode_status(eid, 'compliance_pass', compliance_pass=1,
                                          compliance_log_id=full_result['logs_created'][-1] if full_result['logs_created'] else None)
                results['summary']['pass'] += 1
            elif full_result['overall'] == 'REVIEW':
                gdb.update_episode_status(eid, 'compliance_pass', compliance_pass=0)
                results['summary']['review'] += 1
            else:
                gdb.update_episode_status(eid, 'blocked', compliance_pass=0)
                results['summary']['block'] += 1

        results['episodes'].append(episode_result)
        logger.info(f"[GALAXY]   Episode {i}: {episode_result['compliance_overall']}")

    logger.info(f"[GALAXY] ✅ Series 完成: pass={results['summary']['pass']} "
                f"review={results['summary']['review']} block={results['summary']['block']}")

    return results


# ============================================================
# 批量生成 (多主题 × 多角色)
# ============================================================

def bulk_generate(plans: List[Dict]) -> List[Dict]:
    """
    批量生成多个系列, 每个 plan 包含:
      { 'title': str, 'topic': str, 'subject': str,
        'role_type': str, 'episode_count': int }
    """
    results = []
    for plan in plans:
        try:
            r = generate_series(**plan)
            results.append(r)
        except Exception as e:
            results.append({'error': str(e), 'plan': plan})
    return results


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='仙女座星系 — 阶梯课程生成')
    parser.add_argument('--topic', '-t', type=str, default='Python 列表推导式')
    parser.add_argument('--role', '-r', type=str, default='andromeda_professor',
                        choices=list(ROLE_TEMPLATES.keys()))
    parser.add_argument('--count', '-c', type=int, default=3)
    parser.add_argument('--subject', '-s', type=str, default='编程')
    args = parser.parse_args()

    print(f"🌌 仙女座星系 content_engine")
    print(f"   主题: {args.topic}")
    print(f"   角色: {args.role} ({ROLE_TEMPLATES[args.role]['title']})")
    print(f"   集数: {args.count}")
    print()

    result = generate_series(
        title=f"《{args.topic}》系列",
        topic=args.topic,
        subject=args.subject,
        role_type=args.role,
        episode_count=args.count,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
