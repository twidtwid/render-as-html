# Quality gates for render-as-html. `make check` is THE pre-push answer to
# "does the repo pass?" — CI runs exactly this.
SHELL := /bin/bash

.PHONY: check test perf tokens versions contracts lint-examples

check: test perf tokens versions contracts lint-examples
	@echo "make check: all gates green"

test:
	uv run --with pytest pytest tests/ -q

perf:
	uv run python scripts/perf_harness.py --check --no-report

tokens:
	node scripts/check-tokens.mjs

versions:
	node scripts/check-versions.mjs

contracts:
	node scripts/review-contracts.mjs

# Shape artifacts get the full gate (incl. the >=3 HTML-native feature floor).
# examples/index.html and examples/primitives.html are gallery/reference surfaces
# (static link lists, no interactive markup) — they lint with --reference, which
# skips ONLY the feature floor, like examples/primitives/*.html.
lint-examples:
	node scripts/lint-artifact.mjs index.html $(filter-out examples/index.html examples/primitives.html,$(wildcard examples/*.html))
	node scripts/lint-artifact.mjs --reference examples/index.html examples/primitives.html examples/primitives/*.html
