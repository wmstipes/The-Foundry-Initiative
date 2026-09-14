function lines(source) {
  const normalized = String(source).replace(/\r\n?/g, "\n");
  if (!normalized) return [];
  const values = normalized.split("\n");
  if (normalized.endsWith("\n")) values.pop();
  return values;
}

function replacementRows(previous, next) {
  let prefix = 0;
  while (prefix < previous.length && prefix < next.length && previous[prefix] === next[prefix]) prefix += 1;

  let suffix = 0;
  while (suffix < previous.length - prefix && suffix < next.length - prefix &&
      previous[previous.length - suffix - 1] === next[next.length - suffix - 1]) suffix += 1;

  return [
    ...previous.slice(0, prefix).map((text, index) => ({
      type: "context", beforeNumber: index + 1, afterNumber: index + 1, text
    })),
    ...previous.slice(prefix, previous.length - suffix).map((text, index) => ({
      type: "removed", beforeNumber: prefix + index + 1, afterNumber: null, text
    })),
    ...next.slice(prefix, next.length - suffix).map((text, index) => ({
      type: "added", beforeNumber: null, afterNumber: prefix + index + 1, text
    })),
    ...previous.slice(previous.length - suffix).map((text, index) => ({
      type: "context",
      beforeNumber: previous.length - suffix + index + 1,
      afterNumber: next.length - suffix + index + 1,
      text
    }))
  ];
}

export function buildLineDiff(before, after) {
  const previousSource = String(before);
  const nextSource = String(after);
  const previous = lines(previousSource);
  const next = lines(nextSource);
  const metadata = {
    newlineChange: previousSource.endsWith("\n") === nextSource.endsWith("\n")
      ? null
      : (nextSource.endsWith("\n") ? "added" : "removed"),
    lineEndingsChanged: /\r/.test(previousSource) !== /\r/.test(nextSource)
  };
  const alignmentCells = previous.length * next.length;
  if (alignmentCells > 1_000_000) {
    const rows = replacementRows(previous, next);
    return {
      rows,
      added: rows.filter((row) => row.type === "added").length,
      removed: rows.filter((row) => row.type === "removed").length,
      simplified: true,
      ...metadata
    };
  }

  const matrix = Array.from({ length: previous.length + 1 }, () =>
    new Uint32Array(next.length + 1));

  for (let oldIndex = previous.length - 1; oldIndex >= 0; oldIndex -= 1) {
    for (let newIndex = next.length - 1; newIndex >= 0; newIndex -= 1) {
      matrix[oldIndex][newIndex] = previous[oldIndex] === next[newIndex]
        ? matrix[oldIndex + 1][newIndex + 1] + 1
        : Math.max(matrix[oldIndex + 1][newIndex], matrix[oldIndex][newIndex + 1]);
    }
  }

  const rows = [];
  let oldIndex = 0;
  let newIndex = 0;
  while (oldIndex < previous.length || newIndex < next.length) {
    if (oldIndex < previous.length && newIndex < next.length &&
        previous[oldIndex] === next[newIndex]) {
      rows.push({
        type: "context",
        beforeNumber: oldIndex + 1,
        afterNumber: newIndex + 1,
        text: previous[oldIndex]
      });
      oldIndex += 1;
      newIndex += 1;
    } else if (newIndex < next.length &&
        (oldIndex === previous.length ||
          matrix[oldIndex][newIndex + 1] > matrix[oldIndex + 1][newIndex])) {
      rows.push({
        type: "added",
        beforeNumber: null,
        afterNumber: newIndex + 1,
        text: next[newIndex]
      });
      newIndex += 1;
    } else {
      rows.push({
        type: "removed",
        beforeNumber: oldIndex + 1,
        afterNumber: null,
        text: previous[oldIndex]
      });
      oldIndex += 1;
    }
  }

  return {
    rows,
    added: rows.filter((row) => row.type === "added").length,
    removed: rows.filter((row) => row.type === "removed").length,
    simplified: false,
    ...metadata
  };
}
