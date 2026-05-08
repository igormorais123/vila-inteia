# arXiv Submission Plan - Vila MRP Political Forecasting

**Target archives:**
- Primary: `stat.AP` (Statistics - Applications)
- Cross-list: `stat.ML` (Statistics - Machine Learning), `cs.LG` (optional)

**License:** CC-BY-4.0 (recommended for OSF compatibility) under arXiv
perpetual non-exclusive distribution license.

**Authors:**
- Pedro Afonso Malheiros (Vila INTEIA / Veredictos) - corresponding
- Igor Morais Vasconcelos (Vila INTEIA)

**ORCID IDs:**
- Pedro: `<ORCID-pending>`
- Igor: `<ORCID-pending>`

(Register at https://orcid.org/register before submitting; arXiv requires
a valid endorsement or a previous arXiv submission for a new account.)

---

## Submission package

### Source manuscript

Primary: `docs/artigo/vila_mrp_artigo_v2.md` (Phase 5 deliverable).
Fallback chain if v2 not yet finalized:
1. `docs/artigo/vila_mrp_artigo_v1.md`
2. `docs/HONEST_FORECASTING_ARTICLE.md` (existing baseline)

### Compile-to-PDF pipeline

Two equivalent paths; LaTeX preferred but Markdown -> PDF accepted by arXiv:

```bash
# Path A - LaTeX (preferred):
cd /home/pedroafonso/vila-inteia
pandoc docs/artigo/vila_mrp_artigo_v2.md \
  --from markdown \
  --to latex \
  --standalone \
  --bibliography docs/artigo/refs.bib \
  --csl docs/artigo/apa.csl \
  -o /tmp/vila_mrp.tex
pdflatex -output-directory=/tmp /tmp/vila_mrp.tex
biber /tmp/vila_mrp
pdflatex -output-directory=/tmp /tmp/vila_mrp.tex
pdflatex -output-directory=/tmp /tmp/vila_mrp.tex

# Path B - Markdown -> PDF direct (fallback):
python3 /tmp/build_pdf_mrp.py \
  --source docs/artigo/vila_mrp_artigo_v2.md \
  --out /tmp/vila_mrp.pdf \
  --dpi 300
```

If `/tmp/build_pdf_mrp.py` is missing, use:

```bash
pandoc docs/artigo/vila_mrp_artigo_v2.md \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V mainfont="Latin Modern Roman" \
  -o /tmp/vila_mrp.pdf
```

### Required figures (300 DPI)

- `fig_year_fold_cv.png` - per-year accuracy bars (2010-2024).
- `fig_calibration.png` - reliability curve at T<=30.
- `fig_selective_coverage.png` - tau vs accuracy vs coverage.
- `fig_brier_decomp.png` - reliability/resolution/uncertainty.
- `fig_2026_picks.png` - top-pick probabilities by office.

All figures live under `docs/artigo/figures/` (create if absent).

---

## Abstract (placeholder - replace from manuscript)

> We present Vila MRP, an MRP-augmented cohort empirical-Bayes forecaster
> for Brazilian elections (presidente, governador, senador), achieving
> 97.21% accuracy under year-fold cross-validation across six BR cycles
> (2010, 2016, 2018, 2020, 2022, 2024; n=394 events at T<=30 days). The
> model ensembles a Stein-shrunk cohort prior over `(cargo, days_bin,
> lead_bin, incumbente, regime)`, a Linzer (2013) state-space win-prob
> from polling leads, and a Laplace-smoothed (UF, regime) MRP state
> baseline. Selective gating at tau=0.40 yields 100% accuracy at 11%
> coverage; tau=0.15 yields 96.1% at 92% coverage. We pre-register
> 2026 BR predictions (frozen 2026-05-07, SHA-256 verified) prior to
> the October 4, 2026 election, with a public commitment to publish the
> outcome evaluation regardless of result.

(Final abstract to be copied verbatim from `vila_mrp_artigo_v2.md`.)

---

## Submission checklist

- [ ] PDF compiled successfully (no LaTeX errors, all references resolved).
- [ ] All figures embedded at 300 DPI; vector PDF/SVG where possible.
- [ ] References complete (target >= 30 entries: Linzer 2013, Gelman & Hill
      2007, Park-Gelman-Bafumi 2004 MRP, Robbins 1956 EB, Stein 1956,
      Brier 1950, Murphy 1973 decomp, DeGroot-Fienberg 1983 calibration,
      Platt 1999, Zadrozny-Elkan 2002 isotonic, Tetlock superforecasters,
      Manifold/Polymarket benchmarks, etc.).
- [ ] No em-dashes in body text (per Vila style policy). Use ` - ` or `.`.
- [ ] Bibliography `.bib` file at `docs/artigo/refs.bib` (recommended).
- [ ] Author affiliations on title page.
- [ ] ORCID IDs (placeholder if missing - obtain before submission).
- [ ] arXiv abstract (max 1920 chars, plain ASCII; no LaTeX).
- [ ] License declaration: CC-BY-4.0.
- [ ] Pre-registration link: OSF DOI from `docs/PREREGISTRATION.md`.
- [ ] Frozen artifact SHAs cited in §3 of pre-registration.
- [ ] Reproducibility section: `git clone ... && git checkout v1.2-prereg
      && python scripts/predict_2026.py`.
- [ ] Endorsement: arXiv `stat.AP` requires endorsement for first-time
      submitters - request from a senior co-author or affiliated researcher.

---

## Submit (manual; one-line instructions)

```bash
# Manual submission (recommended for first-time):
#   1. Go to https://arxiv.org/submit
#   2. Click "Start New Submission"
#   3. Choose archive: stat.AP (primary)
#   4. Cross-list: stat.ML
#   5. Upload /tmp/vila_mrp.pdf + docs/artigo/figures/* (zip optional)
#   6. Paste abstract from manuscript
#   7. Add authors + ORCID + affiliations
#   8. License: CC-BY-4.0
#   9. Comments field: "Pre-registered at OSF: <DOI from step 9 of PREREGISTRATION.md>"
#  10. Click "Submit"
#
# arXiv API (advanced; requires registered identity):
#   See https://info.arxiv.org/help/api/user-manual.html
#   The submission API is paper-specific and currently requires browser-based
#   auth + manual confirmation. There is no fully-automated CLI submit.
```

---

## Expected timeline

- **Day 0**: Submit. Status "submitted" -> "processing".
- **Day 0-1 business**: arXiv moderation (mostly automated; flagged papers
  go to human review).
- **Day 1-3 business**: Paper appears on arXiv listing as `arXiv:2611.NNNNN`
  (May 2026 ID range). DOI registered with DataCite if requested.
- **Day 3+**: Cross-listing to `stat.ML` propagates within 24h.

If moderation flags the submission (e.g. missing endorsement, unclear
contribution, ToS issue), arXiv emails the corresponding author.
Resubmit after addressing the issue.

---

## Cross-references

- Pre-registration: `docs/PREREGISTRATION.md`
- OSF submission instructions: `docs/OSF_PREREG_INSTRUCTIONS.md`
- Freeze procedure: `docs/PREREG_FREEZE_PROCEDURE.md`
- Frozen snapshot: `data/predictions_2026.json` (SHA in PREREGISTRATION.md §3)
