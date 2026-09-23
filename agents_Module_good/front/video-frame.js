(function () {
  function canvasFrame(source, width, height, quality) {
    if (!width || !height) throw new Error('实时画面尚未就绪');
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d', { alpha: false }).drawImage(source, 0, 0, width, height);
    return canvas.toDataURL('image/jpeg', quality);
  }
  class VideoFrameAdapter {
    constructor(streamId, deviceId, sourceType) {
      this.streamId = streamId;
      this.deviceId = deviceId;
      this.sourceType = sourceType;
      this.sequence = 0;
    }
    envelope(frameData) {
      return {
        stream_id: this.streamId,
        device_id: this.deviceId,
        source_type: this.sourceType,
        timestamp_ms: Date.now(),
        sequence: this.sequence++,
        mime_type: 'image/jpeg',
        frame_data: frameData
      };
    }
  }
  class Link2FrameAdapter extends VideoFrameAdapter {
    constructor(video, deviceId = 'link2-local') {
      super('link2-main', deviceId, 'insta360_link2_uvc');
      this.video = video;
    }
    available() { return Boolean(this.video.srcObject && this.video.videoWidth && !this.video.hidden); }
    async nextFrame() {
      return this.envelope(canvasFrame(this.video, this.video.videoWidth, this.video.videoHeight, 0.78));
    }
  }
  class X5FrameAdapter extends VideoFrameAdapter {
    constructor(image, deviceId = 'x5-local') {
      super('x5-main', deviceId, 'insta360_x5_mediasdk');
      this.image = image;
    }
    available() { return Boolean(this.image.complete && this.image.naturalWidth && !this.image.hidden); }
    async nextFrame() {
      return this.envelope(canvasFrame(this.image, this.image.naturalWidth, this.image.naturalHeight, 0.78));
    }
  }
  window.ovvVideoFrame = { VideoFrameAdapter, Link2FrameAdapter, X5FrameAdapter };
})();