# CUDL canonical syntax contract

Status: normative syntax decisions for v1. The parser and runtime remain the
source of truth for what is executable; a syntax rule marked "specified" is
not automatically an implementation claim.

## 1. Source modes

- A complete application uses the five peer sections: `GUIDE`, `KIT`,
  `PAGES`, `SCRIPTS` and `TIME`.
- Sections may appear in any order, at most once each. Empty sections may be
  omitted.
- A source fragment may contain a single page, script or component body when
  a host explicitly requests fragment parsing. A fragment is not silently
  treated as a complete five-part application.
- Built-in keywords and section names are case-insensitive. User-defined names
  preserve their spelling; lookup is case-insensitive.
- Four spaces form one indentation level. Tabs, braces as block delimiters,
  semicolons and explicit block-closing keywords are not part of the language.

## 2. The small punctuation set

| Form | One meaning |
| --- | --- |
| `#name` | Declare or reference a variable |
| `## comment` | Comment, including an inline trailing comment |
| `@name` | Function declaration/call in SCRIPTS; component reference in KIT/PAGES |
| `name = value` | Assignment |
| `[a, b]` | List literal; `#items[0]` is indexed access |
| `(expression)` | Expression grouping only |
| Quotes | Optional for ordinary text; required when escaping or preserving special text |

A single hash is never a comment marker. Two hashes begin a comment outside a
quoted string. The meaning of `@` is determined by its containing section,
not by capitalization.

## 3. Values and expressions

- Values are dynamically typed; reassignment may change a variable's type.
- `true`, `false` and `null` are typed literals.
- Numbers remain numeric. Ordinary unquoted words and phrases are text.
- Supported expression operators are arithmetic `+`, `-`, `*`, `/`, `%`,
  comparisons, and boolean `and`, `or`, `not`.
- A variable reference begins with `#`. Dotted paths and bracket indexing
  are data access, not arbitrary host-language reflection.
- Indexing is bounds-checked.
- `const #name = value` is the immutable-binding spelling in the language
  direction; it must be rejected by a parser/runtime that does not yet
  implement immutable declarations rather than treated as an ordinary name.

## 4. Canonical complete-file shape

```cudl
GUIDE
    name = HelloApp
    version = 1.0
    targets = [web, android]
    routing = automatic

KIT
    theme = warm
        background = #F5F0E8
        accent = #B98B68

PAGES
    page Home
        center
            title Welcome
            button Get Started
                on click @start

SCRIPTS
    #started = false

    @start
        #started = true

TIME
    timeline Intro
        duration = 2
```

This is a shape example, not a promise that every shown component, event or
TIME construct is currently executable by every adapter. Consult the
implementation-status table in `five-part-language-spec.md`.

## 5. Functions and component references

```cudl
SCRIPTS
    @greet #person
        print Hello #person

    @add #left #right
        return #left + #right

    #total = @add 10 20

PAGES
    page Home
        @WelcomeCard
            heading = Welcome
```

A declaration owns its indented body. A call does not. In design sections,
`@Name` denotes a reusable component; in SCRIPTS it denotes a function.
Parameters and variable references use the hash prefix.

## 6. Maps, native blocks and unsupported syntax

Square-bracket lists and indexing are part of the syntax direction. Inline map
literals, native-language execution, loops, conditionals, asynchronous
functions, and arbitrary host reflection must not be assumed available merely
because an example or proposal mentions them. They require parser, semantic,
runtime/adapter and conformance-test evidence before being advertised as
implemented.

Native blocks, when recognized, are opaque source for a compatible host
adapter. CUDL does not execute downloaded or embedded native code itself.
JSON is structured data, never executable code.

## 7. Conformance rules

Every grammar change must update this contract, `grammar.md`, the five-part
specification, at least one canonical example, parser/runtime tests and the
README syntax sample in the same reviewable change. No second syntax dialect
may be introduced to avoid resolving an ambiguity.

The implementation must produce a clear diagnostic for unsupported or
ambiguous constructs. It must not silently reinterpret a variable, comment,
function or component reference.
