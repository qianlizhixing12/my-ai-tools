---
name: weread
description: 微信读书阅读数据助手 — 获取最新一周 / 本周 / 所有时期阅读统计数据
version: 1.1.0
---

# WeRead 阅读数据助手

通过 MCP 工具 `weread_get_reading_stats` 获取微信读书阅读数据，
支持查询最新一周（上周完整周）、本周（当前周至今）、所有时期（总计）的阅读统计。

## 前置条件

- MCP Server 由 Codex 自动管理，启动 session 后工具自动挂载
- MCP 工具 `weread_get_reading_stats` 已注册即可直接调用

## 能力

| 查询类型 | 说明 | MCP 工具 | 核心参数 |
|----------|------|----------|----------|
| **本周** | 当前自然周（周一至今）的阅读数据 | `weread_get_reading_stats` | `mode="weekly"` |
| **最新一周/上周** | 上一个完整自然周的阅读数据 | `weread_get_reading_stats` | `mode="weekly"` + `baseTime=上周一时间戳` |
| **所有时期/总计** | 自注册以来全部阅读数据 | `weread_get_reading_stats` | `mode="overall"` |
| **本月** | 当前自然月阅读数据 | `weread_get_reading_stats` | `mode="monthly"` |
| **本年** | 当前自然年阅读数据 | `weread_get_reading_stats` | `mode="annually"` |
| **自定义周期** | 任意起止日期区间 | `weread_get_reading_stats` | 多个 mode 组合，参考 `readdata.md` |

## 工作流

### 1. 获取本周阅读数据

直接调 `weread_get_reading_stats(mode="weekly")`。
回包包含本周的阅读时长、天数、排行、偏好等。

### 2. 获取最新一周/上周阅读数据

计算上周一 00:00 的 Unix 时间戳（秒），作为 `baseTime` 传入：

```
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
last_monday = now - timedelta(days=now.weekday() + 7)
last_monday_midnight = int(last_monday.replace(
    hour=0, minute=0, second=0, microsecond=0
).timestamp())
```

调 `weread_get_reading_stats(mode="weekly", base_time=last_monday_midnight)`。

### 3. 获取所有时期阅读数据

调 `weread_get_reading_stats(mode="overall")`。

### 4. 组合查询

如需同时展示最新一周、本周、所有时期，进行并行查询（同时调多次 `weread_get_reading_stats`）。

## 字段解读

所有回包字段的详细说明见 `readdata.md`。关键规则：

- **阅读时长（秒）**：`totalReadTime` 是秒，展示时转为 "X小时Y分钟"
- **阅读天数**：`readDays` 是有效阅读天数（单日阅读满 1 分钟算 1 天）
- **日均时长**：`dayAverageReadTime` 是自然日平均（秒），不是阅读日平均
- **读书排行**：`readLongest[]` 按时长降序，低于 5 分钟被过滤
- **时间戳**：所有 Unix 时间戳展示时转为 YYYY-MM-DD 格式

## 输出格式

- 总览：阅读天数、总时长、自然日均时长
- 与上一周期对比（增长/下降百分比）
- 读书排行 Top 5：书名 + 阅读时长
- 阅读统计摘要：读过本数、读完本数、笔记数等
- 偏好分析：分类、时段、作者（如有）

**示例输出：**

> **本周阅读统计**
> 阅读 3 天，共 5 小时 32 分钟，日均 47 分钟（较上周 ↑20%）
> 排行：1. 《三体》2 小时 15 分  2. 《深入理解计算机系统》1 小时 30 分
> 读过 2 本，读完 0 本，笔记 5 条
> 偏好：文学、编程

> **所有时期阅读统计**
> 累计阅读 128 天，共 312 小时 45 分钟
> 读过 45 本，读完 12 本
> 偏好：文学、计算机科学

## 注意事项

1. 展示时长必须将秒转为 "X小时Y分钟" 格式
2. 日均时长 = `dayAverageReadTime`（自然日平均），不是阅读日平均
3. 阅读天数 = `readDays`，不是 `totalReadTime / dayAverageReadTime`
4. `totalReadTime` 是总时长，优先于 `readTimes` 累加
5. 跨周期查询时，完整周期用 `totalReadTime`，边界周期用 `dailyReadTimes` 做日级扣减
6. 所有时间戳展示格式为 YYYY-MM-DD
