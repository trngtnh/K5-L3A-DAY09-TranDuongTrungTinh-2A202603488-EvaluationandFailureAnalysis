"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    from lab9.graders import GRADERS

    problems = []
    for label, report in (("PR", pr), ("baseline", base)):
        manifest = report.get("manifest", {})
        rows = report.get("rows", [])
        seeds = manifest.get("seeds", [])
        if report.get("evaluator_failures"):
            problems.append(f"{label}: evaluator failures")
        if len(rows) != manifest.get("items", 0) * len(seeds):
            problems.append(f"{label}: wrong row count")
        pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
        if len(set(pairs)) != len(pairs):
            problems.append(f"{label}: duplicate item/seed")
        if len(set(seeds)) != len(seeds) or {r.get("seed") for r in rows} != set(seeds):
            problems.append(f"{label}: invalid seed set")
        item_ids = {r.get("item_id") for r in rows}
        if len(item_ids) != manifest.get("items") or set(pairs) != {(i, s) for i in item_ids for s in seeds}:
            problems.append(f"{label}: incomplete item/seed grid")
        for key, value in report.get("metrics", {}).items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                problems.append(f"{label}: non-finite metric {key}")
        for metric in spec.get("metrics", []):
            mid = metric["id"]
            if mid in GRADERS and any(not isinstance(r.get(mid), bool) for r in rows):
                problems.append(f"{label}: missing or invalid graded metric {mid}")
    pr_pairs = {(r.get("item_id"), r.get("seed")) for r in pr.get("rows", [])}
    base_pairs = {(r.get("item_id"), r.get("seed")) for r in base.get("rows", [])}
    if pr_pairs != base_pairs:
        problems.append("item/seed pairs differ from baseline")
    base_tags = {(r.get("item_id"), r.get("seed")): set(r.get("slices") or []) for r in base.get("rows", [])}
    for row in pr.get("rows", []):
        pair = (row.get("item_id"), row.get("seed"))
        if pair in base_tags and set(row.get("slices") or []) != base_tags[pair]:
            problems.append(f"slice tags differ for {pair}")
            break
    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        def ratchet(old_entries, new_entries, key):
            old_map = {key(x): x for x in old_entries}
            new_map = {key(x): x for x in new_entries}
            for ident, previous in old_map.items():
                current = new_map.get(ident)
                if current is None:
                    problems.append(f"ratchet: removed {ident}")
                    continue
                if previous.get("blocking") and not current.get("blocking"):
                    problems.append(f"ratchet: disabled blocking for {ident}")
                old_th = previous.get("threshold", previous)
                new_th = current.get("threshold", current)
                for field, direction in (("min", "lower"), ("max", "higher"), ("max_increase", "higher")):
                    if field in old_th and (field not in new_th or
                        (new_th[field] < old_th[field] if direction == "lower" else new_th[field] > old_th[field])):
                        problems.append(f"ratchet: loosened {field} for {ident}")
                if old_th.get("no_significant_drop") and not new_th.get("no_significant_drop"):
                    problems.append(f"ratchet: removed no_significant_drop for {ident}")
        ratchet(base_spec.get("metrics", []), spec.get("metrics", []), lambda x: x["id"])
        ratchet(base_spec.get("slices", []), spec.get("slices", []), lambda x: (x["name"], x["metric"]))
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        ident = f"slice:{name}/{metric}"
        a, b = per_item(pr, metric, slice_name=name), per_item(base, metric, slice_name=name)
        verdict, note = "ok", ""
        if not a or set(a) != set(b):
            verdict, note = "fail", "missing or unmatched slice items"
            value = None
        else:
            keys = sorted(a)
            value = sum(a[k] for k in keys) / len(keys)
            if "min" in entry and value < entry["min"]:
                verdict = "fail"
            if entry.get("no_significant_drop") and len(keys) < 2 and a[keys[0]] != b[keys[0]]:
                verdict, note = "fail", "insufficient paired items for bootstrap"
            elif entry.get("no_significant_drop"):
                delta, lo, hi = stats.paired_bootstrap(
                    [a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95))
                note = f"delta {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"
        if verdict != "ok" and entry.get("blocking"):
            blocked.append(ident)
        label = "ok" if verdict == "ok" else ("BLOCK" if entry.get("blocking") else "warn")
        lines.append(f"  {ident:<30} {value!s:<8} {note:<35} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
