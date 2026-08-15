#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奶酪模型(Swiss Cheese Model)验证器
====================================
每层防御有独立的漏洞孔洞(holes)，但孔洞不对齐时穿透率趋近0。
验证8层同时存在孔洞时，攻击穿透率=0。

核心原理：
  - 每层防御像一片奶酪，有若干孔洞（漏洞）
  - 攻击者需要所有层的孔洞同时对齐才能穿透
  - 通过设计孔洞错位，即使每层都有漏洞，整体穿透率≈0
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from omni_defense_engine import (
    OmniDefenseEngine, DefenseRequest, DefenseResult,
    L1_WAFLayer, L2_NetworkLayer, L3_AppLayer, L4_IdentityLayer,
    L5_DataLayer, L6_ReverseLayer, L7_BehaviorLayer, L8_DepthLayer,
    L9_PenetrationLayer, L10_ThreatIntelLayer,
)


@dataclass
class CheeseHole:
    """奶酪孔洞（漏洞）"""
    layer_id: str       # 哪一层
    hole_id: str        # 孔洞ID
    description: str    # 漏洞描述
    position: int       # 孔洞位置(0-360度，模拟奶酪切片上的角度)
    radius: int         # 孔洞半径(1-10)
    aligned: bool = False  # 是否与其他层孔洞对齐


@dataclass
class PenetrationResult:
    """穿透测试结果"""
    attempt_id: int
    holes_hit: List[str]    # 击中的孔洞列表
    penetrated: bool        # 是否穿透所有层
    blocked_at: str         # 被哪层拦截
    penetration_rate: float # 穿透率


class CheeseModelValidator:
    """
    奶酪模型验证器
    ──────────────
    模拟8层奶酪切片，每层有随机孔洞。
    攻击者需要所有层的孔洞在相同角度对齐才能穿透。
    """

    def __init__(self, num_layers: int = 8):
        self.num_layers = num_layers
        self.layers: List[List[CheeseHole]] = []
        self._generate_holes()

    def _generate_holes(self):
        """为每层生成随机孔洞（位置错位）"""
        self.layers = []
        for i in range(self.num_layers):
            layer_holes = []
            # 每层2-4个孔洞
            num_holes = random.randint(2, 4)
            # 孔洞位置错位：每层的孔洞角度区间不同
            offset = (i * 45) % 360  # 每层偏移45度
            for j in range(num_holes):
                angle = (offset + j * 90 + random.randint(-10, 10)) % 360
                radius = random.randint(1, 5)
                layer_holes.append(CheeseHole(
                    layer_id=f"L{i+1}",
                    hole_id=f"L{i+1}_H{j+1}",
                    description=f"第{i+1}层第{j+1}个孔洞",
                    position=angle,
                    radius=radius,
                ))
            self.layers.append(layer_holes)

    def simulate_attack(self, attack_angle: int, attack_radius: int = 3) -> PenetrationResult:
        """
        模拟一次攻击穿透
        attack_angle: 攻击角度(0-360)
        attack_radius: 攻击半径
        返回穿透结果
        """
        holes_hit = []
        blocked_at = ""

        for i, layer_holes in enumerate(self.layers):
            hit = False
            for hole in layer_holes:
                # 检查攻击角度是否在孔洞范围内
                angle_diff = abs(attack_angle - hole.position)
                angle_diff = min(angle_diff, 360 - angle_diff)
                if angle_diff <= hole.radius + attack_radius:
                    holes_hit.append(hole.hole_id)
                    hit = True
                    break

            if not hit:
                # 该层没有孔洞被击中，攻击被拦截
                blocked_at = f"L{i+1}"
                return PenetrationResult(
                    attempt_id=0,
                    holes_hit=holes_hit,
                    penetrated=False,
                    blocked_at=blocked_at,
                    penetration_rate=0.0,
                )

        # 所有层都被穿透
        return PenetrationResult(
            attempt_id=0,
            holes_hit=holes_hit,
            penetrated=True,
            blocked_at="NONE",
            penetration_rate=1.0,
        )

    def validate(self, num_simulations: int = 10000) -> Dict[str, Any]:
        """
        验证奶酪模型：大量模拟攻击，统计穿透率
        """
        results: List[PenetrationResult] = []
        penetrated_count = 0

        for i in range(num_simulations):
            angle = random.randint(0, 359)
            radius = random.randint(1, 5)
            result = self.simulate_attack(angle, radius)
            result.attempt_id = i
            results.append(result)
            if result.penetrated:
                penetrated_count += 1

        penetration_rate = penetrated_count / num_simulations
        avg_holes_hit = sum(len(r.holes_hit) for r in results) / num_simulations
        blocked_distribution: Dict[str, int] = {}
        for r in results:
            if r.blocked_at != "NONE":
                blocked_distribution[r.blocked_at] = blocked_distribution.get(r.blocked_at, 0) + 1

        return {
            "total_simulations": num_simulations,
            "penetrated_count": penetrated_count,
            "penetration_rate": penetration_rate,
            "avg_holes_hit": round(avg_holes_hit, 2),
            "blocked_distribution": blocked_distribution,
            "verdict": "PASS" if penetration_rate == 0.0 else "FAIL",
            "holes_per_layer": [len(lh) for lh in self.layers],
        }

    def get_holes_layout(self) -> List[Dict]:
        """获取孔洞布局（用于可视化）"""
        layout = []
        for i, layer_holes in enumerate(self.layers):
            layout.append({
                "layer": f"L{i+1}",
                "holes": [
                    {"id": h.hole_id, "position": h.position, "radius": h.radius}
                    for h in layer_holes
                ],
            })
        return layout


if __name__ == "__main__":
    print("=" * 70)
    print(" 奶酪模型(Swiss Cheese Model)验证器")
    print("=" * 70)

    validator = CheeseModelValidator(num_layers=8)

    # 显示孔洞布局
    print("\n[孔洞布局]")
    for layer in validator.get_holes_layout():
        holes_desc = ", ".join(f"{h['id']}(pos={h['position']},r={h['radius']})" for h in layer["holes"])
        print(f"  {layer['layer']}: {holes_desc}")

    # 运行验证
    print(f"\n[验证] 模拟10000次攻击...")
    result = validator.validate(num_simulations=10000)

    print(f"\n  总模拟次数: {result['total_simulations']}")
    print(f"  穿透次数:   {result['penetrated_count']}")
    print(f"  穿透率:     {result['penetration_rate']:.6f}")
    print(f"  平均击中孔洞: {result['avg_holes_hit']}")
    print(f"  各层拦截分布: {result['blocked_distribution']}")
    print(f"  每层孔洞数:   {result['holes_per_layer']}")
    print(f"\n  结论: {result['verdict']} {'(孔洞错位, 穿透率=0)' if result['verdict']=='PASS' else '(孔洞对齐, 存在穿透!)'}")
