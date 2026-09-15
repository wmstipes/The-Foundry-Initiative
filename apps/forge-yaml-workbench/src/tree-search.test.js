import { describe, expect, it } from "vitest";
import { buildTreeSearchIndex, childYamlPath, matchingTextRanges, searchTreeIndex } from "./tree-search.js";

describe("YAML tree search", () => {
  const documents = [{
    index: 1,
    raw: {
      metadata: { name: "Demo" },
      enabled: true,
      retries: 3,
      optional: null,
      containers: [{ image: "example/app:1.0" }],
      "dotted.key": "value"
    }
  }, {
    index: 2,
    raw: { name: "Second" }
  }];

  it("builds stable canonical paths in document and depth-first order", () => {
    const paths = buildTreeSearchIndex(documents).map((record) => record.path);
    expect(paths).toEqual([
      "$", "$.metadata", "$.metadata.name", "$.enabled", "$.retries", "$.optional",
      "$.containers", "$.containers[0]", "$.containers[0].image", '$["dotted.key"]',
      "$", "$.name"
    ]);
    expect(childYamlPath("$", "dash-key")).toBe('$["dash-key"]');
  });

  it("matches keys, scalar values, and paths case-insensitively once per node", () => {
    const index = buildTreeSearchIndex(documents);
    expect(searchTreeIndex(index, "NAME").map((record) => record.id)).toEqual([
      "document-1:$.metadata.name",
      "document-2:$.name"
    ]);
    expect(searchTreeIndex(index, "true").map((record) => record.path)).toEqual(["$.enabled"]);
    expect(searchTreeIndex(index, "3").map((record) => record.path)).toEqual(["$.retries"]);
    expect(searchTreeIndex(index, "null").map((record) => record.path)).toEqual(["$.optional"]);
    expect(searchTreeIndex(index, "containers[0]").map((record) => record.path)).toEqual([
      "$.containers[0]",
      "$.containers[0].image"
    ]);
  });

  it("returns literal highlight segments without interpreting regular expressions", () => {
    expect(matchingTextRanges("a.b.A.B", "a.b")).toEqual([
      { text: "a.b", match: true },
      { text: ".", match: false },
      { text: "A.B", match: true }
    ]);
    expect(searchTreeIndex(buildTreeSearchIndex(documents), ".*")).toEqual([]);
  });
});
