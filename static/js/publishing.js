(() => {
  const $ = (id) => document.getElementById(id);
  let selectedRenderJobId = null;
  let lastRenderedPublishMetadata = null;
  let publisherCsrfToken = '';
  let publisherState = null;
  let publishingPollTimer = null;
  const activeUploadStates = new Set(['queued','initializing','uploading','processing','cancelling']);
  const uploadStateLabels = {
    queued:'Queued', initializing:'Preparing upload', uploading:'Uploading', processing:'Processing on platform',
    cancelling:'Cancelling upload', waiting_user:'Draft ready · action needed in TikTok', published:'Published', available:'Processed and available',
    failed:'Failed · retry available', cancelled:'Cancelled', uploaded:'Uploaded',
  };

  function setPublishMetadata(metadata) {
    $('publish-yt-title').value = metadata.title || '';
    $('publish-yt-description').value = metadata.description || '';
    $('publish-yt-tags').value = Array.isArray(metadata.tags) ? metadata.tags.join(', ') : '';
    $('publish-hashtags').value = Array.isArray(metadata.hashtags) ? metadata.hashtags.join(' ') : '';
    $('publish-tt-caption').value = metadata.caption || '';
    updateTikTokCaptionCount();
  }

  function selectedHashtags() {
    const values = $('publish-hashtags').value.split(/[\s,]+/).map(value => value.trim())
      .filter(value => /^#[\p{L}\p{M}\p{N}_]+$/u.test(value));
    return [...new Map(values.map(value => [value.toLocaleLowerCase(), value])).values()];
  }

  function appendHashtags(text, hashtags) {
    const present = new Set([...String(text || '').matchAll(/#[\p{L}\p{M}\p{N}_]+/gu)].map(match => match[0].toLocaleLowerCase()));
    const missing = hashtags.filter(tag => !present.has(tag.toLocaleLowerCase()));
    return missing.length ? `${String(text || '').trim()}\n\n${missing.join(' ')}`.trim() : String(text || '');
  }

  function publishConnectUrl(platform) {
    const url = new URL(`/api/publishing/${platform}/connect`, window.location.origin);
    if (selectedRenderJobId) url.searchParams.set('render_job_id', selectedRenderJobId);
    return url.pathname + url.search;
  }

  function updateTikTokCaptionCount() {
    const finalCaption = appendHashtags($('publish-tt-caption').value, selectedHashtags());
    const length = finalCaption.length;
    const over = length > 2200;
    $('tiktok-caption-count').textContent = `${length.toLocaleString()} / 2,200 UTF-16 characters${over ? ' · shorten before upload' : ''}`;
    $('tiktok-caption-count').classList.toggle('text-red-700', over);
    $('tiktok-caption-count').classList.toggle('text-gray-500', !over);
    $('tiktok-final-caption-preview').textContent = finalCaption ? `Final caption preview:\n${finalCaption}` : '';
    const entry = publisherState?.providers?.tiktok;
    const providerReady = $('publish-tt-mode').value === 'direct'
      ? entry?.direct_post_ready : entry?.ready;
    $('tiktok-upload-btn').disabled = !(selectedRenderJobId && lastRenderedPublishMetadata
      && providerReady && !over);
  }

  function setAccountCard(platform, entry) {
    const connected = Boolean(entry?.connected);
    const ready = Boolean(entry?.ready);
    $(`${platform}-account-status`).textContent = ready ? 'Ready to Upload'
      : connected ? 'Connected · setup needed' : 'Not connected';
    $(`${platform}-account-status`).className = ready ? 'text-[10px] font-semibold text-emerald-700'
      : connected ? 'text-[10px] font-semibold text-amber-700' : 'text-[10px] text-gray-500';
    const account = entry?.account || {};
    $(`${platform}-account-detail`).textContent = connected
      ? `${account.display_name || (platform === 'youtube' ? 'YouTube channel' : 'TikTok account')}${account.external_id ? ` · ${account.external_id}` : ''}`
      : 'Connect an account to make this destination available.';
    const messages = [];
    if (account.unreadable) messages.push('Stored credentials could not be decrypted. Reconnect this account with the current encryption key.');
    if (!entry?.configured && entry?.setup_message) messages.push(entry.setup_message);
    if (entry?.credential_message) messages.push(entry.credential_message);
    if (entry?.missing_scopes?.length) messages.push(`Reconnect to grant: ${entry.missing_scopes.join(', ')}.`);
    if (entry?.direct_missing_scopes?.length && $('publish-tt-mode')?.value === 'direct') {
      messages.push(`Direct publishing requires: ${entry.direct_missing_scopes.join(', ')}.`);
    }
    $(`${platform}-account-setup`).textContent = messages.join(' ');
    const connect = $(`${platform}-connect-btn`);
    connect.hidden = false;
    connect.textContent = connected ? (ready ? 'Reconnect Account' : 'Reconnect to Enable Upload') : 'Connect Account';
    connect.disabled = !entry?.configured;
    $(`${platform}-disconnect-btn`).classList.toggle('hidden', !connected);
    if (platform === 'tiktok') {
      const directOption = $('publish-tt-direct-option');
      const directReady = Boolean(entry?.direct_post_ready);
      directOption.hidden = !directReady;
      directOption.disabled = !directReady;
      if (!directReady && $('publish-tt-mode').value === 'direct') $('publish-tt-mode').value = 'draft';
      $('tiktok-upload-btn').textContent = $('publish-tt-mode').value === 'direct' ? 'Publish directly to TikTok' : 'Upload to TikTok';
    }
    const hasRender = Boolean(selectedRenderJobId && lastRenderedPublishMetadata);
    const latest = (publisherState?.uploads || []).find(upload => upload.platform === platform && upload.render_job_id === selectedRenderJobId);
    const retry = latest?.status === 'failed';
    const button = $(platform === 'youtube' ? 'youtube-upload-btn' : 'tiktok-upload-btn');
    if (retry) button.textContent = platform === 'youtube' ? 'Retry YouTube upload' : 'Retry TikTok upload';
    else if (platform === 'youtube') button.textContent = 'Upload to YouTube';
    else button.textContent = $('publish-tt-mode').value === 'direct' ? 'Publish directly to TikTok' : 'Upload to TikTok';
    if (platform === 'youtube') {
      button.disabled = !(ready && hasRender && !activeUploadStates.has(latest?.status));
    } else {
      const modeReady = $('publish-tt-mode').value === 'direct' ? entry?.direct_post_ready : ready;
      button.disabled = !(modeReady
        && hasRender && !activeUploadStates.has(latest?.status)
        && appendHashtags($('publish-tt-caption').value, selectedHashtags()).length <= 2200);
    }
    const both = Boolean(publisherState?.providers?.youtube?.ready
      && publisherState?.providers?.tiktok?.ready && hasRender);
    $('upload-both-btn').disabled = !both;
  }

  function displayUpload(upload) {
    const platform = upload.platform;
    if (!['youtube','tiktok'].includes(platform)) return;
    const message = upload.message || uploadStateLabels[upload.status] || 'Upload status updated.';
    $(`${platform}-upload-message`).textContent = `${uploadStateLabels[upload.status] || upload.status} · ${message}`;
    $(`${platform}-upload-progress`).value = Math.max(0, Math.min(100, Number(upload.progress || 0)));
    const linkBox = $(`${platform}-upload-link`); linkBox.replaceChildren();
    if (upload.result_url && /^https:\/\//i.test(upload.result_url)) {
      const link = document.createElement('a'); link.href = upload.result_url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.className = 'mt-1 inline-block font-semibold underline';
      link.textContent = platform === 'youtube' ? 'View on YouTube' : 'View on TikTok';
      linkBox.append(link);
    }
    if (['processing','waiting_user','uploaded'].includes(upload.status)) {
      const refresh = document.createElement('button'); refresh.type = 'button'; refresh.className = 'mt-1 ml-2 underline';
      refresh.textContent = 'Refresh status'; refresh.addEventListener('click', () => refreshUpload(upload.id, refresh));
      linkBox.append(refresh);
    }
    if (platform === 'youtube' && ['queued','initializing','uploading'].includes(upload.status)) {
      const cancel = document.createElement('button'); cancel.type = 'button'; cancel.className = 'mt-1 ml-2 underline';
      cancel.textContent = 'Cancel upload'; cancel.addEventListener('click', async () => {
        cancel.disabled = true;
        try {
          const response = await fetch(`/api/publishing/uploads/${encodeURIComponent(upload.id)}/cancel`, {
            method:'POST', headers:{'X-Publisher-CSRF':publisherCsrfToken},
          });
          const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Could not cancel upload.');
          await loadPublishingState();
        } catch (error) { $('youtube-upload-message').textContent = error.message; }
        finally { cancel.disabled = false; }
      });
      linkBox.append(cancel);
    }
    setAccountCard(platform, publisherState?.providers?.[platform]);
  }

  function renderUploadHistory(uploads) {
    const history = $('publish-history'); history.replaceChildren();
    [...(uploads || [])].slice(0, 12).forEach(upload => {
      const row = document.createElement('div'); row.className = 'flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-[10px] text-gray-700';
      const title = upload.metadata?.title || upload.metadata?.caption?.split('\n')[0] || 'Rendered Quran video';
      const label = document.createElement('span'); label.textContent = `${upload.platform === 'youtube' ? 'YouTube' : 'TikTok'} · ${title} · ${uploadStateLabels[upload.status] || upload.status} · ${upload.message || ''}`;
      row.append(label);
      if (upload.result_url && /^https:\/\//i.test(upload.result_url)) {
        const link = document.createElement('a'); link.href = upload.result_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.className = 'font-semibold underline'; link.textContent = 'Open'; row.append(link);
      }
      history.append(row);
    });
  }

  async function loadPublishingState() {
    const response = await fetch('/api/publishing', {cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load publishing accounts.');
    publisherCsrfToken = data.csrf_token || '';
    publisherState = data;
    setAccountCard('youtube', data.providers?.youtube);
    setAccountCard('tiktok', data.providers?.tiktok);
    const relevantUploads = (data.uploads || []).filter(upload => upload.render_job_id === selectedRenderJobId);
    const latest = {};
    relevantUploads.forEach(upload => { if (!latest[upload.platform]) latest[upload.platform] = upload; });
    if (latest.youtube) displayUpload(latest.youtube);
    else $('youtube-upload-message').textContent = data.providers?.youtube?.ready ? 'Ready to upload the selected completed MP4.' : 'Connect YouTube and grant its upload permission to make this destination available.';
    if (latest.tiktok) displayUpload(latest.tiktok);
    else $('tiktok-upload-message').textContent = data.providers?.tiktok?.ready ? 'Ready to upload the selected completed MP4.' : 'Connect TikTok and grant its upload permission to make this destination available.';
    renderUploadHistory(data.uploads);
    if ((data.uploads || []).some(upload => activeUploadStates.has(upload.status))) schedulePublishingPoll();
    return data;
  }

  function schedulePublishingPoll() {
    if (publishingPollTimer) return;
    publishingPollTimer = setTimeout(() => {
      publishingPollTimer = null;
      loadPublishingState().catch(error => console.error('Could not refresh publishing status:', error));
    }, 1400);
  }

  async function refreshUpload(uploadId, button) {
    if (button) button.disabled = true;
    try {
      const response = await fetch(`/api/publishing/uploads/${encodeURIComponent(uploadId)}/refresh`, {
        method:'POST', headers:{'X-Publisher-CSRF':publisherCsrfToken},
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not refresh upload status.');
      await loadPublishingState();
    } catch (error) {
      $('publish-video-summary').textContent = error.message;
    } finally { if (button) button.disabled = false; }
  }

  async function submitSocialUpload(platform) {
    if (!selectedRenderJobId || !lastRenderedPublishMetadata) {
      $('publish-video-summary').textContent = 'Select a completed full-quality video before uploading.';
      return;
    }
    const button = $(platform === 'youtube' ? 'youtube-upload-btn' : 'tiktok-upload-btn');
    button.disabled = true;
    const body = {platform, render_job_id:selectedRenderJobId};
    const hashtags = selectedHashtags();
    if (platform === 'youtube') {
      body.metadata = {
        title:$('publish-yt-title').value,
        description:appendHashtags($('publish-yt-description').value, hashtags),
        tags:$('publish-yt-tags').value,
      };
      body.privacy = $('publish-yt-privacy').value;
      body.category_id = $('publish-yt-category').value;
    } else {
      body.mode = $('publish-tt-mode').value;
      body.metadata = {caption:appendHashtags($('publish-tt-caption').value, hashtags)};
      body.privacy = $('publish-tt-privacy').value;
      body.allow_comments = $('publish-tt-comments').checked;
      body.allow_duet = $('publish-tt-duet').checked;
      body.allow_stitch = $('publish-tt-stitch').checked;
      if (body.metadata.caption.length > 2200) {
        $('tiktok-upload-message').textContent = 'Final caption exceeds TikTok’s 2,200 UTF-16 character limit. Review the caption and hashtags before uploading.';
        button.disabled = false; return;
      }
    }
    $(`${platform}-upload-message`).textContent = 'Starting secure upload…';
    try {
      const response = await fetch('/api/publishing/uploads', {
        method:'POST', headers:{'Content-Type':'application/json','X-Publisher-CSRF':publisherCsrfToken},
        body:JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not start upload.');
      displayUpload(data.upload);
      await loadPublishingState();
    } catch (error) {
      $(`${platform}-upload-message`).textContent = error.message;
      button.disabled = false;
    }
  }

  async function loadTikTokCreatorOptions() {
    if (!publisherState?.providers?.tiktok?.direct_post_ready) return;
    const response = await fetch('/api/publishing/tiktok/creator-info', {
      method:'POST', headers:{'X-Publisher-CSRF':publisherCsrfToken},
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'TikTok direct-post settings are unavailable.');
    const select = $('publish-tt-privacy'); select.replaceChildren();
    const labels = {PUBLIC_TO_EVERYONE:'Everyone', FOLLOWER_OF_CREATOR:'Followers',
      MUTUAL_FOLLOW_FRIENDS:'Friends', SELF_ONLY:'Only you'};
    (data.privacy_level_options || []).forEach(value => select.add(new Option(labels[value] || value, value)));
    const privateIndex = [...select.options].findIndex(option => option.value === 'SELF_ONLY');
    if (privateIndex >= 0) select.selectedIndex = privateIndex;
    $('tiktok-privacy-wrap').classList.toggle('hidden', !select.options.length);
    $('tiktok-privacy-wrap').classList.toggle('flex', Boolean(select.options.length));
    [['comments','comment_disabled'],['duet','duet_disabled'],['stitch','stitch_disabled']].forEach(([setting, disabledKey]) => {
      const control = $(`publish-tt-${setting}`);
      control.disabled = Boolean(data[disabledKey]);
      control.checked = !control.disabled;
    });
  }

  function updateTikTokMode() {
    const direct = $('publish-tt-mode').value === 'direct';
    $('tiktok-mode-note').textContent = direct
      ? 'Direct publishing requires approved video.publish access. Review the caption, audience, and interaction settings; unaudited apps are restricted to private visibility by TikTok.'
      : 'Draft mode uploads the video only. TikTok sends an inbox notification; add or edit the caption and finish publishing in TikTok.';
    $('tiktok-upload-btn').textContent = direct ? 'Publish directly to TikTok' : 'Upload to TikTok';
    $('tiktok-privacy-wrap').classList.toggle('hidden', !direct);
    $('tiktok-privacy-wrap').classList.toggle('flex', direct);
    $('tiktok-interaction-settings').classList.toggle('hidden', !direct);
    if (direct) loadTikTokCreatorOptions().catch(error => { $('tiktok-upload-message').textContent = error.message; });
    updateTikTokCaptionCount();
  }

  async function loadSelectedRender(renderJobId) {
    $('selected-render-error').textContent = '';
    $('publish-metadata-error').classList.add('hidden');
    selectedRenderJobId = renderJobId || null;
    lastRenderedPublishMetadata = null;
    $('published-render-preview').pause();
    $('published-render-preview').removeAttribute('src');
    $('published-render-preview').classList.add('hidden');
    $('selected-render-download').classList.add('hidden');
    setAccountCard('youtube', publisherState?.providers?.youtube);
    setAccountCard('tiktok', publisherState?.providers?.tiktok);
    const response = await fetch(`/api/publishing/renders/${encodeURIComponent(renderJobId)}`, {cache:'no-store'});
    const render = await response.json();
    if (!response.ok) throw new Error(render.error || 'This completed render is unavailable.');
    selectedRenderJobId = render.render_job_id;
    lastRenderedPublishMetadata = render.publish_metadata || null;
    const video = $('published-render-preview');
    video.src = render.preview_url; video.classList.remove('hidden'); video.load();
    $('selected-render-filename').textContent = `${render.download_title} · ${render.surah || 'Quran'} · Ayahs ${render.ayah_start ?? '?'}–${render.ayah_end ?? '?'} · Project ${render.project_id || 'draft'}`;
    const download = $('selected-render-download'); download.href = render.download_url; download.classList.remove('hidden');
    $('publish-video-summary').textContent = `Using the completed MP4 ${(render.download_title || render.filename).replace(/\.mp4$/i, '')}. No new render will be started.`;
    if (lastRenderedPublishMetadata) setPublishMetadata(lastRenderedPublishMetadata);
    if (render.metadata_error) {
      $('publish-metadata-error').textContent = render.metadata_error;
      $('publish-metadata-error').classList.remove('hidden');
    }
    const url = new URL(window.location.href); url.searchParams.set('render_job_id', selectedRenderJobId);
    window.history.replaceState({}, '', url.pathname + url.search + url.hash);
    setAccountCard('youtube', publisherState?.providers?.youtube);
    setAccountCard('tiktok', publisherState?.providers?.tiktok);
  }

  async function loadCompletedRenders() {
    const response = await fetch('/api/publishing/renders', {cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load completed renders.');
    const select = $('completed-render-select'); select.replaceChildren();
    const renders = data.renders || [];
    renders.forEach(render => select.add(new Option(
      `${render.surah || 'Quran video'} · Ayahs ${render.ayah_start ?? '?'}–${render.ayah_end ?? '?'} · ${render.download_title}`,
      render.render_job_id)));
    const requested = new URLSearchParams(window.location.search).get('render_job_id') || document.body.dataset.initialRenderId || '';
    const requestedIsAvailable = renders.some(render => render.render_job_id === requested);
    if (requested && !requestedIsAvailable) {
      selectedRenderJobId = requested;
      select.add(new Option(`Requested render unavailable · ${requested.slice(0, 8)}`, requested), 0);
      select.value = requested;
      try { await loadSelectedRender(requested); }
      catch (error) {
        $('selected-render-error').textContent = error.message;
        $('publish-video-summary').textContent = 'The requested render expired or is unavailable. Choose another completed render if one is listed.';
      }
      return;
    }
    selectedRenderJobId = requestedIsAvailable ? requested : (renders[0]?.render_job_id || '');
    if (selectedRenderJobId) {
      select.value = selectedRenderJobId;
      try { await loadSelectedRender(selectedRenderJobId); }
      catch (error) {
        $('selected-render-error').textContent = error.message;
        $('publish-video-summary').textContent = 'The selected render has expired or is unavailable. Choose another completed render.';
      }
    } else {
      select.add(new Option('No completed renders available', ''), 0);
      $('publish-video-summary').textContent = 'No completed video is available in this browser session. Render one in the editor, then choose Publish Video.';
      $('selected-render-filename').textContent = 'Completed videos from this browser will appear here.';
    }
  }

  $('youtube-connect-btn').addEventListener('click', () => window.location.assign(publishConnectUrl('youtube')));
  $('tiktok-connect-btn').addEventListener('click', () => window.location.assign(publishConnectUrl('tiktok')));
  ['youtube','tiktok'].forEach(platform => $(`${platform}-disconnect-btn`).addEventListener('click', async () => {
    if (!publisherCsrfToken) return;
    const button = $(`${platform}-disconnect-btn`); button.disabled = true;
    try {
      const response = await fetch(`/api/publishing/${platform}/disconnect`, {method:'POST', headers:{'X-Publisher-CSRF':publisherCsrfToken}});
      const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Could not disconnect account.');
      await loadPublishingState();
    } catch (error) { $(`${platform}-account-setup`).textContent = error.message; }
    finally { button.disabled = false; }
  }));
  $('youtube-upload-btn').addEventListener('click', () => submitSocialUpload('youtube'));
  $('tiktok-upload-btn').addEventListener('click', () => submitSocialUpload('tiktok'));
  $('upload-both-btn').addEventListener('click', async () => {
    $('upload-both-btn').disabled = true;
    await Promise.all([submitSocialUpload('youtube'), submitSocialUpload('tiktok')]);
    if (publisherState) { setAccountCard('youtube', publisherState.providers?.youtube); setAccountCard('tiktok', publisherState.providers?.tiktok); }
  });
  $('publish-refresh-btn').addEventListener('click', () => loadPublishingState().then(() => loadTikTokCreatorOptions().catch(() => {})).catch(error => {
    $('publish-video-summary').textContent = error.message;
  }));
  $('publish-tt-mode').addEventListener('change', updateTikTokMode);
  $('publish-tt-caption').addEventListener('input', updateTikTokCaptionCount);
  $('publish-hashtags').addEventListener('input', updateTikTokCaptionCount);
  $('completed-render-select').addEventListener('change', async () => {
    const renderJobId = $('completed-render-select').value;
    if (!renderJobId) return;
    try { await loadSelectedRender(renderJobId); await loadPublishingState(); }
    catch (error) { $('selected-render-error').textContent = error.message; }
  });

  const publishNotice = new URLSearchParams(window.location.search).get('publishing');
  const notices = {
    youtube_connected:'YouTube account connected.', tiktok_connected:'TikTok account connected.',
    youtube_setup:'YouTube is not configured on this server yet.', tiktok_setup:'TikTok is not configured on this server yet.',
    youtube_denied:'YouTube authorization was cancelled.', tiktok_denied:'TikTok authorization was cancelled.',
    youtube_state_error:'YouTube connection expired or failed its security check. Try connecting again.',
    tiktok_state_error:'TikTok connection expired or failed its security check. Try connecting again.',
    youtube_connection_error:'YouTube could not connect. Check the OAuth setup and try again.',
    tiktok_connection_error:'TikTok could not connect. Check the Login Kit setup and try again.',
  };
  if (publishNotice && notices[publishNotice]) $('publishing-notice').textContent = notices[publishNotice];
  loadCompletedRenders().then(() => loadPublishingState())
    .then(() => loadTikTokCreatorOptions().catch(() => {}))
    .catch(error => { $('publish-video-summary').textContent = `Publishing status could not be loaded: ${error.message}`; });
})();
