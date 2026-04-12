#!/usr/bin/env python3
"""DDD 领域分析脚本 - 静态分析现有代码中的领域模型

零 token 消耗，毫秒级执行。
使用 AST 分析（不依赖 importlib 动态导入），避免依赖缺失导致失败。
输出实体、值对象、领域服务接口的结构化报告。
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


def analyze_entities(entities_path: Path) -> list[dict]:
    """分析实体文件，提取 dataclass 和 Enum"""
    results = []
    try:
        tree = ast.parse(entities_path.read_text())
    except (FileNotFoundError, SyntaxError):
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            info = {"name": node.name, "type": "class", "fields": [], "bases": []}

            # 检测 dataclass
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "dataclass":
                    info["type"] = "entity"
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    if dec.func.id == "dataclass":
                        info["type"] = "entity"
                        # 检查 frozen=True
                        for kw in dec.keywords:
                            if kw.arg == "frozen" and isinstance(
                                kw.value, ast.Constant
                            ):
                                if kw.value.value:
                                    info["type"] = "value_object"

            # 检测 Enum
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Enum":
                    info["type"] = "value_object"
                elif isinstance(base, ast.Attribute) and base.attr == "Enum":
                    info["type"] = "value_object"
                elif isinstance(base, ast.Name):
                    info["bases"].append(base.id)
                elif isinstance(base, ast.Attribute):
                    info["bases"].append(base.attr)

            # 提取字段
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and item.target:
                    field_name = (
                        item.target.id if isinstance(item.target, ast.Name) else "?"
                    )
                    info["fields"].append(field_name)

            if info["type"] != "class" or info["fields"]:
                results.append(info)

    return results


def analyze_interfaces(converter_path: Path) -> list[dict]:
    """分析领域服务接口文件，提取 ABC 类和抽象方法"""
    results = []
    try:
        tree = ast.parse(converter_path.read_text())
    except (FileNotFoundError, SyntaxError):
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_abstract = False
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "ABC":
                    is_abstract = True

            if not is_abstract:
                continue

            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_abstract_method = any(
                        isinstance(dec, ast.Name) and dec.id == "abstractmethod"
                        for dec in item.decorator_list
                    )
                    if is_abstract_method:
                        args = [a.arg for a in item.args.args if a.arg != "self"]
                        methods.append(
                            {
                                "name": item.name,
                                "is_async": isinstance(item, ast.AsyncFunctionDef),
                                "args": args,
                            }
                        )

            if methods:
                results.append({"name": node.name, "methods": methods})

    return results


def analyze_exceptions(exceptions_path: Path) -> list[dict]:
    """分析异常文件，提取异常类"""
    results = []
    try:
        tree = ast.parse(exceptions_path.read_text())
    except (FileNotFoundError, SyntaxError):
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = ""
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr

                if "Error" in base_name or "Error" in node.name:
                    results.append({"name": node.name, "base": base_name})
                    break

    return results


def main():
    pkg_root = find_package_root()
    if pkg_root is None:
        print("Error: No Python package found under src/")
        sys.exit(1)

    core_dir = pkg_root / "core"
    if not core_dir.exists():
        print("Error: No core/ directory found")
        sys.exit(1)

    print("## DDD 领域分析报告\n")
    print(f"Package: {pkg_root.name}\n")

    # 分析实体
    entities_path = core_dir / "entities.py"
    if entities_path.exists():
        entities = analyze_entities(entities_path)
        if entities:
            print("### 聚合根 / 实体\n")
            for e in entities:
                if e["type"] == "entity":
                    print(f"- **{e['name']}**")
                    for f in e["fields"]:
                        print(f"  - {f}")
                    print()

            print("### 值对象\n")
            for e in entities:
                if e["type"] == "value_object":
                    print(f"- **{e['name']}**")
                    for f in e["fields"]:
                        print(f"  - {f}")
                    print()

    # 分析接口
    converter_path = core_dir / "converter.py"
    if converter_path.exists():
        interfaces = analyze_interfaces(converter_path)
        if interfaces:
            print("### 领域服务接口\n")
            for iface in interfaces:
                print(f"- **{iface['name']}**")
                for m in iface["methods"]:
                    async_marker = "async " if m["is_async"] else ""
                    args_str = ", ".join(m["args"])
                    print(f"  - {async_marker}{m['name']}({args_str})")
                print()

    # 分析异常
    exceptions_path = core_dir / "exceptions.py"
    if exceptions_path.exists():
        exceptions = analyze_exceptions(exceptions_path)
        if exceptions:
            print("### 领域异常\n")
            for exc in exceptions:
                print(f"- **{exc['name']}** (extends {exc['base']})")
            print()


if __name__ == "__main__":
    main()
