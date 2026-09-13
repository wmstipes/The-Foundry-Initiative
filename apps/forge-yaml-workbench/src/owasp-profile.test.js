import { describe, expect, it } from "vitest";
import { analyzeYaml } from "./analyze.js";
import { OWASP_SOURCE_COMMIT } from "./owasp-profile.js";

describe("OWASP Kubernetes Top 10:2025 review profile", () => {
  it("pins all ten categories and labels the browser-local coverage boundary", () => {
    const profile = analyzeYaml("apiVersion: v1\nkind: ConfigMap\nmetadata: {name: profile}\n").owaspProfile;

    expect(profile).toHaveLength(10);
    expect(profile.map((item) => [item.id, item.coverage])).toEqual([
      ["K01:2025", "direct"],
      ["K02:2025", "partial"],
      ["K03:2025", "partial"],
      ["K04:2025", "partial"],
      ["K05:2025", "partial"],
      ["K06:2025", "partial"],
      ["K07:2025", "cluster-context-required"],
      ["K08:2025", "partial"],
      ["K09:2025", "partial"],
      ["K10:2025", "cluster-context-required"]
    ]);
    expect(profile.every((item) => item.url.includes(OWASP_SOURCE_COMMIT))).toBe(true);
    expect(profile.every((item) => item.evidence.includes("not a pass result"))).toBe(true);
  });

  it("counts manifest-local signals without converting coverage into a score", () => {
    const source = [
      "apiVersion: v1",
      "kind: Pod",
      "metadata: {name: cloud-app}",
      "spec:",
      "  containers:",
      "    - name: app",
      "      image: example/app:1.0.0",
      "      env:",
      "        - name: AWS_SECRET_ACCESS_KEY",
      "          value: exposed",
      "---",
      "apiVersion: networking.k8s.io/v1",
      "kind: NetworkPolicy",
      "metadata: {name: default-deny}",
      "spec: {podSelector: {}, policyTypes: [Ingress, Egress]}",
      ""
    ].join("\n");
    const profile = analyzeYaml(source).owaspProfile;

    expect(profile.find((item) => item.id === "K05:2025").evidenceCount).toBe(1);
    expect(profile.find((item) => item.id === "K08:2025").evidenceCount).toBe(1);
    expect(profile.find((item) => item.id === "K10:2025").evidenceCount).toBe(0);
  });

  it("does not create an OWASP profile in General YAML mode", () => {
    expect(analyzeYaml("kind: Pod\n", "general").owaspProfile).toEqual([]);
  });
});
