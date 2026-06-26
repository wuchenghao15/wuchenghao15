# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""渲染引擎服务 - SVG渲染、物理模拟可视化、图表生成"""
import math
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class RenderEngineService:
    """渲染引擎服务"""

    def __init__(self):
        self.default_width = 800
        self.default_height = 600
        self.default_background = '#f5f5f5'

    def _create_svg_header(self, width: int, height: int,
                           background: str = None,
                           viewbox: str = None) -> str:
        """创建SVG头部"""
        bg = background or self.default_background
        vb = viewbox or f"0 0 {width} {height}"
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{vb}">
  <rect width="100%" height="100%" fill="{bg}"/>
'''

    def _create_svg_footer(self) -> str:
        return '</svg>'

    def render_particles(self, particles: List[Dict],
                         width: int = 800, height: int = 600,
                         background: str = None,
                         scale: float = 1.0,
                         offset_x: float = 0, offset_y: float = 0,
                         show_grid: bool = True,
                         show_labels: bool = True,
                         trails: List[List] = None) -> str:
        """渲染粒子系统

        Args:
            particles: 粒子列表，每个粒子包含x, y, z, vx, vy, vz, color, radius, name等
            width: 画布宽度
            height: 画布高度
            background: 背景颜色
            scale: 缩放比例
            offset_x: X偏移
            offset_y: Y偏移
            show_grid: 是否显示网格
            show_labels: 是否显示标签
            trails: 粒子轨迹列表

        Returns:
            SVG字符串
        """
        cx = width / 2 + offset_x
        cy = height / 2 + offset_y

        svg = self._create_svg_header(width, height, background)

        if show_grid:
            svg += self._draw_grid(width, height, grid_size=50)

        if trails:
            for trail in trails:
                if len(trail) > 1:
                    path_data = 'M '
                    for i, point in enumerate(trail):
                        px = cx + point[0] * scale
                        py = cy - point[1] * scale
                        if i == 0:
                            path_data += f'{px},{py}'
                        else:
                            path_data += f' L {px},{py}'
                    svg += f'  <path d="{path_data}" fill="none" stroke="rgba(100, 100, 255, 0.4)" stroke-width="1.5"/>\n'

        for p in particles:
            if not p.get('is_active', True):
                continue

            px = cx + p['x'] * scale
            py = cy - p['y'] * scale
            color = p.get('color', '#FF5722')
            radius = p.get('radius', 5) * scale
            radius = max(1, min(radius, 50))

            svg += f'  <circle cx="{px:.2f}" cy="{py:.2f}" r="{radius:.2f}" fill="{color}" opacity="0.9">'
            svg += f'<title>{p.get("name", "Particle")}</title></circle>\n'

            if show_labels and p.get('name'):
                svg += f'  <text x="{px + radius + 2:.2f}" y="{py - radius - 2:.2f}" font-size="10" fill="#333">{p["name"]}</text>\n'

            if p.get('vx') is not None and p.get('vy') is not None:
                vx, vy = p['vx'], p['vy']
                speed = math.sqrt(vx * vx + vy * vy)
                if speed > 0:
                    arrow_len = min(speed * scale * 0.1, 30)
                    dx = (vx / speed) * arrow_len
                    dy = (-vy / speed) * arrow_len
                    svg += f'  <line x1="{px:.2f}" y1="{py:.2f}" x2="{px + dx:.2f}" y2="{py + dy:.2f}" stroke="#666" stroke-width="1.5" marker-end="url(#arrowhead)"/>\n'

        svg += f'<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#666"/></marker></defs>\n'

        svg += self._draw_axes(width, height, cx, cy)

        svg += self._create_svg_footer()
        return svg

    def render_particle_animation_frames(self, simulation_results: List[Dict],
                                         width: int = 800, height: int = 600,
                                         background: str = None,
                                         scale: float = 1.0,
                                         show_grid: bool = True,
                                         show_trails: bool = True,
                                         trail_length: int = 20) -> List[str]:
        """渲染粒子动画帧

        Args:
            simulation_results: 模拟结果帧列表
            width: 画布宽度
            height: 画布高度
            background: 背景颜色
            scale: 缩放比例
            show_grid: 是否显示网格
            show_trails: 是否显示轨迹
            trail_length: 轨迹长度

        Returns:
            SVG帧列表
        """
        frames = []
        particle_trails = {}

        for frame_idx, frame in enumerate(simulation_results):
            particles = frame.get('particles', [])

            if show_trails:
                for p in particles:
                    pid = p.get('id', p.get('name', 'particle'))
                    if pid not in particle_trails:
                        particle_trails[pid] = []
                    particle_trails[pid].append([p['x'], p['y']])
                    if len(particle_trails[pid]) > trail_length:
                        particle_trails[pid].pop(0)

            trails = list(particle_trails.values()) if show_trails else None

            svg = self.render_particles(
                particles, width, height, background,
                scale, show_grid=show_grid,
                show_labels=False, trails=trails
            )

            time_text = f't = {frame.get("time", 0):.3f}s'
            svg = svg.replace('</svg>',
                             f'  <text x="10" y="25" font-size="14" fill="#333" font-family="monospace">{time_text}</text>\n</svg>')

            frames.append(svg)

        return frames

    def render_pendulum(self, length: float, angle: float,
                        width: int = 400, height: int = 500,
                        background: str = None,
                        scale: float = 100.0) -> str:
        """渲染单摆

        Args:
            length: 摆长 (m)
            angle: 角度 (度)
            width: 画布宽度
            height: 画布高度
            background: 背景颜色
            scale: 缩放比例 (像素/米)

        Returns:
            SVG字符串
        """
        cx = width / 2
        pivot_y = 50

        svg = self._create_svg_header(width, height, background)

        svg += f'  <line x1="{cx - 60}" y1="{pivot_y}" x2="{cx + 60}" y2="{pivot_y}" stroke="#333" stroke-width="3"/>\n'
        svg += f'  <circle cx="{cx}" cy="{pivot_y}" r="5" fill="#333"/>\n'

        rad = math.radians(angle)
        bob_x = cx + length * scale * math.sin(rad)
        bob_y = pivot_y + length * scale * math.cos(rad)
        bob_radius = 20

        svg += f'  <line x1="{cx:.2f}" y1="{pivot_y}" x2="{bob_x:.2f}" y2="{bob_y:.2f}" stroke="#555" stroke-width="2"/>\n'
        svg += f'  <circle cx="{bob_x:.2f}" cy="{bob_y:.2f}" r="{bob_radius}" fill="#FF5722" stroke="#E64A19" stroke-width="2"/>\n'

        angle_arc_r = 40
        if angle >= 0:
            start_angle = 270
            end_angle = 270 + angle
        else:
            start_angle = 270 + angle
            end_angle = 270

        large_arc = abs(angle) > 180
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        sx = cx + angle_arc_r * math.cos(start_rad)
        sy = pivot_y + angle_arc_r * math.sin(start_rad)
        ex = cx + angle_arc_r * math.cos(end_rad)
        ey = pivot_y + angle_arc_r * math.sin(end_rad)

        svg += f'  <path d="M {sx:.2f} {sy:.2f} A {angle_arc_r} {angle_arc_r} 0 {1 if large_arc else 0} 1 {ex:.2f} {ey:.2f}" fill="none" stroke="#2196F3" stroke-width="2"/>\n'
        svg += f'  <text x="{cx + angle_arc_r + 10}" y="{pivot_y}" font-size="12" fill="#2196F3">{angle:.1f}°</text>\n'

        svg += f'  <text x="10" y="{height - 10}" font-size="12" fill="#666">L = {length}m</text>\n'

        svg += self._create_svg_footer()
        return svg

    def render_projectile(self, v0: float, angle: float, height: float = 0.0,
                          gravity: float = 9.81,
                          width: int = 800, height_px: int = 500,
                          background: str = None,
                          scale: float = 5.0,
                          show_trajectory: bool = True,
                          show_vectors: bool = True) -> str:
        """渲染抛体运动

        Args:
            v0: 初速度 (m/s)
            angle: 发射角度 (度)
            height: 初始高度 (m)
            gravity: 重力加速度
            width: 画布宽度
            height_px: 画布高度
            background: 背景颜色
            scale: 缩放比例 (像素/米)
            show_trajectory: 是否显示轨迹
            show_vectors: 是否显示速度矢量

        Returns:
            SVG字符串
        """
        ground_y = height_px - 50
        start_x = 60

        svg = self._create_svg_header(width, height_px, background)

        svg += f'  <line x1="0" y1="{ground_y}" x2="{width}" y2="{ground_y}" stroke="#4CAF50" stroke-width="3"/>\n'
        for i in range(0, width, 100):
            svg += f'  <line x1="{i}" y1="{ground_y}" x2="{i}" y2="{ground_y + 5}" stroke="#4CAF50" stroke-width="2"/>\n'
            svg += f'  <text x="{i}" y="{ground_y + 18}" font-size="10" fill="#4CAF50" text-anchor="middle">{i // scale:.0f}m</text>\n'

        theta = math.radians(angle)
        v0x = v0 * math.cos(theta)
        v0y = v0 * math.sin(theta)
        discriminant = v0y * v0y + 2 * gravity * height
        t_flight = (v0y + math.sqrt(discriminant)) / gravity
        range_x = v0x * t_flight
        max_height = height + v0y * v0y / (2 * gravity)

        start_y = ground_y - height * scale

        if show_trajectory:
            path_points = []
            steps = 50
            for i in range(steps + 1):
                t = (i / steps) * t_flight
                x = start_x + v0x * t * scale
                y = start_y - (v0y * t - 0.5 * gravity * t * t) * scale
                path_points.append(f'{x:.2f},{y:.2f}')

            svg += f'  <polyline points="{" ".join(path_points)}" fill="none" stroke="#2196F3" stroke-width="2" stroke-dasharray="5,3"/>\n'

        svg += f'  <circle cx="{start_x}" cy="{start_y}" r="12" fill="#FF5722" stroke="#E64A19" stroke-width="2"/>\n'

        if show_vectors:
            v_scale = 3.0
            vx_px = v0x * v_scale
            vy_px = -v0y * v_scale

            svg += f'  <line x1="{start_x}" y1="{start_y}" x2="{start_x + vx_px:.2f}" y2="{start_y}" stroke="#4CAF50" stroke-width="2" marker-end="url(#v-arrow)"/>\n'
            svg += f'  <text x="{start_x + vx_px / 2:.2f}" y="{start_y - 5}" font-size="11" fill="#4CAF50" text-anchor="middle">v₀x</text>\n'

            svg += f'  <line x1="{start_x}" y1="{start_y}" x2="{start_x}" y2="{start_y + vy_px:.2f}" stroke="#F44336" stroke-width="2" marker-end="url(#v-arrow)"/>\n'
            svg += f'  <text x="{start_x + 15}" y="{start_y + vy_px / 2:.2f}" font-size="11" fill="#F44336">v₀y</text>\n'

            v_mag = math.sqrt(v0x * v0x + v0y * v0y) * v_scale
            svg += f'  <line x1="{start_x}" y1="{start_y}" x2="{start_x + vx_px:.2f}" y2="{start_y + vy_px:.2f}" stroke="#FF9800" stroke-width="3" marker-end="url(#v-arrow)"/>\n'
            svg += f'  <text x="{start_x + vx_px / 2 - 20:.2f}" y="{start_y + vy_px / 2 - 10:.2f}" font-size="11" fill="#FF9800">v₀={v0}m/s</text>\n'

        svg += f'<defs><marker id="v-arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#FF9800"/></marker></defs>\n'

        svg += f'  <text x="10" y="25" font-size="13" fill="#333">初速度: {v0} m/s | 角度: {angle}° | 高度: {height} m</text>\n'
        svg += f'  <text x="10" y="45" font-size="12" fill="#666">飞行时间: {t_flight:.2f}s | 最大高度: {max_height:.2f}m | 射程: {range_x:.2f}m</text>\n'

        svg += self._create_svg_footer()
        return svg

    def render_chart(self, data: Dict[str, Any],
                     chart_type: str = 'line',
                     width: int = 800, height: int = 500,
                     background: str = None,
                     title: str = '',
                     x_label: str = '',
                     y_label: str = '',
                     show_legend: bool = True,
                     colors: List[str] = None) -> str:
        """渲染图表

        Args:
            data: 图表数据 { 'datasets': [{'label': '', 'data': [(x,y),...]}], 'x_labels': [...] }
            chart_type: 图表类型 line/bar/area
            width: 画布宽度
            height: 画布高度
            background: 背景颜色
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            show_legend: 是否显示图例
            colors: 颜色列表

        Returns:
            SVG字符串
        """
        margin = {'top': 60, 'right': 30, 'bottom': 60, 'left': 70}
        chart_w = width - margin['left'] - margin['right']
        chart_h = height - margin['top'] - margin['bottom']

        if not colors:
            colors = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0', '#FF9800',
                      '#00BCD4', '#E91E63', '#8BC34A']

        datasets = data.get('datasets', [])
        all_values = []
        for ds in datasets:
            for point in ds.get('data', []):
                if isinstance(point, (list, tuple)):
                    all_values.append(point[1])
                else:
                    all_values.append(point)

        if not all_values:
            all_values = [0, 1]

        y_min = min(all_values) * 0.9 if min(all_values) > 0 else min(all_values) * 1.1
        y_max = max(all_values) * 1.1 if max(all_values) > 0 else max(all_values) * 0.9
        if y_min == y_max:
            y_min -= 1
            y_max += 1

        x_min = 0
        x_max = max(len(ds.get('data', [])) for ds in datasets) - 1
        if x_max <= 0:
            x_max = 1

        def x_px(x_val):
            return margin['left'] + (x_val - x_min) / (x_max - x_min) * chart_w

        def y_px(y_val):
            return margin['top'] + chart_h - (y_val - y_min) / (y_max - y_min) * chart_h

        svg = self._create_svg_header(width, height, background)

        if title:
            svg += f'  <text x="{width/2}" y="30" font-size="18" fill="#333" text-anchor="middle" font-weight="bold">{title}</text>\n'

        grid_y_count = 5
        for i in range(grid_y_count + 1):
            y_val = y_min + (y_max - y_min) * i / grid_y_count
            y = y_px(y_val)
            svg += f'  <line x1="{margin["left"]}" y1="{y:.2f}" x2="{width - margin["right"]}" y2="{y:.2f}" stroke="#ddd" stroke-width="1"/>\n'
            svg += f'  <text x="{margin["left"] - 8}" y="{y + 4:.2f}" font-size="11" fill="#666" text-anchor="end">{y_val:.3g}</text>\n'

        svg += f'  <line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{height - margin["bottom"]}" stroke="#333" stroke-width="2"/>\n'
        svg += f'  <line x1="{margin["left"]}" y1="{height - margin["bottom"]}" x2="{width - margin["right"]}" y2="{height - margin["bottom"]}" stroke="#333" stroke-width="2"/>\n'

        for ds_idx, ds in enumerate(datasets):
            color = colors[ds_idx % len(colors)]
            points = ds.get('data', [])

            if chart_type == 'bar':
                bar_width = chart_w / len(points) * 0.7 if points else 20
                for i, point in enumerate(points):
                    y_val = point[1] if isinstance(point, (list, tuple)) else point
                    x = x_px(i) - bar_width / 2 + (chart_w / len(points)) * 0.15
                    y = y_px(y_val)
                    h = (height - margin['bottom']) - y
                    if h < 0:
                        y = height - margin['bottom']
                        h = -h
                    svg += f'  <rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{h:.2f}" fill="{color}" opacity="0.8">\n'
                    svg += f'<title>{ds.get("label", "")}: {y_val:.3g}</title></rect>\n'

            elif chart_type == 'area':
                if len(points) > 1:
                    path_data = f'M {x_px(0):.2f} {height - margin["bottom"]:.2f} '
                    for i, point in enumerate(points):
                        y_val = point[1] if isinstance(point, (list, tuple)) else point
                        path_data += f'L {x_px(i):.2f} {y_px(y_val):.2f} '
                    path_data += f'L {x_px(len(points)-1):.2f} {height - margin["bottom"]:.2f} Z'
                    svg += f'  <path d="{path_data}" fill="{color}" opacity="0.3"/>\n'

                    path_data = 'M '
                    for i, point in enumerate(points):
                        y_val = point[1] if isinstance(point, (list, tuple)) else point
                        if i == 0:
                            path_data += f'{x_px(i):.2f} {y_px(y_val):.2f}'
                        else:
                            path_data += f' L {x_px(i):.2f} {y_px(y_val):.2f}'
                    svg += f'  <path d="{path_data}" fill="none" stroke="{color}" stroke-width="2"/>\n'

            else:
                if len(points) > 1:
                    path_data = 'M '
                    for i, point in enumerate(points):
                        y_val = point[1] if isinstance(point, (list, tuple)) else point
                        if i == 0:
                            path_data += f'{x_px(i):.2f} {y_px(y_val):.2f}'
                        else:
                            path_data += f' L {x_px(i):.2f} {y_px(y_val):.2f}'
                    svg += f'  <path d="{path_data}" fill="none" stroke="{color}" stroke-width="2">\n'
                    svg += f'<title>{ds.get("label", "")}</title></path>\n'

                for i, point in enumerate(points):
                    y_val = point[1] if isinstance(point, (list, tuple)) else point
                    x = x_px(i)
                    y = y_px(y_val)
                    svg += f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" stroke="#fff" stroke-width="1">\n'
                    svg += f'<title>{ds.get("label", "")}: ({i}, {y_val:.3g})</title></circle>\n'

        if x_label:
            svg += f'  <text x="{width/2}" y="{height - 20}" font-size="12" fill="#333" text-anchor="middle">{x_label}</text>\n'

        if y_label:
            svg += f'  <text x="20" y="{height/2}" font-size="12" fill="#333" text-anchor="middle" transform="rotate(-90, 20, {height/2})">{y_label}</text>\n'

        if show_legend and datasets:
            legend_x = margin['left']
            legend_y = margin['top'] - 10
            for ds_idx, ds in enumerate(datasets):
                color = colors[ds_idx % len(colors)]
                label = ds.get('label', f'Dataset {ds_idx + 1}')
                svg += f'  <rect x="{legend_x}" y="{legend_y - 12}" width="14" height="14" fill="{color}"/>\n'
                svg += f'  <text x="{legend_x + 20}" y="{legend_y}" font-size="12" fill="#333">{label}</text>\n'
                legend_x += len(label) * 8 + 40

        svg += self._create_svg_footer()
        return svg

    def render_energy_chart(self, energy_history: List[Dict],
                            width: int = 800, height: int = 400,
                            background: str = None) -> str:
        """渲染能量图表

        Args:
            energy_history: 能量历史 [{step, time, kinetic, potential, total}, ...]
            width: 画布宽度
            height: 画布高度
            background: 背景颜色

        Returns:
            SVG字符串
        """
        datasets = [
            {'label': '动能 (J)', 'data': [(e['time'], e.get('kinetic', 0)) for e in energy_history]},
            {'label': '势能 (J)', 'data': [(e['time'], e.get('potential', 0)) for e in energy_history]},
            {'label': '总能量 (J)', 'data': [(e['time'], e.get('total', 0)) for e in energy_history]},
        ]

        data = {
            'datasets': datasets,
            'x_labels': [f"{e['time']:.2f}" for e in energy_history]
        }

        return self.render_chart(
            data, chart_type='line',
            width=width, height=height, background=background,
            title='能量 - 时间图',
            x_label='时间 (s)', y_label='能量 (J)',
            show_legend=True,
            colors=['#2196F3', '#FF9800', '#4CAF50']
        )

    def _draw_grid(self, width: int, height: int, grid_size: int = 50) -> str:
        """绘制网格"""
        lines = ''
        for x in range(0, width, grid_size):
            lines += f'  <line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#ddd" stroke-width="0.5"/>\n'
        for y in range(0, height, grid_size):
            lines += f'  <line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#ddd" stroke-width="0.5"/>\n'
        return lines

    def _draw_axes(self, width: int, height: int, cx: float, cy: float) -> str:
        """绘制坐标轴"""
        return f'''  <line x1="0" y1="{cy}" x2="{width}" y2="{cy}" stroke="#999" stroke-width="1" stroke-dasharray="5,5"/>
  <line x1="{cx}" y1="0" x2="{cx}" y2="{height}" stroke="#999" stroke-width="1" stroke-dasharray="5,5"/>
  <text x="{width - 15}" y="{cy - 5}" font-size="11" fill="#999">X</text>
  <text x="{cx + 5}" y="15" font-size="11" fill="#999">Y</text>
'''

    def render_svg_to_data_uri(self, svg: str) -> str:
        """将SVG转换为data URI"""
        import base64
        encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f'data:image/svg+xml;base64,{encoded}'

    def render_text(self, text: str, x: float, y: float,
                    font_size: int = 14, color: str = '#333',
                    font_family: str = 'sans-serif',
                    text_anchor: str = 'start') -> str:
        """渲染文本"""
        return f'<text x="{x}" y="{y}" font-size="{font_size}" fill="{color}" font-family="{font_family}" text-anchor="{text_anchor}">{text}</text>\n'

    def render_rect(self, x: float, y: float, w: float, h: float,
                    fill: str = '#fff', stroke: str = '#333',
                    stroke_width: float = 1, radius: float = 0) -> str:
        """渲染矩形"""
        if radius > 0:
            return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" rx="{radius}" ry="{radius}"/>\n'
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'

    def render_circle(self, cx: float, cy: float, r: float,
                      fill: str = '#FF5722', stroke: str = '#E64A19',
                      stroke_width: float = 2) -> str:
        """渲染圆形"""
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'

    def render_line(self, x1: float, y1: float, x2: float, y2: float,
                    stroke: str = '#333', stroke_width: float = 2,
                    dashed: bool = False) -> str:
        """渲染线条"""
        dash = ' stroke-dasharray="5,3"' if dashed else ''
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>\n'

    def save_svg(self, svg: str, filepath: str) -> bool:
        """保存SVG到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg)
            logger.info(f"SVG保存成功: {filepath}")
            return True
        except Exception as e:
            logger.error(f"SVG保存失败: {str(e)}")
            return False


render_engine_service = RenderEngineService()
