export const OWASP_PROFILE_VERSION = "2025";
export const OWASP_SOURCE_COMMIT = "828cfa2e2d7af63cdf7025c09ca871265d71f59c";

const sourceUrl = (slug) =>
  "https://github.com/OWASP/www-project-kubernetes-top-ten/blob/" +
  OWASP_SOURCE_COMMIT + "/2025/en/src/" + slug + ".md";

export const OWASP_STANDARDS = {
  K01: { id: "K01:2025", title: "Insecure Workload Configurations", url: sourceUrl("K01-Insecure-Workload-Configurations") },
  K02: { id: "K02:2025", title: "Overly Permissive Authorization Configurations", url: sourceUrl("K02-Overly-Permissive-Authorization-Configurations") },
  K03: { id: "K03:2025", title: "Secrets Management Failures", url: sourceUrl("K03-Secrets-Management-Failures") },
  K04: { id: "K04:2025", title: "Lack of Cluster-Level Policy Enforcement", url: sourceUrl("K04-Lack-Of-Cluster-Level-Policy-Enforcement") },
  K05: { id: "K05:2025", title: "Missing Network Segmentation Controls", url: sourceUrl("K05-Missing-Network-Segmentation-Controls") },
  K06: { id: "K06:2025", title: "Overly Exposed Kubernetes Components", url: sourceUrl("K06-Overly-Exposed-Kubernetes-Components") },
  K07: { id: "K07:2025", title: "Misconfigured and Vulnerable Cluster Components", url: sourceUrl("K07-Misconfigured-And-Vulnerable-Cluster-Components") },
  K08: { id: "K08:2025", title: "Cluster-to-Cloud Lateral Movement", url: sourceUrl("K08-Cluster-To-Cloud-Lateral-Movement") },
  K09: { id: "K09:2025", title: "Broken Authentication Mechanisms", url: sourceUrl("K09-Broken-Authentication-Mechanisms") },
  K10: { id: "K10:2025", title: "Inadequate Logging and Monitoring", url: sourceUrl("K10-Inadequate-Logging-And-Monitoring") }
};

const PROFILE = [
  ["K01", "direct", "Workload securityContext, host namespaces, HostPath, resources, and ServiceAccount-token settings are directly reviewable in the supplied YAML."],
  ["K02", "partial", "RBAC rules and bindings in the supplied YAML are reviewable; effective permissions, aggregation, and identities require cluster context."],
  ["K03", "partial", "Secret-backed environment injection and literal cloud credentials in the supplied YAML are reviewable; storage encryption, repositories, images, rotation, and logs are not."],
  ["K04", "partial", "Namespace Pod Security Admission labels and policy resources in the supplied YAML are visible; installed admission configuration and enforcement require cluster context."],
  ["K05", "partial", "NetworkPolicy resources in the supplied YAML are visible; effective namespace-wide segmentation and CNI enforcement require cluster context."],
  ["K06", "partial", "NodePort, LoadBalancer, and Ingress declarations are reviewable; actual reachability, firewalls, and control-plane exposure require cluster context."],
  ["K07", "cluster-context-required", "Component versions, flags, patch status, and runtime vulnerability state are not established by workload YAML."],
  ["K08", "partial", "Literal cloud credential environment variables are reviewable; node IAM, workload identity, metadata-service access, and cloud policy require cluster and cloud context."],
  ["K09", "partial", "Automatic ServiceAccount-token mounting is reviewable; user authentication, API anonymous access, MFA, and token lifetime require cluster or identity-provider context."],
  ["K10", "cluster-context-required", "Audit policy, log collection, alert delivery, retention, and monitoring health require live cluster and observability context."]
];

function findingStandardIds(finding) {
  return [finding.standard, ...(finding.standards || [])]
    .filter(Boolean)
    .map((standard) => standard.id);
}

export function buildOwaspProfile(documents) {
  const findings = documents.flatMap((document) => document.findings);
  const resourceKinds = new Map();
  documents.forEach((document) => resourceKinds.set(document.kind, (resourceKinds.get(document.kind) || 0) + 1));

  return PROFILE.map(([key, coverage, boundary]) => {
    const standard = OWASP_STANDARDS[key];
    const findingCount = findings.filter((finding) => findingStandardIds(finding).includes(standard.id)).length;
    const resourceEvidence = key === "K05" ? (resourceKinds.get("NetworkPolicy") || 0) :
      (key === "K04" ? documents.filter((document) =>
        ["ValidatingAdmissionPolicy", "ValidatingWebhookConfiguration"].includes(document.kind) ||
        (document.kind === "Namespace" && document.raw.metadata?.labels?.["pod-security.kubernetes.io/enforce"])
      ).length : 0);
    const evidenceCount = findingCount + resourceEvidence;
    return {
      ...standard,
      coverage,
      evidenceCount,
      evidence: evidenceCount
        ? evidenceCount + " matching manifest-local signal" + (evidenceCount === 1 ? "" : "s") + " in this file."
        : "No matching manifest-local signal in this file; this is not a pass result.",
      boundary
    };
  });
}
