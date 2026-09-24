"""O .env.example é o contrato de configuração do deploy: tem de listar
exatamente as variáveis que o código lê (nem faltar, nem sobrar)."""
import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def env_vars_read_by_code():
    names = set()
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant) \
                    and ast.unparse(node.func) in ("os.getenv", "os.environ.get", "getenv"):
                names.add(node.args[0].value)
            if isinstance(node, ast.Subscript) and ast.unparse(node.value) == "os.environ" \
                    and isinstance(node.slice, ast.Constant):
                names.add(node.slice.value)
    return names


def env_example_keys():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z][A-Za-z0-9_]*)=", text, re.MULTILINE))


def test_every_variable_the_code_reads_is_documented():
    # Faltavam MONGO_URI e REDIS_URL; AUTH_DEV_RETURN_LINK precisa estar documentada.
    assert env_vars_read_by_code() - env_example_keys() == set()


def test_example_has_no_variable_the_code_ignores():
    assert env_example_keys() - env_vars_read_by_code() == set()
