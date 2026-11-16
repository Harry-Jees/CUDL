# Component declarations and registry

CUDL components are declared in `KIT` modules and referenced from pages or
other modules. A declaration is a named reusable design unit:

```cudl
component ProfileCard
    property name
    property photo
    property subtitle optional

    card
        image photo
        heading name
        text subtitle
```

A page can reference a component using its concise component-reference form:

```cudl
import {ProfileCard as Card} from "KIT/profile"

page Home
    content
        @Card
            name = Harry
            photo = profile.png
```

## Current semantic pass

`build_component_registry(module_graph)` collects top-level component
declarations, checks duplicate/invalid declarations, verifies named imports
against component declarations in their target modules, and checks component
references against local declarations and imported names.

CUDL identifiers are matched case-insensitively. Import aliases are the names
visible to the importing module. At-prefixed declarations and calls inside native
`script` blocks are functions, not design component references.

The registry validates required and optional component properties, unknown
properties, duplicate assignments, and safe value syntax. It does not execute
component bodies or native scripts.

Diagnostic codes:

- `CUDL3001`: invalid or missing component name.
- `CUDL3002`: duplicate component declaration in one module.
- `CUDL3003`: named import does not match a component in the target module.
- `CUDL3004`: component reference is not locally declared or imported.
- `CUDL3005`: invalid property name.
- `CUDL3006`: duplicate property declaration.
- `CUDL3007`: malformed property declaration.
- `CUDL3008`: unknown instance property.
- `CUDL3009`: duplicate instance assignment.
- `CUDL3010`: missing required property.
- `CUDL3011`: invalid hash-prefixed property path.

## Dynamic values

Ordinary unquoted values are text. Numbers, booleans, and null retain their
natural values. Prefix a variable path with `#` to resolve it from the host's
explicit data mapping:

```cudl
@ProfileCard
    name = #user.profile.display_name
    photo = profile.png
    active = true
    subtitle = null
```

Safe indexed paths are supported:

```cudl
@ProfileCard
    name = #users[0].name
    photo = #assets[profile]
```

The expression parser does not execute calls or arbitrary source. The Python reference runtime separately supports a bounded set of arithmetic, comparison, and boolean expressions plus native @-functions. A malformed
hash path produces a diagnostic. The React adapter resolves hash paths only
against the explicit data object passed by the host; paths are read through
own properties and must resolve to a primitive value.

Dynamic typing is the language direction: no explicit type declaration is
required, and values are not locked to one declared type. The native runtime
that will execute variable assignments and functions is still a future
milestone.
