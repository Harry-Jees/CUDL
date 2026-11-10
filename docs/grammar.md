# CUDL grammar — initial draft

This document defines the deliberately small syntax accepted by the first
CUDL prototype. It is a starting contract, not the complete language spec.

## Layout and blocks

- A statement occupies one physical line.
- Four spaces represent one indentation level.
- Tabs are not valid indentation.
- A deeper indentation level must be exactly one level deeper than its parent.
- Blank lines and full-line comments beginning with `#` are ignored.
- Indentation determines block nesting; braces and semicolons are not required.

## Statements

A statement begins with a name-like word. The parser currently preserves the
first word as a normalized statement kind and the remaining text as its value.
This allows new design vocabulary and custom component names to be introduced
without changing the lexer.

Examples:

```cudl
page Home
    header
        title "Welcome"
    content
        text "Hello"
        button "Continue" -> next
```

## Lexical forms

- Identifiers: letters or underscore, followed by letters, digits, underscore,
  or hyphen.
- Strings: single- or double-quoted, with common backslash escapes.
- Numbers: numeric-leading literals; detailed numeric validation is deferred.
- Navigation arrow: `->`.
- Punctuation: `:`, `,`, `.`, `@`, brackets and parentheses.
- Operators: `=`, arithmetic and comparison characters.

## Reserved design vocabulary

Words such as `page`, `header`, `content`, `row`, `column`, `grid`,
`stack`, `button`, `text`, and `image` are not hard-reserved by the
lexer. Their meaning is assigned by semantic analysis and adapter capabilities.

## Planned syntax, not yet implemented

- Full expression grammar and precedence.
- Import declarations and module resolution.
- Component declarations and property schemas.
- Native `script[]` blocks and external language blocks.
- Typed diagnostics and recovery rules.
- Versioned project configuration and dependency manifests.
