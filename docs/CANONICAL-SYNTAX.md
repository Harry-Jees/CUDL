# CUDL canonical syntax contract

Status: normative v1 syntax decisions. The parser, reference runtime, IR and
host adapters remain the source of truth for what is executable.

## 1. Application shape

- A complete application contains the peer sections `GUIDE`, `KIT`,
  `PAGES`, `SCRIPTS` and `TIME`. Sections may appear in any order and
  at most once each; empty sections may be omitted.
- An optional `bundle AppName` block may wrap all sections. If present, it
  must be the only root-level statement.
- A host may explicitly request a standalone fragment. A fragment is not
  silently treated as a complete application.
- Four spaces form one indentation level. Indentation closes every block.
  Braces, semicolons and explicit closing tags are not block syntax.
- Built-in keywords, section names and tag names are case-insensitive.
  User-defined names retain their written spelling; lookup is case-insensitive.

## 2. Named blocks and visual tags

Language, configuration, script and time structures use readable named blocks:

~~~cudl
SCRIPTS
    @greet #person
        print Hello #person
~~~

Only visual structure in `KIT` and `PAGES` uses angle-bracket tags:

~~~cudl
PAGES
    <page Home>
        <column>
            <title Welcome to CUDL>
            <button Get Started>
~~~

- A tag is `<name>` or `<name optional text>`, one opening tag per line.
- Indentation defines its children and closes its scope; no closing tag is written.
- The optional text becomes the node's value. Put component properties in
  indented `name = value` assignments, not inline attributes.
- Custom components are declared with `component Name` in `KIT` and used
  as `<Name>` in visual sections.
- Angle tags are not used for variables, functions, application sections,
  control flow or TIME declarations.

## 3. Values and the small punctuation set

| Form | Meaning |
| --- | --- |
| `#name` | Declare or reference a variable |
| `## comment` | Full-line or trailing comment |
| `@name` | Declare or call a function in `SCRIPTS` |
| `name = value` | Assignment |
| `#items[0]`, `#user[name]` | Bounds-checked data indexing |
| Quotes | Optional for ordinary text; use them to preserve special characters |

A single hash is never a comment marker. `@name` is reserved for functions;
custom visual components use angle tags, not `@Name`.

Values are dynamically typed. Reassignment may change a variable's type.
Numbers, `true`, `false` and `null` retain their types. Ordinary unquoted
words and phrases are text. Parentheses may group an expression; they are not
used for function calls or block delimiters.

Square brackets are reserved for indexing. List, tuple and mapping literals
are not part of CUDL v1. Collections are supplied by the host or an adapter
and read through hash-prefixed paths. Indexes must be non-negative integers,
valid property names or quoted string keys; missing paths and out-of-range
indexes fail safely.

The reference script runtime supports bounded arithmetic, comparisons and
boolean expressions. It supports `const #name = value` for an immutable
binding. Unsupported syntax must produce a clear diagnostic rather than be
silently reinterpreted.

## 4. Canonical complete-file shape

~~~cudl
bundle HelloApp
    GUIDE
        name = HelloApp
        version = 1.0
        targets = web, android
        routing = automatic

    KIT
        theme = warm
            background = "#F5F0E8"
            accent = "#B98B68"

        component WelcomeCard
            property heading
            <column>
                <title heading>

    PAGES
        <page Home>
            <column>
                <WelcomeCard>
                    heading = Welcome to CUDL
                <button Get Started>

    SCRIPTS
        #started = false

        @start
            #started = true

    TIME
        timeline Intro
            duration 2
~~~

This shape shows the language syntax. It does not promise that every component,
event or TIME construct is rendered by every adapter. Consult the
implementation-status table in `five-part-language-spec.md`.

## 5. Functions and custom components

~~~cudl
SCRIPTS
    @greet #person
        print Hello #person

    @add #left #right
        return #left + #right

    #total = @add 10 20
    @greet Harry

KIT
    component WelcomeCard
        property heading
        <column>
            <title heading>

PAGES
    <page Home>
        <WelcomeCard>
            heading = Welcome
~~~

A function declaration owns an indented body; a call does not. Function
parameters and variable references use the hash prefix. A custom component
declaration owns a KIT block; a matching visual tag instantiates it.

## 6. Native blocks and unsupported syntax

Native host-language source is written as an indented language block, for
example `python` or `javascript`. It is opaque to the CUDL runtime; CUDL
does not execute downloaded or embedded native code itself. A compatible host
adapter may preserve or select it.

List/map/tuple literals, inline tag attributes, explicit closing tags,
arbitrary host reflection, loops, conditional statement blocks, asynchronous
functions and native-code execution must not be assumed available merely
because another language or an earlier proposal supports them.

## 7. Conformance rules

Every grammar change updates this contract, `grammar.md`, the five-part
specification, at least one canonical example, parser/runtime tests and the
README syntax sample in the same reviewable change. No second syntax dialect
may be introduced to avoid resolving an ambiguity.

The implementation must produce a clear diagnostic for unsupported or
ambiguous constructs. It must not silently reinterpret a variable, comment,
function or visual component tag.
