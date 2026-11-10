# @cudl/react

The first React host adapter for CUDL. It consumes the framework-neutral
CUDL Intermediate Representation (IR); it does not parse `.cudl` source
inside the browser.

## Integration boundary

The CUDL core parses source and serializes IR. A host build step or loader
provides that IR to React:

`.cudl source → CUDL core → CUDLIR JSON → @cudl/react → React elements`

The host React application retains control of routing, state, lifecycle,
bundling and application startup.

## Current support

- CUDL IR v1 input.
- Basic layout and text elements.
- Lazy image elements.
- Custom component registry.
- Local component definitions and primitive property injection.
- Unquoted text, numeric, boolean, and null values.
- Safe hash-prefixed data paths with dotted properties and array/mapping indexes.
- Runtime diagnostics for missing or unsupported property values.
- Unknown elements are preserved as marked wrapper elements.
- Source document and line metadata are retained where available.

## Not implemented yet

- Native CUDL function execution, computed expressions, and arithmetic.
- Button actions and event handlers.
- Defaults, slots, and cross-module component bundling.
- Import-driven runtime resolution.
- Themes, responsive layout engine and motion.
- Automatic conversion from `.cudl` files to IR during a Vite build.

This package is an early renderer, not a production-ready release.

## Runtime data binding

Pass the host's current data as the third argument to `renderCUDL`:

```tsx
const ui = renderCUDL(ir, components, {
  data: {
    user: {
      profile: { display_name: "Harry" },
      avatar: "/profile.png",
    },
    users: [{ name: "Ada" }, { name: "Harry" }],
  },
  onDiagnostic: (diagnostic) => console.warn(diagnostic),
});
```

CUDL uses a hash to make variable lookup explicit:

```cudl
@ProfileCard
    name = #user.profile.display_name
    photo = #user.avatar
    active = true
    subtitle = Student Developer
    firstUser = #users[0].name
```

Only a hash-prefixed path reads from the supplied data object. Ordinary values
such as `profile.png` or `Student Developer` remain text, even if they contain
dots or spaces. Indexed paths support non-negative array indexes and mapping
keys such as `#assets[profile]`.

Paths are read through own properties and must resolve to a string, number,
boolean, or null. Missing or invalid paths produce runtime diagnostics
(`CUDL4001` for component assignments, `CUDL4002` for unresolved element
values). The React host remains responsible for supplying current state; call
`renderCUDL` again when that data changes.

The adapter never evaluates source code or invokes functions from CUDL values.
