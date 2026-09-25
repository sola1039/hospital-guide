Page({
  goChat: function () {
    wx.navigateTo({ url: '/pages/chat/chat' });
  },
  goNavigate: function () {
    wx.switchTab({ url: '/pages/navigate/navigate' });
  },
  goJourney: function () {
    wx.navigateTo({ url: '/pages/journey/journey' });
  },
  goGuide: function () {
    wx.navigateTo({ url: '/pages/guide/guide' });
  },
  goRegister: function () {
    wx.navigateTo({ url: '/pages/register/register' });
  },
  goMy: function () {
    wx.switchTab({ url: '/pages/my/my' });
  }
});
