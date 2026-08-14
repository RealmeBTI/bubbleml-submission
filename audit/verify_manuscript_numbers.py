#!/usr/bin/env python3
import pathlib
import sys
import csv

def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    ledger_path = root / "numerical_ledger.csv"
    md_path = root / "manuscript" / "full_manuscript.md"
    tex_path = root / "manuscript" / "manuscript_elsarticle.tex"

    if not ledger_path.exists():
        print("numerical_ledger.csv not found.")
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    tex_text = tex_path.read_text(encoding="utf-8")

    # The canonical numbers for 48x48 n=11 Section 4.1 from ledger
    expected_numbers = [
        "0.04917", # Mass Cons
        "0.18853", # Interface RMSE
        "0.09277", # Interface Jump MAE
        ".0214844", # Holm Mass Cons
        ".46875", # Holm Interface RMSE
        ".588867", # Holm Jump MAE
    ]
    
    retracted_numbers = [
        "0.04494",
        "0.50190",
        "0.43147",
        "statistically significant Pareto trade-off", # Because there is no Pareto trade-off at 48x48
    ]

    failed = False
    
    for text, name in [(md_text, "full_manuscript.md"), (tex_text, "manuscript_elsarticle.tex")]:
        for num in expected_numbers:
            if num not in text:
                print(f"[FAIL] Expected canonical number {num} not found in {name}")
                failed = True
            else:
                print(f"[PASS] Expected canonical number {num} found in {name}")
                
        for num in retracted_numbers:
            if num in text:
                print(f"[FAIL] Retracted artifact '{num}' STILL FOUND in {name}")
                failed = True
            else:
                print(f"[PASS] Retracted artifact '{num}' absent from {name}")

    if failed:
        print("\n[ERROR] Manuscript regression detected! Canonical numbers missing or retracted claims present.")
        sys.exit(1)
    
    print("\n[SUCCESS] Manuscript matches canonical ledger. No regressions found.")

if __name__ == "__main__":
    main()
