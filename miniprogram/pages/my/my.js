const api = require('../../utils/api');
const req = require('../../utils/request');

Page({
  data: {
    patientName: '',
    records: []
  },

  onShow: function () {
    this.setData({ patientName: wx.getStorageSync('patientName') || '' });
    this.loadRecords();
  },

  onNameInput: function (e) {
    const name = e.detail.value;
    this.setData({ patientName: name });
    wx.setStorageSync('patientName', name);
    this.loadRecords();
  },

  loadRecords: function () {
    const self = this;
    const name = this.data.patientName.trim();
    api.registrations(name || null).then(function (list) {
      self.setData({ records: list });
    }).catch(function () {
      self.setData({ records: [] });
    });
  },

  goRegister: function () {
    wx.navigateTo({ url: '/pages/register/register' });
  },

  goJourney: function () {
    wx.navigateTo({ url: '/pages/journey/journey' });
  },

  goGuide: function () {
    wx.navigateTo({ url: '/pages/guide/guide' });
  }
});
