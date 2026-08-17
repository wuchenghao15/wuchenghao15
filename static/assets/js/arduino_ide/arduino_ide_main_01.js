// Arduino IDE Main JavaScript - Minimal Working Version
// Syntax verified - no template literals
(function() {
  "use strict";

  // ============ BOARDS ============
  var BOARD_NAMES = {
    "uno": "Arduino Uno",
    "nano": "Arduino Nano",
    "mega": "Arduino Mega 2560",
    "leonardo": "Arduino Leonardo",
    "micro": "Arduino Micro",
    "due": "Arduino Due",
    "esp8266": "ESP8266 (NodeMCU)",
    "esp32": "ESP32 DevKit",
    "proMini": "Arduino Pro Mini"
  };

  var COMP_CAT = {
    "input":  { "label": "输入组件", "icon": "fa-arrow-right-to-bracket" },
    "output": { "label": "输出组件", "icon": "fa-arrow-right-from-bracket" },
    "sensor": { "label": "传感器",   "icon": "fa-satellite-dish" },
    "comm":   { "label": "通信",     "icon": "fa-wifi" },
    "power":  { "label": "电源",     "icon": "fa-bolt" },
    "misc":   { "label": "杂项",     "icon": "fa-cube" }
  };

  var TEMPLATE_CAT = {
    "basic":        { "label": "入门基础", "icon": "fa-seedling" },
    "intermediate": { "label": "中级进阶", "icon": "fa-layer-group" },
    "advanced":     { "label": "高级项目", "icon": "fa-rocket" }
  };

  // ============ DEFAULT CODE ============
  var DEFAULT_CODE = "" +
    "// Arduino 基础模板\n" +
    "// 功能: LED闪烁 (引脚13)\n" +
    "\n" +
    "int ledPin = 13;\n" +
    "\n" +
    "void setup() {\n" +
    "  pinMode(ledPin, OUTPUT);\n" +
    "  Serial.begin(9600);\n" +
    "  Serial.println(\"系统启动\");\n" +
    "}\n" +
    "\n" +
    "void loop() {\n" +
    "  digitalWrite(ledPin, HIGH);\n" +
    "  delay(1000);\n" +
    "  digitalWrite(ledPin, LOW);\n" +
    "  delay(1000);\n" +
    "}\n";

  // ============ GLOBAL STATE ============
  var currentBoard = "uno";
  var currentProjectId = null;
  var _componentsFlat = [];
  var _templatesFlat = [];
  var _aiPanelOpen = false;
  var _aiLoading = false;
  var _agentPanelOpen = false;
  var _agentsCache = [];

  // Extended state stubs
  var _undoStack = [];
  var _redoStack = [];
  var _files = {};
  _files["sketch.ino"] = { "type": "ino", "content": DEFAULT_CODE };
  var _pinUsage = {};
  var _watchVars = [];
  var _breakpoints = [];
  var _plotterData = [[], [], [], []];
  var _serialHistory = [];

  // ============ UTILITIES ============
  function escapeHtml(s) {
    s = String(s == null ? "" : s);
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, "&quot;");
  }

  function boardDisplayName(b) {
    return BOARD_NAMES[b] || b || "Arduino Uno";
  }

  function emptyHtml(msg, icon) {
    var ic = icon || "fa-inbox";
    var s = '<div class="empty-text">';
    s += '<i class="fas ' + ic + '" style="font-size:22px;display:block;margin-bottom:8px;color:var(--text-muted);"></i>';
    s += escapeHtml(msg);
    s += '</div>';
    return s;
  }

  function toast(msg, lvl) {
    if (window.ApiRequest && ApiRequest.showToast) {
      ApiRequest.showToast(msg, lvl || "info");
    }
  }

  // ============ SYNTAX HIGHLIGHT ============
  var TOKEN_RE = /(\/\*[\s\S]*?\*\/|\/\/[^\n]*)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|(^[ \t]*#[^\n]*)|\b(void|int|float|double|char|bool|boolean|long|short|byte|unsigned|const|static|volatile|if|else|for|while|do|switch|case|break|continue|return|new|class|struct|public|private|protected|default|sizeof|true|false|HIGH|LOW|INPUT|OUTPUT|INPUT_PULLUP|LED_BUILTIN)\b|\b(setup|loop|pinMode|digitalWrite|digitalRead|analogWrite|analogRead|delay|delayMicroseconds|millis|micros|attachInterrupt|detachInterrupt|map|constrain|random|randomSeed|tone|noTone|pulseIn|shiftOut|begin|end|print|println|write|read|available|flush|peek|attach)\b|\b(Serial|Servo|LiquidCrystal|String|Wire|SPI|EEPROM)\b|\b(0x[0-9a-fA-F]+|\d+\.?\d*)\b/gm;

  function highlightCode(code) {
    var escaped = code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return escaped.replace(TOKEN_RE, function(m, comment, str, pre, kw, fn, cls, num) {
      if (comment) return '<span class="tok-comment">' + comment + '</span>';
      if (str)     return '<span class="tok-string">' + str + '</span>';
      if (pre)     return '<span class="tok-preprocessor">' + pre + '</span>';
      if (kw)      return '<span class="tok-keyword">' + kw + '</span>';
      if (fn)      return '<span class="tok-function">' + fn + '</span>';
      if (cls)     return '<span class="tok-class">' + cls + '</span>';
      if (num)     return '<span class="tok-number">' + num + '</span>';
      return m;
    });
  }

  // ============ EDITOR CORE ============
  function updateEditor() {
    var ta = document.getElementById("code-editor");
    var hl = document.getElementById("highlighted");
    if (!ta || !hl) return;
    hl.innerHTML = highlightCode(ta.value) + "\n";
    updateLineNumbers();
    updateStatusBar();
  }

  function updateLineNumbers() {
    var ta = document.getElementById("code-editor");
    var ln = document.getElementById("line-numbers-inner");
    if (!ta || !ln) return;
    var lines = ta.value.split("\n").length;
    var html = "";
    for (var i = 1; i <= lines; i++) { html += i + "\n"; }
    ln.textContent = html;
  }

  function updateStatusBar() {
    var ta = document.getElementById("code-editor");
    if (!ta) return;
    var s1 = document.getElementById("status-lines");
    var s2 = document.getElementById("status-chars");
    var s3 = document.getElementById("status-board");
    if (s1) s1.textContent = ta.value.split("\n").length;
    if (s2) s2.textContent = ta.value.length;
    if (s3) s3.textContent = boardDisplayName(currentBoard);
  }

  function syncScroll() {
    var ta = document.getElementById("code-editor");
    if (!ta) return;
    var bd = document.getElementById("code-backdrop");
    var ln = document.getElementById("line-numbers-inner");
    if (bd) { bd.scrollTop = ta.scrollTop; bd.scrollLeft = ta.scrollLeft; }
    if (ln) ln.style.transform = "translateY(" + (-ta.scrollTop) + "px)";
  }

  function getEditorCode() {
    var ta = document.getElementById("code-editor");
    return ta ? ta.value : "";
  }

  function setEditorCode(code) {
    var ta = document.getElementById("code-editor");
    if (!ta) return;
    ta.value = code || "";
    updateEditor();
    syncScroll();
  }

  function insertComponent(code) {
    var ta = document.getElementById("code-editor");
    if (!ta) return;
    var start = ta.selectionStart, end = ta.selectionEnd;
    var ins = (code ? code + "\n" : "");
    ta.value = ta.value.substring(0, start) + ins + ta.value.substring(end);
    ta.selectionStart = ta.selectionEnd = start + ins.length;
    ta.focus();
    updateEditor(); syncScroll();
    toast("已插入组件示例代码", "success");
  }

  function loadTemplate(code) {
    if (!confirm("加载模板将覆盖当前编辑器内容，是否继续？")) return;
    setEditorCode(code || "");
    toast("模板代码已加载", "success");
  }

  // ============ TABS / PANELS ============
  function switchTab(panel, tab) {
    var p = document.getElementById(panel + "-panel");
    if (!p) return;
    var btns = p.querySelectorAll(".tab-btn");
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle("active", btns[i].dataset.tab === tab);
    }
    var panes = p.querySelectorAll(".tab-pane");
    for (var j = 0; j < panes.length; j++) {
      var pane = panes[j];
      var match = pane.dataset.tab === tab;
      pane.classList.toggle("active", match);
      pane.style.display = match ? (pane.dataset.tab === "serial" ? "flex" : "block") : "none";
    }
  }

  function togglePanel(panel) {
    var p = document.getElementById(panel + "-panel");
    if (p) p.classList.toggle("collapsed");
  }

  function toggleProjects() {
    var el = document.getElementById("projects-bar");
    if (el) el.classList.toggle("expanded");
  }

  // ============ LOAD COMPONENTS ============
  function loadComponents() {
    var container = document.getElementById("components-list");
    if (!container) return;
    container.innerHTML = '<div class="loading-text"><i class="fas fa-spinner fa-spin"></i> 加载组件中...</div>';
    if (!window.ApiRequest) {
      container.innerHTML = emptyHtml("ApiRequest 未加载", "fa-triangle-exclamation");
      return;
    }
    ApiRequest.get("/api/arduino/components").then(function(res) {
      var data = (res && res.data) || [];
      if (!data.length) { container.innerHTML = emptyHtml("暂无组件数据"); return; }
      var groups = {};
      for (var d = 0; d < data.length; d++) {
        var k = data[d].category || "output";
        if (!groups[k]) groups[k] = [];
        groups[k].push(data[d]);
      }
      var flat = [];
      var html = "";
      var cats = ["input", "output", "sensor", "comm", "power", "misc"];
      for (var c = 0; c < cats.length; c++) {
        var cat = cats[c];
        var meta = COMP_CAT[cat] || { label: cat, icon: "fa-cube" };
        var items = groups[cat] || [];
        if (!items.length) continue;
        html += '<div class="lib-group"><div class="lib-group-title"><i class="fas ' + meta.icon + '"></i> ' + meta.label + '</div>';
        for (var x = 0; x < items.length; x++) {
          var comp = items[x];
          var idx = flat.length;
          flat.push(comp);
          html += '<div class="lib-item" data-idx="' + idx + '" title="' + escapeAttr(comp.description || "") + '">';
          html += '<span class="lib-icon">' + escapeHtml(comp.icon || "\uD83D\uDD0C") + '</span>';
          html += '<div class="lib-info"><div class="lib-name">' + escapeHtml(comp.name) + '</div>';
          html += '<div class="lib-desc">' + escapeHtml(comp.pin_type || "") + '</div></div>';
          html += '<span class="lib-badge">插入</span></div>';
        }
        html += '</div>';
      }
      _componentsFlat = flat;
      container.innerHTML = html;
      var els = container.querySelectorAll(".lib-item");
      for (var k = 0; k < els.length; k++) {
        (function(el) {
          el.addEventListener("click", function() {
            var i = parseInt(el.dataset.idx, 10);
            if (_componentsFlat[i]) insertComponent(_componentsFlat[i].default_code || "");
          });
        })(els[k]);
      }
    }).catch(function() {
      container.innerHTML = emptyHtml("组件加载失败，请刷新重试", "fa-triangle-exclamation");
    });
  }

  // ============ LOAD TEMPLATES ============
  function loadTemplates() {
    var container = document.getElementById("templates-list");
    if (!container) return;
    container.innerHTML = '<div class="loading-text"><i class="fas fa-spinner fa-spin"></i> 加载模板中...</div>';
    if (!window.ApiRequest) {
      container.innerHTML = emptyHtml("ApiRequest 未加载", "fa-triangle-exclamation");
      return;
    }
    ApiRequest.get("/api/arduino/templates").then(function(res) {
      var data = (res && res.data) || [];
      if (!data.length) { container.innerHTML = emptyHtml("暂无模板"); return; }
      var groups = { basic: [], intermediate: [], advanced: [] };
      for (var d = 0; d < data.length; d++) {
        var k = data[d].category || "basic";
        if (!groups[k]) groups[k] = [];
        groups[k].push(data[d]);
      }
      var flat = [];
      var html = "";
      var cats = ["basic", "intermediate", "advanced"];
      for (var c = 0; c < cats.length; c++) {
        var cat = cats[c];
        var meta = TEMPLATE_CAT[cat] || { label: cat, icon: "fa-code" };
        var items = groups[cat] || [];
        if (!items.length) continue;
        html += '<div class="lib-group"><div class="lib-group-title"><i class="fas ' + meta.icon + '"></i> ' + meta.label + '</div>';
        for (var x = 0; x < items.length; x++) {
          var tpl = items[x];
          var idx = flat.length;
          flat.push(tpl);
          html += '<div class="lib-item" data-idx="' + idx + '" title="' + escapeAttr(tpl.description || "") + '">';
          html += '<span class="lib-icon"><i class="fas fa-file-code" style="color:var(--primary-light);"></i></span>';
          html += '<div class="lib-info"><div class="lib-name">' + escapeHtml(tpl.name) + '</div>';
          html += '<div class="lib-desc">' + escapeHtml(tpl.description || "") + '</div></div>';
          html += '<span class="lib-badge">加载</span></div>';
        }
        html += '</div>';
      }
      _templatesFlat = flat;
      container.innerHTML = html;
      var els = container.querySelectorAll(".lib-item");
      for (var k = 0; k < els.length; k++) {
        (function(el) {
          el.addEventListener("click", function() {
            var i = parseInt(el.dataset.idx, 10);
            if (_templatesFlat[i]) loadTemplate(_templatesFlat[i].code || "");
          });
        })(els[k]);
      }
    }).catch(function() {
      container.innerHTML = emptyHtml("模板加载失败，请刷新重试", "fa-triangle-exclamation");
    });
  }

  // ============ LOAD PROJECTS ============
  function loadProjects() {
    var list = document.getElementById("projects-list");
    var cnt = document.getElementById("projects-count");
    if (!list) return;
    list.innerHTML = '<div class="empty-text">加载中...</div>';
    if (!window.ApiRequest) return;
    ApiRequest.get("/api/arduino/projects").then(function(res) {
      var data = (res && res.data) || [];
      if (cnt) cnt.textContent = data.length;
      if (!data.length) { list.innerHTML = emptyHtml("暂无项目"); return; }
      var html = "";
      for (var d = 0; d < data.length; d++) {
        var p = data[d];
        var pid = String(p.id);
        var active = (pid === String(currentProjectId)) ? " active" : "";
        var desc = p.description ? ' · <span class="project-desc">' + escapeHtml(p.description) + '</span>' : "";
        html += '<div class="project-item' + active + '" onclick="window.ArduinoIDE.loadProject(\'' + escapeAttr(pid) + '\')">';
        html += '<div class="project-info">';
        html += '<div class="project-name">' + escapeHtml(p.name) + ' <span class="board-tag">' + escapeHtml(p.board_type || "uno") + '</span></div>';
        html += '<div class="project-meta"><i class="far fa-clock"></i> ' + escapeHtml(p.updated_at || p.created_at || "") + desc + '</div>';
        html += '</div>';
        html += '<button class="project-del" onclick="window.ArduinoIDE.deleteProject(\'' + escapeAttr(pid) + '\', event)" title="删除项目"><i class="fas fa-trash"></i></button>';
        html += '</div>';
      }
      list.innerHTML = html;
    }).catch(function() {
      list.innerHTML = emptyHtml("项目列表加载失败", "fa-triangle-exclamation");
    });
  }

  // ============ PROJECT OPS ============
  function newProject() {
    if (!confirm("新建项目将清空当前编辑器内容，是否继续？")) return;
    currentProjectId = null;
    var pn = document.getElementById("project-name");
    if (pn) pn.value = "新建项目";
    setEditorCode(DEFAULT_CODE);
    var bs = document.getElementById("board-select");
    if (bs) { bs.value = "uno"; currentBoard = "uno"; updateStatusBar(); }
    loadProjects();
    toast("已创建新项目", "info");
  }

  function saveProject() {
    var pn = document.getElementById("project-name");
    var name = pn ? (pn.value || "").trim() : "";
    if (!name) { toast("请输入项目名称", "warning"); return; }
    var code = getEditorCode();
    var payload = { name: name, description: "", code: code, board_type: currentBoard, tags: "" };
    if (!window.ApiRequest) return;
    if (currentProjectId) {
      ApiRequest.put("/api/arduino/projects/" + currentProjectId, payload, { showSuccessToast: true, successMessage: "项目已保存" })
        .then(function() { loadProjects(); });
    } else {
      ApiRequest.post("/api/arduino/projects", payload, { showSuccessToast: true, successMessage: "项目已创建" })
        .then(function(res) {
          if (res && res.data && res.data.id) currentProjectId = res.data.id;
          loadProjects();
        });
    }
  }

  function loadProject(id) {
    if (!window.ApiRequest) return;
    ApiRequest.get("/api/arduino/projects/" + id).then(function(res) {
      var p = (res && res.data) || {};
      currentProjectId = p.id;
      var pn = document.getElementById("project-name");
      if (pn) pn.value = p.name || "未命名项目";
      setEditorCode(p.code || "");
      var bs = document.getElementById("board-select");
      if (bs) { bs.value = p.board_type || "uno"; currentBoard = p.board_type || "uno"; updateStatusBar(); }
      var pb = document.getElementById("projects-bar");
      if (pb) pb.classList.add("expanded");
      loadProjects();
      toast("已加载项目: " + (p.name || ""), "success");
    }).catch(function() { toast("加载项目失败", "error"); });
  }

  function deleteProject(id, ev) {
    if (ev) { ev.stopPropagation(); ev.preventDefault(); }
    if (!confirm("确认删除该项目？此操作不可恢复。")) return;
    if (!window.ApiRequest) return;
    ApiRequest.delete("/api/arduino/projects/" + id, { showSuccessToast: true, successMessage: "项目已删除" })
      .then(function() {
        if (String(currentProjectId) === String(id)) currentProjectId = null;
        loadProjects();
      });
  }

  // ============ COMPILE ============
  function compileCode() {
    var code = getEditorCode();
    var out = document.getElementById("compile-output");
    switchTab("right", "compile");
    if (out) out.innerHTML = '<div class="compile-pane"><div class="compile-status idle"><i class="fas fa-spinner fa-spin"></i> 正在编译...</div></div>';
    if (!window.ApiRequest) {
      if (out) out.innerHTML = '<div class="compile-pane"><div class="compile-status fail"><i class="fas fa-times-circle"></i> ApiRequest 未加载</div></div>';
      return;
    }
    ApiRequest.post("/api/arduino/compile", { code: code, board_type: currentBoard }, { showErrorToast: false })
      .then(function(res) { renderCompileResult(res); })
      .catch(function(err) {
        if (err && err.data) { renderCompileResult(err.data); }
        else if (out) {
          out.innerHTML = '<div class="compile-pane"><div class="compile-status fail"><i class="fas fa-times-circle"></i> 编译请求失败: ' + escapeHtml(err.message || "未知错误") + '</div></div>';
        }
      });
  }

  function renderCompileResult(res) {
    var out = document.getElementById("compile-output");
    if (!out) return;
    var success = !!(res && res.success);
    var errors = (res && res.errors) || [];
    var warnings = (res && res.warnings) || [];
    var stats = (res && res.stats) || {};
    var html = '<div class="compile-pane">';
    var okC = success ? "ok" : "fail";
    var okI = success ? "fa-check-circle" : "fa-times-circle";
    var okT = success ? "编译成功" : "编译失败";
    html += '<div class="compile-status ' + okC + '"><i class="fas ' + okI + '"></i> ' + okT + '</div>';
    if (errors.length) {
      html += '<div class="compile-section"><div class="compile-section-title error"><i class="fas fa-bug"></i> 错误 (' + errors.length + ')</div>';
      for (var e = 0; e < errors.length; e++) {
        html += '<div class="compile-item"><span class="compile-line">行 ' + (errors[e].line || 0) + '</span><span class="compile-msg">' + escapeHtml(errors[e].message || "") + '</span></div>';
      }
      html += '</div>';
    }
    if (warnings.length) {
      html += '<div class="compile-section"><div class="compile-section-title warning"><i class="fas fa-triangle-exclamation"></i> 警告 (' + warnings.length + ')</div>';
      for (var w = 0; w < warnings.length; w++) {
        html += '<div class="compile-item warning"><span class="compile-line">行 ' + (warnings[w].line || 0) + '</span><span class="compile-msg">' + escapeHtml(warnings[w].message || "") + '</span></div>';
      }
      html += '</div>';
    }
    html += '<div class="compile-section"><div class="compile-section-title" style="color:var(--text-secondary);"><i class="fas fa-chart-simple"></i> 编译统计</div>';
    html += '<div class="compile-stats">';
    html += '<div class="stat-row"><span class="label">代码总行数</span><span class="value">' + (stats.total_lines || 0) + '</span></div>';
    html += '<div class="stat-row"><span class="label">源码大小</span><span class="value">' + (stats.code_size || 0) + ' B</span></div>';
    if (stats.binary_size) html += '<div class="stat-row"><span class="label">二进制大小</span><span class="value">' + stats.binary_size + ' B</span></div>';
    if (stats.flash_usage) html += '<div class="stat-row"><span class="label">Flash 占用</span><span class="value good">' + stats.flash_usage + '</span></div>';
    if (stats.ram_usage) html += '<div class="stat-row"><span class="label">RAM 占用</span><span class="value good">' + stats.ram_usage + '</span></div>';
    html += '</div></div></div>';
    out.innerHTML = html;
  }

  // ============ SERIAL ============
  function runSerial() {
    var code = getEditorCode();
    var term = document.getElementById("serial-terminal");
    switchTab("right", "serial");
    if (term) term.innerHTML = "";
    appendSerial("sys", "> 启动串口模拟 (9600 baud)...");
    appendSerial("sys", "> 正在解析 Serial 输出语句...");
    if (!window.ApiRequest) { appendSerial("err", "> ApiRequest 未加载"); return; }
    ApiRequest.post("/api/arduino/serial", { code: code, duration: 5 }, { showErrorToast: false })
      .then(function(res) {
        var data = (res && res.data) || [];
        appendSerial("sys", "> 共生成 " + data.length + " 条输出，开始模拟：");
        appendSerial("sys", "----------------------------------------");
        for (var i = 0; i < data.length; i++) {
          (function(d, idx) {
            setTimeout(function() { appendSerial("out", "[" + d.time + "] " + d.data); }, idx * 130);
          })(data[i], i);
        }
      }).catch(function(err) {
        appendSerial("err", "> 串口模拟失败: " + (err.message || "未知错误"));
      });
  }

  function appendSerial(cls, text) {
    var term = document.getElementById("serial-terminal");
    if (!term) return;
    var div = document.createElement("div");
    div.className = "serial-line " + cls;
    div.textContent = text;
    term.appendChild(div);
    var auto = document.getElementById("auto-scroll");
    if (!auto || auto.checked) term.scrollTop = term.scrollHeight;
  }

  function clearSerial() {
    var term = document.getElementById("serial-terminal");
    if (term) term.innerHTML = '<div class="serial-line sys">> 串口监视器已清空</div>';
  }

  function uploadCode() {
    toast("正在上传到开发板（模拟）...", "info");
    compileCode();
    setTimeout(function() {
      toast("上传完成（模拟）", "success");
      appendSerial("sys", "> [上传] 代码已上传至 " + boardDisplayName(currentBoard) + "（模拟）");
    }, 1400);
  }

  // ============ AI ASSISTANT ============
  function toggleAIPanel() {
    var panel = document.getElementById("ai-assistant-panel");
    if (!panel) return;
    _aiPanelOpen = !_aiPanelOpen;
    panel.classList.toggle("open", _aiPanelOpen);
    if (_aiPanelOpen) {
      setTimeout(function() {
        var ai = document.getElementById("ai-input");
        if (ai) ai.focus();
      }, 200);
    }
  }

  function handleAIInputKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendAIMessage(); }
  }

  function addAIMessage(role, contentHtml) {
    var chatArea = document.getElementById("ai-chat-area");
    if (!chatArea) return null;
    var msgDiv = document.createElement("div");
    msgDiv.className = "ai-chat-msg " + role;
    var icon = role === "user" ? "fa-user" : "fa-robot";
    msgDiv.innerHTML = '<div class="msg-avatar"><i class="fas ' + icon + '"></i></div>' +
      '<div class="msg-bubble">' + contentHtml + '</div>';
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    return msgDiv;
  }

  function addAILoadingMessage() {
    var chatArea = document.getElementById("ai-chat-area");
    if (!chatArea) return null;
    var msgDiv = document.createElement("div");
    msgDiv.className = "ai-chat-msg ai";
    msgDiv.id = "ai-loading-msg";
    msgDiv.innerHTML = '<div class="msg-avatar"><i class="fas fa-robot"></i></div>' +
      '<div class="msg-bubble"><div class="ai-loading-dots"><span></span><span></span><span></span></div></div>';
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
    return msgDiv;
  }

  function removeAILoadingMessage() {
    var el = document.getElementById("ai-loading-msg");
    if (el) el.remove();
  }

  function parseAICodeBlocks(text) {
    var html = "";
    var parts = text.split(/(```[\s\S]*?```)/g);
    for (var p = 0; p < parts.length; p++) {
      var part = parts[p];
      var cm = part.match(/^```(\w*)\n?([\s\S]*?)\n?```$/);
      if (cm) {
        var lang = cm[1] || "cpp";
        var code = cm[2];
        var cid = "ai-code-" + Date.now() + "-" + Math.random().toString(36).substr(2, 6);
        html += '<div class="ai-code-block">';
        html += '<div class="ai-code-header"><span class="lang">' + escapeHtml(lang) + '</span>';
        html += '<button class="insert-btn" onclick="window.ArduinoIDE.insertAICodeToEditor(\'' + cid + '\')">';
        html += '<i class="fas fa-code-merge"></i> 插入到编辑器</button></div>';
        html += '<pre id="' + cid + '"><code>' + escapeHtml(code) + '</code></pre>';
        html += '</div>';
      } else {
        html += formatAIMarkdown(part);
      }
    }
    return html;
  }

  function formatAIMarkdown(text) {
    var html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(99,102,241,0.15);padding:1px 6px;border-radius:4px;font-family:var(--font-mono);font-size:12px;color:var(--primary-light);">$1</code>');
    var lines = html.split("\n");
    var result = [];
    var inList = false;
    for (var li = 0; li < lines.length; li++) {
      var t = lines[li].trim();
      if (t.match(/^[-*]\s/)) {
        if (!inList) { result.push("<ul>"); inList = true; }
        result.push("<li>" + t.replace(/^[-*]\s/, "") + "</li>");
      } else if (t.match(/^\d+\.\s/)) {
        if (!inList) { result.push("<ol>"); inList = true; }
        result.push("<li>" + t.replace(/^\d+\.\s/, "") + "</li>");
      } else if (t === "") {
        if (inList) { result.push("</ul>"); inList = false; }
      } else {
        if (inList) { result.push("</ul>"); inList = false; }
        if (t) result.push("<p>" + lines[li] + "</p>");
      }
    }
    if (inList) result.push("</ul>");
    return result.join("");
  }

  function insertAICodeToEditor(codeId) {
    var el = document.getElementById(codeId);
    if (!el) return;
    var code = el.textContent || el.innerText;
    setEditorCode(code);
    toast("代码已插入到编辑器", "success");
  }

  function clearAIChat() {
    var chatArea = document.getElementById("ai-chat-area");
    if (!chatArea) return;
    chatArea.innerHTML =
      '<div class="ai-chat-msg ai">' +
        '<div class="msg-avatar"><i class="fas fa-robot"></i></div>' +
        '<div class="msg-bubble">' +
          '<p><strong>👋 对话已清空</strong></p>' +
          '<p>有什么我可以帮你的吗？点击上方快捷按钮或直接输入问题开始。</p>' +
        '</div></div>';
  }

  function sendAIMessage() {
    if (_aiLoading) return;
    var input = document.getElementById("ai-input");
    if (!input) return;
    var text = (input.value || "").trim();
    if (!text) return;
    addAIMessage("user", "<p>" + escapeHtml(text) + "</p>");
    input.value = "";
    input.style.height = "38px";
    _aiLoading = true;
    var btn = document.getElementById("ai-send-btn");
    if (btn) btn.disabled = true;
    addAILoadingMessage();
    if (!window.ApiRequest) { handleAIError({ message: "ApiRequest 未加载" }); return; }
    ApiRequest.post("/api/arduino/ai/generate", {
      description: text, components: "", difficulty: "intermediate"
    }, { showErrorToast: false }).then(function(r) { handleAIResponse(r); }).catch(function(e) { handleAIError(e); });
  }

  function handleAIResponse(res) {
    removeAILoadingMessage();
    _aiLoading = false;
    var btn = document.getElementById("ai-send-btn");
    if (btn) btn.disabled = false;
    var data = (res && res.data) || {};
    var content = data.content || data.result || data.message || (typeof res === "string" ? res : "");
    if (!content && data.code) {
      content = "以下是生成的代码：\n\n```cpp\n" + data.code + "\n```";
      if (data.explanation) content += "\n\n" + data.explanation;
    }
    if (!content) content = "抱歉，我无法生成有效的响应。";
    addAIMessage("ai", parseAICodeBlocks(content));
  }

  function handleAIError(err) {
    removeAILoadingMessage();
    _aiLoading = false;
    var btn = document.getElementById("ai-send-btn");
    if (btn) btn.disabled = false;
    var msg = (err && err.message) ? err.message : "请求失败，请稍后重试";
    addAIMessage("ai", '<p style="color:var(--accent-error);"><strong>❌ 出错了</strong></p><p>' + escapeHtml(msg) + '</p>');
  }

  function quickAIAction(type) {
    if (_aiLoading) return;
    var code = getEditorCode();
    if (type === "generate") {
      if (!_aiPanelOpen) toggleAIPanel();
      setTimeout(function() {
        var ai = document.getElementById("ai-input");
        if (ai) ai.focus();
        addAIMessage("ai",
          '<p><strong><i class="fas fa-sparkles"></i> 代码生成模式</strong></p>' +
          '<p>请描述你想要实现的功能，例如：</p>' +
          '<ul>' +
            '<li>控制LED灯闪烁，间隔500ms</li>' +
            '<li>使用超声波传感器测距并在串口输出</li>' +
            '<li>通过PWM控制电机转速</li>' +
          '</ul>' +
          '<p>请输入你的需求描述：</p>');
      }, 150);
      return;
    }
    if (!_aiPanelOpen) toggleAIPanel();
    var labels = {
      debug: "🔍 代码调试",
      optimize: '<i class="fas fa-bolt"></i> 代码优化',
      components: '<i class="fas fa-wrench"></i> 组件推荐',
      explain: '<i class="fas fa-book-open"></i> 代码解释'
    };
    addAIMessage("user", '<p><strong>' + (labels[type] || type) + '</strong></p>');
    _aiLoading = true;
    var btn = document.getElementById("ai-send-btn");
    if (btn) btn.disabled = true;
    addAILoadingMessage();
    var apiMap = {
      debug:      { url: "/api/arduino/ai/debug",      body: { code: code } },
      optimize:   { url: "/api/arduino/ai/optimize",   body: { code: code, level: "balanced" } },
      components: { url: "/api/arduino/ai/components", body: { description: code, project_type: "project" } },
      explain:    { url: "/api/arduino/ai/explain",    body: { code: code } }
    };
    var api = apiMap[type];
    if (!api || !window.ApiRequest) return;
    ApiRequest.post(api.url, api.body, { showErrorToast: false })
      .then(function(r) { handleAIResponse(r); })
      .catch(function(e) { handleAIError(e); });
  }

  function autoResizeAIInput() {
    var ta = document.getElementById("ai-input");
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 100) + "px";
  }

  // ============ AI AGENT PANEL ============
  var DEFAULT_AGENTS = [
    { id: "code-gen", name: "Arduino代码生成Agent", icon: "gen", fa_icon: "fa-wand-magic-sparkles", status: "running", description: "根据需求描述自动生成Arduino代码" },
    { id: "code-debug", name: "Arduino代码调试Agent", icon: "debug", fa_icon: "fa-bug", status: "running", description: "智能分析代码错误并提供修复建议" },
    { id: "code-optimize", name: "Arduino代码优化Agent", icon: "optimize", fa_icon: "fa-gauge-high", status: "running", description: "优化代码性能、内存占用和功耗" },
    { id: "component-rec", name: "Arduino组件推荐Agent", icon: "component", fa_icon: "fa-microchip", status: "stopped", description: "根据项目需求推荐合适的电子元件" }
  ];

  function toggleAgentPanel(e) {
    if (e) { e.stopPropagation(); e.preventDefault(); }
    var panel = document.getElementById("ai-agent-panel");
    if (!panel) return;
    _agentPanelOpen = !_agentPanelOpen;
    panel.classList.toggle("open", _agentPanelOpen);
    if (_agentPanelOpen) loadAIAgents();
  }

  document.addEventListener("click", function(e) {
    var panel = document.getElementById("ai-agent-panel");
    var btn = document.querySelector(".ai-agent-btn");
    if (_agentPanelOpen && panel && !panel.contains(e.target) && btn && !btn.contains(e.target)) {
      _agentPanelOpen = false;
      panel.classList.remove("open");
    }
  });

  function loadAIAgents() {
    var list = document.getElementById("ai-agent-list");
    if (!list) return;
    if (!window.ApiRequest) { _agentsCache = DEFAULT_AGENTS; renderAgentList(DEFAULT_AGENTS); return; }
    ApiRequest.get("/api/arduino/ai/agents", { showErrorToast: false }).then(function(res) {
      var a = (res && res.data) || [];
      if (!a || !a.length) a = DEFAULT_AGENTS;
      _agentsCache = a; renderAgentList(a);
    }).catch(function() { _agentsCache = DEFAULT_AGENTS; renderAgentList(DEFAULT_AGENTS); });
  }

  function renderAgentList(agents) {
    var list = document.getElementById("ai-agent-list");
    if (!list) return;
    var html = "";
    for (var i = 0; i < agents.length; i++) {
      var ag = agents[i];
      var ic = ag.icon || "gen";
      var fi = ag.fa_icon || "fa-robot";
      var st = ag.status || "stopped";
      var stTxt = st === "running" ? "运行中" : "已停止";
      html += '<div class="ai-agent-item">';
      html += '<div class="agent-icon ' + ic + '"><i class="fas ' + fi + '"></i></div>';
      html += '<div class="agent-info">';
      html += '<div class="agent-name">' + escapeHtml(ag.name) + '</div>';
      html += '<div class="agent-desc">' + escapeHtml(ag.description || "") + '</div>';
      html += '</div>';
      html += '<div class="agent-status ' + st + '"><span class="sdot"></span>' + stTxt + '</div>';
      html += '</div>';
    }
    list.innerHTML = html;
  }

  // ============ LIBRARY DATA ============
  var LIBRARIES = [
    { "name": "Wire", "ver": "1.0.0", "cat": "comm", "icon": "fa-link", "desc": "I2C/TWI 通信库", "installed": true, "builtin": true },
    { "name": "SPI", "ver": "1.0.0", "cat": "comm", "icon": "fa-exchange", "desc": "SPI 串行外设接口通信", "installed": true, "builtin": true },
    { "name": "SoftwareSerial", "ver": "1.0.0", "cat": "comm", "icon": "fa-comments", "desc": "软件串口", "installed": true, "builtin": true },
    { "name": "EEPROM", "ver": "2.0.0", "cat": "storage", "icon": "fa-memory", "desc": "读写EEPROM存储器", "installed": true, "builtin": true },
    { "name": "Servo", "ver": "1.2.1", "cat": "motor", "icon": "fa-gear", "desc": "舵机控制库", "installed": true, "builtin": true },
    { "name": "Stepper", "ver": "1.1.0", "cat": "motor", "icon": "fa-gears", "desc": "步进电机控制库", "installed": false, "builtin": true },
    { "name": "LiquidCrystal", "ver": "1.0.7", "cat": "display", "icon": "fa-display", "desc": "LCD液晶屏驱动", "installed": true, "builtin": false },
    { "name": "DHT sensor library", "ver": "1.4.6", "cat": "sensor", "icon": "fa-temperature-half", "desc": "DHT温湿度传感器", "installed": false, "builtin": false },
    { "name": "FastLED", "ver": "3.6.0", "cat": "display", "icon": "fa-lightbulb", "desc": "WS2812 LED灯带", "installed": false, "builtin": false },
    { "name": "ArduinoJson", "ver": "7.0.4", "cat": "basic", "icon": "fa-code", "desc": "JSON解析", "installed": false, "builtin": false }
  ];

  // ============ INITIALIZATION ============
  function init() {
    var ta = document.getElementById("code-editor");
    if (!ta) { console.warn("Arduino IDE: code-editor not found"); return; }
    ta.value = DEFAULT_CODE;
    ta.addEventListener("input", function() { updateEditor(); });
    ta.addEventListener("scroll", syncScroll);
    ta.addEventListener("keydown", function(e) {
      if (e.key === "Tab") {
        e.preventDefault();
        var s = this.selectionStart, en = this.selectionEnd;
        this.value = this.value.substring(0, s) + "  " + this.value.substring(en);
        this.selectionStart = this.selectionEnd = s + 2;
        updateEditor(); syncScroll();
      }
      if (e.key === "Enter") {
        var pos = this.selectionStart;
        var lineStart = this.value.lastIndexOf("\n", pos - 1) + 1;
        var line = this.value.substring(lineStart, pos);
        var indent = (line.match(/^[ \t]*/) || [""])[0];
        var after = this.value.substring(pos);
        var trimmed = line.trim();
        if (trimmed.charAt(trimmed.length - 1) === "{") indent += "  ";
        this.value = this.value.substring(0, pos) + "\n" + indent + after;
        this.selectionStart = this.selectionEnd = pos + 1 + indent.length;
        e.preventDefault(); updateEditor(); syncScroll();
      }
    });
    var bs = document.getElementById("board-select");
    if (bs) {
      bs.addEventListener("change", function() { currentBoard = this.value; updateStatusBar(); });
    }
    updateEditor();
    loadComponents();
    loadTemplates();
    loadProjects();
    loadAIAgents();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    setTimeout(init, 0);
  }

  // ============ EXPORTS ============
  window.ArduinoIDE = {
    newProject: newProject,
    saveProject: saveProject,
    loadProject: loadProject,
    deleteProject: deleteProject,
    compileCode: compileCode,
    uploadCode: uploadCode,
    runSerial: runSerial,
    clearSerial: clearSerial,
    switchTab: switchTab,
    togglePanel: togglePanel,
    toggleProjects: toggleProjects,
    toggleAIPanel: toggleAIPanel,
    sendAIMessage: sendAIMessage,
    clearAIChat: clearAIChat,
    quickAIAction: quickAIAction,
    handleAIInputKeydown: handleAIInputKeydown,
    autoResizeAIInput: autoResizeAIInput,
    toggleAgentPanel: toggleAgentPanel,
    insertAICodeToEditor: insertAICodeToEditor,
    getEditorCode: getEditorCode,
    setEditorCode: setEditorCode,
    insertComponent: insertComponent,
    loadTemplate: loadTemplate,
    loadComponents: loadComponents,
    loadTemplates: loadTemplates,
    loadProjects: loadProjects,
    updateEditor: updateEditor,
    syncScroll: syncScroll
  };

  // ========== STUBS (未实现功能的空实现，避免点击报错) ==========
  function _stub(name) {
    return function() {
      console.warn("[ArduinoIDE] 功能尚未实现: " + name);
      if (window.toast) {
        try { window.toast("功能开发中: " + name, "info"); } catch (e) {}
      }
    };
  }

  var undoEdit = _stub("撤销");
  var redoEdit = _stub("重做");
  var formatCode = _stub("格式化代码");
  var openFindReplace = _stub("查找替换");
  var openExamples = _stub("示例导入");
  var checkMemory = _stub("检查内存");
  var openShare = _stub("分享项目");
  var openThemeSelector = _stub("主题设置");
  var openShortcuts = _stub("快捷键");
  var filterLibCat = _stub("筛选库分类");
  var autoAssignPins = _stub("自动分配引脚");
  var newFile = _stub("新建文件");
  var renameFile = _stub("重命名文件");
  var deleteFile = _stub("删除文件");
  var switchSerialPort = _stub("切换串口");
  var addSerialPort = _stub("新建串口");
  var pauseSerial = _stub("暂停串口");
  var setSerialView = _stub("切换串口视图");
  var toggleHistory = _stub("历史记录");
  var sendSerialData = _stub("发送串口数据");
  var startPlotter = _stub("开始绘图");
  var pausePlotter = _stub("暂停绘图");
  var stopPlotter = _stub("停止绘图");
  var clearPlotter = _stub("清空绘图");
  var exportPlotterCSV = _stub("导出CSV");
  var debugRun = _stub("仿真运行");
  var debugPause = _stub("仿真暂停");
  var debugStep = _stub("单步执行");
  var debugStepOver = _stub("步过");
  var debugStepOut = _stub("步出");
  var debugReset = _stub("仿真重置");
  var addWatchVar = _stub("添加监视变量");
  var addBreakpoint = _stub("添加断点");
  var regenSchematic = _stub("重新生成原理图");
  var exportSchematic = _stub("导出原理图");
  var zoomSchematic = _stub("缩放原理图");
  var resetSchematicZoom = _stub("复位原理图");
  var runAISuggest = _stub("AI分析");
  var runMemoryEstimate = _stub("内存估算");
  var insertNextCompletion = _stub("代码补全");
  var openProject = _stub("打开项目");
  var toggleSerial = _stub("切换串口");

  // ========== GLOBAL ALIASES (HTML onclick 直接调用时需要全局函数) ==========
  var globals = [
    "newProject","saveProject","loadProject","deleteProject","compileCode","uploadCode",
    "runSerial","clearSerial","switchTab","togglePanel","toggleProjects","toggleAIPanel",
    "sendAIMessage","clearAIChat","quickAIAction","handleAIInputKeydown","autoResizeAIInput",
    "toggleAgentPanel","insertAICodeToEditor","getEditorCode","setEditorCode","insertComponent",
    "loadTemplate","loadComponents","loadTemplates","loadProjects","updateEditor","syncScroll",
    "undoEdit","redoEdit","formatCode","openFindReplace","openExamples","checkMemory","openShare",
    "openThemeSelector","openShortcuts","filterLibCat","autoAssignPins","newFile","renameFile",
    "deleteFile","switchSerialPort","addSerialPort","pauseSerial","setSerialView","toggleHistory",
    "sendSerialData","startPlotter","pausePlotter","stopPlotter","clearPlotter","exportPlotterCSV",
    "debugRun","debugPause","debugStep","debugStepOver","debugStepOut","debugReset","addWatchVar",
    "addBreakpoint","regenSchematic","exportSchematic","zoomSchematic","resetSchematicZoom",
    "runAISuggest","runMemoryEstimate","insertNextCompletion","openProject","toggleSerial"
  ];
  for (var i = 0; i < globals.length; i++) {
    var key = globals[i];
    if (typeof window[key] === "undefined") {
      window[key] = (typeof ArduinoIDE[key] === "function") ? ArduinoIDE[key] : eval(key);
    }
  }

})();
