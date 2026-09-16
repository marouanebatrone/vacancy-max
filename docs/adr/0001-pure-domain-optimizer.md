# ADR 0001 — The optimizer core is framework-free

**Status:** accepted · 2026-09-16

## Context

The value of this product lives in one algorithm. Everything else -- REST,
serializers, the ORM -- is replaceable plumbing. The usual Django habit of
putting logic in models or views would make that algorithm slow to test
(database round-trips), hard to reason about (implicit state) and impossible to
reuse.

## Decision

`backend/apps/optimizer/domain/` is pure Python: frozen dataclasses in, frozen
dataclasses out. No Django import, no I/O, no clock, no randomness. A test in
`tests/domain/test_purity.py` fails the build if that is ever violated.

`services.py` is the only bridge: it loads ORM objects, converts them to domain
types, calls the solver, and converts the result back.

## Consequences

- Domain tests run in milliseconds and can be property-based with Hypothesis.
- The solver is reusable from a management command, a Celery task or a CLI.
- Slight cost: an explicit mapping layer between ORM models and domain types.
  Worth it.
