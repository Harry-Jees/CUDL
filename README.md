# CUDL

**Creative Unified Design Language** is an embeddable, cross-language design
language for describing pages, reusable components, layouts, interactions,
and design behavior inside existing applications.

CUDL does not replace the host application or its runtime. A host project such
as React, Python, Java, or C integrates CUDL through a compatible adapter. The
host remains responsible for application execution and lifecycle.

## Current status

CUDL is in its foundation stage. The repository includes an indentation-based
parser, a versioned intermediate representation, module and component
resolution, safe dynamic values, and an early React adapter. Native script
execution and production-ready host integration are still under development.

## First example

```cudl
page Home
    header
        title Hello, CUDL

    content
        text My first CUDL application
        button Get Started
```

## Native script direction

CUDL uses `#` for variables, `##` for comments, and `@` for function
declarations and calls. Indentation defines blocks. Values are dynamically typed and
ordinary text does not need quotes.

```cudl
script
    ## A small example
    #name = Harry

    @greet #person
        print Hello #person

    @greet #name
```

This is the intended syntax direction. The current parser recognizes these
structures, but it does not yet execute native CUDL functions or arithmetic.

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
- A small, consistent syntax should be easy for beginners to learn.
- Variables are dynamically typed and use an explicit `#` marker.
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

CUDL is an evolving language specification. Syntax and APIs in this early
prototype are subject to change.


## Run native CUDL scripts

The Python reference runtime supports dynamically typed variables, safe
expressions, hash-path indexing, function calls and returns:

```bash
cudl check examples/hello.cudl
cudl run examples/hello.cudl
```

Only native CUDL `script` blocks are interpreted. External-language blocks
remain owned by their host runtimes and are never executed by this command.
