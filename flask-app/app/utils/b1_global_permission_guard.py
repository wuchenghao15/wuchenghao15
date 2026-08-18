#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B轮议题1产出: 全局权限装饰器兜底拦截器 (P0修复版)
flow_id: flow_full_repair_20260818_001 / flow_test_repair_20260818_002
基于 mt_route_decorator_audit 表做无装饰器路由的权限校验, 避免修改943个源文件

P0修复 (测试报告 TEST_20260818_104856 驱动, 通过率80.6%→目标≥90%):
  ① 三段式匹配: 精确路由 > 多段通配 > 单段通配(最低优先级, 且role!=guest)
     → 解决 catch-all 单段路由 /<path:copy_key> /<test_id> 正则 ^/[^/]+$ 过宽匹配
       导致 /index /home 误拦401、不存在路径返回401而非404
  ② category分支响应 (建2·EF安全架构):
     page_* 未登录 → 302重定向登录页 (UX友好, 非abort401)
     api_*  未登录 → 401 JSON (前端fetch需明确状态码)
     static/guest级 → 放行
  ③ 单段通配命中时校验Flask真实路由存在性 (建1·EF战略组长 架构层消除误匹配):
     非真实路由 → 不拦截, 让Flask自然404
专家意见融合: 建1+专1(单段合法不排除改精确优先) + 专5(catch-all不删改精确优先) + 建2(category分支)
"""


def _b1_register_global_permission_guard(app):
    """注册B轮议题1全局权限拦截器 (P0三段式+category分支修复)"""
    import sqlite3, re
    from flask import request, session, redirect, jsonify

    _AUDIT_DB = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/ai_engines/app.db'
    _STATIC_PREFIXES = ('/static/', '/assets/', '/favicon', '/css/', '/js/',
                        '/img/', '/images/', '/fonts/', '/webfonts/',
                        '/.well-known/', '/robots.txt', '/sitemap.xml')
    # 公开认证路由白名单: 这些路由天然面向匿名用户(登录/注册/校验/找回密码/会话健康),
    # 审计表将其标为 suggested_role='login'/category='unknown', 若不在此处短路放行,
    # _derive_category 会把 /auth/login 归为 page_general → 未登录 302 重定向到 '/',
    # 导致登录端点完全不可达(用户看到"用户名或密码错误"实为 fetch 拿到 HTML 重定向体)。
    _PUBLIC_AUTH_PATHS = {
        '/auth/login', '/auth/logout', '/auth/register', '/auth/check_username',
        '/auth/check_password', '/auth/validate', '/auth/forgot_password',
        '/auth/session_health', '/login', '/register', '/forgot_password',
        '/forgot-password', '/admin_app/login', '/admin_app/logout',
    }
    # 三段式缓存: None=未加载, dict含 exact/multi_wild/single_wild 三层
    _ROUTE_TIERS = None
    # Flask真实路由正则缓存 (用于单段通配命中后校验路由存在性)
    _FLASK_RULE_PATS = None

    def _compile_route_regex(route_path):
        """将Flask路由转为正则: <int:id> <path:filename> <id> → [^/]+"""
        pat = re.sub(r'<[^>]+>', '[^/]+', route_path)
        return '^' + pat + '$'

    def _is_single_segment_wild(route_path):
        """判断是否单段通配路由: 整个路径就是单个<...>参数, 如 /<path:copy_key> /<test_id>

        这类路由生成正则 ^/[^/]+$ 会匹配所有单段路径, 是catch-all误匹配的根因.
        """
        return re.match(r'^/<[^>]+>$', route_path) is not None

    def _load_route_tiers():
        """加载审计表为三层: exact(精确) / multi_wild(多段通配) / single_wild(单段通配)"""
        nonlocal _ROUTE_TIERS
        if _ROUTE_TIERS is not None:
            return _ROUTE_TIERS
        tiers = {'exact': [], 'multi_wild': [], 'single_wild': []}
        try:
            conn = sqlite3.connect("file:" + _AUDIT_DB + "?mode=ro", uri=True, timeout=2)
            cur = conn.cursor()
            cur.execute("""
                SELECT route_path, suggested_role, category
                FROM mt_route_decorator_audit
                WHERE flow_id='flow_full_repair_20260818_001'
            """)
            for rp, role, cat in cur.fetchall():
                entry = (rp, role, cat, _compile_route_regex(rp))
                if '<' not in rp:
                    tiers['exact'].append(entry)
                elif _is_single_segment_wild(rp):
                    tiers['single_wild'].append(entry)
                else:
                    tiers['multi_wild'].append(entry)
            conn.close()
        except Exception:
            pass
        _ROUTE_TIERS = tiers
        return tiers

    def _load_flask_rules():
        """加载Flask app真实注册路由的正则, 用于校验单段通配命中是否为真实路由

        (建1·EF战略组长: 让Flask先确定路由存在性, 404自然处理, 架构层消除catch-all误匹配)
        """
        nonlocal _FLASK_RULE_PATS
        if _FLASK_RULE_PATS is not None:
            return _FLASK_RULE_PATS
        pats = []
        try:
            for rule in app.url_map.iter_rules():
                pat = re.sub(r'<[^>]+>', '[^/]+', rule.rule)
                pats.append('^' + pat + '$')
        except Exception:
            pass
        _FLASK_RULE_PATS = pats
        return pats

    def _is_real_flask_route(path):
        """判断path是否匹配Flask真实注册的某条路由"""
        for pat in _load_flask_rules():
            if re.match(pat, path):
                return True
        return False

    def _match_route_role(path):
        """三段式匹配: exact(精确) > multi_wild(多段通配) > single_wild(单段通配,最低优先级)

        单段通配仅当 suggested_role != 'guest' 且 path 是Flask真实路由时才命中,
        避免不存在路径被误判需登录(专1: 单段路由合法不排除; 专5: catch-all不删改精确优先).
        """
        tiers = _load_route_tiers()
        # 第一优先级: 精确路由 (如 /admin/dashboard /student/home)
        for rp, role, cat, pat in tiers['exact']:
            if re.match(pat, path):
                return role, cat, rp
        # 第二优先级: 多段通配路由 (如 /static/<path:filename> /api/<flow_id>/advance)
        for rp, role, cat, pat in tiers['multi_wild']:
            if re.match(pat, path):
                return role, cat, rp
        # 第三优先级(最低): 单段通配 (如 /<path:copy_key> /<test_id>)
        for rp, role, cat, pat in tiers['single_wild']:
            if role == 'guest':
                continue  # guest级单段通配直接放行(不参与拦截)
            if re.match(pat, path):
                # 单段通配命中后, 校验是否为Flask真实路由
                # 非真实路由(如/this_does_not_exist) → 不拦截, 让Flask自然404
                if _is_real_flask_route(path):
                    return role, cat, rp
                continue
        return None, None, None

    def _user_role_level(role):
        """session.role → 数字等级"""
        _LEVELS = {
            'guest': 0, 'login': 1, 'student': 2, 'student_vip': 2,
            'parent': 2, 'adult_student': 2,
            'teacher': 3, 'teaching_leader': 3, 'academic_affairs': 3,
            'principal': 4, 'operator': 3,
            'admin': 4, 'super_admin': 5,
        }
        return _LEVELS.get(role, 0)

    def _required_level(suggested_role):
        """suggested_role → 数字等级"""
        _LEVELS = {'guest': 0, 'login': 1, 'admin': 4, 'super_admin': 5}
        return _LEVELS.get(suggested_role, 1)

    def _is_api_category(cat):
        return bool(cat) and cat.startswith('api_')

    def _is_page_category(cat):
        return bool(cat) and cat.startswith('page_')

    def _derive_category(path, cat):
        """运行时category推导 (P0修复: 解决扫描器unknown占65%导致分支响应失效)

        扫描器分类规则过窄 → /exam/<id> /<test_id> /download/<fid> 等落入unknown
        本函数在audit category为unknown/空时按path前缀推导:
          /api/*    → api_general  (前端fetch需401JSON)
          /admin/*  → page_admin   (302重定向登录)
          /student/* → page_student
          /mobile/* → page_mobile
          / /index /home → page_home
          其他      → page_general (默认按页面处理, 302重定向, UX友好)
        """
        if cat and cat != 'unknown':
            return cat
        if not path:
            return 'page_general'
        p = path.lower()
        if p.startswith('/api/'):
            return 'api_general'
        if p.startswith('/admin/') or p == '/admin':
            return 'page_admin'
        if p.startswith('/student/'):
            return 'page_student'
        if p.startswith('/mobile/'):
            return 'page_mobile'
        if p in ('/', '/index', '/home'):
            return 'page_home'
        # 默认按页面处理 (非API路由多数为HTML, 302重定向对UX更友好)
        return 'page_general'

    @app.before_request
    def _b1_global_permission_guard():
        """全局权限拦截器 (P0三段式+category分支): 无装饰器路由按审计表兜底校验"""
        # 静态资源直接放行
        path = request.path
        if any(path.startswith(p) for p in _STATIC_PREFIXES):
            return None
        # 公开认证路由强制放行 (登录/注册/校验/找回密码/会话健康等天然面向匿名用户)
        if path in _PUBLIC_AUTH_PATHS:
            return None
        # 三段式匹配审计表
        suggested_role, category, rp = _match_route_role(path)
        if not suggested_role:
            # 未在审计表 或 单段通配但非真实路由 → 放行(Flask 404自然处理)
            return None
        required = _required_level(suggested_role)
        if required == 0:
            return None  # guest级直接放行
        # P0修复: 运行时推导category (解决扫描器unknown占65%问题)
        category = _derive_category(path, category)
        # 读取session角色
        try:
            user_role = session.get('role', '') if session else ''
        except Exception:
            user_role = ''
        is_api = _is_api_category(category)
        is_page = _is_page_category(category)
        # 未登录 → 按category分支 (建2·EF安全架构: page→302重定向, api→401JSON)
        if not user_role:
            if is_api:
                return jsonify({'code': 401, 'msg': '未登录', 'data': {}}), 401
            if is_page:
                return redirect('/')  # 302重定向到首页登录
            from flask import abort
            abort(401)  # 兜底: unknown类别未登录
        # 已登录但权限不足 → 越权拦截 (建5·AI安全专家: student→/admin/* 必403)
        user_level = _user_role_level(user_role)
        if user_level < required:
            if is_api:
                return jsonify({'code': 403, 'msg': '权限不足', 'data': {}}), 403
            if is_page:
                from flask import abort
                abort(403)  # 403异常页
            from flask import abort
            abort(403)
        return None

    return app
