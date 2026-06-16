# AI STEM Education Daily Brief Bot

这是一个自动化的 Python 服务，用于从 Google News RSS 自动搜索 **AI STEM Education** 相关的最新新闻，获取最近 10 条新闻，并使用 Gemini API 进行智能总结，最后将简报保存到本地归档、记录日志并推送到指定的 Discord 频道。

## 功能特点

1. **Google News RSS 搜索**：自动查询最新的 "AI STEM Education" 新闻。
2. **最新资讯获取**：获取最近的 10 条新闻条目。
3. **AI 智能总结**：使用 Gemini API (`gemini-2.5-flash`) 生成定制的教育简报。
4. **归档功能**：每次运行后自动将简报以 Markdown 格式保存到 `archive/YYYY-MM-DD.md`（采用北京时间 UTC+8 命名）。
5. **日志系统**：运行过程全程记录到 `logs/app.log`，包含启动、新闻数量、Gemini 状态、Discord 发送状态及错误信息。
6. **自动定时调度**：支持通过 `scheduler.py` 设定每日固定时间（例如：北京时间上午 8:00）自动运行。
7. **灵活配置**：所有的搜索词、新闻条数、Gemini 模型、定时时间及 Discord Webhook 均可在 `config.yaml` 中配置。

## 项目结构

```
stem-news-bot/
├── archive/              # 存放每日 Markdown 简报归档 (自动创建)
│   ├── 2026-06-16.md
│   └── ...
├── logs/                 # 存放系统运行日志 (自动创建)
│   └── app.log
├── .env                  # 存放 API 密钥与 Webhook 地址 (本地敏感配置)
├── .env.example          # 环境变量模板
├── config.yaml           # 项目配置文件 (关键词、模型、Webhook、定时时间)
├── main.py               # 单次运行/核心业务逻辑主程序
├── scheduler.py          # 定时调度服务程序
├── requirements.txt      # 依赖包列表
└── README.md             # 使用说明
```

## 快速开始

### 1. 准备环境

确保你的系统上已安装 Python 3.8+。

### 2. 安装依赖

在项目根目录下运行：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

1. 复制 `.env.example` 并重命名为 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 编辑 `.env` 文件，填写你的 Gemini API Key 和 Discord Webhook URL：
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   # 也可以在 config.yaml 中配置 DISCORD_WEBHOOK_URL，但 .env 中的优先级最高
   DISCORD_WEBHOOK_URL=your_actual_discord_webhook_url_here
   ```

### 4. 调整配置 `config.yaml`

你可以根据需求修改 `config.yaml` 文件中的参数：

```yaml
# Google News RSS 搜索配置
search:
  query: "AI STEM Education"  # 搜索关键词
  limit: 10                   # 获取的新闻条数

# Gemini API 配置
gemini:
  model_name: "gemini-2.5-flash" # 使用的 Gemini 模型

# Discord Webhook 配置
discord:
  webhook_url: "your_discord_webhook_url_here"  # 也可以在 .env 中设置
  username: "STEM News Bot"   # 发送者的自定义显示昵称

# 定时调度配置
schedule:
  time: "08:00"  # 每天自动运行的时间 (北京时间 UTC+8)
```

---

## 运行方式

### 方式 A：单次手动运行

适用于手动测试、补发或按需获取最新资讯：

```bash
python main.py
```

> **提示**：如果未配置 `.env` 或 `config.yaml` 中的真实 API Key 和 Webhook URL，脚本将自动以 **Dry-run (模拟运行)** 模式运行。它会照常获取最新的 Google News，但会生成模拟的简报，保存到本地 `archive/` 归档并记录到 `logs/`，不会调用实际的 API 或发送到 Discord。

### 方式 B：自动运行服务 (Scheduler)

启动定时服务，程序将在后台挂起，根据 `config.yaml` 配置的 `schedule.time` 时间（默认为每天北京时间上午 `08:00`）自动触发运行：

```bash
python scheduler.py
```

---

## 部署为长期运行的服务

为了使机器人能够在服务器（如 Linux VPS、云服务器）上 7×24 小时稳定运行，推荐使用以下部署方案：

### 1. 使用 `nohup` (简单便捷)

在后台无挂断地运行调度器，并将输出重定向：

```bash
nohup python -u scheduler.py > /dev/null 2>&1 &
```

若要停止该后台服务，可以通过以下命令查找进程并终止：

```bash
ps aux | grep scheduler.py
kill -9 <进程PID>
```

### 2. 使用 Systemd (推荐，最稳定且支持开机自启)

如果你在 Linux (如 Ubuntu/CentOS) 上部署，可以将其创建为 Systemd 服务：

1. 创建服务文件 `/etc/systemd/system/stem-news.service`：

   ```ini
   [Unit]
   Description=AI STEM News Bot Scheduler Service
   After=network.target

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/Users/ying/Documents/GitHub/stem-news-bot
   ExecStart=/usr/bin/python3 scheduler.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   *(请将 `your_username`、`WorkingDirectory` 以及 `/usr/bin/python3` 路径替换为你的实际服务器配置)*

2. 启动并启用服务：

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start stem-news.service
   sudo systemctl enable stem-news.service
   ```

3. 查看服务状态：

   ```bash
   sudo systemctl status stem-news.service
   ```

## 输出格式样例

机器人生成并发送至 Discord，以及保存在 `archive/` 中的简报格式如下：

```markdown
# AI + STEM Education Daily Brief

## Key Developments
- [从获取的新闻中提炼的关键技术进展或行业消息点 1]
- [关键技术进展或行业消息点 2]

## Implications for Educators
- [针对上述进展给教育者和课堂带来的启示点 1]
- [给教育者和课堂带来的启示点 2]
```
