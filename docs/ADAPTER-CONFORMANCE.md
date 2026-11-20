# CUDL adapter v1 conformance checklist

This checklist is a verification contract for host adapters. Items are acceptance
criteria, not claims that a given adapter currently passes them.

## Document and traversal

- [ ] Reject a document with an unsupported IR version before rendering.
- [ ] Preserve source-line information for runtime diagnostics.
- [ ] Render child nodes in source order.
- [ ] Treat unknown nodes as safe, non-executable generic nodes.
- [ ] Never evaluate preserved native-language block content.

## Data resolution

- [ ] Resolve only hash-prefixed paths through the supplied data object.
- [ ] Support property access and documented indexing forms.
- [ ] Fail safely on missing keys, invalid paths, or out-of-range indices.
- [ ] Do not expose prototype traversal, arbitrary reflection, or executable values.
- [ ] Keep data-resolution failures observable through diagnostics.

## Components and properties

- [ ] Resolve registered components consistently and case-insensitively.
- [ ] Preserve explicit property assignments and child ordering.
- [ ] Do not silently execute unregistered components.
- [ ] Keep component definitions separate from component invocations.

## Accessibility and rendering

- [ ] Use semantic host elements for known built-in tags where possible.
- [ ] Preserve values and text safely; do not inject raw HTML.
- [ ] Avoid adding event handlers from untrusted serialized IR.
- [ ] Report unsupported rendering behavior instead of silently changing intent.

## Release evidence

For each adapter, record the exact adapter version, supported tag map, passing
conformance test command, and known limitations in its README. Do not mark a
checkbox based solely on this specification. Test evidence belongs in CI or
review artifacts.
