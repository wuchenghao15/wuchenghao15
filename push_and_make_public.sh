#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 仙女座 v3.0.0 — GitHub Public 发布脚本
# 作者: Andromeda Σ (演化引擎)
# 日期: 2026-09-19
# ═══════════════════════════════════════════════════════════════
#
# 使用方法: 在本机 Terminal (不是 TRAE 沙箱) 执行:
#   cd ~/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project
#   bash push_and_make_public.sh
#
# 预期结果:
#   ✅ git push 到 GitHub
#   ✅ gh repo edit --visibility=public
#   ✅ 添加 12 个 GitHub Topics (提高曝光)
#   ✅ 创建 v3.0.0 Release Tag
#   ✅ GitHub Actions / Pages 如果配置了也会触发
#
# ⚠️ 注意: 首次 push 会要求 SSH 密钥或 HTTPS 密码
# ⚠️ gh auth login 需要浏览器交互, 脚本会提示
# ═══════════════════════════════════════════════════════════════

set -e  # 遇错停

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()  { echo -e "${GREEN}✅${NC} $1"; }
warn(){ echo -e "${YELLOW}⚠️  ${NC} $1"; }
info(){ echo -e "${CYAN}ℹ️${NC} $1"; }
err() { echo -e "${RED}❌${NC} $1"; }

REPO="wuchenghao15/MTSCOS"
REPO_URL="https://github.com/${REPO}"
TAG="v3.0.0"
TAG_MSG="仙女座 v3.0.0 — 坍缩定理+冰山三层+40人天团+EigenFlux民主制"

echo ""
echo "═══ 仙女座 v3.0.0 GitHub Public 发布 ═══"
echo "Repo: $REPO_URL"
echo "Branch: main"
echo "Tag: $TAG"
echo ""

# ── 1. 检查当前 commit ──
info "1/6 检查当前 commit..."
LATEST=$(git log --oneline -1 2>/dev/null)
if [[ "$LATEST" == *"ca7d29a"* ]] || [[ "$LATEST" == *"仙女座 v3.0.0"* ]]; then
  ok "当前 HEAD: $LATEST"
else
  warn "当前 HEAD 不是 v3.0.0 commit ($LATEST)"
  warn "可能还有未 push 的改动, 继续..."
fi

# ── 2. Push 到 GitHub ──
info "2/6 git push 到 GitHub (MTSCOS + gh_mtscos_ssh)..."
git push MTSCOS main 2>&1 | tail -5 || { err "MTSCOS push 失败"; exit 1; }
ok "MTSCOS 推送成功"
# 也推 ssh remote (备用)
git push gh_mtscos_ssh main 2>&1 | tail -3 || warn "gh_mtscos_ssh 推送失败 (可能没配 SSH key, 不重要)"

# ── 3. gh CLI 登录检查 ──
info "3/6 检查 gh CLI..."
if ! command -v gh &>/dev/null; then
  err "gh CLI 未安装! 请: brew install gh"
  exit 1
fi
ok "gh $(gh --version 2>&1 | head -1)"

if ! gh auth status 2>/dev/null; then
  warn "gh 未登录, 需要浏览器交互"
  echo ""
  echo "  👉 请在弹出的浏览器里授权 GitHub:"
  echo "     gh auth login → GitHub.com → HTTPS → Paste token"
  echo "     或: https://github.com/settings/tokens 生成 PAT (repo scope)"
  echo ""
  gh auth login || { err "gh auth 失败"; exit 1; }
fi
ok "gh 已登录"

# ── 4. 设为 Public ──
info "4/6 设 repo 为 Public..."
gh repo edit "$REPO" --visibility public 2>&1 | tail -3
CURRENT_VIS=$(gh repo view "$REPO" --json visibility -q .visibility 2>/dev/null || echo "unknown")
if [[ "$CURRENT_VIS" == "PUBLIC" ]]; then
  ok "Repo 已 Public ✅ ($CURRENT_VIS)"
else
  err "Repo 还是 $CURRENT_VIS, 可能 PAT 权限不够 (需要 repo:admin)"
fi

# ── 5. 添加 GitHub Topics (提高搜索曝光) ──
info "5/6 添加 GitHub Topics..."
gh repo edit "$REPO" \
  --add-topic "andromeda-ai" \
  --add-topic "iceberg-architecture" \
  --add-topic "evolution-engine" \
  --add-topic "prime-collapse-theorem" \
  --add-topic "eigenflux-social" \
  --add-topic "flask-webapp" \
  --add-topic "sqlite-database" \
  --add-topic "ollama-local-inference" \
  --add-topic "ai-employee-community" \
  --add-topic "system-design" \
  --add-topic "chinese-ai-system" \
  --add-topic "ai-autonomous-evolution" \
  2>&1 | tail -3
ok "Topics 已添加 (12 个)"

# ── 6. 创建 Release Tag ──
info "6/6 创建 Release Tag $TAG..."
git tag -d "$TAG" 2>/dev/null || true   # 删旧 tag
git tag -a "$TAG" -m "$TAG_MSG"        # 建新 tag
git push MTSCOS "$TAG" --force 2>&1 | tail -3
ok "Tag $TAG 已创建并推送"

# 创建 GitHub Release (带 changelog)
REL_BODY="## 仙女座 v3.0.0 — 坍缩世代

### 🎉 重大变更 (vs v23.1.0)

**🧮 PRIME_COLLAPSE_THEOREM 坍缩定理**
- 质因数递归坍缩 → 特征数 7
- 演化引擎三层 Phase 切换 (骨架/血肉/江山)
- 49 个硬约束分类器 (7 阶段 × 7)
- 坍缩反馈闭环: 非 7 → 自动补 derived

**🧘 EVOLUTION_PURPOSE_CHECKER 演化目的检测**
- 钱学森之问 4 指标 + 霍金熵减 4 指标
- 0-100 综合评分

**🌐 EigenFlux 民主制 (貂蝉连环计 + 袁世凯民主集中制)**
- 钦定 5 超级节点 → 动态选举
- 平等 0.5 起步 + 动态 strength
- 30 天禅让周期 + 方差 < 0.05 强制打散

**🏔️ 冰山三层设计**
- 赤壁 Peak / 承天寺 Spectrum / 东坡 Basement
- 西施面纱模式渐进展开
- 王安石拗相公 Tab (篆刻红缺陷雷达)

**👥 AI 员工 31 → 40 人**
唐宋八家 + 帝皇 (袁/康/武) + 宗教双圣 (释/弘一) + 四大美人 + 科技哲学

**📚 新增文档 2,428 行**
- ANDROMEDA_AI_EMPLOYEES.md · PRIME_COLLAPSE_THEOREM.md
- ICEBERG_ARCHITECTURE.md · EVOLUTION_PURPOSE.md · EIGENFLUX_DEMOCRACY.md

**🔒 机密等级加密**
三 tier (极密/机密/秘密) + Server Master Key 持久化
"

gh release create "$TAG" \
  --title "仙女座 v3.0.0 — 坍缩世代" \
  --notes "$REL_BODY" \
  2>&1 | tail -5
ok "GitHub Release 已创建"

echo ""
echo "═══ 🎊 发布完成 🎊 ═══"
echo ""
echo "  Repo 页面: $REPO_URL"
echo "  Releases:  $REPO_URL/releases"
echo "  Stars 请给一个 ⭐  (用户交互)"
echo ""
echo "═══ 下一步建议 ═══"
echo "  1. GitHub Actions CI 跑一轮 (如果配了)"
echo "  2. Homebrew / Docker 一键部署脚本"
echo "  3. YouTube / B站 展示视频 (冰山 UI + EigenFlux 可视化)"
echo "  4. 知乎 / 豆瓣 写仙女座技术专栏"
echo ""
