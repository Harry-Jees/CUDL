# CUDL example conformance

CI validates the three checked-in examples at the level they actually support.

| Example | Purpose | CI validation |
| --- | --- | --- |
| `hello.cudl` | Minimal visual page fragment using canonical angle-tag layout syntax | `cudl check` |
| `five-part-welcome.cudl` | Canonical GUIDE/KIT/PAGES/SCRIPTS/TIME bundle | `cudl bundle` (parser, bundle lowering and TIME compilation) |
| `hello-react-python.cudl` | Host-integration specimen, including routing and opaque native blocks | `cudl check` only; native blocks are not executed |

The bundle command emits the application IR and compiled TIME data. The
integration specimen is intentionally not treated as an executable React/Python
application: host execution and event wiring remain adapter responsibilities.

Reproduce the CI checks from the repository root:

```sh
cudl check examples/hello.cudl
cudl check examples/hello-react-python.cudl
cudl bundle examples/five-part-welcome.cudl
```
