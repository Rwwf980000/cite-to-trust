"""
تحليل تجربة A/B: أثر عرض المصادر على نسبة التقييم الإيجابي.
يعتمد فقط على numpy / pandas / scipy / matplotlib.
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from pathlib import Path

ALPHA, POWER = 0.05, 0.80
P_BASE, MDE = 0.60, 0.05

# ---------- 1) حجم العينة ----------
def sample_size_two_proportions(p1, p2, alpha=0.05, power=0.80):
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    p_bar = (p1 + p2) / 2
    num = (z_a * np.sqrt(2 * p_bar * (1 - p_bar))
           + z_b * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return int(np.ceil(num / (p2 - p1) ** 2))

n_required = sample_size_two_proportions(P_BASE, P_BASE + MDE, ALPHA, POWER)

# ---------- 2) البيانات ----------
df = pd.read_csv("data/experiment_data.csv")
summary = df.groupby("group").agg(
    users=("user_id", "count"),
    thumbs_up=("thumbs_up", "sum"),
    rate=("thumbs_up", "mean"),
    latency_mean=("latency_ms", "mean"),
)
nA, nB = summary.loc["A", "users"], summary.loc["B", "users"]
xA, xB = summary.loc["A", "thumbs_up"], summary.loc["B", "thumbs_up"]
pA, pB = xA / nA, xB / nB

# ---------- 3) فحص سلامة التوزيع (SRM) ----------
srm_chi2, srm_p = stats.chisquare([nA, nB])

# ---------- 4) اختبار Z لنسبتين ----------
p_pool = (xA + xB) / (nA + nB)
se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / nA + 1 / nB))
z = (pB - pA) / se_pool
p_value = 2 * (1 - stats.norm.cdf(abs(z)))

# فترة ثقة 95% للفرق
se_diff = np.sqrt(pA * (1 - pA) / nA + pB * (1 - pB) / nB)
z_crit = stats.norm.ppf(1 - ALPHA / 2)
diff = pB - pA
ci_low, ci_high = diff - z_crit * se_diff, diff + z_crit * se_diff
rel_lift = diff / pA

# ---------- 5) مقياس الحماية: زمن ظهور الإجابة ----------
latA = df.loc[df.group == "A", "latency_ms"]
latB = df.loc[df.group == "B", "latency_ms"]
t_stat, lat_p = stats.ttest_ind(latB, latA, equal_var=False)
lat_change = (latB.mean() - latA.mean()) / latA.mean()
GUARDRAIL_LIMIT = 0.10   # نقبل زيادة حتى 10% فقط

# ---------- 6) رسم بياني ----------
Path("outputs").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(6, 4.5))
rates = [pA, pB]
errs = [z_crit * np.sqrt(p * (1 - p) / n) for p, n in [(pA, nA), (pB, nB)]]
bars = ax.bar(["A: No citations", "B: With citations"], rates, yerr=errs,
              capsize=8, color=["#9aa5b1", "#2f6fdb"], width=0.55)
for b, r, e in zip(bars, rates, errs):
    ax.text(b.get_x() + b.get_width() / 2, r + e + 0.02, f"{r:.1%}",
            ha="center", fontsize=12, fontweight="bold")
ax.set_ylim(0, 0.8)
ax.set_ylabel("Thumbs-up rate")
ax.set_title("Positive rating rate by group (95% CI)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("outputs/thumbs_up_rate.png", dpi=150)

# ---------- 7) طباعة النتائج ----------
decision = "رفض H0: عرض المصادر يرفع التقييم الإيجابي" if p_value < ALPHA else "لا نرفض H0: لا يوجد دليل كافٍ"
guard_ok = lat_change <= GUARDRAIL_LIMIT

report = f"""# Results

| Metric | A (Control) | B (Treatment) |
|---|---|---|
| Users | {nA:,} | {nB:,} |
| Thumbs-up | {xA:,} | {xB:,} |
| Thumbs-up rate | {pA:.2%} | {pB:.2%} |
| Mean latency (ms) | {latA.mean():.0f} | {latB.mean():.0f} |

- Required sample size per group: **{n_required:,}** (achieved: A={nA:,}, B={nB:,})
- SRM check (chi-square): p = {srm_p:.3f} -> {"OK" if srm_p > 0.01 else "SRM DETECTED"}
- Absolute difference: **{diff:+.2%}** (95% CI: {ci_low:+.2%} to {ci_high:+.2%})
- Relative lift: **{rel_lift:+.1%}**
- Z = {z:.2f}, p-value = **{p_value:.4g}**
- Decision: {decision}
- Guardrail (latency): change = {lat_change:+.1%} (limit +10%), p = {lat_p:.3g} -> {"PASS" if guard_ok else "FAIL"}
"""
Path("outputs/results.md").write_text(report, encoding="utf-8")
print(report)
