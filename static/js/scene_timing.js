(function attachSceneTiming(scope) {
  function isExplicitSeekTime(value) {
    return value !== null && value !== undefined && value !== ''
      && Number.isFinite(Number(value));
  }

  function splitQuranWords(value) {
    // U+200A HAIR SPACE joins orthographic fragments in some Uthmani words;
    // keep it inside the token so scene boundaries never split those words.
    return String(value ?? '').match(/\S+(?:\u200a+\S+)*/gu) || [];
  }

  function scenePageBounds(totalScenes, requestedPage = 0, pageSize = 6) {
    const count = Math.max(0, Math.floor(Number(totalScenes) || 0));
    const size = Math.max(1, Math.floor(Number(pageSize) || 6));
    const pageCount = Math.max(1, Math.ceil(count / size));
    const page = Math.max(0, Math.min(pageCount - 1, Math.floor(Number(requestedPage) || 0)));
    return {page, pageCount, start:page * size, end:Math.min(count, (page + 1) * size)};
  }

  function sceneResizeBounds(scenes, sceneIndex, timelineDuration) {
    if (!Array.isArray(scenes) || !Number.isInteger(Number(sceneIndex))) return {known:false};
    const index = Number(sceneIndex);
    if (index < 0 || index >= scenes.length) return {known:false};
    const durations = scenes.map(scene => {
      if (scene?.duration == null || scene.duration === '') return null;
      const duration = Number(scene.duration);
      return Number.isFinite(duration) && duration > 0 ? duration : null;
    });
    if (durations.slice(0, index).some(duration => duration == null)
        || durations.slice(index + 1).some(duration => duration == null)) {
      return {known:false, sceneIndex:index};
    }
    const sceneStart = durations.slice(0, index).reduce((sum, duration) => sum + duration, 0);
    const currentDuration = durations[index];
    const followingDuration = durations.slice(index + 1).reduce((sum, duration) => sum + duration, 0);
    const total = Number(timelineDuration);
    const maxDuration = Number.isFinite(total) && total > 0
      ? total - sceneStart - followingDuration : 3600;
    const timelineEnd = durations.reduce((sum, duration) => sum + (duration || 0), 0);
    return {
      known:true,
      sceneIndex:index,
      sceneStart:Number(sceneStart.toFixed(3)),
      currentDuration,
      followingDuration,
      maxDuration:Number(maxDuration.toFixed(3)),
      timelineEnd:Number(timelineEnd.toFixed(3)),
      overflow:Number.isFinite(total) && total > 0 ? Math.max(0, timelineEnd - total) : 0,
    };
  }

  function effectiveAudioDuration({trimEnabled = false, trimStart = 0, trimEnd = 0,
                                  untrimmedDuration, effectiveDuration, baseDuration} = {}) {
    const start = Math.max(0, Number(trimStart) || 0);
    const end = Math.max(0, Number(trimEnd) || 0);
    const untrimmed = Number(untrimmedDuration);
    const effective = Number(effectiveDuration);
    const base = Number(baseDuration);
    if (trimEnabled && Number.isFinite(untrimmed) && untrimmed > 0) {
      return Math.max(0, untrimmed - start - end);
    }
    if (Number.isFinite(effective) && effective > 0) return effective;
    if (Number.isFinite(base) && base > 0) return Math.max(0, base - (trimEnabled ? start + end : 0));
    if (Number.isFinite(untrimmed) && untrimmed > 0) return untrimmed;
    return NaN;
  }

  function resizedSceneDuration(startingDuration, deltaSeconds, timelineDuration, sceneStart,
                                followingDurations = [], locked = true) {
    const start = Math.max(0, Number(sceneStart) || 0);
    const total = Number(timelineDuration);
    const requested = Number(startingDuration) + Number(deltaSeconds);
    if (!Number.isFinite(requested)) return null;
    if (!locked) return Number(Math.max(.01, Math.min(3600, requested)).toFixed(2));
    const later = Array.isArray(followingDurations)
      ? followingDurations.map(Number) : [Number(followingDurations) || 0];
    if (later.some(duration => !Number.isFinite(duration) || duration <= 0)) {
      return Number(Math.max(.01, Math.min(Number(startingDuration), requested)).toFixed(2));
    }
    const trailing = later.reduce((sum, duration) => sum + duration, 0);
    const maximum = Number.isFinite(total) && total > 0
      ? Math.min(3600, total - start - trailing) : 3600;
    const current = Number(startingDuration);
    // An already-overfull timeline can be repaired by shortening this scene,
    // but a drag must not silently move it to a different boundary on pointerdown.
    if (maximum < .01 || current > maximum) {
      return Number(Math.max(.01, Math.min(current, requested)).toFixed(2));
    }
    return Number(Math.max(.01, Math.min(maximum, requested)).toFixed(2));
  }

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
    isExplicitSeekTime,
    splitQuranWords,
    scenePageBounds,
    sceneResizeBounds,
    effectiveAudioDuration,
    resizedSceneDuration,
    calculateDurationFromPlayhead, reflowManualTimeline, readTimelineTime, resumePlaybackTime,
    canResumePlayback,
  });
})(typeof window !== 'undefined' ? window : globalThis);
