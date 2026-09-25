const req = require('./request');

module.exports = {
  // 导诊
  triage: function (symptoms) {
    return req.post('/api/triage', { symptoms: symptoms });
  },
  departments: function (floor) {
    return req.get('/api/departments', floor ? { floor: floor } : {});
  },
  department: function (deptId) {
    return req.get('/api/departments/' + deptId);
  },
  // 就诊流程
  journeyCard: function (deptId, exams) {
    return req.post('/api/journey/card', { dept_id: deptId, exams: exams || null });
  },
  journeySession: function (sessionId, deptId) {
    return req.post('/api/journey/session', { session_id: sessionId || null, dept_id: deptId });
  },
  journeyStep: function (sessionId, action, key) {
    return req.post('/api/journey/step', { session_id: sessionId, action: action, key: key || null });
  },
  journeyState: function (sessionId) {
    return req.get('/api/journey/session/' + sessionId);
  },
  // 院内导航
  navigate: function (start, end) {
    return req.get('/api/navigate', { start: start, end: end });
  },
  pois: function (floor) {
    return req.get('/api/pois', floor ? { floor: floor } : {});
  },
  floors: function () {
    return req.get('/api/floors');
  },
  // AI 对话
  chat: function (sessionId, message, deptId) {
    return req.post('/api/chat', { session_id: sessionId || null, message: message, dept_id: deptId || null });
  },
  // 须知
  medicine: function () {
    return req.get('/api/medicine');
  },
  examPrep: function () {
    return req.get('/api/exam-prep');
  },
  // 挂号演示
  doctors: function (deptId) {
    return req.get('/api/demo/doctors', deptId ? { dept_id: deptId } : {});
  },
  register: function (patientName, doctorId, visitDate, slot) {
    return req.post('/api/demo/register', {
      patient_name: patientName, doctor_id: doctorId, visit_date: visitDate, slot: slot
    });
  },
  registrations: function (patientName) {
    return req.get('/api/demo/registrations', patientName ? { patient_name: patientName } : {});
  }
};
