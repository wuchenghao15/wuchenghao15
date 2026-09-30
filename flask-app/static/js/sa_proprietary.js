/**
 * sa_proprietary.js  —— SA 专有 UI 热插拔控制器 (v24.3.4 · 低延迟)
 *
 * 延迟优化（v24.3.4）：
 *   - BASE_INTERVAL: 5000ms → 2000ms（2s 心跳，安全场景快速响应）
 *   - 删除 legacy 模式 10s lockTimer → 检测到 both=false 立即锁定/跳转
 *   - backoff 仅在网络错误时触发，密钥在位=false 不退避（保持 2s 固定间隔）
 *   - 专用页 exitToHome 延迟 700ms → 400ms（更快跳转）
 *
 * 两种模式（按 body[data-auth-stage] 自动识别）：
 *
 * A) SA 专用页模式（/sa/dashboard，data-auth-stage = pre_auth | full_auth）
 *    · full_auth：心跳 /api/hardware/dual-status（登录态完整载荷）
 *        - 任一密钥离线 / 401 → 立即锁定遮罩 + 400ms 后 /auth/logout 登出回首页
 *    · pre_auth：心跳 ?hardware_only=1（仅硬件在位布尔，loopback 限定）
 *        - 密钥拔出 → 立即锁定遮罩 + 400ms 后回首页
 *
 * B) 标准页模式（无 data-auth-stage：首页/base/admin 等）
 *    · 2s 心跳 ?hardware_only=1（guest 也能拿到真实双钥在位布尔）
 *    · 双钥在线 + 当前在 / 或 /index → 自动跳转 /sa/dashboard
 *    · 双钥离线（已在 SA 页面的例外）→ 立即 setLocked + setLayout STANDARD
 */
(function () {
  'use strict';
  var BASE_INTERVAL = 2000;   // 2s 心跳（v24.3.4: 5000→2000，安全场景快速响应）
  var MAX_INTERVAL = 30000;   // 30s 退避上限（原 60s）
  var API = '/api/hardware/dual-status';

  function body() { return document.body || document.documentElement; }
  function authStage() {
    var b = body();
    return (b && b.getAttribute && b.getAttribute('data-auth-stage')) || '';
  }
  function isDedicatedPage() { return !!authStage(); }
  function setLayout(mode) {
    var b = body();
    ['SA_PROPRIETARY', 'STANDARD'].forEach(function (m) {
      b.classList.toggle('layout-mode-' + m, mode === m);
    });
    b.setAttribute('data-layout-mode', mode || 'STANDARD');
  }
  function setLocked(state, reason) {
    var b = body();
    b.classList.toggle('sa-lock', !!state);
    var ov = document.getElementById('sa-lock-overlay');
    if (!state) {
      if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
      return;
    }
    if (!ov) {
      ov = document.createElement('div');
      ov.id = 'sa-lock-overlay';
      ov.setAttribute('role', 'dialog');
      ov.setAttribute('aria-modal', 'true');
      ov.innerHTML =
        '<div class="card">' +
          '<div class="title"><span class="pulse"></span>SA 会话已锁定</div>' +
          '<div class="sub" id="sa-lock-reason">请重新插入 VIKEY 加密狗 和 SZU100 专用U盘。</div>' +
        '</div>';
      document.body.appendChild(ov);
    }
    var txt = document.getElementById('sa-lock-reason');
    if (txt) {
      txt.textContent = reason || '请重新插入 VIKEY 加密狗 和 SZU100 专用U盘。';
    }
  }
  function fireLayoutEvent(detail) {
    try {
      var e;
      if (typeof CustomEvent === 'function') {
        e = new CustomEvent('sa-layout-updated', { detail: detail, bubbles: true });
      } else {
        e = document.createEvent('CustomEvent');
        e.initCustomEvent('sa-layout-updated', true, false, detail);
      }
      document.dispatchEvent(e);
      window.dispatchEvent(e);
    } catch (err) { /* 忽略派发异常 */ }
  }
  function currentMode() {
    var b = body();
    if (b.classList.contains('layout-mode-SA_PROPRIETARY')) return 'SA_PROPRIETARY';
    return 'STANDARD';
  }

  var interval = BASE_INTERVAL;
  var timer = null;
  var consecutiveErrors = 0;
  var lastBoth = null;
  var lockShown = false;
  var exiting = false;

  /** 顶栏三模块占位注入 */
  function ensureTopbarModules() {
    var b = body();
    if (!b.classList.contains('layout-mode-SA_PROPRIETARY')) return;
    var panelId = 'sa-topbar-modules';
    if (document.getElementById(panelId)) return;
    var host = document.querySelector('.topbar, .art-header, .sa-topbar .brand');
    if (!host) return;
    var wrap = document.createElement('div');
    wrap.id = panelId;
    wrap.className = 'sa-topbar-modules';
    wrap.innerHTML =
      '<span class="sa-hw-panel" id="sa-hardware-panel" style="display:none">' +
        '<span class="sa-hw-chip vikey"><span class="sa-lock"></span><i class="fas fa-key" aria-hidden="true"></i> <span id="sa-vikey-txt">VIKEY</span></span>' +
        '<span class="sa-hw-chip szu100"><span class="sa-lock"></span><i class="fas fa-usb" aria-hidden="true"></i> <span id="sa-szu100-txt">SZU100</span></span>' +
      '</span>' +
      '<span class="sa-ef-panel" title="EigenFlux 专家已连接">' +
        '<i class="fas fa-users" aria-hidden="true"></i> EF 专家 <span class="num" id="sa-ef-count">12</span>' +
      '</span>' +
      '<span class="sa-daemon-bar" title="自动化 daemon 健康度">' +
        '<i class="fas fa-server" aria-hidden="true"></i> ' +
        '<span class="track"><span class="fill" id="sa-daemon-fill" style="width:100%"></span></span> ' +
        '<span id="sa-daemon-txt">34/34</span>' +
      '</span>';
    host.prepend ? host.prepend(wrap) : host.insertBefore(wrap, host.firstChild);
  }

  /**
   * 退避：仅网络错误时触发（req.status >= 500 / timeout / onerror）。
   * 密钥在位=false 是正常业务状态，不退避——保持 2s 固定间隔快速响应。
   */
  function backoff(networkErr) {
    consecutiveErrors = networkErr ? Math.min(consecutiveErrors + 1, 5) : 0;
    if (networkErr) {
      var mul = Math.pow(2, consecutiveErrors - 1);
      interval = Math.min(BASE_INTERVAL * mul, MAX_INTERVAL);
    } else {
      interval = BASE_INTERVAL;
    }
  }

  /* ════════ A) SA 专用页模式 ════════ */

  function exitToHome(reason, doLogout) {
    if (exiting) return;
    exiting = true;
    var target = doLogout ? '/auth/logout?from=sa_dual_lost' : '/index?from=' + (reason || 'sa_no_keys');
    fireLayoutEvent({ mode: 'EXIT', reason: reason || 'dual_key_lost', stage: authStage() });
    var b = body();
    b.classList.remove('sa-enter');
    b.classList.add('sa-exit');
    setLocked(true, reason === 'sa_dual_lost' ? '双密钥已断开，正在安全退出…' : 'SA 会话已锁定，即将返回首页…');
    setTimeout(function () {
      try { window.location.replace(target); }
      catch (e) { window.location.href = target; }
    }, 400);  // v24.3.4: 700→400ms，更快跳转
  }

  function applyDedicated(p, ok, status) {
    if (exiting) return;
    var stage = authStage();
    if (stage === 'full_auth') {
      var both = !!(ok && p && p.both_authenticated);
      if (!both) {
        exitToHome('sa_dual_lost', true);
      }
      return;
    }
    if (stage === 'pre_auth') {
      var present = !!(ok && p && p.both_present);
      if (!present) {
        exitToHome('sa_no_keys', false);
      }
      return;
    }
  }

  /* ════════ B) 标准页模式 ════════ */

  function applyTransition(p) {
    var both = !!(p && p.both_authenticated);
    var layout = (p && p.layout_mode) || 'STANDARD';

    // 自动跳转：双钥在线 + 当前在首页 → 立即跳 /sa/dashboard
    if (both) {
      var path = window.location.pathname || '/';
      if (path === '/' || path === '/index') {
        if (timer) { clearTimeout(timer); timer = null; }
        window.location.replace('/sa/dashboard');
        return;
      }
    }

    // v24.3.4: 删除 legacy 10s lockTimer — 检测到 both=false 立即锁定
    if (lastBoth === null) lastBoth = both;

    if (lastBoth && !both) {
      // 双钥刚离线：立即锁定 + STANDARD 布局（不再等 10s）
      setLayout('STANDARD');
      setLocked(true, (p && p.error) || '双密钥已断开，请重新插入 VIKEY 和 SZU100。');
      lockShown = true;
      fireLayoutEvent({ mode: 'STANDARD', reason: 'dual_key_lost', payload: p });
    } else if (!lastBoth && both) {
      // 双钥刚恢复：清除锁定 + SA 布局
      setLocked(false);
      lockShown = false;
      setLayout(layout);
      ensureTopbarModules();
      fireLayoutEvent({ mode: layout, reason: 'dual_key_restored', payload: p });
    }
    if (both) {
      ensureTopbarModules();
      var panel = document.getElementById('sa-hardware-panel');
      if (panel) panel.style.display = 'inline-flex';
    } else {
      setLayout('STANDARD');
    }
    lastBoth = both;
  }

  /* ════════ 心跳轮询 ════════ */

  function tick() {
    var req;
    try { req = new XMLHttpRequest(); } catch (e) { return; }
    // 专用页 full_auth 走完整载荷；其余（专用页未登录 + 标准页）走 hardware_only
    var url;
    if (isDedicatedPage()) {
      url = authStage() === 'full_auth' ? API : API + '?hardware_only=1';
    } else {
      url = API + '?hardware_only=1';
    }
    req.open('GET', url, true);
    req.timeout = Math.min(interval, 5000);
    req.onreadystatechange = function () {
      if (req.readyState !== 4) return;
      var ok = req.status >= 200 && req.status < 300;
      var p = null;
      try { p = JSON.parse(req.responseText || '{}'); } catch (e) { p = null; ok = false; }

      if (isDedicatedPage()) {
        applyDedicated(p, ok, req.status);
        // 专用页不退避 — 退出由 exitToHome 控制，正常响应保持 2s
        if (!ok) backoff(true); else interval = BASE_INTERVAL;
      } else {
        // 标准页：硬件在位=false 是正常业务状态，不退避
        var _both = false;
        var networkErr = false;
        if (ok && p) {
          if (p.hardware_only) _both = !!p.both_present;
          else _both = !!p.both_authenticated;
        } else {
          networkErr = true;
        }
        if (networkErr) {
          backoff(true);  // 仅网络错误退避
        } else {
          interval = BASE_INTERVAL;  // 正常 + 密钥离线/在线都保持 2s
        }
        var _compat = p ? {
          both_authenticated: _both,
          is_sa: !!p.is_sa,
          layout_mode: p.layout_mode,
          error: p.error,
        } : null;
        if (_compat) applyTransition(_compat);
      }
      schedule();
    };
    req.onerror = function () {
      if (isDedicatedPage()) { exitToHome('sa_network_error', false); return; }
      backoff(true); schedule();
    };
    req.ontimeout = function () {
      if (isDedicatedPage()) { exitToHome('sa_timeout', false); return; }
      backoff(true); schedule();
    };
    try { req.send(null); } catch (e) {
      if (isDedicatedPage()) { exitToHome('sa_send_error', false); return; }
      backoff(true); schedule();
    }
  }

  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(tick, interval);
  }

  function start() {
    try {
      if (isDedicatedPage()) {
        schedule();
      } else {
        lastBoth = body().classList.contains('layout-mode-SA_PROPRIETARY');
        if (lastBoth) ensureTopbarModules();
        schedule();
      }
    } catch (e) { /* 静默失败 */ }
  }

  window.SAUIManager = {
    start: start,
    refresh: tick,
    setLocked: setLocked,
    getState: function () {
      return {
        mode: currentMode(),
        stage: authStage(),
        dedicated: isDedicatedPage(),
        lastBoth: lastBoth,
        lockShown: lockShown,
        exiting: exiting,
        interval: interval,
      };
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
