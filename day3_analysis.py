"""
اليوم 3 (الثلاثاء): خطة التحليل ثم التحليل
-----------------------------------------
خطة التحليل (محددة قبل رؤية النتائج):
  1. توليد بيانات المحاكاة لمدة التجربة
  2. فحص سلامة التوزيع (SRM) باختبار Chi-square
  3. اختبار Z لنسبتين للمقياس الأساسي + فترة ثقة 95%
  4. فحص مقياس الحماية (زمن الإجابة) باختبار Welch t-test
النتائج تُحفظ في outputs/results/results.json ليستخدمها اليوم 4.
"""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
import numpy as np
import pandas as pd
from scipy import stats
from day1_design import ALPHA, USERS_PER_DAY, GUARDRAIL_LIMIT
from day2_sample_size import N_PER_GROUP, DAYS

# ---------- 1) توليد بيانات المحاكاة ----------
SEED = 42
P_A, P_B = 0.60, 0.65                    # النسب الحقيقية المفترضة في المحاكاة
LAT_A, LAT_B, LAT_SD = 1800, 1850, 400    # زمن الإجابة (ms)


def simulate():
    rng = np.random.default_rng(SEED)
    rows, uid = [], 1
    start = pd.Timestamp("2026-10-01")
    for day in range(DAYS):
        for _ in range(rng.poisson(USERS_PER_DAY)):
            g = rng.choice(["A", "B"])
            rows.append({
                "user_id": uid,
                "date": (start + pd.Timedelta(days=day)).date(),
                "group": g,
                "thumbs_up": int(rng.random() < (P_A if g == "A" else P_B)),
                "latency_ms": max(200, round(rng.normal(LAT_A if g == "A" else LAT_B, LAT_SD))),
            })
            uid += 1
    return pd.DataFrame(rows)


(BASE / "data").mkdir(exist_ok=True)
df = simulate()
df.to_csv(BASE / "data" / "experiment_data.csv", index=False)

# ---------- فحوص جودة البيانات ----------
missing = int(df.isna().sum().sum())                 # قيم مفقودة
dup_users = int(df.user_id.duplicated().sum())       # سجلات مكررة
users_in_both = int((df.groupby("user_id").group.nunique() > 1).sum())  # مستخدم في المجموعتين
invalid_metric = int((~df.thumbs_up.isin([0, 1])).sum())
assert missing == 0 and dup_users == 0 and users_in_both == 0 and invalid_metric == 0, "فشل فحص جودة البيانات"

nA, nB = (df.group == "A").sum(), (df.group == "B").sum()
xA = df.loc[df.group == "A", "thumbs_up"].sum()
xB = df.loc[df.group == "B", "thumbs_up"].sum()
pA, pB = xA / nA, xB / nB

# ---------- 2) فحص SRM ----------
_, srm_p = stats.chisquare([nA, nB])

# ---------- 3) اختبار Z لنسبتين ----------
p_pool = (xA + xB) / (nA + nB)
z = (pB - pA) / np.sqrt(p_pool * (1 - p_pool) * (1 / nA + 1 / nB))
p_value = 2 * (1 - stats.norm.cdf(abs(z)))

z_crit = stats.norm.ppf(1 - ALPHA / 2)
se_diff = np.sqrt(pA * (1 - pA) / nA + pB * (1 - pB) / nB)
diff = pB - pA
ci = (diff - z_crit * se_diff, diff + z_crit * se_diff)

# ---------- 4) مقياس الحماية ----------
latA = df.loc[df.group == "A", "latency_ms"]
latB = df.loc[df.group == "B", "latency_ms"]
_, lat_p = stats.ttest_ind(latB, latA, equal_var=False)
lat_change = (latB.mean() - latA.mean()) / latA.mean()

results = {
    "n_required_per_group": int(N_PER_GROUP), "days": int(DAYS),
    "nA": int(nA), "nB": int(nB), "xA": int(xA), "xB": int(xB),
    "pA": float(pA), "pB": float(pB),
    "srm_p": float(srm_p),
    "diff": float(diff), "ci_low": float(ci[0]), "ci_high": float(ci[1]),
    "rel_lift": float(diff / pA), "z": float(z), "p_value": float(p_value),
    "latA": float(latA.mean()), "latB": float(latB.mean()),
    "lat_change": float(lat_change), "lat_p": float(lat_p),
    "missing": missing, "duplicates": dup_users, "users_in_both": users_in_both,
    "guardrail_limit": GUARDRAIL_LIMIT, "alpha": ALPHA,
}
(BASE / "outputs" / "results").mkdir(parents=True, exist_ok=True)
(BASE / "outputs" / "results" / "results.json").write_text(json.dumps(results, indent=2))

if __name__ == "__main__":
    print(f"البيانات: {len(df):,} مستخدم على {DAYS} يومًا -> data/experiment_data.csv")
    print(f"فحص الجودة: مفقود={missing}، مكرر={dup_users}، في المجموعتين={users_in_both} (سليم)")
    print(f"A: {pA:.2%} ({nA:,})   B: {pB:.2%} ({nB:,})")
    print(f"SRM p = {srm_p:.3f}")
    print(f"الفرق = {diff:+.2%}  CI95 = [{ci[0]:+.2%}, {ci[1]:+.2%}]")
    print(f"Z = {z:.2f}, p-value = {p_value:.4g}")
    print(f"زمن الإجابة: {lat_change:+.1%} (p = {lat_p:.3g})")
