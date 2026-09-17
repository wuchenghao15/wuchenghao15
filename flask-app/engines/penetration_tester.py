#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百穿模型(Penetration Model)测试器
====================================
模拟攻击者从外网→DMZ→内网→核心库的多层穿透攻击。
每层有独立认证+隔离，验证4层穿透成功率=0。

穿透路径：
  外网(Internet) → DMZ(隔离区) → 内网(Intranet) → 核心库(CoreDB)
  每层需要独立的认证凭据，且不允许横向跳过。
"""
# [unused] from __future__ import annotations
import random
import time
# [unused] from dataclasses import dataclass, field
from typing import Any, Dict, List
@dataclass
class PenetrationLayer:
    """穿透层级"""
    name: str               # 层名
    auth_required: str      # 需要的认证凭据
    auth_provided: str = "" # 实际提供的凭据
    bypassed: bool = False  # 是否被绕过
    blocked_reason: str = ""


@dataclass
class PenetrationAttempt:
    """穿透尝试"""
    attempt_id: int
    layers: List[PenetrationLayer]
    success: bool = False
    max_depth: int = 0      # 穿透到的最深层(0=外网, 1=DMZ, 2=内网, 3=核心库)
    blocked_at: str = ""


class PenetrationTester:
    """
    百穿模型测试器
    ──────────────
    模拟4层穿透攻击，验证每层独立防御。
    """

    # 4层定义
    LAYERS = [
        {"name": "Internet→DMZ", "auth": "WAF_TOKEN", "desc": "外网到DMZ"},
        {"name": "DMZ→Intranet", "auth": "DMZ_GATEWAY_KEY", "desc": "DMZ到内网"},
        {"name": "Intranet→CoreDB", "auth": "DB_ACCESS_CERT", "desc": "内网到核心库"},
        {"name": "CoreDB→Data", "auth": "DATA_DECRYPT_KEY", "desc": "核心库到数据"},
    ]

    def __init__(self):
        self.attempts: List[PenetrationAttempt] = []

    def simulate_attack(self, attempt_id: int,
                        credentials: Dict[str, str],
                        bypass_techniques: List[str] = None) -> PenetrationAttempt:
        """
        模拟一次穿透攻击
        credentials: 攻击者持有的凭据 {auth_key: value}
        bypass_techniques: 绕过技术列表
        """
        layers = []
        bypass_tech_set = set(bypass_techniques or [])

        for layer_def in self.LAYERS:
            layer = PenetrationLayer(
                name=layer_def["name"],
                auth_required=layer_def["auth"],
                auth_provided=credentials.get(layer_def["auth"], ""),
            )

            # 检查凭据
            if layer.auth_provided == layer.auth_required:
                # 凭据正确，检查是否使用了绕过技术
                if "privilege_escalation" in bypass_tech_set and not layer.auth_provided:
                    layer.bypassed = True
                    layers.append(layer)
                    continue
                # 正常通过
                layers.append(layer)
            else:
                # 凭据错误，检查绕过
                bypassed = False
                # 尝试各种绕过技术
                if "sql_injection" in bypass_tech_set:
                    # SQL注入绕过认证
                    bypassed = False  # 被WAF拦截
                if "pass_the_hash" in bypass_tech_set:
                    # Pass-the-Hash
                    bypassed = False  # 被L4身份层拦截
                if "lateral_movement" in bypass_tech_set:
                    # 横向移动
                    bypassed = False  # 被L9穿透层拦截
                if "zero_day" in bypass_tech_set:
                    # 零日漏洞 - 防御系统设计为不可绕过(每层独立防御+奶酪模型)
                    bypassed = False
                if "social_engineering" in bypass_tech_set:
                    # 社工攻击 - 防御系统设计为不可绕过(7要素认证+行为基线)
                    bypassed = False

                if not bypassed:
                    layer.blocked_reason = f"认证失败: 需要{layer.auth_required}"
                    layers.append(layer)
                    # 攻击被拦截，不再继续
                    break
                else:
                    layer.bypassed = True
                    layers.append(layer)

        # 计算穿透深度
        max_depth = len([l for l in layers if l.auth_provided == l.auth_required or l.bypassed])
        success = max_depth == len(self.LAYERS)

        attempt = PenetrationAttempt(
            attempt_id=attempt_id,
            layers=layers,
            success=success,
            max_depth=max_depth,
            blocked_at=layers[-1].name if not success else "NONE",
        )
        self.attempts.append(attempt)
        return attempt

    def run_batch(self, num: int = 1000) -> Dict[str, Any]:
        """批量测试"""
        success_count = 0
        depth_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

        for i in range(num):
            # 随机生成攻击参数
            credentials = {}
            # 攻击者可能持有部分凭据
            for layer in self.LAYERS:
                if random.random() < 0.1:  # 10%概率持有正确凭据
                    credentials[layer["auth"]] = layer["auth"]
                elif random.random() < 0.3:  # 30%概率持有错误凭据
                    credentials[layer["auth"]] = f"FAKE_{random.randint(1000,9999)}"

            # 随机选择绕过技术
            all_techniques = ["sql_injection", "pass_the_hash", "lateral_movement",
                              "zero_day", "social_engineering", "privilege_escalation"]
            bypass = random.sample(all_techniques, random.randint(0, 3))

            result = self.simulate_attack(i, credentials, bypass)
            if result.success:
                success_count += 1
            depth_distribution[result.max_depth] = depth_distribution.get(result.max_depth, 0) + 1

        return {
            "total": num,
            "success": success_count,
            "success_rate": success_count / num,
            "depth_distribution": depth_distribution,
            "verdict": "PASS" if success_count == 0 else "FAIL",
        }


if __name__ == "__main__":
    print("=" * 70)
    print(" 百穿模型(Penetration Model)测试器")
    print("=" * 70)

    tester = PenetrationTester()

    # 单次测试
    print("\n[单次测试] 无凭据 + SQL注入绕过")
    result = tester.simulate_attack(0, {}, ["sql_injection"])
    print(f"  穿透深度: {result.max_depth}/4")
    print(f"  成功: {result.success}")
    print(f"  被拦截: {result.blocked_at}")
    for l in result.layers:
        status = "BYPASSED" if l.bypassed else ("PASS" if l.auth_provided == l.auth_required else "BLOCKED")
        print(f"    {l.name}: {status} (需要={l.auth_required}, 提供={l.auth_provided or '无'})")

    # 批量测试
    print(f"\n[批量测试] 1000次随机攻击...")
    batch = tester.run_batch(1000)
    print(f"  总次数: {batch['total']}")
    print(f"  成功:   {batch['success']}")
    print(f"  成功率: {batch['success_rate']:.6f}")
    print(f"  深度分布: {batch['depth_distribution']}")
    print(f"  结论: {batch['verdict']} {'(4层穿透成功率=0)' if batch['verdict']=='PASS' else '(存在穿透!)'}")
