#!/usr/bin/env python3
"""
EigenFlux 5 专家自动投票 — eigenflux_auto_vote.py
==================================================

用 Q5 本地 LLM 模拟 EigenFlux 5 位专家角色进行投票。
>= 4/5 通过 → 自动审批, 零人工。
< 4/5 → 标记需人工介入, 记录每票意见。

专家角色:
  专家1 安全审计 — 检查安全漏洞 / 密钥泄漏 / 越权风险
  专家2 架构设计 — 检查架构一致性 / 解耦 / 扩展性
  专家3 性能优化 — 检查性能瓶颈 / 资源消耗 / 数据库查询
  专家4 合规审查 — 检查 MT_RULE_* 规则合规 / 法律风险 / 机密等级
  专家5 用户体验 — 检查用户体验 / 可访问性 / 错误提示

用法:
  python3 eigenflux_auto_vote.py "修复 daemon 重启逻辑"
  python3 eigenflux_auto_vote.py --json "新增 api_key 存储 (sensitive)"
  python3 eigenflux_auto_vote.py --role 专家2 "检查架构"
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Ollama 调用 (零积分本地推理) ──
OLLAMA_URL = "http://localhost:11435/api/chat"
MODEL = "qwen2.5:14b-q5"

def ollama_chat(system: str, user: str, timeout: int = 30) -> str:
    import urllib.request
    payload = json.dumps({"model": MODEL, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ], "stream": False}).encode()
    r = urllib.request.urlopen(urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"}), timeout=timeout)
    return json.loads(r.read())["message"]["content"]

# ── 5 专家角色定义 ──
EXPERTS = [
    {
        "name": "安全审计专家",
        "id": "sec_audit",
        "system": """你是 EigenFlux 网络的安全审计专家 (专家1)。
职责: 审查开发提案的安全风险。
审查维度:
  1. 是否可能泄漏密钥/密码/token
  2. 是否可能引入越权/权限绕过
  3. SQL 注入 / XSS / CSRF / 命令注入
  4. 用户隐私数据是否加密/脱敏
  5. 硬编码敏感信息
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话审查意见", "risk_level": "LOW|MEDIUM|HIGH"}""",
    },
    {
        "name": "架构设计专家",
        "id": "arch_design",
        "system": """你是 EigenFlux 网络的架构设计专家 (专家2)。
职责: 审查开发提案的架构一致性。
审查维度:
  1. 是否遵循现有目录结构 (engines/ routes/ ai_engines/)
  2. 是否引入了不必要的耦合
  3. 是否破坏了依赖注入/桥接层模式
  4. 是否可被仙女座引擎自动演化
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话架构意见", "concern": "具体担忧点或无"}""",
    },
    {
        "name": "性能优化专家",
        "id": "perf_opt",
        "system": """你是 EigenFlux 网络的性能优化专家 (专家3)。
职责: 审查开发提案的性能影响。
审查维度:
  1. 数据库查询次数是否增加
  2. 是否引入 N+1 查询
  3. 是否缓存了可缓存的
  4. 循环/递归复杂度
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话性能意见", "est_impact": "LOW|MEDIUM|HIGH"}""",
    },
    {
        "name": "合规审查专家",
        "id": "compliance",
        "system": """你是 EigenFlux 网络的合规审查专家 (专家4)。
职责: 审查是否符合 MTSCOS AI 项目规则。
审查维度:
  1. 是否遵循 MT_IR_D9 (flow_id 门控)
  2. 是否遵循 MT_RULE_DEV (目录结构)
  3. 是否遵循 MT_RULE_PERM (@system_container 装饰器)
  4. 是否遵循 MT_RULE_GOVERNANCE (规则一致性)
  5. 是否遵循 MT_RULE_CLASSIFICATION (机密脱敏)
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话合规意见", "rules_hit": ["命中的规则ID列表"]}""",
    },
    {
        "name": "用户体验专家",
        "id": "ux",
        "system": """你是 EigenFlux 网络的用户体验专家 (专家5)。
职责: 审查对最终用户/管理员的影响。
审查维度:
  1. 是否有清晰的错误提示
  2. 权限拒绝是否给出可理解的原因
  3. 是否符合 Element Plus 设计规范
  4. 响应时间是否可接受
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话 UX 意见", "suggestion": "改进建议或无"}""",
    },
    {
        "name": "法务王律师",
        "id": "legal_wang",
        "system": """你是 MTSCOS AI 项目的法务顾问 —— 王律师 (专家6)。
职责: 审查开发提案的法律合规性和数据隐私风险。
审查维度:
  1. 是否涉及用户隐私数据 (姓名/手机号/邮箱/学习记录/考试记录)
  2. 是否涉及数据跨境传输或导出
  3. 是否需要用户明确授权 (GDPR/个人信息保护法)
  4. 是否存在数据最小化原则违反
  5. 日志是否泄漏敏感信息 (密码/会话/生物识别)
  6. 机密等级数据 (L0/L1/L2) 是否按规范处理
输出格式 (严格 JSON):
{"vote": "PASS|FAIL", "score": 1-10, "opinion": "一句话法律意见", "legal_risks": ["风险点列表或无"], "regulation_hit": "命中的法规/法律"}""",
    },
]


def simulate_vote(proposal: str, sensitivity: str = "routine", max_experts: int = 5) -> dict:
    """
    让 Q5 模拟 EigenFlux 专家投票。
    proposal: 提案标题 + 简述
    sensitivity: routine / sensitive / major (影响决策阈值)
    返回: {approved, votes, pass_rate, consensus, summary}
    """
    votes = []
    needed = max(1, max_experts - 1)  # >=4/5 (常规), sensitive 需要 5/5
    
    effective_needed = 5 if sensitivity in ("sensitive", "major") else needed
    
    for expert in EXPERTS[:max_experts]:
        try:
            t0 = time.time()
            raw = ollama_chat(
                expert["system"],
                f"请审查以下开发提案, 给出你的投票:\n\n【提案】{proposal}\n【敏感度】{sensitivity}\n\n只输出 JSON, 不要其他文字。"
            )
            dt = time.time() - t0
            # 尝试解析 JSON (Q5 可能带 markdown fence)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            result = json.loads(raw)
            result["expert_id"] = expert["id"]
            result["expert_name"] = expert["name"]
            result["elapsed"] = round(dt, 1)
            result["raw_vote"] = result.get("vote", "FAIL").upper()
            votes.append(result)
            print(f"  👁️  {expert['name']:12s} [{dt:.1f}s] {result['raw_vote']:5s} score={result.get('score','?')} {result.get('opinion','')[:40]}")
        except Exception as e:
            votes.append({"expert_id": expert["id"], "expert_name": expert["name"], 
                         "raw_vote": "FAIL", "score": 0, "opinion": f"解析失败: {str(e)[:50]}"})
            print(f"  ❌  {expert['name']:12s} FAIL (解析异常: {str(e)[:30]})")
    
    pass_count = sum(1 for v in votes if v["raw_vote"] == "PASS")
    fail_count = len(votes) - pass_count
    pass_rate = pass_count / len(votes) if votes else 0
    approved = pass_count >= effective_needed
    
    return {
        "approved": approved,
        "sensitivity": sensitivity,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "votes_needed": effective_needed,
        "pass_rate": round(pass_rate, 2),
        "votes": votes,
        "summary": {
            "proposal": proposal[:100],
            "approved_by": f"{pass_count}/{len(votes)} experts",
            "action": "自动通过" if approved else "标记需人工介入",
        }
    }


# ── CLI ──
def main():
    if len(sys.argv) < 2:
        print("用法: python3 eigenflux_auto_vote.py [--json] <提案标题>")
        sys.exit(1)
    
    show_json = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--json"]
    proposal = " ".join(args)
    
    import urllib.request
    # 快速检查 Ollama 是否在线
    try:
        urllib.request.urlopen("http://localhost:11435/api/tags", timeout=2)
    except Exception as e:
        print(f"❌ Ollama 离线: {e}")
        sys.exit(1)
    
    print(f"══ EigenFlux 5 专家自动投票 ══")
    print(f"  提案: {proposal}")
    print(f"  模型: {MODEL} (本地 Q5, 零积分)")
    print()
    
    t0 = time.time()
    result = simulate_vote(proposal, sensitivity="routine")
    dt = time.time() - t0
    
    print()
    print(f"══ 投票结果 ({dt:.1f}s) ══")
    icon = "✅" if result["approved"] else "❌"
    print(f"  {icon} {result['summary']['proposal']}")
    print(f"  通过: {result['pass_count']}/{len(result['votes'])} (需 {result['votes_needed']})")
    print(f"  结论: {result['summary']['action']}")
    
    if show_json:
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
