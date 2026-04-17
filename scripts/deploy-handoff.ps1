# deploy-handoff.ps1
# Script único que finaliza o handoff da Vila INTEIA para desenvolvedor externo.
#
# O QUE ELE FAZ:
#   1. Remove lixo (.planning, .playwright-mcp, .tmp_*, screenshots soltos)
#   2. Move docs privados (investimento, parecer diretores) para ~/vila-inteia-privado/
#   3. Remove .env do tracking do git (se estiver tracked)
#   4. Sincroniza com origin (fetch, cria branch handoff/dev-v1)
#   5. Commit temático de tudo
#   6. Push da branch
#
# USO:
#   cd C:\Agentes\vila-inteia
#   powershell -ExecutionPolicy Bypass -File .\deploy-handoff.ps1
#
# ATENÇÃO:
#   - roda em Bash-less Windows (PowerShell nativo)
#   - NÃO faz push para main. Só cria branch + sobe. Você revê e faz merge manual.

$ErrorActionPreference = "Stop"
$repo = "C:\Agentes\vila-inteia"
$privado = "C:\Users\IgorPC\vila-inteia-privado"
$branch = "handoff/dev-v1"

function Section($t) { Write-Host "`n==== $t ====" -ForegroundColor Cyan }
function Ok($t)     { Write-Host "  [OK] $t"    -ForegroundColor Green }
function Warn($t)   { Write-Host "  [!!] $t"    -ForegroundColor Yellow }

if (-not (Test-Path $repo)) {
    Write-Host "Repo não encontrado: $repo" -ForegroundColor Red
    exit 1
}

Set-Location $repo

# =========================================================
Section "1. Pasta privada para docs sigilosos"
# =========================================================

if (-not (Test-Path $privado)) {
    New-Item -ItemType Directory -Path $privado | Out-Null
    Ok "criada $privado"
} else {
    Ok "já existe $privado"
}

# Lista de docs que vão para pasta privada
$docsPrivados = @(
    "PARECER_4_DIRETORES.md",
    "INVESTIMENTO_MIRANTE*.md",
    "MAESTRAL*.md",
    "PROPOSTA_*.md",
    "MEL_*.md",
    "COMBOS_POR_AREA.md",
    "PLANO_REFORMA_VILA.md"
)

$pastasVarredura = @($repo, (Join-Path $repo "docs"))
foreach ($base in $pastasVarredura) {
    if (-not (Test-Path $base)) { continue }
    foreach ($padrao in $docsPrivados) {
        Get-ChildItem -Path $base -Filter $padrao -ErrorAction SilentlyContinue | ForEach-Object {
            $destino = Join-Path $privado $_.Name
            Move-Item -Path $_.FullName -Destination $destino -Force
            $rel = $_.FullName.Substring($repo.Length).TrimStart('\')
            Ok "movido: $rel -> vila-inteia-privado"
        }
    }
}

# =========================================================
Section "2. Remover lixo do repo"
# =========================================================

$lixo = @(
    ".planning",
    ".playwright-mcp",
    ".tmp_*",
    "__pycache__"
)

foreach ($padrao in $lixo) {
    Get-ChildItem -Path $repo -Filter $padrao -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.PSIsContainer) {
            Remove-Item -Path $_.FullName -Recurse -Force
            Ok "removido (dir): $($_.Name)"
        } else {
            Remove-Item -Path $_.FullName -Force
            Ok "removido (arq): $($_.Name)"
        }
    }
}

# Screenshots soltos na raiz
$imagensRaiz = Get-ChildItem -Path $repo -Filter "*.png" -File -ErrorAction SilentlyContinue
$pastaScreenshots = Join-Path $repo "docs\screenshots"
if ($imagensRaiz -and -not (Test-Path $pastaScreenshots)) {
    New-Item -ItemType Directory -Path $pastaScreenshots -Force | Out-Null
}
foreach ($img in $imagensRaiz) {
    Move-Item $img.FullName (Join-Path $pastaScreenshots $img.Name) -Force
    Ok "screenshot -> docs/screenshots/: $($img.Name)"
}

# =========================================================
Section "3. Garantir .env fora do tracking"
# =========================================================

$envPath = Join-Path $repo ".env"
if (Test-Path $envPath) {
    try {
        & git rm --cached .env 2>$null
        if ($LASTEXITCODE -eq 0) {
            Ok ".env removido do tracking (arquivo local preservado)"
        } else {
            Ok ".env já não estava tracked"
        }
    } catch {
        Warn "falha ao rodar git rm --cached .env: $_"
    }
} else {
    Ok ".env inexistente no disco (OK pro handoff)"
}

# Conferir .gitignore
$gi = Get-Content (Join-Path $repo ".gitignore") -Raw
if ($gi -notmatch "(?m)^\.env$") {
    Add-Content (Join-Path $repo ".gitignore") "`n.env`n"
    Ok "adicionado .env ao .gitignore"
} else {
    Ok ".env já listado em .gitignore"
}

# =========================================================
Section "4. Sincronizar com GitHub"
# =========================================================

try {
    & git fetch origin 2>&1 | Out-Null
    Ok "git fetch origin"
} catch {
    Warn "falha no fetch — verifique credenciais"
}

# Checa se a branch já existe
$branchExiste = & git rev-parse --verify "$branch" 2>$null
if ($branchExiste) {
    Warn "branch $branch já existe — vou continuar nela"
    & git checkout $branch 2>&1 | Out-Null
} else {
    & git checkout -b $branch 2>&1 | Out-Null
    Ok "branch $branch criada"
}

# =========================================================
Section "5. Commits temáticos"
# =========================================================

# Garante index limpo antes
& git add -A 2>&1 | Out-Null

# Helper: commit apenas se tiver mudança staged relevante
function CommitIfStaged($mensagem, $globs) {
    & git reset HEAD -- . 2>&1 | Out-Null
    foreach ($g in $globs) {
        & git add -- $g 2>&1 | Out-Null
    }
    $staged = & git diff --cached --name-only
    if ($staged) {
        & git commit -m $mensagem 2>&1 | Out-Null
        Ok "commit: $mensagem"
    } else {
        Ok "sem mudanças para: $mensagem"
    }
}

CommitIfStaged "chore: remove .planning, .tmp, caches e docs privados" @(
    ".gitignore", ".env.example", "docs/screenshots"
)

CommitIfStaged "feat(jornal): Chateaubriand editor-chefe + pipeline Mirante" @(
    "engine/chateaubriand.py", "engine/mirante_client.py"
)

CommitIfStaged "feat(vilas): save/load + pacotes de habitantes" @(
    "engine/save_load.py", "engine/pacotes_habitantes.py", "data/pacotes"
)

CommitIfStaged "feat(governanca): economia viva + constituicao com enforcement" @(
    "engine/economia.py",
    "engine/constituicao.py",
    "engine/constituinte.py",
    "engine/executor_constitucional.py"
)

CommitIfStaged "feat(mirofish): bridge para simulacao de rede social" @(
    "engine/mirofish_bridge.py"
)

CommitIfStaged "chore(seguranca): sanitiza URLs hardcoded e carregamento .env" @(
    "engine/supabase_db.py", "teste_prompt_rico.py"
)

CommitIfStaged "docs: README + docs/ completo + CONTRIBUTING + CONSTITUICAO_VILA" @(
    "README.md",
    "CONTRIBUTING.md",
    "CONSTITUICAO_VILA.md",
    "FRAMEWORK_INTERACOES.md",
    "docs/ARCHITECTURE.md",
    "docs/INTEGRATIONS.md",
    "docs/DEPLOY.md",
    "docs/ROADMAP.md",
    "docs/FLUXO_DADOS.md",
    "docs/EVOLUCAO_GENOMAS.md",
    "docs/API_COLMEIA.md",
    "docs/API_COLMEIA_QUICKSTART.md",
    "ARCHITECTURE.md",
    "INTEGRATIONS.md",
    "DEPLOY.md",
    "ROADMAP.md"
)

CommitIfStaged "feat(sql): migrations versionadas" @(
    "sql/migrations"
)

CommitIfStaged "chore(scripts): script de handoff + utilitarios" @(
    "scripts/deploy-handoff.ps1",
    "scripts"
)

# Qualquer resto
& git add -A 2>&1 | Out-Null
$staged = & git diff --cached --name-only
if ($staged) {
    & git commit -m "chore: demais ajustes do handoff" 2>&1 | Out-Null
    Ok "commit: demais ajustes"
}

# =========================================================
Section "6. Push"
# =========================================================

try {
    & git push -u origin $branch 2>&1 | Tee-Object -Variable pushOut | Out-Null
    Ok "push origin $branch"
} catch {
    Warn "push falhou — rode manualmente: git push -u origin $branch"
    Write-Host $_ -ForegroundColor Red
}

# =========================================================
Section "PRONTO"
# =========================================================

Write-Host ""
Write-Host "Branch de handoff no ar:   https://github.com/igormorais123/vila-inteia/tree/$branch" -ForegroundColor Green
Write-Host "Pra mergear em main:       abre PR no GitHub, revisa e clica merge" -ForegroundColor Green
Write-Host "Docs privados foram para:  $privado" -ForegroundColor Green
Write-Host ""
