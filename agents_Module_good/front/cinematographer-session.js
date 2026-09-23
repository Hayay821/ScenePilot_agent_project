(function () {
  class CinematographerSessionClient {
    constructor(baseUrl = '/api/v1') {
      this.baseUrl = baseUrl.replace(/\/$/, '');
      this.sessionId = null;
    }
    async request(path, options = {}) {
      const response = await fetch(this.baseUrl + path, {
        ...options,
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || body.error?.message || '摄影指导服务请求失败');
      return body;
    }
    async start(userText) {
      const body = await this.request('/agents/cinematographer/session/start', {
        method: 'POST',
        body: JSON.stringify({ user_text: userText, skills_filter: { stage: 'cinematographer', limit: 3 } })
      });
      this.sessionId = body.data.session_id;
      return body.data;
    }
    async sendFrame(frame) {
      if (!this.sessionId) throw new Error('Cinematographer Session 尚未启动');
      const body = await this.request('/agents/cinematographer/session/' + this.sessionId + '/frame', {
        method: 'POST', body: JSON.stringify(frame)
      });
      return body.data;
    }
    async stop() {
      if (!this.sessionId) return null;
      const id = this.sessionId;
      this.sessionId = null;
      const body = await this.request('/agents/cinematographer/session/' + id + '/stop', { method: 'POST' });
      return body.data;
    }
  }
  window.ovvCinematographerSessionClient = CinematographerSessionClient;
})();