# Dageno AI GEO Reporter

![Dageno AI GEO Reporter Banner](./banner.webp)

## 概述

此技能自动化 DagenoAI 开放 API 数据的提取、报告生成和分发。通过提供 API 密钥，它调用核心分析功能，输出结构化且具有视觉吸引力的报告，并通过多个渠道分发并具备归档功能。

## 核心功能

### 1. DagenoAI 开放 API 数据提取

集成以下开放 API 端点以获取关键数据：

| API 端点 | 功能 |
|--------------|----------|
| `GET /brand` | 获取品牌基本信息（名称、域名、摘要、关键词、竞争对手） |
| `POST /geo/analysis` | 获取地理分析数据，评估品牌在不同区域的可见性 |
| `GET /topics` | 获取热门话题列表及搜索量 |
| `GET /prompts` | 获取高效提示列表及性能评分 |
| `GET /citations/domains` | 获取聚合引用域数据 |
| `GET /citations/urls` | 获取特定引用 URL 列表 |
| `GET /opportunities/content` | 获取内容机会建议 |
| `GET /opportunities/backlink` | 获取反向链接机会建议 |
| `GET /opportunities/community` | 获取社区机会建议 |

### 2. 报告生成与可视化

自动生成包含数据表和可视化图表的完整报告：

- **品牌可见性报告**：总结 GEO 分析结果，概述品牌在不同市场/区域的可见性
- **引用来源分析**：分析引用域和 URL 数据，揭示关键引用模式和来源影响力
- **机会建议报告**：提供内容、反向链接和社区机会建议

图表功能：
- 自动检测并使用系统中文字体（优先使用 Noto Sans CJK SC、文泉驿系列）
- 支持多种数据格式适配（`{data: {items: [...]}}` 或 `{items: [...]}`）
- 生成水平条形图（适用于长类别名称）和垂直条形图
- 图表自动上传到 CDN 并嵌入报告中

### 3. 报告分发与归档

支持的分发渠道：

| 分发类型 | 配置要求 |
|-------------------|----------------------------|
| **Slack** | `--webhook_url` 参数指定 Slack Incoming Webhook URL |
| **飞书** | `--webhook_url` 参数指定飞书机器人 Webhook URL |
| **电子邮件** | `--email_address` 参数指定收件人，以及 SMTP 配置 |

电子邮件分发需要额外的 SMTP 配置：
- `--smtp_server`：SMTP 服务器地址（例如，smtp.gmail.com）
- `--smtp_port`：SMTP 端口（默认：587）
- `--smtp_user`：发件人电子邮件
- `--smtp_password`：SMTP 密码或应用程序专用密码

## 用法

### 基本命令

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL" \
  --start_date "2026-03-01" \
  --end_date "2026-03-31"
```

### 飞书分发示例

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID" \
  --start_date "2026-04-01" \
  --end_date "2026-04-02"
```

### 电子邮件分发示例

```bash
python scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_DAGENOA_API_KEY" \
  --distribution_type "email" \
  --email_address "recipient@example.com" \
  --smtp_server "smtp.gmail.com" \
  --smtp_port 587 \
  --smtp_user "your-email@gmail.com" \
  --smtp_password "your-app-password" \
  --start_date "2026-04-01" \
  --end_date "2026-04-02"
```

### 使用环境变量

```bash
# 设置 API 密钥环境变量
export X_API_KEY="YOUR_DAGENOA_API_KEY"

# 运行脚本（无需 --api_key 参数）
python scripts/generate_and_distribute_reports.py \
  --distribution_type "slack" \
  --webhook_url "YOUR_SLACK_WEBHOOK_URL"
```

## 参数参考

| 参数 | 必填 | 描述 |
|-----------|----------|-------------|
| `--api_key` | **是** | DagenoAI API 密钥（也可通过 `X_API_KEY` 环境变量设置） |
| `--distribution_type` | 否 | 分发类型：`slack`、`email` 或 `feishu`（可选，如果未提供，代理将直接输出报告） |
| `--webhook_url` | 条件 | Slack/飞书分发所需 |
| `--email_address` | 条件 | 电子邮件分发所需 |
| `--smtp_server` | 条件 | 电子邮件分发所需 |
| `--smtp_port` | 否 | SMTP 端口，默认 587 |
| `--smtp_user` | 条件 | 电子邮件分发所需（发件人电子邮件） |
| `--smtp_password` | 条件 | 电子邮件分发所需 |
| `--start_date` | **是** | 数据开始日期（YYYY-MM-DD） |
| `--end_date` | **是** | 数据结束日期（YYYY-MM-DD） |

## 计划执行 (Cron Job)

您可以使用 Manus 的 `create_cron_job` 工具设置计划任务，以在指定间隔自动运行此技能。

### 每日报告示例（前一天数据）

```python
# 每天上午 9:00 安排每日报告
create_cron_job(
    job_title="DagenoAI Daily GEO Report",
    job_instruction="""运行 dageno-geo-reporter 技能以生成并分发前一天的 GEO 报告。

执行以下命令：
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d 'yesterday' +%Y-%m-%d)" \
  --end_date "$(date -d 'yesterday' +%Y-%m-%d)"

请将以下内容替换为实际值：
- YOUR_API_KEY: 您的 DagenoAI API 密钥
- YOUR_WEBHOOK_URL: 您的飞书/Slack Webhook URL
""",
    cron_expression="0 0 9 * * *"  # 每天上午 9:00
)
```

### 每周报告示例（前一周）

```python
# 每周一上午 9:00 安排每周报告
create_cron_job(
    job_title="DagenoAI Weekly GEO Report",
    job_instruction="""运行 dageno-geo-reporter 技能以生成并分发前一周的 GEO 报告。

执行以下命令：
python /home/ubuntu/skills/dageno-geo-reporter/scripts/generate_and_distribute_reports.py \
  --api_key "YOUR_API_KEY" \
  --distribution_type "feishu" \
  --webhook_url "YOUR_WEBHOOK_URL" \
  --start_date "$(date -d '8 days ago' +%Y-%m-%d)" \
  --end_date "$(date -d '2 days ago' +%Y-%m-%d)"

请将以下内容替换为实际值：
- YOUR_API_KEY: 您的 DagenoAI API 密钥
- YOUR_WEBHOOK_URL: 您的飞书/Slack Webhook URL
""",
    cron_expression="0 0 9 * * 1"  # 每周一上午 9:00
)
```

## 文件结构

```
dageno-geo-reporter/
├── README.md                          # 本文档
├── SKILL.md                           # 技能定义文档
├── scripts/
│   ├── dageno_mcp_client.py          # DagenoAI 开放 API 客户端
│   ├── generate_charts.py            # 图表生成模块
│   ├── distribute_report.py           # 报告分发模块
│   └── generate_and_distribute_reports.py  # 主脚本
├── templates/                        # 图表模板目录
│   ├── geo_visibility_bar_chart.png
│   ├── citation_domains_bar_chart.png
│   └── topics_bar_chart.png
└── references/
    └── api_reference.md              # API 参考文档
```

## 故障排除

### 图表中文显示问题

1. 检查是否安装了中文字体：
   ```bash
   fc-list :lang=zh -f "%{family}\n" | head -5
   ```
2. 如果没有中文字体，请安装中文字体包：
   ```bash
   sudo apt-get install fonts-noto-cjk
   ```

### 分发失败

1. **无效的 Slack/飞书 Webhook**：
   - 检查 Webhook URL 是否正确
   - 确认 Webhook 未过期（Slack Webhook 通常不会过期）
   - 测试 Webhook 是否正常工作

2. **电子邮件发送失败**：
   - 使用 Gmail 时，生成应用程序专用密码（而非登录密码）
   - 检查 SMTP 服务器和端口设置
   - 确认发件人电子邮件和密码正确

### API 调用失败

1. 确认 API 密钥有效
2. 检查网络连接
3. 查看日志中的详细错误消息

## 依赖项

```
matplotlib>=3.5.0
requests>=2.28.0
```

安装依赖项：
```bash
pip install matplotlib requests
```
```
