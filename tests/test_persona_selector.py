"""Testes Onda 127: persona selector por dataset categoria."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.persona_selector import (
    detectar_categoria, selecionar_panel, panels_por_dataset,
    PANELS_POR_CATEGORIA,
)

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def t_detecta_politica_br():
    teste("impeachment_dilma_2016", detectar_categoria("impeachment_dilma_2016") == "politica_br")
    teste("eleicao_presidencial_br_2022", detectar_categoria("eleicao_presidencial_br_2022") == "politica_br")
    teste("lava_jato_2014_2018", detectar_categoria("lava_jato_2014_2018") == "politica_br")


def t_detecta_financeiro():
    teste("americanas_crise_2023", detectar_categoria("americanas_crise_2023") == "financeiro")
    teste("pix_adoption_2020", detectar_categoria("pix_adoption_2020") == "financeiro")


def t_detecta_crypto():
    teste("crypto_bitcoin_2024", detectar_categoria("crypto_bitcoin_2024") == "crypto")


def t_detecta_tech():
    teste("lancamento_apple_vpro_2024", detectar_categoria("lancamento_apple_vpro_2024") == "tech")
    teste("tiktok_viral_2024", detectar_categoria("tiktok_viral_2024") == "tech")
    teste("twitter_musk_2022_2024", detectar_categoria("twitter_musk_2022_2024") == "tech")


def t_generico_fallback():
    teste("dataset aleatório → generico",
           detectar_categoria("random_xyz_dataset") == "generico")


def t_keyword_scan_eventos():
    # Dataset com nome ambíguo, keywords políticas
    eventos = [{"contexto": "congresso aprova impeachment em brasilia"}]
    teste("scan keywords detecta política",
           detectar_categoria("ambiguo", eventos_sample=eventos) == "politica_br")


def t_selecionar_panel_politica():
    r = selecionar_panel("impeachment_dilma_2016")
    teste("categoria politica_br", r["categoria"] == "politica_br")
    teste("Bezos (CL007) primeiro", r["persona_ids"][0] == "CL007")


def t_selecionar_panel_crypto():
    r = selecionar_panel("crypto_bitcoin_2024")
    teste("categoria crypto", r["categoria"] == "crypto")
    teste("Musk (CL001) no panel", "CL001" in r["persona_ids"])


def t_filtro_personas_validas():
    # Só CL001 e CL002 disponíveis, politica_br pede CL007+CL002+CL001
    r = selecionar_panel("impeachment_test", personas_validas={"CL001", "CL002"})
    teste("filtra indisponíveis", "CL007" not in r["persona_ids"])
    teste("mantém disponíveis", "CL002" in r["persona_ids"] or "CL001" in r["persona_ids"])


def t_fallback_generico_quando_vazio():
    r = selecionar_panel("xyz", personas_validas={"CL100"})
    # generico também não tem CL100 → fallback últim0 = sorted([CL100])[:3]
    teste("fallback não crasha", "persona_ids" in r)


def t_panels_por_dataset():
    datasets = ["impeachment_x", "crypto_y", "tech_z"]
    r = panels_por_dataset(datasets)
    teste("3 datasets mapeados", len(r) == 3)
    teste("cada tem categoria", all("categoria" in v for v in r.values()))


def main():
    print("=== test_persona_selector ===")
    for fn in [t_detecta_politica_br, t_detecta_financeiro, t_detecta_crypto,
               t_detecta_tech, t_generico_fallback, t_keyword_scan_eventos,
               t_selecionar_panel_politica, t_selecionar_panel_crypto,
               t_filtro_personas_validas, t_fallback_generico_quando_vazio,
               t_panels_por_dataset]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
