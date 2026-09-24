"""Roda dentro da imagem construída pelo Dockerfile (dev-local/run-tests.sh):
o que não pode ir para a imagem de produção."""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", [".env", "py_log.log", ".idea"])
def test_local_files_do_not_go_into_the_image(name):
    # Sem .dockerignore, o COPY . . do Dockerfile levava segredos e logs locais.
    assert not (ROOT / name).exists()


def test_what_the_image_needs_is_still_there():
    for name in ("main.py", "pyproject.toml", "poetry.lock", ".env.example"):
        assert (ROOT / name).exists(), name
