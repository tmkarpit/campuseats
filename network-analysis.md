# Network Analysis

Website tested: `https://www.iana.org/`

Method: opened the site for a no-cache reload and reviewed the request waterfall metrics. Cache was disabled for the reload.

Test time: 15 Aug 2026, 11:23 UTC

## Summary

- Request count: 7
- Total page size: 194,057 bytes, about 189.5 KiB
- Slowest resource: `https://www.iana.org/static/css/iana_website.3c174467e53c.css`
- Slowest resource time: 878 ms
- 3xx responses seen: none
- 4xx responses seen: none

## Requests Observed

| # | Resource | Status | Type | Size | Time |
|---|---|---:|---|---:|---:|
| 1 | `https://www.iana.org/` | 200 | HTML document | 6,253 bytes | 561 ms |
| 2 | `/static/js/jquery.a8e7cabd4d49.js` | 200 | JavaScript | 78,748 bytes | 99 ms |
| 3 | `/static/js/dtable.46ee921d4414.js` | 200 | JavaScript | 2,824 bytes | 79 ms |
| 4 | `/static/js/relative-time.79f0e30be3b8.js` | 200 | JavaScript | 3,179 bytes | 354 ms |
| 5 | `/static/css/iana_website.3c174467e53c.css` | 200 | CSS | 88,241 bytes | 878 ms |
| 6 | `/static/img/bookmark_icon.e14a2530b3e9.ico` | 200 | Icon | 7,406 bytes | 50 ms |
| 7 | `/favicon.ico` | 200 | Icon | 7,406 bytes | 212 ms |

## Notes

All observed resources returned `200 OK`, so the page loaded successfully with no redirect, missing-file, or client-error responses in the waterfall. The CSS file was the slowest single resource even though the largest file by size was also CSS; this suggests static styling was the main load cost for this page.
