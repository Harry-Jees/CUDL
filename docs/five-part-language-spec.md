# CUDL five-part language specification

Status: canonical design direction; the five-part bundle validator and initial numeric TIME evaluator are implemented on the development branch. Full TIME events, host rendering, capability negotiation and cross-platform adapters remain staged.

CUDL (Creative Unified Design Language) is an embeddable, indentation-first language for describing application configuration, reusable UI, pages, program logic, and time-based experiences. CUDL does not replace the host application's runtime or lifecycle.

## 1. Five-part bundle

A complete application is organized into five peer sections, in any source order:

| Section | Responsibility |
| --- | --- |
| GUIDE | Metadata, targets, dependencies, global settings, tokens and conventions |
| KIT | Reusable components, themes, styles, widgets and component contracts |
| PAGES | Screens, layout, content, navigation and interaction declarations |
| SCRIPTS | Variables, expressions, functions, application logic and host-language adapters |
| TIME | Timelines, scenes, tracks, keyframes, scheduling, playback and temporal events |

Each section appears at most once. Empty sections may be omitted. The compiler preserves source order in the source model and emits the serialized application IR in canonical GUIDE, KIT, PAGES, SCRIPTS, TIME order. Built-in section names and keywords are case-insensitive.

## 2. Source rules

- Four spaces are the canonical indentation unit; indentation defines blocks.
- No mandatory braces, semicolons, block-closing keywords or colons.
- Built-in keywords, section names and identifier lookup are case-insensitive.
- Blank lines are insignificant.
- Ordinary text can be unquoted; quotes remain available for escaping or special characters.
- `#` introduces variable declarations/references; `##` introduces comments.
- Source locations are preserved for diagnostics.

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
#discount = #total * 0.1
#final = #total - #discount
```

Values are dynamically typed; reassignment may change type. `true`, `false`, and `null` are typed literals. `const #name = value` declares a non-reassignable binding. Indexing must be bounds-checked and must not expose arbitrary host-object reflection.

Core operators:

| Purpose | Operators |
| --- | --- |
| Assignment | `=` |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| Boolean | `and`, `or`, `not` |
| Grouping | `(` and `)` inside expressions |
| Access | `#path[index]`, dotted hash paths |

Precedence: grouping/indexing; unary; multiplication/division/remainder; addition/subtraction; comparisons; `not`; `and`; `or`. Mixed-type operations require explicit documented conversion rules; unsupported combinations produce diagnostics.

## 4. Comments, functions and control flow

```cudl
## A comment
#name = Harry ## inline comment

@greet #person
    print Hello #person

@add #left #right
    return #left + #right

#sum = @add 20 22
@greet Harry
```

An at-prefixed declaration owns an indented body; a call does not. In design context, `@ComponentName` references a reusable component. The parser resolves this by grammar context, not capitalization guesses.

Intended control-flow syntax:

```cudl
if #score >= 50
    print Passed
else
    print Try again

for #item in #items
    print #item
```

Conditionals and loops are target language features, not claims about current runtime support. Add parser/runtime implementation and tests before advertising them as executable.

## 5. GUIDE

GUIDE declares project metadata and environment requirements, not page markup or executable logic.

```cudl
GUIDE
    name = WelcomeApp
    version = 1.0
    targets = [react, python]
    platforms = [android, ios, web, windows, macos, linux]
    routing = device
    time-unit = ms

    route = android
        component = Navigation
        device = phone
        use = AndroidPhoneNavigation

    route = default
        component = Navigation
        use = ResponsiveNavigation
```

A target does not guarantee adapter availability. Dependency resolution belongs to the host/build integration. Never place secrets in source-controlled configuration.

## 6. KIT

KIT defines reusable components, themes, tokens, styles and widgets.

```cudl
KIT
    theme = soft
        background = #F5F0E8
        foreground = #292521
        accent = #B98B68
        radius = 18

    component WelcomeCard
        property heading
        property subtitle optional
        card
            title heading
            text subtitle
```

Component properties are explicit inputs. Adapters map components to DOM nodes, native widgets or other host representations while preserving their contracts.

## 7. Platform and device routing

GUIDE may define a global route map, and individual KIT components may define
their own routes. Both use explicit equals assignments:

```cudl
GUIDE
    route = android
        component = Navigation
        device = phone
        use = AndroidPhoneNavigation
    route = default
        component = Navigation
        use = ResponsiveNavigation

KIT
    component Navigation
        route = android
            device = tablet
            use = AndroidTabletNavigation
        route = web
            use = WebNavigation
        route = default
            use = ResponsiveNavigation
```

Component-local rules take precedence over global rules for equal matches.
The initial route model supports platform, device class, width ranges, input
mode, required capabilities and explicit priority. A missing match returns a
diagnostic/result; it must not silently use an incompatible implementation.
The host adapter supplies the device context; CUDL core does not guess or
probe the device itself.

## 8. PICKER host selection

PICKER selects native script blocks for an explicitly declared host profile.
React selects JavaScript/TypeScript, Python selects Python, Android selects
Kotlin/Java, and iOS selects Swift. Portable CUDL script blocks and JSON data
are retained for every host. Excluded native blocks are reported. Selection
does not execute code, install dependencies, or guarantee that a runtime is
available. Native source-preserving extraction and full bundle packaging are
still staged.


## 9. PAGES

PAGES describes screens and layout trees. Business logic belongs in SCRIPTS.

```cudl
PAGES
    page Home
        background soft.background
        center
            @WelcomeCard
                heading = Welcome, Harry
                subtitle = A little room to breathe
            button Get Started
                on click @start
```

Layout and interaction nodes lower to typed IR nodes. Unsupported essential behavior must produce diagnostics, not disappear silently.


## 10. SCRIPTS

SCRIPTS owns variables, functions, calculations, event handlers and calls to host capabilities.

```cudl
SCRIPTS
    #started = false
    #price = 100
    #tax = 18
    #total = #price + #tax

    @start
        #started = true
        print Application started

    python
        print("Executed only by a configured Python host")
```

Host-language blocks preserve native syntax. CUDL does not execute arbitrary host code; the host adapter checks whether the language runtime and dependencies are available and permitted.

## 11. TIME — portable timeline system

TIME is a first-class peer of SCRIPTS, not a UI-only animation shortcut. It describes visual animation, scene sequencing, presentations, simulations, audio/visual experiences and other time-based behavior.

Core concepts:

- **Timeline:** named time domain and playback plan.
- **Scene:** named interval/phase; scenes may be sequential or overlap explicitly.
- **Track:** independently evaluated channel targeting a property, signal or adapter output.
- **Keyframe:** value at a timeline position.
- **Transition:** interpolation with duration and easing.
- **Event:** occurrence at a time, scene boundary, completion or signal.
- **Clock:** time source used to advance playback.
- **Binding:** typed reference between a track and its target.

### Proposed syntax

```cudl
TIME
    timeline WelcomeFlow
        duration 2400ms
        clock relative
        mode once

        scene Entrance
            at 0ms
            duration 1000ms

            track card.opacity
                from 0
                to 1
                duration 700ms
                ease out-cubic

            track greeting.opacity
                from 0
                to 1
                start 300ms
                duration 700ms

        scene Transition
            at 1000ms
            duration 1400ms

            track button.scale
                key 0ms 1
                key 400ms 1.05
                ease spring

        on complete
            @welcomeFinished
```

The from/to form is shorthand for two keyframes; explicit keyframes are canonical. Target paths resolve through typed bindings, never arbitrary reflection.

### Timing semantics

- Target units are `ms`, `s`, `min` and `frame`; the current experimental compiler accepts `ms`, `s` and `min` only. `frame` remains staged until explicit frame-rate support is implemented.
- Bare durations are invalid unless a default unit is declared.
- `at` is absolute on the parent timeline; `start` is an offset from scene start.
- Offsets are non-negative; timeline, scene and track durations must be positive. Contradictory keyframe order is an error.
- Frame timing requires an explicit frame rate; never assume 60 FPS.
- Internally normalize time to a monotonic integer timebase to avoid accumulated floating-point drift.
- Wall-clock scheduling is separate from animation playback and requires an explicit clock and permission.

### Playback and interpolation

Portable playback operations: play, pause, resume, stop, seek, cancel; modes: once, loop, ping-pong, hold. Define end-of-timeline, restart, reverse and seek behavior. Seeking must not replay side effects unless explicitly requested. Side-effect events declare whether they fire once, on each iteration or on completion.

Baseline easing: linear, in, out, in-out, in-cubic, out-cubic, in-out-cubic, step. Interpolation is type-aware: numbers, colors (documented color space), transforms and discrete values each have defined rules. Unsupported values require an adapter interpolator or a diagnostic.

### Events and synchronisation

Events may occur at positions, scene boundaries, completion, cancellation or named signals. Events call SCRIPTS only through declared bindings. Multiple timelines may share a clock or synchronise through named signals. External waits need cancellation and timeout policies. Pure notifications are distinct from side effects.

### Portable architecture

Compile TIME to a versioned Timeline IR containing stable IDs, normalized timestamps/timebase, typed target bindings, value types, keyframes, easing descriptors, playback/repeat policies, event references, source locations and capability requirements.

The current experimental evaluator handles deterministic numeric interpolation, seeking by supplied position, and once/loop/ping-pong/hold playback normalization. It uses integer microseconds internally. Track targets must be dot-separated identifiers, and a scene may bind a target only once (case-insensitively); separate scenes may address the same target. Host adapters handle frame delivery, drawing, native animation APIs, audio output and lifecycle integration. The core must not depend on browser timers, CSS, Android APIs, a particular OS scheduler or a specific language. The current subset does not yet implement event dispatch, wall-clock scheduling, frame-based time, colors or transforms. It supports linear, quadratic/cubic in/out/in-out, step and deterministic spring easing for numeric tracks.

Adapters advertise capabilities (target types, easing, clock precision, audio/video, background execution and lifecycle). Missing capabilities produce diagnostics or an explicitly declared fallback; they must not silently alter timing semantics. Disposed targets cancel or detach their tracks. Untrusted timelines have configurable limits for duration, tracks, keyframes, recursion and event frequency.

## 12. Unified compiler model

Pipeline:

1. Lexer and source map.
2. Parser and diagnostics.
3. Semantic validation and name resolution.
4. Typed section ASTs.
5. Unified versioned application IR, including Timeline IR.
6. Host capability negotiation.
7. Host execution/rendering.

SCRIPTS controls timelines through typed operations such as play, pause, seek and cancel. TIME calls SCRIPTS only through declared event bindings. This keeps side effects explicit and avoids circular evaluation.

## 13. Complete five-part single-page specimen

This is the target design specimen, not a claim that every construct is currently executable.

```cudl
bundle WelcomeApp

    GUIDE
        name = WelcomeApp
        version = 1.0
        target = universal
        theme = soft
        time-unit = ms

    KIT
        theme = soft
            background = #F5F0E8
            foreground = #292521
            accent = #B98B68
            radius = 18

        component WelcomeCard
            property heading
            property subtitle optional
            card
                title heading
                text subtitle

    PAGES
        page Home
            background soft.background
            center
                @WelcomeCard
                    heading = Welcome
                    subtitle = A little room to breathe
                text #greeting
                button Get Started
                    on click @start

    SCRIPTS
        #greeting = Hello, Harry
        #started = false

        @start
            #started = true
            @play WelcomeFlow

        @welcomeFinished
            print Welcome experience completed

    TIME
        timeline WelcomeFlow
            duration 1800ms
            clock relative
            mode once

            scene Entrance
                at 0ms
                duration 1000ms
                track Home.WelcomeCard.opacity
                    from 0
                    to 1
                    duration 700ms
                    ease out-cubic
                track Home.greeting.opacity
                    from 0
                    to 1
                    start 250ms
                    duration 750ms

            scene Prompt
                at 1000ms
                duration 800ms
                track Home.GetStarted.scale
                    from 1
                    to 1.05
                    duration 400ms
                    ease spring

            on complete
                @welcomeFinished
```

## 14. Conformance and implementation status

This specification is the target contract, not a statement that all features exist today.

| Capability | Target | Current status |
| --- | --- | --- |
| Indentation-first syntax | Required | Existing parser |
| Hash variables and comments | Required | Implemented |
| Dynamic assignment and safe expressions | Required | Implemented subset |
| Functions and returns | Required | Implemented subset |
| Conditionals and loops | Required | Planned |
| Five-part bundle | Required | Flexible source order, mixed-case section keywords, GUIDE/KIT equals validation and section-aware application IR |
| Platform/device routing | Required | Initial global and component route compiler with fallback, device class, width, input and capability matching |
| PICKER host selection | Required | Initial React/Python/Android/iOS native block filtering; no source-preserving packaging or execution |
| Developer tooling | Required | CLI checks and diagnostics; editor language server, formatter and debugger remain planned |
| Timeline syntax and model | Required | Experimental numeric timelines/scenes/tracks/keyframes; serialized separately from application IR |
| Portable timeline evaluator | Required | Experimental numeric subset with integer-microsecond evaluation and bounded playback modes |
| React/native timeline adapters | Required | React renders KIT/PAGES; TIME playback adapters are not implemented |
| Capability negotiation | Required | Planned |

Remaining implementation order:
1. Add section-specific semantic validation for GUIDE, KIT, PAGES and SCRIPTS while preserving the shared application IR.
2. Promote the experimental numeric timeline model into a versioned Timeline IR within the application bundle.
3. Add explicit TIME event dispatch and SCRIPTS bindings with side-effect and cancellation rules.
4. Extend interpolation to colors, transforms and discrete values with documented semantics.
5. Add a React TIME playback adapter, then additional host adapters against a shared conformance suite.
6. Add capability negotiation and conformance fixtures for clock precision, lifecycle and unsupported targets.

A feature is implemented only when parser, IR, runtime/adapter, tests, docs and CI agree.
