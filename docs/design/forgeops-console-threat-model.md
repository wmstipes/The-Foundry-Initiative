# ForgeOps Console threat model

**Status:** Accepted ForgeOps Console C1 security boundary

## Assets to protect

- kubeconfig files, client certificates, private keys, bearer tokens, and
  external authentication material;
- the identity and permissions represented by the selected context;
- Kubernetes object data and application logs;
- the operator's understanding of which cluster and namespace are active;
- ForgeOps evidence integrity and authority boundaries; and
- the local workstation and browser session.

## Trust zones

| Zone | Trust decision |
| --- | --- |
| Browser UI | Unprivileged presentation client; never receives credentials or a raw Kubernetes client |
| Local core | Trusted credential and policy broker for one process lifetime |
| Built-in plugin | Reviewed code, but still constrained to declared SDK capabilities |
| Kubernetes API | Authoritative for authentication, authorization, and returned cluster data |
| Cluster objects and logs | Untrusted data that may contain hostile markup, terminal sequences, or sensitive values |
| Future exported artifact | Untrusted until its exact contract is validated by the intended offline consumer |

## Primary threats and required controls

### Credential disclosure

Threats include returning kubeconfig content to the browser, logging
credentials, serializing client configuration, exposing authentication errors
verbatim, or allowing a plugin to access the Kubernetes client.

Required controls:

- load credentials only inside the local core;
- expose context names and bounded display metadata, not credential fields;
- prohibit raw client, transport, configuration, and token handles in the SDK;
- apply structured error mapping before returning errors;
- exclude credential values from activity records and diagnostics; and
- test browser responses and logs for representative credential markers.

### Wrong-cluster or wrong-namespace action

The operator could mistake one context for another or retain a stale selection.

Required controls:

- show the exact context and namespace in the persistent application header;
- require an explicit context selection after every process start;
- never modify or silently inherit `current-context`;
- invalidate dependent selections when context or namespace changes;
- bind every request to the context-generation identifier active when the
  request was created; and
- reject responses from a superseded generation rather than displaying them
  under the new context.

### Excessive Kubernetes authority

A general proxy, arbitrary GVR request, or shell interface could turn a UI
feature into unrestricted cluster access.

Required controls:

- deny by default at the capability broker;
- map every capability to a fixed resource, subresource, verb, and bounded
  request shape;
- omit mutation, exec, attach, proxy, port-forward, and Secret capabilities
  from v0.1;
- use authorization review only as UI guidance and still rely on the API
  server's final decision;
- do not expose a raw URL, verb, JSON patch, command, or shell field; and
- test every unknown capability and parameter as a rejection.

### Malicious or compromised plugin

A plugin could attempt to bypass policy, exfiltrate data, impersonate another
plugin, or destabilize the process.

Required controls:

- ship only reviewed first-party plugins in the initial executable;
- reject duplicate identities, unknown manifest fields, incompatible SDK
  versions, and undeclared contributions;
- resolve all Kubernetes work through the broker rather than plugin-owned
  clients;
- namespace routes, settings, and activity records by plugin identity;
- bound plugin calls with timeouts, cancellation, size limits, and error
  isolation; and
- prohibit runtime downloads, remote modules, user-supplied JavaScript, and
  third-party installation in v0.1.

### Browser attacks and loopback abuse

A hostile webpage could attempt cross-origin loopback requests, DNS rebinding,
CSRF, or unauthorized WebSocket connections.

Required controls:

- bind only to loopback addresses;
- serve UI and API from one origin;
- reject unexpected `Host` and `Origin` values;
- disable permissive CORS;
- require an unguessable process-session nonce for API and stream setup;
- use restrictive CSP, frame, content-type, and referrer headers; and
- avoid placing credentials, cluster data, or sensitive query values in URLs.

### Untrusted cluster content

Object fields, annotations, Events, and logs can contain HTML, control
characters, huge values, misleading text, or credential material.

Required controls:

- render data as text, never trusted HTML;
- strip or visibly encode unsafe control characters;
- enforce item, byte, line, and time bounds before browser delivery;
- do not automatically turn log or annotation text into commands, links, or
  diagnoses;
- keep logs in memory and require explicit review before any future export; and
- omit Secrets and ConfigMap values from the initial surface.

### Command confusion

An equivalent command could be mistaken for the operation actually performed
or copied with unsafe quoting.

Required controls:

- label commands as explanatory previews;
- generate them only from validated structured selections;
- use platform-appropriate deterministic quoting;
- show when no exact `kubectl` equivalent exists;
- never pass preview text to a shell; and
- record the capability identity separately from the preview string.

### Evidence overclaim or cross-contract confusion

UI selections could be presented as authenticated evidence, complete cluster
health, or input compatible with ForgeOps when no such contract exists.

Required controls:

- keep browser activity records distinct from ForgeOps evidence;
- define a new artifact boundary before any export enters ForgeOps;
- require explicit selection and review rather than background capture;
- preserve context, collection time, capability, limits, and missing evidence;
- validate an exported contract independently; and
- retain the existing limits on authenticity, causation, severity, impact,
  applicability, and remediation authority.

## Security acceptance required before live use

A later implementation cannot connect to SignalForge until tests prove:

- no credential-bearing field reaches browser responses, diagnostics, or
  activity records;
- absent or invalid explicit kubeconfig input fails closed;
- ambient kubeconfig and in-cluster authentication are not used;
- unknown resources, operations, parameters, and plugin capabilities fail
  closed;
- context changes cancel or invalidate outstanding results;
- cross-origin, invalid-host, and missing-session requests are rejected;
- response, stream, and concurrency limits are enforced; and
- no mutation, Secret, exec, attach, proxy, or port-forward path exists.

Passing these tests establishes only the reviewed implementation boundary. It
does not prove that a kubeconfig is safe, that RBAC is least privilege, that
cluster data contains no sensitive text, or that every browser and local-host
attack is prevented.
