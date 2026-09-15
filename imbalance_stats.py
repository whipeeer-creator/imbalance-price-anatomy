#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What the Czech imbalance price actually does. Reproduces every number
and chart in the README.

    python3 imbalance_stats.py qh.csv
    python3 imbalance_stats.py qh.csv --price-col cena_odch --out out/

Input is a CSV with one row per quarter hour and at least these columns
(rename with the flags if yours differ):

    date        YYYYMMDD or YYYY-MM-DD
    time        HH:MM
    price       imbalance settlement price, EUR/MWh
    imbalance   system imbalance, MW — negative = system short
    da_price    day-ahead price, EUR/MWh (optional)

Where to get it: ČEPS publishes the system imbalance
(https://github.com/whipeeer-creator/ceps-ote), OTE publishes the final
imbalance price in its yearly market reports. This deliberately ships no
market data — get your own and point the script at it.

Charts need matplotlib. Everything else is standard library.
"""
import argparse
import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

BANDS = [(None, -500), (-500, -250), (-250, -100), (-100, 0),
         (0, 100), (100, 250), (250, 500), (500, None)]


def load(path, cols):
    rows = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            try:
                rows.append({
                    'year': r[cols['date']][:4],
                    'hour': int(str(r[cols['time']])[:2]),
                    'price': float(r[cols['price']]),
                    'imb': float(r[cols['imbalance']]),
                    'da': float(r[cols['da']]) if cols['da'] in r
                    and r[cols['da']] else None,
                })
            except (ValueError, KeyError):
                continue          # empty cells are normal in these exports
    if not rows:
        sys.exit('no usable rows — check the column names with --help')
    return rows


def pct(values, q):
    """Percentile by position. No interpolation: with 90k points it is
    the same to a decimal, and it keeps the dependency list empty."""
    s = sorted(values)
    return s[min(len(s) - 1, int(q / 100 * len(s)))]


def distribution(rows):
    p = [r['price'] for r in rows]
    neg = sum(1 for x in p if x < 0)
    high = sum(1 for x in p if x > 500)
    total_abs = sum(abs(x) for x in p)
    tail_abs = sum(abs(x) for x in p if x < 0 or x > 500)
    return {
        'n': len(p), 'mean': st.mean(p), 'median': pct(p, 50),
        'min': min(p), 'max': max(p),
        'p1': pct(p, 1), 'p5': pct(p, 5), 'p25': pct(p, 25),
        'p75': pct(p, 75), 'p95': pct(p, 95), 'p99': pct(p, 99),
        'share_negative': 100 * neg / len(p),
        'share_above_500': 100 * high / len(p),
        'tail_share_of_rows': 100 * (neg + high) / len(p),
        'tail_share_of_magnitude': 100 * tail_abs / total_abs,
    }


def by_year(rows):
    out = []
    groups = defaultdict(list)
    for r in rows:
        groups[r['year']].append(r)
    for year in sorted(groups):
        g = groups[year]
        p = [x['price'] for x in g]
        out.append({
            'year': year, 'quarter_hours': len(g), 'median': pct(p, 50),
            'share_negative': 100 * sum(1 for x in p if x < 0) / len(p),
            'share_above_500': 100 * sum(1 for x in p if x > 500) / len(p),
            'share_short': 100 * sum(1 for x in g if x['imb'] < 0) / len(g),
        })
    return out


def by_sign(rows):
    out = []
    for name, keep in (('short', lambda x: x['imb'] < 0),
                       ('long', lambda x: x['imb'] > 0)):
        p = [r['price'] for r in rows if keep(r)]
        if not p:
            continue
        out.append({'system': name, 'quarter_hours': len(p),
                    'median': pct(p, 50), 'p5': pct(p, 5), 'p95': pct(p, 95)})
    return out


def by_band(rows):
    out = []
    for lo, hi in BANDS:
        p = [r['price'] for r in rows
             if (lo is None or r['imb'] >= lo) and (hi is None or r['imb'] < hi)]
        if len(p) < 50:
            continue
        out.append({'imbalance_from': lo if lo is not None else '',
                    'imbalance_to': hi if hi is not None else '',
                    'quarter_hours': len(p), 'median_price': pct(p, 50)})
    return out


def write(path, rows):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print('  wrote', path)


def charts(rows, out):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('  (matplotlib not installed — skipping charts)')
        return

    ink, accent, warn = '#11151c', '#4f7df3', '#e0765a'

    # 1 — the distribution, clipped so the tail does not flatten the body
    fig, ax = plt.subplots(figsize=(8, 3.6))
    p = [min(max(r['price'], -400), 900) for r in rows]
    ax.hist(p, bins=130, color=accent, edgecolor='none')
    ax.axvline(0, color=warn, lw=1)
    ax.set_xlabel('imbalance price, EUR/MWh  (clipped to −400…900)')
    ax.set_ylabel('quarter hours')
    ax.set_title('Where the imbalance price actually lands', color=ink,
                 loc='left', fontsize=11)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(Path(out) / 'distribution.png', dpi=140)
    plt.close(fig)

    # 2 — the tail collapsing year by year
    years = by_year(rows)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = [y['year'] for y in years]
    ax.plot(x, [y['share_negative'] for y in years], 'o-', color=accent,
            label='negative price')
    ax.plot(x, [y['share_above_500'] for y in years], 'o-', color=warn,
            label='above 500 EUR/MWh')
    ax.set_ylabel('% of quarter hours')
    ax.set_title('The extremes are disappearing', color=ink, loc='left',
                 fontsize=11)
    ax.legend(frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(Path(out) / 'tail_by_year.png', dpi=140)
    plt.close(fig)

    # 3 — price against system imbalance
    bands = by_band(rows)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    labels = [f"{b['imbalance_from']}…{b['imbalance_to']}" for b in bands]
    vals = [b['median_price'] for b in bands]
    ax.bar(labels, vals,
           color=[warn if v < 0 else accent for v in vals])
    ax.axhline(0, color=ink, lw=.8)
    ax.set_xlabel('system imbalance, MW  (negative = system short)')
    ax.set_ylabel('median imbalance price, EUR/MWh')
    ax.set_title('One variable explains the sign', color=ink, loc='left',
                 fontsize=11)
    ax.tick_params(axis='x', labelrotation=30, labelsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(Path(out) / 'price_vs_imbalance.png', dpi=140)
    plt.close(fig)
    print('  wrote 3 charts')


def main():
    a = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('csv')
    a.add_argument('--date-col', default='den')
    a.add_argument('--time-col', default='qh')
    a.add_argument('--price-col', default='cena_odch')
    a.add_argument('--imbalance-col', default='sys_odch')
    a.add_argument('--da-col', default='dt')
    a.add_argument('--out', default='data')
    args = a.parse_args()

    rows = load(args.csv, {'date': args.date_col, 'time': args.time_col,
                           'price': args.price_col,
                           'imbalance': args.imbalance_col, 'da': args.da_col})
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    d = distribution(rows)
    print(f"\n{d['n']} quarter hours")
    print(f"  median {d['median']:.1f} · mean {d['mean']:.1f} · "
          f"min {d['min']:.1f} · max {d['max']:.1f} EUR/MWh")
    print(f"  p1 {d['p1']:.0f} · p5 {d['p5']:.0f} · p25 {d['p25']:.0f} · "
          f"p75 {d['p75']:.0f} · p95 {d['p95']:.0f} · p99 {d['p99']:.0f}")
    print(f"  negative {d['share_negative']:.1f}% · "
          f"above 500 {d['share_above_500']:.1f}%")
    print(f"  the tail is {d['tail_share_of_rows']:.1f}% of quarter hours "
          f"but {d['tail_share_of_magnitude']:.1f}% of total magnitude")

    print('\nby year')
    print(f"  {'year':<6}{'QH':>8}{'median':>9}{'neg':>8}{'>500':>8}{'short':>8}")
    for y in by_year(rows):
        print(f"  {y['year']:<6}{y['quarter_hours']:>8}{y['median']:>9.1f}"
              f"{y['share_negative']:>7.1f}%{y['share_above_500']:>7.1f}%"
              f"{y['share_short']:>7.1f}%")

    print('\nby sign of the system imbalance')
    for s in by_sign(rows):
        print(f"  {s['system']:<8}n={s['quarter_hours']:>6}  "
              f"median {s['median']:>8.1f}  p5 {s['p5']:>8.1f}  "
              f"p95 {s['p95']:>8.1f}")

    print('\nby size of the system imbalance')
    for b in by_band(rows):
        print(f"  {str(b['imbalance_from']):>6} … {str(b['imbalance_to']):<6}"
              f"n={b['quarter_hours']:>6}  median {b['median_price']:>8.1f}")

    da = [r for r in rows if r['da'] is not None]
    if da:
        diff = [r['price'] - r['da'] for r in da]
        corr = st.correlation([r['imb'] for r in rows],
                              [r['price'] for r in rows])
        print(f"\nmedian (imbalance price − day-ahead): {pct(diff, 50):.1f} EUR/MWh")
        print(f"correlation imbalance vs price: {corr:.3f}")

    print('\noutputs')
    write(out / 'summary_by_year.csv', by_year(rows))
    write(out / 'by_system_sign.csv', by_sign(rows))
    write(out / 'price_vs_imbalance.csv', by_band(rows))
    write(out / 'distribution.csv',
          [{'metric': k, 'value': round(v, 3)} for k, v in d.items()])
    charts(rows, out)
    print()


if __name__ == '__main__':
    main()
