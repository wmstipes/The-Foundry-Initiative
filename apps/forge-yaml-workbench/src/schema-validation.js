import Ajv from "ajv";
import schemaBundle from "./schema/kubernetes-v1.36.4.json" with { type: "json" };

export const KUBERNETES_SCHEMA_VERSION = schemaBundle.kubernetesVersion;
export const SUPPORTED_SCHEMA_RESOURCES = Object.freeze(Object.keys(schemaBundle.supportedResources));

const SCHEMA_ID = `https://signalforge.local/schemas/kubernetes/${KUBERNETES_SCHEMA_VERSION}`;
const ajv = new Ajv({ allErrors: true, strict: false, validateFormats: false });
ajv.addSchema({ $id: SCHEMA_ID, definitions: schemaBundle.definitions }, SCHEMA_ID);

const validators = new Map();

function resourceKey(apiVersion, kind) {
  return `${apiVersion}|${kind}`;
}

function apiGroup(apiVersion) {
  if (typeof apiVersion !== "string" || !apiVersion) return null;
  const slash = apiVersion.indexOf("/");
  return slash < 0 ? "" : apiVersion.slice(0, slash);
}

function decodePointerSegment(segment) {
  return segment.replace(/~1/g, "/").replace(/~0/g, "~");
}

function pointerPath(pointer = "") {
  if (!pointer) return "";
  return pointer.split("/").slice(1).map(decodePointerSegment).map((segment) =>
    /^\d+$/.test(segment) ? `[${segment}]` : `.${segment}`).join("");
}

function errorPath(error) {
  const base = pointerPath(error.instancePath);
  if (error.keyword === "required") return `${base}.${error.params.missingProperty}`;
  if (error.keyword === "additionalProperties") return `${base}.${error.params.additionalProperty}`;
  return base || ".";
}

function describeError(error) {
  if (error.keyword === "required") return `Required field ${error.params.missingProperty} is missing.`;
  if (error.keyword === "additionalProperties") return `Field ${error.params.additionalProperty} is not defined by this Kubernetes schema.`;
  if (error.keyword === "type") return `Expected ${error.params.type}, but received a different value type.`;
  if (error.keyword === "enum") return `Value must be one of: ${error.params.allowedValues.join(", ")}.`;
  return error.message ? error.message.charAt(0).toUpperCase() + error.message.slice(1) + "." : "The value does not match the schema.";
}

function validatorFor(definitionName) {
  if (!validators.has(definitionName)) {
    validators.set(definitionName, ajv.compile({ $ref: `${SCHEMA_ID}#/definitions/${definitionName}` }));
  }
  return validators.get(definitionName);
}

export function validateKubernetesResource(resource) {
  const apiVersion = resource?.apiVersion;
  const kind = resource?.kind;
  const base = { kubernetesVersion: KUBERNETES_SCHEMA_VERSION, apiVersion, kind, errors: [] };

  if (typeof apiVersion !== "string" || typeof kind !== "string" || !apiVersion || !kind) {
    return {
      ...base,
      status: "not-evaluated",
      message: "Schema validation was not run because apiVersion and kind are both required to select a schema."
    };
  }

  const key = resourceKey(apiVersion, kind);
  const definitionName = schemaBundle.supportedResources[key];
  if (!definitionName) {
    const group = apiGroup(apiVersion);
    if (group && !schemaBundle.builtInGroups.includes(group)) {
      return {
        ...base,
        status: "schema-unavailable",
        message: `CRD schema unavailable for ${apiVersion} ${kind}; no custom-resource schemas are bundled.`
      };
    }
    return {
      ...base,
      status: "unsupported",
      message: `No bundled ${KUBERNETES_SCHEMA_VERSION} schema supports ${apiVersion} ${kind}.`
    };
  }

  const validate = validatorFor(definitionName);
  if (validate(resource)) {
    return {
      ...base,
      status: "valid",
      message: `Matches the bundled Kubernetes ${KUBERNETES_SCHEMA_VERSION} schema.`
    };
  }

  return {
    ...base,
    status: "invalid",
    message: `Does not match the bundled Kubernetes ${KUBERNETES_SCHEMA_VERSION} schema.`,
    errors: (validate.errors || []).map((error) => ({
      level: "error",
      title: "Schema mismatch",
      path: errorPath(error),
      explanation: describeError(error),
      keyword: error.keyword
    }))
  };
}
