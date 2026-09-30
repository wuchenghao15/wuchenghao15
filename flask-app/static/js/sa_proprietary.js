/**
 * sa_proprietary.js  —— SA 专有 UI 热插拔控制器 (v24.3.3)
 * 两种模式（按 body[data-auth-stage] 自动识别）：
 *
 * A) SA 专用页模式（/sa/dashboard，data-auth-stage = pre_auth | full_auth）
 *    · full_auth：心跳 /api/hardware/dual-status（登录态完整载荷）
 *        - 任一密钥离线 / 401 → 立即跳 /index?from=sa_dual_lost（自动登出）
 *    · pre_auth：心跳 ?hardware_only=1（仅硬件在位布尔，loopback 限定）
 *        - 密钥拔出 → 立即跳 /index?from=sa_no_keys
 *    · 注：server 端在 should_redirect=False 时已 302→/index，前端此 JS 是补充
 *          （会话中途密钥拔出的"主动检测"，不依赖下一次 HTTP 请求才触发）
 *
 * B) 标准页模式（无 data-auth-stage：首页/base/admin 等，legacy 行为）
 *    · 5s 心跳；双钥 true→false：≤10s 内锁定遮罩 + body 切 STANDARD
 *    · 双钥 false→true：恢复 SA_PROPRIETARY 布局
 *    · SA 已登录 + 双钥在线且当前在 / 或 /index → 自动跳转 /sa/dashboard（页面级切换）
 *    · 连续失败指数退避：5 → 10 → 20 → 40 → 60（max）；成功一次立刻重置 5s
 */
(function () {
  'use strict';
  var BASE_INTERVAL = 5000;   // 5s 心跳
  var MAX_INTERVAL = 60000;   // 60s 退避上限
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
  var lastBoth = null;        // legacy: null | true | false
  var lockShown = false;
  var lockTimer = null;       // legacy: 拔出 → ≤10s 锁定计时器
  var exiting = false;        // dedicated: 已触发跳首页（一次性，防重复）

  /** 注入顶栏三模块占位：如果模板已有，就不覆盖 */
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

  function backoff(err) {
    consecutiveErrors = err ? Math.min(consecutiveErrors + 1, 5) : 0;
    if (err) {
      var mul = Math.pow(2, consecutiveErrors - 1);
      interval = Math.min(BASE_INTERVAL * mul, MAX_INTERVAL);
    } else {
      interval = BASE_INTERVAL;
    }
  }

  /* ════════ A) SA 专用页模式：密钥离线 → 先播退出动画再跳首页 ════════ */

  function exitToHome(reason, doLogout) {
    if (exiting) return;
    exiting = true;
    var target = doLogout ? '/auth/logout?from=sa_dual_lost' : '/index?from=' + (reason || 'sa_no_keys');
    fireLayoutEvent({ mode: 'EXIT', reason: reason || 'dual_key_lost', stage: authStage() });

    // 先播放退出动画（body 加 .sa-exit + 锁定遮罩脉冲），等动画播完再跳页
    var b = body();
    b.classList.remove('sa-enter');
    b.classList.add('sa-exit');
    setLocked(true, reason === 'sa_dual_lost' ? '双密钥已断开，正在安全退出…' : 'SA 会话已锁定，即将返回首页…');

    setTimeout(function () {
      try { window.location.replace(target); }
      catch (e) { window.location.href = target; }
    }, 700);  // 与 .sa-exit (0.65s) + 遮罩入场 (0.08s) 匹配，留 60ms 余量
  }

  function applyDedicated(p, ok, status) {
    if (exiting) return;
    var stage = authStage();
    if (stage === 'full_auth') {
      var both = !!(ok && p && p.both_authenticated);
      if (!both) {
        // 登录态：密钥离线 / 401 / 服务端判失败 → 登出回首页
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
    // 其他（无 data-auth-stage / locked_nokeys 已删）→ 不处理
  }

  /* ════════ B) 标准页模式（legacy） ════════ */

  function applyTransition(p) {
    var both = !!(p && p.both_authenticated);
    var layout = (p && p.layout_mode) || 'STANDARD';

    // 满足条件自动切换：SA 已登录 + 双钥在线 + 当前在首页 → 页面级跳转 SA 专用页
    if (p && p.is_sa && both) {
      var path = window.location.pathname || '/';
      if (path === '/' || path === '/index') {
        if (timer) { clearTimeout(timer); timer = null; }
        window.location.replace('/sa/dashboard');
        return;
      }
    }

    // 初始化 lastBoth
    if (lastBoth === null) lastBoth = both;

    // true → false：启动 10s 锁定计时
    if (lastBoth && !both) {
      if (!lockTimer) {
        lockTimer = setTimeout(function () {
          setLayout('STANDARD');
          setLocked(true, (p && p.error) || '双密钥已断开，请重新插入 VIKEY 和 SZU100。');
          lockShown = true;
          fireLayoutEvent({ mode: 'STANDARD', reason: 'dual_key_lost', payload: p });
        }, Math.max(0, 10000 - (interval - BASE_INTERVAL)));
      }
    }
    // false → true：清除锁定
    if (!lastBoth && both) {
      if (lockTimer) { clearTimeout(lockTimer); lockTimer = null; }
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
    var url = isDedicatedPage() && authStage() !== 'full_auth'
      ? API + '?hardware_only=1'
      : API;
    req.open('GET', url, true);
    req.timeout = Math.min(interval, 8000);
    req.onreadystatechange = function () {
      if (req.readyState !== 4) return;
      var ok = req.status >= 200 && req.status < 300;
      var p = null;
      try { p = JSON.parse(req.responseText || '{}'); } catch (e) { p = null; ok = false; }
      if (isDedicatedPage()) {
        // 专用页：退避不影响响应及时性，保持 5s
        applyDedicated(p, ok, req.status);
      } else {
        backoff(!ok);
        if (ok && p) applyTransition(p);
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
