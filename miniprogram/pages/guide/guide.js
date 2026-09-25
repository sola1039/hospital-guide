const api = require('../../utils/api');
const req = require('../../utils/request');

Page({
  data: {
    tab: 'medicine',
    medicineList: [],
    examList: []
  },

  onLoad: function () {
    const self = this;
    api.medicine().then(function (list) {
      self.setData({ medicineList: list });
    }).catch(function (err) {
      req.showError(err);
    });
    api.examPrep().then(function (list) {
      self.setData({ examList: list });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  switchTab: function (e) {
    this.setData({ tab: e.currentTarget.dataset.tab });
  }
});
