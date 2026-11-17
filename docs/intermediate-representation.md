# CUDL Intermediate Representation

The CUDL front end and host adapters communicate through a versioned
Intermediate Representation (IR).

## Pipeline

`source (.cudl) → lexer/parser → AST Document → lower() → CUDLIR → adapter`

The parser remains framework-neutral. React and other implemented adapters
consume the same IR rather than implementing independent CUDL parsers.

## Contract (version 1)

- The root object has `type: "CUDLIR"`, a numeric `version`, optional source
  path, and ordered `nodes`.
- Each node contains normalized `kind` and `name`, original argument
  `value`, semantic `category`, source line, and ordered children.
- Categories currently include `layout`, `element`, `declaration`,
  `component`, and `generic`.
- Unknown node names are preserved as generic nodes. This is intentional:
  custom components must survive parsing and lowering.
- Child order is significant and must be preserved by adapters.
- IR version changes require compatibility notes and tests.

## Serialization and validation

`IRDocument.to_dict()` produces the JSON-compatible v1 representation.
`IRDocument.from_dict(payload)` validates and reconstructs that representation
without evaluating values or executing native blocks.

The v1 deserializer rejects unknown versions, malformed field types, unknown
node categories, invalid source lines, excessive nesting and excessive node
counts. It uses the same front-end safety limits for maximum nesting and node
count. Callers must explicitly migrate older or newer payloads rather than
silently interpreting them as v1.

A round trip preserves node order, original value text, source line provenance,
custom node categories and opaque native-block source. The IR remains
structural: dynamic values and hash paths are preserved as text for the next
semantic or host-specific stage; deserialization does not resolve variables,
imports, component properties or expressions.

## Scope

IR v1 is a structural contract, not a renderer. It does not yet resolve imports,
evaluate expressions, validate component properties, or execute scripts.
Those belong to later semantic and runtime stages.
