from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from engine.oficinas import Workspace, WorkspacePathError


def test_workspace_roundtrip_stays_inside_base():
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        meta = ws.escrever(
            desafio_id="desafio_seguro",
            agente_id="CL001",
            agente_nome="Elon Musk",
            nome_arquivo="entrega.md",
            conteudo="conteudo seguro",
        )

        base = Path(tmp).resolve()
        saved = Path(meta["caminho"]).resolve()

        assert base in saved.parents
        assert ws.ler("desafio_seguro", "entrega.md") == "conteudo seguro"
        assert ws.listar("desafio_seguro")[0]["arquivo"] == "entrega.md"


@pytest.mark.parametrize(
    "desafio_id",
    ["../fora", "..\\fora", "/tmp/fora", "C:\\fora", ".", ""],
)
def test_workspace_rejects_unsafe_desafio_id(desafio_id):
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        with pytest.raises(WorkspacePathError):
            ws.escrever(
                desafio_id=desafio_id,
                agente_id="CL001",
                agente_nome="Elon Musk",
                nome_arquivo="entrega.md",
                conteudo="x",
            )


@pytest.mark.parametrize(
    "nome_arquivo",
    ["../evil.md", "..\\evil.md", "/tmp/evil.md", "C:\\evil.md", ".", ""],
)
def test_workspace_rejects_unsafe_file_names(nome_arquivo):
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        with pytest.raises(WorkspacePathError):
            ws.escrever(
                desafio_id="desafio_seguro",
                agente_id="CL001",
                agente_nome="Elon Musk",
                nome_arquivo=nome_arquivo,
                conteudo="x",
            )


def test_workspace_read_rejects_traversal_without_creating_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp)
        with pytest.raises(WorkspacePathError):
            ws.ler("desafio_seguro", "../evil.md")
        assert not (Path(tmp) / "desafio_seguro").exists()
