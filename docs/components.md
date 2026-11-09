# Component declarations and registry

CUDL components are declared in `KIT` modules and referenced from pages or
other modules. A declaration is a named reusable design unit:

```cudl
component ProfileCard
    card
        image photo
        heading name
        text description
```

A page can reference a component using its concise component-reference form:

```cudl
import {ProfileCard as Card} from "KIT/profile"

page Home
    content
        @Card
```

## Current semantic pass

`build_component_registry(module_graph)` collects top-level component
declarations, checks duplicate/invalid declarations, verifies named imports
against component declarations in their target modules, and checks component
references against local declarations and imported names.

CUDL identifiers are matched case-insensitively. Import aliases are the names
visible to the importing module.

This is intentionally a name-resolution milestone, not a component runtime.
Component properties, required/optional property checking, instance overrides,
slot composition, and React rendering of component definitions are not yet
implemented. The pass reports diagnostics without executing or transforming
component bodies.

Diagnostic codes:
- `CUDL3001`: invalid or missing component name.
- `CUDL3002`: duplicate component declaration in one module.
- `CUDL3003`: named import does not match a component in the target module.
- `CUDL3004`: component reference is not locally declared or imported.
