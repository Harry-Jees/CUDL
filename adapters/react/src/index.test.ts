import assert from "node:assert/strict";
import test from "node:test";
import { isValidElement, type ReactElement, type ReactNode } from "react";
import { renderCUDL, renderCUDLApplication, resolveCUDLValue, type CUDLApplicationIR, type CUDLIRDocument } from "./index.js";

function findElements(node: ReactNode, type: string): ReactElement<any>[] {
  const found: ReactElement<any>[] = [];
  const visit = (value: ReactNode): void => {
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }
    if (!isValidElement(value)) return;
    if (value.type === type) found.push(value);
    visit((value as ReactElement<any>).props.children as ReactNode);
  };
  visit(node);
  return found;
}

function document(values: Array<{ name: string; value: string; line: number }>): CUDLIRDocument {
  return {
    type: "CUDLIR",
    version: 1,
    nodes: values.map(({ name, value, line }) => ({
      kind: "element",
      category: "element",
      name,
      value,
      source: { line },
    })),
  };
}

test("blocks unsafe links and image URLs with source-aware diagnostics", () => {
  const diagnostics: Array<{ code: string; line?: number }> = [];
  const ir = document([
    { name: "link", value: "javascript:alert(1)", line: 3 },
    { name: "link", value: "//evil.example/path", line: 4 },
    { name: "link", value: "\\\\evil.example\\path", line: 5 },
    { name: "link", value: "https://example.org/\u0000bad", line: 6 },
    { name: "image", value: "data:text/html,unsafe", line: 7 },
    { name: "image", value: "ftp://example.org/image.png", line: 8 },
  ]);
  const rendered = renderCUDL(ir, {}, { onDiagnostic: (d) => diagnostics.push(d) });
  assert.equal(findElements(rendered, "a").length, 4);
  assert.equal(findElements(rendered, "img").length, 2);
  assert.deepEqual(findElements(rendered, "a").map((e) => e.props.href), [undefined, undefined, undefined, undefined]);
  assert.deepEqual(findElements(rendered, "img").map((e) => e.props.src), [undefined, undefined]);
  assert.deepEqual(diagnostics.map((d) => d.code), Array(6).fill("CUDL4003"));
  assert.deepEqual(diagnostics.map((d) => d.line), [3, 4, 5, 6, 7, 8]);
});

test("allows ordinary relative and HTTP(S) resources and safe link schemes", () => {
  const ir = document([
    { name: "link", value: "https://example.org/page", line: 1 },
    { name: "link", value: "mailto:hello@example.org", line: 2 },
    { name: "link", value: "/docs/start", line: 3 },
    { name: "image", value: "/assets/logo.png", line: 4 },
    { name: "image", value: "https://cdn.example.org/logo.png", line: 5 },
  ]);
  const rendered = renderCUDL(ir);
  assert.deepEqual(findElements(rendered, "a").map((e) => e.props.href), [
    "https://example.org/page",
    "mailto:hello@example.org",
    "/docs/start",
  ]);
  assert.deepEqual(findElements(rendered, "img").map((e) => e.props.src), [
    "/assets/logo.png",
    "https://cdn.example.org/logo.png",
  ]);
});

test("rejects unsupported IR versions before rendering", () => {
  assert.throws(() => renderCUDL({ type: "CUDLIR", version: 2, nodes: [] }), /Unsupported CUDL IR/);
});


test("preserves source lines on built-in and unknown host elements", () => {
  const rendered = renderCUDL(document([
    { name: "title", value: "Welcome", line: 12 },
    { name: "custom-unknown", value: "Safe fallback", line: 13 },
  ]));
  assert.equal(findElements(rendered, "h1")[0]?.props["data-cudl-source-line"], 12);
  const fallback = findElements(rendered, "div").find((element) => element.props["data-cudl-component"] === "custom-unknown");
  assert.equal(fallback?.props["data-cudl-source-line"], 13);
});

test("resolves indexed host data paths and refuses inherited properties", () => {
  assert.equal(resolveCUDLValue("#users[0].name", { users: [{ name: "Ada" }] }), "Ada");
  assert.equal(resolveCUDLValue("#assets[logo]", { assets: { logo: "/logo.svg" } }), "/logo.svg");
  assert.throws(() => resolveCUDLValue("#user.constructor", { user: {} }), /was not found/);
  assert.throws(() => resolveCUDLValue("#user.__proto__", { user: {} }), /was not found/);
});

test("renders KIT definitions through application IR and rejects unsupported KIT versions", () => {
  const application: CUDLApplicationIR = {
    type: "CUDLApplicationIR",
    version: 1,
    sections: {
      kit: {
        type: "CUDLIR",
        version: 1,
        nodes: [{
          kind: "component",
          category: "component",
          name: "component",
          value: "WelcomeCard",
          children: [
            { kind: "property", category: "property", name: "property", value: "heading" },
            { kind: "element", category: "element", name: "title", value: "heading", source: { line: 4 } },
          ],
        }],
      },
      pages: {
        type: "CUDLIR",
        version: 1,
        nodes: [{
          kind: "element",
          category: "element",
          name: "WelcomeCard",
          value: "",
          source: { line: 10 },
          children: [{
            kind: "property",
            category: "property",
            name: "heading",
            value: "= #user.name",
            source: { line: 11 },
          }],
        }],
      },
    },
  };
  const rendered = renderCUDLApplication(application, {}, { data: { user: { name: "Harry" } } });
  assert.equal(findElements(rendered, "h1")[0]?.props.children, "Harry");

  const invalid = {
    ...application,
    sections: {
      ...application.sections,
      kit: { type: "CUDLIR", version: 2, nodes: [] },
    },
  } as unknown as CUDLApplicationIR;
  assert.throws(() => renderCUDLApplication(invalid), /Unsupported CUDL KIT IR/);
});
