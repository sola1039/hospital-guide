const config = require('./config');

function request(method, path, data) {
  return new Promise(function (resolve, reject) {
    wx.request({
      url: config.apiBase + path,
      method: method,
      data: method === 'GET' ? data : JSON.stringify(data || {}),
      header: method === 'GET' ? {} : { 'Content-Type': 'application/json' },
      success: function (res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          var detail = (res.data && res.data.detail) ? res.data.detail : '服务返回 ' + res.statusCode;
          reject(new Error(detail));
        }
      },
      fail: function (err) {
        reject(new Error('无法连接服务, 请确认后端已启动: ' + (err.errMsg || '')));
      }
    });
  });
}

function get(path, data) {
  return request('GET', path, data);
}

function post(path, data) {
  return request('POST', path, data);
}

function showError(err) {
  wx.showToast({ title: (err && err.message) ? err.message : '请求失败', icon: 'none', duration: 2500 });
}

module.exports = { get: get, post: post, showError: showError };
