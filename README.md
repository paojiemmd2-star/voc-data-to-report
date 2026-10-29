# VOC Data to Report

**An evidence-first Voice of Customer research skill for e-commerce products.**

[中文说明](README.zh-CN.md) · [Skill instructions](SKILL.md) · [Data contract](references/data-contract.md) · [MIT license](LICENSE)

Turn customer feedback into human-calibrated tags, auditable sentiment statistics, and visual research reports. Link each annotation to a verbatim quote and source ID, and link report findings to their complete evidence sets.

## What this repository provides

- A reusable agent workflow for Amazon, Reddit, and X research, with product-specific scope, sampling limits, and stopping conditions.
- Data-quality checks for mixed-product reviews, seller replies, duplicates, incentivized reviews, truncated text, and missing metadata.
- A three-level taxonomy with four top-level categories: **people and scenarios, functional value, assurance value, and experiential value**. The provided workflow uses Chinese tag names and enum values; source comments remain in their original language.
- A human calibration gate before formal annotation and statistics. Explicitly authorized exploratory work remains labeled as an uncalibrated analyst draft.
- Python statistics for top-20 third-level themes by sentiment, brand × second-level theme × sentiment, and low-star defect mentions.
- A complete `source_id` evidence map for every statistics cell.
- Guidance for a seven-part visual report and evidence-based listing strategy.

**This is an agent skill, not a standalone scraper or one-command report application.** Platform collection requires a compatible tool or separately installed collection skill, such as `bggg-data-amazon`, `bggg-data-reddit`, or `bggg-data-x`. These tools are not bundled. Visual/PDF/Word reports require the host agent's relevant authoring and rendering tools; this repository does not bundle an automatic report renderer.

## Install

### With a compatible skill installer

Ask your agent:

> Install the `voc-data-to-report` skill from https://github.com/paojiemmd2-star/voc-data-to-report. The skill is at the repository root.

### Manual installation

Clone the repository and copy its contents into a folder named `voc-data-to-report` inside your agent's user-skill directory. The folder must contain `SKILL.md` directly. Use the skill directory supported by your host; do not create multiple active copies under different discovery paths.

For environments configured to load `~/.codex/skills`:

```bash
git clone https://github.com/paojiemmd2-star/voc-data-to-report.git
mkdir -p "$HOME/.codex/skills"
cp -R voc-data-to-report "$HOME/.codex/skills/voc-data-to-report"
```

If that destination already exists, inspect and back up your existing version before updating it. Refresh the host's skill list or start a new conversation. Installation and discovery behavior depends on the host.

## Start a research project

Invoke `$voc-data-to-report`, or select the skill in your host's skill picker, and provide:

> Research **[product]** for **[market]** using **[ASINs/URLs]** and **[keywords]**. Use **[rendered pages only / the authorized platform skill method]**, with **[sample limits and time window]**. Produce a taxonomy JSON and wait for calibration before annotation. Then generate evidence-linked statistics and a visual report. Include listing strategy only if requested.

The skill can also continue from an existing corpus, taxonomy, or statistics. It does not require restarting the entire workflow.

## Python helpers

Python **3.9+** is sufficient for the bundled helpers; they use the standard library and make no network requests.

Create a new workspace outside this repository:

```bash
python3 scripts/init_voc_project.py \
  --root ../research-example \
  --product "Example product" \
  --market "US" \
  --method rendered_only \
  --keywords "example product" "example accessory" \
  --parent-cap 30 \
  --sample-cap 200
```

These are example limits, not required research sizes. The initializer refuses to overwrite an existing project and creates no sample reviews or fabricated results. Collection has not started merely because configuration files exist.

After annotation has actually been calibrated, run:

```bash
python3 scripts/voc_statistics.py \
  --input ../research-example/data/coded/coded_reviews.jsonl \
  --out ../research-example/output/statistics \
  --low-star-max 3
```

See the [input contract](references/data-contract.md) and [statistics rules](references/analysis-and-report.md). Each record must contain its original text and a `labels` array. Each label requires a verbatim quote, evidence object, theme-level sentiment, assertion type, and explicit defect flag. The script rejects uncalibrated inputs; changing a status string does not substitute for human review.

### Generated statistics

| File | Contents |
|---|---|
| `top20_level3_sentiment.csv` | Top-20 third-level theme paths, sentiment counts, sample denominator, and mention rates |
| `brand_level2_sentiment.csv` | Brand/object × second-level theme × sentiment, with brand and overall denominators |
| `low_star_defects.csv` | Actual low-star defects, grouped by evidence object, with supporting source IDs |
| `label_evidence.csv` | Every annotation with its quote, full original text, source ID, and URL |
| `cell_source_map.json` | Complete source-ID membership for each statistics cell |
| `statistics_metadata.json` | Input hash, exclusions, denominators, and counting rules |
| `statistics.json` | Combined machine-readable tables and metadata |

Unknown brands stay unknown. A device brand mentioned in an accessory review must not be assumed to be the accessory brand. The helper currently supports one brand/object assignment per record; multi-brand comparisons require a label-level brand extension or exclusion from the brand comparison.

Low-star defaults to Amazon ratings of 1–3. Reddit/X engagement is not converted into ratings. When no eligible low-star records exist, the defect output contains headers and metadata with `n=0`, not a claim that no defects exist.

## Report structure

1. One-page overview
2. Data and methodology
3. Positive themes and pain-point rankings
4. Anomaly signal cards
5. Needs-based user profiles
6. Traceable evidence chain
7. Visual charts

Recommendations are separated from observed results. Sampling frequency is not market prevalence, a complaint is not proof of a root cause, and customer praise is not a product-performance test. Listing claims require both demand evidence and verified facts about the specific product/SKU.

## Validation

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

Tests use explicitly synthetic fixtures. They check deduplication, conflicting sentiments, source-linked counts, seller exclusion, low-star boundaries, evidence quotes, and brand/object separation. They do not validate annotation semantics or guarantee access to a platform.

## Privacy and collection limits

- Respect user-specified collection methods, access controls, login requirements, CAPTCHAs, and rate limits.
- Do not export browser credentials, cookies, tokens, profiles, or unrelated private UI data.
- Preserve failed attempts and report partial coverage. Requested collection modes do not guarantee completeness.
- Do not publish customer datasets or private project exports with this skill. The `.gitignore` excludes common workspace/export folders, but it does not replace a review before publishing.

## Repository layout

```text
SKILL.md
agents/openai.yaml
references/
  data-contract.md
  collection-and-tools.md
  analysis-and-report.md
  listing-method.md
  quality-checks.md
scripts/
  init_voc_project.py
  voc_statistics.py
  test_voc_statistics.py
```

The skill and detailed references are primarily in Chinese. This README is in English; the Chinese guide is linked above.

## License

MIT. See [LICENSE](LICENSE). External platform tools and third-party skills retain their own licenses and terms; they are not redistributed here.
