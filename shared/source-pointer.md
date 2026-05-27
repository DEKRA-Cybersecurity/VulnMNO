# Source pointer

Section index into [../docs/VulnMNO.md](../docs/VulnMNO.md). Use this to jump straight to the section you need rather than re-reading the whole document.

| Section | Topic | Used heavily by stage |
| --- | --- | --- |
| §2 | Product description | 01 |
| §4 | Stakeholders | 01 |
| §5 | High-level architecture (component list) | 01 |
| §7.1 | Android app sections (Home, Account, Balance, Shop, …) | 05 (screen inventory) |
| §7.2–§7.14 | Component responsibilities | 02 (endpoint grouping), 03 (entity ownership) |
| §8 | Roles and permissions | 02 (authorization), 01 |
| §9.1–§9.6 | Customer journeys | 01 (requirements), 02 (endpoint composition), 05 (screen flows), 07 (E2E tests) |
| §10 | Main business operations | 02 |
| §11 | Data model overview (entities + fields) | 03 |
| §12 (endpoints) | Example API structure | 02 (canonical source for `EP-` IDs) |
| §13 | Example request/response objects | 02, 04 (response shape exactness) |
| §12 (events block) | Example operational events | 04 (audit service write side) |
| §13 (assumptions) | Operational assumptions | 02 (auth/session model), 04 (business rules) |

## Specific anchors worth bookmarking

- **Endpoint inventory.** §12 is the canonical list. When stage 02 names an endpoint, it must match a row in §12 unless explicitly extending it (and the extension is logged in stage 02's output).
- **Payload shapes.** §13 examples are authoritative for field names and JSON shape. Pydantic schemas in stage 03/04 must produce output that matches §13 byte-for-byte (modulo dynamic values).
- **Currency = EUR, money formatted as decimal with two digits.** §13 examples (`"price": 9.99`, `"finalPrice": 7.99`).
- **ID format.** §13 uses prefixed strings: `CUST-10001`, `ACC-10001`, `PUR-90001`, `DATA-10GB-7D`. The API must keep this format; do not expose integer primary keys.
- **OTP validity = 5 min.** §13.1. Hard requirement for stage 04's auth implementation.
- **Session lifetime.** §13.1 says "several days unless manually revoked". Stage 02 decides the exact JWT TTL; stage 04 implements it.
