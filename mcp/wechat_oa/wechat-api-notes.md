# WeChat Official Account API Notes

Gathered from live testing on 2026-06-01 with a personal subscription account (个人订阅号).

## Account Type: 个人订阅号 (未认证)

### API Permissions Tested
| Endpoint | Status | Notes |
|----------|--------|-------|
| `/cgi-bin/token` | ✓ | Works with AppID + AppSecret |
| `/cgi-bin/draft/add` | ✓ | Creates drafts in draft box |
| `/cgi-bin/draft/count` | ✓ | Returns `{total_count: N}` (no errcode on success) |
| `/cgi-bin/draft/delete` | ✓ | Deletes drafts by media_id |
| `/cgi-bin/freepublish/submit` | ✗ 48001 | `api unauthorized` — personal accounts cannot auto-publish |
| `/cgi-bin/freepublish/batchget` | ✗ 48001 | Same restriction |
| `/cgi-bin/material/add_material` | ✓ | Upload images for cover (jpg/png, ≤10MB, returns media_id) |
| `/cgi-bin/media/uploadimg` | ✓ | Upload images for article body (returns mmbiz.qpic.cn URL) |
| `/cgi-bin/freebiz/album/*` | ✗ 404 | 合集 API unavailable for personal accounts |
| `/cgi-bin/tags/*` | ✗ 48001 | Tag API unauthorized |

### Title Byte Limit
- **NOT 64 characters** as commonly documented.
- Actual limit appears to be ~60-64 **UTF-8 bytes** for the draft API.
- Chinese characters are 3 bytes each, so ~20 Chinese chars max.
- 34 ASCII bytes: ✓ OK
- 33 bytes (11 Chinese chars): ✗ FAIL (errcode 45003)
- 30 bytes (10 Chinese chars): ✓ OK
- Mixed content at 32 bytes: ✓ OK
- Original title "ai使用场景思考+程序员agent环境部署" (47 bytes) → 45003

### JSON Encoding Trap (CRITICAL)
- `requests.post(url, json=payload)` → `ensure_ascii=True` by default
- All Chinese chars escaped to `\uXXXX` in the JSON body
- WeChat stores the literal `\uXXXX` strings → garbled display in draft box
- **Fix**: `json.dumps(payload, ensure_ascii=False).encode('utf-8')` + explicit `Content-Type: application/json; charset=utf-8`
- Max content length: unknown but 6,913 chars worked fine.

### Image Upload: Two Endpoints — Do NOT Mix
| Use case | Endpoint | Returns | HTML/JSON format |
|----------|----------|---------|-------------------|
| Article body | `/cgi-bin/media/uploadimg` | `http://mmbiz.qpic.cn/...` URL | `<img src="URL">` |
| Cover image | `/cgi-bin/material/add_material` | `media_id` string | `"thumb_media_id": "MEDIA_ID"` in payload |

Using `material/add_material` media_id in `<img data-src="MEDIA_ID">` does NOT work via API — that format is specific to the WeChat web editor.

### 原创 (Original Declaration)
- Add to draft article: `"copyright_type": 1, "copyright_author": "nxx"`
- API accepts it. Effect depends on account having 原创 permission (silently ignored if not).

### 合集 (Collections/Albums)
- All tested endpoints return 404 or 48001 — NOT available for personal accounts via API.
- Must be set manually in WeChat back-end after publishing.

### IP Whitelist
- Required for ALL API calls. Server IPv4 must be in whitelist.
- Server IP at time of testing: `124.90.54.250` (China Unicom, Hangzhou, dynamic)
- Dynamic IPs from home broadband WILL break the whitelist when IP changes.
- Config location: 设置与开发 → 基本配置 → IP白名单

### Draft API Payload
```json
{
  "articles": [{
    "title": "...",
    "content": "...",
    "thumb_media_id": "...",   // REQUIRED — will fail with 40007 if missing
    "content_source_url": "",
    "need_open_comment": 0,
    "only_fans_can_comment": 0
  }]
}
```

### Content HTML Restrictions
WeChat's editor only accepts a subset of HTML. Key rules:
- No `<div>`, no `class`, no `id` attributes
- Allowed: section, h1-h6, p, span, strong, em, br, ul, ol, li, img, a, blockquote, pre, code
- Styles MUST be inline (style="..."). No external CSS.
- Images MUST use `<img src="URL">` where URL comes from `/cgi-bin/media/uploadimg` (returns `mmbiz.qpic.cn` URL). Do NOT use `data-src` with media_id from `material/add_material`.
- Max content length: unknown but 6,913 chars worked fine.
