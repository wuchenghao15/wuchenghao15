"""
CTC Detector · 闭合类时曲线检测
爱因斯坦：Blueprint 之间的 circular dep = 闭合类时曲线 (Closed Timelike Curve) = 时间旅行
规则：每个 Blueprint 只能依赖「过去」的 Blueprint，不能依赖「未来」的

Usage:
    from ai_engines.ctc_detector import CTCDetector
    detector = CTCDetector()
    report = detector.detect_flask_blueprints(app)
    # report = {"cycles": [["bp_a", "bp_b", "bp_a"]], "dep_graph": {...}, "safe": bool}
"""

import os
import re
import sys
import importlib


class CTCDetector:
    """Flask Blueprint 依赖图 · 闭合类时曲线 (CTC) 检测器

    用 DFS 三色标记（白/灰/黑）检测有向图中的环。
    白 = 未访问, 灰 = 当前递归栈, 黑 = 已完成。
    灰节点发现邻居也是灰 → 发现 CTC（时间旅行）。
    """

    def __init__(self):
        self.dep_graph = {}       # bp_name -> set(dep_bp_names)
        self.visited = set()      # 黑节点集合
        self.rec_stack = set()    # 灰节点集合（递归栈）
        self.cycles = []          # 检测到的所有环

    # ── 基础 API ──────────────────────────────────────────────────────

    def add_dependency(self, bp_name, depends_on_bp_name):
        """注册 Blueprint 依赖关系"""
        if bp_name not in self.dep_graph:
            self.dep_graph[bp_name] = set()
        if depends_on_bp_name and depends_on_bp_name != bp_name:
            self.dep_graph[bp_name].add(depends_on_bp_name)

    def scan_module_deps(self, module, bp_name):
        """扫描一个模块的 import 语句，提取对同级 Blueprint 的依赖"""
        try:
            src_path = getattr(module, '__file__', None)
            if not src_path or not os.path.isfile(src_path):
                return
            with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            # 匹配 from blueprints.xxx import / import blueprints.xxx
            # 以及 from routes.xxx import / import routes.xxx
            for m in re.finditer(r'(?:from|import)\s+(blueprints|routes)\.(\w+)', source):
                dep_bp = m.group(2)
                self.add_dependency(bp_name, dep_bp)
            # 也扫描同级 blueprint 目录名 import
            parent_dir = os.path.dirname(os.path.dirname(src_path))
            bp_root = os.path.join(parent_dir, 'blueprints')
            if os.path.isdir(bp_root):
                for entry in os.listdir(bp_root):
                    full = os.path.join(bp_root, entry)
                    if os.path.isdir(full) and os.path.isfile(os.path.join(full, '__init__.py')):
                        bp_candidate = entry
                        if re.search(rf'(?:from|import)\s+blueprints\.{bp_candidate}', source):
                            self.add_dependency(bp_name, bp_candidate)
        except Exception:
            pass

    # ── DFS 环检测 ─────────────────────────────────────────────────────

    def _dfs(self, node, path):
        """DFS 三色标记检测环"""
        self.rec_stack.add(node)
        path.append(node)

        for neighbor in self.dep_graph.get(node, set()):
            if neighbor not in self.dep_graph and neighbor not in self.visited and neighbor not in self.rec_stack:
                # 未注册的邻居 — 把它也加进图避免漏检
                self.dep_graph[neighbor] = set()
            if neighbor in self.rec_stack:
                # 发现灰邻居 → CTC！提取环
                if neighbor in path:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    self.cycles.append(cycle)
            elif neighbor not in self.visited:
                self._dfs(neighbor, path)

        path.pop()
        self.rec_stack.remove(node)
        self.visited.add(node)

    def detect_cycles(self):
        """DFS 检测所有环 (CTC)"""
        self.cycles = []
        self.visited = set()
        self.rec_stack = set()

        # 对所有未访问节点启动 DFS
        all_nodes = set(self.dep_graph.keys())
        for deps in self.dep_graph.values():
            all_nodes.update(deps)

        for node in all_nodes:
            if node not in self.visited:
                self._dfs(node, [])

        # 去重（同一环可能被多次发现）
        unique_cycles = []
        seen_signatures = set()
        for cycle in self.cycles:
            # 标准化签名：从最小元素开始
            min_idx = cycle.index(min(cycle[:-1])) if len(cycle) > 1 else 0
            rotated = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
            sig = tuple(rotated)
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                unique_cycles.append(cycle)
        self.cycles = unique_cycles
        return self.cycles

    # ── Flask app 自动扫描 ─────────────────────────────────────────────

    def detect_flask_blueprints(self, flask_app):
        """从 Flask app 自动扫描所有 Blueprint 及其 import 依赖"""
        self.dep_graph = {}
        self.cycles = []

        # 把 Flask app 注册的所有 Blueprint 节点先加进图
        bp_names = set()
        for bp_name, bp_obj in flask_app.blueprints.items():
            bp_names.add(bp_name)
            self.dep_graph[bp_name] = set()
            # 扫描 Blueprint 模块
            mod = sys.modules.get(bp_obj.import_name)
            if mod is not None:
                self.scan_module_deps(mod, bp_name)

        # 扫描 blueprints/ 目录下的 __init__.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bp_root = os.path.join(base_dir, 'blueprints')
        if os.path.isdir(bp_root):
            for entry in os.listdir(bp_root):
                init_file = os.path.join(bp_root, entry, '__init__.py')
                if os.path.isfile(init_file) and entry not in self.dep_graph:
                    self.dep_graph[entry] = set()
                    # 尝试 import 扫描
                    try:
                        pkg_name = f'blueprints.{entry}'
                        if pkg_name in sys.modules:
                            self.scan_module_deps(sys.modules[pkg_name], entry)
                    except Exception:
                        pass

        # 跑环检测
        self.detect_cycles()
        return self.report()

    # ── 报告 ──────────────────────────────────────────────────────────

    def report(self):
        """返回可读报告 dict"""
        return {
            "cycles": self.cycles,
            "dep_graph": {k: sorted(v) for k, v in sorted(self.dep_graph.items())},
            "safe": len(self.cycles) == 0,
            "bp_count": len(self.dep_graph),
        }
