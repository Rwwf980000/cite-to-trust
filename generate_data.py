"""
توليد بيانات محاكاة لتجربة A/B:
هل عرض مصادر الإجابة (Citations) في المساعد الذكي يرفع نسبة التقييم الإيجابي؟

A (Control)   : إجابة بدون مصادر
B (Treatment) : نفس الإجابة مع روابط المصادر
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
DAYS = 14                 # مدة التجربة (أسبوعين كاملين)
USERS_PER_DAY = 300       # متوسط المستخدمين الذين يقيّمون يوميًا
P_A = 0.60                # النسبة الافتراضية للتقييم الإيجابي في A
P_B = 0.65                # النسبة الافتراضية في B (التأثير المفترض)
LAT_A, LAT_B, LAT_SD = 1800, 1850, 400   # زمن ظهور الإجابة بالمللي ثانية (مقياس حماية)

rng = np.random.default_rng(SEED)
rows = []
user_id = 1
start = pd.Timestamp("2026-10-01")

for day in range(DAYS):
    # تذبذب يومي بسيط في عدد المستخدمين
    n_today = rng.poisson(USERS_PER_DAY)
    for _ in range(n_today):
        group = rng.choice(["A", "B"])          # توزيع عشوائي 50/50 على مستوى المستخدم
        p = P_A if group == "A" else P_B
        lat_mean = LAT_A if group == "A" else LAT_B
        rows.append({
            "user_id": user_id,
            "date": (start + pd.Timedelta(days=day)).date(),
            "group": group,
            "thumbs_up": int(rng.random() < p),
            "latency_ms": max(200, round(rng.normal(lat_mean, LAT_SD))),
        })
        user_id += 1

df = pd.DataFrame(rows)
Path("data").mkdir(exist_ok=True)
df.to_csv("data/experiment_data.csv", index=False)
print(f"Saved {len(df):,} rows -> data/experiment_data.csv")
print(df.groupby("group")["thumbs_up"].agg(["count", "mean"]))
