(function () {
  const client = new window.ovvCinematographerSessionClient();
  let timer = null;
  let busy = false;
  function messages() { return document.querySelector('.chat-messages'); }
  function append(text, role) {
    const item = document.createElement('pre');
    item.className = 'chat-message ' + role;
    item.textContent = text;
    messages()?.appendChild(item);
  }
  function isCinematographer() {
    return document.getElementById('chat-title')?.textContent.startsWith('摄影师');
  }
  function activeAdapter() {
    return Object.values(window.ovvFrameAdapters || {}).find(adapter => adapter.available()) || null;
  }
  async function pushActiveFrame() {
    if (busy || !client.sessionId) return;
    const adapter = activeAdapter();
    if (!adapter) return;
    busy = true;
    try {
      const result = await client.sendFrame(await adapter.nextFrame());
      if (!result.skipped) {
        const suggestion = result.suggestion || {};
        append((result.stream_id || adapter.streamId) + '：' +
          (suggestion.reason || result.analysis?.summary || suggestion.action || '分析完成'), 'assistant');
      }
    } catch (error) { append(error.message, 'error'); }
    finally { busy = false; }
  }
  async function start(goal) {
    if (client.sessionId) await stop();
    const session = await client.start(goal);
    append('实时摄影指导已启动：' + session.session_id, 'assistant');
    await pushActiveFrame();
    timer = setInterval(pushActiveFrame, 2500);
  }
  async function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    const result = await client.stop();
    if (result) append('实时摄影指导已停止，共分析 ' + result.frame_count + ' 帧。', 'assistant');
  }
  document.querySelector('.chat-send')?.addEventListener('click', () => {
    if (!isCinematographer()) return;
    const goal = document.querySelector('.chat-input')?.value.trim();
    if (goal) setTimeout(() => start(goal).catch(error => append(error.message, 'error')), 0);
  }, true);
  document.getElementById('chat-back-button')?.addEventListener('click', () => stop().catch(() => {}));
  window.addEventListener('beforeunload', () => stop().catch(() => {}));
  window.ovvCinematographerBridge = { start, stop, pushActiveFrame, client };
})();