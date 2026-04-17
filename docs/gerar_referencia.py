"""Gera docs/REFERENCIA_TECNICA.md com documentação completa."""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "engine")
API = os.path.join(ROOT, "api")
COGNITIVO = os.path.join(ENGINE, "cognitivo")
MEMORIA = os.path.join(ENGINE, "memoria")

def extrair_modulo(caminho):
    """Extrai classes, funções e docstrings de um arquivo Python."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return {"erro": str(e), "docstring": "", "classes": [], "funcoes": []}

    docstring = ast.get_docstring(tree) or ""
    classes = []
    funcoes = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            metodos = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args if a.arg != "self"]
                    metodos.append({
                        "nome": item.name,
                        "args": args,
                        "doc": ast.get_docstring(item) or "",
                        "linha": item.lineno,
                    })
            classes.append({
                "nome": node.name,
                "doc": ast.get_docstring(node) or "",
                "metodos": metodos,
                "linha": node.lineno,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            funcoes.append({
                "nome": node.name,
                "args": args,
                "doc": ast.get_docstring(node) or "",
                "linha": node.lineno,
            })

    return {"docstring": docstring, "classes": classes, "funcoes": funcoes}


def gerar_secao(nome_rel, caminho):
    """Gera markdown para um modulo."""
    info = extrair_modulo(caminho)
    linhas = []

    with open(caminho, "r", encoding="utf-8") as f:
        n_linhas = sum(1 for _ in f)

    linhas.append(f"## {nome_rel} ({n_linhas} linhas)")
    linhas.append("")
    if info.get("docstring"):
        linhas.append(f"**Proposito:** {info['docstring'].split(chr(10))[0]}")
        linhas.append("")

    if info.get("erro"):
        linhas.append(f"> Erro ao parsear: {info['erro']}")
        linhas.append("")
        return "\n".join(linhas)

    for cls in info["classes"]:
        linhas.append(f"### Classe `{cls['nome']}` (linha {cls['linha']})")
        if cls["doc"]:
            linhas.append(f"\n{cls['doc'].split(chr(10))[0]}\n")
        if cls["metodos"]:
            linhas.append("| Metodo | Parametros | Linha | Descricao |")
            linhas.append("|--------|-----------|-------|-----------|")
            for m in cls["metodos"]:
                if m["nome"].startswith("_") and m["nome"] != "__init__":
                    continue
                args_str = ", ".join(m["args"][:4])
                if len(m["args"]) > 4:
                    args_str += ", ..."
                doc_curto = m["doc"].split("\n")[0][:80] if m["doc"] else ""
                linhas.append(f"| `{m['nome']}` | {args_str} | {m['linha']} | {doc_curto} |")
            linhas.append("")

    if info["funcoes"]:
        linhas.append("### Funcoes")
        linhas.append("")
        linhas.append("| Funcao | Parametros | Linha | Descricao |")
        linhas.append("|--------|-----------|-------|-----------|")
        for fn in info["funcoes"]:
            if fn["nome"].startswith("_"):
                continue
            args_str = ", ".join(fn["args"][:4])
            doc_curto = fn["doc"].split("\n")[0][:80] if fn["doc"] else ""
            linhas.append(f"| `{fn['nome']}` | {args_str} | {fn['linha']} | {doc_curto} |")
        linhas.append("")

    linhas.append("---\n")
    return "\n".join(linhas)


def main():
    doc = []
    doc.append("# Referencia Tecnica — Vila INTEIA\n")
    doc.append("> Documentacao completa extraida do codigo-fonte.")
    doc.append("> Gerada automaticamente por docs/gerar_referencia.py\n")
    doc.append("---\n")

    # Core
    for nome, caminho in [
        ("main.py", os.path.join(ROOT, "main.py")),
        ("config.py", os.path.join(ROOT, "config.py")),
    ]:
        if os.path.exists(caminho):
            doc.append(gerar_secao(nome, caminho))

    # Engine
    doc.append("# Engine — Motor de Simulacao\n")
    for py in sorted(os.listdir(ENGINE)):
        if py.endswith(".py") and py != "__init__.py":
            caminho = os.path.join(ENGINE, py)
            doc.append(gerar_secao(f"engine/{py}", caminho))

    # Cognitivo
    if os.path.isdir(COGNITIVO):
        doc.append("# engine/cognitivo/ — Pipeline Cognitivo\n")
        for py in sorted(os.listdir(COGNITIVO)):
            if py.endswith(".py") and py != "__init__.py":
                caminho = os.path.join(COGNITIVO, py)
                doc.append(gerar_secao(f"engine/cognitivo/{py}", caminho))

    # Memoria
    if os.path.isdir(MEMORIA):
        doc.append("# engine/memoria/ — Sistema de Memoria\n")
        for py in sorted(os.listdir(MEMORIA)):
            if py.endswith(".py") and py != "__init__.py":
                caminho = os.path.join(MEMORIA, py)
                doc.append(gerar_secao(f"engine/memoria/{py}", caminho))

    # API
    doc.append("# API — Endpoints REST\n")
    for py in sorted(os.listdir(API)):
        if py.endswith(".py") and py != "__init__.py":
            caminho = os.path.join(API, py)
            doc.append(gerar_secao(f"api/{py}", caminho))

    resultado = "\n".join(doc)
    out_path = os.path.join(ROOT, "docs", "REFERENCIA_TECNICA.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resultado)

    n_linhas = resultado.count("\n")
    print(f"Gerado: {out_path} ({n_linhas} linhas, {len(resultado)} chars)")


if __name__ == "__main__":
    main()
