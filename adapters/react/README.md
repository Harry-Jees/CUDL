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
- Unknown elements are preserved as marked wrapper elements.
- Source document and line metadata are retained where available.

## Not implemented yet

- CUDL expressions, properties and data binding.
- Button actions and event handlers.
- Import and module resolution.
- Themes, responsive layout engine and motion.
- Automatic conversion from `.cudl` files to IR during a Vite build.

Those features will be added through the core semantic model and later adapter
milestones. This package is an early renderer, not a production-ready release.
