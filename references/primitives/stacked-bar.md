# Stacked bar — composition over time

Load before implementing or changing the stacked-bar primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/04-stacked-bar.html`.

- **Pick when:** categories sum to a meaningful whole each period (success/fail buckets, traffic mix, deal stages); 7–30 periods on the x-axis.
- **Required:** y-axis recomputes when categories toggle off; severity-ascending bottom-up stack order; per-column tooltip with the day's breakdown + total; chip legend doubles as the filter (clicking removes that category from the stack).
- **Interaction:** hover any column for the full breakdown tooltip; click chips to remove/add categories.
- **Avoid:** categories that don't sum cleanly (use grouped bars); fixed y-axis when categories can toggle off.
