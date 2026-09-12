import { describe, expect, it } from "vitest";
import { analyzeYaml, formatYaml, splitImage } from "./analyze.js";
import { SAMPLE_YAML } from "./sample.js";

describe("Forge YAML Workbench analysis", () => {
  it("summarizes multi-document Kubernetes YAML", () => {
    const result = analyzeYaml(SAMPLE_YAML);
    expect(result.errors).toHaveLength(0);
    expect(result.documents).toHaveLength(2);
    expect(result.documents[0]).toMatchObject({
      kind: "Deployment",
      name: "restaurant-api",
      namespace: "forge-restaurant",
      replicas: 3
    });
    expect(result.documents[0].containers[0]).toMatchObject({
      imageRepository: "wmstipes/signalforge-restaurant-api",
      imageReference: "0.7.0"
    });
    expect(result.documents[1]).toMatchObject({ kind: "Service", serviceType: "ClusterIP" });
  });

  it("reports duplicate keys", () => {
    const [error] = analyzeYaml("apiVersion: v1\nkind: Pod\nkind: Service\n").errors;
    expect(error).toMatchObject({ document: 1, line: 3, column: 1 });
  });

  it("flags risky workload settings", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata:",
      "  name: risky",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: nginx:latest",
      "      securityContext:",
      "        privileged: true",
      ""
    ].join("\n");
    const titles = analyzeYaml(source).documents[0].findings.map((item) => item.title);
    expect(titles).toContain("app: mutable image reference");
    expect(titles).toContain("app: privileged container");
  });

  it("separates registry ports from image tags", () => {
    expect(splitImage("registry.example:5000/team/app:2.4.0")).toEqual({
      repository: "registry.example:5000/team/app",
      reference: "2.4.0",
      type: "tag"
    });
  });

  it("formats valid YAML", () => {
    expect(formatYaml("kind:  Pod\nmetadata: {name: demo}\n")).toContain("metadata:\n  name: demo");
  });

  it("formats multi-document YAML without creating an empty document", () => {
    const formatted = formatYaml(SAMPLE_YAML);
    const result = analyzeYaml(formatted);

    expect(formatted).not.toContain("---\n---");
    expect(result.errors).toHaveLength(0);
    expect(result.documents.map((document) => document.kind)).toEqual(["Deployment", "Service"]);
  });
});
