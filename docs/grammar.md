# CUDL syntax — beginner-first draft

This is the canonical syntax direction for CUDL. It favors readable words,
indentation, and a small number of symbols. The parser and runtime are still
being built in stages; syntax shown as planned is not a claim of execution support.

## 1. Blocks and indentation

- Four spaces represent one indentation level.
- Indentation defines every native CUDL block.
- Tabs, braces, block brackets, colons, and semicolons are not required.
- Blank lines are ignored.
- Keywords and CUDL identifiers are case-insensitive.
- A nested block is indented exactly one level beneath its parent.

```cudl
page Home
    header
        title Welcome to CUDL

    content
        text My first CUDL application
        button Get Started
```

Ordinary text values do not need quotes. Quotes remain available for strings
that need explicit escaping or unambiguous special characters.

## 2. Variables and dynamic values

A single hash introduces a variable declaration or reference:

```cudl
#name = Harry
#age = 21
#active = true

print #name
```

- Variables are dynamically typed.
- Values determine their type; explicit type declarations are not required.
- A variable may be reassigned to a value of another type.
- `true`, `false`, and `null` are typed values.
- `const` may be used for a value that must not be reassigned.
- A hash-prefixed path is the only canonical way to request variable lookup.

```cudl
#users = #data.users
#first = #users[0]
#displayName = #users[0].profile[name]
```

Indexing uses square brackets. Numeric indexes address sequences; bare names
inside brackets are mapping keys. Quoted keys are available for keys containing
spaces or punctuation. Simple lists and mappings can also be written without
quoting ordinary words:

```cudl
#people = [Harry, Ada, Lin]
#profile = {name: Harry, age: 21}
#first = #people[0]
#person = #profile[name]
```

The first runtime supports bounded list and mapping literals, safe indexing,
and primitive values. It does not yet provide arbitrary object construction.

## 3. Comments

Double hash starts a comment:

```cudl
## This is a comment
#name = Harry ## This is an inline comment
```

A single hash is reserved for variables and must not be treated as a comment.

## 4. Functions

An at-prefixed name declares a native CUDL function. Its parameters are hash
variables. The function body is an indentation block; no `def`, colon, or
parentheses are required.

```cudl
script
    @greet #person
        print Hello #person

    @greet Harry
```

Function calls use `@` too. Indentation distinguishes the two: a function
declaration has an indented body; a call has no child block. Within a `script`
block, `@name` is a function declaration when it owns a body and a function
call when it does not. In page/design blocks, `@Name` remains a reusable
component reference.

```cudl
script
    @add #a #b
        return #a + #b

    #total = @add 10 20
```

The reference runtime now executes dynamic assignments, type-changing
reassignment, hash-path indexing, safe arithmetic/comparison/boolean
expressions, function calls, return values, and text interpolation. Function
parameters and variables are dynamically typed. For example:

\x60\x60\x60cudl
script
    #age = 21
    #age = Harry

    @greet #person
        print Hello #person

    @add #left #right
        return #left + #right

    @greet #age
    #total = @add 10 20
    print #total
\x60\x60\x60

Use `const #name = value` when reassignment should be rejected. The runtime
uses a bounded, explicit expression evaluator; it does not use Python eval/exec,
load host modules, or execute `js`/`python` blocks. The first runtime release
does not yet implement loops, conditional blocks, asynchronous functions, or
host-language execution.

## 5. Design components

Components keep the concise at-reference form in design blocks:

```cudl
component ProfileCard
    property name
    property photo
    property subtitle optional

    card
        image photo
        heading name
        text subtitle

page Home
    @ProfileCard
        name = Harry
        photo = profile.png
        subtitle = Student Developer
```

## 6. External languages

External-language blocks keep their own native syntax. CUDL does not rewrite
JavaScript, Python, Java, C, or another host language.

```cudl
js
    const version = 1
    console.log(version)

python
    print("Hello from Python")
```

The host project and installed adapters determine which external runtimes and
dependencies are actually available.

## 7. Punctuation

- `#` — variable declaration and reference.
- `##` — comment.
- `@` — native function declaration/call in scripts; component reference in design.
- `[]` — indexing only in native CUDL syntax.
- `.` — property access in a hash-prefixed path.
- `=` — assignment.
- `->` — reserved for concise navigation/action declarations.
- Quotes — optional for ordinary text, available for escaped or special strings.

## 8. Application configuration and platform routing

GUIDE and KIT configuration values always use an explicit equals sign.
Structural declarations such as `component Navigation` and `page Home`
remain declarations, not assignments.

```cudl
GUIDE
    name = WelcomeApp
    version = 1.0
    platforms = [android, ios, web]
    routing = device

KIT
    theme = light-brown
        background = #F5F0E8
        foreground = #292521
        accent = #B98B68
        radius = 18
```

The five top-level sections may appear in any order, but each may appear only
once. Built-in keywords, section names and identifier lookup are case-insensitive. The compiler
normalizes section order in serialized application IR.

Platform routing supports both global GUIDE routes and component-local KIT
routes. A route may match a platform, device class, minimum/maximum width,
input mode, required capabilities and priority. Component-local rules take
precedence over global rules; a default route is the fallback.

```cudl
GUIDE
    route = android
        component = Navigation
        device = phone
        use = AndroidPhoneNavigation
    route = default
        component = Navigation
        use = ResponsiveNavigation
```

PICKER selects declared native script blocks for an explicit host profile.
React selects JavaScript/TypeScript, Python selects Python, Android selects
Kotlin/Java, and iOS selects Swift. Portable CUDL script blocks and JSON data
are retained. Native code is preserved as opaque source; CUDL does not execute
it or install dependencies.

Run a file with `cudl run app.cudl` to execute its supported native `script`
blocks. Use `cudl check app.cudl` to validate indentation and syntax without
running it.

The goal is not to remove every symbol. Each symbol should have one obvious
purpose and should not be required when indentation or plain words are clearer.
