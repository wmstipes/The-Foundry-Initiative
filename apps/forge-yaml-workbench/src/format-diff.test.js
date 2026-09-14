import { describe, expect, it } from "vitest";
import { buildLineDiff } from "./format-diff.js";

describe("formatting line diff", () => {
  it("aligns unchanged lines and labels additions and removals", () => {
    const diff = buildLineDiff(
      "kind: Pod\nmetadata: {name: demo}\n",
      "kind: Pod\nmetadata:\n  name: demo\n"
    );

    expect(diff).toMatchObject({ added: 2, removed: 1 });
    expect(diff.rows).toEqual([
      { type: "context", beforeNumber: 1, afterNumber: 1, text: "kind: Pod" },
      { type: "added", beforeNumber: null, afterNumber: 2, text: "metadata:" },
      { type: "added", beforeNumber: null, afterNumber: 3, text: "  name: demo" },
      { type: "removed", beforeNumber: 2, afterNumber: null, text: "metadata: {name: demo}" }
    ]);
  });

  it("uses bounded replacement alignment for unusually large comparisons", () => {
    const before = Array.from({ length: 1001 }, (_, index) => "old-" + index).join("\n");
    const after = Array.from({ length: 1001 }, (_, index) => "new-" + index).join("\n");
    const diff = buildLineDiff(before, after);

    expect(diff).toMatchObject({ added: 1001, removed: 1001, simplified: true });
    expect(diff.rows[0]).toMatchObject({ type: "removed", beforeNumber: 1 });
    expect(diff.rows.at(-1)).toMatchObject({ type: "added", afterNumber: 1001 });
  });

  it("normalizes CRLF and omits the trailing newline marker", () => {
    const diff = buildLineDiff("one\r\ntwo\r\n", "one\ntwo\n");

    expect(diff).toMatchObject({ added: 0, removed: 0 });
    expect(diff.rows).toHaveLength(2);
    expect(diff.rows.every((row) => row.type === "context")).toBe(true);
  });
});
