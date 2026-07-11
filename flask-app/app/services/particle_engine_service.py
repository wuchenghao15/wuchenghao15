# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""粒子引擎服务 - 粒子系统模拟、N体问题、力场模拟"""
import sqlite3
import os
import json
import math
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

MAX_PARTICLES = 500
MAX_STEPS = 10000
SAMPLING_INTERVAL = 10


class ParticleEngineService:
    """粒子引擎服务"""

    def __init__(self, db_path: str = 'app.db'):
        self.db_path = db_path
        self._create_tables()
        self._init_default_data()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """创建粒子引擎相关表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS particle_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                symbol TEXT,
                mass REAL,
                charge REAL,
                spin REAL,
                color TEXT DEFAULT '#4CAF50',
                description TEXT,
                category TEXT DEFAULT 'fundamental',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS particle_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                integration_method TEXT DEFAULT 'euler',
                time_step REAL DEFAULT 0.001,
                duration REAL DEFAULT 1.0,
                boundary_type TEXT DEFAULT 'none',
                boundary_x_min REAL DEFAULT -10.0,
                boundary_x_max REAL DEFAULT 10.0,
                boundary_y_min REAL DEFAULT -10.0,
                boundary_y_max REAL DEFAULT 10.0,
                boundary_z_min REAL DEFAULT -10.0,
                boundary_z_max REAL DEFAULT 10.0,
                gravity REAL DEFAULT 0.0,
                damping REAL DEFAULT 0.0,
                status TEXT DEFAULT 'created',
                particle_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS particles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                type_id INTEGER,
                name TEXT,
                x REAL NOT NULL,
                y REAL NOT NULL,
                z REAL NOT NULL DEFAULT 0.0,
                vx REAL NOT NULL DEFAULT 0.0,
                vy REAL NOT NULL DEFAULT 0.0,
                vz REAL NOT NULL DEFAULT 0.0,
                ax REAL NOT NULL DEFAULT 0.0,
                ay REAL NOT NULL DEFAULT 0.0,
                az REAL NOT NULL DEFAULT 0.0,
                mass REAL DEFAULT 1.0,
                charge REAL DEFAULT 0.0,
                radius REAL DEFAULT 0.5,
                lifetime REAL DEFAULT 0.0,
                remaining_life REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                color TEXT DEFAULT '#FF5722',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES particle_systems(id),
                FOREIGN KEY (type_id) REFERENCES particle_types(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS force_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                field_type TEXT DEFAULT 'gravity',
                magnitude REAL DEFAULT 9.81,
                direction TEXT DEFAULT '[0, -1, 0]',
                origin TEXT DEFAULT '[0, 0, 0]',
                parameters TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES particle_systems(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS particle_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                interaction_type TEXT DEFAULT 'collision',
                particle_type_a INTEGER,
                particle_type_b INTEGER,
                coefficient REAL DEFAULT 1.0,
                min_distance REAL DEFAULT 0.0,
                max_distance REAL DEFAULT 100.0,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES particle_systems(id)
            )
        ''')

        try:
            cursor.execute('ALTER TABLE particle_interactions ADD COLUMN name TEXT NOT NULL DEFAULT ""')
        except sqlite3.OperationalError:
            pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS particle_simulation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                step INTEGER NOT NULL,
                time REAL NOT NULL,
                particles TEXT,
                energy TEXT,
                FOREIGN KEY (system_id) REFERENCES particle_systems(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("粒子引擎表创建完成")

    def _init_default_data(self):
        """初始化默认粒子类型"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM particle_types')
        count = cursor.fetchone()[0]

        if count == 0:
            now = datetime.now().isoformat()
            particle_types = [
                ('电子', 'e⁻', 9.1093837015e-31, -1.602176634e-19, 0.5, '#2196F3', '带负电荷的基本粒子', 'fundamental', now, now),
                ('质子', 'p⁺', 1.67262192369e-27, 1.602176634e-19, 0.5, '#F44336', '带正电荷的基本粒子', 'fundamental', now, now),
                ('中子', 'n', 1.67492749804e-27, 0.0, 0.5, '#9E9E9E', '不带电的基本粒子', 'fundamental', now, now),
                ('光子', 'γ', 0.0, 0.0, 1.0, '#FFEB3B', '光的量子粒子', 'fundamental', now, now),
                ('α粒子', 'α', 6.6446573357e-27, 3.204353268e-19, 0.0, '#E91E63', '氦原子核', 'composite', now, now),
                ('氢原子', 'H', 1.6735575e-27, 0.0, 0.5, '#4CAF50', '最简单的原子', 'atom', now, now),
                ('电子对', 'e⁺e⁻', 1.821867403e-30, 0.0, 0.0, '#9C27B0', '电子和正电子对', 'composite', now, now),
                ('尘埃粒子', 'dust', 1e-15, 0.0, 0.0, '#795548', '微小固体颗粒', 'macroscopic', now, now),
                ('气体分子', 'gas', 2.6566962e-26, 0.0, 0.0, '#8BC34A', '气体分子', 'molecule', now, now),
                ('行星', 'planet', 5.972e24, 0.0, 0.0, '#00BCD4', '行星级天体', 'astronomical', now, now),
                ('恒星', 'star', 1.989e30, 0.0, 0.0, '#FF9800', '恒星级天体', 'astronomical', now, now),
                ('自定义粒子', 'custom', 1.0, 0.0, 0.0, '#607D8B', '用户自定义粒子', 'custom', now, now),
            ]

            cursor.executemany('''
                INSERT OR IGNORE INTO particle_types 
                (name, symbol, mass, charge, spin, color, description, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', particle_types)
            logger.info(f"初始化了 {len(particle_types)} 个粒子类型")

        conn.commit()
        conn.close()

    def create_particle_system(self, name: str, description: str = '',
                               integration_method: str = 'euler',
                               time_step: float = 0.001, duration: float = 1.0,
                               boundary_type: str = 'none',
                               boundary_x_min: float = -10.0,
                               boundary_x_max: float = 10.0,
                               boundary_y_min: float = -10.0,
                               boundary_y_max: float = 10.0,
                               gravity: float = 0.0, damping: float = 0.0) -> int:
        """创建粒子系统"""
        now = datetime.now().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO particle_systems 
                (name, description, integration_method, time_step, duration, 
                 boundary_type, boundary_x_min, boundary_x_max, boundary_y_min, 
                 boundary_y_max, gravity, damping, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, integration_method, time_step, duration,
                  boundary_type, boundary_x_min, boundary_x_max, boundary_y_min,
                  boundary_y_max, gravity, damping, now, now))

            system_id = cursor.lastrowid
            conn.commit()
            logger.info(f"粒子系统创建成功: {name}")
            return system_id
        except Exception as e:
            logger.error(f"创建粒子系统失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_particle(self, system_id: int, x: float, y: float, z: float = 0.0,
                     vx: float = 0.0, vy: float = 0.0, vz: float = 0.0,
                     mass: float = 1.0, charge: float = 0.0, radius: float = 0.5,
                     lifetime: float = 0.0, color: str = '#FF5722',
                     type_id: int = None, name: str = '') -> int:
        """添加粒子"""
        now = datetime.now().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT particle_count FROM particle_systems WHERE id = ?', (system_id,))
            row = cursor.fetchone()
            if row and row[0] >= MAX_PARTICLES:
                raise ValueError(f"粒子数量超过上限 {MAX_PARTICLES}")

            cursor.execute('''
                INSERT INTO particles 
                (system_id, type_id, name, x, y, z, vx, vy, vz, ax, ay, az, 
                 mass, charge, radius, lifetime, remaining_life, is_active, color,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (system_id, type_id, name, x, y, z, vx, vy, vz, 0.0, 0.0, 0.0,
                  mass, charge, radius, lifetime, lifetime if lifetime > 0 else 0.0, 1, color,
                  now, now))

            cursor.execute('UPDATE particle_systems SET particle_count = particle_count + 1 WHERE id = ?', (system_id,))

            particle_id = cursor.lastrowid
            conn.commit()
            return particle_id
        except Exception as e:
            logger.error(f"添加粒子失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_force_field(self, system_id: int, name: str, field_type: str = 'gravity',
                        magnitude: float = 9.81, direction: List[float] = None,
                        origin: List[float] = None, parameters: Dict = None) -> int:
        """添加力场"""
        now = datetime.now().isoformat()
        direction = direction or [0, -1, 0]
        origin = origin or [0, 0, 0]
        parameters = parameters or {}

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO force_fields 
                (system_id, name, field_type, magnitude, direction, origin, parameters,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (system_id, name, field_type, magnitude, json.dumps(direction),
                  json.dumps(origin), json.dumps(parameters), now, now))

            field_id = cursor.lastrowid
            conn.commit()
            logger.info(f"力场添加成功: {name}")
            return field_id
        except Exception as e:
            logger.error(f"添加力场失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _compute_forces(self, particles: List[Dict], force_fields: List[Dict],
                        interactions: List[Dict], gravity: float) -> List[Dict]:
        """计算所有力"""
        for particle in particles:
            ax, ay, az = 0.0, 0.0, 0.0

            for field in force_fields:
                if not field.get('is_active', 1):
                    continue

                field_type = field.get('field_type', 'gravity')
                magnitude = field.get('magnitude', 9.81)
                direction = field.get('direction', [0, -1, 0])
                if isinstance(direction, str):
                    direction = json.loads(direction)
                origin = field.get('origin', [0, 0, 0])
                if isinstance(origin, str):
                    origin = json.loads(origin)
                params = field.get('parameters', {})
                if isinstance(params, str):
                    params = json.loads(params)

                if field_type == 'gravity':
                    ax += direction[0] * magnitude
                    ay += direction[1] * magnitude
                    az += direction[2] * magnitude

                elif field_type == 'point_gravity':
                    dx = origin[0] - particle['x']
                    dy = origin[1] - particle['y']
                    dz = origin[2] - particle['z']
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                    if dist > 0:
                        force = magnitude / (dist * dist)
                        ax += (dx / dist) * force
                        ay += (dy / dist) * force
                        az += (dz / dist) * force

                elif field_type == 'electric':
                    q = particle.get('charge', 0.0)
                    ax += direction[0] * magnitude * q
                    ay += direction[1] * magnitude * q
                    az += direction[2] * magnitude * q

                elif field_type == 'magnetic':
                    q = particle.get('charge', 0.0)
                    vx, vy, vz = particle['vx'], particle['vy'], particle['vz']
                    bx, by, bz = direction[0], direction[1], direction[2]
                    ax += q * (vy * bz - vz * by)
                    ay += q * (vz * bx - vx * bz)
                    az += q * (vx * by - vy * bx)

                elif field_type == 'drag':
                    speed = math.sqrt(particle['vx']**2 + particle['vy']**2 + particle['vz']**2)
                    if speed > 0:
                        drag = magnitude * speed
                        ax -= (particle['vx'] / speed) * drag
                        ay -= (particle['vy'] / speed) * drag
                        az -= (particle['vz'] / speed) * drag

            for other in particles:
                if particle['id'] == other['id']:
                    continue

                dx = other['x'] - particle['x']
                dy = other['y'] - particle['y']
                dz = other['z'] - particle['z']
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)

                for interaction in interactions:
                    if not interaction.get('enabled', 1):
                        continue

                    itype = interaction.get('interaction_type', 'collision')
                    coeff = interaction.get('coefficient', 1.0)
                    min_dist = interaction.get('min_distance', 0.0)
                    max_dist = interaction.get('max_distance', 100.0)

                    if dist >= min_dist and dist <= max_dist:
                        if itype == 'gravity':
                            G = 6.67430e-11 * coeff
                            force = G * particle['mass'] * other['mass'] / (dist * dist)
                            ax += (dx / dist) * force
                            ay += (dy / dist) * force
                            az += (dz / dist) * force

                        elif itype == 'electrostatic':
                            k = 8.9875517873681764e9 * coeff
                            force = k * particle['charge'] * other['charge'] / (dist * dist)
                            ax += (dx / dist) * force
                            ay += (dy / dist) * force
                            az += (dz / dist) * force

                        elif itype == 'spring':
                            rest_length = params.get('rest_length', 1.0) if isinstance(params, dict) else 1.0
                            force = coeff * (dist - rest_length)
                            ax += (dx / dist) * force
                            ay += (dy / dist) * force
                            az += (dz / dist) * force

            if gravity != 0:
                ay -= gravity

            particle['ax'], particle['ay'], particle['az'] = ax, ay, az

        return particles

    def _integrate_euler(self, particles: List[Dict], dt: float) -> List[Dict]:
        """Euler积分"""
        for p in particles:
            p['vx'] += p['ax'] * dt
            p['vy'] += p['ay'] * dt
            p['vz'] += p['az'] * dt
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['z'] += p['vz'] * dt
        return particles

    def _integrate_verlet(self, particles: List[Dict], dt: float) -> List[Dict]:
        """Verlet积分"""
        for p in particles:
            old_x, old_y, old_z = p['x'], p['y'], p['z']
            p['x'] = 2 * p['x'] - p.get('prev_x', p['x']) + p['ax'] * dt * dt
            p['y'] = 2 * p['y'] - p.get('prev_y', p['y']) + p['ay'] * dt * dt
            p['z'] = 2 * p['z'] - p.get('prev_z', p['z']) + p['az'] * dt * dt
            p['vx'] = (p['x'] - old_x) / dt
            p['vy'] = (p['y'] - old_y) / dt
            p['vz'] = (p['z'] - old_z) / dt
            p['prev_x'], p['prev_y'], p['prev_z'] = old_x, old_y, old_z
        return particles

    def _integrate_rk4(self, particles: List[Dict], dt: float, force_fields: List[Dict],
                       interactions: List[Dict], gravity: float) -> List[Dict]:
        """RK4积分"""
        n = len(particles)

        k1_v = [[0.0, 0.0, 0.0] for _ in range(n)]
        k1_x = [[0.0, 0.0, 0.0] for _ in range(n)]

        temp_particles = [{'id': p['id'], 'x': p['x'], 'y': p['y'], 'z': p['z'],
                           'vx': p['vx'], 'vy': p['vy'], 'vz': p['vz'],
                           'ax': p['ax'], 'ay': p['ay'], 'az': p['az'],
                           'mass': p['mass'], 'charge': p['charge']}
                          for p in particles]

        temp_particles = self._compute_forces(temp_particles, force_fields, interactions, gravity)
        for i, p in enumerate(temp_particles):
            k1_v[i] = [p['ax'], p['ay'], p['az']]
            k1_x[i] = [p['vx'], p['vy'], p['vz']]

        k2_v = [[0.0, 0.0, 0.0] for _ in range(n)]
        k2_x = [[0.0, 0.0, 0.0] for _ in range(n)]

        temp_particles = [{'id': p['id'], 'x': p['x'] + k1_x[i][0] * dt / 2,
                           'y': p['y'] + k1_x[i][1] * dt / 2,
                           'z': p['z'] + k1_x[i][2] * dt / 2,
                           'vx': p['vx'] + k1_v[i][0] * dt / 2,
                           'vy': p['vy'] + k1_v[i][1] * dt / 2,
                           'vz': p['vz'] + k1_v[i][2] * dt / 2,
                           'ax': 0, 'ay': 0, 'az': 0,
                           'mass': p['mass'], 'charge': p['charge']}
                          for i, p in enumerate(particles)]

        temp_particles = self._compute_forces(temp_particles, force_fields, interactions, gravity)
        for i, p in enumerate(temp_particles):
            k2_v[i] = [p['ax'], p['ay'], p['az']]
            k2_x[i] = [p['vx'], p['vy'], p['vz']]

        k3_v = [[0.0, 0.0, 0.0] for _ in range(n)]
        k3_x = [[0.0, 0.0, 0.0] for _ in range(n)]

        temp_particles = [{'id': p['id'], 'x': p['x'] + k2_x[i][0] * dt / 2,
                           'y': p['y'] + k2_x[i][1] * dt / 2,
                           'z': p['z'] + k2_x[i][2] * dt / 2,
                           'vx': p['vx'] + k2_v[i][0] * dt / 2,
                           'vy': p['vy'] + k2_v[i][1] * dt / 2,
                           'vz': p['vz'] + k2_v[i][2] * dt / 2,
                           'ax': 0, 'ay': 0, 'az': 0,
                           'mass': p['mass'], 'charge': p['charge']}
                          for i, p in enumerate(particles)]

        temp_particles = self._compute_forces(temp_particles, force_fields, interactions, gravity)
        for i, p in enumerate(temp_particles):
            k3_v[i] = [p['ax'], p['ay'], p['az']]
            k3_x[i] = [p['vx'], p['vy'], p['vz']]

        k4_v = [[0.0, 0.0, 0.0] for _ in range(n)]
        k4_x = [[0.0, 0.0, 0.0] for _ in range(n)]

        temp_particles = [{'id': p['id'], 'x': p['x'] + k3_x[i][0] * dt,
                           'y': p['y'] + k3_x[i][1] * dt,
                           'z': p['z'] + k3_x[i][2] * dt,
                           'vx': p['vx'] + k3_v[i][0] * dt,
                           'vy': p['vy'] + k3_v[i][1] * dt,
                           'vz': p['vz'] + k3_v[i][2] * dt,
                           'ax': 0, 'ay': 0, 'az': 0,
                           'mass': p['mass'], 'charge': p['charge']}
                          for i, p in enumerate(particles)]

        temp_particles = self._compute_forces(temp_particles, force_fields, interactions, gravity)
        for i, p in enumerate(temp_particles):
            k4_v[i] = [p['ax'], p['ay'], p['az']]
            k4_x[i] = [p['vx'], p['vy'], p['vz']]

        for i, p in enumerate(particles):
            p['vx'] += (k1_v[i][0] + 2*k2_v[i][0] + 2*k3_v[i][0] + k4_v[i][0]) * dt / 6
            p['vy'] += (k1_v[i][1] + 2*k2_v[i][1] + 2*k3_v[i][1] + k4_v[i][1]) * dt / 6
            p['vz'] += (k1_v[i][2] + 2*k2_v[i][2] + 2*k3_v[i][2] + k4_v[i][2]) * dt / 6
            p['x'] += (k1_x[i][0] + 2*k2_x[i][0] + 2*k3_x[i][0] + k4_x[i][0]) * dt / 6
            p['y'] += (k1_x[i][1] + 2*k2_x[i][1] + 2*k3_x[i][1] + k4_x[i][1]) * dt / 6
            p['z'] += (k1_x[i][2] + 2*k2_x[i][2] + 2*k3_x[i][2] + k4_x[i][2]) * dt / 6

        return particles

    def _apply_boundary(self, particles: List[Dict], boundary_type: str,
                        bx_min: float, bx_max: float, by_min: float, by_max: float) -> List[Dict]:
        """应用边界条件"""
        if boundary_type == 'none':
            return particles

        for p in particles:
            if boundary_type == 'bounce':
                if p['x'] <= bx_min or p['x'] >= bx_max:
                    p['vx'] *= -0.9
                    p['x'] = max(bx_min, min(bx_max, p['x']))
                if p['y'] <= by_min or p['y'] >= by_max:
                    p['vy'] *= -0.9
                    p['y'] = max(by_min, min(by_max, p['y']))

            elif boundary_type == 'wrap':
                if p['x'] <= bx_min:
                    p['x'] = bx_max
                elif p['x'] >= bx_max:
                    p['x'] = bx_min
                if p['y'] <= by_min:
                    p['y'] = by_max
                elif p['y'] >= by_max:
                    p['y'] = by_min

            elif boundary_type == 'absorb':
                if p['x'] <= bx_min or p['x'] >= bx_max or p['y'] <= by_min or p['y'] >= by_max:
                    p['is_active'] = 0

        return particles

    def _detect_collisions(self, particles: List[Dict], damping: float = 0.0) -> List[Dict]:
        """检测碰撞"""
        n = len(particles)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = particles[i]
                p2 = particles[j]

                if not p1.get('is_active', 1) or not p2.get('is_active', 1):
                    continue

                dx = p2['x'] - p1['x']
                dy = p2['y'] - p1['y']
                dz = p2['z'] - p1['z']
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                min_dist = p1.get('radius', 0.5) + p2.get('radius', 0.5)

                if dist < min_dist and dist > 0:
                    nx, ny, nz = dx / dist, dy / dist, dz / dist

                    dvx = p1['vx'] - p2['vx']
                    dvy = p1['vy'] - p2['vy']
                    dvz = p1['vz'] - p2['vz']

                    vel_normal = dvx * nx + dvy * ny + dvz * nz

                    if vel_normal > 0:
                        m1, m2 = p1['mass'], p2['mass']
                        restitution = 0.8

                        j = -(1 + restitution) * vel_normal
                        j /= (1/m1) + (1/m2)

                        p1['vx'] += (j / m1) * nx
                        p1['vy'] += (j / m1) * ny
                        p1['vz'] += (j / m1) * nz
                        p2['vx'] -= (j / m2) * nx
                        p2['vy'] -= (j / m2) * ny
                        p2['vz'] -= (j / m2) * nz

                        overlap = 0.5 * (min_dist - dist)
                        p1['x'] -= overlap * nx
                        p1['y'] -= overlap * ny
                        p1['z'] -= overlap * nz
                        p2['x'] += overlap * nx
                        p2['y'] += overlap * ny
                        p2['z'] += overlap * nz

        if damping > 0:
            for p in particles:
                p['vx'] *= (1 - damping)
                p['vy'] *= (1 - damping)
                p['vz'] *= (1 - damping)

        return particles

    def _compute_energy(self, particles: List[Dict]) -> Dict[str, float]:
        """计算系统能量"""
        kinetic = 0.0
        potential = 0.0

        for p in particles:
            if not p.get('is_active', 1):
                continue
            v2 = p['vx']**2 + p['vy']**2 + p['vz']**2
            kinetic += 0.5 * p['mass'] * v2

        n = len(particles)
        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = particles[i], particles[j]
                if not p1.get('is_active', 1) or not p2.get('is_active', 1):
                    continue
                dx = p2['x'] - p1['x']
                dy = p2['y'] - p1['y']
                dz = p2['z'] - p1['z']
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist > 0:
                    potential += -6.67430e-11 * p1['mass'] * p2['mass'] / dist

        return {'kinetic': round(kinetic, 12), 'potential': round(potential, 12), 'total': round(kinetic + potential, 12)}

    def run_simulation(self, system_id: int) -> Dict[str, Any]:
        """运行粒子模拟"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM particle_systems WHERE id = ?', (system_id,))
            system_row = cursor.fetchone()
            if not system_row:
                return {'success': False, 'error': '粒子系统不存在'}

            system = self._parse_system_row(system_row)

            cursor.execute('SELECT * FROM particles WHERE system_id = ?', (system_id,))
            particle_rows = cursor.fetchall()
            particles = [self._parse_particle_row(row) for row in particle_rows]

            cursor.execute('SELECT * FROM force_fields WHERE system_id = ?', (system_id,))
            field_rows = cursor.fetchall()
            force_fields = [self._parse_force_field_row(row) for row in field_rows]

            cursor.execute('SELECT * FROM particle_interactions WHERE system_id = ?', (system_id,))
            interaction_rows = cursor.fetchall()
            interactions = [self._parse_interaction_row(row) for row in interaction_rows]

            conn.close()

            dt = system['time_step']
            duration = system['duration']
            method = system['integration_method']
            gravity = system['gravity']
            damping = system['damping']
            boundary_type = system['boundary_type']

            steps = int(duration / dt)
            if steps > MAX_STEPS:
                steps = MAX_STEPS
                duration = steps * dt

            sampled_results = []
            energy_history = []

            for step in range(steps + 1):
                t = step * dt

                particles = self._compute_forces(particles, force_fields, interactions, gravity)

                if method == 'verlet':
                    particles = self._integrate_verlet(particles, dt)
                elif method == 'rk4':
                    particles = self._integrate_rk4(particles, dt, force_fields, interactions, gravity)
                else:
                    particles = self._integrate_euler(particles, dt)

                particles = self._apply_boundary(particles, boundary_type,
                                                 system['boundary_x_min'],
                                                 system['boundary_x_max'],
                                                 system['boundary_y_min'],
                                                 system['boundary_y_max'])

                particles = self._detect_collisions(particles, damping)

                for p in particles:
                    if p.get('lifetime', 0) > 0:
                        p['remaining_life'] -= dt
                        if p['remaining_life'] <= 0:
                            p['is_active'] = 0

                if step % SAMPLING_INTERVAL == 0 or step == steps:
                    energy = self._compute_energy(particles)
                    energy_history.append({'step': step, 'time': round(t, 6), **energy})

                    sampled_particles = [{
                        'id': p['id'],
                        'name': p.get('name', ''),
                        'x': round(p['x'], 6),
                        'y': round(p['y'], 6),
                        'z': round(p['z'], 6),
                        'vx': round(p['vx'], 6),
                        'vy': round(p['vy'], 6),
                        'vz': round(p['vz'], 6),
                        'is_active': p.get('is_active', 1),
                        'color': p.get('color', '#FF5722')
                    } for p in particles]

                    sampled_results.append({
                        'step': step,
                        'time': round(t, 6),
                        'particles': sampled_particles,
                        'energy': energy
                    })

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE particle_systems SET status = ?, duration = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
            ''', ('completed', duration, datetime.now().isoformat(), datetime.now().isoformat(), system_id))

            cursor.executemany('''
                UPDATE particles SET x = ?, y = ?, z = ?, vx = ?, vy = ?, vz = ?,
                    ax = ?, ay = ?, az = ?, is_active = ?, remaining_life = ?, updated_at = ?
                WHERE id = ?
            ''', [(p['x'], p['y'], p['z'], p['vx'], p['vy'], p['vz'],
                   p['ax'], p['ay'], p['az'], p.get('is_active', 1),
                   p.get('remaining_life', 0), datetime.now().isoformat(), p['id'])
                  for p in particles])

            conn.commit()
            conn.close()

            return {
                'success': True,
                'system_id': system_id,
                'parameters': {
                    'integration_method': method,
                    'time_step': dt,
                    'duration': duration,
                    'steps': steps,
                    'particle_count': len(particles),
                    'sampling_interval': SAMPLING_INTERVAL
                },
                'results': sampled_results,
                'energy_history': energy_history,
                'total_sampled_frames': len(sampled_results)
            }

        except Exception as e:
            logger.error(f"粒子模拟失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def create_preset_solar_system(self, name: str = '太阳系', duration: float = 1000.0) -> int:
        """创建太阳系预设场景"""
        system_id = self.create_particle_system(
            name=name,
            description='简化的太阳系模型',
            integration_method='verlet',
            time_step=0.01,
            duration=duration,
            boundary_type='none'
        )

        self.add_particle(system_id, 0, 0, 0, 0, 0, 0,
                          mass=1.989e30, charge=0, radius=0.5,
                          color='#FF9800', name='太阳')

        planets = [
            {'name': '水星', 'distance': 5.79e10, 'speed': 4.74e4, 'mass': 3.285e23, 'radius': 0.2, 'color': '#9E9E9E'},
            {'name': '金星', 'distance': 1.082e11, 'speed': 3.50e4, 'mass': 4.867e24, 'radius': 0.3, 'color': '#FFC107'},
            {'name': '地球', 'distance': 1.496e11, 'speed': 2.98e4, 'mass': 5.972e24, 'radius': 0.35, 'color': '#2196F3'},
            {'name': '火星', 'distance': 2.279e11, 'speed': 2.41e4, 'mass': 6.39e23, 'radius': 0.25, 'color': '#F44336'},
            {'name': '木星', 'distance': 7.786e11, 'speed': 1.31e4, 'mass': 1.898e27, 'radius': 0.8, 'color': '#FFA726'},
            {'name': '土星', 'distance': 1.434e12, 'speed': 9.69e3, 'mass': 5.683e26, 'radius': 0.7, 'color': '#FFCC80'},
        ]

        for planet in planets:
            self.add_particle(system_id, planet['distance'], 0, 0,
                              0, planet['speed'], 0,
                              mass=planet['mass'], charge=0,
                              radius=planet['radius'], color=planet['color'],
                              name=planet['name'])

        self.add_force_field(system_id, '太阳引力', field_type='point_gravity',
                             magnitude=1.32712440018e20,
                             origin=[0, 0, 0])

        self.add_interaction(system_id, 'nbody_gravity', interaction_type='gravity',
                             coefficient=1.0, max_distance=1e13)

        return system_id

    def create_preset_gas_molecules(self, name: str = '气体分子', count: int = 50,
                                     duration: float = 1.0) -> int:
        """创建气体分子预设场景"""
        system_id = self.create_particle_system(
            name=name,
            description='理想气体分子运动模拟',
            integration_method='verlet',
            time_step=0.001,
            duration=duration,
            boundary_type='bounce',
            boundary_x_min=-5.0,
            boundary_x_max=5.0,
            boundary_y_min=-5.0,
            boundary_y_max=5.0,
            damping=0.0
        )

        import random
        for i in range(count):
            x = random.uniform(-4.0, 4.0)
            y = random.uniform(-4.0, 4.0)
            vx = (random.random() - 0.5) * 10
            vy = (random.random() - 0.5) * 10
            self.add_particle(system_id, x, y, 0, vx, vy, 0,
                              mass=2.6566962e-26, charge=0,
                              radius=0.1, color='#8BC34A',
                              name=f'分子{i+1}')

        self.add_interaction(system_id, 'collision', interaction_type='collision',
                             coefficient=1.0, min_distance=0.0, max_distance=0.3)

        return system_id

    def create_preset_electric_field(self, name: str = '电场中的带电粒子',
                                      duration: float = 1.0) -> int:
        """创建电场预设场景"""
        system_id = self.create_particle_system(
            name=name,
            description='带电粒子在电场中的运动',
            integration_method='rk4',
            time_step=0.001,
            duration=duration,
            boundary_type='bounce',
            boundary_x_min=-10.0,
            boundary_x_max=10.0,
            boundary_y_min=-10.0,
            boundary_y_max=10.0
        )

        self.add_particle(system_id, 0, 0, 0, 0, 0, 0,
                          mass=9.1093837015e-31, charge=-1.602176634e-19,
                          radius=0.1, color='#2196F3', name='电子')

        self.add_force_field(system_id, '匀强电场', field_type='electric',
                             magnitude=100.0, direction=[1, 0, 0])

        return system_id

    def create_preset_magnetic_field(self, name: str = '磁场中的带电粒子',
                                      duration: float = 1.0) -> int:
        """创建磁场预设场景"""
        system_id = self.create_particle_system(
            name=name,
            description='带电粒子在磁场中的圆周运动',
            integration_method='rk4',
            time_step=0.0001,
            duration=duration,
            boundary_type='none'
        )

        self.add_particle(system_id, 0, 0, 0, 1e6, 0, 0,
                          mass=9.1093837015e-31, charge=-1.602176634e-19,
                          radius=0.05, color='#2196F3', name='电子')

        self.add_force_field(system_id, '匀强磁场', field_type='magnetic',
                             magnitude=0.1, direction=[0, 0, 1])

        return system_id

    def create_preset_brownian_motion(self, name: str = '布朗运动', count: int = 20,
                                        duration: float = 1.0) -> int:
        """创建布朗运动预设场景"""
        system_id = self.create_particle_system(
            name=name,
            description='布朗运动模拟',
            integration_method='euler',
            time_step=0.001,
            duration=duration,
            boundary_type='bounce',
            boundary_x_min=-5.0,
            boundary_x_max=5.0,
            boundary_y_min=-5.0,
            boundary_y_max=5.0
        )

        import random
        for i in range(count):
            x = random.uniform(-4.0, 4.0)
            y = random.uniform(-4.0, 4.0)
            self.add_particle(system_id, x, y, 0, 0, 0, 0,
                              mass=1e-15, charge=0,
                              radius=0.15, color='#E91E63',
                              name=f'粒子{i+1}')

        for i in range(200):
            x = random.uniform(-5.0, 5.0)
            y = random.uniform(-5.0, 5.0)
            vx = (random.random() - 0.5) * 500
            vy = (random.random() - 0.5) * 500
            self.add_particle(system_id, x, y, 0, vx, vy, 0,
                              mass=1e-20, charge=0,
                              radius=0.02, color='#BDBDBD',
                              name=f'热分子{i+1}')

        return system_id

    def add_interaction(self, system_id: int, name: str, interaction_type: str = 'collision',
                        particle_type_a: int = None, particle_type_b: int = None,
                        coefficient: float = 1.0, min_distance: float = 0.0,
                        max_distance: float = 100.0) -> int:
        """添加粒子交互规则"""
        now = datetime.now().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO particle_interactions 
                (system_id, name, interaction_type, particle_type_a, particle_type_b,
                 coefficient, min_distance, max_distance, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ''', (system_id, name, interaction_type, particle_type_a, particle_type_b,
                  coefficient, min_distance, max_distance, now, now))

            interaction_id = cursor.lastrowid
            conn.commit()
            return interaction_id
        except Exception as e:
            logger.error(f"添加交互规则失败: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_particle_system(self, system_id: int) -> Optional[Dict[str, Any]]:
        """获取粒子系统"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM particle_systems WHERE id = ?', (system_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._parse_system_row(row)
        return None

    def get_particle_systems(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取粒子系统列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM particle_systems ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
        rows = cursor.fetchall()

        conn.close()

        return [self._parse_system_row(row) for row in rows]

    def get_particles(self, system_id: int) -> List[Dict[str, Any]]:
        """获取粒子列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM particles WHERE system_id = ?', (system_id,))
        rows = cursor.fetchall()

        conn.close()

        return [self._parse_particle_row(row) for row in rows]

    def get_particle_types(self) -> List[Dict[str, Any]]:
        """获取粒子类型列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM particle_types ORDER BY category, name')
        rows = cursor.fetchall()

        conn.close()

        return [{
            'id': row[0],
            'name': row[1],
            'symbol': row[2],
            'mass': row[3],
            'charge': row[4],
            'spin': row[5],
            'color': row[6],
            'description': row[7],
            'category': row[8],
            'created_at': row[9],
            'updated_at': row[10]
        } for row in rows]

    def delete_particle_system(self, system_id: int) -> bool:
        """删除粒子系统"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM particles WHERE system_id = ?', (system_id,))
            cursor.execute('DELETE FROM force_fields WHERE system_id = ?', (system_id,))
            cursor.execute('DELETE FROM particle_interactions WHERE system_id = ?', (system_id,))
            cursor.execute('DELETE FROM particle_simulation_results WHERE system_id = ?', (system_id,))
            cursor.execute('DELETE FROM particle_systems WHERE id = ?', (system_id,))

            conn.commit()
            logger.info(f"粒子系统删除成功: {system_id}")
            return True
        except Exception as e:
            logger.error(f"删除粒子系统失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_particle_stats(self) -> Dict[str, Any]:
        """获取粒子引擎统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) FROM particle_systems')
        stats['total_systems'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM particles')
        stats['total_particles'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM force_fields')
        stats['total_force_fields'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM particle_types')
        stats['total_particle_types'] = cursor.fetchone()[0]

        cursor.execute('SELECT status, COUNT(*) FROM particle_systems GROUP BY status')
        stats['systems_by_status'] = dict(cursor.fetchall())

        cursor.execute('SELECT category, COUNT(*) FROM particle_types GROUP BY category')
        stats['particle_types_by_category'] = dict(cursor.fetchall())

        conn.close()
        return stats

    def _parse_system_row(self, row) -> Dict[str, Any]:
        return {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'integration_method': row[3],
            'time_step': row[4],
            'duration': row[5],
            'boundary_type': row[6],
            'boundary_x_min': row[7],
            'boundary_x_max': row[8],
            'boundary_y_min': row[9],
            'boundary_y_max': row[10],
            'boundary_z_min': row[11],
            'boundary_z_max': row[12],
            'gravity': row[13],
            'damping': row[14],
            'status': row[15],
            'particle_count': row[16],
            'created_by': row[17],
            'created_at': row[18],
            'updated_at': row[19],
            'completed_at': row[20] if len(row) > 20 else None
        }

    def _parse_particle_row(self, row) -> Dict[str, Any]:
        return {
            'id': row[0],
            'system_id': row[1],
            'type_id': row[2],
            'name': row[3],
            'x': row[4],
            'y': row[5],
            'z': row[6],
            'vx': row[7],
            'vy': row[8],
            'vz': row[9],
            'ax': row[10],
            'ay': row[11],
            'az': row[12],
            'mass': row[13],
            'charge': row[14],
            'radius': row[15],
            'lifetime': row[16],
            'remaining_life': row[17],
            'is_active': bool(row[18]),
            'color': row[19],
            'created_at': row[20],
            'updated_at': row[21]
        }

    def _parse_force_field_row(self, row) -> Dict[str, Any]:
        return {
            'id': row[0],
            'system_id': row[1],
            'name': row[2],
            'field_type': row[3],
            'magnitude': row[4],
            'direction': json.loads(row[5]) if row[5] else [0, -1, 0],
            'origin': json.loads(row[6]) if row[6] else [0, 0, 0],
            'parameters': json.loads(row[7]) if row[7] else {},
            'is_active': bool(row[8]),
            'created_at': row[9],
            'updated_at': row[10]
        }

    def _parse_interaction_row(self, row) -> Dict[str, Any]:
        return {
            'id': row[0],
            'system_id': row[1],
            'name': row[2] if len(row) > 2 else '',
            'interaction_type': row[3] if len(row) > 3 else 'collision',
            'particle_type_a': row[4] if len(row) > 4 else None,
            'particle_type_b': row[5] if len(row) > 5 else None,
            'coefficient': row[6] if len(row) > 6 else 1.0,
            'min_distance': row[7] if len(row) > 7 else 0.0,
            'max_distance': row[8] if len(row) > 8 else 100.0,
            'enabled': bool(row[9]) if len(row) > 9 else True,
            'created_at': row[10] if len(row) > 10 else '',
            'updated_at': row[11] if len(row) > 11 else ''
        }


particle_engine_service = ParticleEngineService()
