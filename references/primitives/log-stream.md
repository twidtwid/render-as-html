# Log stream — chronological event table

Load before implementing or changing the log-stream primitive. The compact picker + stub live in `SKILL.md` §Canonical primitives; reference implementation is `examples/primitives/09-logs.html`.

- **Pick when:** the data is a tail of timestamped events with a categorical level; newest-first reading is the default; payloads have structure worth expanding.
- **Required:** three live-state cues (pulsing dot + LIVE/PAUSED label + button mode-flip) so state reads without sound and survives a screenshot; ochre flash on new rows (~1.2s fade) for peripheral-glance detection; FATAL fills its pill background, other levels are outline-only (visual weight matches operational weight); counts are against full event set (never the filtered view); expanded payload uses the same syntax-token palette as the diff primitive (keys terracotta, strings ochre, numbers note-blue).
- **Interaction:** multi-select level chips; search across messages; click any row to expand the payload; `⏸ pause tail` freezes scroll and tail state so investigation doesn't lose the spot.
- **Avoid:** live-only state cues (must read when muted or in screenshots); identical pill styling for FATAL vs ERROR; expanding a row that destroys scroll position.
