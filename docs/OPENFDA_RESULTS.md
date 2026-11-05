# Results on FDA public recall data (qa-open)

Generated 2026-11-04 by `examples/run_openfda.py`. Source: openFDA drug enforcement reports, file last updated 2026-11-03. SHA-256 of the file used: `3737ce89ca4bba3576937037e2a545fd748c91b67edbd4f08f1b3bdfc7147bf7`.

## What was run

- Records in the file: 18,076. After keeping recalls of injectable drug products that began in 2015 to 2025, and counting each recall event once: **844** events.
- Mapping (keyword rules in `src/qa_open/openfda.py`): area = product form; category = cause, from the reason text; severity = FDA recall class (I = critical, II = major, III = minor); description = FDA's reason for recall.
- Methods: `find_recurrences` with the same defaults used for the synthetic tests (at least 5 linked events, within 365 days, word-overlap threshold 0.4), then `risk.rank` with the default weights. No code in the methods was changed.
- Not run: the CAPA-recurrence flag, environmental-monitoring flags and cost worksheet, because public recall data contain no CAPA, monitoring or cost records.

## Result

- Recurrence clusters found: **15**, holding **249** of 844 events (30 percent).

Top 10 clusters by score (a prompt for human review, not a conclusion):

| Rank | Product form | Cause | Events | Distinct firms | Largest firm share | First | Last | Median gap (days) | Worst class | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | vial | particulate / foreign matter | 52 | 32 | 12% | 2015-03-18 | 2025-10-01 | 40 | I | 49.5 |
| 2 | vial | sterility / microbial | 38 | 32 | 8% | 2021-02-17 | 2025-10-21 | 34 | II | 13.9 |
| 3 | vial | sterility / microbial | 36 | 35 | 6% | 2015-02-18 | 2020-01-15 | 37 | II | 13.8 |
| 4 | other injectable | sterility / microbial | 19 | 17 | 11% | 2021-07-09 | 2025-10-27 | 56 | II | 11.8 |
| 5 | vial | impurity / degradation / stability | 16 | 14 | 12% | 2021-03-04 | 2025-08-27 | 92 | II | 11.3 |
| 6 | prefilled syringe or pen | sterility / microbial | 16 | 12 | 19% | 2022-05-06 | 2025-10-10 | 43 | II | 11.3 |
| 7 | vial | impurity / degradation / stability | 14 | 9 | 36% | 2015-04-24 | 2019-03-15 | 77 | II | 10.9 |
| 8 | bag or infusion | sterility / microbial | 10 | 7 | 30% | 2016-04-18 | 2018-05-31 | 49 | II | 9.9 |
| 9 | vial | potency / assay | 10 | 9 | 20% | 2020-12-10 | 2023-05-30 | 74 | II | 9.9 |
| 10 | other injectable | sterility / microbial | 10 | 9 | 20% | 2017-02-10 | 2020-03-26 | 130 | II | 9.9 |

## Sensitivity to the settings

| Word-overlap threshold | Minimum events | Clusters | Events in clusters |
|---|---|---|---|
| 0.3 | 3 | 30 | 393 |
| 0.3 | 5 | 14 | 338 |
| 0.4 | 3 | 36 | 318 |
| 0.4 | 5 | 15 | 249 |
| 0.5 | 3 | 32 | 230 |
| 0.5 | 5 | 11 | 159 |

## Cause categories in the data

| Cause | Events |
|---|---|
| sterility / microbial | 309 |
| particulate / foreign matter | 142 |
| impurity / degradation / stability | 93 |
| potency / assay | 82 |
| labeling / packaging error | 80 |
| container / closure / device | 62 |
| cGMP / process deficiency | 51 |
| other / unclear | 25 |

## Limits (read these before relying on any number above)

- A recall is the end of a quality problem that reached the market. It is not an internal deviation. This run shows that the recurrence and ranking steps work on real, messy free text. It does not show how they perform on a plant's own records.
- Cause and product form come from keyword rules on one free-text field. A different rule set would give different groups.
- FDA writes many reasons in standard phrases (for example "Lack of Assurance of Sterility" and "Presence of Particulate Matter"). That makes word overlap easy here, and the groups largely reproduce FDA's own headings. Real internal deviation reports are written in many styles and would be harder.
- The method links reports by shared words. It can miss the same cause described in different words and link unrelated reports that share common words. The spot-check file lets a reader judge this.
- Recurrence here means similar recalls of injectable products within a year, across all firms. It says nothing about any one firm.
- The data are as published by FDA on the download date. Recall classification can change after publication.
