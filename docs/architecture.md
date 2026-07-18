# Architecture Notes

This document will evolve as the first implementation is selected.

## Repository organization

- `src/` contains maintainable implementation code.
- `tests/` contains automated validation.
- `experiments/` contains exploratory work that may be discarded or promoted.
- `docs/` contains durable context, architecture, decisions, and learning records.

## Design expectations

Projects added here should favor:

- clear boundaries between components
- minimal dependencies
- reproducible local setup
- configuration outside source code
- no committed credentials or secrets
- automated tests for important behavior
- logs and errors that support troubleshooting
- documentation of meaningful tradeoffs

## Decision records

Significant decisions should eventually be captured under `docs/decisions/` using a simple format:

1. Context
2. Decision
3. Alternatives considered
4. Consequences
5. Follow-up

## First implementation

The architecture for the first working artifact has not yet been selected. It should be defined only after the initial problem and success criteria are narrow enough to complete.
