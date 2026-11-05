# qa-open: open quality-record analytics (prototype v0.2.0)

A small, readable Python package for looking at pharmaceutical quality records in four ways:

1. **Recurring deviations.** Groups deviation reports that keep coming back in the same area and category, and notes where a deviation recurred after a CAPA (corrective and preventive action) for an earlier one was closed.
2. **Environmental-monitoring trend flags.** Alert and action counts, a run flag and a rate-rise flag for cleanroom results.
3. **A transparent risk ranking.** A weighted score whose weights are printed in the code and can be changed.
4. **A cost-of-quality worksheet.** It uses only numbers the user types in. It does not guess costs from public data.

It also contains a **synthetic plant generator**, so the methods can be tested without any confidential records.

## Status and honest limits

- This is **v0.2.0**. The methods are tested on synthetic data, and the recurrence and ranking steps have also been run on FDA's public drug recall reports (see below). They have **not** been tested on a plant's own records, because no confidential records may be shared.
- It runs on **synthetic data**. The synthetic plant has three planted recurring problems and one planted drift, so the tests know the right answer. Real records are messier, and the results here do not show how it would perform on them.
- The output is **a prompt for human review**. It does not decide whether a deviation is a real problem, and it is not a validated system for regulated decisions. Anyone using it in a GMP setting would need to validate it for that use.
- The loss probabilities and delay days in the cost worksheet are **placeholder defaults**, not facts. Replace them with your own figures.
- No confidential employer data was used or is included.

## Install and run

```
pip install -e .
qa-open demo            # prints a report on synthetic data
pytest                  # 16 tests
python examples/run_benchmark.py
```

Sample output is in `docs/SAMPLE_REPORT.md`. The benchmark and its limits are in `docs/BENCHMARK.md`. The methods are in `docs/METHODS.md`.

## Run on FDA public recall data (new in v0.2.0)

`src/qa_open/openfda.py` turns FDA's public drug enforcement (recall) reports into the table the recurrence method reads. `examples/run_openfda.py` runs the methods and writes `docs/OPENFDA_RESULTS.md`, with a spot-check file of the actual reason text (`docs/openfda_spotcheck.csv`). To repeat it, download `drug-enforcement-0001-of-0001.json.zip` from https://open.fda.gov/data/downloads/ and run `python examples/run_openfda.py <file> 2015 2025`. The results page records the file's date and checksum.

What this shows and does not show: public recalls hold no CAPA, monitoring or cost records, so only the recurrence and ranking steps could be tried. A recall is the end of a quality problem that reached the market, not an internal deviation. FDA words many reasons in standard phrases, which makes word overlap easier than it would be on a plant's own reports. No firm is named in any output.

## Using your own records

`find_recurrences` expects a table with columns `deviation_id, date, area, category, severity, description`, and optionally a CAPA table with `deviation_id, closed`. `trend_flags` expects environmental-monitoring results with a location, date and count. See `src/qa_open/synthetic.py` for the exact layout.

## License and citation

MIT License (see `LICENSE`). To cite, see `CITATION.cff`.
