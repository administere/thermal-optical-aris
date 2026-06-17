#!/usr/bin/env bash
# ============================================================
#  热光混合处理器 — ARIS 自动化科研环境一键安装
# ============================================================
#  用法: bash setup-aris.sh
#
#  这个脚本会:
#    1. 克隆 ARIS 仓库（如果还没有）
#    2. 将 80+ 科研 skills symlink 到当前项目
#    3. 安装 Python 依赖
#    4. （可选）配置跨模型审稿
#
#  不需要 GPU。不需要 API key。审稿用 manual 模式，零成本。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARIS_REPO="${ARIS_REPO:-$HOME/Auto-claude-code-research-in-sleep}"
ARIS_VERSION="v0.5.0"  # 安装时锁定的版本，可修改

echo "=============================================="
echo "  热光混合处理器 · ARIS 环境安装"
echo "=============================================="
echo ""

# ---- Step 1: 克隆 ARIS ----
if [ -d "$ARIS_REPO" ]; then
    echo "[1/4] ARIS 仓库已存在: $ARIS_REPO"
    echo "       如需更新: cd $ARIS_REPO && git pull"
else
    echo "[1/4] 克隆 ARIS 仓库..."
    git clone https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep.git "$ARIS_REPO"
    echo "       ✅ 完成"
fi

# ---- Step 2: 安装 skills ----
echo "[2/4] 安装 ARIS skills 到当前项目..."
mkdir -p "$SCRIPT_DIR/.claude/skills"

# 非交互式安装
echo "y" | bash "$ARIS_REPO/tools/install_aris.sh" "$SCRIPT_DIR"

echo "       ✅ 完成 ($(ls "$SCRIPT_DIR/.claude/skills/" | wc -l) 个 skills)"

# ---- Step 3: Python 依赖 ----
echo "[3/4] 安装 Python 依赖..."
pip install numpy scipy matplotlib openpyxl -q 2>&1 | tail -1 || true
echo "       ✅ 完成"

# ---- Step 4: 配置审稿模式 ----
echo "[4/4] 配置审稿模式 (manual — 零成本，无需 API key)..."
mkdir -p "$SCRIPT_DIR/.claude"

# 只在 settings.json 不存在时创建
if [ ! -f "$SCRIPT_DIR/.claude/settings.json" ]; then
    cat > "$SCRIPT_DIR/.claude/settings.json" <<'JSON'
{
  "permissions": {
    "allow": [
      "Bash(curl:*)",
      "Bash(python:*)",
      "Bash(pip:*)",
      "Bash(git:*)",
      "WebSearch",
      "WebFetch"
    ]
  },
  "env": {
    "ARIS_REVIEWER_PROVIDER": "manual",
    "ARIS_NO_HISTORY": "false"
  }
}
JSON
    echo "       ✅ 已创建 .claude/settings.json"
else
    echo "       ⚠️  .claude/settings.json 已存在，跳过"
fi

# ---- 完成 ----
echo ""
echo "=============================================="
echo "  ✅ ARIS 环境安装完成"
echo "=============================================="
echo ""
echo "  启动方式:"
echo "    cd $SCRIPT_DIR"
echo "    claude"
echo ""
echo "  常用命令 (在 claude 会话中输入):"
echo "    /research-lit    \"研究方向\"            — 文献调研"
echo "    /idea-discovery  \"研究方向\"            — 找创新点"
echo "    /research-pipeline \"研究方向\"          — 全流程自动化"
echo "    /paper-writing   \"报告文件\"            — 写论文"
echo ""
echo "  本项目已验证的分析链路:"
echo "    材料源数据/吸收分析.py        — 吸收系数外推"
echo "    材料源数据/调制机制.py        — 三种调制机制对比"
echo "    材料源数据/晶体结构分析.py    — 共晶结构分析"
echo "    工程验证.py                  — 核心工程分析"
echo "    综合验证.py                  — 8 子系统多维验证"
echo "    能量对比v2.py                — 5 方案能耗对比"
echo "    FDTD光学验证.py              — MEEP 全波电磁仿真"
echo ""
echo "  审稿模式: manual (如需 Codex/GPT-5.5 审稿，运行 codex setup)"
echo ""
