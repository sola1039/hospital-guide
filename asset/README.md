# asset — 核心层

系统核心能力都在这里，不直接对外，经 input/api 调用。

- `navigation/` — 室内寻路核心算法（Dijkstra，移植自 simpleroutingsvg 的 shortestway），支持多楼层换乘；路网数据在 `input/data_source/nav_data/`，本目录只放通用算法
- `ai_core/` — 就诊引导 AI：就诊全流程知识库与状态机 + LLM 编排（OpenAI 兼容接口）
- `tools/` — 平面图路网标注工具（map-annotator.html），产出 nav_graph.json 与 SVG

输出能力经 output/ 预留接口透传给下一个模块。
