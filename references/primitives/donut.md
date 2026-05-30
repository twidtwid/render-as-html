# Donut — categorical status mix

Load before implementing or changing the donut primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/01-donut.html`.

- **Pick when:** 2–5 mutually-exclusive categories where the proportion is more useful at a glance than the absolute counts.
- **Required:** subject-count in the center (never a category count, never an artifact count); ring track in `--rule-soft` so partial fills don't read as missing data; legend in CSS subgrid so counts and percents align in columns across rows.
- **Interaction:** click a legend row to isolate that segment (others dim); visible `× clear` appears while a filter is active.
- **Avoid:** 6+ slivers (use a stacked bar instead); donut-on-its-own as a hero — pair it with the data beneath.
