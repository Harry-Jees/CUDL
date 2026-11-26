# CUDL v1 release-readiness audit (living checklist)

This checklist is evidence-oriented and deliberately distinguishes implemented behavior from proposals.

## Verified in the current development stack
- [x] Indentation-first syntax and canonical tag syntax reconciled in the current parser/spec work.
- [x] Parser errors include source context; malformed tag/function regressions are covered.
- [x] IR v1 serialization/deserialization validates node/category semantics and bounds.
- [x] React adapter has URL safety diagnostics and automated conformance tests.
- [x] React adapter preserves source lines on built-in/unknown elements, rejects unsupported KIT IR versions, and tests indexed host-data paths, inherited-property rejection and KIT property rendering.
- [x] CI exercises Python tests, all checked-in example validation, canonical five-part bundle compilation, adapter build and adapter tests.
- [x] CI builds source and wheel distributions, installs the wheel in a clean virtual environment, and smoke-tests the installed CLI against canonical examples ([run #181](https://github.com/Harry-Jees/CUDL/actions/runs/45458141278)).
- [x] CI renders nested adapter output through `react-dom/server`, checking actual React DOM serialization, HTML escaping, source metadata and the unknown-tag fallback.

## Acceptance gates before a v1 candidate
- [ ] Freeze a normative grammar and test every documented construct against it.
- [ ] Verify the CLI end-to-end from source file to stable IR and React output.
- [ ] Confirm source-span behavior across multiline strings, indentation and nested tags.
- [ ] Verify resource limits for parser depth, node count, source bytes and IR payloads.
- [ ] Run complete tests, lint, typecheck, package/build and example checks from a clean checkout.
- [ ] Verify interactive adapter output in a real browser, including host event/state integration; the server-render smoke test is not a browser test.
- [ ] Document the adapter's unsupported features, rather than promising events, native execution, responsive/theme systems or bundling without evidence.
- [ ] Review dependencies, license metadata, package contents and version compatibility.
- [ ] Tag a release candidate only after all gates pass; production release requires explicit approval.

## Known boundary
The React adapter is a prototype/conformance surface, not a production UI runtime. CI now verifies static React DOM rendering through `react-dom/server`; this does not verify browser interactions, host event/state integration or production bundling.
