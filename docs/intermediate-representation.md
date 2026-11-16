# CUDL Intermediate Representation

The CUDL front end and host adapters communicate through a versioned
Intermediate Representation (IR).

## Pipeline

`source (.cudl) → lexer/parser → AST Document → lower() → CUDLIR → adapter`

The parser remains framework-neutral. React, Python, Java and other adapters
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

## Scope

IR v1 is a structural contract, not a renderer. It does not yet resolve imports,
evaluate expressions, validate component properties, or execute scripts.
Those belong to later semantic and runtime stages.
