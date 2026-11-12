# CUDL syntax — beginner-first draft

This document defines the current syntax direction. Examples marked as planned
are specifications, not claims that every adapter already executes them.

## 1. Blocks, names and indentation

- Four spaces represent one indentation level.
- Indentation defines native CUDL blocks.
- Tabs, braces, semicolons and block-closing keywords are not required.
- Blank lines are ignored.
- Built-in keywords and the five section names are case-insensitive.
- User-defined names preserve their written spelling; name lookup is
  case-insensitive for portability.
- A nested block is indented exactly one level beneath its parent.
- The five peer sections may appear in any order, at most once each.

```cudl
GUIDE
    name = HelloApp

PAGES
    page Home
        header
            title Welcome to CUDL
        content
            text My first CUDL application
            button Get Started
```

Ordinary text values do not need quotes. Quotes remain available when escaping
or unambiguous special characters are needed.

## 2. Assignments and values

Use one consistent assignment form in configuration, themes, component
properties and variables:

```cudl
name = HelloApp
background = #F5F0E8
radius = 18
#active = true
```

The equals sign separates a name from its value. Structural declarations such
as `page Home`, `component Card` and `route = android` introduce blocks;
their nested properties use assignments.

Values are dynamically typed. Numbers, booleans and null retain their types.
Ordinary words and phrases are text. Lists use square brackets; mappings use
curly braces only as inline values, not as block delimiters.

```cudl
#people = [Harry, Ada, Lin]
#profile = {name: Harry, age: 21}
#first = #people[0]
#person = #profile[name]
#displayName = #data.users[0].profile[name]
```

Variables are dynamically typed; a later assignment may change the value's
type. A hash-prefixed path is the explicit way to read a variable or host-data
path. Indexing is bounds-checked and does not expose arbitrary host reflection.

## 3. Comments

Double hash starts a comment. Single hash is reserved for variables.

```cudl
## Full-line comment
#name = Harry ## Inline comment
```

## 4. Functions

An at-prefixed name declares or calls a CUDL function. Parameters are
hash-prefixed variables. A declaration owns an indented body; a call does not.

```cudl
@greet #person
    print Hello #person

@add #left #right
    return #left + #right

#total = @add 10 20
@greet Harry
```

In design context, `@Name` references a reusable component. The parser
resolves the meaning from its containing section, not capitalization.

The reference runtime supports dynamic assignments, safe expressions,
hash-path indexing, function calls, returns and text interpolation. It does
not yet support loops, conditional blocks, asynchronous functions or arbitrary
host-language execution.

## 5. GUIDE

GUIDE is the small application manifest: identity, target platforms, runtime
requirements and global routing policy. It is not a general-purpose settings
drawer and does not contain visual styling or page logic.

```cudl
GUIDE
    name = HelloApp
    version = 1.0
    targets = [android, ios, web, windows, macos, linux]
    routing = automatic
    default-device = responsive
```

Use `targets` to declare intended build targets, not to claim that adapters
are installed. Dependency declarations and host-stack discovery are handled
by INDERMOS. Never put secrets in source-controlled GUIDE data.

## 6. KIT

KIT defines reusable components, themes, design tokens, styles and component
contracts. Every token and component property uses the same equals syntax.

```cudl
KIT
    theme = light-brown
        background = #F5F0E8
        foreground = #292521
        accent = #B98B68
        radius = 18

    component WelcomeCard
        property = heading
        property = subtitle
        card
            title heading
            text subtitle
```

### Component routing

A component may have multiple implementations. The adapter selects the most
specific compatible route for the current platform and device class, then
falls back to `default`.

```cudl
KIT
    component Navigation
        route = android
            device = phone
            use = AndroidPhoneNavigation

        route = android
            device = tablet
            use = AndroidTabletNavigation

        route = web
            use = WebNavigation

        route = default
            use = ResponsiveNavigation
```

Platform and device class are separate: an Android tablet is both
`platform = android` and `device = tablet`. Optional route constraints may
include `min-width`, `max-width`, `input`, `requires` and `priority`.
A route is only selected when the host adapter reports the required
capabilities. No compatible route and no default must produce a diagnostic;
CUDL must not silently substitute an unrelated component.

GUIDE's `routing = automatic` enables host-context selection. Component routes
provide explicit overrides. A host may also supply a global responsive
fallback; component-specific matches take precedence.

## 7. PAGES

PAGES describes screens, layout and interaction declarations. Business logic
belongs in SCRIPTS.

```cudl
PAGES
    page Home
        background = light-brown.background
        center
            @WelcomeCard
                heading = Welcome, Harry
                subtitle = A little room to breathe
            button Get Started
                on click @start
```

## 8. SCRIPTS and native language blocks

SCRIPTS owns variables, functions, calculations, event handlers and host
capability calls.

```cudl
SCRIPTS
    #started = false

    @start
        #started = true
        print Application started

    python
        print("Python host only")

    javascript
        console.log("JavaScript host only")
```

Native blocks preserve their original language source. PICKER selects blocks
compatible with the host target; CUDL does not execute arbitrary native code.
JSON blocks, when enabled, are structured data and are never executable.

## 9. TIME

TIME describes timelines, scenes, tracks, keyframes, playback and temporal
events. Its numeric evaluator is experimental; host playback adapters and
event dispatch remain staged. See the five-part language specification for
timing and interpolation semantics.

## 10. Punctuation

- `#` — variable declaration and reference.
- `##` — comment.
- `@` — CUDL function declaration/call or component reference by context.
- `[]` — list literals and indexing.
- `=` — assignment.
- Quotes — optional for ordinary text, available for escaping and special text.

The goal is not to remove every symbol. Each symbol should have one obvious
purpose and should not be required when indentation or plain words are clearer.
