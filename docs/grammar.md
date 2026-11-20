# CUDL syntax — beginner-first guide

The normative v1 rules live in [CANONICAL-SYNTAX.md](CANONICAL-SYNTAX.md).
This guide explains the same syntax with practical examples. A documented
design direction is not automatically a claim that every adapter executes it.

## 1. Blocks and indentation

- Four spaces represent one indentation level.
- Indentation defines every block and closes it; no braces, semicolons or
  explicit closing tags are needed.
- Blank lines are ignored.
- Built-in keywords, section names and visual tag names are case-insensitive.
- User-defined names retain their spelling and are looked up case-insensitively.
- The five peer sections may appear in any order, at most once each.
- A standalone fragment is valid only when the host explicitly requests it.

~~~cudl
GUIDE
    name = HelloApp

PAGES
    <page Home>
        <column>
            <title Welcome to CUDL>
            <text My first CUDL application>
            <button Get Started>
~~~

## 2. Visual tags

Use angle-bracket tags only for visual structure in KIT and PAGES:

~~~cudl
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

A tag is written as `<name>` or `<name optional text>`. The optional text
is its value. Indentation nests visual children; do not write a closing tag.
Put properties on indented assignment lines. A custom tag is declared with
`component Name` in KIT and used as `<Name>`.

## 3. Assignments and dynamic values

Use one assignment form for configuration, theme tokens, component properties
and variables:

~~~cudl
GUIDE
    name = HelloApp
    targets = web, android
    background = "#F5F0E8"

SCRIPTS
    #age = 21
    #age = Harry
    #first = #people[0]
~~~

Values are dynamically typed; a variable can be reassigned to a different
type. Numbers, booleans and null retain their types. Ordinary words and
phrases are text. The `#people` collection in this example is supplied by
the host; CUDL reads it through the hash-prefixed path.

Square brackets are reserved for indexing, not collection literals. Indexing
is bounds-checked and does not expose arbitrary host reflection. Use quotes
when text contains syntax characters that must remain literal.

## 4. Comments

Double hash starts a comment. A single hash always belongs to a variable or
data path.

~~~cudl
## Full-line comment
#name = Harry ## Inline comment
~~~

## 5. Functions

An at-prefixed name declares or calls a CUDL function. Parameters are
hash-prefixed variables. Function calls do not use parentheses or colons.

~~~cudl
SCRIPTS
    @greet #person
        print Hello #person

    @add #left #right
        return #left + #right

    #total = @add 10 20
    @greet Harry
~~~

The reference runtime supports dynamic assignments, safe expressions,
hash-path indexing, function calls, returns and text interpolation. It does
not execute arbitrary host-language blocks or support general loop and
conditional statement blocks.

## 6. GUIDE

GUIDE is the application manifest: identity, target platforms, host
requirements and global routing policy. It does not contain page markup or
business logic.

~~~cudl
GUIDE
    name = HelloApp
    version = 1.0
    targets = android, ios, web, windows, macos, linux
    routing = automatic
    default-device = responsive
~~~

A target declares intent; it does not guarantee that an adapter is installed.
Never put secrets in source-controlled GUIDE data.

## 7. KIT

KIT defines reusable components, themes, design tokens, styles and component
contracts. Configuration uses assignments; visual component bodies use tags.

~~~cudl
KIT
    theme = light-brown
        background = "#F5F0E8"
        foreground = "#292521"
        accent = "#B98B68"
        radius = 18

    component WelcomeCard
        property heading
        property subtitle optional
        <column>
            <title heading>
            <text subtitle>
~~~

Component routing remains a separate capability: the adapter selects the
most specific compatible platform/device route, then the declared default.
A missing compatible route must produce a diagnostic rather than silently
selecting an unrelated component.

## 8. PAGES

PAGES describes screens, visual hierarchy, layout and interaction declarations.
Business logic belongs in SCRIPTS.

~~~cudl
PAGES
    <page Home>
        <column>
            <WelcomeCard>
                heading = Welcome, Harry
                subtitle = A little room to breathe
            <button Get Started>
                on click @start
~~~

React event dispatch and responsive rendering remain adapter capabilities;
this source shape alone does not claim they are implemented.

## 9. SCRIPTS and native language blocks

SCRIPTS owns variables, functions, calculations and application logic.

~~~cudl
SCRIPTS
    #started = false

    @start
        #started = true

    python
        print("Python host only")

    javascript
        console.log("JavaScript host only")
~~~

Native blocks preserve their source text for compatible host tooling. The
CUDL reference runtime does not execute Python, JavaScript or other native
code. Use indentation-based blocks rather than bracket-delimited code.

## 10. TIME

TIME describes timelines, scenes, tracks, keyframes, playback and temporal
events. Its numeric evaluator is experimental; host playback adapters and
event dispatch remain staged. See the five-part language specification.

## 11. Punctuation

- `#` — variable declaration and reference.
- `##` — comment.
- `@` — function declaration or call.
- `<tag>` — visual layout/design node in KIT or PAGES.
- `[]` — indexing only.
- `=` — assignment.
- Quotes — optional for ordinary text, required when preserving special text.

## 12. Bounded parsing

The reference lexer and parser bound source size, line length, indentation
depth, node count and token count. Exceeding a limit produces a location-aware
error. Split large applications into smaller modules.


## 13. Deterministic syntax diagnostics

The parser reports unsupported tag forms as CUDL1009 and malformed
at-prefixed function statements as CUDL1010.

~~~cudl
PAGES
    <button Start color=red> ## invalid: inline attributes are not v1 syntax

SCRIPTS
    @start#person ## invalid: separate the function name and arguments
    @start!       ## invalid: function names cannot have punctuation suffixes
~~~

Use a tag's optional text for its value and put component properties on
indented name = value lines. Quote text when it must preserve characters
that would otherwise look like syntax. A function statement is @name
with optional whitespace-separated arguments; function calls do not use
parentheses.
