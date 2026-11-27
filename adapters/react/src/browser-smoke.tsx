import { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  renderCUDL,
  type CUDLComponentProps,
  type CUDLIRDocument,
} from "./index.js";

function Counter({ value }: CUDLComponentProps) {
  const [count, setCount] = useState(0);
  return (
    <button id="counter" type="button" onClick={() => setCount((current) => current + 1)}>
      {value}: {count}
    </button>
  );
}

const application: CUDLIRDocument = {
  type: "CUDLIR",
  version: 1,
  nodes: [
    {
      kind: "element",
      category: "element",
      name: "page",
      value: "",
      source: { line: 1 },
      children: [
        {
          kind: "element",
          category: "element",
          name: "title",
          value: "CUDL browser smoke",
          source: { line: 2 },
        },
        {
          kind: "element",
          category: "element",
          name: "counter",
          value: "Clicks",
          source: { line: 3 },
        },
        {
          kind: "element",
          category: "element",
          name: "link",
          value: "javascript:alert(1)",
          source: { line: 4 },
        },
        {
          kind: "element",
          category: "element",
          name: "unknown-widget",
          value: "",
          source: { line: 5 },
          children: [
            {
              kind: "element",
              category: "element",
              name: "text",
              value: "Fallback",
              source: { line: 6 },
            },
          ],
        },
      ],
    },
  ],
};

const target = globalThis.document.getElementById("root");
if (!target) throw new Error("Browser smoke root element is missing.");
createRoot(target).render(renderCUDL(application, { counter: Counter }));
