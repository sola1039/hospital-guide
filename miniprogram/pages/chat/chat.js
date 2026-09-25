const api = require('../../utils/api');
const req = require('../../utils/request');

Page({
  data: {
    mode: 'chat',
    messages: [],
    inputText: '',
    symptomText: '',
    triageResult: null,
    loading: false,
    quickChips: ['我牙疼', '孩子发烧咳嗽', '头晕血压高', '下一步', '药怎么吃']
  },

  onLoad: function () {
    this.setData({
      messages: [{
        role: 'assistant',
        text: '您好, 我是就医陪伴助手。您可以跟我说说哪里不舒服, 我帮您选科室、安排看病流程。'
      }]
    });
  },

  switchMode: function (e) {
    this.setData({ mode: e.currentTarget.dataset.mode });
  },

  onSymptomInput: function (e) {
    this.setData({ symptomText: e.detail.value });
  },

  startTriage: function () {
    const self = this;
    const text = this.data.symptomText.trim();
    if (!text) {
      wx.showToast({ title: '请先说说哪里不舒服', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    api.triage(text).then(function (res) {
      self.setData({ loading: false, triageResult: res });
    }).catch(function (err) {
      self.setData({ loading: false });
      req.showError(err);
    });
  },

  pickAlternative: function (e) {
    const dept = this.data.triageResult.alternatives[e.currentTarget.dataset.index];
    const result = this.data.triageResult;
    result.alternatives = [result.dept].concat(result.alternatives.filter(function (d) { return d.id !== dept.id; }));
    result.dept = dept;
    result.suggestion = '已改为' + dept.name + '(在' + dept.floor + '楼)';
    this.setData({ triageResult: result });
  },

  goNavigateToDept: function () {
    const dept = this.data.triageResult.dept;
    getApp().globalData.currentDept = dept;
    getApp().globalData.navTarget = dept.name;
    wx.switchTab({ url: '/pages/navigate/navigate' });
  },

  makeJourneyCard: function () {
    const self = this;
    const dept = this.data.triageResult.dept;
    getApp().globalData.currentDept = dept;
    api.journeySession(null, dept.id).then(function (res) {
      getApp().globalData.sessionId = res.session_id;
      wx.navigateTo({ url: '/pages/journey/journey?session=' + res.session_id + '&dept=' + dept.id });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  onChatInput: function (e) {
    this.setData({ inputText: e.detail.value });
  },

  tapChip: function (e) {
    this.sendMessage(e.currentTarget.dataset.text);
  },

  sendCurrent: function () {
    const text = this.data.inputText.trim();
    if (!text) return;
    this.setData({ inputText: '' });
    this.sendMessage(text);
  },

  sendMessage: function (text) {
    const self = this;
    const messages = this.data.messages.concat([{ role: 'user', text: text }]);
    this.setData({ messages: messages, loading: true });
    api.chat(getApp().globalData.sessionId || null, text, getApp().globalData.currentDept ? getApp().globalData.currentDept.id : null)
      .then(function (res) {
        if (res.session_id) {
          getApp().globalData.sessionId = res.session_id;
        }
        const updated = self.data.messages.concat([{ role: 'assistant', text: res.reply }]);
        self.setData({ messages: updated, loading: false, lastStep: res.step || null });
      }).catch(function (err) {
        self.setData({ loading: false });
        req.showError(err);
      });
  },

  goJourney: function () {
    wx.navigateTo({ url: '/pages/journey/journey' });
  }
});
