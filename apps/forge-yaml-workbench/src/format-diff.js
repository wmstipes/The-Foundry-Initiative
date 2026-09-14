function lines(source) {
  const normalized = String(source).replace(/\r\n?/g, "\n");
  const values = normalized.split("\n");
  if (normalized.endsWith("\n")) values.pop();
  return values;
}

export function buildLineDiff(before, after) {
  const previous = lines(before);
  const next = lines(after);
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
          matrix[oldIndex][newIndex + 1] >= matrix[oldIndex + 1][newIndex])) {
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
    removed: rows.filter((row) => row.type === "removed").length
  };
}
