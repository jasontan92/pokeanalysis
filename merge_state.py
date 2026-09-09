#!/usr/bin/env python3
"""Merge two versions of a scanner state file (seen_listings / wsj_seen_listings).

Used by the GitHub Actions "Save state" steps. A run's state file and the one
on origin/main can both hold alerts the other has never seen: the runner's copy
has this pass's alerts, the remote's copy has whatever landed while this pass
was executing. Picking a side drops alerts from the loser and they re-fire as
duplicates on the next run, so we union the two instead.

    python merge_state.py <mine.json> <theirs.json> -o <out.json>

Union rules, matching how each scanner reads the values back:
  - id -> ISO timestamp maps: keep the LATER stamp (that's mark_seen's own
    semantics), then drop anything past the 30-day cleanup horizon so the
    union can't resurrect entries a cleanup already pruned.
  - category_first_seen: keep the EARLIER stamp. This drives the settling
    window; taking the later one would restart settling for that category.
  - category_settling_alerts: counters, keep the larger.
  - scalars (last_check, last_heartbeat): keep mine, the running job's value.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

CLEANUP_DAYS = 30

# Maps whose values are not "last seen at" stamps and must not be pruned.
EARLIEST_WINS = {'category_first_seen'}
COUNTERS = {'category_settling_alerts'}


def _merge_map(key: str, mine: dict, theirs: dict, cutoff: str) -> dict:
    merged = dict(theirs)
    for k, v in mine.items():
        if k not in merged:
            merged[k] = v
            continue
        other = merged[k]
        if key in COUNTERS:
            try:
                merged[k] = max(v, other)
            except TypeError:
                merged[k] = v
        elif key in EARLIEST_WINS:
            merged[k] = min(str(v), str(other))
        else:
            merged[k] = max(str(v), str(other))

    if key in EARLIEST_WINS or key in COUNTERS:
        return merged
    # Timestamp map: re-apply the scanner's own 30-day cleanup.
    return {k: v for k, v in merged.items() if not isinstance(v, str) or v > cutoff}


def merge(mine: dict, theirs: dict) -> dict:
    cutoff = (datetime.now() - timedelta(days=CLEANUP_DAYS)).isoformat()
    merged = dict(theirs)
    for key, value in mine.items():
        other = merged.get(key)
        if isinstance(value, dict) and isinstance(other, dict):
            merged[key] = _merge_map(key, value, other, cutoff)
        else:
            # Scalars and type mismatches: the running job's value wins.
            merged[key] = value
    return merged


def _load(path: str) -> dict:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"merge_state: ignoring unreadable {path}: {e}", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mine', help="state file written by this run")
    ap.add_argument('theirs', help="state file currently on origin/main")
    ap.add_argument('-o', '--out', required=True, help="merged output path")
    args = ap.parse_args()

    mine, theirs = _load(args.mine), _load(args.theirs)
    if not mine and not theirs:
        print("merge_state: both inputs empty/missing, nothing to write", file=sys.stderr)
        return 1

    merged = merge(mine, theirs)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    tracked = sum(len(v) for v in merged.values() if isinstance(v, dict))
    only_theirs = sum(
        len(set(v) - set(mine.get(k, {})))
        for k, v in theirs.items()
        if isinstance(v, dict) and isinstance(mine.get(k), dict)
    )
    print(f"merge_state: {tracked} ids after merge ({only_theirs} recovered from origin/main)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
