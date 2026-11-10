import {
  createElement,
  type ComponentType,
  type ReactNode,
} from "react";

export interface CUDLIRNode {
  kind: string;
  name: string;
  value?: string;
  category: string;
  source?: { line?: number };
  children?: CUDLIRNode[];
}

export interface CUDLIRDocument {
  type: "CUDLIR";
  version: number;
  source?: string | null;
  nodes: CUDLIRNode[];
}

export interface CUDLComponentProps {
  name: string;
  value: string;
  sourceLine?: number;
  properties?: Record<string, unknown>;
  children?: ReactNode;
}

export type CUDLComponentRegistry = Record<string, ComponentType<CUDLComponentProps>>;

const TAGS: Record<string, string> = {
  page: "main", header: "header", content: "section", footer: "footer",
  row: "div", column: "div", grid: "div", stack: "div", split: "div",
  cards: "div", overlay: "div", scroll: "div", title: "h1", heading: "h2",
  text: "p", paragraph: "p", button: "button", image: "img", link: "a",
  divider: "hr", spacer: "div",
};

const NON_RENDERING_BLOCKS = new Set(["script", "js", "javascript", "python", "java", "c", "cpp", "rust", "go", "swift", "kotlin"]);

type CUDLValue = string | number | boolean | null | undefined;
type CUDLData = Record<string, unknown>;
type CUDLPathPart = string | number;

export interface CUDLRuntimeDiagnostic {
  code: "CUDL4001" | "CUDL4002";
  message: string;
  line?: number;
}
export interface CUDLRenderOptions {
  data?: CUDLData;
  onDiagnostic?: (diagnostic: CUDLRuntimeDiagnostic) => void;
}

function decodeString(raw: string): string {
  return raw.slice(1, -1).replace(/\\(n|r|t|\\|"|')/g, (_, escaped: string) => {
    const escapes: Record<string, string> = {
      n: "\n", r: "\r", t: "\t", "\\": "\\", '"': '"', "'": "'",
    };
    return escapes[escaped] ?? escaped;
  });
}

function parseDataPath(source: string): CUDLPathPart[] | null {
  if (!source.startsWith("#")) return null;
  const path = source.slice(1);
  const root = /^[A-Za-z_][A-Za-z0-9_]*/.exec(path);
  if (!root) return null;

  const parts: CUDLPathPart[] = [root[0]];
  let index = root[0].length;
  while (index < path.length) {
    if (path[index] === ".") {
      const property = /^[A-Za-z_][A-Za-z0-9_]*/.exec(path.slice(index + 1));
      if (!property) return null;
      parts.push(property[0]);
      index += property[0].length + 1;
      continue;
    }
    if (path[index] === "[") {
      const end = path.indexOf("]", index + 1);
      if (end < 0) return null;
      const key = path.slice(index + 1, end).trim();
      if (/^(0|[1-9]\d*)$/.test(key)) {
        parts.push(Number(key));
      } else if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
        parts.push(key);
      } else if ((key.startsWith('"') && key.endsWith('"')) ||
                 (key.startsWith("'") && key.endsWith("'"))) {
        parts.push(decodeString(key));
      } else {
        return null;
      }
      index = end + 1;
      continue;
    }
    return null;
  }
  return parts;
}

function resolveDataPath(path: string, data: CUDLData): CUDLValue {
  const parts = parseDataPath(path);
  if (!parts) throw new Error("Invalid CUDL variable path.");

  let current: unknown = data;
  for (const part of parts) {
    if (typeof part === "number") {
      if (!Array.isArray(current) || !Number.isSafeInteger(part) ||
          part < 0 || part >= current.length) {
        throw new Error('Data index in "' + path + '" was not found.');
      }
      current = current[part];
      continue;
    }
    if (current === null || typeof current !== "object" ||
        !Object.prototype.hasOwnProperty.call(current, part)) {
      throw new Error('Data path "' + path + '" was not found.');
    }
    current = (current as Record<string, unknown>)[part];
  }
  if (current === null || typeof current === "string" ||
      typeof current === "number" || typeof current === "boolean") {
    return current;
  }
  throw new Error('Data path "' + path + '" must resolve to a primitive value.');
}

/** Resolve dynamic CUDL values; only #name requests host-data lookup. */
export function resolveCUDLValue(
  source: string,
  data: CUDLData = {},
): CUDLValue {
  const raw = source.trim();
  if (!raw) return "";
  if ((raw.startsWith('"') && raw.endsWith('"')) ||
      (raw.startsWith("'") && raw.endsWith("'"))) {
    return decodeString(raw);
  }
  if (/^(true|false)$/i.test(raw)) return raw.toLowerCase() === "true";
  if (/^(null|none)$/i.test(raw)) return null;
  if (/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(raw)) {
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error("Numeric values must be finite.");
    return value;
  }
  if (raw.startsWith("#")) return resolveDataPath(raw, data);
  return raw;
}

function stringifyValue(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

function readAssignments(
  node: CUDLIRNode,
  data: CUDLData,
  onDiagnostic?: CUDLRenderOptions["onDiagnostic"],
): Record<string, CUDLValue> {
  const values: Record<string, CUDLValue> = {};
  for (const child of node.children ?? []) {
    const raw = child.value ?? "";
    if (!raw.trimStart().startsWith("=")) continue;
    try {
      values[child.name.toLowerCase()] = resolveCUDLValue(raw.trimStart().slice(1), data);
    } catch (error) {
      onDiagnostic?.({
        code: "CUDL4001",
        message: error instanceof Error ? error.message : "Invalid component property value.",
        line: child.source?.line,
      });
    }
  }
  return values;
}

function renderNode(
  node: CUDLIRNode,
  registry: CUDLComponentRegistry,
  definitions: Map<string, CUDLIRNode>,
  key: string,
  properties: Record<string, CUDLValue> = {},
  data: CUDLData = {},
  onDiagnostic?: CUDLRenderOptions["onDiagnostic"],
): ReactNode {
  const name = node.name.toLowerCase();
  if (name === "property" || name === "component" || NON_RENDERING_BLOCKS.has(name)) return null;

  const rawValue = (node.value ?? "").trim();
  let resolved: CUDLValue;
  if (Object.prototype.hasOwnProperty.call(properties, rawValue.toLowerCase())) {
    resolved = properties[rawValue.toLowerCase()];
  } else {
    try {
      resolved = resolveCUDLValue(rawValue, data);
    } catch (error) {
      resolved = rawValue;
      if (rawValue.startsWith("#")) {
        onDiagnostic?.({
          code: "CUDL4002",
          message: error instanceof Error ? error.message : "Unable to resolve CUDL value.",
          line: node.source?.line,
        });
      }
    }
  }
  const value = stringifyValue(resolved);

  if (name.startsWith("@")) {
    const componentName = name.slice(1);
    const assigned = readAssignments(node, data, onDiagnostic);
    const CustomComponent = registry[componentName];
    const definition = definitions.get(componentName);

    if (CustomComponent) {
      return createElement(
        CustomComponent,
        { key, name: componentName, value, sourceLine: node.source?.line, properties: assigned },
        ...(node.children ?? [])
          .filter((child) => !(child.value ?? "").trimStart().startsWith("="))
          .map((child, index) => renderNode(child, registry, definitions, \`${key}.${index}\`, assigned, data, onDiagnostic)),
      );
    }

    if (definition) {
      const body = (definition.children ?? []).filter((child) => child.name !== "property");
      return createElement(
        "div",
        { key, "data-cudl-component": componentName, "data-cudl-source-line": node.source?.line },
        ...body.map((child, index) => renderNode(child, registry, definitions, \`${key}.component.${index}\`, assigned, data, onDiagnostic)),
      );
    }
  }

  const children = (node.children ?? [])
    .filter((child) => !(child.value ?? "").trimStart().startsWith("="))
    .map((child, index) => renderNode(child, registry, definitions, \`${key}.${index}\`, properties, data, onDiagnostic));

  const CustomComponent = registry[name];
  if (CustomComponent) {
    return createElement(CustomComponent, { key, name, value, sourceLine: node.source?.line, properties }, ...children);
  }

  const tag = TAGS[name];
  if (!tag) {
    return createElement("div", { key, "data-cudl-component": name }, ...children);
  }
  if (name === "image") {
    return createElement(tag, { key, src: value, alt: "", loading: "lazy" });
  }
  if (name === "button") {
    return createElement(tag, { key, type: "button" }, value, ...children);
  }
  if (name === "link") {
    return createElement(tag, { key, href: value || undefined }, ...children);
  }

  const className = ["row", "column", "grid", "stack", "split", "cards", "overlay", "scroll"].includes(name)
    ? \`cudl-${name}\`
    : undefined;
  return createElement(
    tag,
    { key, className, "data-cudl": name },
    value && !["page", "header", "content", "footer", "divider", "spacer"].includes(name) ? value : null,
    ...children,
  );
}

/** Render CUDL IR inside an existing React application.
 * Component declarations in the supplied document are indexed automatically.
 * Component properties accept dynamic values and explicit #data paths.
 * No source code or function calls are evaluated.
 */
export function renderCUDL(
  document: CUDLIRDocument,
  components: CUDLComponentRegistry = {},
  options: CUDLRenderOptions = {},
): ReactNode {
  if (document.type !== "CUDLIR" || document.version !== 1) {
    throw new Error("Unsupported CUDL IR document or version.");
  }

  const definitions = new Map<string, CUDLIRNode>();
  for (const node of document.nodes) {
    if (node.name.toLowerCase() === "component") {
      const componentName = (node.value ?? "").trim().split(/\s+/, 1)[0]?.toLowerCase();
      if (componentName) definitions.set(componentName, node);
    }
  }

  return createElement(
    "div",
    { "data-cudl-root": "", "data-cudl-source": document.source ?? undefined },
    ...document.nodes
      .filter((node) => node.name.toLowerCase() !== "component")
      .map((node, index) => renderNode(node, components, definitions, String(index), {}, options.data ?? {}, options.onDiagnostic)),
  );
}
