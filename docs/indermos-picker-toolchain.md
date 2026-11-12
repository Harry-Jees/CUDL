# INDERMOS and PICKER toolchain specification

Status: architecture specification only. Neither system is implemented by this document. The
interfaces and behaviors below are the proposed contract; implementation must be staged behind
tests and capability checks.

## Purpose

CUDL is embedded in an existing application. It must understand the host stack, resolve the
project's declared dependencies, and select only the code and components that belong in that
host's output. Two cooperating toolchain services provide those responsibilities:

- **INDERMOS** — Intelligent Dependency Resolver and Module Ordering System. The requested
  spelling is INDERMOS (I-N-D-E-R-M-O-S); "Intermos" is an acceptable spoken shorthand.
- **PICKER** — Platform Intelligent CUDL Kit Exchange Router. Its host-language package/API
  namespace is `cudl_picker`.

They are services in the CUDL toolchain, not new source-language keywords and not additional
peer sections alongside GUIDE, KIT, PAGES, SCRIPTS and TIME.

## Pipeline placement

```text
CUDL source + host project metadata
              |
           Lexer
              |
           Parser
              |
     Typed source / application IR
              |
    +---------+----------+
    |                    |
 INDERMOS              PICKER
 stack + deps          target selection
 module graph          script/component filter
 diagnostics           package routing
    |                    |
    +----------+---------+
               |
      Host adapter / packager
               |
       Host build and runtime
```

INDERMOS supplies the resolved project graph and environment capabilities to PICKER. PICKER
must not independently install packages or reinterpret unresolved imports. Both consume the
same canonical IR and source-location metadata.

## INDERMOS responsibilities

### 1. Stack identification

Identify the host stack using explicit GUIDE targets first, then project manifests and adapter
configuration. Useful evidence includes `package.json`, Python project metadata, Maven/Gradle
files, Cargo manifests, CMake files and platform project files.

Detection must return evidence and confidence, not silently guess. If evidence conflicts or is
insufficient, report an actionable diagnostic and ask the host integration to select a target.
Never inspect secrets or execute project code to identify a stack.

The result is a structured HostProfile containing at least:

- primary language and supported language versions;
- framework/runtime and version, when detected;
- operating system and target platform(s);
- package manager and lockfile;
- installed adapter capabilities;
- supported native block languages;
- project root and entry module.

Explicit user/host configuration always overrides inferred metadata.

### 2. Dependency and module resolution

INDERMOS extends the existing CUDL module graph. It should:

1. Parse CUDL imports and GUIDE dependency declarations.
2. Resolve local CUDL modules deterministically.
3. Resolve declared external packages against the selected host ecosystem.
4. Check version ranges, platform markers, optional dependencies and adapter compatibility.
5. Detect missing, incompatible, duplicate-conflicting and cyclic dependencies.
6. Produce a stable dependency-first order, preserving deterministic tie-breaking.
7. Report the exact source declaration and the manifest/constraint that caused a conflict.

Resolution is not installation. The default operation is read-only and offline-capable. Any
package download, installation, lockfile update or build-script execution requires an explicit
host permission and must use the host's configured package manager. Never run arbitrary install
scripts as a side effect of parsing or checking CUDL.

### 3. Diagnostics and safe repair

Diagnostics use stable codes, severity, source spans, affected dependency/module, explanation,
and a suggested next action. Where possible, include a machine-readable fix proposal.

Safe automatic fixes may include deterministic import ordering, correcting an unambiguous
local module path, or selecting an already-installed compatible adapter. Changes to version
constraints, package installation, deletion, network access, or source semantics require
explicit approval. Always support a no-write dry run and show the proposed diff before mutation.

### 4. Proposed API

The first implementation should expose a pure planning API before any package-manager actions:

- `identify_stack(project_snapshot, explicit_target?) -> HostProfile`
- `resolve_dependencies(project_snapshot, host_profile) -> ResolutionPlan`
- `order_modules(module_graph) -> OrderedModuleGraph`
- `diagnose(plan) -> Diagnostic[]`
- `propose_fixes(plan) -> FixProposal[]`

A ProjectSnapshot is a bounded collection of project-relative paths and metadata, not an
unrestricted filesystem handle. ResolutionPlan must be serializable and deterministic.

## PICKER responsibilities

### 1. Host-aware filtering

PICKER reads the HostProfile and resolved IR, then selects compatible content:

- CUDL-native script blocks are host-neutral and are lowered by the selected runtime/adapter.
- A `python` block is selected only for a Python host or an explicitly configured Python
  bridge.
- A `javascript` / `typescript` block is selected only for a compatible JavaScript host.
- A `java` block is selected only for a compatible JVM target.
- A `cpp` / `c` block is selected only when the matching native toolchain/bridge is configured.
- JSON is treated as structured data, validated and serialized; it is not executed as a script.
- Unknown or unsupported language blocks are preserved in source/IR for tooling but excluded
  from the host package with a clear diagnostic. They must never be silently executed.

A project may contain several native-language blocks. The selected host package includes only
the blocks whose declared target matches its HostProfile and whose required capabilities are
available. Explicit multi-target builds may produce separate packages from the same source.

### 2. KIT and component exchange

PICKER selects reusable KIT components according to the host adapter's declared capabilities.
It maps portable component contracts to native representations without changing their public
properties or behavior. A component with no compatible mapping produces a diagnostic; it must
not be replaced by an unrelated component or dropped silently.

### 3. Portable package output

The proposed `cudl_picker` package emits a native-convertible bundle containing:

- selected component and script payloads;
- a manifest describing target stack, language, versions and required capabilities;
- dependency references supplied by INDERMOS;
- stable module order;
- source maps and original source locations;
- content hashes for integrity and reproducibility;
- excluded-block report with reasons;
- adapter/IR compatibility version.

The bundle format should be deterministic and versioned. Host adapters may convert it into
their native build inputs; PICKER itself does not pretend to compile Python, JavaScript, Java or
C++.

### 4. Proposed API

- `select_targets(ir, host_profile) -> SelectionPlan`
- `filter_scripts(ir, selection_plan) -> SelectedScripts`
- `map_components(ir, adapter_capabilities) -> ComponentPlan`
- `package(selection_plan, resolution_plan) -> PortableBundle`

The CLI may later expose `cudl inspect-stack`, `cudl resolve --dry-run`,
`cudl picker --target <host>` and `cudl bundle --target <host>`. These commands are proposals,
not current CLI features.

## Native blocks and JSON contract

SCRIPTS must distinguish CUDL-native code, host-language source and structured data. Each block
needs an explicit language/kind, target constraint, source span and optional dependency
declarations. The parser preserves opaque native source without parsing it as CUDL expressions.

For example, a future source form may look like:

```cudl
SCRIPTS
    #title = Hello

    python
        print("Python host only")

    javascript
        console.log("JavaScript host only")

    cpp
        #include <iostream>
        std::cout << "C++ host only";

    json
        {
            "title": "Hello",
            "enabled": true
        }
```

This example illustrates the target-selection contract; native execution and JSON block syntax
must not be advertised as implemented until parser, IR, adapter and tests support them. JSON
must be parsed as data (with duplicate-key and size limits), never executed.

## Safety, reproducibility and error handling

- Parsing, stack identification, dependency planning and target selection are non-executing.
- No implicit network access, package installation, arbitrary shell commands or build scripts.
- Host adapters declare capabilities; absence means unsupported, not best-effort execution.
- Native blocks are isolated by language and target; no cross-language execution by accidental
  fall-through.
- Resolver and picker outputs are deterministic for the same source, manifests and profile.
- All errors include stable codes, source locations and actionable suggestions.
- Fixes that mutate files or environments require explicit approval and a preview.
- Build output records selected and excluded content for auditability.

## Implementation sequence

1. **Contracts and diagnostics:** typed HostProfile, dependency constraints, SelectionPlan and
   stable diagnostic codes; keep the current module resolver API compatible.
2. **INDERMOS read-only MVP:** explicit target + manifest detection, deterministic CUDL module
   graph ordering, missing-module and dependency diagnostics. No installation.
3. **PICKER IR MVP:** preserve language-tagged script blocks and select CUDL-native blocks plus
   one explicitly configured host language; produce an exclusion report.
4. **First real adapter:** integrate selection with the React/JavaScript adapter and prove that
   Python/C++ blocks are excluded from a JavaScript package.
5. **Additional hosts:** Python, JVM and native C/C++ adapters, each with isolated fixtures and
   capability tests.
6. **Opt-in repair and package-manager bridges:** only after dry-run plans, lockfile behavior,
   approvals and reproducibility are tested.

## Current implementation boundary

The repository currently has a basic local CUDL module resolver and dependency-first graph
ordering. It does not yet detect complete host stacks, resolve third-party packages, execute
host-language blocks, filter scripts by target, or produce PICKER bundles. The current runtime
does not implement a standalone garbage collector or full general-purpose control flow.
Maintain this distinction in README, CLI help and release notes until each capability is
implemented and verified.


## Initial implementation status

The Python core now exposes `analyze_project(files, entry=None)` from
`cudl.indermos`. It inspects caller-supplied manifest text without filesystem
access or execution. Initial recognition includes npm/package.json, Python
requirements and pyproject manifests, Cargo, Go modules, Maven, Gradle/Android,
Swift Package Manager, .NET project files and CMake. It extracts a bounded set
of declared dependency names and versions, reports conflicting declarations,
and can include the existing local CUDL module graph.

This is static manifest analysis, not full dependency resolution. It does not
query registries, calculate transitive dependency graphs, select package
versions, install packages, execute build scripts, inspect the local machine,
or verify that a compiler/runtime is installed. Those operations need explicit
host tooling and approval. Unsupported manifests are not guessed.
