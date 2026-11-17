"""GTA VI Twitch CCU forecast: comparable-launch ratio quantiles.

Forecasts hours 2..24 of GTA VI's release day, five quantiles an hour,
anchored to the hour-1 print. From the case file: pull each comparable's
release-day curve (24 hourly counts from its day_start), dropping
incomplete curves, the case's own game, and the GTA VI pre-release
history; drop the most shape-deviant quarter of curves (mean absolute
log-ratio distance from the median curve), keeping at least five; per
hour, median log-ratio is the centre and 1.4826 * MAD the spread
(floored 0.15, capped 0.7); quantile tau is anchor * exp(centre +
z_tau * spread). Under three comparables, fall back to persistence.
Deterministic: no randomness, clock, or network.
"""

import json
import math
import os
import sys
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z_SCORES = [-1.645, -0.674, 0.0, 0.674, 1.645]
SPREAD_FLOOR = 0.15
SPREAD_CAP = 0.7
DROP_FRACTION = 0.25
MIN_POOL = 5
MIN_COMPARABLES = 3
BASELINE_SIGMA = 0.15


def _median(values):
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _round2(value):
    """Round to 2 decimals, half up; whole numbers come back as int."""
    scaled = value * 100.0
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    rounded = whole / 100.0
    return int(rounded) if float(rounded).is_integer() else rounded


def _release_curve(comparable):
    """The comparable's 24 hourly viewer counts starting at its day_start."""
    hourly = comparable.get("hourly") or []
    start = comparable.get("day_start")
    for i, point in enumerate(hourly):
        if point.get("from") == start:
            window = hourly[i:i + 24]
            if len(window) < 24:
                return None
            viewers = [p.get("viewers") for p in window]
            if any(v is None or v <= 0 for v in viewers):
                return None
            return viewers
    return None


def _usable_curves(case):
    """Release-day curves of the comparables, excluding the case's own game
    and the GTA VI pre-release history (no release day yet)."""
    game_name = (case.get("game") or {}).get("name", "")
    curves = []
    for comp in case.get("comparables") or []:
        name = comp.get("name", "")
        if name == game_name:
            continue
        if "before release" in name:
            continue
        curve = _release_curve(comp)
        if curve is not None:
            curves.append((name, curve))
    curves.sort(key=lambda item: item[0])
    return [curve for _, curve in curves]


def _shape_filtered(curves):
    """Drop the most shape-deviant quarter of curves (mean absolute
    log-ratio distance from the median curve), keeping at least MIN_POOL."""
    if len(curves) <= MIN_POOL:
        return curves
    median_log = []
    for h in range(24):
        logs = [math.log(c[h] / c[0]) for c in curves]
        median_log.append(_median(logs))
    scored = []
    for curve in curves:
        dev = sum(
            abs(math.log(curve[h] / curve[0]) - median_log[h])
            for h in range(1, 24)
        ) / 23.0
        scored.append((dev, curve))
    scored.sort(key=lambda item: item[0])
    keep = max(MIN_POOL, len(curves) - int(len(curves) * DROP_FRACTION))
    return [curve for _, curve in scored[:keep]]


def _hour_quantiles(p1, hour, curves):
    """Five quantiles for one hour from the pool's log-ratios."""
    logs = [math.log(c[hour - 1] / c[0]) for c in curves]
    centre = _median(logs)
    mad = _median([abs(x - centre) for x in logs])
    spread = min(max(1.4826 * mad, SPREAD_FLOOR), SPREAD_CAP)
    out = []
    for z in Z_SCORES:
        value = p1 * math.exp(centre + z * spread)
        out.append(_round2(max(value, 0.01)))
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def _baseline_quantiles(p1, hour):
    """Persistence fallback: every hour at hour 1, random-walk spread."""
    out = []
    for z in Z_SCORES:
        value = p1 * math.exp(z * BASELINE_SIGMA * math.sqrt(hour - 1))
        out.append(_round2(max(value, 0.01)))
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def forecast_case(case):
    if case.get("levels") != LEVELS:
        raise ValueError("levels are not %s" % (LEVELS,))
    first = next(
        (row for row in case.get("known", []) if row.get("hour") == 1), None
    )
    if first is None:
        raise ValueError("case has no hour-1 print")
    p1 = max(1, first["viewers"])
    curves = _shape_filtered(_usable_curves(case))
    use_model = len(curves) >= MIN_COMPARABLES
    hours = []
    for row in case.get("forecast", []):
        h = row["hour"]
        if use_model:
            quantiles = _hour_quantiles(p1, h, curves)
        else:
            quantiles = _baseline_quantiles(p1, h)
        hours.append({"hour": h, "q": quantiles})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast_case(case)
        text = json.dumps(result, separators=(",", ":")) + "\n"
        (OUTPUT_DIR / (path.stem + ".out")).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
