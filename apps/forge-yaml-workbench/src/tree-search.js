const SIMPLE_PATH_KEY = /^[A-Za-z_][A-Za-z0-9_]*$/;

export function childYamlPath(parentPath, key, parentIsArray = false) {
  if (parentIsArray) return `${parentPath}[${key}]`;
  const text = String(key);
  return SIMPLE_PATH_KEY.test(text)
    ? `${parentPath}.${text}`
    : `${parentPath}[${JSON.stringify(text)}]`;
}

export function buildTreeSearchIndex(documents) {
  const records = [];

  function visit(value, name, path, documentIndex, ancestorIds) {
    const id = `document-${documentIndex}:${path}`;
    const scalar = value === null || typeof value !== "object";
    records.push({
      id,
      documentIndex,
      name: String(name),
      path,
      valueText: scalar ? (value === null ? "null" : String(value)) : null,
      scalar,
      ancestorIds: [...ancestorIds]
    });

    if (!scalar) {
      const nextAncestors = [...ancestorIds, id];
      Object.entries(value).forEach(([key, item]) => {
        visit(item, key, childYamlPath(path, key, Array.isArray(value)), documentIndex, nextAncestors);
      });
    }
  }

  documents.forEach((document) => visit(document.raw, "root", "$", document.index, []));
  return records;
}

export function searchTreeIndex(records, query) {
  const normalized = String(query || "").trim().toLocaleLowerCase();
  if (!normalized) return [];

  return records.filter((record) => [record.name, record.valueText, record.path]
    .filter((value) => value !== null)
    .some((value) => value.toLocaleLowerCase().includes(normalized)));
}

export function matchingTextRanges(value, query) {
  const source = String(value);
  const normalized = String(query || "").trim().toLocaleLowerCase();
  if (!normalized) return [{ text: source, match: false }];

  const lower = source.toLocaleLowerCase();
  const ranges = [];
  let cursor = 0;
  let matchAt = lower.indexOf(normalized, cursor);
  while (matchAt !== -1) {
    if (matchAt > cursor) ranges.push({ text: source.slice(cursor, matchAt), match: false });
    ranges.push({ text: source.slice(matchAt, matchAt + normalized.length), match: true });
    cursor = matchAt + normalized.length;
    matchAt = lower.indexOf(normalized, cursor);
  }
  if (cursor < source.length) ranges.push({ text: source.slice(cursor), match: false });
  return ranges.length ? ranges : [{ text: source, match: false }];
}
