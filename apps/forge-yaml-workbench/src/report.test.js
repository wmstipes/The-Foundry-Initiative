import { describe, expect, it } from "vitest";
import { analyzeYaml } from "./analyze.js";
import { buildMarkdownReport, reportFilename } from "./report.js";

describe("Markdown analysis reports", () => {
  it("builds a deterministic Kubernetes report without embedding the source YAML", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata:",
      "  name: report-demo",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: example/app:latest",
      ""
    ].join("\n");
    const analysis = analyzeYaml(source, "kubernetes");
    const first = buildMarkdownReport({ filename: "demo.yaml", analysis });
    const second = buildMarkdownReport({ filename: "demo.yaml", analysis });

    expect(first).toEqual(second);
    expect(first.filename).toBe("demo-report.md");
    expect(first.markdown).toContain("# Forge YAML Workbench Analysis Report");
    expect(first.markdown).toContain("## Document 1 — Pod/report\\-demo");
    expect(first.markdown).toContain("## Deterministic Operational Findings");
    expect(first.markdown).toContain("## Kubernetes Schema Results");
    expect(first.markdown).toContain("OWASP Kubernetes Top 10:2025 Review Profile");
    expect(first.markdown).toContain("not a compliance score or pass/fail result");
    expect(first.markdown).not.toContain(source);
    expect(first.markdown).not.toContain("Generated at");
  });

  it("keeps General YAML reports free of Kubernetes-specific review sections", () => {
    const analysis = analyzeYaml("settings:\n  theme: dark\n", "general");
    const report = buildMarkdownReport({ filename: "settings.yml", analysis });

    expect(report.markdown).toContain("**Inspection mode:** General YAML");
    expect(report.markdown).toContain("**Top-level keys:** `settings`");
    expect(report.markdown).not.toContain("# Kubernetes Review");
    expect(report.markdown).not.toContain("Kubernetes Schema Results");
    expect(report.markdown).not.toContain("OWASP Kubernetes");
  });

  it("reports empty and invalid input without inventing parsed documents", () => {
    const empty = buildMarkdownReport({
      filename: "empty.yaml",
      analysis: analyzeYaml("", "kubernetes")
    });
    expect(empty.documentCount).toBe(0);
    expect(empty.markdown).toContain("No YAML documents were parsed.");
    expect(empty.markdown).toContain("No parsed Kubernetes resources were available");

    const invalid = buildMarkdownReport({
      filename: "invalid.yaml",
      analysis: analyzeYaml("kind: Pod\nkind: Service\n", "kubernetes")
    });
    expect(invalid.documentCount).toBe(0);
    expect(invalid.findingCount).toBeGreaterThan(0);
    expect(invalid.markdown).toContain("## YAML Syntax Errors");
    expect(invalid.markdown).toContain("**Location:** Line 2, column 1");
  });

  it("preserves multi-document order and includes schema boundary states", () => {
    const source = [
      "apiVersion: networking.k8s.io/v1",
      "kind: Ingress",
      "metadata: {name: unsupported}",
      "---",
      "apiVersion: database.example.com/v1",
      "kind: Database",
      "metadata: {name: custom}",
      ""
    ].join("\n");
    const report = buildMarkdownReport({ filename: "bundle.yaml", analysis: analyzeYaml(source) });

    expect(report.markdown.indexOf("Ingress/unsupported")).toBeLessThan(
      report.markdown.indexOf("Database/custom")
    );
    expect(report.markdown).toContain("No bundled v1.36.4 schema supports");
    expect(report.markdown).toContain("CRD schema unavailable");
  });

  it("escapes Markdown structure and safely fences generated examples", () => {
    const analysis = analyzeYaml([
      "apiVersion: v1",
      "kind: Pod",
      "metadata:",
      "  name: \"name|with*[markup]\"",
      "spec:",
      "  containers:",
      "    - name: \"app`name\"",
      "      image: example/app:1.0.0",
      ""
    ].join("\n"));
    const report = buildMarkdownReport({ filename: "unsafe`name.yaml", analysis });

    expect(report.markdown).toContain("Pod/name\\|with\\*\\[markup\\]");
    expect(report.markdown).toContain("``unsafe`name.yaml``");
    expect(report.markdown).toContain("**Example YAML:**");
    expect(report.markdown).toMatch(/```yaml\n[\s\S]+\n```/);
  });

  it("derives bounded portable report filenames", () => {
    expect(reportFilename("C:\\manifests\\opened.yml")).toBe("opened-report.md");
    expect(reportFilename("../service.yaml")).toBe("service-report.md");
    expect(reportFilename(".yaml")).toBe("manifest-report.md");
    expect(reportFilename("bad:name.yaml")).toBe("bad-name-report.md");
  });
});
