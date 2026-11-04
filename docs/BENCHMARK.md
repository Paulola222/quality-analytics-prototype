# Benchmark on synthetic data

Command: `python examples/run_benchmark.py` (20 random seeds, 24 months of records each).

```
Seeds: 20
Planted recurring problems found: 60 of 60
Planted problems ranked in top 5: 43 of 60
Other groups flagged per run (for human review): 9.6
Planted EM drift location given a rate-rise flag: 20 of 20 runs
Rate-rise flags on other locations: 3 in 20 runs
```

## How to read this
- The planted problems have distinctive wording, so finding all of them is expected. It is a check that the code works, not evidence of performance on real records.
- Fewer than three-quarters of planted problems reach the top 5 of the ranking, because the ranking also rewards groups that are large by chance in the random background. The ranking weights need tuning on real data.
- The rate-rise check also flagged other locations in a few runs (see the last line above), which are false alarms. About ten other recurring groups per run are flagged. The synthetic background uses only a few description templates per category, so it repeats by chance. Real records would behave differently, in either direction.
- No real plant data was used.
