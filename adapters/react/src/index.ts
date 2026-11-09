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
  properties?: Record<string, string>;
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

function displayValue(raw = ""): string {
  const value = raw.trim();
  if (value.length < 2) return value;
  const quote = value[0];
  if ((quote !== '"' && quote !== "'") || value.at(-1) !== quote) return value;
  return value.slice(1, -1).replace(/\\(n|r|t|\\|"|')/g, (_, escaped: string) => {
    const escapes: Record<string, string> = {
      n: "\n", r: "\r", t: "\t", "\\": "\\", '"': '"', "'": "'",
    };
    return escapes[escaped] ?? escaped;
  });
}

function readAssignments(node: CUDLIRNode): Record<string, string> {
  const values: Record<string, string> = {};
  for (const child of node.children ?? []) {
    const raw = child.value ?? "";
    if (!raw.trimStart().startsWith("=")) continue;
    values[child.name.toLowerCase()] = displayValue(raw.trimStart().slice(1));
  }
  return values;
}

function renderNode(
  node: CUDLIRNode,
  registry: CUDLComponentRegistry,
  definitions: Map<string, CUDLIRNode>,
  key: string,
  properties: Record<string, string> = {},
): ReactNode {
  const name = node.name.toLowerCase();
  if (name === "property" || name === "component") return null;

  let value = displayValue(node.value);
  if (Object.prototype.hasOwnProperty.call(properties, value.toLowerCase())) {
    value = properties[value.toLowerCase()];
  }

  if (name.startsWith("@")) {
    const componentName = name.slice(1);
    const assigned = readAssignments(node);
    const CustomComponent = registry[componentName];
    const definition = definitions.get(componentName);

    if (CustomComponent) {
      return createElement(
        CustomComponent,
        { key, name: componentName, value, sourceLine: node.source?.line, properties: assigned },
        ...(node.children ?? [])
          .filter((child) => !(child.value ?? "").trimStart().startsWith("="))
          .map((child, index) => renderNode(child, registry, definitions, `${key}.${index}`, assigned)),
      );
    }

    if (definition) {
      const body = (definition.children ?? []).filter((child) => child.name !== "property");
      return createElement(
        "div",
        { key, "data-cudl-component": componentName, "data-cudl-source-line": node.source?.line },
        ...body.map((child, index) => renderNode(child, registry, definitions, `${key}.component.${index}`, assigned)),
      );
    }
  }

  const children = (node.children ?? [])
    .filter((child) => !(child.value ?? "").trimStart().startsWith("="))
    .map((child, index) => renderNode(child, registry, definitions, `${key}.${index}`, properties));

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
    ? `cudl-${name}`
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
 * This early renderer supports string-valued component properties only.
 */
export function renderCUDL(
  document: CUDLIRDocument,
  components: CUDLComponentRegistry = {},
): ReactNode {
  if (document.type !== "CUDLIR" || document.version !== 1) {
    throw new Error("Unsupported CUDL IR document or version.");
  }

  const definitions = new Map<string, CUDLIRNode>();
  for (const node of document.nodes) {
    if (node.name.toLowerCase() === "component") {
      const componentName = (node.value ?? "").trim().split(/\\s+/, 1)[0]?.toLowerCase();
      if (componentName) definitions.set(componentName, node);
    }
  }

  return createElement(
    "div",
    { "data-cudl-root": "", "data-cudl-source": document.source ?? undefined },
    ...document.nodes
      .filter((node) => node.name.toLowerCase() !== "component")
      .map((node, index) => renderNode(node, components, definitions, String(index))),
  );
}
