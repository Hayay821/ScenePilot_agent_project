(function () {
  const api = window.ovvDeviceApi;
  const service = document.getElementById('service-state');
  const log = document.getElementById('device-event-log');
  const video = document.getElementById('link2-preview');
  const image = document.getElementById('x5-preview');
  const placeholder = document.getElementById('preview-placeholder');
  const badge = document.getElementById('preview-live-badge');
  const label = document.getElementById('preview-source-label');
  const assetList = document.getElementById('local-asset-list');
  let stream = null, x5Timer = null, linkRecorder = null, linkChunks = [];
  image.crossOrigin = 'anonymous';
  window.ovvFrameAdapters = {
    'link2-main': new window.ovvVideoFrame.Link2FrameAdapter(video),
    'x5-main': new window.ovvVideoFrame.X5FrameAdapter(image)
  };
  const toggles = { set_tracking: false, set_privacy: false };

  service.textContent = '正在连接设备控制服务…';

  function add(message, type = 'success') {
    if (log.firstElementChild?.textContent === '等待操作') log.textContent = '';
    const item = document.createElement('li');
    item.className = type;
    item.textContent = new Date().toLocaleTimeString() + ' ' + message;
    log.prepend(item);
  }
  function markConnected(id, value) {
    document.querySelector('[data-device-card="' + id + '"]')?.classList.toggle('connected', value);
    const state = document.getElementById(id === 'x5-main' ? 'x5-state' : 'link2-state');
    if (state) state.textContent = value ? '已连接' : '未连接';
  }
  function show(kind) {
    image.closest('.camera-preview-frame').classList.toggle('is-x5', kind === 'x5');
    placeholder.hidden = true; video.hidden = kind !== 'link2'; image.hidden = kind !== 'x5';
    badge.hidden = false;
    label.textContent = kind === 'link2' ? 'Link 2 · UVC 本机画面' : 'X5 · MediaSDK 实时拼接';
  }
  function stopLocalPreview() {
    image.closest('.camera-preview-frame').classList.remove('is-x5');
    if (x5Timer) { clearInterval(x5Timer); x5Timer = null; }
    stream?.getTracks().forEach(track => track.stop());
    stream = null; video.srcObject = null; image.removeAttribute('src');
    video.hidden = true; image.hidden = true; placeholder.hidden = false; badge.hidden = true;
    label.textContent = '尚未选择设备';
  }
  async function refreshAssets() {
    try {
      const assets = await api.assets();
      assetList.textContent = '';
      if (!assets.length) {
        assetList.innerHTML = '<p class="asset-empty">暂无拍摄素材</p>';
        return;
      }
      assets.sort((a, b) => b.name.localeCompare(a.name)).forEach(asset => {
        const link = document.createElement('a');
        link.className = 'asset-item';
        link.href = asset.url;
        link.target = '_blank';
        link.innerHTML = '<span class="asset-symbol">' +
          (/\.(mp4|insv|lrv|webm)$/i.test(asset.name) ? 'VID' : 'IMG') +
          '</span><span>' + asset.name + '</span>';
        assetList.appendChild(link);
      });
    } catch (_) {}
  }
  async function refresh() {
    try {
      const [, devices] = await Promise.all([api.health(), api.devices()]);
      service.textContent = '设备控制服务运行中';
      service.className = 'service-state online';
      devices.forEach(device => markConnected(device.id, device.connected));
    } catch (error) {
      service.textContent = error.message;
      service.className = 'service-state offline';
    }
  }
  async function run(id, action, parameters = {}) {
    const result = await api.execute(id, action, parameters);
    add(result.message || action + ' 执行成功');
    if (result.output_uri) await refreshAssets();
    return result;
  }

  document.querySelectorAll('[data-connect]').forEach(button => button.onclick = async () => {
    const original = button.textContent;
    button.disabled = true;
    button.textContent = '连接中…';
    add((button.dataset.connect === 'x5-main' ? 'X5' : 'Link 2') + ' 正在连接，请稍候');
    try {
      const result = await api.connect(button.dataset.connect);
      markConnected(button.dataset.connect, true);
      add(result.message || '连接成功');
    } catch (error) {
      add(error.message, 'error');
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  });
  document.querySelectorAll('[data-disconnect]').forEach(button => button.onclick = async () => {
    try {
      const id = button.dataset.disconnect;
      const result = await api.disconnect(id);
      markConnected(id, false);
      if (id === 'x5-main' || id === 'link2-main') stopLocalPreview();
      add(result.message || '设备已断开');
    } catch (error) { add(error.message, 'error'); }
  });
  document.querySelectorAll('[data-action]').forEach(button => button.onclick = async () => {
    const action = button.dataset.action, parameters = {};
    if (action in toggles) { toggles[action] = !toggles[action]; parameters.enabled = toggles[action]; }
    try {
      await run(button.dataset.device, action, parameters);
      if (action in toggles) {
        button.classList.toggle('is-active', toggles[action]);
        if (action === 'set_tracking') button.textContent = toggles[action] ? '停止追踪' : '开启追踪';
        if (action === 'set_privacy') button.textContent = toggles[action] ? '退出隐私' : '隐私模式';
      }
    } catch (error) {
      if (action in toggles) toggles[action] = !toggles[action];
      add(error.message, 'error');
    }
  });
  const zoomSlider = document.getElementById('zoom-range');
  const zoomValue = document.getElementById('zoom-value');
  async function applyZoom(value) {
    const zoom = Number(value);
    zoomSlider.value = zoom;
    zoomValue.textContent = zoom.toFixed(1) + '×';
    try {
      await run('link2-main', 'set_zoom', { zoom });
      document.querySelectorAll('[data-zoom]').forEach(item =>
        item.classList.toggle('is-active', Number(item.dataset.zoom) === zoom));
    } catch (error) { add(error.message, 'error'); }
  }
  zoomSlider.oninput = () => {
    zoomValue.textContent = Number(zoomSlider.value).toFixed(1) + '×';
    document.querySelectorAll('[data-zoom]').forEach(item => item.classList.remove('is-active'));
  };
  zoomSlider.onchange = () => applyZoom(zoomSlider.value);
  document.querySelectorAll('[data-zoom]').forEach(button =>
    button.onclick = () => applyZoom(button.dataset.zoom));

  document.getElementById('link2-browser-preview').onclick = async () => {
    try {
      stopLocalPreview();
      const permissionStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      const devices = await navigator.mediaDevices.enumerateDevices();
      const link = devices.find(device => device.kind === 'videoinput' && /insta360|link\s*2/i.test(device.label));
      permissionStream.getTracks().forEach(track => track.stop());
      if (!link) throw new Error('没有在 Windows 摄像头列表中找到 Insta360 Link 2');
      stream = await navigator.mediaDevices.getUserMedia({
        video: { deviceId: { exact: link.deviceId }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false
      });
      video.srcObject = stream; show('link2'); add('Link 2 实时预览已开启');
    } catch (error) { add('无法打开 Link 2：' + error.message, 'error'); }
  };
  document.getElementById('link2-snapshot').onclick = async () => {
    if (!stream || !video.videoWidth) { add('请先开启 Link 2 实时预览', 'error'); return; }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    try {
      const result = await api.saveLinkSnapshot(blob);
      add(result.message); await refreshAssets();
    } catch (error) { add(error.message, 'error'); }
  };
  const linkRecordStart = document.getElementById('link2-record-start');
  const linkRecordStop = document.getElementById('link2-record-stop');
  linkRecordStart.onclick = async () => {
    if (!stream) { add('请先开启 Link 2 实时预览', 'error'); return; }
    try {
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9' : 'video/webm';
      linkChunks = [];
      linkRecorder = new MediaRecorder(stream, { mimeType });
      linkRecorder.ondataavailable = event => { if (event.data.size) linkChunks.push(event.data); };
      linkRecorder.onstop = async () => {
        try {
          const blob = new Blob(linkChunks, { type: 'video/webm' });
          const result = await api.saveLinkVideo(blob);
          add(result.message);
          await refreshAssets();
        } catch (error) {
          add(error.message, 'error');
        } finally {
          linkRecordStart.disabled = false;
          linkRecordStop.disabled = true;
          linkRecorder = null;
          linkChunks = [];
        }
      };
      linkRecorder.start(1000);
      linkRecordStart.disabled = true;
      linkRecordStop.disabled = false;
      add('Link 2 视频录制已开始');
    } catch (error) { add('无法开始录像：' + error.message, 'error'); }
  };
  linkRecordStop.onclick = () => {
    if (!linkRecorder || linkRecorder.state !== 'recording') {
      add('Link 2 当前没有正在进行的录像', 'error');
      return;
    }
    linkRecordStop.disabled = true;
    linkRecordStop.textContent = '正在保存…';
    linkRecorder.addEventListener('stop', () => {
      linkRecordStop.textContent = '停止录像并保存';
    }, { once: true });
    linkRecorder.stop();
  };

  document.getElementById('x5-stream-preview').onclick = async () => {
    try {
      await run('x5-main', 'start_preview'); stopLocalPreview(); show('x5');
      const update = () => { image.src = api.x5StreamUrl() + '?t=' + Date.now(); };
      update(); x5Timer = setInterval(update, 200);
    } catch (error) { add(error.message, 'error'); }
  };
  document.getElementById('stop-preview-button').onclick = async () => {
    if (!image.hidden) try { await api.execute('x5-main', 'stop_preview'); } catch (_) {}
    stopLocalPreview(); add('实时预览已停止');
  };
  window.ovvStopLocalPreview = stopLocalPreview;
  window.addEventListener('beforeunload', stopLocalPreview);
  refresh();
  refreshAssets();
})();
