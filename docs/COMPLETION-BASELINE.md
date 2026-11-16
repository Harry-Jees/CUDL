# CUDL v1 completion baseline

Audit date: 2026-11-16  
Repository: `Harry-Jees/CUDL`  
Baseline branch: `implementation/parser-resource-guards-20261115`  
Baseline commit: `0f96e455a28ddfd597cc5fdb66d970158ad2cdde`

This document is the evidence-based starting point for the 15-day completion sprint. It distinguishes implemented behavior from v1 acceptance work and explicitly excludes aspirational platform features from the completion claim.

## Current verified baseline

- Default branch is `main`; work is being developed on stacked feature branches and draft PRs.
- Latest development PR at audit: [#10 — bounded parser resource guards](https://github.com/Harry-Jees/CUDL/pull/10), based on PR #9.
- Open PR chain also includes #1–#9. There are no open repository issues at this audit.
- Latest CI for the baseline commit: [CUDL core checks #43632246503](https://github.com/Harry-Jees/CUDL/actions/runs/43632246503), completed successfully. The immediately preceding attempt failed and was followed by a corrective commit and successful run.
- Existing implementation includes an indentation-first lexer/parser, source-aware diagnostics, dynamic values and safe expression/runtime subset, versioned framework-neutral IR, five-part bundle validation (GUIDE/KIT/PAGES/SCRIPTS/TIME), Python reference runtime, React application adapter, device-aware route selection, host-aware PICKER previews, and bounded parser resource guards.
- Existing limits and unsupported behavior are documented in README and the language specifications. The TIME evaluator remains experimental and numeric-only.

## v1 completion definition

CUDL v1 is complete when all of the following are true on one reviewable development branch:

1. **One canonical language contract:** README, grammar, five-part specification, parser behavior, examples and tests agree on indentation, assignment, dynamic values, `#` references, `##` comments, `@` functions/component references, indexing and quoting rules. Any syntax ambiguity is resolved before implementation; no parallel syntax is introduced.
2. **Reliable front end:** lexer/parser enforce resource bounds, preserve source locations, reject malformed indentation and invalid syntax deterministically, and produce useful diagnostics.
3. **Consistent semantics and IR:** validated AST lowers to a versioned stable IR; child ordering, values, references, functions, component declarations and supported TIME data survive lowering without silent loss.
4. **Honest executable subset:** the reference runtime explicitly validates and executes only its documented safe subset. Unsupported control flow, native blocks and host behavior fail clearly or remain opaque; no arbitrary code execution is implied.
5. **Adapter contract:** React consumes the canonical IR and has tests for supported nodes, custom components, properties, routing and unsupported constructs. Other hosts are listed as planned unless a real adapter and tests exist.
6. **Tooling and examples:** CLI checks, parse/bundle/route/PICKER previews work on canonical examples; packaging/install instructions are reproducible.
7. **Release evidence:** complete Python tests, adapter tests/build, example/conformance checks, type checks where configured, and GitHub Actions pass. Docs clearly separate implemented, experimental and not-yet-supported capabilities.

Out of v1 unless already implemented and verified: production Android/iOS/desktop renderers, full INDERMOS package installation/resolution, arbitrary native-language execution, automatic device discovery, non-numeric TIME interpolation, frame/event dispatch and production playback.

## 15-day delivery sequence

| Day | Date | CUDL milestone | Exit evidence |
|---|---|---|---|
| 1 | Nov 16 | Repository audit and acceptance baseline | This document; branch/PR/CI snapshot |
| 2 | Nov 17 | Reconcile canonical syntax and specs | Spec/grammar consistency tests |
| 3 | Nov 18 | Parser edge cases and diagnostics | Malformed-input and location tests |
| 4 | Nov 19 | Semantic validation and IR contract | IR golden/round-trip tests |
| 5 | Nov 20 | React adapter consistency | Adapter behavior tests |
| 6 | Nov 21 | CLI, examples, packaging and docs | Reproducible install and command checks |
| 7 | Nov 22 | CUDL v1 release-candidate audit | Full suite and capability matrix |
| 8–14 | Nov 23–29 | Fix only CUDL gaps exposed by integration/review; avoid adding speculative language features | Regression-free CI and resolved review feedback |
| 15 | Nov 30 | Final CUDL v1 verification | Evidence-based completion report or exact remaining gaps |

## Working rules

- Inspect current branch, PR chain, commits and CI before every change.
- Keep changes on development/feature branches; stack PRs intentionally and never retarget or merge into `main` without explicit approval.
- Do not overwrite user changes or force-push.
- A passing CI run is required before calling a milestone verified. Report local checks separately from CI.
- Do not mark a feature complete because it appears in a design document; require implementation and tests.
