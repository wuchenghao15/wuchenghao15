"""
galaxy_dyn_team_engine.py — 仙女座 AI 员工动态组合引擎

核心理念: 不固定 2-3 人小队, 从 33,525 名 AI 员工中按 neuralhub_task 职能
自由组合 (最多 15 人同时协作), 每个职能对视频生产的某个环节负责.

工作流 (Dynamic Video Production Pipeline):
  Phase 1 信息收集 → knowledge_ingest + question_generate (774+2579人)
  Phase 2 文案写作 → copy_write + listening_generate (516+516人)
  Phase 3 分镜规划 → system_plan + ui_designer (774+1人)
  Phase 4 视觉设计 → design_ingest + eigenflux_design_review (774+516人)
  Phase 5 合规审查 → sa_advisor + security_audit + rule_patrol (5138+2063+1032人)
  Phase 6 教育适配 → edu_curriculum_adapt + subject_sync (516+516人)

CLI:
  python3 galaxy_dyn_team_engine.py assemble -t "秦统一六国" [--team-size 12] [--style epic]
  python3 galaxy_dyn_team_engine.py roster                   # 查看全部可组合职能
  python3 galaxy_dyn_team_engine.py simulate -t "量子纠缠"   # 模拟完整协作过程

依赖: 同目录 engines/ (composition_engine, video_renderer, jimeng_pipeline)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = "database/app.db"
TABLE = "mt_andromeda_employee_registry"


# =====================================================================
# 1. 职能 → 视频生产工作流节点映射
# =====================================================================

@dataclass
class RoleAssignment:
    """一个 AI 员工职能 → 视频生产中的职责"""
    neuralhub_task: str          # 员工在 DB 里的 neuralhub_task 值
    job_phase: str               # 工作流阶段 (info/copy/storyboard/visual/compliance/edu)
    job_label: str               # 给人看的标签
    job_output: str              # 这个职能产出什么
    weight: int = 2              # 组合时抽几个人

PHASE_ORDER = ["info", "copy", "storyboard", "visual", "compliance", "edu", "publish"]

ROLE_ASSIGNMENTS: List[RoleAssignment] = [
    # ---- Phase 1: 信息收集 ----
    RoleAssignment("knowledge_ingest",   "info",   "知识吸收员",   "从话题中提取真实知识点和数据", weight=2),
    RoleAssignment("question_generate",  "info",   "知识点出题员", "把知识点转化为有趣的知识点问题", weight=1),
    RoleAssignment("edu_policy_analyze", "info",   "教育政策分析", "判断内容适合哪个年龄段/教育场景", weight=1),

    # ---- Phase 2: 文案写作 ----
    RoleAssignment("copy_write",         "copy",   "文案主笔",     "写 hook + 6 段旁白 + CTA",      weight=2),
    RoleAssignment("listening_generate",  "copy",   "旁白优化员",   "让旁白口语化 适合 TTS 朗读",     weight=1),
    RoleAssignment("eigenflux_chat",      "copy",   "灵感对话员",   "提供多个开头角度和反转建议",     weight=1),

    # ---- Phase 3: 分镜规划 ----
    RoleAssignment("system_plan",         "storyboard", "分镜主规划", "按知识点分布 规划 6 镜头结构", weight=2),
    RoleAssignment("curriculum_designer", "storyboard", "教学设计师", "让分镜符合学习曲线 (易→难)",   weight=1),

    # ---- Phase 4: 视觉设计 ----
    RoleAssignment("design_ingest",       "visual",      "视觉风格师", "选配色/爆炸特效/画面氛围",     weight=2),
    RoleAssignment("eigenflux_design_review", "visual", "视觉审稿人", "检查画面信息密度/视觉引导",   weight=1),
    RoleAssignment("ui_designer",         "visual",      "UI设计师",  "文字排版/卡片布局/字号行距",   weight=1),

    # ---- Phase 5: 合规审查 ----
    RoleAssignment("sa_advisor",          "compliance", "合规审查员", "过 C1~C7 社区规范 + DB 词库",    weight=2),
    RoleAssignment("security_audit",      "compliance", "安全审计员", "额外隐私/版权/引用安全检查",     weight=1),
    RoleAssignment("rule_patrol",         "compliance", "规则巡逻员", "扫描极限词/违禁话术自动替换",     weight=1),

    # ---- Phase 6: 教育适配 ----
    RoleAssignment("edu_curriculum_adapt","edu",        "教育适配员", "调整难度/类比/数据 适合目标用户", weight=1),
    RoleAssignment("subject_sync",        "edu",        "学科同步员", "确保内容和学科最新进展一致",       weight=1),

    # ---- Phase 7: 发布准备 ----
    RoleAssignment("bilibili_sub_extract","publish",    "B站字幕员", "生成 B站适合的字幕时间轴",        weight=1),
    RoleAssignment("planner",             "publish",    "发布规划师", "选平台/标题/tag/发布时间",       weight=1),
]


# =====================================================================
# 2. 从 DB 抽 AI 员工
# =====================================================================

def _db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


@dataclass
class AICrewMember:
    employee_id: str
    name: str
    employee_type: str
    level: int
    neuralhub_task: str
    phase: str
    job_label: str
    job_output: str

    def to_dict(self) -> Dict:
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "employee_type": self.employee_type,
            "level": self.level,
            "neuralhub_task": self.neuralhub_task,
            "phase": self.phase,
            "job_label": self.job_label,
            "job_output": self.job_output,
        }


def sample_by_neuralhub_task(task: str, count: int = 2) -> List[AICrewMember]:
    """从 DB 随机抽取 neuralhub_task 匹配的 AI 员工"""
    c = _db()
    rows = c.execute('''
        SELECT employee_id, name, employee_type, level, neuralhub_task
        FROM mt_andromeda_employee_registry 
        WHERE enabled=1 AND (neuralhub_task=? OR neuralhub_task LIKE ?)
        ORDER BY RANDOM() LIMIT ?
    ''', (task, f'%{task}%', count)).fetchall()
    c.close()
    return [
        AICrewMember(
            employee_id=r[0], name=r[1], employee_type=r[2], level=r[3] or 5,
            neuralhub_task=r[4] or task,
            phase="", job_label="", job_output="",
        )
        for r in rows
    ]


def assemble_dynamic_crew(topic: str, team_size: int = 12,
                          preferred_phases: Optional[List[str]] = None,
                          excluded_tasks: Optional[List[str]] = None) -> List[AICrewMember]:
    """按 RoleAssignment 动态组装 AI 员工团队

    Args:
        topic: 视频主题 (用于信息收集阶段的话题上下文)
        team_size: 团队总人数 (建议 8-15, 最大 20)
        preferred_phases: 优先哪些阶段 (None = 全部)
        excluded_tasks: 排除哪些 neuralhub_task

    Returns:
        List[AICrewMember] 按 phase 排序的团队
    """
    preferred = set(preferred_phases or PHASE_ORDER)
    excluded = set(excluded_tasks or [])

    # 计算每个职能要抽多少人 (按 weight 比例)
    assignments = [a for a in ROLE_ASSIGNMENTS
                   if a.job_phase in preferred and a.neuralhub_task not in excluded]
    total_weight = sum(a.weight for a in assignments) or 1

    crew: List[AICrewMember] = []
    target_per_phase: Dict[str, int] = {}

    for asgn in assignments:
        slot = max(1, round(asgn.weight * team_size / total_weight))
        members = sample_by_neuralhub_task(asgn.neuralhub_task, count=slot)
        for m in members:
            m.phase = asgn.job_phase
            m.job_label = asgn.job_label
            m.job_output = asgn.job_output
        crew.extend(members)

    # 如果不够 team_size, 用 eigenflux_expert 补位 (带 context)
    if len(crew) < team_size:
        needed = team_size - len(crew)
        c = _db()
        fillers = c.execute('''
            SELECT employee_id, name, level, neuralhub_task 
            FROM mt_andromeda_employee_registry 
            WHERE enabled=1 AND employee_type='eigenflux_expert'
            AND neuralhub_task NOT IN (SELECT DISTINCT neuralhub_task FROM mt_andromeda_employee_registry WHERE employee_id IN (''' +
            ",".join(["?"]*len(crew)) + '''))
            ORDER BY RANDOM() LIMIT ?
        ''', [m.employee_id for m in crew] + [needed]).fetchall()
        c.close()
        for fid, fname, flv, ftask in fillers:
            crew.append(AICrewMember(
                employee_id=fid, name=fname, employee_type="eigenflux_expert",
                level=flv or 5, neuralhub_task=ftask or "eigenflux_chat",
                phase="copy", job_label="自由灵感员", job_output="给创意发散建议",
            ))

    # 如果超出 team_size, 截断
    if len(crew) > team_size:
        crew = crew[:team_size]

    # 按 phase 排序
    crew.sort(key=lambda m: PHASE_ORDER.index(m.phase) if m.phase in PHASE_ORDER else 999)
    return crew


# =====================================================================
# 3. 团队画像 + 协作模拟
# =====================================================================

def crew_brief(crew: List[AICrewMember], topic: str) -> str:
    """生成团队简报 (给用户看)"""
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"🚀 仙女座动态 AI 团队 | 话题: 「{topic}」 | {len(crew)} 人协作")
    lines.append(f"{'='*70}")

    for phase in PHASE_ORDER:
        phase_members = [m for m in crew if m.phase == phase]
        if not phase_members:
            continue
        phase_label = {
            "info": "📚 Phase 1 信息收集",
            "copy": "✍️ Phase 2 文案写作",
            "storyboard": "🎞️ Phase 3 分镜规划",
            "visual": "🎨 Phase 4 视觉设计",
            "compliance": "🛡️ Phase 5 合规审查",
            "edu": "🎓 Phase 6 教育适配",
            "publish": "📤 Phase 7 发布准备",
        }.get(phase, phase)
        lines.append(f"\n  {phase_label} ({len(phase_members)} 人)")
        for m in phase_members:
            lines.append(f"    💫 {m.name:20s} [Lv{m.level}] → {m.job_label} ({m.neuralhub_task[:30]})")

    lines.append(f"\n{'='*70}")
    lines.append(f"🔥 组合亮点:")
    phases_covered = {m.phase for m in crew}
    lines.append(f"  • 覆盖阶段: {len(phases_covered)}/{len(PHASE_ORDER)}")
    lines.append(f"  • 总人数: {len(crew)}")
    unique_tasks = {m.neuralhub_task for m in crew}
    lines.append(f"  • 不同职能: {len(unique_tasks)}")
    avg_level = sum(m.level for m in crew) / len(crew) if crew else 0
    lines.append(f"  • 平均等级: {avg_level:.1f}")
    lines.append(f"{'='*70}\n")
    return "\n".join(lines)


def simulate_crew_workflow(crew: List[AICrewMember], topic: str) -> Dict:
    """模拟 AI 团队协作全过程 (用本地 Ollama 驱动)

    返回一个 production_spec 风格的 Dict —— 包含每个阶段的产出.
    注意: 这是协作流程模拟, 真正执行由 galaxy_jimeng_pipeline 接手.
    """
    result = {
        "topic": topic,
        "crew_size": len(crew),
        "phases": {},
        "estimated_quality_score": 0,
    }

    # Phase 1: 信息收集
    info = [m for m in crew if m.phase == "info"]
    if info:
        result["phases"]["info"] = {
            "crew": [m.to_dict() for m in info],
            "task": f"围绕「{topic}」提取真实知识点, 每个知识点附数据/日期/来源",
            "estimated_output": f"预计产出 {len(info)*3} 条真实知识点",
        }

    # Phase 2: 文案写作
    copy = [m for m in crew if m.phase == "copy"]
    if copy:
        result["phases"]["copy"] = {
            "crew": [m.to_dict() for m in copy],
            "task": "6 段旁白 + hook + CTA, 每段 30-50 字, 口语化",
            "estimated_output": f"6 段旁白, 适合 TTS 朗读, 约 40-60 秒",
        }

    # Phase 3: 分镜规划
    sb = [m for m in crew if m.phase == "storyboard"]
    if sb:
        result["phases"]["storyboard"] = {
            "crew": [m.to_dict() for m in sb],
            "task": "6 镜头 content_type 分配 + 视觉描述 + 爆炸特效位置",
            "estimated_output": "title / timeline / fact_card / comparison / formula / cta 等 8 种",
        }

    # Phase 4: 视觉设计
    visual = [m for m in crew if m.phase == "visual"]
    if visual:
        result["phases"]["visual"] = {
            "crew": [m.to_dict() for m in visual],
            "task": "配色方案 + 爆炸 emoji + 视觉引导",
            "estimated_output": "每个镜头独立视觉方案, 渐变背景 + 半透明面板",
        }

    # Phase 5: 合规审查
    comp = [m for m in crew if m.phase == "compliance"]
    if comp:
        result["phases"]["compliance"] = {
            "crew": [m.to_dict() for m in comp],
            "task": "C1~C7 全链路合规 + DB 72 词动态词库 + 极限词替换",
            "estimated_output": "PASS / REVIEW / BLOCK 三档结果",
        }

    # Phase 6: 教育适配
    edu = [m for m in crew if m.phase == "edu"]
    if edu:
        result["phases"]["edu"] = {
            "crew": [m.to_dict() for m in edu],
            "task": "调整类比/难度/数据 适合目标受众",
            "estimated_output": "K12 / 高等 / 科普 三档适配",
        }

    # Phase 7: 发布准备
    pub = [m for m in crew if m.phase == "publish"]
    if pub:
        result["phases"]["publish"] = {
            "crew": [m.to_dict() for m in pub],
            "task": "多平台标题/tag/发布时间建议",
            "estimated_output": "抖音/B站/小红书 差异化 manifest",
        }

    # 综合质量分 (基于覆盖阶段数 × 人数 × 职能多样性)
    phases = list(result["phases"].keys())
    unique_tasks = {m.neuralhub_task for m in crew}
    result["estimated_quality_score"] = min(100,
        len(phases) * 12 + len(crew) * 2 + len(unique_tasks) * 3
    )

    return result


# =====================================================================
# 4. 把 crew 协作注入 production_spec → 渲染视频
# =====================================================================

def crew_to_production_spec(crew: List[AICrewMember], topic: str,
                            use_ollama: bool = True) -> Dict:
    """让 AI 团队协作产出完整 production_spec → 渲染视频

    流程:
      1. 把 crew 信息写入 composition_engine 的 generate_production_spec
      2. 调用 jimeng_pipeline.run_jimeng_pipeline
      3. 返回渲染结果
    """
    from engines.galaxy_composition_engine import generate_production_spec

    # 先让 composition_engine 生成基础 spec (知识密集型文案)
    spec = generate_production_spec(topic, use_ollama=use_ollama)

    # 把动态 crew 信息注入 meta
    spec.setdefault("meta", {})
    spec["meta"]["dynamic_crew"] = [m.to_dict() for m in crew]
    spec["meta"]["crew_size"] = len(crew)
    spec["meta"]["crew_assembly_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # 把 crew_brief 写到 script 里 (下游展示用)
    brief = crew_brief(crew, topic)
    spec.setdefault("script", {})["crew_brief"] = brief

    # 用 video_renderer 渲染
    from engines.galaxy_video_renderer import render_video, build_publishing_manifest
    from pathlib import Path

    out_dir = Path("/tmp/galaxy_video_out")
    video = render_video(spec, out_dir=out_dir)
    manifest = build_publishing_manifest(spec, video, out_dir)

    return {
        "spec": spec,
        "crew_size": len(crew),
        "video": video,
        "manifest": manifest,
        "brief": brief,
    }


# =====================================================================
# 5. CLI 入口
# =====================================================================

def _print_roster():
    """打印全部可组合职能 (ROLE_ASSIGNMENTS 清单)"""
    print("🏢 仙女座 AI 员工动态组合 — 职能总览")
    print(f"{'='*80}")
    for phase in PHASE_ORDER:
        asgns = [a for a in ROLE_ASSIGNMENTS if a.job_phase == phase]
        phase_label = {
            "info": "📚 Phase 1 信息收集",
            "copy": "✍️ Phase 2 文案写作",
            "storyboard": "🎞️ Phase 3 分镜规划",
            "visual": "🎨 Phase 4 视觉设计",
            "compliance": "🛡️ Phase 5 合规审查",
            "edu": "🎓 Phase 6 教育适配",
            "publish": "📤 Phase 7 发布准备",
        }.get(phase, phase)
        print(f"\n  {phase_label}")
        for a in asgns:
            print(f"    💫 {a.job_label:15s} neuralhub_task={a.neuralhub_task:35s} weight={a.weight}")

    # DB 汇总
    c = _db()
    total = c.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE enabled=1").fetchone()[0]
    print(f"\n  📊 AI 员工总数: {total:,}")
    task_counts = c.execute(f'''
        SELECT neuralhub_task, COUNT(*) FROM {TABLE} 
        WHERE enabled=1 AND neuralhub_task IN ({",".join("?"*len(ROLE_ASSIGNMENTS))})
        GROUP BY neuralhub_task ORDER BY COUNT(*) DESC
    ''', [a.neuralhub_task for a in ROLE_ASSIGNMENTS]).fetchall()
    c.close()
    print("\n  📋 可调度职能人数:")
    for t, cnt in task_counts:
        print(f"    [{cnt:>6,}] {t}")
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(description="仙女座 AI 员工动态组合引擎")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # roster
    sub.add_parser("roster", help="打印可组合职能清单")

    # assemble
    p_as = sub.add_parser("assemble", help="组装团队 + 渲染视频")
    p_as.add_argument("-t", "--topic", required=True, help="视频主题")
    p_as.add_argument("--team-size", type=int, default=12, help="团队人数 (8-15)")
    p_as.add_argument("--phase", action="append", help="优先阶段 (可重复)")
    p_as.add_argument("--render", action="store_true", default=True, help="组装后立即渲染")
    p_as.add_argument("--no-render", dest="render", action="store_false")

    # simulate
    p_sm = sub.add_parser("simulate", help="模拟团队协作全过程")
    p_sm.add_argument("-t", "--topic", required=True)
    p_sm.add_argument("--team-size", type=int, default=12)

    args = parser.parse_args()

    if args.cmd == "roster":
        _print_roster()
        return

    if args.cmd == "simulate":
        print(f"\n🎲 仙女座动态 AI 团队协作模拟\n   话题: {args.topic}\n   团队规模: {args.team_size} 人")
        crew = assemble_dynamic_crew(args.topic, team_size=args.team_size)
        print(crew_brief(crew, args.topic))
        sim = simulate_crew_workflow(crew, args.topic)
        print("\n📋 协作输出:")
        for phase, info in sim["phases"].items():
            print(f"\n  [{phase.upper()}] 任务: {info['task']}")
            print(f"           产出: {info['estimated_output']}")
            for m in info["crew"][:3]:
                print(f"           💫 {m['name']} → {m['job_label']}")
        print(f"\n  🏆 预计质量分: {sim['estimated_quality_score']}/100")
        return

    if args.cmd == "assemble":
        print(f"\n🚀 仙女座动态 AI 团队\n   话题: {args.topic}\n   目标规模: {args.team_size} 人")
        crew = assemble_dynamic_crew(args.topic, team_size=args.team_size,
                                     preferred_phases=args.phase)
        print(crew_brief(crew, args.topic))

        if not args.render:
            print("  ⏸️  仅组装, 不渲染 (--no-render)")
            return

        print("  🎬 让 AI 团队协作 + 渲染视频...\n")
        result = crew_to_production_spec(crew, args.topic)
        video = result["video"]
        print(f"\n✅ 完成!")
        print(f"   📁 视频: {video['video_path']}")
        print(f"   ⏱️ 时长: {video['duration_sec']:.1f}s")
        print(f"   💾 大小: {video['size_mb']}MB")
        print(f"   📄 Manifest: {result['manifest']}")

        # 打开视频
        import subprocess
        subprocess.run(["open", video["video_path"]], capture_output=True)


if __name__ == "__main__":
    main()
