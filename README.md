# daily_brief — 每日情报 Agent

每天定时自动生成 4 份报告并推送到微信（ClawBot）。从 [video_kb](../video_kb) 项目演化而来，复用了其 LLM 接口 / 转写链路 / 研究 Agent 的思路。

## 任务（一任务一报告）

| 任务 | 命令 | 内容 | 数据源 |
|---|---|---|---|
| ① AI 产业日报 | `run_task.py ai_industry` | 科技大厂动态、战略、AI 产品发布 | 量子位/InfoQ中文/TechCrunch·AI/MIT科技评论/HN(Algolia)/GitHub Trending（RSSHub 可追加 36氪/华尔街见闻/机器之心） |
| ② AI 科研日报 | `run_task.py ai_research` | 有影响力的新论文：创新点 + 影响 | HuggingFace Daily Papers + arXiv |
| ③ 求职情报日报 | `run_task.py ai_jobs` | 校招/实习开放、面经建议、大厂内幕 | V2EX求职 + B站搜索（需 BILI_SESSDATA）（RSSHub 可追加 知乎热榜/牛客） |
| ④ 情感 UP 主日报 | `run_task.py emotion_ups` | 清单内 UP 主新视频 → 口播转写 → 要点总结 | B站公开 API + yt-dlp + faster-whisper |

## 快速开始

```bash
cd daily_brief
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入 LLM_API_KEY、ClawBot 三项
```

测试（只采集不推送）：
```bash
python run_task.py ai_research --dry-run     # 看能抓到什么
python run_task.py ai_industry --no-push     # 生成报告但不发微信
python run_task.py all                       # 全量
```

## 微信推送（ClawBot）

走 [WeClawBot-API](https://github.com/Cp0204/WeClawBot-API) 协议：
`POST {CLAWBOT_API_URL}/bots/{CLAWBOT_BOT_ID}/messages`，Bearer token，body `{"text": "..."}`。
长报告自动按 1800 字分段推送。不配 ClawBot 三件套则只落盘不推送（报告在 `data/reports/`）。

## 服务器部署（cron）

```bash
git clone <repo> /opt/daily_brief && cd /opt/daily_brief
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填好配置
mkdir -p logs
```

crontab 示例（服务器时区建议 Asia/Shanghai，错峰避免源站限流）：

```cron
# 07:30 AI 产业日报
30 7 * * * cd /opt/daily_brief && .venv/bin/python run_task.py ai_industry >> logs/cron.log 2>&1
# 08:00 AI 科研日报
0 8 * * * cd /opt/daily_brief && .venv/bin/python run_task.py ai_research >> logs/cron.log 2>&1
# 08:30 求职情报日报
30 8 * * * cd /opt/daily_brief && .venv/bin/python run_task.py ai_jobs >> logs/cron.log 2>&1
# 21:00 情感 UP 主日报（转写较耗时，放晚上）
0 21 * * * cd /opt/daily_brief && .venv/bin/python run_task.py emotion_ups >> logs/cron.log 2>&1
```

## 配置说明（.env）

| 变量 | 说明 |
|---|---|
| `LLM_API_KEY/BASE_URL/MODEL` | OpenAI 兼容协议，DeepSeek/Kimi/通义均可。默认 deepseek-chat，每天 4 份报告成本约几毛钱 |
| `CLAWBOT_API_URL/BOT_ID/TOKEN` | WeClawBot-API 三件套 |
| `PUSH_ENABLED` | false 时只生成报告文件不推送 |
| `RSSHUB_BASE` | 可选。自建 RSSHub 后解锁 36氪快讯/华尔街见闻/机器之心/知乎热榜/牛客讨论区 |
| `BILI_SESSDATA` | B站登录 Cookie。**情感 UP 主任务基本必需**（B站接口未登录风控严格）：浏览器登录 bilibili.com → F12 → Application → Cookies → 复制 `SESSDATA` 值 |
| `WHISPER_MODEL` | 情感任务转写模型。CPU 用 `small`（10 分钟视频约 2-4 分钟），有 GPU 可 `medium` |

## 维护

- **加 UP 主**：编辑 `data/up_list.txt`，每行一个昵称（搜索取第一个结果，尽量写全名）；昵称搜索被风控时可直接写 `uid:123456`（UP主空间页 URL 里的数字）。
- **加 RSS 源**：改 `tasks/ai_industry.py` 的 `_feeds()` 或对应任务的 collect。
- **去重**：`data/state/*.json` 记录已处理条目（14 天窗口），删掉即全量重跑。
- **报告**：`data/reports/{任务}_{日期}.md`。

## 合规

仅个人学习使用；B站内容请控制频率，勿二次分发；知乎/B站接口均为公开端点，如失效请提 issue 换源。
