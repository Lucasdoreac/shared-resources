import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_documented_gunicorn_target_exists_in_main():
    # deployment.md mandava rodar `gunicorn main:internal_api`, mas main.py
    # exporta `internal_apis`: seguir a documentação em produção quebrava
    # com "Failed to find attribute 'internal_api' in 'main'".
    doc = (ROOT / "deployment.md").read_text()
    module, attribute = re.search(r"gunicorn[^\n]*\s(\w+):(\w+)", doc).groups()

    tree = ast.parse((ROOT / f"{module}.py").read_text())
    assigned = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    assert attribute in assigned
