# Dense ops table

Load before implementing or changing the dense-ops-table primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/06-table-ops.html`.

- **Pick when:** flat list of records keyed by an identifier; ≥6 rows; filtering / sorting is the central interaction. The instrument-register workhorse.
- **Required:** mono first column (the identifier); sans middle (the labels); mono right-aligned numerics with `tabular-nums`; status pills carry outline + colored dot + text (color is never the sole signal); footer reports true row count (not the filtered count).
- **Interaction:** column-header click cycles sort asc → desc → none (always-escapable); pill-filter in toolbar inverts (ink fill, paper text) when active; search across identifier + label fields.
- **Avoid:** color-only status; footers that lie about dataset size when filtered; sorts with no neutral state.
