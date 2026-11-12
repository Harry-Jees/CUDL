# CUDL

**Creative Unified Design Language** is an embeddable, cross-language design language
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

## Toolchain architecture

CUDL's planned host-integration toolchain has two cooperating services:

- **INDERMOS** — Intelligent Dependency Resolver and Module Ordering System.
  It identifies host stacks from supplied manifests, inspects declared dependencies,
  resolves local CUDL modules, orders them and reports actionable diagnostics.
- **PICKER** — Platform Intelligent CUDL Kit Exchange Router. The
  `cudl_picker` package selects compatible KIT components and native script
  blocks for the host stack, then prepares a portable, native-convertible
  bundle.

They are toolchain services, not extra language sections or source keywords.
INDERMOS supplies a read-only host/dependency report; PICKER uses an explicit
host profile to filter native script blocks. Full packaging remains planned. Their architecture, proposed APIs,
safety boundaries and implementation stages are specified in
[`docs/indermos-picker-toolchain.md`](docs/indermos-picker-toolchain.md).

**Status:** the repository has local module resolution and dependency-first ordering, component-level and GUIDE-level device routing, and an initial PICKER selector for declared React, Python, Android and iOS host profiles. Full transitive/registry dependency resolution, automatic device detection, generated platform bundles and production host adapters remain unfinished.

## Current status

CUDL is in its foundation stage. The repository includes an indentation-based
parser, a versioned intermediate representation, module and component
resolution, safe dynamic values, a bounded native script runtime, and an early
React adapter with a first five-part application entry point. The five-part
bundle validator and section-aware application IR are implemented on the
current development branch. An experimental numeric TIME compiler and
deterministic evaluator support bounded timeline, scene, track, keyframe,
interpolation and playback-mode semantics; host rendering, event dispatch,
non-numeric interpolation and production TIME adapters remain in development.

The reference runtime supports a bounded subset of dynamic assignments,
safe expressions, hash-path indexing, function calls, return values, and text
interpolation. It does not execute arbitrary host-language blocks. Native
Python, JavaScript, Java and C/C++ execution, general-purpose control flow,
a CUDL-owned garbage collector and full JSON block interoperability are not
currently implemented.

## Configuration and routing

GUIDE and KIT configuration uses explicit assignments (`name = value`). Built-in keywords, section names and identifier lookup are case-insensitive. A single application file can contain all five sections in any order; each section may appear once.

Device routing supports a GUIDE-level default map and component-specific overrides. Rules can match platform, device class, width range, input mode and required capabilities. Component-local rules take precedence over global rules, then the declared `default` route is used. PICKER selects native script blocks for an explicit host profile; it does not execute them or install dependencies.

See [`docs/platform-routing.md`](docs/platform-routing.md) for routing and PICKER examples.

## Development

Requires Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
cudl check examples/hello.cudl
cudl parse examples/hello.cudl
cudl run examples/hello.cudl
cudl bundle examples/five-part-welcome.cudl
cudl analyze .
pytest
```

## Design principles

- Indentation defines native CUDL blocks.
- Beginner-friendly syntax with a small, consistent set of symbols.
- Dynamic values and explicit hash-prefixed variable references.
- A framework-neutral, versioned intermediate representation.
- Portable semantics with host-specific adapters.
- Unsupported or malformed syntax produces clear diagnostics.
- Parsing and planning must not execute native code or install dependencies.
- Features are only described as implemented when parser, IR, runtime or
  adapter, tests, documentation, and CI agree.

CUDL is an evolving language. The five-part specification describes the
intended direction; consult implementation tests and release notes for
currently executable features.
