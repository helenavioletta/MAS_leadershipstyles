# MAS — Multi-Agent System for Leadership Style Experiments

A multi-agent system built with the Anthropic Python SDK to study how different leadership styles affect team performance in data analysis tasks.

Four LLM-powered agents (Boss, Coder, Writer, Reviewer) collaborate on a shared task while the Boss operates under one of six Goleman leadership styles (or a baseline). The system logs all communication, API calls, and code executions for post-experiment analysis.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

## Project Structure

```
MAS/
├── config/
│   ├── experiment_config.yaml      # Models, styles, token budgets
│   └── tasks/
│       ├── test_task.md             # Smoke test (1 chart, 1 sentence)
│       ├── short_task.md            # Short task (4 charts + 100-word summary)
│       └── long_task.md             # Long task (full EDA)
│
├── prompts/
│   ├── boss/
│   │   ├── 1_base_role.md           # Shared base role for all styles
│   │   ├── 2_baseline.md            # No style overlay
│   │   ├── 3_coercive.md            # "Do what I tell you"
│   │   ├── 4_authoritative.md       # "Come with me"
│   │   ├── 5_affiliative.md         # "People come first"
│   │   ├── 6_democratic.md          # "What do you think?"
│   │   ├── 7_pacesetting.md         # "Do as I do, now"
│   │   └── 8_coaching.md            # "Try this"
│   ├── coder.md                     # Coder system prompt
│   ├── writer.md                    # Writer system prompt
│   ├── reviewer.md                  # Reviewer system prompt
│   ├── control_agent.md             # Post-run evaluation prompt
│   └── satisfaction_survey.md        # Post-run satisfaction survey questions
│
├── src/
│   ├── orchestrator.py              # 7-phase workflow, turn management
│   ├── message_bus.py               # Shared chat channel → messages.jsonl
│   ├── shared_state.py              # Task spec, outputs, variables, report draft
│   ├── sandbox.py                   # Code execution (subprocess) → code_executions.jsonl
│   ├── agents/
│   │   ├── base_agent.py            # Base class: prompt building, API calls, token tracking
│   │   ├── boss.py                  # Boss: base role + style overlay (Sonnet)
│   │   ├── coder.py                 # Coder: code loop + sandbox + presentation (Haiku)
│   │   ├── writer.py                # Writer: narrative + saves report draft (Haiku)
│   │   └── reviewer.py              # Reviewer: quality gate on outputs + text (Haiku)
│   ├── evaluation/
│   │   ├── control_agent.py         # LLM-as-judge: quality scores + trap detection
│   │   ├── satisfaction_survey.py    # Post-run satisfaction survey workflow
│   │   └── sentiment.py             # Sentiment scoring: VADER + RoBERTa backends, per-message scores + aggregates
│   ├── analysis/
│   │   └── sentiment_io.py          # Loads sentiment_<analyzer>.json into DataFrames (shared by both sentiment notebooks)
│   └── utils/
│       ├── api_client.py            # Anthropic SDK wrapper, retries, token logging
│       ├── logger.py                # Run folder setup, metadata.json
│       └── transcript_generator.py   # Converts messages.jsonl into transcript.md for human readability
│
├── experiments/
│   ├── run_experiments.py           # Run a single experiment
│   ├── run_all.py                   # Batch all styles × tasks × repetitions
│   └── score_sentiment.py           # (Re)score sentiment for existing runs — no API calls
│
├── notebooks/
│   ├── 01_explore_dataset.ipynb     # Dataset exploration
│   ├── 01_long_task_ground_truth.ipynb  # Ground truth for long task
│   ├── 02_validation_check.ipynb    # Data integrity & validity checks
│   ├── 03_analyze_results.ipynb     # Cross-run analysis
│   ├── 03_sentiment_analysis_vader.ipynb    # Message log sentiment (VADER)
│   └── 03_sentiment_analysis_roberta.ipynb  # Message log sentiment (RoBERTa)
│
├── data/                            # global_weather.csv (not tracked in git)
├── results/                         # Experiment outputs (not tracked in git)
├── .env                             # API key (not tracked in git)
└── requirements.txt
```

## Workflow

Each experiment run executes a 7-phase sequential workflow:

| Phase | Name | What happens |
|-------|------|-------------|
| 1 | Briefing | Boss introduces the task |
| 2 | Planning | Boss plans → Coder, Writer, Reviewer discuss → Boss wraps up |
| 3 | Coding | Coder writes & executes code → Boss check-in |
| 4 | Writing | Writer drafts report → Boss check-in |
| 5 | Review | Reviewer evaluates deliverables |
| 6 | Revision | Boss decides: `SHIP`, `REVISE_CODE`, `REVISE_REPORT`, or `REVISE_BOTH` (max 2 rounds) |
| 7 | Delivery | Final output logged |

## Experiment Design

- **7 leadership styles** (6 Goleman + 1 baseline)
- **2 task types** (short, long)
- **5 repetitions** per condition
- **Total: 7 × 2 × 5 = 70 runs**

## Run Outputs

Each run produces a folder in `results/` with:

```
results/{style}_{task}_run{N}/
├── messages.jsonl              # Full message history
├── api_calls.jsonl             # Every LLM call with tokens
├── code_executions.jsonl       # Every code execution with stdout/stderr
├── shared_state_final.json     # Final snapshot of shared state
├── evaluation.json             # Control Agent scores + trap detection verdicts
├── survey_results.json         # Satisfaction survey scores per worker
├── sentiment_vader.json        # Per-message sentiment scores + aggregates (VADER lexicon)
├── sentiment_roberta.json      # Per-message sentiment scores + aggregates (RoBERTa transformer)
├── metadata.json               # Run parameters and summary stats
└── outputs/                    # Charts, data files produced by Coder
```

### Sentiment artifacts

`messages.jsonl` is the only raw artifact — it costs API calls and can never be
regenerated. Sentiment is *derived* from it: deterministic, offline, and one
file per analyzer, so VADER and RoBERTa results exist side by side and are
directly comparable (identical message filtering and aggregation, only the
scorer differs).

Each file carries a provenance block — analyzer, model, pinned model revision,
library versions, and the SHA-256 of the `messages.jsonl` it was derived from.
That makes the file its own cache: re-scoring skips runs that are up to date,
and automatically recomputes any run whose messages or analyzer configuration
changed.

```bash
# (Re)score existing runs — no API calls, no experiment re-run needed
python experiments/score_sentiment.py                     # both analyzers, all runs
python experiments/score_sentiment.py --analyzer roberta  # one analyzer
python experiments/score_sentiment.py --run coercive_short_run01
python experiments/score_sentiment.py --force             # ignore the up-to-date check
python experiments/score_sentiment.py --dry-run           # report what would be scored
```

`run_experiments.py` writes both files automatically for new runs, so
`score_sentiment.py` is only needed when adding an analyzer, changing the
scoring configuration, or rebuilding artifacts from scratch.

## Running Experiments

### Smoke test (validate pipeline without spending tokens on evaluation)

```bash
python experiments/run_experiments.py --smoke --style baseline
python experiments/run_experiments.py --smoke --style coercive
```

Force evaluation on a smoke test:
```bash
python experiments/run_experiments.py --smoke --style coercive --eval
```

### Single experiment run

```bash
python experiments/run_experiments.py --style democratic --task short --run 1
python experiments/run_experiments.py --style coercive --task long --run 2
```

Skip evaluation (useful for debugging):
```bash
python experiments/run_experiments.py --style coercive --task short --run 1 --skip-eval
```

### Full batch (7 styles × 2 tasks × 5 reps = 70 runs)

```bash
python experiments/run_all.py
```

- Skips already-completed runs (resume support)
- Retries failed runs once before continuing
- Prints summary table at the end

### CLI flags reference

| Flag | Effect |
|------|--------|
| `--style X` | Required. One of: baseline, coercive, authoritative, affiliative, democratic, pacesetting, coaching |
| `--task X` | Required for experiments: `short` or `long`. Auto-set by `--smoke` |
| `--run N` | Repetition number (default: 1) |
| `--smoke` | Uses test_task.md, skips evaluation by default |
| `--skip-eval` | Skip post-experiment evaluation on any run |
| `--eval` | Force evaluation even on smoke test |

## Models

- **Boss:** `claude-sonnet-5` — needs nuanced leadership behavior
- **Workers:** `claude-haiku-4-5-20251001` — cost-efficient, handles structured tasks