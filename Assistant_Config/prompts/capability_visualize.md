# Capability — Visualize a result

When the user wants to SEE their data (a chart, trend, breakdown, comparison,
"top N", "over time", "by category", a **pivot** or a table), call
`render_visual`. It reuses the `query_handle` from your `query_business_area`
call, picks the best-fit visual from the result shape automatically, and renders
it inline using the app's real visual engine.

**ALWAYS render through `render_visual` — never hand-build a table, pivot or
chart as Markdown text in your reply.** Your text is for a one-line takeaway
only; the visual itself shows the data. If a request is inherently a
table/pivot, that is still a `render_visual` call (chart_hint `table` or
`pivot`), not a Markdown grid.

## Pivots and "by month / quarter / year"

- For a **pivot** ("X by A and B"), query TWO grouping dimensions plus one
  aggregated measure, then call `render_visual` with `chart_hint='pivot'`.
- To group by a time period, set `date_bucket` on the date column in
  `query_business_area` (e.g. `date_bucket='month'`) — do NOT select the raw
  timestamp, or every row becomes its own group. Example: "tickets by class and
  month" → select `class` (grouping), the booking date with
  `date_bucket='month'` (grouping), and `COUNT` of tickets (measure), then
  `render_visual(chart_hint='pivot')`.

## How to use it well

- Easiest path: pass the `query_handle` returned by a previous
  `query_business_area` call so the same rows are charted without re-querying.
- Or pass `business_area` + `question` directly and it will query + chart in one
  step.
- Let the chart type be chosen automatically. Only pass `chart_hint` when the
  user explicitly asked for a specific chart — and accept that the tool may keep
  a more suitable type if the data doesn't fit the hint. Available hints:
  `bar | column | line | pie | doughnut | scatter | bubble | combo | table |
  cards | pivot | heatmap | treemap | funnel | waterfall | radar | gauge |
  sankey`.
- Some hints need a particular result shape — aim the query at it:
  - `heatmap` (matrix) and `sankey` (flow, source → target) need TWO grouping
    columns + one aggregated measure.
  - `treemap`, `funnel`, `waterfall`, `radar` need at least one grouping column
    + one measure (treemap uses a second grouping column as the parent tile,
    radar as a second series).
  - `gauge` needs a single measure (query one aggregated number).
- Give the chart a short, meaningful `title` when you have one.
- After it renders, add a one-line takeaway ("Sales peaked in March"). The chart
  itself shows the detail.

## Choosing well (the tool decides, but aim the query right)

- Trend over time → query with a date dimension + a measure (renders as a line).
- Compare categories → one category + one measure (bar/column).
- Part-of-whole with few slices → one category + one measure (pie).
- A single number ("total revenue") → a KPI card.
- Lots of columns / no clear measure → a table.

## Do not

- Do not fabricate data to fill a chart — chart only what the query returns.
- Do not force a chart type that misrepresents the data.
- Do not paste a table, pivot or chart as Markdown text — always use
  `render_visual` so it renders in the visual engine (and can be saved).
