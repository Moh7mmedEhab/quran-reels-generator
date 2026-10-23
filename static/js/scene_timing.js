(function attachSceneTiming(scope) {
  function resumePlaybackTime(player, sourceChanged) {
    if (sourceChanged) return 0;
    const currentTime = Number(player?.currentTime);
    return Number.isFinite(currentTime) && currentTime >= 0 ? currentTime : 0;
  }

  function canResumePlayback(player, selectionMatches) {
    // A paused media element can resume while it is buffering. Its source and
    // currentTime remain authoritative; waiting for HAVE_CURRENT_DATA here can
    // send Play through the preview initialization path unnecessarily.
    return Boolean(player?.src && selectionMatches && !player.ended);
  }

  function readTimelineTime(player, playbackStarted) {
    if (!playbackStarted || !player?.src
        || !Number.isFinite(Number(player.currentTime)) || Number(player.currentTime) < 0
        || !Number.isFinite(Number(player.duration)) || Number(player.duration) <= 0) {
      throw new Error('Play the recitation or rendered video first, then pause at the scene boundary.');
    }
    // Preview audio is served as the selected recitation range from t=0, the
    // same origin used by the rendered reel, so currentTime is already global.
    return Number(player.currentTime);
  }

  function reflowManualTimeline(scenes) {
    let cursor = 0;
    let positionKnown = true;
    return scenes.map(scene => {
      const duration = Number(scene.duration);
      if (!Number.isFinite(duration) || duration <= 0 || !positionKnown) {
        positionKnown = false;
        return {...scene, start_time:null, end_time:null};
      }
      const start_time = Number(cursor.toFixed(3));
      cursor += duration;
      return {...scene, start_time, end_time:Number(cursor.toFixed(3))};
    });
  }

  function calculateDurationFromPlayhead(scenes, sceneId, playbackTime) {
    if (!Array.isArray(scenes)) throw new Error('The scene timeline is unavailable.');
    const sceneIndex = scenes.findIndex(scene => String(scene.scene_id) === String(sceneId));
    if (sceneIndex < 0) throw new Error('The selected scene is no longer in the scene timeline.');

    const time = Number(playbackTime);
    if (!Number.isFinite(time) || time < 0) {
      throw new Error('A valid preview playback position is not available. Play the recitation or video first.');
    }

    let sceneStart = 0;
    for (const scene of scenes.slice(0, sceneIndex)) {
      const duration = Number(scene.duration);
      if (!Number.isFinite(duration) || duration <= 0) {
        throw new Error('An earlier scene has no committed duration. Apply or reset its timing first.');
      }
      sceneStart += duration;
    }

    if (time < sceneStart - .0005) {
      throw new Error(`Playback is at ${time.toFixed(1)}s, before this scene starts at ${sceneStart.toFixed(1)}s.`);
    }
    const duration = Math.round((time - sceneStart) * 1000) / 1000;
    if (duration <= 0) {
      throw new Error('Playback has not passed this scene start. Move the playhead to its end and try again.');
    }
    if (duration > 3600) {
      throw new Error('The calculated duration exceeds the supported 3600-second scene limit.');
    }
    return {sceneIndex, sceneStart, duration};
  }

  scope.QuranSceneTiming = Object.freeze({
    calculateDurationFromPlayhead, reflowManualTimeline, readTimelineTime, resumePlaybackTime,
    canResumePlayback,
  });
})(typeof window !== 'undefined' ? window : globalThis);
