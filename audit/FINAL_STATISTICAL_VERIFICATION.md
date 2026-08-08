# Final Statistical Verification

The current source was executed with:

```text
python scripts/reproduce_reported_results.py --output-dir reproduced
python -m pytest -q
```

The stored-result command returned `PASS`. The test suite executed 38 tests and
reported **38 passed**, with no skip or expected-failure output.

The reproduction script recomputes the retained 11-seed tutorial paired
contrasts and lambda=.30 non-inferiority result, using exact sign-flip tests and
the stored Holm-adjusted values. It verifies the tutorial interface-temperature
RMSE contrast (Holm=.03515625), interface jump contrast (Holm=.021484375), mass
MAE contrast (Holm=.021484375), and the lambda=.30 one-sided non-inferiority
p=.00048828125. The compact n=5 cross-condition record retains summary values
only; it is not promoted to a recomputable per-seed confirmation.

No numerical result, split, multiplicity family, or statistical method was
changed by this gate.

`FINAL_STATISTICAL_VERIFICATION = PASS` within retained-result scope.
