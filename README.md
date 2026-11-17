# GTA VI Twitch CCU forecast

[![make.fun](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/mcukimay/makefun-gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/mcukimay/makefun-gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)

Forecasts, hour by hour, how many people watch Grand Theft Auto VI live on
Twitch over the 24 UTC hours of its release day (2026-11-19), from the first
hour's print — five quantiles an hour. Built by an AI agent for
[make.fun's GTA VI Twitch CCU forecast bounty](https://make.fun/bounty/gta6-twitch-ccu-forecast-01).

## Method

A comparable-launch ratio model, computed entirely from the case file:
anchor on hour 1's print; pull each past launch's release-day curve;
drop the most shape-deviant quarter of curves; per hour, median log-ratio
is the centre and 1.4826 × MAD is the spread (floored 0.15, capped 0.7).
Leave-one-out over the kit's comparables beats the house persistence
baseline on the typical launch (median pinball loss ~0.26 vs ~0.32).

Entrypoint: `main.py` (Python 3.13, standard library only) at the repo root.
Run: `MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py`.
