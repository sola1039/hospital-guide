const api = require('../../utils/api');
const req = require('../../utils/request');

function buildDates() {
  const dates = [];
  const now = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(now.getTime() + i * 86400000);
    const text = (d.getMonth() + 1) + '月' + d.getDate() + '日';
    dates.push({ label: (i === 0 ? '今天 ' : '') + text, value: d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) });
  }
  return dates;
}

function pad(n) {
  return n < 10 ? '0' + n : '' + n;
}

Page({
  data: {
    deptList: [],
    deptIndex: 0,
    doctorList: [],
    doctorIndex: -1,
    dates: [],
    dateIndex: 0,
    slots: ['上午', '下午'],
    slotIndex: 0,
    patientName: '',
    result: null,
    records: []
  },

  onLoad: function () {
    const self = this;
    this.setData({
      dates: buildDates(),
      patientName: wx.getStorageSync('patientName') || ''
    });
    api.departments().then(function (list) {
      const clinic = list.filter(function (d) {
        return d.category === '门诊' || d.category === '急诊';
      });
      self.setData({ deptList: clinic });
      if (clinic.length > 0) self.loadDoctors(clinic[0].id);
    }).catch(function (err) {
      req.showError(err);
    });
    this.loadRecords();
  },

  onDeptChange: function (e) {
    const index = Number(e.detail.value);
    this.setData({ deptIndex: index, doctorIndex: -1, result: null });
    this.loadDoctors(this.data.deptList[index].id);
  },

  loadDoctors: function (deptId) {
    const self = this;
    api.doctors(deptId).then(function (list) {
      self.setData({ doctorList: list });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  pickDoctor: function (e) {
    this.setData({ doctorIndex: Number(e.currentTarget.dataset.index), result: null });
  },

  onDateChange: function (e) {
    this.setData({ dateIndex: Number(e.detail.value) });
  },

  onSlotChange: function (e) {
    this.setData({ slotIndex: Number(e.detail.value) });
  },

  onNameInput: function (e) {
    this.setData({ patientName: e.detail.value });
  },

  submit: function () {
    const self = this;
    const name = this.data.patientName.trim();
    if (!name) {
      wx.showToast({ title: '请填写就诊人姓名', icon: 'none' });
      return;
    }
    if (this.data.doctorIndex < 0) {
      wx.showToast({ title: '请先选择医生', icon: 'none' });
      return;
    }
    wx.setStorageSync('patientName', name);
    const doctor = this.data.doctorList[this.data.doctorIndex];
    const date = this.data.dates[this.data.dateIndex];
    const slot = this.data.slots[this.data.slotIndex];
    api.register(name, doctor.id, date.value, slot).then(function (res) {
      self.setData({ result: res });
      self.loadRecords();
    }).catch(function (err) {
      req.showError(err);
    });
  },

  loadRecords: function () {
    const self = this;
    const name = this.data.patientName ? this.data.patientName.trim() : '';
    api.registrations(name || null).then(function (list) {
      self.setData({ records: list });
    }).catch(function () {
      self.setData({ records: [] });
    });
  }
});
