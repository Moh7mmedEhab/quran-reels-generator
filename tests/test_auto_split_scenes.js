const test = require('node:test');
const assert = require('node:assert/strict');
require('../static/js/auto_split_scenes.js');

const autoSplit = globalThis.QuranAutoSplit;

test('auto split replaces only selected ayahs and preserves exact chunk settings', () => {
  const current = [
    {scene_id:'ayah-1-word-0', ayah_number:1, text:'short ayah', locked:false},
    {scene_id:'ayah-2-word-0', ayah_number:2, text:'one two three', locked:true, manual_duration:4.25},
    {scene_id:'ayah-2-word-3', ayah_number:2, text:'four five six', locked:false},
  ];
  const proposed = [
    {scene_id:'ayah-2-word-0', ayah_number:2, text:'one two three', locked:false},
    {scene_id:'ayah-2-word-3', ayah_number:2, text:'four five', locked:false},
    {scene_id:'ayah-2-word-5', ayah_number:2, text:'six', locked:false},
  ];

  const result = autoSplit.replaceSplitAyahs(current, proposed, [2]);
  assert.deepEqual(result.scenes.map(scene => scene.text), ['short ayah', 'one two three', 'four five', 'six']);
  assert.equal(result.scenes[1].manual_duration, 4.25);
  assert.equal(result.scenes[1].locked, true);
  assert.equal(result.preservedSettings, 2);
  assert.equal(result.changed, true);
});

test('running the same split twice is idempotent and does not append duplicate scenes', () => {
  const split = [
    {scene_id:'ayah-7-word-0', ayah_number:7, text:'one two three'},
    {scene_id:'ayah-7-word-3', ayah_number:7, text:'four five six'},
  ];
  const result = autoSplit.replaceSplitAyahs(split, split, [7]);
  assert.equal(result.changed, false);
  assert.deepEqual(result.scenes.map(scene => scene.text), ['one two three', 'four five six']);
  assert.equal(result.scenes.length, 2);
});
