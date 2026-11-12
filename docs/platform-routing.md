# CUDL platform routing and PICKER

Status: routing and host-block selection are initial core implementations. They
select declared branches; they do not execute native code or produce native
application packages yet.

## GUIDE configuration

Configuration assignments always use equals:

```cudl
GUIDE
    name = WelcomeApp
    version = 1.0
    targets = [react, python]
    platforms = [android, ios, web, windows, macos, linux]
    routing = device
    time-unit = ms
```

The five sections may appear in any order and may be written in any keyword
capitalization. Each section may appear at most once. The serialized
application IR presents sections in canonical GUIDE, KIT, PAGES, SCRIPTS, TIME
order.

## Global routing map

A GUIDE route can route one component from a central place. Multiple component
entries can be declared using separate route blocks:

```cudl
GUIDE
    route = android
        component = Navigation
        device = phone
        use = AndroidPhoneNavigation

    route = android
        component = Navigation
        device = tablet
        use = AndroidTabletNavigation

    route = default
        component = Navigation
        use = ResponsiveNavigation
```

## Component-specific routing

A component can define local implementations in KIT:

```cudl
KIT
    component Navigation
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

Local routes override global routes with an otherwise equal match. The
initial route model supports:

- platform: android, ios, web, windows, macos, linux, or default
- device class: phone, tablet, desktop, or any
- optional minimum and maximum width in logical pixels
- input mode such as touch, pointer, keyboard or stylus
- required adapter capabilities such as camera, stylus or multitouch
- explicit priority for deterministic tie-breaking

The route compiler validates missing implementations and invalid width ranges.
Resolution chooses the most specific compatible route, then the default.
If neither exists, it returns an explicit no-route result; it does not silently
select an incompatible platform implementation.

## PICKER native script selection

```cudl
SCRIPTS
    script
        #ready = true

    javascript
        export const greeting = "Hello from React";

    python
        def greeting():
            return "Hello from Python"

    kotlin
        fun greeting() = "Hello from Android"

    json
        { "label": "Hello" }
```

The Python core exposes `filter_scripts(nodes, host)`:

- React selects JavaScript and TypeScript.
- Python selects Python.
- Android selects Kotlin and Java.
- iOS selects Swift.
- CUDL script blocks and JSON data blocks are included for every host.
- Other native language blocks are listed as excluded.

Additional host languages can be explicitly supplied. Unknown host profiles
raise an error rather than guessing. JSON is data, never executable code.

## Current boundaries

The current parser stores a generic indentation tree. Native code is not yet
captured as a byte-for-byte opaque source span, and PICKER currently selects
parsed language nodes rather than emitting a complete portable bundle.
Host-specific dependency discovery, package installation, native execution,
React Native/Android/iOS rendering and automatic device detection remain host
adapter work. The host application must provide a trusted DeviceContext and
must execute only code it explicitly supports.
