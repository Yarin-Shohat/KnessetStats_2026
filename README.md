# Knesset 26 vs 25: election shifts and TV-poll accuracy

A Streamlit dashboard that runs six statistical tests on the 25th and 26th Knesset elections and on
six TV-channel polls.

Created by [Yarin Shohat](https://www.linkedin.com/in/yarinsh/).

| Tab | Test |
|---|---|
| 1 | Paired t-test / Wilcoxon on per-locality change in a party's share |
| 2 | Chi-square test of homogeneity on national vote counts (25th vs 26th) |
| 3 | Two-proportion z-test for one party (with Cohen's h) |
| 4 | Chi-square goodness of fit: each poll vs the true result |
| 5 | One-sample z-test: did a channel miss one party? |
| 6 | MAE / RMSE per channel and paired comparisons between channels |

The UI is available in English and Hebrew (selector at the top of the sidebar; Hebrew switches the
page to right-to-left). Translations live in `knesset_stats/i18n.py`, keyed by the English text.

## Data sources and credits
All data belongs to its original publishers and is used here for non-commercial statistical analysis.
The `resources/` folder (original poll PDFs and results text) is git-ignored because it is third-party
material. Only the figures extracted from it are committed, as `data/polls.json` and
`data/final_results.json`; the app reads the original files when present and these snapshots otherwise
(so a fresh clone or a public deployment works without `resources/`). After changing a parser or a source
file, regenerate the snapshots with `uv run python scripts/export_snapshots.py`.

- **Election results per locality:** [Kaplan Open Source - Elections](https://elections.kaplanopensource.co.il/locality/)
  (1,232 locality pages, scraped politely with delay and cached in `.cache/` after the first run, which takes
  about 2 minutes). The underlying figures are the official results of the Central Elections Committee. The
  `/25/` and `/26/` map pages are JS-rendered and are not used.
- **Pre-election polls (`resources/ערוץ *.pdf`):** polls published by Israeli TV channels 11 (Kan), 12, 13,
  14, 16 and 24, and by the polling firms that conducted them. They are parsed with `pdfplumber` (sample size
  N is read from each PDF). Only the extracted figures are analysed; the documents are not redistributed.
- **Final results (`resources/תוצאות האמת...txt`):** final seat split and vote totals for the 26th Knesset.

Methodology notes are shown inside the app (Data quality tab). The six PDFs are pre-election polls,
not exit polls. Polls are compared with the true result after dropping undecided voters and lists
that failed the threshold.

## Run
```
uv sync
uv run streamlit run streamlit_app.py
uv run pytest
```
