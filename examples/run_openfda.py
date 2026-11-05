"""Run the recurrence and ranking methods on FDA's public drug enforcement (recall) reports.

Usage:
    python examples/run_openfda.py PATH_TO_drug-enforcement-0001-of-0001.json.zip [first_year] [last_year]

Get the file from https://open.fda.gov/data/downloads/ (Drug > Enforcement). Writes
docs/OPENFDA_RESULTS.md and docs/openfda_clusters.csv. Only product form and cause are reported;
firm names are never read into the output.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import sys
from pathlib import Path

import pandas as pd

from qa_open import deviations, openfda, risk

path = Path(sys.argv[1])
first = int(sys.argv[2]) if len(sys.argv) > 2 else 2015
last = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
root = Path(__file__).resolve().parents[1]

# file provenance (the openFDA download carries a "meta" block with the last-updated date)
meta = openfda.load_meta(path)
raw = openfda.load_enforcement(path)
table = openfda.to_deviation_table(raw, first, last)
n_total = len(raw)

clusters = deviations.find_recurrences(table)  # defaults: 5 events, 365 days, similarity 0.4
sha = hashlib.sha256(path.read_bytes()).hexdigest()
firm_of = dict(zip(raw["recall_number"].astype(str), raw["recalling_firm"].astype(str)))
firm_counts, top_share = [], []
for ids in clusters["deviation_ids"]:
    firms = pd.Series([firm_of.get(i, "?") for i in ids])
    firm_counts.append(int(firms.nunique()))
    top_share.append(float(firms.value_counts(normalize=True).iloc[0]))
clusters["distinct_firms"] = firm_counts
clusters["largest_firm_share"] = top_share
ranked = risk.rank(clusters)
in_clusters = int(clusters["events"].sum()) if len(clusters) else 0

lines = []
w = lines.append
w("# Results on FDA public recall data (qa-open)\n")
w(f"Generated {dt.date.today().isoformat()} by `examples/run_openfda.py`. "
  f"Source: openFDA drug enforcement reports, file last updated {meta.get('last_updated', 'date not recorded')}. "
  f"SHA-256 of the file used: `{sha}`.\n")
w("## What was run\n")
w(f"- Records in the file: {n_total:,}. After keeping recalls of injectable drug products that began in {first} to {last}, "
  f"and counting each recall event once: **{len(table):,}** events.")
w("- Mapping (keyword rules in `src/qa_open/openfda.py`): area = product form; category = cause, from the reason text; "
  "severity = FDA recall class (I = critical, II = major, III = minor); description = FDA's reason for recall.")
w("- Methods: `find_recurrences` with the same defaults used for the synthetic tests (at least 5 linked events, within 365 days, "
  "word-overlap threshold 0.4), then `risk.rank` with the default weights. No code in the methods was changed.")
w("- Not run: the CAPA-recurrence flag, environmental-monitoring flags and cost worksheet, because public recall data "
  "contain no CAPA, monitoring or cost records.\n")
w("## Result\n")
w(f"- Recurrence clusters found: **{len(clusters)}**, holding **{in_clusters:,}** of {len(table):,} events "
  f"({100*in_clusters/max(len(table),1):.0f} percent).")
if len(ranked):
    w("\nTop 10 clusters by score (a prompt for human review, not a conclusion):\n")
    w("| Rank | Product form | Cause | Events | Distinct firms | Largest firm share | First | Last | Median gap (days) | Worst class | Score |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    sev_name = {"critical": "I", "major": "II", "minor": "III"}
    for i, r in enumerate(ranked.head(10).itertuples(), 1):
        w(f"| {i} | {r.area} | {r.category} | {r.events} | {r.distinct_firms} | {100*r.largest_firm_share:.0f}% | {r.first} | {r.last} | {r.median_gap_days:.0f} | "
          f"{sev_name[r.worst_severity]} | {r.score:.1f} |")
w("\n## Sensitivity to the settings\n")
w("| Word-overlap threshold | Minimum events | Clusters | Events in clusters |")
w("|---|---|---|---|")
for sim in (0.3, 0.4, 0.5):
    for me in (3, 5):
        c = deviations.find_recurrences(table, min_events=me, min_similarity=sim)
        w(f"| {sim} | {me} | {len(c)} | {int(c['events'].sum()) if len(c) else 0} |")
w("\n## Cause categories in the data\n")
w("| Cause | Events |")
w("|---|---|")
for k, v in table["category"].value_counts().items():
    w(f"| {k} | {v} |")
w("\n## Limits (read these before relying on any number above)\n")
w("- A recall is the end of a quality problem that reached the market. It is not an internal deviation. This run shows that the "
  "recurrence and ranking steps work on real, messy free text. It does not show how they perform on a plant's own records.")
w("- Cause and product form come from keyword rules on one free-text field. A different rule set would give different groups.")
w("- FDA writes many reasons in standard phrases (for example \"Lack of Assurance of Sterility\" and \"Presence of Particulate Matter\"). That makes word overlap easy here, and the groups largely reproduce FDA's own headings. Real internal deviation reports are written in many styles and would be harder.")
w("- The method links reports by shared words. It can miss the same cause described in different words and link unrelated "
  "reports that share common words. The spot-check file lets a reader judge this.")
w("- Recurrence here means similar recalls of injectable products within a year, across all firms. It says nothing about any one firm.")
w("- The data are as published by FDA on the download date. Recall classification can change after publication.\n")
(root / "docs").mkdir(exist_ok=True)
(root / "docs" / "OPENFDA_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")

# spot-check sample: reason text of members of the 8 largest clusters
sample = []
for r in clusters.head(8).itertuples():
    ids = r.deviation_ids[:6]
    for did in ids:
        row = table[table.deviation_id == did].iloc[0]
        sample.append({"cluster": f"{r.area} | {r.category}", "recall_number": did, "date": row.date.date(),
                       "class": row.severity, "reason": row.description[:300]})
pd.DataFrame(sample).to_csv(root / "docs" / "openfda_spotcheck.csv", index=False)
clusters.drop(columns=["deviation_ids"]).to_csv(root / "docs" / "openfda_clusters.csv", index=False)
print(f"events {len(table)}, clusters {len(clusters)}, in clusters {in_clusters}")
