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
  children?: ReactNode;
}

export type CUDLComponentRegistry = Record<
  string,
  ComponentType<CUDLComponentProps>
>;

const TAGS: Record<string, string> = {
  page: "main",
  header: "header",
  content: "section",
  footer: "footer",
  row: "div",
  column: "div",
  grid: "div",
  stack: "div",
  split: "div",
  cards: "div",
  overlay: "div",
  scroll: "div",
  title: "h1",
  heading: "h2",
  text: "p",
  paragraph: "p",
  button: "button",
  image: "img",
  link: "a",
  divider: "hr",
  spacer: "div",
};

function displayValue(raw = ""): string {
  const value = raw.trim();
  if (value.length < 2) return value;
  const quote = value[0];
  if ((quote !== '"' && quote !== "'") || value.at(-1) !== quote) {
    return value;
  }

  return value.slice(1, -1).replace(/\\(n|r|t|\\|"|')/g, (_, escaped: string) => {
    const escapes: Record<string, string> = {
      n: "\n",
      r: "\r",
      t: "\t",
      "\\": "\\",
      '"': '"',
      "'": "'",
    };
    return escapes[escaped] ?? escaped;
  });
}

function renderNode(
  node: CUDLIRNode,
  registry: CUDLComponentRegistry,
  key: string,
): ReactNode {
  const name = node.name.toLowerCase();
  const children = (node.children ?? []).map((child, index) =>
    renderNode(child, registry, `${key}.${index}`),
  );
  const value = displayValue(node.value);
  const sourceLine = node.source?.line;

  const CustomComponent = registry[name];
  if (CustomComponent) {
    return createElement(
      CustomComponent,
      { key, name, value, sourceLine },
      ...children,
    );
  }

  const tag = TAGS[name];
  if (!tag) {
    return createElement(
      "div",
      { key, "data-cudl-component": name },
      ...children,
    );
  }

  if (name === "image") {
    return createElement(tag, {
      key,
      src: value,
      alt: "",
      loading: "lazy",
    });
  }

  if (name === "button") {
    return createElement(tag, { key, type: "button" }, value, ...children);
  }

  if (name === "link") {
    return createElement(tag, { key, href: value || undefined }, ...children);
  }

  const className =
    ["row", "column", "grid", "stack", "split", "cards", "overlay", "scroll"]
      .includes(name)
      ? `cudl-${name}`
      : undefined;

  return createElement(
    tag,
    { key, className, "data-cudl": name },
    value && !["page", "header", "content", "footer", "divider", "spacer"].includes(name)
      ? value
      : null,
    ...children,
  );
}

/**
 * Render a CUDL IR document inside an existing React application.
 * This adapter renders structure only; state, events, styles and asset
 * resolution are added by later adapter milestones.
 */
export function renderCUDL(
  document: CUDLIRDocument,
  components: CUDLComponentRegistry = {},
): ReactNode {
  if (document.type !== "CUDLIR" || document.version !== 1) {
    throw new Error("Unsupported CUDL IR document or version.");
  }

  return createElement(
    "div",
    { "data-cudl-root": "", "data-cudl-source": document.source ?? undefined },
    ...document.nodes.map((node, index) =>
      renderNode(node, components, String(index)),
    ),
  );
}
