"""
تشغيل المشروع كاملًا بالترتيب: python main.py
مشروع دورة "التجارب واختبارات A/B والاستدلال السببي" - أكاديمية سدايا
"""
import runpy
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
STEPS = ["day1_design.py", "day2_sample_size.py", "day3_analysis.py", "day4_report.py"]

for step in STEPS:
    print(f"\n{'=' * 15} {step} {'=' * 15}")
    runpy.run_path(str(BASE / step), run_name="__main__")

print("\nتم. النتائج في outputs/results والرسم في outputs/charts")
