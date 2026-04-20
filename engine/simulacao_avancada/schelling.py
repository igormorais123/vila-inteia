"""
Schelling segregation model (1971).

Dado 2 grupos num grid 2D, cada agente "feliz" se fração de vizinhos do mesmo grupo
>= threshold τ. Se infeliz, move para célula vazia aleatória.

Emergência surpreendente: τ=33% já produz segregação severa.

Uso na Vila: modelar clusters de categoria/tier no campus espacial.
"""

from __future__ import annotations

import numpy as np
import random


def schelling_step(
    grid: np.ndarray,
    threshold: float = 0.33,
    rng: random.Random | None = None,
) -> tuple[np.ndarray, int]:
    """
    Um passo do modelo Schelling.

    grid: shape (h, w) — valores: 0 vazio, 1 grupo A, 2 grupo B
    threshold: fração mínima de vizinhos same-group para agente ficar feliz

    Retorna (novo_grid, n_movimentos).
    """
    if rng is None:
        rng = random.Random()
    h, w = grid.shape
    novo = grid.copy()
    movimentos = 0
    vazias = [(i, j) for i in range(h) for j in range(w) if grid[i, j] == 0]

    for i in range(h):
        for j in range(w):
            if grid[i, j] == 0:
                continue
            meu = grid[i, j]
            vizinhos = []
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < h and 0 <= nj < w and grid[ni, nj] != 0:
                        vizinhos.append(grid[ni, nj])
            if not vizinhos:
                continue
            frac_mesmo = sum(1 for v in vizinhos if v == meu) / len(vizinhos)
            if frac_mesmo < threshold and vazias:
                destino = rng.choice(vazias)
                vazias.remove(destino)
                vazias.append((i, j))
                novo[destino] = meu
                novo[i, j] = 0
                movimentos += 1
    return novo, movimentos


def _indice_segregacao(grid: np.ndarray) -> float:
    """
    Índice de segregação simples: fração média de vizinhos same-group.
    0.5 = distribuição aleatória (2 grupos iguais); 1.0 = totalmente segregado.
    """
    h, w = grid.shape
    total_same = 0
    total_viz = 0
    for i in range(h):
        for j in range(w):
            if grid[i, j] == 0:
                continue
            meu = grid[i, j]
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < h and 0 <= nj < w and grid[ni, nj] != 0:
                        total_viz += 1
                        if grid[ni, nj] == meu:
                            total_same += 1
    return total_same / total_viz if total_viz > 0 else 0.5


def tipping_point(
    tamanho_grid: tuple[int, int] = (20, 20),
    fracao_preenchimento: float = 0.7,
    passos: int = 200,
    thresholds_testar: list[float] | None = None,
    seed: int = 42,
) -> dict[float, float]:
    """
    Varredura de thresholds. Para cada τ, inicializa grid aleatório, roda N steps,
    calcula índice de segregação final.
    Esperado: τ=0.3 já produz segregação notável; τ=0.5 produz forte.
    """
    if thresholds_testar is None:
        thresholds_testar = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    h, w = tamanho_grid
    resultados: dict[float, float] = {}
    for tau in thresholds_testar:
        grid = np.zeros((h, w), dtype=int)
        n_ocupadas = int(h * w * fracao_preenchimento)
        idx = np_rng.permutation(h * w)[:n_ocupadas]
        for k, flat in enumerate(idx):
            grupo = 1 if k < n_ocupadas // 2 else 2
            i, j = flat // w, flat % w
            grid[i, j] = grupo
        for _ in range(passos):
            grid, mov = schelling_step(grid, threshold=tau, rng=rng)
            if mov == 0:
                break
        resultados[tau] = _indice_segregacao(grid)
    return resultados
