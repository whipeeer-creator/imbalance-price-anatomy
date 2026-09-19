# How often aFRR and mFRR are actually activated — Czechia, August 2026

The numbers behind
[progrunners.com/afrr-mfrr](https://progrunners.com/afrr-mfrr/), kept here so
they can be cited and checked without reading an article.

Computed from ČEPS data for August 2026: **2 977 quarter hours** of activation
volumes and **44 641 minutes** of prices. Same source and method as the
five-year imbalance study in this repository.

## Activation frequency

| Product | Share of quarter hours with activation | Median when active | Peak |
|---|---|---|---|
| aFRR upward | 76.3 % | 3.6 MW | 131.3 MW |
| aFRR downward | 71.1 % | −3.5 MW | −100 MW range |
| mFRR upward | 31.9 % | 2.0 MW | 55.7 MW |
| mFRR downward | 6.0 % | −2.8 MW | rare |

Both directions of aFRR are active in roughly three quarters of all quarter
hours, and frequently **both within the same quarter hour** — the imbalance
changes sign inside fifteen minutes and the controller follows it. Any model
that treats a quarter hour as simply "short" or "long" is already losing
information.

## Activated energy price

| Product | Median | p95 | Maximum |
|---|---|---|---|
| aFRR | 135.5 EUR/MWh | 221.8 EUR/MWh | 6 688 EUR/MWh |
| mFRR | 75 EUR/MWh (administrative) | — | — |

The median is unremarkable and the maximum is fifty times higher. That gap is
the whole economics of balancing: reserve revenue is not a steady stream with
occasional noise, it is a flat line with a handful of hours that pay for the
year.

The same shape appears in the imbalance settlement price, which is built from
these activations — [measured on 92 018 quarter hours](../README.md) in this
repository.

## Why the distinction matters

Capacity and energy are two different markets. Capacity is procured in advance
and pays you to stand ready whether or not you move; energy pays for what is
actually delivered when the TSO calls. A unit can earn from the first and never
be activated. Confusing them is the most common error in reserve revenue
models, and the figures above are energy only.

---

## The full article

This page is the data. The explanation — what each reserve layer does, how
FCR, aFRR, mFRR and RR hand the load down to each other, which European
platform clears what, and where to get the data for each market without a
token — is on the site:

**[aFRR and mFRR, with the numbers →](https://progrunners.com/afrr-mfrr/)**

Related, also on the site:

- [The ENTSO-E API, as it actually behaves](https://progrunners.com/entso-e-api/)
  — document types, publication delays, what breaks
- [European power market glossary](https://progrunners.com/glossary/)
- [Market data, country by country](https://progrunners.com/market-data/germany/)
  — where each TSO publishes, and what it costs you to get in

Everything we publish openly is listed at
[progrunners.com/open-source](https://progrunners.com/open-source/).

We build trading dashboards and market data pipelines for European power
markets. If you are modelling reserve revenue and the numbers will not
reconcile, write to `info@progrunners.com`.
