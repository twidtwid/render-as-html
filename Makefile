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

# Every page under examples/ is a real artifact and faces the full gate, incl.
# the >=3 HTML-native feature floor. Only examples/primitives/*.html — the
# single-primitive reference frames, which showcase one feature in isolation by
# design — lint with --reference, which skips ONLY that floor.
lint-examples:
	node scripts/lint-artifact.mjs index.html examples/*.html
	node scripts/lint-artifact.mjs --reference examples/primitives/*.html
