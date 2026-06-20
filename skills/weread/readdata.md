# readdata — 阅读统计字段参考

本文档描述 `weread_get_reading_stats` MCP 工具返回的字段含义。
用于解读阅读数据回包，正确展示阅读时长、天数、排行和偏好分析。

> **使用前必须阅读本文件字段说明。** 阅读统计字段容易因字段名产生误判，
> 尤其是所有阅读时长字段的单位。禁止凭字段名或数值大小推断单位。

## 请求参数

通过 MCP 工具 `weread_get_reading_stats` 获取数据，支持以下参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 否 | 统计维度：`weekly`=本周, `monthly`=本月, `annually`=本年, `overall`=总计。默认 `monthly`。 |
| `base_time` | int | 否 | 基准时间戳（Unix 秒）。0=当前周期，此时服务端会归一化到周期起点（周一/月初/年初）。传历史时间戳可查看该时间戳所在周期的数据。 |

## 回包字段说明

字段按 `mode` 和数据条件可选返回：

| 字段 | 说明 |
|------|------|
| `baseTime` | 统计周期的基准时间戳：`weekly` 为周一 00:00，`monthly` 为月初 00:00，`annually` 为年初 00:00，`overall` 为 0 |
| `readTimes` | 分桶阅读/收听总时长（对象，key 为分桶起始时间戳，value 为**秒数**）。`weekly`/`monthly` 通常按天分桶，`annually` 按月分桶，`overall` 按年分桶 |
| `dailyReadTimes` | 年度模式可能返回的每日阅读时长明细（对象，key 为日期时间戳，value 为**秒数**）；用于日历明细展示，不应替代 `totalReadTime` 作为总量口径 |
| `readDays` | 有效阅读天数。服务端按有效阅读规则计算，当前规则为单日阅读满 1 分钟 |
| `totalReadTime` | 当前请求周期的总阅读/收听时长（**秒**）。统计总时长时优先使用该字段，`readTimes` 仅用于明细展示；**禁止误当成分钟或小时** |
| `dayAverageReadTime` | 日均阅读/收听时长（**秒**），分母是当前周期已过去的自然日数或历史完整周期自然日数，不是 `readDays` |
| `compare` | 与上一周期的日均时长对比比例；正数表示增长，负数表示下降。只在当前周期且上一周期数据足够时返回，`0.2` 表示约增长 20% |
| `readLongest` | 读得最多的书/有声内容排行数组，最多 10 条，按 `readTime` 降序；低于 5 分钟的条目会被过滤 |
| `readLongest[].book` | 书籍信息对象（电子书/出版书），包含 `bookId`、`title`、`author`、`cover` 等 |
| `readLongest[].albumInfo` | 有声内容信息对象；当排行条目是有声书/专辑时返回 |
| `readLongest[].readTime` | 该书或有声内容在当前统计范围内的阅读/收听时长（**秒**） |
| `readLongest[].recordReadingTime` | 该书的朗读/记录类阅读时长（秒），存在时才返回 |
| `readLongest[].tags` | 标签数组，目前常见值包括 `笔记最多`、`单日阅读最久` |
| `readStat` | 阅读统计摘要数组 |
| `readStat[].stat` | 统计项名称，常见为 `读过`、`读完`、`阅读`、`笔记` |
| `readStat[].counts` | 统计值文案，如 `12本`、`45天`、`120条` |
| `readStat[].scheme` | 对应统计项的 App 跳转链接，可能为空 |
| `preferCategory` | 偏好阅读分类数组，最多 8 个 |
| `preferCategory[].categoryTitle` | 分类名称 |
| `preferCategory[].val` | 分类偏好权重，按最高分类阅读时长归一化后的相对值 |
| `preferCategory[].readingTime` | 该分类阅读时长（**秒**） |
| `preferCategory[].readingCount` | 该分类阅读本数 |
| `preferCategoryWord` | 偏好分类文案，如 `偏好阅读文学` |
| `preferTime` | 24 小时阅读时段分布数组，值为**秒数**。注意输出顺序从 6 点开始，依次到次日 5 点，不是从 0 点开始 |
| `preferTimeWord` | 偏好时段文案。总偏好时段数据不足 10 小时时可能不返回 |
| `preferAuthor` | 偏好作者数组。只有作者数据达到展示阈值时返回 |
| `preferAuthor[].name` | 作者名 |
| `preferAuthor[].count` | 阅读该作者的书本数 |
| `preferAuthor[].readTime` | 阅读该作者作品的时长，格式化字符串，如 `5小时30分钟`，不是秒数 |
| `preferPublisher` | 偏好出版社数组。至少 3 个出版社且最高出版社阅读本数达到阈值时返回 |
| `preferPublisher[].name` | 出版社名 |
| `preferPublisher[].count` | 阅读该出版社书籍的本数 |
| `readRate` | 文字阅读占比百分比。当总时长不足 1 小时或文字阅读占比过高时不返回 |
| `wrReadTime` | 文字阅读时长（秒），通常为 `totalReadTime - wrListenTime` |
| `wrListenTime` | 听书/TTS/有声内容时长（秒） |
| `rank` | 本周好友阅读排行信息；仅当前周且未隐藏排行时返回 |
| `rank.text` | 排行文案，如 `朋友中排第3名` |
| `registTime` | 用户注册时间戳 |

## 周期组合规则

`weread_get_reading_stats` 只支持按固定自然周期查询，不支持直接传任意起止日期。
遇到"某天至今"、"某月中旬到现在"、"跨年区间"这类请求时，应通过多次调用结果组合计算。

| mode | 周期粒度 | base_time 行为 | 适合用途 |
|------|----------|---------------|----------|
| `weekly` | 自然周 | 归一到该周周一 00:00 | 本周、某历史周 |
| `monthly` | 自然月 | 归一到该月 1 日 00:00 | 本月、某历史月、区间边界扣减 |
| `annually` | 自然年 | 归一到该年 1 月 1 日 00:00 | 某年全年、今年至今、跨年区间拼接 |
| `overall` | 全部历史 | 固定为 0 | 总计，不适合拆任意日期区间 |

**组合原则：**

1. 优先用较大周期减少调用次数：整年用 `annually`，整月用 `monthly`。
2. 跨年区间按自然年拆分：历史整年 + 当前年至今。
3. 起点落在年/月中间时，可用"大周期 - 起点之前的完整小周期"近似组合；
   如果接口返回 `dailyReadTimes`，可对边界日期做日级精确扣减。
4. **完整周期**使用该周期回包的 `totalReadTime`；
   **不完整边界周期**优先使用 `dailyReadTimes` 精确扣除起点前/终点后的日期。
5. 不要把截断展示的 `readTimes` 当作主结果；`readTimes` 仅用于明细展示或交叉校验。

## 输出格式

- **总览**：阅读天数、总时长（转为 x 小时 y 分钟）、自然日均时长、与上期对比（增长/下降百分比）
- **读书排行**：列出读得最多的书/有声内容，书名或专辑名 + 阅读/收听时长
- **阅读统计**：读过本数、读完本数、阅读天数、笔记数等
- **偏好分析**：偏好分类、偏好时段、偏好作者、偏好出版社/版权方（如有）
- 时长单位统一转换：所有阅读时长字段均按**秒**处理，秒 → "x 小时 y 分钟"格式；
  不得把 `totalReadTime` 当成分钟或小时
