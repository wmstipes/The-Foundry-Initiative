import { describe, expect, it } from "vitest";
import {
  KUBERNETES_SCHEMA_VERSION,
  SUPPORTED_SCHEMA_RESOURCES,
  validateKubernetesResource
} from "./schema-validation.js";

describe("pinned Kubernetes schema validation", () => {
  it("pins one Kubernetes version and an explicit supported set", () => {
    expect(KUBERNETES_SCHEMA_VERSION).toBe("v1.36.4");
    expect(SUPPORTED_SCHEMA_RESOURCES).toContain("v1|Pod");
    expect(SUPPORTED_SCHEMA_RESOURCES).toContain("apps/v1|Deployment");
    expect(SUPPORTED_SCHEMA_RESOURCES).toHaveLength(12);
  });

  it("loads every precompiled schema in the explicit support set", () => {
    for (const key of SUPPORTED_SCHEMA_RESOURCES) {
      const [apiVersion, kind] = key.split("|");
      expect(() => validateKubernetesResource({ apiVersion, kind })).not.toThrow();
    }
  });

  it("accepts a supported resource that matches the pinned schema", () => {
    const result = validateKubernetesResource({
      apiVersion: "v1",
      kind: "Service",
      metadata: { name: "web" },
      spec: { selector: { app: "web" }, ports: [{ port: 80, targetPort: "http" }] }
    });

    expect(result.status).toBe("valid");
    expect(result.errors).toEqual([]);
  });

  it("reports schema paths for wrong types and unknown fields", () => {
    const result = validateKubernetesResource({
      apiVersion: "apps/v1",
      kind: "Deployment",
      metadata: { name: "web" },
      spec: { replicas: "three", mysteryField: true }
    });

    expect(result.status).toBe("invalid");
    expect(result.errors).toEqual(expect.arrayContaining([
      expect.objectContaining({ path: ".spec.replicas", keyword: "type" }),
      expect.objectContaining({ path: ".spec.mysteryField", keyword: "additionalProperties" })
    ]));
  });

  it("preserves Kubernetes IntOrString behavior", () => {
    const numeric = validateKubernetesResource({
      apiVersion: "v1",
      kind: "Service",
      metadata: { name: "web" },
      spec: { ports: [{ port: 80, targetPort: 8080 }] }
    });
    expect(numeric.status).toBe("valid");
  });

  it("does not classify unsupported built-ins as valid or invalid", () => {
    const result = validateKubernetesResource({ apiVersion: "networking.k8s.io/v1", kind: "Ingress" });
    expect(result.status).toBe("unsupported");
    expect(result.message).toContain("No bundled v1.36.4 schema supports");
  });

  it("reports custom-resource schemas as unavailable", () => {
    const result = validateKubernetesResource({ apiVersion: "database.example.com/v1", kind: "Database" });
    expect(result.status).toBe("schema-unavailable");
    expect(result.message).toContain("CRD schema unavailable");
  });

  it("does not evaluate resources without a complete identity", () => {
    const result = validateKubernetesResource({ kind: "Pod", metadata: { name: "missing-version" } });
    expect(result.status).toBe("not-evaluated");
  });
});
