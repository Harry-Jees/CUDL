# CUDL IR v1 semantic validation

The serialized IR is a versioned adapter boundary, not an arbitrary tree. Each
node retains its normalized kind/name, value, category, source line, raw source
when present, and ordered children.

## Category contract

The reference lowering pass assigns categories consistently:

- Built-in layout nodes (such as `page`, `row`, and `column`) are
  `layout`.
- Built-in visual elements (such as `button`, `text`, and `image`) are
  `element`.
- Known declarations (such as `component`, `theme`, `style`, and
  `script`) are `declaration`.
- Hash-free custom visual tags are preserved as `generic` unless a host
  explicitly recognizes them.
- `@name` nodes outside a script block are `component`. Within script
  context, a node with an indented body is a function declaration
  (`declaration`); a body-less invocation is `generic`.

IR deserialization validates these category semantics in addition to the
version, field types, source provenance, normalized kind, node-count and
nesting limits. Script context is propagated to child nodes so function
declarations and calls are distinguished consistently. A mismatch is rejected
with an `IRValidationError`; it is not silently normalized.

## Stability

IR v1 remains deterministic and round-trippable. This validation does not
execute source, native-language blocks or host components. Unknown node kinds
remain `generic` and can be preserved by adapters. Changing the IR shape or
category rules requires a versioned compatibility decision and conformance
tests.
