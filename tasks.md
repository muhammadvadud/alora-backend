# Alora Backend — Ish rejasi (tasks.md)

> Manba: `plan/01-BACKEND-TZ.md` · Qoidalar: `rules.md`
> Belgilar: `[ ]` boshlanmagan · `[~]` jarayonda · `[x]` tugallangan (test o'tgan)
> Har bir ish tugagach shu fayl **o'sha ishning commit'i ichida** yangilanadi.

**Umumiy holat:** 197 / 201 bajarildi (2 jarayonda) · 335 test o'tgan · coverage 87% · ruff toza (2026-09-13)

---

## Bosqich 0 — Poydevor (infratuzilma)

- [x] 0.1 Repo boshlanishi: `.gitignore`, `README.md`, `LICENSE`, `.editorconfig`
- [x] 0.2 `pyproject.toml` — Python 3.13, bog'liqliklar, ruff/mypy/pytest sozlamalari
- [x] 0.3 Django 5.x loyihasi: `config/` + `settings/{base,dev,prod}.py`
- [x] 0.4 `.env.example` va `django-environ` orqali sozlash
- [x] 0.5 PostgreSQL 16 ulanishi va `dj_database_url`
- [x] 0.6 Redis ulanishi (cache + Celery broker + pub/sub)
- [x] 0.7 `config/celery.py` — app, navbatlar (`default`, `usage`, `heavy`), beat jadvali
- [x] 0.8 ASGI sozlash (`config/asgi.py`, Uvicorn)
- [x] 0.9 `structlog` JSON logging + Sentry
- [x] 0.10 `pre-commit`: ruff, ruff-format, mypy, detect-secrets, migratsiya tekshiruvi
- [x] 0.11 `docker/` — Dockerfile, docker-compose (postgres, redis, django, celery-worker, celery-beat, nginx)
- [x] 0.12 `scripts/entrypoint.sh` — migrate + collectstatic + server
- [x] 0.13 CI (GitHub Actions): lint → mypy → test → coverage gate (`--cov-fail-under=70`)
- [~] 0.14 `/health/` endpoint (DB, Redis, gRPC holati)

## Bosqich 1 — `apps/common` (umumiy poydevor)

- [x] 1.1 `BaseModel` — UUID pk, `created_at`, `updated_at`, `is_active`
- [~] 1.2 `TenantScopedModel` + `TenantScopedQuerySetMixin` (avtomatik tenant filtri)
- [x] 1.3 `StandardCursorPagination` (default 20, max 100)
- [x] 1.4 Yagona xato formati: `custom_exception_handler` + `errors` maydoni
- [x] 1.5 Rol permission klasslari: `IsEmployee`, `IsManager`, `IsAdmin`, `IsOwnerOrManager`
- [x] 1.6 Umumiy `TextChoices` to'plamlari (role, price_unit, part_role, status)
- [x] 1.7 `factory_boy` bazaviy fabrikalar va `conftest.py`
- [x] 1.8 i18n karkasi (uz asosiy, ru zaxira), xato matnlari o'zbekcha
- [x] 1.9 Testlar: pagination, xato formati, tenant scoping

## Bosqich 2 — `apps/accounts` (auth va rollar)

- [x] 2.1 `Tenant` modeli (name, address, phone, currency, timezone)
- [x] 2.2 `User` modeli (`AbstractBaseUser`, phone login, role, tenant, device_id)
- [x] 2.3 `UserManager` — `create_user`, `create_superuser`
- [x] 2.4 JWT sozlash: access 15 daq, refresh 30 kun, rotation + blacklist
- [x] 2.5 Token payload: `user_id`, `role`, `tenant_id`
- [x] 2.6 `POST /auth/login/` — phone + password
- [x] 2.7 `POST /auth/refresh/`
- [x] 2.8 `POST /auth/logout/` — refresh bekor qilish
- [x] 2.9 `GET /auth/me/` — profil + rol + limit holati
- [x] 2.10 Login rate limit (5/daqiqa/IP)
- [x] 2.11 Argon2 password hasher
- [x] 2.12 Testlar: login, refresh rotation, noto'g'ri parol, bloklangan foydalanuvchi

## Bosqich 3 — `apps/catalog` (mahsulot bazasi)

- [x] 3.1 `Category` — parent (self FK), slug, sort_order
- [x] 3.2 `Product` — AI atributlari bilan (fabric_type, pattern, style, transparency, density, composition, care, recommended_rooms, recommended_coef, default_width_m, is_sewing_required, segment, tags)
- [x] 3.3 `ProductVariant` — sku, color_name, color_hex, width_m, price, price_unit, old_price, cost_price
- [x] 3.4 `ProductImage` — product/variant, siqilgan o'lchamlar, is_primary
- [x] 3.5 `Fason` shabloni
- [x] 3.6 `FasonPart` — role, width_share, height_share, default_coef
- [x] 3.7 `FasonAccessory` — category, default_qty, qty_formula
- [x] 3.8 Indekslar: `sku`, `code`, `category`, `segment`
- [x] 3.9 Read serializerlar (nested variant + rasm) va Write serializerlar
- [x] 3.10 `cost_price` faqat admin'ga ko'rinadigan qilib yopish
- [x] 3.11 `GET /catalog/categories/`
- [x] 3.12 `GET /catalog/products/` — filtr: category, style, room, segment, price_unit, search, min_price, max_price
- [x] 3.13 `GET /catalog/products/{id}/` — variant va rasmlar bilan
- [x] 3.14 `GET /catalog/variants/{id}/`
- [x] 3.15 `POST/PATCH/DELETE /catalog/products/` (manager+)
- [x] 3.16 `POST/PATCH/DELETE /catalog/variants/` (manager+)
- [x] 3.17 `POST /catalog/variants/bulk-price/` — foiz yoki summa bo'yicha ommaviy narx
- [x] 3.18 `POST /catalog/products/{id}/images/` — multipart yuklash
- [x] 3.19 `DELETE /catalog/images/{id}/`
- [x] 3.20 Rasm siqish Celery task (thumbnail 300px, to'liq 1200px)
- [ ] 3.21 `POST /catalog/import/` — Excel/CSV import
- [x] 3.22 `GET/POST/PATCH/DELETE /catalog/fasons/`
- [x] 3.23 Seed skript: kategoriyalar, namuna mahsulot va aksessuarlar
- [x] 3.24 N+1 nazorati (`assertNumQueries`) va 300 ms javob testi
- [x] 3.25 Testlar: filtr, qidiruv, permission, tannarx yopiqligi

## Bosqich 4 — `apps/pricing` (narx va hisob)

- [x] 4.1 `CalcRule` — key, value, unit, description, applies_to
- [x] 4.2 `ServicePrice` — sewing, install, delivery, tape, hook, weight_tape
- [x] 4.3 `DiscountTier` — min_amount, percent
- [x] 4.4 `DiscountPolicy` — qo'lda chegirma chegaralari, stack_with_tier
- [x] 4.5 `OrderDefaults` — prepayment_percent, delivery_amount, deadline_days
- [x] 4.6 `ModelPricing` — LLM narxlari va usd_to_uzs kursi
- [x] 4.7 Boshlang'ich qiymatlar migratsiyasi (coef_default, seam_allowance, hem_allowance, hook_step, round_area_to, round_total_to, min_order_amount, waste_warn_percent)
- [x] 4.8 `calculator.py` — yuza hisobi (bo'lak, koeffitsient, zapas)
- [x] 4.9 Narx birligi bo'yicha hisob: `per_sqm`, `per_piece`, `per_meter`
- [x] 4.10 Chiqindi (waste) hisobi va `waste_warn_percent` ogohlantirishi
- [x] 4.11 Xizmat qatorlari hisobi (tikuv, montaj, tasma, ilgich, yetkazish)
- [x] 4.12 Chegirma qo'llash: tier tanlash + qo'lda chegirma chegarasi
- [x] 4.13 Yaxlitlash tartibi (yuza → qator → jami)
- [x] 4.14 `POST /calc/preview/` endpointi
- [x] 4.15 `GET/PATCH /pricing/calc-rules/`
- [x] 4.16 `GET/PATCH /pricing/services/`
- [x] 4.17 `GET/POST/PATCH/DELETE /pricing/discount-tiers/`
- [x] 4.18 `GET/PATCH /pricing/discount-policy/`
- [x] 4.19 `GET/PATCH /pricing/order-defaults/`
- [x] 4.20 `ModelPricing` CRUD (faqat admin)
- [x] 4.21 `tests/fixtures/calc_cases.json` — 20 ta etalon misol (Go bilan umumiy)
- [x] 4.22 Etalon testlar: 20 misol 1:1 mos kelishi
- [x] 4.23 Chekka holat testlari: 10 bo'lakli parda, nol o'lcham, manfiy narx

## Bosqich 5 — `apps/knowledge` (sotuv bilimlari)

- [x] 5.1 `KnowledgeRule` — kind, condition (JSON), recommendation, priority
- [x] 5.2 `GET/POST/PATCH/DELETE /knowledge/rules/` (manager+)
- [x] 5.3 Shartga mos qoidalarni tanlash selektori (priority bo'yicha)
- [x] 5.4 Go'ga sinxronlash uchun serializatsiya formati
- [x] 5.5 Testlar: shart moslashuvi, ustuvorlik tartibi

## Bosqich 6 — gRPC shartnoma va klient

- [x] 6.1 `protos/alora.proto` yozilishi (Agent, Catalog, Backend servislari)
- [x] 6.2 `scripts/gen_proto.sh` — `grpc_gen/` generatsiyasi (ishga tushirildi, `grpc_gen/` generatsiya qilindi)
- [x] 6.3 Proto'ni Go repo bilan umumiy qilish — `scripts/export_proto.sh` + `docs/GO-CONTRACT.md` (Go repo bu mashinada yo'q, submodule o'rniga eksport skripti)
- [x] 6.4 `apps/chat/grpc_client.py` — ulanish pool'i, retry, deadline 60s, keep-alive
- [x] 6.5 Go ishlamaganda tushunarli xato (503, "AI xizmati vaqtincha ishlamayapti")
- [x] 6.6 `Catalog.Snapshot` server tomoni (sahifalab)
- [x] 6.7 `Catalog.Watch` stream — delta push
- [x] 6.8 `Backend.ReportUsage` qabul qilish
- [x] 6.9 `Backend.SaveOrderDraft` qabul qilish (draft `Order` yaratadi, Conversation bilan bog'laydi)
- [x] 6.10 `Backend.LogMessage` qabul qilish
- [~] 6.11 `Agent.Health` tekshiruvi `/health/` ichida
- [x] 6.12 gRPC mock testlari
- [x] 6.13 Kontrakt 1.1 — `alora.proto` kengaytmasi: `CatalogSnapshot` 8–13 (`service_prices`, `discount_tiers`, `discount_policy`, `order_defaults`, `fasons`, `prompt`), yangi `Catalog*` xabarlari, `go_package` tuzatildi, `context`/`kind`/`items_json`/`FULL_RESYNC` hujjat izohlari (`docs/GO-CONTRACT.md` 1.1)
- [x] 6.14 `Catalog.Snapshot` — pricing/fason/prompt bloklari; mahsulotdan boshqa ro'yxatlar faqat birinchi sahifada; `catalog_payload.py` (Snapshot va delta uchun yagona manba)
- [x] 6.15 Gateway → Go `ChatRequest.context`: `role`, `customer_mode`, `conversation_id` (`build_agent_context`)
- [x] 6.16 `ChatEvent.kind="stage"` → SSE'ga 1:1 + Celery `update_conversation_stage` (`Conversation.stage`, `context.agent_state`)
- [x] 6.17 `Backend.SaveOrderDraft` → `create_order_from_draft` ulash (`items_json` sxemasi GO-CONTRACT §1.3; user `user_id` bo'yicha; xato → `OrderDraftResponse.error`)
- [x] 6.18 `grpc_client.py` — har chaqiruvda `x-service-token` (`AGENT_SERVICE_TOKEN` env) va `x-request-id` metadata (server tomoni ham bajarilgan)
- [x] 6.19 `Pricing.CalcPreview` RPC (hisob faqat Django'da — Go chaqiradi)
- [x] 6.20 gRPC server bootstrap: `run_grpc` command, 9091, compose servisi, `x-service-token` interceptor (server tomoni)

## Bosqich 7 — `apps/chat` (gateway)

- [x] 7.1 `Conversation` modeli — session_id, mode, status, stage, context, order FK
- [x] 7.2 `Message` modeli — role, content, tool_calls, tool_result, audio_url, tokenlar
- [x] 7.3 Indekslar: `Message.conversation`, `Conversation.session_id`
- [x] 7.4 `GET /conversations/` (employee — o'zi, manager — hammasi)
- [x] 7.5 `POST /conversations/` — session_id generatsiya
- [x] 7.6 `GET /conversations/{id}/messages/` — cursor pagination
- [x] 7.7 `POST /conversations/{id}/messages/` — **SSE stream** (asosiy endpoint)
- [x] 7.8 SSE oqim mantiqi: JWT → limit → rate limit → conversation → gRPC → frame
- [x] 7.9 Klient uzilganda gRPC context cancel
- [x] 7.10 `done` event'ida Message + UsageRecord saqlash (Celery)
- [x] 7.11 `DELETE /conversations/{id}/` — arxivlash
- [x] 7.12 `POST /conversations/{id}/reset/` — kontekst tozalash
- [x] 7.13 `GET /conversations/{id}/transcript/` — manager to'liq o'qishi
- [x] 7.14 `WS /ws/voice/{conversation_id}/` — ovozli kanal (Channels)
- [x] 7.15 Chat rate limit (Redis, rol bo'yicha)
- [x] 7.16 Async view ichida bloklovchi ORM chaqiruvi yo'qligini tekshirish
- [x] 7.17 Testlar: SSE oqimi (gRPC mock), uzilish, limit 429, permission
- [x] 7.18 VoiceChat: metadata uzatish, transcript/done qayta ishlash (kontrakt 1.4)

## Bosqich 8 — `apps/orders` (buyurtmalar)

- [x] 8.1 `Order` modeli — number, status, summalar, chegirma, avans, deadline
- [x] 8.2 Buyurtma raqami generatori: `ALR-2026-000123` (poyga holatisiz)
- [x] 8.3 `OrderMeasurement` — room_name, cornice_length_m, height_m, layers, coefficient
- [x] 8.4 `OrderCurtainPart` — variant, role, o'lcham, koeffitsient, `price_per_sqm` snapshot
- [x] 8.5 `OrderAccessory` — variant, qty, unit, `unit_price` snapshot
- [x] 8.6 `OrderItem` — xizmat qatorlari, `name_snapshot`
- [x] 8.7 Snapshot mantiqi: katalog o'zgarsa buyurtma o'zgarmasligi
- [x] 8.8 Status mashinasi va ruxsat etilgan o'tishlar
- [x] 8.9 `GET /orders/` — filtr: status, sana, xodim
- [x] 8.10 `POST /orders/` — AI draft'idan buyurtma yaratish
- [x] 8.11 `GET/PATCH /orders/{id}/`
- [x] 8.12 `POST /orders/{id}/confirm/` — tasdiqlash
- [x] 8.13 `POST /orders/{id}/status/` — izoh va sana bilan
- [x] 8.14 `GET /orders/statuses/` — status ro'yxati va o'tishlar
- [x] 8.15 `GET /orders/{id}/pdf/` — kommercheskiy taklif PDF
- [x] 8.16 Buyurtma summasini `calculator.py` orqali qayta hisoblash
- [x] 8.17 Employee faqat o'z buyurtmasini ko'rishi
- [x] 8.18 Testlar: snapshot, status o'tishlari, summa mosligi, permission

## Bosqich 9 — `apps/usage` (limit va statistika)

- [x] 9.1 `UsageRecord` — tokenlar, stt/tts, tool_calls, latency, cost_usd/uzs
- [x] 9.2 `UsageDaily` rollup jadvali
- [x] 9.3 `UsageLimit` — user yoki role, period, is_unlimited, max_*, on_exceed
- [x] 9.4 Limit tekshirish mantiqi (shaxsiy > rol > cheksiz)
- [x] 9.5 Xarajat hisobi `ModelPricing` bo'yicha (USD → UZS)
- [x] 9.6 `GET /usage/summary/?period=day|week|month&user=`
- [x] 9.7 `GET /usage/by-user/` — xodimlar reytingi
- [x] 9.8 `GET /usage/conversations/` — eng qimmat suhbatlar
- [x] 9.9 `GET /analytics/conversion/` — suhbat → buyurtma konversiyasi
- [x] 9.10 `POST /team/employees/{id}/limit/` — `is_unlimited` toggle bilan
- [x] 9.11 Statistika `UsageDaily` dan o'qilishi (xom jadvaldan emas)
- [x] 9.12 Testlar: limit tugaganda 429, cheksiz rejim, rollup to'g'riligi

## Bosqich 10 — Jamoa boshqaruvi (manager paneli)

- [x] 10.1 `GET /team/employees/` — xodimlar + bugungi faollik
- [x] 10.2 `POST /team/employees/` — xodim qo'shish
- [x] 10.3 `PATCH /team/employees/{id}/` — bloklash, rol, limit
- [x] 10.4 `GET /team/employees/{id}/conversations/`
- [x] 10.5 Ruxsatlar matritsasi bo'yicha to'liq test to'plami

## Bosqich 11 — System prompt boshqaruvi (admin)

- [x] 11.1 `PromptVersion` modeli (versiya, matn, muallif, sana)
- [x] 11.2 `GET /settings/prompt/` — joriy + tarix
- [x] 11.3 `POST /settings/prompt/` — yangi versiya
- [x] 11.4 `POST /settings/prompt/{version}/rollback/`
- [x] 11.5 Prompt o'zgarganda Go'ga xabar berish
- [x] 11.6 Testlar: faqat admin kirishi, rollback to'g'riligi

## Bosqich 12 — Katalog sinxronizatsiyasi (Django → Go)

- [x] 12.1 `post_save` / `post_delete` signallari (Product, Variant, CalcRule, KnowledgeRule)
- [x] 12.2 Redis pub/sub kanaliga delta e'lon qilish
- [x] 12.3 Versiya hisoblagichi (Redis `INCR`)
- [x] 12.4 `Catalog.Watch` stream orqali Go'ga push
- [x] 12.5 Versiya uzilishida qayta snapshot mantiqi
- [x] 12.6 Signal ichida og'ir ish yo'qligini tekshirish
- [x] 12.7 Testlar: delta e'loni, versiya o'sishi
- [x] 12.8 Delta `payload_json` barcha entity'lar uchun (Snapshot bilan bir xil proto-JSON) — Go delta'ni Snapshot'siz qo'llaydi
- [x] 12.9 Yangi signallar: `ServicePrice`, `DiscountTier`, `DiscountPolicy`, `OrderDefaults`, `Fason` (+`FasonPart`/`FasonAccessory` → butun fason), `PromptVersion` (faqat joriy; Redis yotsa endpoint yiqilmaydi)

## Bosqich 13 — Fon vazifalari (Celery)

- [x] 13.1 `save_usage_record`
- [x] 13.2 `save_message`
- [x] 13.3 `generate_conversation_title`
- [x] 13.4 `daily_usage_rollup` (har kuni 00:05)
- [x] 13.5 `archive_old_conversations` (haftalik, 6 oydan eski)
- [x] 13.6 `check_limits_and_notify` (har soat)
- [x] 13.7 `catalog_reindex`
- [x] 13.8 `stock_low_alert`
- [x] 13.9 Idempotentlik va retry testlari
- [x] 13.10 `update_conversation_stage` — Go `stage` event'idan bosqich va holat (idempotent, noma'lum bosqich e'tiborsiz)

## Bosqich 14 — Sifat, xavfsizlik, ishlash

- [x] 14.1 Coverage ≥ 70% (umumiy 84%, `apps/pricing` 94%, `apps/common/permissions.py` 94%)
- [x] 14.2 Ruxsat testlari to'liq matritsa bo'yicha
- [x] 14.3 `pip-audit` va `detect-secrets` CI'da (`.secrets.baseline` qo'shildi)
- [x] 14.4 Log maskalash: token, parol, telefon
- [x] 14.5 Fayl yuklash validatsiyasi (MIME, ≤ 10MB)
- [x] 14.6 Yuk testi: 50 parallel chat sessiyasi
- [x] 14.7 Gateway overhead ≤ 150 ms o'lchovi
- [x] 14.8 Katalog API ≤ 300 ms o'lchovi
- [x] 14.9 DB indekslarini `EXPLAIN` bilan tekshirish

## Bosqich 15 — Hujjat va yetkazish

- [x] 15.1 OpenAPI sxemasi (`drf-spectacular`) + `/api/docs/` (0 ogohlantirish, 0 xato)
- [x] 15.2 `README.md` — o'rnatish, ishga tushirish, muhit o'zgaruvchilari
- [x] 15.3 Mobil jamoa uchun API qo'llanmasi (xato kodlari, SSE formati)
- [x] 15.4 Go jamoasi bilan proto va etalon test kelishuvi hujjati
- [x] 15.5 Deploy qo'llanmasi va backup tartibi
- [x] 15.6 Django admin — texnik zaxira sifatida minimal sozlash

---

## Ish tartibi (bog'liqliklar)

```
0 → 1 → 2 ─┬→ 3 → 4 ──┬→ 8
           ├→ 5       ├→ 9 → 10
           └→ 6 → 7 ──┘
6 → 12 ;  7,8,9 → 13 ;  hammasi → 14 → 15
```

- Bosqich 0–2 ketma-ket bajariladi, ularsiz qolgani boshlanmaydi.
- Bosqich 3, 5, 6 parallel ketishi mumkin.
- Bosqich 4 (`calculator.py`) — 8-bosqich uchun blokirovkachi.
- Bosqich 14 doimiy: har bosqich yakunida qisman tekshiriladi.
