# A股小市值股票筛选系统

## 功能介绍

这是一个自动化的A股股票筛选系统，主要功能包括：

1. **自动筛选**：每日下午14:30自动执行
2. **筛选逻辑**：
   - 从A股所有股票中筛选市值倒数1000名的股票
   - 在这1000只股票中，按归母净利润增速排序，取前30名
3. **数据展示**：
   - 完整的行情数据（开盘价、最高价、最低价、收盘价、成交额、成交量、流通市值、总市值）
   - 支持日线、周线、月线K线图查看
4. **邮件通知**：筛选结果自动发送到指定邮箱

## 前置依赖

### 必需依赖

1. **Python 3.8+**
2. **Vercel账号**：用于部署Web应用
3. **Git**：用于代码版本管理

### Python包依赖

```
fastapi==0.104.1
uvicorn==0.24.0
akshare==1.11.36
pandas==2.1.3
numpy==1.26.2
jinja2==3.1.2
aiofiles==23.2.1
apscheduler==3.10.4
pydantic==2.5.2
python-multipart==0.0.6
requests==2.31.0
mangum==0.17.0  # Vercel部署必需
```

## 项目结构

```
a_stock_screener/
├── api/
│   └── index.py          # Vercel Serverless入口
├── data/                 # 数据存储目录
├── templates/
│   └── index.html        # Web界面模板
├── data_collector.py     # 数据收集模块
├── email_sender.py       # 邮件发送模块
├── main.py              # FastAPI主应用（本地运行）
├── scheduler.py         # 定时任务调度器
├── requirements.txt     # Python依赖
├── requirements-vercel.txt  # Vercel部署依赖
├── vercel.json         # Vercel配置文件
└── README.md           # 项目说明
```

## 部署步骤

### 1. 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 运行本地服务器
python main.py

# 或者使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看Web界面

### 2. Vercel部署

#### 2.1 准备工作

1. 注册 [Vercel](https://vercel.com) 账号
2. 安装 Vercel CLI：
   ```bash
   npm install -g vercel
   ```
3. 登录Vercel：
   ```bash
   vercel login
   ```

#### 2.2 部署命令

```bash
# 进入项目目录
cd a_stock_screener

# 使用Vercel部署
vercel --prod
```

#### 2.3 配置环境变量（可选）

在Vercel Dashboard中设置环境变量：
- `EMAIL_PASSWORD`: 邮箱授权码

### 3. 定时任务配置

Vercel的Serverless函数不支持长期运行的定时任务，需要使用外部服务：

#### 方案1：使用GitHub Actions（推荐）

创建 `.github/workflows/schedule.yml`：

```yaml
name: Daily Stock Screening

on:
  schedule:
    - cron: '30 6 * * 1-5'  # 工作日14:30 (UTC+8)
  workflow_dispatch:

jobs:
  screen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run screening
        run: |
          python scheduler.py --run-now
```

#### 方案2：使用外部定时任务服务

- [Cron-job.org](https://cron-job.org)
- [EasyCron](https://www.easycron.com)

配置定时请求你的Vercel API：
```
POST https://your-app.vercel.app/api/refresh
```

### 4. 手动运行筛选

```bash
# 立即执行一次筛选
python scheduler.py --run-now

# 启动定时调度器（本地）
python scheduler.py --start
```

## API接口

### 获取股票列表
```
GET /api/stocks
```

### 刷新数据
```
POST /api/refresh
```

### 获取K线数据
```
GET /api/kline/{code}?period=daily|weekly|monthly
```

### 获取股票详情
```
GET /api/stock/{code}
```

### 健康检查
```
GET /api/health
```

## 注意事项

1. **数据源**：使用AKShare免费数据源，可能有频率限制
2. **执行时间**：筛选1000只股票需要一定时间（约5-10分钟）
3. **Vercel限制**：
   - Serverless函数执行时间限制（免费版10秒，付费版300秒）
   - 可能需要将数据获取逻辑拆分到多个函数
4. **邮件发送**：163邮箱需要开启SMTP授权

## 常见问题

### Q: Vercel部署后数据获取超时怎么办？
A: 考虑使用Vercel的Edge Functions或拆分任务，也可以部署到支持长时运行的平台如Railway、Render等。

### Q: 如何修改筛选条件？
A: 编辑 `data_collector.py` 中的 `screen_stocks` 方法，调整市值排名和净利润增速的筛选逻辑。

### Q: 邮件发送失败怎么办？
A: 检查163邮箱的SMTP授权码是否正确，以及是否开启了SMTP服务。

## 更新日志

### v1.0.0 (2026-03-05)
- 初始版本发布
- 实现基本筛选功能
- 支持Web界面和K线图
- 支持邮件通知

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。