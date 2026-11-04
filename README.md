# qa-open: open quality-record analytics (prototype v0.1.0)

A small, readable Python package for looking at pharmaceutical quality records in four ways:

1. **Recurring deviations.** Groups deviation reports that keep coming back in the same area and category, and notes where a deviation recurred after a CAPA (corrective and preventive action) for an earlier one was closed.
2. **Environmental-monitoring trend flags.** Alert and action counts, a run flag and a rate-rise flag for cleanroom results.
3. **A transparent risk ranking.** A weighted score whose weights are printed in the code and can be changed.
4. **A cost-of-quality worksheet.** It uses only numbers the user types in. It does not guess costs from public data.

It also contains a **synthetic plant generator**, so the methods can be tested without any confidential records.

## Status and honest limits

- This is the **first release (v0.1.0)**. It has been tested on synthetic data only, because no confidential plant records may be shared.
- It runs on **synthetic data**. The synthetic plant has three planted recurring problems and one planted drift, so the tests know the right answer. Real records are messier, and the results here do not show how it would perform on them.
- The output is **a prompt for human review**. It does not decide whether a deviation is a real problem, and it is not a validated system for regulated decisions. Anyone using it in a GMP setting would need to validate it for that use.
- The loss probabilities and delay days in the cost worksheet are **placeholder defaults**, not facts. Replace them with your own figures.
- No confidential employer data was used or is included.

## Install and run

```
pip install -e .
qa-open demo            # prints a report on synthetic data
pytest                  # 13 tests
python examples/run_benchmark.py
```

Sample output is in `docs/SAMPLE_REPORT.md`. The benchmark and its limits are in `docs/BENCHMARK.md`. The methods are in `docs/METHODS.md`.

## Using your own records

`find_recurrences` expects a table with columns `deviation_id, date, area, category, severity, description`, and optionally a CAPA table with `deviation_id, closed`. `trend_flags` expects environmental-monitoring results with a location, date and count. See `src/qa_open/synthetic.py` for the exact layout.

## Development note

This code was written with the help of an AI assistant (Claude). The author defined the problem and the methods, reviewed and tested the code, and is responsible for it.

## License and citation

MIT License (see `LICENSE`). To cite, see `CITATION.cff`.
