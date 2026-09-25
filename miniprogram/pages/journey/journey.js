const api = require('../../utils/api');
const req = require('../../utils/request');

Page({
  data: {
    sessionId: '',
    deptId: '',
    deptList: [],
    card: null,
    step: null,
    state: null,
    showPicker: false,
    placeTarget: '',
    placeLabel: ''
  },

  onLoad: function (options) {
    const session = options.session || getApp().globalData.sessionId || '';
    const dept = options.dept || (getApp().globalData.currentDept ? getApp().globalData.currentDept.id : '');
    if (session && dept) {
      this.setData({ sessionId: session, deptId: dept });
      this.loadCard(dept);
    } else if (session) {
      this.setData({ sessionId: session });
    } else {
      this.loadDepts();
    }
  },

  loadDepts: function () {
    const self = this;
    api.departments().then(function (list) {
      const clinic = list.filter(function (d) {
        return d.category === '门诊' || d.category === '检查' || d.category === '急诊';
      });
      self.setData({ deptList: clinic, showPicker: true });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  pickDept: function (e) {
    const dept = this.data.deptList[e.currentTarget.dataset.index];
    const self = this;
    api.journeySession(null, dept.id).then(function (res) {
      getApp().globalData.sessionId = res.session_id;
      getApp().globalData.currentDept = dept;
      self.setData({
        sessionId: res.session_id,
        deptId: dept.id,
        showPicker: false,
        card: res.card,
        step: res.step,
        state: null
      });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  loadCard: function (deptId) {
    const self = this;
    api.journeyCard(deptId).then(function (card) {
      self.setData({ card: card });
      self.refreshStep();
    }).catch(function (err) {
      req.showError(err);
    });
  },

  refreshStep: function () {
    const self = this;
    api.journeyState(this.data.sessionId).then(function (res) {
      self.setData({ step: res.step, state: res.state });
      self.applyStepPlace(res.step);
    }).catch(function () {
      self.setData({ step: null });
    });
  },

  applyStepPlace: function (step) {
    if (!step || !this.data.card) return;
    const item = this.data.card.steps[step.index];
    this.setData({
      placeTarget: item && item.nav_target ? item.nav_target : '',
      placeLabel: item && item.nav_label ? item.nav_label : ''
    });
  },

  nextStep: function () {
    const self = this;
    api.journeyStep(this.data.sessionId, 'next').then(function (res) {
      self.setData({ step: res.step, state: res.state });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  prevStep: function () {
    const self = this;
    api.journeyStep(this.data.sessionId, 'back').then(function (res) {
      self.setData({ step: res.step, state: res.state });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  goNavigate: function () {
    const target = this.data.placeTarget || (this.data.card && this.data.card.dept ? this.data.card.dept.name : '');
    if (!target) return;
    getApp().globalData.navTarget = target;
    wx.switchTab({ url: '/pages/navigate/navigate' });
  }
});
