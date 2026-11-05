"""Adapter for FDA's public drug enforcement (recall) reports.

The openFDA drug enforcement file lists drug recalls. Each record has a recall number, the date
the recall started, FDA's recall class, and a free-text reason. This module turns those records
into the table that ``deviations.find_recurrences`` expects, so the same recurrence method can be
tried on real, public, messy text.

What this is and is not
-----------------------
* A recall is not a plant deviation. It is what is left after a quality problem reached the market.
  Public recall data hold no CAPA records, no environmental-monitoring data and no cost data, so only
  the recurrence and ranking steps can be tried on them.
* The mapping rules are plain keyword rules that anyone can read and change (``CAUSE_RULES`` and
  ``FORM_RULES``). They are a judgment, not a standard. They are applied to the reason text only.
* Results are reported by product form and cause. Firm names are never used.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd

# First rule that matches wins, so order matters.
CAUSE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("sterility / microbial", ("steril", "microb", "bacteri", "endotoxin", "mold", "fung", "yeast", "bacillus",
                               "burkholderia", "contaminat")),
    ("particulate / foreign matter", ("particulate", "particle", "foreign", "glass", "precipitate", "crystal",
                                      "fiber", "fibre", "delaminat", "visible")),
    ("potency / assay", ("subpotent", "sub-potent", "superpotent", "super-potent", "potency", "assay",
                         "low out of specification", "high out of specification")),
    ("impurity / degradation / stability", ("impurit", "degradat", "nitrosamine", "ndma", "stability",
                                            "out of specification", "oos", "ph ")),
    ("container / closure / device", ("container", "closure", "leak", "crimp", "seal", "stopper", "cap ",
                                      "syringe", "needle", "vial", "cartridge", "pen ")),
    ("labeling / packaging error", ("label", "carton", "packag", "mix-up", "mixup", "mix up", "incorrect",
                                    "wrong", "barcode", "insert")),
    ("cGMP / process deficiency", ("cgmp", "gmp", "manufacturing practice", "data integrity", "deviation",
                                   "lack of assurance", "quality system", "process")),
]

FORM_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("prefilled syringe or pen", ("syringe", "pen injector", "autoinjector", "auto-injector", "cartridge")),
    ("bag or infusion", ("infusion", "iv bag", "intravenous bag", "premix", "bag")),
    ("ampule", ("ampul", "ampoule")),
    ("vial", ("vial",)),
]
INJECTABLE_WORDS = ("injection", "injectable", "infusion", "intravenous", "for injection", "parenteral",
                    "prefilled syringe", "vial", "ampul", "ampoule")
CLASS_TO_SEVERITY = {"class i": "critical", "class ii": "major", "class iii": "minor"}


def _first_match(text: str, rules) -> str | None:
    t = text.lower()
    for label, words in rules:
        if any(w in t for w in words):
            return label
    return None


def _read_json(path: str | Path):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".json")]
            if not names:
                raise ValueError("no .json file inside the zip")
            return json.loads(z.read(names[0]))
    return json.loads(path.read_text(encoding="utf-8"))


def load_meta(path: str | Path) -> dict:
    """Return the file's own "meta" block (it records the last-updated date), or an empty dict."""
    data = _read_json(path)
    return data.get("meta", {}) if isinstance(data, dict) else {}


def load_enforcement(path: str | Path) -> pd.DataFrame:
    """Read the openFDA drug enforcement download (.json or .zip with one .json)."""
    data = _read_json(path)
    rows = data["results"] if isinstance(data, dict) else data
    return pd.DataFrame(rows)


def to_deviation_table(raw: pd.DataFrame, first_year: int = 2015, last_year: int = 2025,
                       injectables_only: bool = True) -> pd.DataFrame:
    """Map recall records to the columns used by ``find_recurrences``.

    deviation_id = recall number of the first product line in the event; date = recall initiation date; area = product form; category = cause
    (keyword rules); severity = FDA recall class; description = reason for recall.
    """
    need = {"recall_number", "reason_for_recall", "product_description", "classification"}
    missing = need - set(raw.columns)
    if missing:
        raise ValueError(f"enforcement file is missing fields: {sorted(missing)}")
    df = raw.copy()
    date_col = "recall_initiation_date" if "recall_initiation_date" in df else "report_date"
    df["date"] = pd.to_datetime(df[date_col].astype(str), format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[(df["date"].dt.year >= first_year) & (df["date"].dt.year <= last_year)]
    if "product_type" in df:
        df = df[df["product_type"].astype(str).str.lower().str.contains("drug")]
    prod = df["product_description"].fillna("").astype(str)
    if injectables_only:
        mask = prod.str.lower().apply(lambda t: any(w in t for w in INJECTABLE_WORDS))
        df, prod = df[mask], prod[mask]
    reason = df["reason_for_recall"].fillna("").astype(str)
    out = pd.DataFrame({
        "deviation_id": df["recall_number"].astype(str),
        "date": df["date"],
        "area": [_first_match(p, FORM_RULES) or "other injectable" for p in prod],
        "category": [_first_match(r, CAUSE_RULES) or "other / unclear" for r in reason],
        "severity": [CLASS_TO_SEVERITY.get(str(c).strip().lower(), "minor") for c in df["classification"]],
        "description": [re.sub(r"\s+", " ", r).strip() for r in reason],
    })
    # One recall event can cover many product lines, each with its own recall number and the same
    # reason text. Count each event once, or one event would look like a recurrence of itself.
    if "event_id" in df:
        out["event_id"] = df["event_id"].astype(str).values
        out = out.drop_duplicates(subset="event_id").drop(columns="event_id")
    else:
        out = out.drop_duplicates(subset=["date", "area", "description"])
    return out.sort_values("date").reset_index(drop=True)
