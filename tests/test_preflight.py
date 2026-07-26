"""Static guardrails for deploy preflight and SiteGround sync targets."""

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = PROJECT_ROOT / "scripts" / "preflight.py"
PUSH_SCRIPT = PROJECT_ROOT / "scripts" / "push_wordpress.py"


def _invoked_preflight_scripts(source: str) -> list[Path]:
    """Extract script paths passed to Preflight.run_step() command lists."""
    roots = {
        "SCRIPTS_DIR": PROJECT_ROOT / "scripts",
        "WORDPRESS_DIR": PROJECT_ROOT / "wordpress",
    }
    scripts = []
    for node in ast.walk(ast.parse(source)):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run_step"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.List)
        ):
            continue
        for item in node.args[1].elts:
            if not (
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Name)
                and item.func.id == "str"
                and len(item.args) == 1
                and isinstance(item.args[0], ast.BinOp)
                and isinstance(item.args[0].op, ast.Div)
                and isinstance(item.args[0].left, ast.Name)
                and isinstance(item.args[0].right, ast.Constant)
                and isinstance(item.args[0].right.value, str)
            ):
                continue
            root = roots.get(item.args[0].left.id)
            if root:
                scripts.append(root / item.args[0].right.value)
    return scripts


def test_every_preflight_script_exists():
    scripts = _invoked_preflight_scripts(PREFLIGHT.read_text())
    assert scripts, "Expected preflight to invoke at least one script"
    missing = [path.relative_to(PROJECT_ROOT) for path in scripts if not path.is_file()]
    assert not missing, f"Preflight invokes missing scripts: {missing}"


def test_sync_functions_never_target_wordpress_content():
    source = PUSH_SCRIPT.read_text()
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("sync_"):
            function_source = ast.get_source_segment(source, node) or ""
            if "wp-content" in function_source:
                offenders.append(node.name)
    assert not offenders, f"Static sync functions target retired paths: {offenders}"
