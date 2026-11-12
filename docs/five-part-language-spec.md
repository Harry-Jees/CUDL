# CUDL five-part language specification

Status: canonical design direction. The bundle validator, reference runtime,
component registry and experimental numeric TIME evaluator are implemented in
the development branch. Full platform adapters, native-block routing and
capability negotiation remain staged.

CUDL (Creative Unified Design Language) is an embeddable, indentation-first
language for application manifests, reusable UI, pages, program logic and
time-based experiences. The host application retains its runtime and lifecycle.

## 1. Five-part application file

A single `.cudl` file may contain all five peer sections. They may appear in
any order, each at most once. Empty sections may be omitted. The compiler
normalizes them to GUIDE, KIT, PAGES, SCRIPTS, TIME in the application IR.

| Section | Responsibility |
| --- | --- |
| GUIDE | Application identity, target platforms, host requirements and global routing policy |
| KIT | Reusable components, themes, tokens, styles, component contracts and component routes |
| PAGES | Screens, layout, content, navigation and interaction declarations |
| SCRIPTS | Variables, expressions, functions, application logic and native host-language blocks |
| TIME | Timelines, scenes, tracks, keyframes, playback and temporal events |

## 2. Source rules

- Four spaces are the canonical indentation unit.
- Indentation defines blocks; no mandatory braces, semicolons or block closers.
- Built-in keywords and section names are case-insensitive.
- User-defined names preserve spelling; symbol lookup is case-insensitive.
- Blank lines are insignificant.
- Ordinary text is unquoted unless escaping or special characters require quotes.
- `#` introduces variables/references; `##` introduces comments.
- Assignments consistently use `name = value`.
- Source locations are retained for diagnostics.

## 3. Values, variables and operators

```cudl
#name = Harry
#age = 21
#active = true
#items = [red, green, blue]
#profile = {name: Harry, age: 21}
#first = #items[0]
#displayName = #profile[name]
#total = 100 + 50
```

Values are dynamically typed. Reassignment may change type. `true`, `false`
and `null` are typed literals. `const #name = value` declares an immutable
binding. Indexing is bounds-checked and cannot access arbitrary host objects.

| Purpose | Operators |
| --- | --- |
| Assignment | `=` |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| Boolean | `and`, `or`, `not` |
| Grouping | `(` and `)` inside expressions |
| Access | `#path[index]`, dotted hash paths |

## 4. GUIDE — application manifest

GUIDE is intentionally small. It answers what the application is, which
platforms it targets, which host capabilities it expects and how default
routing behaves. It is not a generic settings section and contains no page
markup, design tokens or business logic.

```cudl
GUIDE
    name = HelloApp
    version = 1.0
    targets = [android, ios, web, windows, macos, linux]
    routing = automatic
    default-device = responsive
```

A declared target does not guarantee an adapter is installed. INDERMOS
inspects host manifests and resolves declared dependencies; it must not
silently install packages. Secrets never belong in source-controlled GUIDE.

## 5. KIT — design system and component routing

KIT owns themes, tokens, styles, reusable component contracts and their
platform-specific implementations.

```cudl
KIT
    theme = light-brown
        background = #F5F0E8
        foreground = #292521
        accent = #B98B68
        radius = 18

    component Navigation
        property active
        route = android
            device = phone
            use = AndroidPhoneNavigation
        route = android
            device = tablet
            use = AndroidTabletNavigation
        route = web
            use = WebNavigation
        route = default
            use = ResponsiveNavigation
```

A route names a platform; nested assignments constrain the match and identify
the implementation. Supported constraints are:

- `device`: `phone`, `tablet`, `desktop`, `tv`, `watch` or `any`.
- `min-width` and `max-width`: logical viewport width in CSS-independent
  logical pixels, supplied by the adapter.
- `input`: an input mode such as `touch`, `pointer`, `keyboard` or `stylus`.
- `requires`: comma-separated adapter capabilities.
- `priority`: non-negative tie-breaker after route specificity.
- `use`: required implementation component name.

A route is compatible only when platform, device, viewport, input and
capability constraints match. Selection order is: exact platform before
fallback; then exact device, bounded viewport/input constraints, capability
specificity and priority. Equal-specificity collisions must be diagnosed
rather than depending on source order. A `default` route is the fallback.
If no compatible route or fallback exists, the adapter reports an error.

GUIDE `routing = automatic` asks the host adapter to provide device context.
Component-specific KIT routes override global responsive defaults. Platform
and device class are independent: an Android tablet is platform Android and
device class tablet. A large phone does not become a desktop merely because
its viewport is wide.

The initial Python routing selector is a pure planning function: it selects a
declared implementation but does not import, execute or render it. Adapter
capability discovery and global route inheritance remain staged.

## 6. PAGES

PAGES declares screens, layout and interaction bindings.

```cudl
PAGES
    page Home
        background = light-brown.background
        center
            @WelcomeCard
                heading = Welcome, Harry
                subtitle = A little room to breathe
            button Get Started
                on click @start
```

## 7. SCRIPTS and native blocks

SCRIPTS owns dynamic values, functions, expressions, event handlers and
explicit host capability calls.

```cudl
SCRIPTS
    #started = false

    @start
        #started = true

    python
        print("Only selected for a configured Python host")

    javascript
        console.log("Only selected for a compatible JavaScript host")
```

Native source blocks are opaque to the CUDL runtime and must preserve their
source text. PICKER selects only blocks compatible with the selected host.
CUDL itself does not run arbitrary Python, JavaScript, Java, C or C++ code.
JSON blocks, when implemented, are validated structured data, never scripts.

## 8. TIME

TIME describes timelines, scenes, tracks, keyframes, easing, playback and
temporal events. The current experimental evaluator supports numeric tracks,
integer-microsecond evaluation and bounded playback modes. Host frame delivery,
event dispatch, colors, transforms, wall-clock scheduling and cross-platform
playback adapters remain staged.

## 9. Compiler and toolchain

```text
.cudl source
  -> lexer and parser
  -> semantic validation and application IR
  -> INDERMOS: host profile, dependencies and module order
  -> PICKER: target and component/script selection
  -> host adapter
  -> host application runtime
```

The parser and reference compiler are currently implemented in Python.
React integration is a TypeScript adapter. Keep the IR language-neutral so
future native implementations (potentially Rust) can be introduced without
changing the language or its source compatibility.

## 10. Implementation status

| Capability | Status |
| --- | --- |
| Five-section parsing, duplicate checks, case-insensitive section names | Implemented |
| Flexible section order with canonical IR serialization | Implemented in this milestone |
| Dynamic values, safe expressions and functions | Implemented subset |
| Component contracts and property validation | Implemented subset |
| Pure device-aware component route selection | Implemented in this milestone |
| GUIDE semantic validation and global routing inheritance | Planned |
| Full native-block preservation and PICKER filtering | Planned |
| INDERMOS host-stack and external package resolution | Planned |
| React events, responsive renderer and native adapters | Planned |
| Full TIME event and rendering adapters | Planned |

A capability is advertised as implemented only when source parsing, IR,
runtime/adapter, tests, documentation and CI agree.
