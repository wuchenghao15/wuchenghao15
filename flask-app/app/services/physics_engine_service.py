# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""物理引擎数据库服务 - 物理模拟、力学计算、物理模型管理"""
import sqlite3
import os
import json
import math
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PhysicsEngineService:
    """物理引擎服务"""

    def __init__(self, db_path: str = 'app.db'):
        self.db_path = db_path
        self._create_tables()
        self._init_default_data()

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """创建物理引擎相关表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                description TEXT,
                color TEXT DEFAULT '#667eea',
                icon TEXT DEFAULT '🔬',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES physics_categories(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_formulas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                formula TEXT NOT NULL,
                latex TEXT,
                category TEXT,
                physics_type TEXT DEFAULT 'mechanics',
                description TEXT,
                variables TEXT,
                constants TEXT,
                examples TEXT,
                derivation_steps TEXT,
                units TEXT,
                difficulty_level INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 0,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_constants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                symbol TEXT,
                value REAL NOT NULL,
                unit TEXT,
                description TEXT,
                category TEXT DEFAULT 'fundamental',
                uncertainty REAL,
                is_exact INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                object_type TEXT DEFAULT 'particle',
                mass REAL,
                position TEXT,
                velocity TEXT,
                acceleration TEXT,
                properties TEXT,
                description TEXT,
                simulation_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_forces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                force_type TEXT DEFAULT 'gravity',
                magnitude REAL,
                direction TEXT,
                point_of_application TEXT,
                properties TEXT,
                description TEXT,
                simulation_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                simulation_type TEXT DEFAULT 'mechanics',
                description TEXT,
                parameters TEXT,
                initial_conditions TEXT,
                results TEXT,
                status TEXT DEFAULT 'created',
                duration REAL DEFAULT 0,
                time_step REAL DEFAULT 0.01,
                gravity REAL DEFAULT 9.81,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physics_simulation_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                time REAL NOT NULL,
                state TEXT,
                energy TEXT,
                FOREIGN KEY (simulation_id) REFERENCES physics_simulations(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS math_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model_type TEXT DEFAULT 'equation',
                description TEXT,
                equations TEXT,
                variables TEXT,
                parameters TEXT,
                boundary_conditions TEXT,
                initial_conditions TEXT,
                solution_method TEXT,
                analytical_solution TEXT,
                numerical_solution TEXT,
                category TEXT,
                difficulty_level INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 0,
                source TEXT,
                examples TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS math_model_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                description TEXT,
                color TEXT DEFAULT '#764ba2',
                icon TEXT DEFAULT '📐',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES math_model_categories(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS math_functions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                function_type TEXT DEFAULT 'algebraic',
                expression TEXT,
                latex TEXT,
                domain TEXT,
                range TEXT,
                properties TEXT,
                derivatives TEXT,
                integrals TEXT,
                description TEXT,
                category TEXT,
                difficulty_level INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("物理引擎和数学模型表创建完成")

    def _init_default_data(self):
        """初始化默认数据"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM physics_constants')
        count = cursor.fetchone()[0]

        if count == 0:
            now = datetime.now().isoformat()
            constants = [
                ('光速', 'c', 299792458.0, 'm/s', '真空中的光速', 'fundamental', 0.0, 1, now, now),
                ('普朗克常数', 'h', 6.62607015e-34, 'J·s', '普朗克常数', 'quantum', 0.0, 1, now, now),
                ('约化普朗克常数', 'ħ', 1.054571817e-34, 'J·s', '约化普朗克常数', 'quantum', 0.0, 0, now, now),
                ('引力常数', 'G', 6.67430e-11, 'N·m²/kg²', '万有引力常数', 'gravity', 0.0, 0, now, now),
                ('玻尔兹曼常数', 'k', 1.380649e-23, 'J/K', '玻尔兹曼常数', 'thermodynamics', 0.0, 1, now, now),
                ('阿伏伽德罗常数', 'N_A', 6.02214076e23, 'mol⁻¹', '阿伏伽德罗常数', 'thermodynamics', 0.0, 1, now, now),
                ('电子电荷', 'e', 1.602176634e-19, 'C', '元电荷', 'electromagnetism', 0.0, 1, now, now),
                ('电子质量', 'm_e', 9.1093837015e-31, 'kg', '电子静止质量', 'particle', 0.0, 0, now, now),
                ('质子质量', 'm_p', 1.67262192369e-27, 'kg', '质子静止质量', 'particle', 0.0, 0, now, now),
                ('中子质量', 'm_n', 1.67492749804e-27, 'kg', '中子静止质量', 'particle', 0.0, 0, now, now),
                ('真空介电常数', 'ε₀', 8.8541878128e-12, 'F/m', '真空电容率', 'electromagnetism', 0.0, 0, now, now),
                ('真空磁导率', 'μ₀', 1.25663706212e-6, 'H/m', '真空磁导率', 'electromagnetism', 0.0, 0, now, now),
                ('标准重力加速度', 'g', 9.80665, 'm/s²', '海平面标准重力加速度', 'mechanics', 0.0, 1, now, now),
                ('精细结构常数', 'α', 7.2973525693e-3, '', '精细结构常数', 'quantum', 0.0, 0, now, now),
                ('里德伯常数', 'R_∞', 10973731.568160, 'm⁻¹', '里德伯常数', 'quantum', 0.0, 0, now, now),
                ('斯特藩-玻尔兹曼常数', 'σ', 5.670374419e-8, 'W/(m²·K⁴)', '斯特藩-玻尔兹曼常数', 'thermodynamics', 0.0, 1, now, now),
                ('维恩位移常数', 'b', 2.897771955e-3, 'm·K', '维恩位移定律常数', 'thermodynamics', 0.0, 1, now, now),
                ('理想气体常数', 'R', 8.314462618, 'J/(mol·K)', '普适气体常数', 'thermodynamics', 0.0, 1, now, now),
                ('法拉第常数', 'F', 96485.33212, 'C/mol', '法拉第常数', 'electrochemistry', 0.0, 1, now, now),
                ('玻尔半径', 'a₀', 5.29177210903e-11, 'm', '玻尔半径', 'quantum', 0.0, 0, now, now),
            ]

            cursor.executemany('''
                INSERT OR IGNORE INTO physics_constants 
                (name, symbol, value, unit, description, category, uncertainty, is_exact, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', constants)
            logger.info(f"初始化了 {len(constants)} 个物理常数")

        cursor.execute('SELECT COUNT(*) FROM physics_formulas')
        formula_count = cursor.fetchone()[0]

        if formula_count == 0:
            now = datetime.now().isoformat()
            formulas = [
                ('牛顿第二定律', 'F = ma', 'F = ma', '经典力学', 'mechanics',
                 '物体加速度与作用力成正比，与质量成反比',
                 json.dumps({'F': '作用力 (N)', 'm': '质量 (kg)', 'a': '加速度 (m/s²)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'m': 2, 'a': 5}, 'output': {'F': 10}}]),
                 json.dumps(['动量定理推导', '实验验证']),
                 json.dumps({'F': 'N', 'm': 'kg', 'a': 'm/s²'}),
                 1, 1, '经典力学', now, now),
                ('万有引力定律', 'F = Gm₁m₂/r²', 'F = G \\frac{m_1 m_2}{r^2}', '万有引力', 'gravity',
                 '两个质点之间的引力与质量乘积成正比，与距离平方成反比',
                 json.dumps({'F': '引力 (N)', 'G': '引力常数', 'm1': '质量1 (kg)', 'm2': '质量2 (kg)', 'r': '距离 (m)'}),
                 json.dumps({'G': 6.67430e-11}),
                 json.dumps([{'input': {'m1': 1000, 'm2': 500, 'r': 10}, 'output': {'F': 3.337e-9}}]),
                 json.dumps(['开普勒定律推导', '牛顿推导']),
                 json.dumps({'F': 'N', 'm': 'kg', 'r': 'm'}),
                 2, 1, '万有引力', now, now),
                ('动能公式', 'E_k = ½mv²', 'E_k = \\frac{1}{2}mv^2', '能量', 'mechanics',
                 '物体由于运动而具有的能量',
                 json.dumps({'E_k': '动能 (J)', 'm': '质量 (kg)', 'v': '速度 (m/s)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'m': 2, 'v': 3}, 'output': {'E_k': 9}}]),
                 json.dumps(['功的定义推导', '运动学方程']),
                 json.dumps({'E_k': 'J', 'm': 'kg', 'v': 'm/s'}),
                 1, 1, '能量守恒', now, now),
                ('势能公式', 'E_p = mgh', 'E_p = mgh', '能量', 'mechanics',
                 '重力势能，物体由于被举高而具有的能量',
                 json.dumps({'E_p': '势能 (J)', 'm': '质量 (kg)', 'g': '重力加速度', 'h': '高度 (m)'}),
                 json.dumps({'g': 9.81}),
                 json.dumps([{'input': {'m': 2, 'h': 5}, 'output': {'E_p': 98.1}}]),
                 json.dumps(['功的定义', '保守力场']),
                 json.dumps({'E_p': 'J', 'm': 'kg', 'h': 'm'}),
                 1, 1, '能量守恒', now, now),
                ('动量公式', 'p = mv', 'p = mv', '动量', 'mechanics',
                 '物体的质量和速度的乘积',
                 json.dumps({'p': '动量 (kg·m/s)', 'm': '质量 (kg)', 'v': '速度 (m/s)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'m': 2, 'v': 3}, 'output': {'p': 6}}]),
                 json.dumps(['牛顿力学定义']),
                 json.dumps({'p': 'kg·m/s', 'm': 'kg', 'v': 'm/s'}),
                 1, 1, '动量守恒', now, now),
                ('胡克定律', 'F = -kx', 'F = -kx', '弹性力学', 'mechanics',
                 '弹簧的弹力与形变量成正比，方向相反',
                 json.dumps({'F': '弹力 (N)', 'k': '劲度系数 (N/m)', 'x': '形变量 (m)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'k': 100, 'x': 0.1}, 'output': {'F': -10}}]),
                 json.dumps(['实验定律', '弹性势能推导']),
                 json.dumps({'F': 'N', 'k': 'N/m', 'x': 'm'}),
                 1, 1, '弹性力学', now, now),
                ('欧姆定律', 'U = IR', 'U = IR', '电磁学', 'electromagnetism',
                 '导体两端电压与电流成正比',
                 json.dumps({'U': '电压 (V)', 'I': '电流 (A)', 'R': '电阻 (Ω)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'I': 2, 'R': 5}, 'output': {'U': 10}}]),
                 json.dumps(['实验定律', '欧姆发现']),
                 json.dumps({'U': 'V', 'I': 'A', 'R': 'Ω'}),
                 1, 1, '电路理论', now, now),
                ('功率公式', 'P = UI', 'P = UI', '电磁学', 'electromagnetism',
                 '电功率等于电压乘以电流',
                 json.dumps({'P': '功率 (W)', 'U': '电压 (V)', 'I': '电流 (A)'}),
                 json.dumps({}),
                 json.dumps([{'input': {'U': 220, 'I': 2}, 'output': {'P': 440}}]),
                 json.dumps(['能量定义', '焦耳定律']),
                 json.dumps({'P': 'W', 'U': 'V', 'I': 'A'}),
                 1, 1, '电路理论', now, now),
                ('理想气体状态方程', 'PV = nRT', 'PV = nRT', '热学', 'thermodynamics',
                 '描述理想气体状态的方程',
                 json.dumps({'P': '压强 (Pa)', 'V': '体积 (m³)', 'n': '物质的量 (mol)', 'R': '气体常数', 'T': '温度 (K)'}),
                 json.dumps({'R': 8.314}),
                 json.dumps([{'input': {'P': 101325, 'V': 0.0224, 'n': 1, 'T': 273.15}, 'output': {'valid': True}}]),
                 json.dumps(['波义耳定律', '查理定律', '盖-吕萨克定律']),
                 json.dumps({'P': 'Pa', 'V': 'm³', 'n': 'mol', 'T': 'K'}),
                 2, 1, '气体动理论', now, now),
                ('质能方程', 'E = mc²', 'E = mc^2', '相对论', 'relativity',
                 '质量和能量的等价关系',
                 json.dumps({'E': '能量 (J)', 'm': '质量 (kg)', 'c': '光速'}),
                 json.dumps({'c': 299792458.0}),
                 json.dumps([{'input': {'m': 1e-3}, 'output': {'E': 8.9876e13}}]),
                 json.dumps(['狭义相对论推导', '爱因斯坦']),
                 json.dumps({'E': 'J', 'm': 'kg'}),
                 3, 1, '相对论', now, now),
            ]

            cursor.executemany('''
                INSERT OR IGNORE INTO physics_formulas 
                (name, formula, latex, category, physics_type, description, variables, constants, 
                 examples, derivation_steps, units, difficulty_level, is_verified, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', formulas)
            logger.info(f"初始化了 {len(formulas)} 个物理公式")

        cursor.execute('SELECT COUNT(*) FROM math_models')
        model_count = cursor.fetchone()[0]

        if model_count == 0:
            now = datetime.now().isoformat()
            models = [
                ('一元二次方程', 'algebra', '形如ax²+bx+c=0的方程',
                 json.dumps(['ax² + bx + c = 0']),
                 json.dumps({'x': '未知数', 'a': '二次项系数', 'b': '一次项系数', 'c': '常数项'}),
                 json.dumps({'a': {'not': 0}}),
                 json.dumps({}),
                 json.dumps({}),
                 'analytical',
                 json.dumps(['x = (-b±√(b²-4ac))/(2a)']),
                 json.dumps({}),
                 '代数方程', 1, 1, '代数学',
                 json.dumps([{'input': {'a': 1, 'b': -5, 'c': 6}, 'output': {'x1': 3, 'x2': 2}}]),
                 now, now),
                ('简谐振动', 'differential', '简谐振动的微分方程模型',
                 json.dumps(['d²x/dt² + ω²x = 0']),
                 json.dumps({'x': '位移', 't': '时间', 'ω': '角频率'}),
                 json.dumps({'ω': {'gt': 0}}),
                 json.dumps({'x(0)': 'A', 'v(0)': 0}),
                 json.dumps({'x(t)': 'A·cos(ωt + φ)'}),
                 'analytical',
                 json.dumps(['x(t) = A cos(ωt + φ)']),
                 json.dumps({}),
                 '微分方程', 2, 1, '振动理论',
                 json.dumps([{'input': {'A': 1, 'ω': 2, 'φ': 0, 't': 0}, 'output': {'x': 1}}]),
                 now, now),
                ('指数增长模型', 'exponential', '指数增长/衰减模型',
                 json.dumps(['dy/dt = ky', 'y(t) = y₀e^(kt)']),
                 json.dumps({'y': '量', 't': '时间', 'k': '增长率'}),
                 json.dumps({}),
                 json.dumps({}),
                 json.dumps({'y(0)': 'y₀'}),
                 'analytical',
                 json.dumps(['y(t) = y₀ e^(kt)']),
                 json.dumps({}),
                 '微分方程', 1, 1, '生物数学',
                 json.dumps([{'input': {'y0': 100, 'k': 0.05, 't': 10}, 'output': {'y': 164.87}}]),
                 now, now),
                ('傅里叶变换', 'integral', '傅里叶变换数学模型',
                 json.dumps(['F(ω) = ∫f(t)e^(-iωt)dt']),
                 json.dumps({'f(t)': '时域函数', 'F(ω)': '频域函数', 'ω': '角频率'}),
                 json.dumps({}),
                 json.dumps({}),
                 json.dumps({}),
                 'integral',
                 json.dumps({}),
                 json.dumps({}),
                 '积分变换', 3, 1, '信号处理',
                 json.dumps([{'input': {'type': 'gaussian', 'sigma': 1}, 'output': {'transform': 'gaussian'}}]),
                 now, now),
                ('拉普拉斯变换', 'integral', '拉普拉斯变换数学模型',
                 json.dumps(['F(s) = ∫₀^∞ f(t)e^(-st)dt']),
                 json.dumps({'f(t)': '时域函数', 'F(s)': 's域函数', 's': '复频率'}),
                 json.dumps({}),
                 json.dumps({}),
                 json.dumps({}),
                 'integral',
                 json.dumps({}),
                 json.dumps({}),
                 '积分变换', 3, 1, '控制理论',
                 json.dumps([{'input': {'f': 'e^(at)', 'a': 2}, 'output': {'F(s)': '1/(s-2)'}}]),
                 now, now),
                ('正态分布', 'probability', '正态分布概率模型',
                 json.dumps(['f(x) = (1/√(2πσ²))e^(-(x-μ)²/(2σ²))']),
                 json.dumps({'x': '随机变量', 'μ': '均值', 'σ': '标准差'}),
                 json.dumps({'σ': {'gt': 0}}),
                 json.dumps({}),
                 json.dumps({}),
                 'analytical',
                 json.dumps({}),
                 json.dumps({}),
                 '概率分布', 2, 1, '统计学',
                 json.dumps([{'input': {'mu': 0, 'sigma': 1, 'x': 0}, 'output': {'pdf': 0.3989}}]),
                 now, now),
                ('线性回归', 'statistics', '一元线性回归模型',
                 json.dumps(['y = β₀ + β₁x + ε']),
                 json.dumps({'y': '因变量', 'x': '自变量', 'β₀': '截距', 'β₁': '斜率', 'ε': '误差项'}),
                 json.dumps({}),
                 json.dumps({}),
                 json.dumps({}),
                 'numerical',
                 json.dumps({}),
                 json.dumps({'method': 'least_squares'}),
                 '统计模型', 2, 1, '回归分析',
                 json.dumps([{'input': {'x': [1,2,3,4,5], 'y': [2,4,5,4,5]}, 'output': {'slope': 0.6, 'intercept': 2.2}}]),
                 now, now),
                ('泊松方程', 'pde', '泊松方程偏微分方程模型',
                 json.dumps(['∇²φ = f']),
                 json.dumps({'φ': '势函数', 'f': '源项'}),
                 json.dumps({}),
                 json.dumps({}),
                 json.dumps({}),
                 'numerical',
                 json.dumps({}),
                 json.dumps({'method': 'finite_element'}),
                 '偏微分方程', 3, 1, '数学物理',
                 json.dumps([{'input': {'dimensions': 2, 'f': 'constant'}, 'output': {'type': 'elliptic'}}]),
                 now, now),
                ('热传导方程', 'pde', '热传导偏微分方程模型',
                 json.dumps(['∂u/∂t = α∇²u']),
                 json.dumps({'u': '温度', 't': '时间', 'α': '热扩散系数'}),
                 json.dumps({'α': {'gt': 0}}),
                 json.dumps({}),
                 json.dumps({}),
                 'numerical',
                 json.dumps({}),
                 json.dumps({'method': 'finite_difference'}),
                 '偏微分方程', 3, 1, '热传导',
                 json.dumps([{'input': {'type': '1D', 'alpha': 0.01}, 'output': {'type': 'parabolic'}}]),
                 now, now),
                ('波动方程', 'pde', '波动方程偏微分方程模型',
                 json.dumps(['∂²u/∂t² = c²∇²u']),
                 json.dumps({'u': '波函数', 't': '时间', 'c': '波速'}),
                 json.dumps({'c': {'gt': 0}}),
                 json.dumps({}),
                 json.dumps({}),
                 'analytical',
                 json.dumps({}),
                 json.dumps({'method': 'd_alembert'}),
                 '偏微分方程', 3, 1, '波动理论',
                 json.dumps([{'input': {'type': '1D', 'c': 343}, 'output': {'type': 'hyperbolic'}}]),
                 now, now),
            ]

            cursor.executemany('''
                INSERT OR IGNORE INTO math_models 
                (name, model_type, description, equations, variables, parameters, boundary_conditions, 
                 initial_conditions, solution_method, analytical_solution, numerical_solution, 
                 category, difficulty_level, is_verified, source, examples, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', models)
            logger.info(f"初始化了 {len(models)} 个数学模型")

        conn.commit()
        conn.close()

    def calculate_formula(self, formula_id: int, inputs: Dict[str, float]) -> Dict[str, Any]:
        """计算物理公式

        Args:
            formula_id: 公式ID
            inputs: 输入变量字典

        Returns:
            计算结果字典
        """
        formula = self.get_physical_formula(formula_id)
        if not formula:
            return {'success': False, 'error': '公式不存在'}

        try:
            variables = formula.get('variables', {})
            constants = formula.get('constants', {})
            name = formula.get('name', '')

            result = {}

            if name == '牛顿第二定律':
                m = inputs.get('m') or inputs.get('mass')
                a = inputs.get('a') or inputs.get('acceleration')
                F = inputs.get('F') or inputs.get('force')

                if F is None and m is not None and a is not None:
                    result['F'] = m * a
                elif m is None and F is not None and a is not None and a != 0:
                    result['m'] = F / a
                elif a is None and F is not None and m is not None and m != 0:
                    result['a'] = F / m
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '万有引力定律':
                G = constants.get('G', 6.67430e-11)
                m1 = inputs.get('m1') or inputs.get('mass1')
                m2 = inputs.get('m2') or inputs.get('mass2')
                r = inputs.get('r') or inputs.get('distance')

                if m1 is not None and m2 is not None and r is not None and r != 0:
                    result['F'] = G * m1 * m2 / (r * r)
                else:
                    return {'success': False, 'error': '需要提供m1, m2, r'}

            elif name == '动能公式':
                m = inputs.get('m') or inputs.get('mass')
                v = inputs.get('v') or inputs.get('velocity')
                Ek = inputs.get('E_k') or inputs.get('Ek')

                if Ek is None and m is not None and v is not None:
                    result['E_k'] = 0.5 * m * v * v
                elif m is None and Ek is not None and v is not None and v != 0:
                    result['m'] = 2 * Ek / (v * v)
                elif v is None and Ek is not None and m is not None and m != 0:
                    result['v'] = math.sqrt(2 * Ek / m)
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '势能公式':
                g = constants.get('g', 9.81)
                m = inputs.get('m') or inputs.get('mass')
                h = inputs.get('h') or inputs.get('height')
                Ep = inputs.get('E_p') or inputs.get('Ep')

                if Ep is None and m is not None and h is not None:
                    result['E_p'] = m * g * h
                elif m is None and Ep is not None and h is not None and h != 0:
                    result['m'] = Ep / (g * h)
                elif h is None and Ep is not None and m is not None and m != 0:
                    result['h'] = Ep / (m * g)
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '动量公式':
                m = inputs.get('m') or inputs.get('mass')
                v = inputs.get('v') or inputs.get('velocity')
                p = inputs.get('p') or inputs.get('momentum')

                if p is None and m is not None and v is not None:
                    result['p'] = m * v
                elif m is None and p is not None and v is not None and v != 0:
                    result['m'] = p / v
                elif v is None and p is not None and m is not None and m != 0:
                    result['v'] = p / m
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '胡克定律':
                k = inputs.get('k') or inputs.get('spring_constant')
                x = inputs.get('x') or inputs.get('displacement')
                F = inputs.get('F') or inputs.get('force')

                if F is None and k is not None and x is not None:
                    result['F'] = -k * x
                elif k is None and F is not None and x is not None and x != 0:
                    result['k'] = -F / x
                elif x is None and F is not None and k is not None and k != 0:
                    result['x'] = -F / k
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '欧姆定律':
                U = inputs.get('U') or inputs.get('voltage')
                I = inputs.get('I') or inputs.get('current')
                R = inputs.get('R') or inputs.get('resistance')

                if U is None and I is not None and R is not None:
                    result['U'] = I * R
                elif I is None and U is not None and R is not None and R != 0:
                    result['I'] = U / R
                elif R is None and U is not None and I is not None and I != 0:
                    result['R'] = U / I
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '功率公式':
                P = inputs.get('P') or inputs.get('power')
                U = inputs.get('U') or inputs.get('voltage')
                I = inputs.get('I') or inputs.get('current')

                if P is None and U is not None and I is not None:
                    result['P'] = U * I
                elif U is None and P is not None and I is not None and I != 0:
                    result['U'] = P / I
                elif I is None and P is not None and U is not None and U != 0:
                    result['I'] = P / U
                else:
                    return {'success': False, 'error': '需要提供两个已知量'}

            elif name == '质能方程':
                c = constants.get('c', 299792458.0)
                m = inputs.get('m') or inputs.get('mass')
                E = inputs.get('E') or inputs.get('energy')

                if E is None and m is not None:
                    result['E'] = m * c * c
                elif m is None and E is not None and c != 0:
                    result['m'] = E / (c * c)
                else:
                    return {'success': False, 'error': '需要提供质量或能量'}

            elif name == '理想气体状态方程':
                R = constants.get('R', 8.314)
                P = inputs.get('P') or inputs.get('pressure')
                V = inputs.get('V') or inputs.get('volume')
                n = inputs.get('n') or inputs.get('moles')
                T = inputs.get('T') or inputs.get('temperature')

                if P is None and V is not None and n is not None and T is not None and V != 0:
                    result['P'] = n * R * T / V
                elif V is None and P is not None and n is not None and T is not None and P != 0:
                    result['V'] = n * R * T / P
                elif n is None and P is not None and V is not None and T is not None and T != 0:
                    result['n'] = P * V / (R * T)
                elif T is None and P is not None and V is not None and n is not None and n != 0:
                    result['T'] = P * V / (n * R)
                else:
                    return {'success': False, 'error': '需要提供三个已知量'}

            else:
                return {'success': False, 'error': f'暂不支持计算的公式: {name}'}

            result['formula_name'] = name
            result['inputs'] = inputs
            return {'success': True, 'result': result}

        except Exception as e:
            logger.error(f"计算公式失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def simulate_simple_pendulum(self, length: float, initial_angle: float, 
                                  duration: float = 10.0, time_step: float = 0.01,
                                  gravity: float = 9.81) -> Dict[str, Any]:
        """单摆模拟

        Args:
            length: 摆长 (m)
            initial_angle: 初始角度 (度)
            duration: 模拟时长 (s)
            time_step: 时间步长 (s)
            gravity: 重力加速度 (m/s²)

        Returns:
            模拟结果
        """
        try:
            omega = math.sqrt(gravity / length)
            period = 2 * math.pi / omega
            frequency = 1.0 / period

            theta0 = math.radians(initial_angle)

            times = []
            angles = []
            angular_velocities = []
            potential_energies = []
            kinetic_energies = []
            total_energies = []

            t = 0.0
            steps = int(duration / time_step)

            for i in range(steps + 1):
                theta = theta0 * math.cos(omega * t)
                omega_t = -theta0 * omega * math.sin(omega * t)

                Ep = 0.5 * gravity * length * theta * theta
                Ek = 0.5 * length * length * omega_t * omega_t
                E_total = Ep + Ek

                times.append(round(t, 4))
                angles.append(round(math.degrees(theta), 6))
                angular_velocities.append(round(omega_t, 6))
                potential_energies.append(round(Ep, 8))
                kinetic_energies.append(round(Ek, 8))
                total_energies.append(round(E_total, 8))

                t += time_step

            return {
                'success': True,
                'parameters': {
                    'length': length,
                    'initial_angle': initial_angle,
                    'duration': duration,
                    'time_step': time_step,
                    'gravity': gravity
                },
                'properties': {
                    'period': round(period, 6),
                    'frequency': round(frequency, 6),
                    'angular_frequency': round(omega, 6)
                },
                'data': {
                    'times': times,
                    'angles': angles,
                    'angular_velocities': angular_velocities,
                    'potential_energies': potential_energies,
                    'kinetic_energies': kinetic_energies,
                    'total_energies': total_energies
                },
                'total_steps': steps + 1
            }
        except Exception as e:
            logger.error(f"单摆模拟失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def simulate_projectile_motion(self, v0: float, angle: float,
                                    height: float = 0.0, gravity: float = 9.81,
                                    time_step: float = 0.01) -> Dict[str, Any]:
        """抛体运动模拟

        Args:
            v0: 初速度 (m/s)
            angle: 发射角度 (度)
            height: 初始高度 (m)
            gravity: 重力加速度 (m/s²)
            time_step: 时间步长 (s)

        Returns:
            模拟结果
        """
        try:
            theta = math.radians(angle)
            v0x = v0 * math.cos(theta)
            v0y = v0 * math.sin(theta)

            discriminant = v0y * v0y + 2 * gravity * height
            t_flight = (v0y + math.sqrt(discriminant)) / gravity
            max_height = height + v0y * v0y / (2 * gravity)
            range_x = v0x * t_flight

            times = []
            x_positions = []
            y_positions = []
            vx_list = []
            vy_list = []
            speed_list = []

            t = 0.0
            steps = int(t_flight / time_step) + 1

            for i in range(steps + 1):
                x = v0x * t
                y = height + v0y * t - 0.5 * gravity * t * t

                if y < 0:
                    y = 0

                vx = v0x
                vy = v0y - gravity * t
                speed = math.sqrt(vx * vx + vy * vy)

                times.append(round(t, 4))
                x_positions.append(round(x, 4))
                y_positions.append(round(y, 4))
                vx_list.append(round(vx, 4))
                vy_list.append(round(vy, 4))
                speed_list.append(round(speed, 4))

                t += time_step
                if t > t_flight:
                    break

            return {
                'success': True,
                'parameters': {
                    'v0': v0,
                    'angle': angle,
                    'height': height,
                    'gravity': gravity
                },
                'key_values': {
                    'flight_time': round(t_flight, 6),
                    'max_height': round(max_height, 6),
                    'range': round(range_x, 6),
                    'v0x': round(v0x, 6),
                    'v0y': round(v0y, 6),
                    'landing_speed': round(speed_list[-1] if speed_list else 0, 6)
                },
                'data': {
                    'times': times,
                    'x_positions': x_positions,
                    'y_positions': y_positions,
                    'vx': vx_list,
                    'vy': vy_list,
                    'speed': speed_list
                },
                'total_steps': len(times)
            }
        except Exception as e:
            logger.error(f"抛体运动模拟失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def add_physical_formula(self, name: str, formula: str, latex: str = '',
                             category: str = '', physics_type: str = 'mechanics',
                             description: str = '', variables: Dict = None,
                             constants: Dict = None, examples: List = None,
                             derivation_steps: List = None, units: Dict = None,
                             difficulty_level: int = 1, source: str = '') -> int:
        """添加物理公式"""
        now = datetime.now().isoformat()
        variables_json = json.dumps(variables) if variables else '{}'
        constants_json = json.dumps(constants) if constants else '{}'
        examples_json = json.dumps(examples) if examples else '[]'
        derivation_json = json.dumps(derivation_steps) if derivation_steps else '[]'
        units_json = json.dumps(units) if units else '{}'

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO physics_formulas 
                (name, formula, latex, category, physics_type, description, variables, constants, 
                 examples, derivation_steps, units, difficulty_level, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, formula, latex, category, physics_type, description, variables_json,
                  constants_json, examples_json, derivation_json, units_json, difficulty_level,
                  source, now, now))

            formula_id = cursor.lastrowid
            conn.commit()
            logger.info(f"物理公式添加成功: {name}")
            return formula_id
        except Exception as e:
            logger.error(f"添加物理公式失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_physical_formula(self, formula_id: int) -> Optional[Dict[str, Any]]:
        """获取单个物理公式"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM physics_formulas WHERE id = ?', (formula_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._parse_physics_formula_row(row)
        return None

    def search_physics_formulas(self, keyword: str = '', category: str = '',
                                 physics_type: str = '', limit: int = 20,
                                 offset: int = 0) -> List[Dict[str, Any]]:
        """搜索物理公式"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM physics_formulas WHERE 1=1'
        params = []

        if keyword:
            query += ' AND (name LIKE ? OR formula LIKE ? OR description LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

        if category:
            query += ' AND category = ?'
            params.append(category)

        if physics_type:
            query += ' AND physics_type = ?'
            params.append(physics_type)

        query += ' ORDER BY difficulty_level, id LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._parse_physics_formula_row(row) for row in rows]

    def _parse_physics_formula_row(self, row) -> Dict[str, Any]:
        """解析物理公式行"""
        return {
            'id': row[0],
            'name': row[1],
            'formula': row[2],
            'latex': row[3] if len(row) > 3 else '',
            'category': row[4] if len(row) > 4 else '',
            'physics_type': row[5] if len(row) > 5 else 'mechanics',
            'description': row[6] if len(row) > 6 else '',
            'variables': json.loads(row[7]) if len(row) > 7 and row[7] else {},
            'constants': json.loads(row[8]) if len(row) > 8 and row[8] else {},
            'examples': json.loads(row[9]) if len(row) > 9 and row[9] else [],
            'derivation_steps': json.loads(row[10]) if len(row) > 10 and row[10] else [],
            'units': json.loads(row[11]) if len(row) > 11 and row[11] else {},
            'difficulty_level': row[12] if len(row) > 12 else 1,
            'is_verified': bool(row[13]) if len(row) > 13 else False,
            'source': row[14] if len(row) > 14 else '',
            'created_at': row[15] if len(row) > 15 else '',
            'updated_at': row[16] if len(row) > 16 else ''
        }

    def get_constants(self, category: str = '', limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取物理常数"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM physics_constants WHERE 1=1'
        params = []

        if category:
            query += ' AND category = ?'
            params.append(category)

        query += ' ORDER BY category, name LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'name': row[1],
                'symbol': row[2],
                'value': row[3],
                'unit': row[4],
                'description': row[5],
                'category': row[6],
                'uncertainty': row[7],
                'is_exact': bool(row[8]),
                'created_at': row[9],
                'updated_at': row[10]
            })
        return result

    def get_constant_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取物理常数"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM physics_constants WHERE name = ? OR symbol = ?', (name, name))
        row = cursor.fetchone()

        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'symbol': row[2],
                'value': row[3],
                'unit': row[4],
                'description': row[5],
                'category': row[6],
                'uncertainty': row[7],
                'is_exact': bool(row[8]),
                'created_at': row[9],
                'updated_at': row[10]
            }
        return None

    def add_math_model(self, name: str, model_type: str = 'equation',
                       description: str = '', equations: List = None,
                       variables: Dict = None, parameters: Dict = None,
                       category: str = '', difficulty_level: int = 1,
                       source: str = '', examples: List = None) -> int:
        """添加数学模型"""
        now = datetime.now().isoformat()
        equations_json = json.dumps(equations) if equations else '[]'
        variables_json = json.dumps(variables) if variables else '{}'
        parameters_json = json.dumps(parameters) if parameters else '{}'
        examples_json = json.dumps(examples) if examples else '[]'

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO math_models 
                (name, model_type, description, equations, variables, parameters, 
                 category, difficulty_level, source, examples, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, model_type, description, equations_json, variables_json,
                  parameters_json, category, difficulty_level, source, examples_json, now, now))

            model_id = cursor.lastrowid
            conn.commit()
            logger.info(f"数学模型添加成功: {name}")
            return model_id
        except Exception as e:
            logger.error(f"添加数学模型失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_math_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """获取单个数学模型"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM math_models WHERE id = ?', (model_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._parse_math_model_row(row)
        return None

    def search_math_models(self, keyword: str = '', category: str = '',
                            model_type: str = '', limit: int = 20,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """搜索数学模型"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM math_models WHERE 1=1'
        params = []

        if keyword:
            query += ' AND (name LIKE ? OR description LIKE ?)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        if category:
            query += ' AND category = ?'
            params.append(category)

        if model_type:
            query += ' AND model_type = ?'
            params.append(model_type)

        query += ' ORDER BY difficulty_level, id LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._parse_math_model_row(row) for row in rows]

    def _parse_math_model_row(self, row) -> Dict[str, Any]:
        """解析数学模型行"""
        return {
            'id': row[0],
            'name': row[1],
            'model_type': row[2],
            'description': row[3],
            'equations': json.loads(row[4]) if row[4] else [],
            'variables': json.loads(row[5]) if row[5] else {},
            'parameters': json.loads(row[6]) if row[6] else {},
            'boundary_conditions': json.loads(row[7]) if row[7] else {},
            'initial_conditions': json.loads(row[8]) if row[8] else {},
            'solution_method': row[9] if row[9] else '',
            'analytical_solution': json.loads(row[10]) if row[10] else [],
            'numerical_solution': json.loads(row[11]) if row[11] else {},
            'category': row[12] if row[12] else '',
            'difficulty_level': row[13],
            'is_verified': bool(row[14]),
            'source': row[15] if row[15] else '',
            'examples': json.loads(row[16]) if row[16] else [],
            'created_at': row[17],
            'updated_at': row[18]
        }

    def get_physics_stats(self) -> Dict[str, Any]:
        """获取物理引擎统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) FROM physics_formulas')
        stats['total_formulas'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM physics_constants')
        stats['total_constants'] = cursor.fetchone()[0]

        cursor.execute('SELECT physics_type, COUNT(*) FROM physics_formulas GROUP BY physics_type')
        stats['formulas_by_type'] = dict(cursor.fetchall())

        cursor.execute('SELECT category, COUNT(*) FROM physics_constants GROUP BY category')
        stats['constants_by_category'] = dict(cursor.fetchall())

        cursor.execute('SELECT COUNT(*) FROM math_models')
        stats['total_math_models'] = cursor.fetchone()[0]

        cursor.execute('SELECT model_type, COUNT(*) FROM math_models GROUP BY model_type')
        stats['math_models_by_type'] = dict(cursor.fetchall())

        conn.close()
        return stats


physics_engine_service = PhysicsEngineService()
