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

  it("keeps Kubernetes as the default mode and rejects non-mapping roots", () => {
    const result = analyzeYaml("- one\n- two\n");

    expect(result.mode).toBe("kubernetes");
    expect(result.documents).toHaveLength(0);
    expect(result.errors[0].message).toContain("Kubernetes manifest must be a YAML mapping");
  });

  it("accepts mappings, sequences, and scalars in General YAML mode", () => {
    const source = [
      "environment: lab",
      "enabled: true",
      "---",
      "- forge-head",
      "- forge-node-01",
      "---",
      "ready",
      ""
    ].join("\n");
    const result = analyzeYaml(source, "general");

    expect(result).toMatchObject({ mode: "general", errors: [], warnings: [] });
    expect(result.documents).toEqual([
      expect.objectContaining({ index: 1, rootType: "mapping", entryCount: 2, keys: ["environment", "enabled"], findings: [] }),
      expect.objectContaining({ index: 2, rootType: "sequence", entryCount: 2, findings: [] }),
      expect.objectContaining({ index: 3, rootType: "scalar", value: "ready", findings: [] })
    ]);
  });

  it("suppresses Kubernetes-only findings in General YAML mode", () => {
    const source = "kind: Pod\nmetadata: {name: risky}\nspec: {containers: [{name: app, image: nginx:latest}]}\n";
    const result = analyzeYaml(source, "general");

    expect(result.errors).toHaveLength(0);
    expect(result.documents[0]).toMatchObject({ rootType: "mapping", findings: [] });
    expect(result.documents[0]).not.toHaveProperty("kind");
    expect(result.documents[0]).not.toHaveProperty("schema");
  });

  it("keeps syntax, operational, and schema results separate", () => {
    const source = [
      "apiVersion: apps/v1",
      "kind: Deployment",
      "metadata: {name: separated}",
      "spec:",
      "  replicas: three",
      "  mysteryField: true",
      ""
    ].join("\n");
    const result = analyzeYaml(source);

    expect(result.syntaxErrors).toEqual([]);
    expect(result.documentErrors).toEqual([]);
    expect(result.documents[0].findings.map((item) => item.title)).toContain("No containers found");
    expect(result.documents[0].schema.status).toBe("invalid");
    expect(result.documents[0].schema.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ path: ".spec.replicas", line: 5 }),
      expect.objectContaining({ path: ".spec.mysteryField", line: 6 })
    ]));
  });

  it("reports unsupported built-ins and unavailable CRD schemas without validity claims", () => {
    const result = analyzeYaml([
      "apiVersion: networking.k8s.io/v1",
      "kind: Ingress",
      "metadata: {name: unsupported}",
      "---",
      "apiVersion: database.example.com/v1",
      "kind: Database",
      "metadata: {name: custom}",
      ""
    ].join("\n"));

    expect(result.documents[0].schema.status).toBe("unsupported");
    expect(result.documents[1].schema.status).toBe("schema-unavailable");
  });

  it("accepts an explicit null scalar in General YAML mode", () => {
    expect(analyzeYaml("null\n", "general").documents[0]).toMatchObject({
      rootType: "scalar",
      value: null,
      findings: []
    });
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

  it("reports selector mismatches with a path and correction", () => {
    const source = [
      "apiVersion: apps/v1",
      "kind: Deployment",
      "metadata:",
      "  name: mismatched",
      "spec:",
      "  selector:",
      "    matchLabels:",
      "      app: expected",
      "  template:",
      "    metadata:",
      "      labels:",
      "        app: actual",
      "    spec:",
      "      containers:",
      "        - name: app",
      "          image: example/app:1.0.0",
      ""
    ].join("\n");

    const finding = analyzeYaml(source).documents[0].findings.find((item) =>
      item.title === "Selector does not match Pod template labels");
    expect(finding).toMatchObject({
      level: "error",
      path: ".spec.selector.matchLabels",
      line: 7,
      column: 1
    });
    expect(finding.explanation).toContain("selector label");
    expect(finding.suggestion).toContain("template.metadata.labels");
  });

  it("does not reject a workload selector that uses matchExpressions", () => {
    const source = [
      "apiVersion: apps/v1",
      "kind: Deployment",
      "metadata: {name: expression-selector}",
      "spec:",
      "  selector:",
      "    matchExpressions:",
      "      - key: app",
      "        operator: In",
      "        values: [demo]",
      "  template:",
      "    metadata: {labels: {app: demo}}",
      "    spec:",
      "      containers: [{name: app, image: example/app:1.0.0}]",
      ""
    ].join("\n");

    const titles = analyzeYaml(source).documents[0].findings.map((item) => item.title);
    expect(titles).not.toContain("Workload has no selector terms");
  });

  it("checks Service selectors and named target ports across documents", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata:",
      "  name: app",
      "  labels:",
      "    app: demo",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: example/app:1.0.0",
      "      ports:",
      "        - name: web",
      "          containerPort: 8080",
      "---",
      "apiVersion: v1",
      "kind: Service",
      "metadata:",
      "  name: app",
      "spec:",
      "  selector:",
      "    app: demo",
      "  ports:",
      "    - port: 80",
      "      targetPort: http",
      ""
    ].join("\n");

    const service = analyzeYaml(source).documents[1];
    const targetPort = service.findings.find((item) => item.title === "Named targetPort is not exposed by the selected workload");
    expect(targetPort).toMatchObject({
      level: "warning",
      path: ".spec.ports[0].targetPort",
      line: 24,
      column: 1
    });
    expect(targetPort.suggestion).toContain("existing container port name");
  });

  it("reports a Service selector that matches no included workload", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: app, labels: {app: actual}}",
      "spec: {containers: [{name: app, image: example/app:1.0.0}]}",
      "---",
      "apiVersion: v1",
      "kind: Service",
      "metadata: {name: app}",
      "spec: {selector: {app: expected}, ports: [{port: 80}]}",
      ""
    ].join("\n");

    expect(analyzeYaml(source).documents[1].findings).toEqual(expect.arrayContaining([
      expect.objectContaining({
        title: "Service selector matches no workload in this file",
        path: ".spec.selector"
      })
    ]));
  });

  it("detects duplicate resource identities", () => {
    const source = [
      "apiVersion: v1",
      "kind: ConfigMap",
      "metadata: {name: duplicate, namespace: demo}",
      "---",
      "apiVersion: v1",
      "kind: ConfigMap",
      "metadata: {name: duplicate, namespace: demo}",
      ""
    ].join("\n");

    const finding = analyzeYaml(source).documents[1].findings[0];
    expect(finding).toMatchObject({
      level: "error",
      title: "Duplicate resource identity",
      path: ".metadata.name",
      line: 7
    });
    expect(finding.explanation).toContain("Document 1");
  });

  it("does not treat repeated generateName prefixes as duplicate identities", () => {
    const source = [
      "apiVersion: batch/v1",
      "kind: Job",
      "metadata: {generateName: worker-}",
      "spec: {template: {spec: {restartPolicy: Never, containers: [{name: worker, image: example/worker:1.0.0}]}}}",
      "---",
      "apiVersion: batch/v1",
      "kind: Job",
      "metadata: {generateName: worker-}",
      "spec: {template: {spec: {restartPolicy: Never, containers: [{name: worker, image: example/worker:1.0.0}]}}}",
      ""
    ].join("\n");

    const titles = analyzeYaml(source).documents[1].findings.map((item) => item.title);
    expect(titles).not.toContain("Duplicate resource identity");
  });

  it("reports host namespaces and container hardening paths", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: host-access}",
      "spec:",
      "  hostPID: true",
      "  hostIPC: true",
      "  containers:",
      "    - name: app",
      "      image: example/app:1.0.0",
      "      securityContext: {runAsUser: 1000}",
      ""
    ].join("\n");

    const findings = analyzeYaml(source).documents[0].findings;
    expect(findings).toEqual(expect.arrayContaining([
      expect.objectContaining({ title: "Host PID namespace enabled", path: ".spec.hostPID" }),
      expect.objectContaining({ title: "Host IPC namespace enabled", path: ".spec.hostIPC" }),
      expect.objectContaining({ title: "app: root filesystem is writable", path: ".spec.containers[0].securityContext.readOnlyRootFilesystem" })
    ]));
    expect(findings.map((item) => item.title)).not.toContain("app: non-root execution not required");
  });

  it("provides OWASP K01 remediation examples and cautions", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: hardening-guidance}",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: example/app:1.0.0",
      ""
    ].join("\n");

    const findings = analyzeYaml(source).documents[0].findings;
    const privilegeEscalation = findings.find((item) => item.title === "app: privilege escalation not disabled");
    expect(privilegeEscalation).toMatchObject({
      example: "securityContext:\n  allowPrivilegeEscalation: false",
      standard: {
        id: "K01:2025",
        title: "Insecure Workload Configurations"
      }
    });
    expect(privilegeEscalation.caution).toContain("setuid");

    const seccomp = findings.find((item) => item.title === "app: RuntimeDefault seccomp profile not required");
    expect(seccomp).toMatchObject({
      path: ".spec.containers[0].securityContext.seccompProfile.type",
      example: "securityContext:\n  seccompProfile:\n    type: RuntimeDefault"
    });
  });

  it("accepts an explicit RuntimeDefault seccomp profile", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: secured}",
      "spec:",
      "  securityContext:",
      "    seccompProfile: {type: RuntimeDefault}",
      "  containers:",
      "    - name: app",
      "      image: example/app:1.0.0",
      ""
    ].join("\n");

    const titles = analyzeYaml(source).documents[0].findings.map((item) => item.title);
    expect(titles).not.toContain("app: RuntimeDefault seccomp profile not required");
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
