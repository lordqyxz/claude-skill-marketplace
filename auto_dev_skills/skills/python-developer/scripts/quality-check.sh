#!/bin/bash
# 代码质量检查脚本
#
# 零 token 消耗，秒级执行。
# 自动运行 ruff format、ruff check、pyright、pytest 并生成量化报告。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检测包管理器
detect_runner() {
    if [ -f "uv.lock" ] || [ -f "pyproject.toml" ] && grep -q "tool.uv" pyproject.toml 2>/dev/null; then
        echo "uv run"
    elif [ -f "poetry.lock" ]; then
        echo "poetry run"
    else
        echo ""
    fi
}

RUNNER=$(detect_runner)

echo "## 代码质量检查报告"
echo ""
echo "Runner: ${RUNNER:-direct}"
echo ""

PASS=0
FAIL=0

# 1. 格式化检查
echo "### 1. Ruff Format"
if ${RUNNER} ruff format --check src/ tests/ 2>&1; then
    echo "  ✅ 格式化检查通过"
    ((PASS++))
else
    FORMAT_ISSUES=$(${RUNNER} ruff format --check src/ tests/ 2>&1 | grep -c "would reformat" || echo "0")
    echo "  ❌ 格式化问题: ${FORMAT_ISSUES} 个文件"
    ((FAIL++))
fi
echo ""

# 2. Lint 检查
echo "### 2. Ruff Lint"
if ${RUNNER} ruff check src/ tests/ 2>&1; then
    echo "  ✅ Lint 检查通过"
    ((PASS++))
else
    LINT_ISSUES=$(${RUNNER} ruff check src/ tests/ 2>&1 | tail -1 | grep -oP 'Found \K\d+' || echo "0")
    echo "  ❌ Lint 问题: ${LINT_ISSUES} 个"
    ((FAIL++))
fi
echo ""

# 3. 类型检查
echo "### 3. Pyright 类型检查"
if ${RUNNER} pyright src/ 2>&1; then
    echo "  ✅ 类型检查通过"
    ((PASS++))
else
    TYPE_ERRORS=$(${RUNNER} pyright src/ 2>&1 | grep -oP '\d+ error' | head -1 || echo "0")
    echo "  ❌ 类型错误: ${TYPE_ERRORS}"
    ((FAIL++))
fi
echo ""

# 4. 测试
echo "### 4. 测试"
if ${RUNNER} pytest tests/ -v --tb=short 2>&1; then
    echo "  ✅ 测试通过"
    ((PASS++))
else
    echo "  ❌ 测试失败"
    ((FAIL++))
fi
echo ""

# 5. 覆盖率（如果 pytest-cov 可用）
echo "### 5. 覆盖率"
COV_OUTPUT=$(${RUNNER} pytest tests/ --cov=src/ --cov-report=term-missing --tb=no -q 2>&1 || true)
COV_LINE=$(echo "$COV_OUTPUT" | grep "^TOTAL" || true)
if [ -n "$COV_LINE" ]; then
    echo "  ${COV_LINE}"
    ((PASS++))
else
    echo "  ⚠️ 覆盖率信息不可用（需要 pytest-cov）"
fi
echo ""

# 6. 架构一致性
echo "### 6. 架构一致性"
if [ -f "${SCRIPT_DIR}/verify-architecture.py" ]; then
    if python "${SCRIPT_DIR}/verify-architecture.py" 2>&1; then
        echo "  ✅ 依赖方向正确"
        ((PASS++))
    else
        echo "  ❌ 依赖方向有违反"
        ((FAIL++))
    fi
else
    echo "  ⚠️ verify-architecture.py 未找到"
fi
echo ""

# 汇总
echo "---"
echo "### 汇总"
echo "  通过: ${PASS}"
echo "  失败: ${FAIL}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "❌ 质量检查未通过，请修复上述问题"
    exit 1
else
    echo "✅ 所有质量检查通过"
    exit 0
fi