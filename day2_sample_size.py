"""
اليوم 2 (الإثنين): حجم العينة والمدة
-----------------------------------
حساب عدد المستخدمين المطلوب لكل مجموعة، ثم مدة التجربة بالأيام.
"""
import math
from scipy import stats
from day1_design import ALPHA, POWER, BASELINE, MDE, USERS_PER_DAY


def sample_size_two_proportions(p1, p2, alpha=0.05, power=0.80):
    """حجم العينة لكل مجموعة لاختبار الفرق بين نسبتين (ثنائي الطرف)."""
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    p_bar = (p1 + p2) / 2
    num = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
           + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p2 - p1) ** 2)


def duration_days(n_per_group, users_per_day):
    """الأيام اللازمة، مقرّبة لأسابيع كاملة لتغطية أيام الأسبوع ونهايته."""
    raw = math.ceil(2 * n_per_group / users_per_day)
    return raw, math.ceil(raw / 7) * 7


N_PER_GROUP = sample_size_two_proportions(BASELINE, BASELINE + MDE, ALPHA, POWER)
RAW_DAYS, DAYS = duration_days(N_PER_GROUP, USERS_PER_DAY)

if __name__ == "__main__":
    print(f"Baseline = {BASELINE:.0%}, MDE = +{MDE:.0%}, alpha = {ALPHA}, power = {POWER:.0%}")
    print(f"حجم العينة لكل مجموعة: {N_PER_GROUP:,}")
    print(f"الإجمالي: {2 * N_PER_GROUP:,}")
    print(f"المدة: {RAW_DAYS} يوم -> نقرّبها إلى {DAYS} يومًا (أسابيع كاملة)")
