# Data Tracker

![tests](https://github.com/YOUR-USERNAME/data-tracker/actions/workflows/tests.yml/badge.svg)

A tool that tracks the current weather in 20 cities. Every day, on its own, it downloads the latest values for each city, adds them to a history with one row per city per day, reports what moved, and publishes the result to a website.

- Live site: https://YOUR-USERNAME.github.io/data-tracker/
- Subject: the weather in 10 US cities and 10 world cities.

## Sources

Both sources are the free Open-Meteo forecast API (`https://api.open-meteo.com/v1/forecast`). It needs no login and no API key, so there is no secret in this repository. Each source is one request that returns the current values for all of its cities as JSON.

| Source | What it covers | Format | Items |
|---|---|---|---|
| `weather-us` | Open-Meteo current weather, 10 US cities | JSON (`.json.gz`) | 10 |
| `weather-world` | Open-Meteo current weather, 10 world cities | JSON (`.json.gz`) | 10 |

The request asks only for the five values below for the cities listed in `sources.json`, so nothing extra is kept. The values are the weather at the moment the daily run asks, so they are a daily snapshot (the run starts a little after 06:17 UTC).

## Items

The key is `item_id`, a short lowercase name for the city. It never changes, so the same city lines up day after day.

| Item | item_id | Country | Region | Source |
|---|---|---|---|---|
| New York | `new-york` | United States | North America | `weather-us` |
| Los Angeles | `los-angeles` | United States | North America | `weather-us` |
| Chicago | `chicago` | United States | North America | `weather-us` |
| Houston | `houston` | United States | North America | `weather-us` |
| Phoenix | `phoenix` | United States | North America | `weather-us` |
| Denver | `denver` | United States | North America | `weather-us` |
| Seattle | `seattle` | United States | North America | `weather-us` |
| Miami | `miami` | United States | North America | `weather-us` |
| Atlanta | `atlanta` | United States | North America | `weather-us` |
| Boston | `boston` | United States | North America | `weather-us` |
| London | `london` | United Kingdom | Europe | `weather-world` |
| Paris | `paris` | France | Europe | `weather-world` |
| Tokyo | `tokyo` | Japan | Asia | `weather-world` |
| Sydney | `sydney` | Australia | Oceania | `weather-world` |
| Mumbai | `mumbai` | India | Asia | `weather-world` |
| Sao Paulo | `sao-paulo` | Brazil | South America | `weather-world` |
| Cairo | `cairo` | Egypt | Africa | `weather-world` |
| Singapore | `singapore` | Singapore | Asia | `weather-world` |
| Mexico City | `mexico-city` | Mexico | North America | `weather-world` |
| Toronto | `toronto` | Canada | North America | `weather-world` |

## Columns of data/history.csv

One row per item per day, sorted by date and then by item_id. A value the source did not report is left empty.

| Column | Meaning | Unit |
|---|---|---|
| `date` | UTC date of the run | YYYY-MM-DD |
| `item_id` | Key that identifies the city from day to day | text |
| `item` | The city's name | text |
| `source` | Which source supplied the row | text |
| `country` | Country of the city | text |
| `region` | Continent of the city | text |
| `temp_c` | Air temperature at 2 m | degrees Celsius |
| `feels_like_c` | Apparent ("feels like") temperature | degrees Celsius |
| `humidity_pct` | Relative humidity at 2 m | percent |
| `wind_kmh` | Wind speed at 10 m | kilometres per hour |
| `pressure_hpa` | Surface air pressure | hectopascals |

## Move rule

A **move** is how much an item's temperature changed since the previous run, measured as `temp_c` now minus `temp_c` before, in degrees Celsius, rounded to 2 decimals.

- Each source is compared with its own previous run: the latest earlier day on which that source has rows. A source with no earlier day is its first load, so nothing is compared. A source that failed today is not compared, and its items are not reported as disappeared.
- An item in today's rows but not in the previous run **appeared**. An item in the previous run but not in today's rows **disappeared**.
- Moves are ranked by absolute size, then by `item_id`. The daily issue lists the **5 biggest moves** with the old and new values, plus every item that appeared or disappeared.
- The rule is `compare()` in `watcher/moves.py`. The Today and Trends pages use the same rule (`compare()` in `app.js`).

## Files

| File | What it does |
|---|---|
| `sources.json` | The two sources, their URL and the cities (key, name, country, region, coordinates) each one tracks |
| `watcher/convert.py` | Converts an Open-Meteo response to the common columns; defines the history columns |
| `watcher/history.py` | Builds `data/history.csv` from the raw files alone |
| `watcher/moves.py` | The move rule: moves, appeared and disappeared items |
| `watcher/status.py` | Builds the contents of `data/status.json` |
| `watcher/issue.py` | Builds the daily issue text and opens, updates and closes the GitHub Issues |
| `watcher/pipeline.py` | The daily run: download, save raw files, build history, write status |
| `tests/` | The pytest suite: conversion, move rule, history logic, second run on the same day |
| `pytest.ini`, `requirements.txt` | Test settings and Python dependencies |
| `.github/workflows/daily.yml` | Runs the pipeline once a day, commits the data, opens the issue |
| `.github/workflows/tests.yml` | Runs the tests on every push |
| `data/raw/<date>/<source>.json.gz` | What each source returned that day, compressed, in the format it came in. `_results.json` records the result of every source for that day |
| `data/history.csv` | The history, one row per item per day |
| `data/status.json` | Describes the latest run |
| `index.html` | Today page: last run, source status, counts, latest values with changes, biggest moves |
| `browse.html` | Browse page: latest values with filters, search, sort and a starred shortlist |
| `trends.html` | Trends page: line chart of each value, and five findings computed from the history |
| `style.css`, `app.js`, `charts.js`, `today.js`, `browse.js`, `trends.js` | Shared look, data loading, SVG charts and page logic |
| `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png` | Make the site installable and usable offline |

## Build the history file from the raw files

```
python -m watcher.history
```

This reads every `data/raw/<date>/<source>.json.gz` in date order and rewrites `data/history.csv` from scratch. Running it again gives the same file.

## Other commands

```
pip install -r requirements.txt
python -m pytest                      # run the tests
python -m watcher.pipeline --check    # test every source, write nothing
python -m watcher.pipeline            # a full run for today (UTC)
```

## How a day is recorded

1. Each source is downloaded and saved, compressed, as `data/raw/<date>/<source>.json.gz`. A source that fails writes no raw file that day. Its result (ok, count, error) is still recorded in `_results.json` and shown on the Today page.
2. The history is rebuilt from all raw files. A day with no raw file for a source has no rows from that source.
3. `data/status.json` is written, the data is committed, and an issue titled with the date lists the biggest moves and the items that appeared or disappeared. The previous day's issue is closed.

A second run on the same day replaces that day's raw files, rebuilds the history, and updates that day's issue, so each day counts once.
