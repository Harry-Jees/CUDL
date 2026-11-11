# CUDL

**Creative Unified Design Language** is an embeddable, cross-language language
for describing application configuration, reusable components, pages, program
logic, and time-based experiences inside existing applications.

CUDL does not replace the host application or its runtime. A host project such
as React, Python, Java, or C integrates CUDL through compatible adapters. The
host remains responsible for application execution and lifecycle.

## Five core parts

A CUDL application is organized into five sections:

- `GUIDE` — project configuration, targets, dependencies, tokens, and shared rules.
- `KIT` — reusable components, themes, widgets, styles, and integrations.
- `PAGES` — screens, page structure, layout, navigation, and interactions.
- `SCRIPTS` — variables, functions, expressions, application logic, and host-language integration.
- `TIME` — timelines, scenes, tracks, keyframes, animation, sequencing, and temporal events.

The full syntax and architecture proposal, including a complete five-part
single-page example and the portable TIME model, is documented in
[`docs/five-part-language-spec.md`](docs/five-part-language-spec.md).

## Syntax direction

CUDL is indentation-first and dynamically typed. It uses `#` for variables,
`##` for comments, and `@` for functions or component references according
to context. Ordinary text does not need quotes.

```cudl
script
    ## A small example
    #name = Harry

    @greet #person
        print Hello #person

    @greet #name
```

## Current status

CUDL is in its foundation stage. The repository includes an indentation-based
parser, a versioned intermediate representation, module and component
resolution, safe dynamic values, a bounded native script runtime, and an early
React adapter. The five-part semantic bundle and TIME engine are design targets
and are not yet fully implemented.

The reference runtime supports a bounded subset of dynamic assignments,
safe expressions, hash-path indexing, function calls, return values, and text
interpolation. It does not execute arbitrary host-language blocks.

## Development

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
cudl check examples/hello.cudl
cudl parse examples/hello.cudl
cudl run examples/hello.cudl
pytest
```

## Design principles

- Indentation defines native CUDL blocks.
- Beginner-friendly syntax with a small, consistent set of symbols.
- Dynamic values and explicit hash-prefixed variable references.
- A framework-neutral, versioned intermediate representation.
- Portable semantics with host-specific adapters.
- Unsupported or malformed syntax produces clear diagnostics.
- Features are only described as implemented when parser, IR, runtime or
  adapter, tests, documentation, and CI agree.

CUDL is an evolving language. The five-part specification describes the
intended direction; consult implementation tests and release notes for
currently executable features.
