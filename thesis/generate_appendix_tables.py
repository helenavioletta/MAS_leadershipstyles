#!/usr/bin/env python3
"""
Regenerate the CSV-backed tabular bodies in appendix_results.tex.
Run from the Thesis/ directory or call it from sync_from_notebooks.sh.
"""
import csv
import math
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TABLES_DIR = BASE / 'appendix' / 'tables'
TEX_FILE = BASE / 'appendix_tables.tex'

STYLE_ORDER = ['coercive', 'authoritative', 'affiliative', 'democratic', 'pacesetting', 'coaching', 'baseline']
ALPHA_STYLE_ORDER = sorted(STYLE_ORDER)
PHASE_ORDER = ['Briefing', 'Planning', 'Coding', 'Writing', 'Review', 'Revision']
TASK_ORDER = ['short', 'long']


def escape_latex(s):
    if not isinstance(s, str):
        return str(s)
    # Order matters: %, $, &, #, _, ~, <, >
    s = s.replace('\\', '\\textbackslash{}')
    s = s.replace('%', '\\%')
    s = s.replace('$', '\\$')
    s = s.replace('&', '\\&')
    s = s.replace('#', '\\#')
    s = s.replace('_', '\\_')
    s = s.replace('~', '\\textasciitilde{}')
    s = s.replace('<', '$<$')
    s = s.replace('>', '$>$')
    return s


def fmt_num(x, decimals=3, comma=False, int_zero=False, strip=True):
    """Format a number for a math-mode LaTeX cell."""
    if isinstance(x, str):
        x = x.strip()
        if x in ('', 'NA', 'nan'):
            return ''
        x = float(x)
    if math.isnan(x):
        return ''
    if comma:
        s = f'{x:,.{decimals}f}'
    else:
        s = f'{x:.{decimals}f}'
    if strip:
        if '.' in s:
            dec = s.split('.', 1)[1]
            if all(c == '0' for c in dec) and not int_zero:
                # Keep one decimal zero (e.g. 1.0, 0.0, 100.0)
                s = s.rstrip('0').rstrip('.') + '.0'
            else:
                s = s.rstrip('0').rstrip('.')
    return f'${s}$'


def fmt_pvalue(x, decimals=4):
    if isinstance(x, str) and x.startswith('<'):
        return f'${x}$'
    if isinstance(x, str):
        x = x.strip()
        if x in ('', 'NA', 'nan'):
            return ''
        x = float(x)
    if math.isnan(x):
        return ''
    if x < 10 ** (-decimals):
        return f'$0.{"0" * decimals}$'
    return fmt_num(x, decimals=decimals, comma=False, int_zero=False, strip=True)


def fmt_text(x):
    return escape_latex(str(x))


def fmt_relationship(x):
    x = str(x)
    x = re.sub(r'\s+~\s+', '  $\\\\leftrightarrow$  ', x)
    return x


def style_formatter(capitalize=False):
    def _fmt(x):
        if capitalize:
            return x.capitalize()
        return x
    return _fmt


def sort_by_order(order, key):
    def _sort(rows):
        pos = {v: i for i, v in enumerate(order)}
        def _key(r):
            return (pos.get(r.get(key, ''), len(order)), r.get(key, ''))
        return sorted(rows, key=_key)
    return _sort


def sort_style_task(rows):
    pos = {v: i for i, v in enumerate(ALPHA_STYLE_ORDER)}
    tpos = {'short': 0, 'long': 1}
    return sorted(rows, key=lambda r: (pos.get(r['style'], 99), tpos.get(r['task'], 99)))


def sort_phase(rows):
    pos = {v: i for i, v in enumerate(PHASE_ORDER)}
    return sorted(rows, key=lambda r: pos.get(r['phase'], 99))


def load_csv(name):
    with open(TABLES_DIR / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Table configurations
# ---------------------------------------------------------------------------

TABLES = {
    'tab:03-kw-omnibus': {
        'csv': '03_kw_omnibus.csv',
        'col_spec': 'llrrr',
        'headers': ['Metric', 'Task', '$H$', '$p$', '$\\varepsilon^2$'],
        'columns': ['Metric', 'Task', 'H-Statistic', 'p-value', 'ε²'],
        'formatters': {
            'Metric': fmt_text,
            'Task': lambda x: x.capitalize(),
            'H-Statistic': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'p-value': lambda x: fmt_pvalue(x, 4),
            'ε²': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
        },
    },
    'tab:03-mde': {
        'csv': '03_mde.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{4cm}lrrrrrrrc',
        'headers': ['Metric', 'Task', 'Within SD', 'Observed range', 'MDE', 'MDE SD', 'Obs./MDE', 'Power', 'Detect?'],
        'columns': ['Metric', 'Task', 'Within-cond SD', 'Observed range', 'MDE (80% power)', 'MDE in SD units', 'Observed / MDE', 'Power at observed range', 'Detectable?'],
        'formatters': {
            'Metric': fmt_text,
            'Task': lambda x: x.capitalize(),
            'Within-cond SD': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'Observed range': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'MDE (80% power)': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'MDE in SD units': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'Observed / MDE': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
            'Power at observed range': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
            'Detectable?': lambda x: x.lower(),
        },
    },
    'tab:03-task-complexity-summary': {
        'csv': '03_task_complexity_summary.csv',
        'col_spec': 'lrrrrrrr',
        'headers': ['Task', 'Tokens', 'Duration (s)', 'Messages', 'Accuracy (judge)', 'Completeness (judge)', 'Cohesion (judge)', 'Quality (judge)'],
        'columns': ['task', 'total_tokens', 'duration_seconds', 'total_messages', 'accuracy', 'completeness', 'cohesion', 'quality'],
        'formatters': {
            'task': lambda x: x.capitalize(),
            'total_tokens': lambda x: fmt_num(x, 1, comma=True, strip=False),
            'duration_seconds': lambda x: fmt_num(x, 1, strip=False),
            'total_messages': lambda x: fmt_num(x, 1, strip=False),
            'accuracy': lambda x: fmt_num(x, 2, strip=False),
            'completeness': lambda x: fmt_num(x, 2, strip=False),
            'cohesion': lambda x: fmt_num(x, 2, strip=False),
            'quality': lambda x: fmt_num(x, 2, strip=False),
        },
        'sorter': sort_by_order(TASK_ORDER, 'task'),
    },
    'tab:03-style-by-task-summary': {
        'csv': '03_style_by_task_summary.csv',
        'col_spec': 'llrrrr',
        'headers': ['Style', 'Task', 'Overall quality', 'Tokens', 'Duration (s)', 'Satisfaction'],
        'columns': ['style', 'task', 'quality_mean', 'total_tokens', 'duration_seconds', 'survey_team_mean'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'task': lambda x: x.capitalize(),
            'quality_mean': lambda x: fmt_num(x, 2, strip=False),
            'total_tokens': lambda x: fmt_num(x, 1, comma=True, strip=False),
            'duration_seconds': lambda x: fmt_num(x, 2, strip=False),
            'survey_team_mean': lambda x: fmt_num(x, 2, strip=False),
        },
        'sorter': sort_style_task,
    },
    'tab:03-correlations': {
        'csv': '03_correlations.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{4.8cm}>{\\raggedright\\arraybackslash}p{4.2cm}rrrc',
        'headers': ['Relationship', 'Scope', '$n$', '$\\rho$', '$p$', 'Significant?'],
        'columns': ['Relationship', 'Scope', 'n', 'Spearman rho', 'p-value', 'Significant'],
        'formatters': {
            'Relationship': fmt_relationship,
            'Scope': fmt_text,
            'n': lambda x: f'${int(float(x))}$',
            'Spearman rho': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'p-value': lambda x: fmt_pvalue(x, 4),
            'Significant': fmt_text,
        },
    },
    'tab:03-trap-counts': {
        'csv': '03_trap_counts.csv',
        'col_spec': 'l>{\\raggedright\\arraybackslash}p{4cm}>{\\raggedright\\arraybackslash}p{5.0cm}rrrr',
        'headers': ['Task', 'Trap ID', 'Trap label', 'Missed', 'Partial', 'Caught', 'Total'],
        'columns': ['Task', 'Trap ID', 'Trap label', 'Missed', 'Partial', 'Caught', 'Total'],
        'formatters': {
            'Task': fmt_text,
            'Trap ID': fmt_text,
            'Trap label': fmt_text,
            'Missed': lambda x: f'${int(float(x))}$',
            'Partial': lambda x: f'${int(float(x))}$',
            'Caught': lambda x: f'${int(float(x))}$',
            'Total': lambda x: f'${int(float(x))}$',
        },
    },
    'tab:03-sentiment-omnibus': {
        'csv': '03_sentiment_omnibus.csv',
        'col_spec': 'l>{\\raggedright\\arraybackslash}p{5.6cm}rr',
        'headers': ['Analyzer', 'Metric', '$H$', '$p$'],
        'columns': ['Analyzer', 'Metric', 'H-Statistic', 'p-value'],
        'formatters': {
            'Analyzer': lambda x: 'RoBERTa' if x == 'ROBERTA' else x,
            'Metric': fmt_text,
            'H-Statistic': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'p-value': lambda x: fmt_pvalue(x, 4),
        },
    },
    'tab:03-sentiment-worker': {
        'csv': '03_sentiment_worker_only.csv',
        'col_spec': 'llrr',
        'headers': ['Analyzer', 'Worker', '$H$', '$p$'],
        'columns': ['Analyzer', 'Worker', 'H-Statistic', 'p-value'],
        'formatters': {
            'Analyzer': lambda x: 'RoBERTa' if x == 'ROBERTA' else x,
            'Worker': fmt_text,
            'H-Statistic': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
            'p-value': lambda x: fmt_pvalue(x, 4),
        },
    },
    'tab:03-sentiment-pairwise-overall-run-mean-compound': {
        'csv': '03_sentiment_pairwise_baseline.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{2.4cm}>{\\raggedright\\arraybackslash}p{2.0cm}>{\\raggedleft\\arraybackslash}p{1.6cm}>{\\raggedleft\\arraybackslash}p{1.6cm}>{\\raggedleft\\arraybackslash}p{1.3cm}>{\\raggedleft\\arraybackslash}p{1.8cm}>{\\centering\\arraybackslash}p{1.2cm}>{\\centering\\arraybackslash}p{1.5cm}>{\\raggedleft\\arraybackslash}p{1.2cm}',
        'headers': ['Analyzer', 'Style', '$M_{\\text{base}}$', '$M_{\\text{style}}$', '$U$', '$p$', '$<.05$', '$<$ Bonf', '$r$'],
        'columns': ['Analyzer', 'Style', 'baseline_mean', 'style_mean', 'U-Statistic', 'p-value', 'p < 0.05', 'p < Bonferroni', 'Effect r'],
        'formatters': {
            'Analyzer': lambda x: 'RoBERTa' if x == 'ROBERTA' else x,
            'Style': lambda x: x.capitalize(),
            'baseline_mean': lambda x: fmt_num(x, 4, int_zero=False, strip=True),
            'style_mean': lambda x: fmt_num(x, 4, int_zero=False, strip=True),
            'U-Statistic': lambda x: fmt_num(x, 1, int_zero=False, strip=False),
            'p-value': lambda x: fmt_pvalue(x, 4),
            'p < 0.05': fmt_text,
            'p < Bonferroni': fmt_text,
            'Effect r': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
        },
        'filter': lambda r: r['Metric'] == 'Overall Run Mean Compound',
    },
    'tab:03-sentiment-pairwise-boss-worker-sentiment-gap': {
        'csv': '03_sentiment_pairwise_baseline.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{2.4cm}>{\\raggedright\\arraybackslash}p{2.0cm}>{\\raggedleft\\arraybackslash}p{1.6cm}>{\\raggedleft\\arraybackslash}p{1.6cm}>{\\raggedleft\\arraybackslash}p{1.3cm}>{\\raggedleft\\arraybackslash}p{1.8cm}>{\\centering\\arraybackslash}p{1.2cm}>{\\centering\\arraybackslash}p{1.5cm}>{\\raggedleft\\arraybackslash}p{1.2cm}',
        'headers': ['Analyzer', 'Style', '$M_{\\text{base}}$', '$M_{\\text{style}}$', '$U$', '$p$', '$<.05$', '$<$ Bonf', '$r$'],
        'columns': ['Analyzer', 'Style', 'baseline_mean', 'style_mean', 'U-Statistic', 'p-value', 'p < 0.05', 'p < Bonferroni', 'Effect r'],
        'formatters': {
            'Analyzer': lambda x: 'RoBERTa' if x == 'ROBERTA' else x,
            'Style': lambda x: x.capitalize(),
            'baseline_mean': lambda x: fmt_num(x, 4, int_zero=False, strip=True),
            'style_mean': lambda x: fmt_num(x, 4, int_zero=False, strip=True),
            'U-Statistic': lambda x: fmt_num(x, 1, int_zero=False, strip=False),
            'p-value': lambda x: fmt_pvalue(x, 4),
            'p < 0.05': fmt_text,
            'p < Bonferroni': fmt_text,
            'Effect r': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
        },
        'filter': lambda r: r['Metric'] == 'Boss-Worker Sentiment Gap',
    },
    'tab:03-sentiment-phase-means': {
        'csv': '03_sentiment_phase_means.csv',
        'col_spec': 'lrrrrrr',
        'pivot': 'sentiment_phase',
    },
    'tab:03-phase-token-share': {
        'csv': '03_phase_token_share.csv',
        'col_spec': 'lrrrrrr',
        'pivot': 'phase_token',
    },
    'tab:03-style-pooled-summary': {
        'csv': '03_style_pooled_summary.csv',
        'col_spec': 'l c c c c c c c',
        'pivot': 'style_pooled',
    },
    'tab:03-quality-dimensions-by-style': {
        'csv': '03_quality_dimensions_by_style.csv',
        'col_spec': 'l >{\\centering\\arraybackslash}p{2.15cm} >{\\centering\\arraybackslash}p{2.15cm} >{\\centering\\arraybackslash}p{2.15cm} >{\\centering\\arraybackslash}p{2.15cm}',
        'headers': ['Style', 'Accuracy (judge)', 'Completeness (judge)', 'Cohesion (judge)', 'Quality (judge)'],
        'columns': ['style', 'accuracy', 'completeness', 'cohesion', 'quality'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'accuracy': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
            'completeness': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
            'cohesion': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
            'quality': lambda x: fmt_num(x, 2, int_zero=False, strip=True),
        },
        'sorter': sort_by_order(STYLE_ORDER, 'style'),
    },
    'tab:03-style-correlations': {
        'csv': '03_style_correlations.csv',
        'col_spec': 'l r r r l',
        'headers': ['Relationship', '$n$', '$\\rho$', '$p$', 'Significant?'],
        'columns': ['Relationship', 'n', 'Spearman rho', 'p-value', 'Significant?'],
        'formatters': {
            'Relationship': fmt_relationship,
            'n': lambda x: fmt_num(x, 0),
            'Spearman rho': lambda x: fmt_num(x, 3, strip=True),
            'p-value': lambda x: fmt_num(x, 4, strip=True),
            'Significant?': fmt_text,
        },
    },
    'tab:03-sentiment-satisfaction-correlation': {
        'csv': '03_sentiment_satisfaction_correlation.csv',
        'col_spec': 'lrr',
        'headers': ['Analyzer', '$\\rho$', '$p$'],
        'columns': ['Analyzer', 'Spearman rho', 'p-value'],
        'formatters': {
            'Analyzer': lambda x: x,
            'Spearman rho': lambda x: fmt_num(x, 2, strip=False, int_zero=False),
            'p-value': lambda x: fmt_pvalue(x, 4),
        },
    },
    'tab:03-sentiment-style-means': {
        'csv': '03_sentiment_style_means.csv',
        'col_spec': 'l c c c',
        'headers': ['Style', 'VADER mean', 'RoBERTa mean', 'Satisfaction mean'],
        'columns': ['style', 'VADER', 'RoBERTa', 'satisfaction_mean'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'VADER': lambda x: fmt_num(x, 4, strip=True),
            'RoBERTa': lambda x: fmt_num(x, 4, strip=True),
            'satisfaction_mean': lambda x: fmt_num(x, 3, int_zero=False, strip=True),
        },
        'sorter': sort_by_order(STYLE_ORDER, 'style'),
    },
    'tab:03-vader-roberta-agreement': {
        'csv': '03_vader_roberta_agreement.csv',
        'col_spec': 'l r r r',
        'headers': ['Statistic', '$n$', '$\\rho$', '$p$'],
        'columns': ['Statistic', 'n', 'Spearman rho', 'p-value'],
        'formatters': {
            'Statistic': fmt_text,
            'n': lambda x: fmt_num(x, 0),
            'Spearman rho': lambda x: fmt_num(x, 3, strip=True),
            'p-value': lambda x: '$< .001$' if float(x) < 0.001 else fmt_num(x, 4, strip=True),
        },
    },
    'tab:03-satisfaction-pairwise': {
        'csv': '03_satisfaction_pairwise.csv',
        'col_spec': 'l l c c r r c c r',
        'headers': ['Style', 'Task', 'Baseline mean', 'Style mean', '$U$', '$p$', '$p < .05$', '$p < \\text{Bonf.}$', '$r$'],
        'columns': ['Style', 'Task', 'baseline_mean', 'style_mean', 'U-Statistic', 'p-value', 'p < 0.05', 'p < Bonferroni', 'Effect r'],
        'formatters': {
            'Style': lambda x: x.capitalize(),
            'Task': lambda x: x.capitalize(),
            'baseline_mean': lambda x: fmt_num(x, 2, strip=True),
            'style_mean': lambda x: fmt_num(x, 2, strip=True),
            'U-Statistic': lambda x: fmt_num(x, 1, int_zero=False),
            'p-value': fmt_pvalue,
            'p < 0.05': fmt_text,
            'p < Bonferroni': fmt_text,
            'Effect r': lambda x: fmt_num(x, 3, strip=True),
        },
        'sorter': lambda rows: sorted(rows, key=lambda r: (
            STYLE_ORDER.index(r['Style']) if r['Style'] in STYLE_ORDER else 99,
            0 if r['Task'] == 'short' else 1
        )),
    },
    'tab:03-satisfaction-by-role': {
        'csv': '03_satisfaction_by_role.csv',
        'col_spec': 'l l c c',
        'headers': ['Style', 'Role', 'Mean satisfaction', 'SD'],
        'columns': ['style', 'role', 'mean_satisfaction', 'sd_satisfaction'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'role': fmt_text,
            'mean_satisfaction': lambda x: fmt_num(x, 2, strip=True),
            'sd_satisfaction': lambda x: fmt_num(x, 2, strip=True),
        },
        'sorter': lambda rows: sorted(rows, key=lambda r: (
            STYLE_ORDER.index(r['style']) if r['style'] in STYLE_ORDER else 99,
            ['Coder', 'Writer', 'Reviewer'].index(r['role']) if r['role'] in ['Coder', 'Writer', 'Reviewer'] else 99
        )),
    },
    'tab:03-communication-dominance': {
        'csv': '03_communication_dominance.csv',
        'col_spec': 'l r r r r r r r',
        'headers': ['Role', 'Total messages', 'Message \%', 'Mean messages / run', 'Total tokens', 'Token \%', 'Mean tokens / run'],
        'columns': ['role', 'total_messages', 'pct_messages', 'mean_messages_per_run', 'total_tokens', 'pct_tokens', 'mean_tokens_per_run'],
        'formatters': {
            'role': fmt_text,
            'total_messages': lambda x: fmt_num(x, 0, comma=True),
            'pct_messages': lambda x: f'${float(x):.1f}\\%$',
            'mean_messages_per_run': lambda x: fmt_num(x, 2, strip=True),
            'total_tokens': lambda x: fmt_num(x, 0, comma=True),
            'pct_tokens': lambda x: f'${float(x):.1f}\\%$',
            'mean_tokens_per_run': lambda x: fmt_num(x, 0, comma=True),
        },
    },
    'tab:03-tokens-per-message': {
        'csv': '03_tokens_per_message.csv',
        'col_spec': 'l l r r r',
        'headers': ['Agent', 'Style', 'Min.', 'Mean', 'Max.'],
        'columns': ['agent', 'style', 'min_tokens', 'mean_tokens', 'max_tokens'],
        'formatters': {
            'agent': fmt_text,
            'style': lambda x: x.capitalize(),
            'min_tokens': lambda x: fmt_num(x, 0, comma=True),
            'mean_tokens': lambda x: fmt_num(x, 0, comma=True),
            'max_tokens': lambda x: fmt_num(x, 0, comma=True),
        },
        'sorter': lambda rows: sorted(rows, key=lambda r: (
            ['Boss', 'Coder', 'Writer', 'Reviewer'].index(r['agent']) if r['agent'] in ['Boss', 'Coder', 'Writer', 'Reviewer'] else 99,
            STYLE_ORDER.index(r['style']) if r['style'] in STYLE_ORDER else 99
        )),
    },
    'tab:03-boss-worker-tokens-kw': {
        'csv': '03_boss_worker_tokens_kw.csv',
        'col_spec': 'llrr',
        'headers': ['Task', 'Scope', '$H$', '$p$'],
        'columns': ['task', 'scope', 'H-statistic', 'p-value'],
        'formatters': {
            'task': lambda x: x.capitalize(),
            'scope': fmt_text,
            'H-statistic': lambda x: fmt_num(x, 2, strip=True),
            'p-value': lambda x: fmt_pvalue(x, 4),
        },
        'sorter': lambda rows: sorted(rows, key=lambda r: (
            0 if r['task'] == 'short' else 1,
            0 if r['scope'] == 'Boss' else 1
        )),
    },
    'tab:03-boss-worker-tokens-per-run': {
        'csv': '03_boss_worker_tokens_per_run.csv',
        'col_spec': 'llrrrrrrrrrrrr',
        'headers': ['Style', 'Task', '$n$', 'Boss mean', 'Boss SD', 'Boss min', 'Boss max', 'Worker mean', 'Worker SD', 'Worker min', 'Worker max', 'Coder', 'Writer', 'Reviewer'],
        'columns': ['style', 'task', 'n', 'boss_mean', 'boss_std', 'boss_min', 'boss_max', 'worker_mean', 'worker_std', 'worker_min', 'worker_max', 'coder_mean', 'writer_mean', 'reviewer_mean'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'task': lambda x: x.capitalize(),
            'n': lambda x: f'${int(x)}$',
            'boss_mean': lambda x: fmt_num(x, 0, comma=True),
            'boss_std': lambda x: fmt_num(x, 0, comma=True),
            'boss_min': lambda x: fmt_num(x, 0, comma=True),
            'boss_max': lambda x: fmt_num(x, 0, comma=True),
            'worker_mean': lambda x: fmt_num(x, 0, comma=True),
            'worker_std': lambda x: fmt_num(x, 0, comma=True),
            'worker_min': lambda x: fmt_num(x, 0, comma=True),
            'worker_max': lambda x: fmt_num(x, 0, comma=True),
            'coder_mean': lambda x: fmt_num(x, 0, comma=True),
            'writer_mean': lambda x: fmt_num(x, 0, comma=True),
            'reviewer_mean': lambda x: fmt_num(x, 0, comma=True),
        },
        'sorter': sort_style_task,
    },
    'tab:02-health-check-summary': {
        'csv': '02_health_check_summary.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{5cm} >{\\raggedright\\arraybackslash}p{5cm} >{\\raggedright\\arraybackslash}p{3cm} >{\\centering\\arraybackslash}p{2cm}',
        'headers': ['Metric', 'Observed', 'Target', 'Status'],
        'columns': ['Metric', 'Observed', 'Target', 'Status'],
        'formatters': {
            'Metric': fmt_text,
            'Observed': fmt_text,
            'Target': fmt_text,
            'Status': fmt_text,
        },
    },
    'tab:02-identical-raw-scores': {
        'csv': '02_identical_raw_scores.csv',
        'col_spec': 'llrrr',
        'headers': ['Style', 'Task', '$n$', 'Identical runs', '\\%'],
        'columns': ['style', 'task', 'n', 'identical_runs', 'pct'],
        'formatters': {
            'style': lambda x: x.capitalize(),
            'task': lambda x: x.capitalize(),
            'n': lambda x: f'${int(float(x))}$',
            'identical_runs': lambda x: f'${int(float(x))}$',
            'pct': lambda x: fmt_num(x, 1, strip=False),
        },
        'sorter': sort_style_task,
    },
    'tab:02-judge-eta-squared': {
        'csv': '02_judge_eta_squared.csv',
        'col_spec': '>{\\raggedright\\arraybackslash}p{5cm} >{\\raggedright\\arraybackslash}p{3.5cm} r',
        'headers': ['Metric', 'Source', '$\\eta^2$'],
        'columns': ['Metric', 'Source', 'eta_squared'],
        'formatters': {
            'Metric': fmt_text,
            'Source': fmt_text,
            'eta_squared': lambda x: fmt_num(x, 3, strip=False),
        },
    },
    'tab:02-judge-scale-usage': {
        'csv': '02_judge_scale_usage.csv',
        'col_spec': 'lrrrrrc',
        'headers': ['Dimension', '$1$', '$2$', '$3$', '$4$', '$5$', 'Points used'],
        'columns': ['Dimension', 'pct_1', 'pct_2', 'pct_3', 'pct_4', 'pct_5', 'points_used'],
        'formatters': {
            'Dimension': fmt_text,
            'pct_1': lambda x: fmt_num(x, 1, strip=False),
            'pct_2': lambda x: fmt_num(x, 1, strip=False),
            'pct_3': lambda x: fmt_num(x, 1, strip=False),
            'pct_4': lambda x: fmt_num(x, 1, strip=False),
            'pct_5': lambda x: fmt_num(x, 1, strip=False),
            'points_used': lambda x: f'${int(float(x))}$',
        },
    },
}


def make_plain_tabular(config, col_spec):
    rows = load_csv(config['csv'])
    if 'filter' in config:
        rows = [r for r in rows if config['filter'](r)]
    if 'sorter' in config:
        rows = config['sorter'](rows)

    lines = [f'\\begin{{tabular}}{{{col_spec}}}',
             '    \\toprule',
             '    ' + ' & '.join(config['headers']) + ' \\\\',
             '    \\midrule']

    for r in rows:
        cells = []
        for col in config['columns']:
            fmt = config['formatters'].get(col, lambda x: x)
            val = r.get(col, '')
            cells.append(fmt(val))
        lines.append('    ' + ' & '.join(cells) + ' \\\\')

    lines.append('    \\bottomrule')
    lines.append('\\end{tabular}%')
    return '\n'.join(lines)


def make_sentiment_phase_pivot(config):
    rows = load_csv(config['csv'])
    data = {}
    for r in rows:
        key = (r['phase'], r['task'], r['analyzer'])
        data[key] = float(r['mean_compound'])

    lines = [f'\\begin{{tabular}}{{{config["col_spec"]}}}',
             '    \\toprule',
             '    & \\multicolumn{2}{c}{Pooled} & \\multicolumn{2}{c}{Short task} & \\multicolumn{2}{c}{Long task} \\\\',
             '    \\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}',
             '    Phase & VADER & RoBERTa & VADER & RoBERTa & VADER & RoBERTa \\\\',
             '    \\midrule']

    for phase in PHASE_ORDER:
        cells = [phase]
        for task in ['pooled', 'short', 'long']:
            for analyzer in ['vader', 'roberta']:
                val = data.get((phase, task, analyzer), math.nan)
                cells.append(fmt_num(val, 4, strip=False))
        lines.append('    ' + ' & '.join(cells) + ' \\\\')

    lines.append('    \\bottomrule')
    lines.append('\\end{tabular}%')
    return '\n'.join(lines)


def make_phase_token_pivot(config):
    rows = load_csv(config['csv'])
    data = {}
    for r in rows:
        if r['task'] == 'pooled':
            data[(r['style'], r['phase'])] = float(r['mean_share_pct'])

    lines = [f'\\begin{{tabular}}{{{config["col_spec"]}}}',
             '    \\toprule',
             '    Style & Briefing & Planning & Coding & Writing & Review & Revision \\\\',
             '    \\midrule']

    for style in STYLE_ORDER:
        cells = [style.capitalize()]
        for phase in PHASE_ORDER:
            val = data.get((style, phase), 0.0)
            cells.append(fmt_num(val, 1, strip=False))
        lines.append('    ' + ' & '.join(cells) + ' \\\\')

    lines.append('    \\bottomrule')
    lines.append('\\end{tabular}%')
    return '\n'.join(lines)


def make_style_pooled_summary(config):
    rows = load_csv(config['csv'])

    headers = ['Style', 'Overall quality', 'Satisfaction', 'Tokens', 'Duration (s)', 'Messages', 'API calls', 'Revision rounds']
    metrics = [
        ('quality_mean', 'quality_sd', 2, False),
        ('satisfaction_mean', 'satisfaction_sd', 2, False),
        ('tokens_mean', 'tokens_sd', 0, True),
        ('duration_mean', 'duration_sd', 1, False),
        ('messages_mean', 'messages_sd', 1, False),
        ('api_calls_mean', 'api_calls_sd', 1, False),
        ('revision_rounds_mean', 'revision_rounds_sd', 1, False),
    ]

    lines = [f'\\begin{{tabular}}{{{config["col_spec"]}}}',
             '    \\toprule',
             '    ' + ' & '.join(headers) + ' \\\\',
             '    \\midrule']

    for r in rows:
        cells = [r['style'].capitalize()]
        for mean_col, sd_col, decimals, comma in metrics:
            mean = float(r[mean_col])
            sd = float(r[sd_col])
            if comma:
                mean_s = f'{mean:,.{decimals}f}'.replace(',', '{,}')
                sd_s = f'{sd:,.{decimals}f}'.replace(',', '{,}')
            else:
                mean_s = f'{mean:.{decimals}f}'
                sd_s = f'{sd:.{decimals}f}'
            cells.append(f'${mean_s} \\pm {sd_s}$')
        lines.append('    ' + ' & '.join(cells) + ' \\\\')

    lines.append('    \\bottomrule')
    lines.append('\\end{tabular}%')
    return '\n'.join(lines)


def make_sentiment_style_agreement(config):
    rows = load_csv(config['csv'])
    agg = load_csv(config['agreement_csv'])[0]

    headers = ['Style', 'VADER', 'RoBERTa']
    lines = [f'\\begin{{tabular}}{{{config["col_spec"]}}}',
             '    \\toprule',
             '    ' + ' & '.join(headers) + ' \\\\',
             '    \\midrule']

    for r in rows:
        style = r['style'].capitalize()
        vader = fmt_num(r['VADER'], 4, strip=True)
        roberta = fmt_num(r['RoBERTa'], 4, strip=True)
        lines.append(f'    {style} & {vader} & {roberta} \\\\\\n')

    n = int(float(agg['n']))
    rho_val = float(agg['Spearman rho'])
    p_val = float(agg['p-value'])

    rho_s = f'{rho_val:.3f}'
    if p_val < 0.001:
        m = re.match(r'(\d\.\d+)e-0*(\d+)', f'{p_val:.2e}')
        if m:
            p_s = f'{m.group(1)} \\times 10^{{-{int(m.group(2))}}}'
        else:
            p_s = f'{p_val:.2e}'
    else:
        p_s = f'{p_val:.4f}'

    lines.append('    \\midrule')
    lines.append(f'    \\multicolumn{{3}}{{l}}{{VADER–RoBERTa rank agreement ($n={n}$): $\\rho = {rho_s},\\ p = {p_s}$}} \\\\\\n')
    lines.append('    \\bottomrule')
    lines.append('\\end{tabular}%')
    return '\\n'.join(lines)


def generate_tabular(label, config, col_spec):
    if config.get('pivot') == 'sentiment_phase':
        return make_sentiment_phase_pivot(config)
    if config.get('pivot') == 'phase_token':
        return make_phase_token_pivot(config)
    if config.get('pivot') == 'style_pooled':
        return make_style_pooled_summary(config)
    return make_plain_tabular(config, col_spec)


def find_tabular(block):
    """Return the (start, end) span of the first \begin{tabular}...\end{tabular}."""
    start_match = re.search(r'\\begin\{tabular\}\{', block)
    if not start_match:
        return None
    start = start_match.start()
    end_pattern = re.compile(r'\\end\{tabular\}')
    end_match = end_pattern.search(block, pos=start)
    if not end_match:
        return None
    end = end_match.end()
    if end < len(block) and block[end] == '%':
        end += 1
    return start, end


def process_table_block(block, label, config):
    marker_key = label.replace('tab:', '')
    marker_begin = f'%% AUTOGEN: {marker_key}'
    marker_end = f'%% END-AUTOGEN: {marker_key}'

    # If the block already has autogen markers, replace only between them.
    # Look for any AUTOGEN/END-AUTOGEN pair (old or new keys).
    marker_pattern = re.compile(
        r'^(\s*)%% AUTOGEN:.*$\n'
        r'(.*?)\n'
        r'^(\s*)%% END-AUTOGEN:.*$',
        re.DOTALL | re.MULTILINE,
    )
    match = marker_pattern.search(block)
    if match:
        indent = match.group(1)
        content = generate_tabular(label, config, config.get('col_spec', 'lrr'))
        new_block = f'{indent}{marker_begin} | {config.get("col_spec", "lrr")}\n{content}\n{indent}{marker_end}'
        return marker_pattern.sub(new_block, block, count=1)

    # Otherwise, replace the first \begin{tabular}...\end{tabular} with markers.
    tabular_span = find_tabular(block)
    if not tabular_span:
        return block

    start, end = tabular_span
    content = generate_tabular(label, config, config.get('col_spec', 'lrr'))
    new_block = block[:start] + \
                f'{marker_begin} | {config.get("col_spec", "lrr")}\n{content}' + \
                f'\n{marker_end}' + \
                block[end:]
    return new_block


def main():
    if not TABLES_DIR.exists():
        print(f'ERROR: {TABLES_DIR} not found.', file=sys.stderr)
        sys.exit(1)
    if not TEX_FILE.exists():
        print(f'ERROR: {TEX_FILE} not found.', file=sys.stderr)
        sys.exit(1)

    tex = TEX_FILE.read_text(encoding='utf-8')

    # Strip any existing AUTOGEN comments (they may be from an older run or broken).
    tex = re.sub(r'^\s*%% (?:AUTOGEN|END-AUTOGEN):.*$\n?', '', tex, flags=re.MULTILINE)

    table_pattern = re.compile(r'\\begin\{table\}(?:\[[^\]]*\])?\s*(.*?)\\end\{table\}', re.DOTALL)

    def repl(match):
        block = match.group(0)
        label_match = re.search(r'\\label\{(tab:[^}]+)\}', block)
        if not label_match:
            return block
        label = label_match.group(1)
        if label not in TABLES:
            return block
        config = TABLES[label]
        if 'csv' in config and not (TABLES_DIR / config['csv']).exists():
            print(f'WARNING: CSV {config["csv"]} not found, leaving {label} unchanged.', file=sys.stderr)
            return block
        return process_table_block(block, label, config)

    new_tex = table_pattern.sub(repl, tex)

    if new_tex == tex:
        print('No changes made to appendix_results.tex.')
    else:
        TEX_FILE.write_text(new_tex, encoding='utf-8')
        print(f'Updated {TEX_FILE}')


if __name__ == '__main__':
    main()
