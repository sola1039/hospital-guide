-- 医院辅助系统 SQLite 表结构
-- 数据流: asset/navigation/nav_data/*.json -> init_db.py 导入 -> 各表 -> dao.py 读取 -> input/api

CREATE TABLE IF NOT EXISTS floors (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  image TEXT NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS nav_nodes (
  id TEXT PRIMARY KEY,
  floor INTEGER NOT NULL,
  x INTEGER NOT NULL,
  y INTEGER NOT NULL,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  link_group TEXT
);

CREATE TABLE IF NOT EXISTS nav_edges (
  node_a TEXT NOT NULL,
  node_b TEXT NOT NULL,
  floor INTEGER NOT NULL,
  weight REAL NOT NULL,
  PRIMARY KEY (node_a, node_b)
);

CREATE TABLE IF NOT EXISTS vertical_links (
  group_name TEXT NOT NULL,
  kind TEXT NOT NULL,
  label TEXT NOT NULL,
  floor INTEGER NOT NULL,
  node_id TEXT NOT NULL,
  PRIMARY KEY (group_name, floor)
);

CREATE TABLE IF NOT EXISTS departments (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  floor INTEGER NOT NULL,
  nav_node_id TEXT NOT NULL,
  category TEXT NOT NULL,
  intro TEXT,
  common_exams TEXT,
  tips TEXT,
  aliases TEXT
);

CREATE TABLE IF NOT EXISTS exam_prep (
  id TEXT PRIMARY KEY,
  exam_name TEXT NOT NULL,
  fasting INTEGER NOT NULL DEFAULT 0,
  duration TEXT,
  prep_text TEXT NOT NULL,
  keywords TEXT
);

CREATE TABLE IF NOT EXISTS medicine_guide (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS doctors_demo (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  dept_id TEXT NOT NULL,
  title TEXT,
  schedule_text TEXT,
  intro TEXT
);

CREATE TABLE IF NOT EXISTS registrations_demo (
  id TEXT PRIMARY KEY,
  patient_name TEXT NOT NULL,
  doctor_id TEXT NOT NULL,
  dept_id TEXT NOT NULL,
  visit_date TEXT NOT NULL,
  slot TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT '已预约',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  state_json TEXT
);

CREATE TABLE IF NOT EXISTS chat_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_nav_nodes_floor ON nav_nodes (floor);
CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_logs (session_id);
