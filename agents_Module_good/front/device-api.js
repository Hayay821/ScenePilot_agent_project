(function () {
  class DeviceApi {
    constructor(baseUrl = 'http://127.0.0.1:8766/api/v1') { this.baseUrl = baseUrl; }
    async request(path, options = {}) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), options.timeout || 2500);
      try {
        const response = await fetch(this.baseUrl + path, {
          ...options,
          cache: 'no-store',
          signal: controller.signal,
          headers: options.body instanceof Blob ? (options.headers || {}) :
            { 'Content-Type': 'application/json', ...(options.headers || {}) }
        });
        if (!response.ok) throw new Error((await response.text()) || ('请求失败：' + response.status));
        return response.json();
      } catch (error) {
        if (error.name === 'AbortError') throw new Error('本机真实设备服务响应超时');
        if (error instanceof TypeError) throw new Error('本机真实设备服务未启动');
        throw error;
      } finally { clearTimeout(timeout); }
    }
    health() { return this.request('/health', { timeout: 1000 }); }
    devices() { return this.request('/devices', { timeout: 1000 }); }
    connect(id) { return this.request('/devices/' + id + '/connect', { method: 'POST', timeout: 90000 }); }
    disconnect(id) { return this.request('/devices/' + id + '/disconnect', { method: 'POST', timeout: 5000 }); }
    assets() { return this.request('/assets', { timeout: 1500 }); }
    saveLinkSnapshot(blob) {
      return this.request('/assets/link2-snapshot', {
        method: 'POST', body: blob, timeout: 10000, headers: { 'Content-Type': 'image/jpeg' }
      });
    }
    saveLinkVideo(blob) {
      return this.request('/assets/link2-video', {
        method: 'POST', body: blob, timeout: 120000, headers: { 'Content-Type': 'video/webm' }
      });
    }
    execute(id, action, parameters = {}) {
      const now = Date.now();
      return this.request('/device-actions/execute', {
        method: 'POST',
        timeout: action === 'capture_photo' || action === 'stop_recording' ? 120000 : 15000,
        body: JSON.stringify({
          request_id: crypto.randomUUID ? crypto.randomUUID() : 'ui-' + now,
          device_id: id, action, approved: true,
          rule_id: 'manual.user_control', evidence_id: 'ui-' + now, parameters
        })
      });
    }
    x5StreamUrl() { return this.baseUrl + '/streams/x5-main.jpg'; }
  }
  window.ovvDeviceApi = new DeviceApi();
})();
