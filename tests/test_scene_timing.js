const assert = require('node:assert/strict');
const test = require('node:test');
require('../static/js/scene_timing.js');

const calculate = globalThis.QuranSceneTiming.calculateDurationFromPlayhead;
const reflow = globalThis.QuranSceneTiming.reflowManualTimeline;
const readTimelineTime = globalThis.QuranSceneTiming.readTimelineTime;
const resumePlaybackTime = globalThis.QuranSceneTiming.resumePlaybackTime;
const canResumePlayback = globalThis.QuranSceneTiming.canResumePlayback;

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
