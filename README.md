# CUDL

**Creative Unified Design Language** is an embeddable, cross-language design language for describing pages, reusable components, layouts, interactions, and design behavior inside existing applications.

CUDL does not replace the host application or its runtime. A host project (such as React, Python, Java, or C) integrates CUDL through a compatible adapter. The host remains responsible for application execution and lifecycle.

## Current status

CUDL is at the foundation stage. This repository currently establishes the first parser prototype and a common, serializable syntax tree. Framework adapters and the native scripting runtime are planned, not yet implemented.

## First example

```cudl
page Home
    header
        title "Hello, CUDL"

    content
        text "My first CUDL application"
        button "Get Started"
```

## Core project sections

- `GUIDE` — project configuration, tokens, dependencies, and shared rules.
- `KIT` — reusable components, themes, widgets, and integrations.
- `PAGES` — screens, page structure, layout intentions, and interactions.
- `SCRIPTS` — logic, native CUDL scripts, animations, and supported external-language blocks.

## Development

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
cudl check examples/hello.cudl
cudl parse examples/hello.cudl
pytest
```

## Design principles

- Indentation defines native CUDL blocks.
- Syntax is intended to be readable and concise.
- Parsing produces a framework-neutral representation.
- Adapters translate that representation into host-framework capabilities.
- Unsupported or malformed syntax should produce clear diagnostics rather than silently pretending it worked.

## Roadmap

1. Lexer, parser, syntax tree, and diagnostics.
2. Intermediate representation and module resolution.
3. Component and layout semantics.
4. React adapter and host integration API.
5. Native scripting and safe execution model.
6. Additional adapters, tooling, and conformance tests.

CUDL is an evolving language specification. Syntax and APIs in this early prototype are subject to change.
