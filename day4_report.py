"""
اليوم 4 (الأربعاء): التقرير والعرض
---------------------------------
يقرأ نتائج اليوم 3، يرسم الشكل البياني، ويكتب التقرير والتوصية.
شغّل day3_analysis.py أولًا.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs"
(OUT / "charts").mkdir(parents=True, exist_ok=True)
(OUT / "results").mkdir(parents=True, exist_ok=True)

r = json.loads((OUT / "results" / "results.json").read_text())

# ---------- الرسم البياني ----------
z_crit = stats.norm.ppf(1 - r["alpha"] / 2)
rates = [r["pA"], r["pB"]]
errs = [z_crit * np.sqrt(p * (1 - p) / n) for p, n in [(r["pA"], r["nA"]), (r["pB"], r["nB"])]]

fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(["A: No citations", "B: With citations"], rates, yerr=errs,
              capsize=8, color=["#9aa5b1", "#2f6fdb"], width=0.55)
for b, rate, e in zip(bars, rates, errs):
    ax.text(b.get_x() + b.get_width() / 2, rate + e + 0.02, f"{rate:.1%}",
            ha="center", fontsize=12, fontweight="bold")
ax.set_ylim(0, 0.8)
ax.set_ylabel("Thumbs-up rate")
ax.set_title("Positive rating rate by group (95% CI)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(OUT / "charts" / "thumbs_up_rate.png", dpi=150)

# ---------- القرار ----------
significant = r["p_value"] < r["alpha"]
guard_ok = r["lat_change"] <= r["guardrail_limit"]
srm_ok = r["srm_p"] > 0.01

if significant and guard_ok and srm_ok:
    decision = ("Launch (gradual rollout): citations significantly increase positive ratings without hurting latency."
                if r["diff"] < 0.05 else "Launch: citations significantly increase positive ratings without hurting latency.")
elif not significant:
    decision = "Don't launch yet: no significant evidence of improvement."
else:
    decision = "Don't launch: guardrail or SRM check failed."

caveat = ""
if significant and r["diff"] < 0.05:
    caveat = ("\n> Caution: the observed lift is below the MDE (+5 pts) and the CI lower bound "
              "is close to zero. Prefer a gradual rollout or a larger re-test.")

report = f"""# Results

| Metric | A (Control) | B (Treatment) |
|---|---|---|
| Users | {r['nA']:,} | {r['nB']:,} |
| Thumbs-up | {r['xA']:,} | {r['xB']:,} |
| Thumbs-up rate | {r['pA']:.2%} | {r['pB']:.2%} |
| Mean latency (ms) | {r['latA']:.0f} | {r['latB']:.0f} |

- Required sample per group: **{r['n_required_per_group']:,}** over **{r['days']} days**
- SRM check: p = {r['srm_p']:.3f} -> {"OK" if srm_ok else "SRM DETECTED"}
- Absolute difference: **{r['diff']:+.2%}** (95% CI: {r['ci_low']:+.2%} to {r['ci_high']:+.2%})
- Relative lift: **{r['rel_lift']:+.1%}**
- Z = {r['z']:.2f}, p-value = **{r['p_value']:.4g}**
- Guardrail (latency): {r['lat_change']:+.1%} (limit +{r['guardrail_limit']:.0%}) -> {"PASS" if guard_ok else "FAIL"}

**Decision:** {decision}
{caveat}

- Data quality: missing={r['missing']}, duplicates={r['duplicates']}, users in both groups={r['users_in_both']}

![chart](../charts/thumbs_up_rate.png)
"""
(OUT / "results" / "results.md").write_text(report, encoding="utf-8")
print(report)
