const api = require('../../utils/api');
const req = require('../../utils/request');

const FIXED_PLACES = ['主入口', '急诊入口', '儿科入口', '检验入口', '西药房取药窗口', '中药房'];

Page({
  data: {
    placeOptions: [],
    startNames: [],
    endNames: [],
    startIndex: 0,
    endIndex: 0,
    route: null,
    currentFloor: 1,
    routeFloors: { 1: false, 2: false, 3: false, 4: false },
    loading: false
  },

  onLoad: function (options) {
    const self = this;
    api.departments().then(function (depts) {
      const names = FIXED_PLACES.concat(depts.map(function (d) { return d.name; }));
      self.setData({
        placeOptions: names,
        startNames: names,
        endNames: names
      });
      if (self._pendingTarget) {
        self.applyTarget(self._pendingTarget);
        self._pendingTarget = '';
      }
    }).catch(function (err) {
      req.showError(err);
    });
    this.drawMap();
  },

  onShow: function () {
    const target = getApp().globalData.navTarget;
    if (target) {
      getApp().globalData.navTarget = '';
      if (this.data.placeOptions.length > 0) {
        this.applyTarget(target);
      } else {
        this._pendingTarget = target;
      }
    }
  },

  applyTarget: function (target) {
    const names = this.data.endNames;
    let idx = names.indexOf(target);
    if (idx < 0) {
      for (let i = 0; i < names.length; i++) {
        if (names[i].indexOf(target) >= 0 || target.indexOf(names[i]) >= 0) {
          idx = i;
          break;
        }
      }
    }
    if (idx < 0) {
      wx.showToast({ title: '没找到地点: ' + target, icon: 'none' });
      return;
    }
    this.setData({ endIndex: idx });
    this.startNavigate();
  },

  onStartChange: function (e) {
    this.setData({ startIndex: Number(e.detail.value) });
  },

  onEndChange: function (e) {
    this.setData({ endIndex: Number(e.detail.value) });
  },

  startNavigate: function () {
    const self = this;
    const start = this.data.startNames[this.data.startIndex];
    const end = this.data.endNames[this.data.endIndex];
    if (start === end) {
      wx.showToast({ title: '起点和终点不能相同', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    api.navigate(start, end).then(function (route) {
      const floorsMap = { 1: false, 2: false, 3: false, 4: false };
      route.segments.forEach(function (s) { floorsMap[s.floor] = true; });
      self.setData({
        route: route,
        routeFloors: floorsMap,
        currentFloor: route.segments[0].floor,
        loading: false
      });
      self.drawMap();
    }).catch(function (err) {
      self.setData({ loading: false });
      req.showError(err);
    });
  },

  switchFloor: function (e) {
    this.setData({ currentFloor: Number(e.currentTarget.dataset.floor) });
    this.drawMap();
  },

  drawMap: function () {
    const self = this;
    const floor = this.data.currentFloor;
    const route = this.data.route;
    wx.createSelectorQuery().select('#mapCanvas').fields({ node: true, size: true }).exec(function (res) {
      if (!res || !res[0] || !res[0].node) return;
      const canvas = res[0].node;
      const ctx = canvas.getContext('2d');
      const width = res[0].width;
      const height = res[0].height;
      const dpr = wx.getWindowInfo ? wx.getWindowInfo().pixelRatio : wx.getSystemInfoSync().pixelRatio;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      const img = canvas.createImage();
      img.onload = function () {
        ctx.drawImage(img, 0, 0, width, height);
        const scale = width / 1200;
        const seg = route ? route.segments.filter(function (s) { return s.floor === floor; })[0] : null;
        if (seg && seg.points.length > 1) {
          ctx.strokeStyle = '#e63946';
          ctx.lineWidth = 8;
          ctx.lineJoin = 'round';
          ctx.lineCap = 'round';
          ctx.beginPath();
          seg.points.forEach(function (p, i) {
            const x = p[0] * scale;
            const y = p[1] * scale;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          });
          ctx.stroke();
          self.drawMarker(ctx, seg.points[0][0] * scale, seg.points[0][1] * scale, '#2e9e6b', '起');
          const last = seg.points[seg.points.length - 1];
          const isFinal = route.segments[route.segments.length - 1].floor === floor;
          self.drawMarker(ctx, last[0] * scale, last[1] * scale, isFinal ? '#d64541' : '#e8833a', isFinal ? '终' : '换');
        }
      };
      img.src = '/static/floors/floor' + floor + '.jpg';
    });
  },

  drawMarker: function (ctx, x, y, color, label) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, x, y);
  }
});
