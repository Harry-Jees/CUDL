# CUDL project imports and module resolution

CUDL imports are resolved by the core project layer, not by individual UI
adapters. This keeps dependency discovery consistent across React and future
host integrations.

## Named imports

    import {PrimaryButton, Navbar} from "KIT/components"
    import {login as sign_in} from "SCRIPTS/auth"

A path may be relative to the importing file:

    import {format_date} from "../SCRIPTS/dates"

Section names KIT, PAGES, SCRIPTS, and GUIDE resolve from the project root.

## Resolution rules (v1)

For a path without an extension, the resolver checks, in order:

1. path.cudl
2. path/module.cudl
3. path/index.cudl

A path ending in .cudl is checked exactly. Filesystem paths are case-sensitive.

## Project API

resolve_project(sources, entry) accepts a mapping of project-relative POSIX
paths to source text and returns a deterministic ModuleGraph. The graph
includes reachable modules, dependency-first order, resolved import bindings
and structured diagnostics.

The resolver detects missing entry files, malformed imports, unresolved paths
and circular dependencies. It does not yet validate exports, load third-party
packages, execute code, or infer runtime availability.
