# Pre-registration code freeze procedure - `v1.2-prereg`

This file is the operational checklist for freezing the Vila INTEIA
political forecaster at the state used in `docs/PREREGISTRATION.md`. It
exists so the freeze is reproducible and auditable.

---

## 1. Verify clean working tree

```bash
cd /home/pedroafonso/vila-inteia
git status
```

Expected: only `docs/PREREGISTRATION.md`, `docs/ARXIV_SUBMISSION.md`,
`docs/OSF_PREREG_INSTRUCTIONS.md`, and `docs/PREREG_FREEZE_PROCEDURE.md`
untracked or newly added. **No modifications to**:

- `data/political_best_config.json`
- `data/predictions_2026.json`
- `engine/political_cohort.py`
- `scripts/predict_2026.py`

If those four files are dirty, **abort**. Resolve, re-run SHA, update
PREREGISTRATION.md, and retry.

---

## 2. Verify SHA-256 hashes match `PREREGISTRATION.md` §3

```bash
sha256sum data/political_best_config.json data/predictions_2026.json \
          engine/political_cohort.py scripts/predict_2026.py
```

Expected output (must match exactly):

```
ed24363e302a97d86d3cc5653fba8ae7c1f207d70418a0b62377e9f818155c7c  data/political_best_config.json
9355abc7adc4593fbebc620ef9981096d6e7ef59fa967dfbade59c97b19c3513  data/predictions_2026.json
f4263ef3ce93ac60b5db3358e92caf30b5cd61ad3ce1c9cb9e27a3cc22fc74b4  engine/political_cohort.py
9e82f1e6752f0444a72d1cdae27985e88a2bc24886fdecbac36a9655e5948d16  scripts/predict_2026.py
```

If any hash differs, **abort and reconcile** before tagging.

---

## 3. Commit pre-registration documents

```bash
cd /home/pedroafonso/vila-inteia
git add docs/PREREGISTRATION.md \
        docs/ARXIV_SUBMISSION.md \
        docs/OSF_PREREG_INSTRUCTIONS.md \
        docs/PREREG_FREEZE_PROCEDURE.md
git commit -m "docs(prereg): add Phase 6 pre-registration package for 2026 BR elections"
```

---

## 4. Tag the freeze

```bash
git tag -a v1.2-prereg -m "Frozen state for 2026 BR election predictions pre-registration

Frozen artifacts (SHA-256):
  data/political_best_config.json: ed24363e302a97d86d3cc5653fba8ae7c1f207d70418a0b62377e9f818155c7c
  data/predictions_2026.json:      9355abc7adc4593fbebc620ef9981096d6e7ef59fa967dfbade59c97b19c3513
  engine/political_cohort.py:      f4263ef3ce93ac60b5db3358e92caf30b5cd61ad3ce1c9cb9e27a3cc22fc74b4
  scripts/predict_2026.py:         9e82f1e6752f0444a72d1cdae27985e88a2bc24886fdecbac36a9655e5948d16

Election: 2026-10-04 (1st round). Post-mortem will follow at v1.2-postmortem.
Pre-registration date: 2026-05-07."
```

If GPG signing is configured (`-s`), prefer:

```bash
git tag -s v1.2-prereg -m "..."
```

---

## 5. Push tag to origin

```bash
git push origin main
git push origin v1.2-prereg
```

Verify on GitHub:

```bash
gh release view v1.2-prereg 2>/dev/null \
  || gh api repos/inteia-br/vila-inteia/git/refs/tags/v1.2-prereg
```

---

## 6. Optionally publish a GitHub Release tied to the tag

```bash
gh release create v1.2-prereg \
  --title "v1.2-prereg - 2026 BR election forecast freeze" \
  --notes-file docs/PREREGISTRATION.md \
  --verify-tag
```

---

## 7. Submit to OSF + arXiv

After the tag is pushed:

1. Follow `docs/OSF_PREREG_INSTRUCTIONS.md` step-by-step.
2. Once OSF returns a DOI, edit `docs/PREREGISTRATION.md` §9 with the
   DOI and OSF URL, then commit:
   ```bash
   git add docs/PREREGISTRATION.md
   git commit -m "docs(prereg): record OSF DOI <short-id>"
   git push
   ```
   This commit lives **after** `v1.2-prereg`. The frozen tag itself is
   not amended.
3. Follow `docs/ARXIV_SUBMISSION.md` to compile and submit the preprint.

---

## 8. Post-election (post Oct 4, 2026)

1. Create `docs/POSTMORTEM_2026.md` with full TSE comparison.
2. Tag `v1.2-postmortem` at the post-mortem commit.
3. Update OSF preprint with v2 (description-only update; do NOT change
   the original PDF - the immutability is the point).
4. Submit a v2 to arXiv with the post-mortem appended.

---

## 9. Rollback safety

If the freeze must be undone (e.g. critical bug discovered before
submission to OSF):

```bash
git tag -d v1.2-prereg                     # local
git push origin :refs/tags/v1.2-prereg     # remote
```

Document the reason in `docs/PREREG_INVALIDATIONS.md` and create a new
freeze tag (e.g. `v1.2.1-prereg`) with a fresh PREREGISTRATION.md and
fresh SHA-256s.

**Do not** rewrite history by force-pushing main. The aborted freeze
must remain visible in git history for audit.

---

## Cross-references

- Pre-registration: `docs/PREREGISTRATION.md`
- OSF instructions: `docs/OSF_PREREG_INSTRUCTIONS.md`
- arXiv plan: `docs/ARXIV_SUBMISSION.md`
