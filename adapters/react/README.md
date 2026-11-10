# @cudl/react

The first React host adapter for CUDL. It consumes the framework-neutral
CUDL Intermediate Representation (IR); it does not parse `.cudl` source
inside the browser.

## Integration boundary

The CUDL core parses source and serializes IR. A host build step or loader
provides that IR to React:

` .cudl source → CUDL core → CUDLIR JSON → @cudl/react → React elements `

The host React application retains control of routing, state, lifecycle,
bundling and application startup.

## Current support

- CUDL IR v1 input.
- Basic layout and text elements.
- Lazy image elements.
- Custom component registry.
- Local component definitions and typed primitive property injection.
- Safe literal and dotted data-path binding through an explicit data object.
- Runtime diagnostics for missing or unsupported property values.
- Unknown elements are preserved as marked wrapper elements.
- Source document and line metadata are retained where available.

## Not implemented yet

- Computed expressions, operators, function calls, and automatic type coercion.
- Defaults, slots, and cross-module component bundling.
- Button actions and event handlers.
- Cross-module component bundling and import-driven runtime resolution.
- Themes, responsive layout engine and motion.
- Automatic conversion from `.cudl` files to IR during a Vite build.

These features will be added through the core semantic model and later adapter
milestones. This package is an early renderer, not a production-ready release.


## Safe runtime data binding

Pass an explicit data object as the third argument to `renderCUDL`:

```tsx
const ui = renderCUDL(ir, components, {
  data: {
    user: {
      profile: { display_name: "Harry" },
      avatar: "/profile.png",
    },
  },
  onDiagnostic: (diagnostic) => console.warn(diagnostic),
});
```

A component instance can bind its properties to that data:

```cudl
@ProfileCard
    name = user.profile.display_name
    photo = user.avatar
    active = true
```

Literal values and dotted paths are resolved without evaluating source code.
Paths are read only through own properties of the supplied data object and must
resolve to a string, number, boolean, or null. Missing paths and unsupported
values produce runtime diagnostics (`CUDL4001` for component assignments,
`CUDL4002` for unresolved element values). The React host remains responsible
for supplying current state; call `renderCUDL` again when that data changes.
