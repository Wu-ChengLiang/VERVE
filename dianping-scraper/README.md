# 大众点评网页元素读取器

基于浏览器扩展 + WebSocket通信架构的大众点评网页数据提取工具。

## 项目结构

```
dianping-scraper/
├── backend/          # Python后端服务
├── extension/        # 浏览器扩展
├── tests/           # 测试文件
├── docs/            # 项目文档
├── requirements.txt # Python依赖
└── README.md       # 项目说明
```

## 技术架构

```
大众点评网页 ←→ 浏览器扩展(Content Script) ←→ WebSocket ←→ Python后端 ←→ 数据处理/存储
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python server.py
```

### 3. 加载浏览器扩展

1. 打开Chrome浏览器
2. 进入扩展管理页面 (chrome://extensions/)
3. 开启开发者模式
4. 点击"加载已解压的扩展程序"
5. 选择 `extension` 目录

### 4. 访问目标网页

打开 https://g.dianping.com/dzim-main-pc/index.html#/ 即可开始数据提取。

## 开发状态

项目正在开发中，当前已完成基础架构搭建。

## 许可证

MIT License 