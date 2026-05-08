# OSF Pre-registration - Step-by-step submission instructions

These instructions assume `docs/PREREGISTRATION.md` is the final canonical
pre-registration document. They walk Pedro/Igor through the OSF submission
flow exactly. **The model produces NO output here - human action only.**

---

## 0. Prerequisites

- An OSF account at https://osf.io (free; sign up with academic or
  personal email).
- An ORCID iD linked to the OSF account (preferred; not strictly
  required).
- The frozen file `docs/PREREGISTRATION.md` converted to PDF.

### Convert PREREGISTRATION.md to PDF

```bash
cd /home/pedroafonso/vila-inteia
pandoc docs/PREREGISTRATION.md \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V mainfont="Latin Modern Roman" \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V urlcolor=blue \
  -o /tmp/PREREGISTRATION.pdf

# Fallback if xelatex missing:
pandoc docs/PREREGISTRATION.md -o /tmp/PREREGISTRATION.pdf
# Or via wkhtmltopdf:
pandoc docs/PREREGISTRATION.md -o /tmp/PREREGISTRATION.html
wkhtmltopdf /tmp/PREREGISTRATION.html /tmp/PREREGISTRATION.pdf
```

Verify the PDF: open `/tmp/PREREGISTRATION.pdf` and confirm:
- All four SHA-256 hashes are visible in §3.
- Hypotheses H1-H4 render correctly.
- Predictions table has all UFs.

---

## 1. Submit as preprint (recommended path)

OSF Preprints supports pre-registrations attached as supplementary
material to a preprint record. This gives both a citable DOI and a
public-facing landing page.

1. Go to https://osf.io/preprints
2. Click **"Add a preprint"** (top-right).
3. **Choose preprint provider**:
   - Primary: **MetaArXiv** (open-science / methodology focus)
   - Alternative: **SocArXiv** (political science / social sciences)
   - Alternative: **OSF Preprints** (generic; always available)
4. **Title**:
   `Pre-registered Forecasts for Brazilian 2026 Elections via MRP-Augmented Cohort Empirical Bayes`
5. **Abstract**: paste §1 of `PREREGISTRATION.md` (the "Summary"
   section), trimmed to ~250 words.
6. **Authors**:
   - Pedro Afonso Malheiros (corresponding)
   - Igor Morais Vasconcelos
   Add ORCID iDs if available.
7. **License**: select **CC-BY-4.0**.
8. **Subjects** (multi-select):
   - Political Science
   - Statistical Methodology
   - Forecasting
   - Bayesian Inference (if available)
9. **Tags** (free-text, comma-separated):
   `pre-registration, MRP, Brazilian elections, 2026, political forecasting, empirical Bayes, cohort analysis, election prediction`
10. **Upload primary file**: `/tmp/PREREGISTRATION.pdf`.
11. **Supplementary materials** (optional but recommended):
    - `data/predictions_2026.json`
    - `data/political_best_config.json`
    - A `frozen_hashes.txt` containing the four SHA-256 lines (see
      generation command below).
12. Click **"Submit"**.

### Generate `frozen_hashes.txt` for upload

```bash
cd /home/pedroafonso/vila-inteia
sha256sum data/political_best_config.json data/predictions_2026.json \
          engine/political_cohort.py scripts/predict_2026.py \
  > /tmp/frozen_hashes.txt
cat /tmp/frozen_hashes.txt
```

---

## 2. Alternative path - OSF Registries (formal pre-registration)

For a stricter pre-registration record (read-only after submission, with
embargo options), use OSF Registries instead of Preprints:

1. Go to https://osf.io/registries
2. Click **"Add new"** -> **"Submit a registration"**.
3. Choose template:
   - **OSF Preregistration** (generic) - simplest
   - **AsPredicted** (concise; 9 questions)
   - **Pre-Registration in Social Psychology** (detailed)
   We recommend **OSF Preregistration** for our use case.
4. Fill in fields, copying content from `PREREGISTRATION.md`:
   - Hypotheses -> §2 of the doc
   - Sampling plan / data -> §3 (frozen artifacts) and §4 (methodology)
   - Analysis plan -> §4-5 (methodology and decision rule)
   - Other -> §7 outcome evaluation, §8 pre-commitments
5. Attach `PREREGISTRATION.pdf` as a supplementary file.
6. Optional: select **embargo** until 2026-10-05 (one day after the
   election) to prevent cherry-picking accusations. The record stays
   private until the embargo lifts.
7. Click **"Register"**.

Both paths produce a citable DOI. The Preprints path is more visible;
the Registries path is more rigorous.

---

## 3. After submission - record the DOI

OSF returns a DOI of the form `10.31219/osf.io/<short-id>` (Preprints) or
`10.17605/OSF.IO/<short-id>` (Registries) within minutes of submission.

Update `docs/PREREGISTRATION.md` §9:

```markdown
DOI: 10.31219/osf.io/<short-id>
OSF URL: https://osf.io/<short-id>/
Submission date: 2026-MM-DD
```

Then commit:

```bash
cd /home/pedroafonso/vila-inteia
git add docs/PREREGISTRATION.md
git commit -m "docs(prereg): record OSF DOI <short-id>"
git push
```

---

## 4. Cross-link with arXiv submission

Once both pre-registration (OSF) and preprint (arXiv) are live:

1. In the arXiv submission Comments field, add:
   `Pre-registered at OSF: https://doi.org/10.31219/osf.io/<short-id>`
2. In the OSF preprint description, add:
   `Companion preprint: https://arxiv.org/abs/2611.NNNNN`
3. Both updates can happen post-publication (OSF allows description
   edits; arXiv allows v2 with metadata-only changes).

---

## 5. Expected timeline

| Step | Duration |
|------|----------|
| Account setup + ORCID | 10 min one-time |
| Convert MD -> PDF | 1 min |
| Fill OSF form + upload | 15 min |
| Moderation (Preprints) | 24-48h auto-publish |
| Moderation (Registries) | immediate (no review) |
| DOI propagation to DataCite | 1-3 business days |

Total: **~30 minutes of human work**, plus 24-48h wait for moderation.

---

## 6. Troubleshooting

- **"PDF too large"**: OSF caps individual files at 5 GB; not an issue here.
- **"Subject not found"**: use any closest match; you can edit subjects
  post-publication.
- **"Cannot find MetaArXiv"**: scroll the provider list; if missing in
  your region, fall back to SocArXiv or generic OSF Preprints.
- **"Want to revise after submission"**: OSF Preprints allows new
  versions; OSF Registries does NOT (only addenda). Pre-registration is
  meant to be immutable - if you need to change methodology, document it
  in the post-mortem instead.

---

## 7. Cross-references

- Pre-registration document: `docs/PREREGISTRATION.md`
- arXiv submission: `docs/ARXIV_SUBMISSION.md`
- Code freeze procedure: `docs/PREREG_FREEZE_PROCEDURE.md`
