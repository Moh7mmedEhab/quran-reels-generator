(function (root) {
  function groupByAyah(scenes) {
    const groups = new Map();
    for (const scene of scenes || []) {
      const number = Number(scene.ayah_number);
      if (!groups.has(number)) groups.set(number, []);
      groups.get(number).push(scene);
    }
    return groups;
  }

  function textPlan(scenes) {
    return JSON.stringify((scenes || []).map(scene => [Number(scene.ayah_number), String(scene.text || '').trim()]));
  }

  function replaceSplitAyahs(currentScenes, proposedScenes, splitAyahs) {
    const split = new Set((splitAyahs || []).map(Number));
    const currentGroups = groupByAyah(currentScenes);
    const proposedGroups = groupByAyah(proposedScenes);
    const ayahOrder = [...currentGroups.keys()];
    for (const number of proposedGroups.keys()) if (!ayahOrder.includes(number)) ayahOrder.push(number);

    const replacements = new Map();
    let preservedSettings = 0;
    for (const number of split) {
      const proposed = proposedGroups.get(number) || [];
      const previous = [...(currentGroups.get(number) || [])];
      const used = new Set();
      replacements.set(number, proposed.map(scene => {
        const row = {...scene};
        const oldIndex = previous.findIndex((old, index) => !used.has(index)
          && String(old.text || '').trim() === String(scene.text || '').trim());
        if (oldIndex >= 0) {
          used.add(oldIndex);
          const old = previous[oldIndex];
          if (old.manual_duration != null && Number.isFinite(Number(old.manual_duration))) {
            row.manual_duration = Number(old.manual_duration);
            preservedSettings++;
          }
          if (old.locked) {
            row.locked = true;
            preservedSettings++;
          }
        }
        return row;
      }));
    }

    const scenes = [];
    for (const number of ayahOrder) {
      const group = split.has(number) ? (replacements.get(number) || []) : (currentGroups.get(number) || []);
      group.forEach((scene, index) => scenes.push({
        ...scene,
        scene_index:scenes.length,
        segment_index:index + 1,
        segment_count:group.length,
      }));
    }
    const changed = [...split].some(number => textPlan(currentGroups.get(number)) !== textPlan(replacements.get(number)));
    return {scenes, changed, preservedSettings};
  }

  root.QuranAutoSplit = Object.freeze({replaceSplitAyahs, textPlan});
})(typeof window !== 'undefined' ? window : globalThis);
