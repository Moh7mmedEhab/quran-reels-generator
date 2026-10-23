const assert = require('node:assert/strict');
const test = require('node:test');
require('../static/js/scene_timing.js');

const calculate = globalThis.QuranSceneTiming.calculateDurationFromPlayhead;
const reflow = globalThis.QuranSceneTiming.reflowManualTimeline;
const readTimelineTime = globalThis.QuranSceneTiming.readTimelineTime;
const resumePlaybackTime = globalThis.QuranSceneTiming.resumePlaybackTime;
const canResumePlayback = globalThis.QuranSceneTiming.canResumePlayback;
const isExplicitSeekTime = globalThis.QuranSceneTiming.isExplicitSeekTime;
const scenePageBounds = globalThis.QuranSceneTiming.scenePageBounds;
const sceneResizeBounds = globalThis.QuranSceneTiming.sceneResizeBounds;
const effectiveAudioDuration = globalThis.QuranSceneTiming.effectiveAudioDuration;
const splitQuranWords = globalThis.QuranSceneTiming.splitQuranWords;
const resizedSceneDuration = globalThis.QuranSceneTiming.resizedSceneDuration;

test('missing seek argument does not become an explicit seek to zero', () => {
  assert.equal(isExplicitSeekTime(null), false);
  assert.equal(isExplicitSeekTime(undefined), false);
  assert.equal(isExplicitSeekTime(''), false);
  assert.equal(isExplicitSeekTime(0), true);
  assert.equal(isExplicitSeekTime('2.5'), true);
});

test('scene page ranges expose up to six scenes and clamp at the final group', () => {
  assert.deepEqual(scenePageBounds(18, 0), {page:0, pageCount:3, start:0, end:6});
  assert.deepEqual(scenePageBounds(18, 2), {page:2, pageCount:3, start:12, end:18});
  assert.deepEqual(scenePageBounds(7, 99), {page:1, pageCount:2, start:6, end:7});
});

test('audio lock uses the trimmed selected range and not the untrimmed file duration', () => {
  assert.equal(effectiveAudioDuration({
    trimEnabled:true, trimStart:1.25, trimEnd:2.5, untrimmedDuration:10,
    effectiveDuration:10, baseDuration:10,
  }), 6.25);
  assert.equal(effectiveAudioDuration({
    trimEnabled:false, untrimmedDuration:10, effectiveDuration:6.25, baseDuration:10,
  }), 6.25);
  assert.equal(effectiveAudioDuration({trimEnabled:true, trimStart:2, trimEnd:1, baseDuration:10}), 7);
});

test('Uthmani hair spaces stay inside Quran word tokens', () => {
  assert.deepEqual(splitQuranWords('بَنِیۤ إِسۡرَ\u200aٰ\u2060ۤءِیلَ وَعَهْدٌ'), [
    'بَنِیۤ', 'إِسۡرَ\u200aٰ\u2060ۤءِیلَ', 'وَعَهْدٌ',
  ]);
});

test('drag resizing keeps positive durations and clamps scene end to the audio timeline', () => {
  assert.equal(resizedSceneDuration(2, -10, 12, 4), .01);
  assert.equal(resizedSceneDuration(2, 10, 12, 4), 8);
  assert.equal(resizedSceneDuration(2, 10, 10000, 0), 12);
});

test('locked resize reserves every later scene duration and marks its permitted boundary', () => {
  const scenes = [
    {scene_id:'scene-1', duration:4},
    {scene_id:'scene-2', duration:3},
    {scene_id:'scene-3', duration:3},
  ];
  const bounds = sceneResizeBounds(scenes, 0, 10);
  assert.equal(bounds.known, true);
  assert.equal(bounds.maxDuration, 4);
  assert.equal(bounds.timelineEnd, 10);
  assert.equal(resizedSceneDuration(4, 3, 10, 0, [3, 3], true), 4);
  assert.equal(resizedSceneDuration(3, 4, 10, 4, [3], true), 3);
});

test('unlocked resize may exceed audio while preserving all later scene lengths', () => {
  const scenes = [
    {scene_id:'scene-1', duration:4},
    {scene_id:'scene-2', duration:3},
    {scene_id:'scene-3', duration:3},
  ];
  const nextFirstDuration = resizedSceneDuration(4, 3, 10, 0, [3, 3], false);
  assert.equal(nextFirstDuration, 7);
  const timeline = reflow([
    {...scenes[0], duration:nextFirstDuration}, ...scenes.slice(1),
  ]);
  assert.deepEqual(timeline.map(scene => scene.duration), [7, 3, 3]);
  assert.deepEqual(timeline.map(scene => [scene.start_time, scene.end_time]), [[0, 7], [7, 10], [10, 13]]);
});

test('two scenes: subtract the selected scene start from the global playback time', () => {
  const result = calculate([
    {scene_id:'scene-1', duration:10},
    {scene_id:'scene-2', duration:4},
  ], 'scene-2', 17);
  assert.equal(result.sceneStart, 10);
  assert.equal(result.duration, 7);
});

test('a scene with no duration yet can be measured from committed earlier scenes', () => {
  const result = calculate([
    {scene_id:'scene-1', duration:10},
    {scene_id:'scene-2', duration:null},
  ], 'scene-2', 17);
  assert.equal(result.sceneStart, 10);
  assert.equal(result.duration, 7);
});

test('three scenes: sum every committed preceding scene', () => {
  const scenes = [
    {scene_id:'scene-1', duration:6},
    {scene_id:'scene-2', duration:4},
    {scene_id:'scene-3', duration:3},
  ];
  const timeline = reflow(scenes);
  const result = calculate(timeline, 'scene-3', 17);
  assert.equal(result.sceneStart, 10);
  assert.equal(result.duration, 7);
  assert.deepEqual(timeline.map(scene => [scene.start_time, scene.end_time]), [[0, 6], [6, 10], [10, 13]]);
});

test('changing an earlier duration reflows the next start and the next calculation', () => {
  let scenes = [
    {scene_id:'scene-1', duration:11},
    {scene_id:'scene-2', duration:7},
  ];
  scenes = reflow(scenes);
  assert.equal(scenes[1].duration, 7);
  const result = calculate(scenes, 'scene-2', 17);
  assert.equal(result.sceneStart, 11);
  assert.equal(result.duration, 6);
  assert.deepEqual(scenes.map(scene => [scene.start_time, scene.end_time]), [[0, 11], [11, 18]]);
  const applied = reflow([
    {...scenes[0]}, {...scenes[1], duration:result.duration},
  ]);
  assert.deepEqual(applied.map(scene => [scene.start_time, scene.end_time]), [[0, 11], [11, 17]]);
});

test('reject playback before the selected scene start', () => {
  assert.throws(() => calculate([
    {scene_id:'scene-1', duration:10}, {scene_id:'scene-2', duration:4},
  ], 'scene-2', 9), /before this scene starts/);
});

test('reject unavailable, zero and over-limit durations', () => {
  const scenes = [{scene_id:'scene-1', duration:10}];
  assert.throws(() => calculate(scenes, 'scene-1', NaN), /valid preview playback position/);
  assert.throws(() => calculate(scenes, 'scene-1', 0), /not passed this scene start/);
  assert.throws(() => calculate(scenes, 'scene-1', 3610), /3600-second scene limit/);
});

test('reject a scene when a previous duration is not committed', () => {
  assert.throws(() => calculate([
    {scene_id:'scene-1', duration:null}, {scene_id:'scene-2', duration:4},
  ], 'scene-2', 17), /no committed duration/);
});

test('audio-only preview uses its live currentTime as the selected reel timeline', () => {
  const audioPlayer = {src:'blob:recitation-range', currentTime:17, duration:24.7};
  assert.equal(readTimelineTime(audioPlayer, true), 17);
});

test('resuming the same preview source preserves the media position', () => {
  const audioPlayer = {src:'blob:recitation-range', currentTime:17.4, duration:24.7};
  assert.equal(resumePlaybackTime(audioPlayer, false), 17.4);
});

test('a changed preview source starts at the beginning', () => {
  const audioPlayer = {src:'blob:new-recitation-range', currentTime:17.4, duration:24.7};
  assert.equal(resumePlaybackTime(audioPlayer, true), 0);
});

test('a paused media element can resume while buffering for its current selection', () => {
  const audioPlayer = {src:'blob:recitation-range', currentTime:17.4, readyState:4, ended:false};
  assert.equal(canResumePlayback(audioPlayer, true), true);
  assert.equal(canResumePlayback(audioPlayer, false), false);
  assert.equal(canResumePlayback({...audioPlayer, readyState:1}, true), true);
  assert.equal(canResumePlayback({...audioPlayer, ended:true}, true), false);
});

test('reject playback clocks before playback starts or without valid duration', () => {
  const player = {src:'blob:recitation-range', currentTime:7, duration:24.7};
  assert.throws(() => readTimelineTime(player, false), /Play the recitation or rendered video first/);
  assert.throws(() => readTimelineTime({...player, duration:NaN}, true), /Play the recitation or rendered video first/);
});
