# input — 数据与接口层

系统输入端：外部数据在这里进入系统。

- `data_source/floor_maps/` — 深圳大学医院 1F-4F 平面图（floor1.jpg ~ floor4.jpg，1200x800）
- `data_source/nav_data/` — 路网标注数据（floor1-4.json 节点与边、vertical_links.json 跨楼层交通），不同医院的数据都放 input 层
- `database/` — SQLite 数据库（schema.sql 建表、init_db.py 初始化、dao.py 数据访问封装）
- `api/` — FastAPI 服务，小程序与其他模块通过 HTTP 进入系统

数据流：小程序 -> input/api -> asset/ 核心处理 -> input/database 读写 -> 返回结果
