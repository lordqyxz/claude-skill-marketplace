#!/usr/bin/env python3
"""Clean Architecture 依赖方向验证脚本

零 token 消耗，毫秒级执行。
使用 AST 分析验证 core/ 不依赖 infrastructure/ 或 interfaces/。
"""

import ast
import sys
from pathlib import Path


def find_package_root() -> Path | None:
    """查找 src/ 下的包根目录"""
    src_dir = Path("src")
    if not src_dir.exists():
        return None
    for pkg in src_dir.iterdir():
        if pkg.is_dir() and (pkg / "__init__.py").exists():
            return pkg
    return None


def resolve_relative_import(
    module: str | None, level: int, file_path: Path, pkg_name: str
) -> str:
    """将相对导入解析为绝对模块路径

    例如: from ..core.converter (level=2) → docconverter.core.converter
    """
    if level == 0 or module is None:
        return module or ""

    # 根据文件位置计算父级包路径
    parts = list(file_path.parts)
    # 找到包名在路径中的位置
    try:
        pkg_idx = parts.index(pkg_name)
    except ValueError:
        return module or ""

    # 相对导入的 level 表示向上几级
    # from ..core 表示向上2级然后进入 core
    base_parts = parts[pkg_idx : len(parts) - level]  # 去掉末尾 level 层
    base = ".".join(base_parts)

    if module:
        return f"{base}.{module}"
    return base


def get_all_imports(file_path: Path, pkg_name: str = "") -> list[str]:
    """提取文件中的所有 from ... import 语句的模块路径（解析相对导入）"""
    imports = []
    try:
        tree = ast.parse(file_path.read_text())
    except (FileNotFoundError, SyntaxError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0 and pkg_name:
                # 相对导入，解析为绝对路径
                resolved = resolve_relative_import(
                    node.module, node.level, file_path, pkg_name
                )
                if resolved:
                    imports.append(resolved)
            elif node.module:
                imports.append(node.module)

    return imports


def check_layer_dependencies(
    pkg_name: str, core_dir: Path, infra_dir: Path, interfaces_dir: Path
) -> tuple[list[dict], int, int]:
    """验证依赖方向"""
    violations = []

    # 1. Core 不依赖 Infrastructure 或 Interfaces
    if core_dir.exists():
        for py_file in core_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            imports = get_all_imports(py_file, pkg_name)
            for imp in imports:
                if f"{pkg_name}.infrastructure" in imp:
                    violations.append(
                        {
                            "file": str(py_file.relative_to(Path("src").parent)),
                            "violation": "Core 依赖 Infrastructure",
                            "import": imp,
                        }
                    )
                if f"{pkg_name}.interfaces" in imp:
                    violations.append(
                        {
                            "file": str(py_file.relative_to(Path("src").parent)),
                            "violation": "Core 依赖 Interfaces",
                            "import": imp,
                        }
                    )

    # 2. Interfaces 不直接依赖 Infrastructure 的具体实现
    if interfaces_dir.exists():
        for py_file in interfaces_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            imports = get_all_imports(py_file, pkg_name)
            for imp in imports:
                # 允许 interfaces 依赖 core
                if f"{pkg_name}.infrastructure" in imp:
                    violations.append(
                        {
                            "file": str(py_file.relative_to(Path("src").parent)),
                            "violation": "Interfaces 直接依赖 Infrastructure",
                            "import": imp,
                        }
                    )

    # 3. Infrastructure 应该依赖 Core（实现核心接口）
    infra_deps_on_core = 0
    infra_files = 0
    if infra_dir.exists():
        for py_file in infra_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            infra_files += 1
            imports = get_all_imports(py_file, pkg_name)
            for imp in imports:
                if f"{pkg_name}.core" in imp:
                    infra_deps_on_core += 1
                    break

    return violations, infra_deps_on_core, infra_files


def main():
    pkg_root = find_package_root()
    if pkg_root is None:
        print("Error: No Python package found under src/")
        sys.exit(1)

    pkg_name = pkg_root.name
    core_dir = pkg_root / "core"
    infra_dir = pkg_root / "infrastructure"
    interfaces_dir = pkg_root / "interfaces"

    print("## Clean Architecture 依赖方向验证\n")
    print(f"Package: {pkg_name}\n")

    violations, infra_deps, infra_files = check_layer_dependencies(
        pkg_name, core_dir, infra_dir, interfaces_dir
    )

    # 输出结果
    if violations:
        print("❌ 发现依赖方向违反：\n")
        for v in violations:
            print(f"  - **{v['file']}**: {v['violation']}")
            print(f"    `from {v['import']} import ...`")
            print()
    else:
        print("✅ Clean Architecture 依赖方向正确\n")

    # 输出依赖统计
    print("### 依赖关系\n")
    if core_dir.exists():
        print(
            "  ✓ Core 不依赖 Infrastructure"
            if not any(v["violation"].startswith("Core 依赖 Infra") for v in violations)
            else "  ✗ Core 依赖了 Infrastructure"
        )
        print(
            "  ✓ Core 不依赖 Interfaces"
            if not any(v["violation"].startswith("Core 依赖 Inter") for v in violations)
            else "  ✗ Core 依赖了 Interfaces"
        )

    if interfaces_dir.exists():
        print(
            "  ✓ Interfaces 不直接依赖 Infrastructure"
            if not any("Interfaces" in v["violation"] for v in violations)
            else "  ✗ Interfaces 直接依赖了 Infrastructure"
        )

    if infra_dir.exists():
        print(f"  ✓ Infrastructure 依赖 Core ({infra_deps}/{infra_files} 个文件)")

    print()

    # 返回状态码
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
