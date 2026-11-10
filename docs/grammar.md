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
spaces or punctuation.

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

    greet Harry
```

Function calls use the function name without `@`. This avoids confusing a
function declaration with a call and keeps `@` declarations visually distinct.
Within a `script` block, `@name` means a function declaration. In page/design
blocks, `@Name` remains a reusable component reference.

```cudl
script
    @add #a #b
        return #a + #b

    #total = add 10 20
```

The parser preserves function declarations and script blocks. Function
execution, arithmetic evaluation, scope, and runtime type behavior are future
interpreter milestones and are not yet executed by the current prototype.

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
- `@` — native function declaration in scripts; component reference in design.
- `[]` — indexing only in native CUDL syntax.
- `.` — property access in a hash-prefixed path.
- `=` — assignment.
- `->` — reserved for concise navigation/action declarations.
- Quotes — optional for ordinary text, available for escaped or special strings.

The goal is not to remove every symbol. Each symbol should have one obvious
purpose and should not be required when indentation or plain words are clearer.
