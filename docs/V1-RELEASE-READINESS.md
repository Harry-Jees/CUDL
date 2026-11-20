# CUDL v1 release-readiness audit (living checklist)

This checklist is evidence-oriented and deliberately distinguishes implemented behavior from proposals.

## Verified in the current development stack
- [x] Indentation-first syntax and canonical tag syntax reconciled in the current parser/spec work.
- [x] Parser errors include source context; malformed tag/function regressions are covered.
- [x] IR v1 serialization/deserialization validates node/category semantics and bounds.
- [x] React adapter has URL safety diagnostics and automated conformance tests.
- [x] CI exercises Python tests, example validation, adapter build and adapter tests.

## Acceptance gates before a v1 candidate
- [ ] Freeze a normative grammar and test every documented construct against it.
- [ ] Verify the CLI end-to-end from source file to stable IR and React output.
- [ ] Confirm source-span behavior across multiline strings, indentation and nested tags.
- [ ] Verify resource limits for parser depth, node count, source bytes and IR payloads.
- [ ] Run complete tests, lint, typecheck, package/build and example checks from a clean checkout.
- [ ] Test adapter output in a browser/runtime, including fallback behavior for unknown tags.
- [ ] Document the adapter's unsupported features, rather than promising events, native execution, responsive/theme systems or bundling without evidence.
- [ ] Review dependencies, license metadata, package contents and version compatibility.
- [ ] Tag a release candidate only after all gates pass; production release requires explicit approval.

## Known boundary
The React adapter is a prototype/conformance surface, not a production UI runtime. This checklist does not treat a successful TypeScript build as runtime verification.
