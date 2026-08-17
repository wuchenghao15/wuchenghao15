#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学问题生成与解题引擎
智能生成数学题目、自动解题、提供多种解法
"""

import os
import sys
import json
import random
import math
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logging import logger
from app.models.math_models import MathProblem, MATH_CATEGORIES


class MathProblemGenerator:
    """数学问题生成引擎"""

    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

        self._init_patterns()
        logger.info("[数学问题生成引擎] 初始化完成")

    def _init_patterns(self):
        """初始化题目模板"""
        self.algebra_patterns = {
            'linear_eq': [
                {
                    'template': '解方程：{a}x + {b} = {c}',
                    'params': {'a': [2, 3, 4, 5, -2, -3], 'b': [5, 7, 9, 11, -5, -8], 'c': [15, 20, 25, 30, 10]},
                    'solve': lambda a, b, c: f'x = {round((c - b) / a, 2)}'
                },
                {
                    'template': '已知 {a}x + {b} = {c}，求x的值',
                    'params': {'a': [2, 3, 5, -2, -4], 'b': [6, 8, 10, -6, -10], 'c': [20, 24, 30, 16, 12]},
                    'solve': lambda a, b, c: f'x = {round((c - b) / a, 2)}'
                }
            ],
            'quadratic_eq': [
                {
                    'template': '解方程：x² - {sum}x + {product} = 0',
                    'params': {'sum': [5, 6, 7, 8, 9, 10], 'product': [6, 8, 12, 15, 20, 21]},
                    'solve': lambda s, p: f'x = {round((s - math.sqrt(s*s - 4*p)) / 2, 2)} 或 x = {round((s + math.sqrt(s*s - 4*p)) / 2, 2)}'
                },
                {
                    'template': '解方程：{a}x² + {b}x + {c} = 0 (a≠0)',
                    'params': {'a': [1, 2, 3], 'b': [-5, -7, -8], 'c': [6, 10, 12]},
                    'solve': lambda a, b, c: f'x = {round((-b - math.sqrt(b*b - 4*a*c)) / (2*a), 2)} 或 x = {round((-b + math.sqrt(b*b - 4*a*c)) / (2*a), 2)}'
                }
            ],
            'arithmetic_seq': [
                {
                    'template': '等差数列首项为{a1}，公差为{d}，求第{n}项',
                    'params': {'a1': [2, 3, 5, -1, 10], 'd': [2, 3, 4, -1, 5], 'n': [10, 15, 20, 25, 30]},
                    'solve': lambda a1, d, n: str(a1 + (n - 1) * d)
                },
                {
                    'template': '等差数列首项{a1}，公差{d}，求前{n}项和',
                    'params': {'a1': [1, 2, 3, 5], 'd': [1, 2, 3, 4], 'n': [10, 15, 20]},
                    'solve': lambda a1, d, n: str(int(n * a1 + n * (n - 1) * d / 2))
                }
            ],
            'inequality': [
                {
                    'template': '解不等式：{a}x + {b} > {c}',
                    'params': {'a': [2, 3, 5, -2, -3], 'b': [4, 6, 8, -5, -7], 'c': [10, 15, 20, 5, 12]},
                    'solve': lambda a, b, c: f'x {">" if a > 0 else "<"} {round((c - b) / a, 2)}'
                }
            ]
        }

        self.geometry_patterns = {
            'right_triangle': [
                {
                    'template': '直角三角形两条直角边分别为{a}和{b}，求斜边长',
                    'params': {'a': [3, 5, 6, 8, 9, 12], 'b': [4, 12, 8, 15, 12, 16]},
                    'solve': lambda a, b: str(int(math.sqrt(a*a + b*b))) if math.sqrt(a*a + b*b).is_integer() else f'√{a*a + b*b}'
                },
                {
                    'template': '直角三角形斜边为{c}，一条直角边为{a}，求另一条直角边',
                    'params': {'c': [5, 13, 10, 25, 17], 'a': [3, 5, 6, 7, 8]},
                    'solve': lambda c, a: str(int(math.sqrt(c*c - a*a))) if math.sqrt(c*c - a*a).is_integer() else f'√{c*c - a*a}'
                }
            ],
            'triangle_area': [
                {
                    'template': '三角形底边长为{a}，高为{h}，求面积',
                    'params': {'a': [5, 8, 10, 12, 15], 'h': [4, 6, 8, 10, 12]},
                    'solve': lambda a, h: str(int(a * h / 2))
                }
            ],
            'circle': [
                {
                    'template': '圆的半径为{r}，求面积（π取3.14）',
                    'params': {'r': [3, 5, 7, 10, 12]},
                    'solve': lambda r: str(round(3.14 * r * r, 2))
                },
                {
                    'template': '圆的直径为{d}，求周长（π取3.14）',
                    'params': {'d': [6, 10, 14, 20, 8]},
                    'solve': lambda d: str(round(3.14 * d, 2))
                }
            ],
            'rectangle': [
                {
                    'template': '长方形长为{a}，宽为{b}，求周长',
                    'params': {'a': [5, 8, 10, 12, 15], 'b': [3, 6, 7, 8, 10]},
                    'solve': lambda a, b: str(2 * (a + b))
                },
                {
                    'template': '长方形长为{a}，宽为{b}，求面积',
                    'params': {'a': [5, 8, 10, 12, 15], 'b': [3, 6, 7, 8, 10]},
                    'solve': lambda a, b: str(a * b)
                }
            ]
        }

        self.probability_patterns = {
            'basic_prob': [
                {
                    'template': '从{n}个红球和{m}个白球中随机取一个，取到红球的概率是多少？',
                    'params': {'n': [3, 5, 8, 10], 'm': [2, 4, 6, 5]},
                    'solve': lambda n, m: f'{n}/{n+m} = {round(n/(n+m), 3)}'
                },
                {
                    'template': '抛一枚均匀硬币{n}次，全是正面的概率是多少？',
                    'params': {'n': [2, 3, 4, 5]},
                    'solve': lambda n: f'1/{2**n} = {round(1/2**n, 4)}'
                }
            ],
            'permutation': [
                {
                    'template': '从{n}个不同元素中任取{m}个的排列数是多少？',
                    'params': {'n': [5, 6, 7, 8, 10], 'm': [2, 3, 4]},
                    'solve': lambda n, m: str(int(math.factorial(n) / math.factorial(n - m)))
                }
            ],
            'combination': [
                {
                    'template': '从{n}个不同元素中任取{m}个的组合数是多少？',
                    'params': {'n': [5, 6, 7, 8, 10], 'm': [2, 3, 4]},
                    'solve': lambda n, m: str(int(math.factorial(n) / (math.factorial(m) * math.factorial(n - m))))
                }
            ]
        }

        self.all_patterns = {
            'algebra': self.algebra_patterns,
            'geometry': self.geometry_patterns,
            'probability': self.probability_patterns
        }

    def generate_problem(self, category: str = 'algebra', difficulty: int = 1,
                          problem_type: str = 'calculation') -> Optional[Dict]:
        """生成一道数学题"""
        try:
            patterns = self.all_patterns.get(category, {})
            if not patterns:
                return None

            pattern_types = list(patterns.keys())
            pattern_type = random.choice(pattern_types)
            pattern_list = patterns[pattern_type]
            pattern = random.choice(pattern_list)

            params = {}
            for key, values in pattern['params'].items():
                params[key] = random.choice(values)

            content = pattern['template'].format(**params)

            try:
                answer = pattern['solve'](**params)
            except Exception:
                return None

            problem = MathProblem(
                id=f"mp_gen_{uuid4().hex[:10]}",
                content=content,
                problem_type=problem_type,
                category=category,
                subcategory=pattern_type,
                difficulty=difficulty,
                correct_answer=str(answer),
                answer_explanation=self._generate_explanation(pattern_type, params, answer),
                related_formulas=self._get_related_formulas(pattern_type),
                hints=self._generate_hints(pattern_type, params),
                solution_steps=self._generate_steps(pattern_type, params, answer),
                points=float(difficulty),
                estimated_time=difficulty * 3,
                source='ai_generated',
                tags=[category, pattern_type, f'难度{difficulty}']
            )

            return problem.to_dict()
        except Exception as e:
            logger.error(f"[数学问题生成引擎] 生成题目失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def generate_problems(self, count: int = 10, category: str = 'algebra',
                          difficulty: int = 1) -> List[Dict]:
        """批量生成数学题"""
        problems = []
        attempts = 0
        max_attempts = count * 5

        while len(problems) < count and attempts < max_attempts:
            problem = self.generate_problem(category, difficulty)
            if problem:
                problems.append(problem)
            attempts += 1

        logger.info(f"[数学问题生成引擎] 生成 {len(problems)} 道题目")
        return problems

    def _generate_explanation(self, pattern_type: str, params: Dict, answer: str) -> str:
        """生成答案解析"""
        explanations = {
            'linear_eq': f"移项得 {params.get('a')}x = {params.get('c')} - {params.get('b')}，计算得 x = {answer}",
            'quadratic_eq': f"利用求根公式或因式分解求解，解得 {answer}",
            'arithmetic_seq': f"利用等差数列公式计算，结果为 {answer}",
            'inequality': f"移项求解不等式，注意不等号方向，解得 {answer}",
            'right_triangle': f"由勾股定理 a² + b² = c² 计算得 {answer}",
            'triangle_area': f"三角形面积 = 底 × 高 ÷ 2 = {answer}",
            'circle': f"利用圆的面积/周长公式计算，结果为 {answer}",
            'rectangle': f"长方形周长/面积公式计算，结果为 {answer}",
            'basic_prob': f"根据古典概型，P(A) = m/n = {answer}",
            'permutation': f"排列数 A(n,m) = n!/(n-m)! = {answer}",
            'combination': f"组合数 C(n,m) = n!/(m!(n-m)!) = {answer}"
        }
        return explanations.get(pattern_type, f"经过计算，答案为 {answer}")

    def _get_related_formulas(self, pattern_type: str) -> List[str]:
        """获取相关公式"""
        formulas = {
            'linear_eq': ['ax + b = 0', 'x = -b/a'],
            'quadratic_eq': ['ax² + bx + c = 0', 'x = (-b ± √(b²-4ac))/(2a)', 'Δ = b² - 4ac'],
            'arithmetic_seq': ['an = a1 + (n-1)d', 'Sn = n(a1+an)/2'],
            'inequality': ['不等式基本性质', '同乘负数不等号反向'],
            'right_triangle': ['a² + b² = c²', '勾股定理'],
            'triangle_area': ['S = ½ah'],
            'circle': ['S = πr²', 'C = 2πr', 'C = πd'],
            'rectangle': ['C = 2(a+b)', 'S = ab'],
            'basic_prob': ['P(A) = m/n', '古典概型'],
            'permutation': ['A(n,m) = n!/(n-m)!'],
            'combination': ['C(n,m) = n!/(m!(n-m)!)']
        }
        return formulas.get(pattern_type, [])

    def _generate_hints(self, pattern_type: str, params: Dict) -> List[str]:
        """生成提示"""
        hints_map = {
            'linear_eq': ['这是一个一元一次方程', '先移项，把含x的项放一边', '然后两边同除以系数'],
            'quadratic_eq': ['这是一个一元二次方程', '试试因式分解', '或者用求根公式', '判别式 Δ = b² - 4ac'],
            'arithmetic_seq': ['回忆等差数列通项公式', 'an = a1 + (n-1)d'],
            'right_triangle': ['回忆勾股定理', '斜边的平方等于两直角边的平方和'],
            'circle': ['回忆圆的相关公式', '面积 S = πr²，周长 C = 2πr'],
            'basic_prob': ['古典概型：P(A) = 有利情况数/总情况数', '先算总情况数，再算有利情况数'],
            'permutation': ['排列是有顺序的', 'A(n,m) = n×(n-1)×...×(n-m+1)'],
            'combination': ['组合是没有顺序的', 'C(n,m) = A(n,m) / m!']
        }
        return hints_map.get(pattern_type, ['仔细分析题目类型', '回忆相关公式和定理'])

    def _generate_steps(self, pattern_type: str, params: Dict, answer: str) -> List[Dict]:
        """生成解题步骤"""
        steps_map = {
            'linear_eq': [
                {'step': 1, 'description': '分析方程类型', 'formula': f"一元一次方程: {params.get('a')}x + {params.get('b')} = {params.get('c')}"},
                {'step': 2, 'description': '移项', 'formula': f"{params.get('a')}x = {params.get('c')} - {params.get('b')}"},
                {'step': 3, 'description': '计算右边', 'formula': f"{params.get('a')}x = {params.get('c') - params.get('b')}"},
                {'step': 4, 'description': '两边同除以系数', 'formula': f"x = {answer}"}
            ],
            'quadratic_eq': [
                {'step': 1, 'description': '分析方程类型', 'formula': '一元二次方程'},
                {'step': 2, 'description': '计算判别式', 'formula': 'Δ = b² - 4ac'},
                {'step': 3, 'description': '应用求根公式', 'formula': 'x = (-b ± √Δ) / 2a'},
                {'step': 4, 'description': '得到答案', 'formula': f'x = {answer}'}
            ],
            'right_triangle': [
                {'step': 1, 'description': '应用勾股定理', 'formula': 'a² + b² = c²'},
                {'step': 2, 'description': '代入数值计算', 'formula': f'c² = {params.get("a")}² + {params.get("b")}²'},
                {'step': 3, 'description': '求解', 'formula': f'c = {answer}'}
            ],
            'circle': [
                {'step': 1, 'description': '确定使用的公式', 'formula': 'S = πr² / C = 2πr'},
                {'step': 2, 'description': '代入数值', 'formula': f'r = {params.get("r", params.get("d"))}'},
                {'step': 3, 'description': '计算结果', 'formula': f'结果 = {answer}'}
            ],
            'basic_prob': [
                {'step': 1, 'description': '计算总情况数', 'formula': 'n = 总数'},
                {'step': 2, 'description': '计算有利情况数', 'formula': 'm = 有利数'},
                {'step': 3, 'description': '计算概率', 'formula': f'P(A) = m/n = {answer}'}
            ]
        }
        return steps_map.get(pattern_type, [
            {'step': 1, 'description': '分析题目', 'formula': ''},
            {'step': 2, 'description': '应用公式', 'formula': ''},
            {'step': 3, 'description': '计算结果', 'formula': f'答案 = {answer}'}
        ])


class MathSolver:
    """数学解题引擎"""

    def __init__(self):
        logger.info("[数学解题引擎] 初始化完成")

    def solve(self, problem: Dict) -> Dict:
        """解题主函数"""
        try:
            content = problem.get('content', '')
            category = problem.get('category', 'algebra')
            problem_type = problem.get('problem_type', 'calculation')

            if not content:
                return {'success': False, 'error': '题目内容为空'}

            result = self._analyze_and_solve(content, category, problem_type)
            return {
                'success': True,
                'problem': content,
                'answer': result.get('answer', ''),
                'steps': result.get('steps', []),
                'method': result.get('method', ''),
                'explanation': result.get('explanation', ''),
                'related_concepts': result.get('related_concepts', []),
                'related_formulas': result.get('related_formulas', [])
            }
        except Exception as e:
            logger.error(f"[数学解题引擎] 解题失败: {e}")
            return {'success': False, 'error': str(e)}

    def _analyze_and_solve(self, content: str, category: str, problem_type: str) -> Dict:
        """分析题目并求解"""
        if category == 'algebra':
            return self._solve_algebra(content)
        elif category == 'geometry':
            return self._solve_geometry(content)
        elif category == 'probability':
            return self._solve_probability(content)
        else:
            return self._solve_generic(content)

    def _solve_algebra(self, content: str) -> Dict:
        """解代数题"""
        if 'x²' in content or '二次方程' in content:
            return self._solve_quadratic(content)
        elif 'x' in content and ('=' in content) and ('解' in content or '求' in content or '方程' in content):
            return self._solve_linear(content)
        elif '数列' in content or '等差' in content:
            return self._solve_sequence(content)
        else:
            return self._solve_generic(content)

    def _solve_linear(self, content: str) -> Dict:
        """解一元一次方程"""
        try:
            nums = re.findall(r'-?\d+', content)
            if len(nums) >= 3:
                a = int(nums[0])
                b = int(nums[1])
                c = int(nums[2])
                if a == 0:
                    return {'answer': '无解', 'steps': [], 'method': '公式法'}
                x = (c - b) / a
                return {
                    'answer': f'x = {round(x, 2)}',
                    'steps': [
                        {'step': 1, 'description': '移项', 'formula': f'{a}x = {c} - {b}'},
                        {'step': 2, 'description': '计算', 'formula': f'{a}x = {c - b}'},
                        {'step': 3, 'description': '两边除以{a}', 'formula': f'x = {round(x, 2)}'}
                    ],
                    'method': '公式法',
                    'explanation': f'一元一次方程 ax + b = c，解得 x = (c-b)/a = {round(x, 2)}',
                    'related_formulas': ['ax + b = 0', 'x = -b/a'],
                    'related_concepts': ['一元一次方程', '等式性质']
                }
        except Exception:
            pass
        return self._solve_generic(content)

    def _solve_quadratic(self, content: str) -> Dict:
        """解一元二次方程"""
        return {
            'answer': '使用求根公式求解',
            'steps': [
                {'step': 1, 'description': '化成标准形式', 'formula': 'ax² + bx + c = 0'},
                {'step': 2, 'description': '计算判别式', 'formula': 'Δ = b² - 4ac'},
                {'step': 3, 'description': '应用求根公式', 'formula': 'x = (-b ± √Δ) / 2a'}
            ],
            'method': '公式法',
            'explanation': '一元二次方程使用求根公式求解',
            'related_formulas': ['ax² + bx + c = 0', 'x = (-b ± √(b²-4ac))/(2a)', 'Δ = b² - 4ac'],
            'related_concepts': ['一元二次方程', '判别式', '求根公式']
        }

    def _solve_sequence(self, content: str) -> Dict:
        """解数列题"""
        return {
            'answer': '使用数列公式求解',
            'steps': [
                {'step': 1, 'description': '确定数列类型', 'formula': '等差数列/等比数列'},
                {'step': 2, 'description': '找出已知量', 'formula': '首项、公差/公比、项数'},
                {'step': 3, 'description': '应用通项/求和公式', 'formula': ''}
            ],
            'method': '公式法',
            'explanation': '数列问题使用对应公式求解',
            'related_formulas': ['an = a1 + (n-1)d', 'Sn = n(a1+an)/2'],
            'related_concepts': ['等差数列', '数列通项', '数列求和']
        }

    def _solve_geometry(self, content: str) -> Dict:
        """解几何题"""
        if '直角' in content or '勾股' in content or '斜边' in content:
            return {
                'answer': '使用勾股定理',
                'steps': [
                    {'step': 1, 'description': '识别直角三角形', 'formula': ''},
                    {'step': 2, 'description': '应用勾股定理', 'formula': 'a² + b² = c²'},
                    {'step': 3, 'description': '计算求解', 'formula': ''}
                ],
                'method': '公式法',
                'explanation': '直角三角形使用勾股定理求解',
                'related_formulas': ['a² + b² = c²'],
                'related_concepts': ['勾股定理', '直角三角形']
            }
        return self._solve_generic(content)

    def _solve_probability(self, content: str) -> Dict:
        """解概率题"""
        return {
            'answer': '使用古典概型',
            'steps': [
                {'step': 1, 'description': '计算总情况数', 'formula': 'n = 总数'},
                {'step': 2, 'description': '计算有利情况数', 'formula': 'm = 有利数'},
                {'step': 3, 'description': '计算概率', 'formula': 'P(A) = m/n'}
            ],
            'method': '公式法',
            'explanation': '古典概型问题使用 P(A) = m/n 求解',
            'related_formulas': ['P(A) = m/n'],
            'related_concepts': ['古典概型', '概率基础']
        }

    def _solve_generic(self, content: str) -> Dict:
        """通用解题方法"""
        return {
            'answer': '请参考答案解析',
            'steps': [
                {'step': 1, 'description': '理解题意', 'formula': ''},
                {'step': 2, 'description': '分析已知条件', 'formula': ''},
                {'step': 3, 'description': '选择合适方法', 'formula': ''},
                {'step': 4, 'description': '计算求解', 'formula': ''}
            ],
            'method': '综合法',
            'explanation': '根据题目类型选择合适的解题方法',
            'related_formulas': [],
            'related_concepts': []
        }


_math_problem_generator = None
_math_solver = None


def get_math_problem_generator(db_path=None) -> MathProblemGenerator:
    """获取数学问题生成器单例"""
    global _math_problem_generator
    if _math_problem_generator is None:
        _math_problem_generator = MathProblemGenerator(db_path)
    return _math_problem_generator


def get_math_solver() -> MathSolver:
    """获取数学解题引擎单例"""
    global _math_solver
    if _math_solver is None:
        _math_solver = MathSolver()
    return _math_solver


if __name__ == '__main__':
    generator = MathProblemGenerator()
    solver = MathSolver()

    print("=== 代数题 ===")
    problems = generator.generate_problems(3, 'algebra', 1)
    for p in problems:
        print(f"  题目: {p['content']}")
        print(f"  答案: {p['correct_answer']}")
        print()

    print("=== 几何题 ===")
    problems = generator.generate_problems(3, 'geometry', 2)
    for p in problems:
        print(f"  题目: {p['content']}")
        print(f"  答案: {p['correct_answer']}")
        print()

    print("=== 概率题 ===")
    problems = generator.generate_problems(3, 'probability', 2)
    for p in problems:
        print(f"  题目: {p['content']}")
        print(f"  答案: {p['correct_answer']}")
        print()
