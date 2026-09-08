# Alora Backend — Ish rejasi (tasks.md)

> Manba: `plan/01-BACKEND-TZ.md` · Qoidalar: `rules.md`
> Belgilar: `[ ]` boshlanmagan · `[~]` jarayonda · `[x]` tugallangan (test o'tgan)
> Har bir ish tugagach shu fayl **o'sha ishning commit'i ichida** yangilanadi.

**Umumiy holat:** 0 / 149 bajarildi

---

## Bosqich 0 — Poydevor (infratuzilma)

- [~] 0.1 Repo boshlanishi: `.gitignore`, `README.md`, `LICENSE`, `.editorconfig`  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.2 `pyproject.toml` — Python 3.13, bog'liqliklar, ruff/mypy/pytest sozlamalari  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.3 Django 5.x loyihasi: `config/` + `settings/{base,dev,prod}.py`  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.4 `.env.example` va `django-environ` orqali sozlash  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.5 PostgreSQL 16 ulanishi va `dj_database_url`  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.6 Redis ulanishi (cache + Celery broker + pub/sub)  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.7 `config/celery.py` — app, navbatlar (`default`, `usage`, `heavy`), beat jadvali  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.8 ASGI sozlash (`config/asgi.py`, Uvicorn)  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.9 `structlog` JSON logging + Sentry  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.10 `pre-commit`: ruff, ruff-format, mypy, detect-secrets, migratsiya tekshiruvi  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.11 `docker/` — Dockerfile, docker-compose (postgres, redis, django, celery-worker, celery-beat, nginx)  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.12 `scripts/entrypoint.sh` — migrate + collectstatic + server  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.13 CI (GitHub Actions): lint → mypy → test → coverage gate  — kod yozildi, tekshiruv kutilmoqda
- [~] 0.14 `/health/` endpoint (DB, Redis, gRPC holati)  — kod yozildi, tekshiruv kutilmoqda

## Bosqich 1 — `apps/common` (umumiy poydevor)

- [~] 1.1 `BaseModel` — UUID pk, `created_at`, `updated_at`, `is_active`  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.2 `TenantScopedModel` + `TenantScopedQuerySetMixin` (avtomatik tenant filtri)  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.3 `StandardCursorPagination` (default 20, max 100)  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.4 Yagona xato formati: `custom_exception_handler` + `errors` maydoni  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.5 Rol permission klasslari: `IsEmployee`, `IsManager`, `IsAdmin`, `IsOwnerOrManager`  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.6 Umumiy `TextChoices` to'plamlari (role, price_unit, part_role, status)  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.7 `factory_boy` bazaviy fabrikalar va `conftest.py`  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.8 i18n karkasi (uz asosiy, ru zaxira), xato matnlari o'zbekcha  — kod yozildi, tekshiruv kutilmoqda
- [~] 1.9 Testlar: pagination, xato formati, tenant scoping  — kod yozildi, tekshiruv kutilmoqda

## Bosqich 2 — `apps/accounts` (auth va rollar)

- [ ] 2.1 `Tenant` modeli (name, address, phone, currency, timezone)
- [ ] 2.2 `User` modeli (`AbstractBaseUser`, phone login, role, tenant, device_id)
- [ ] 2.3 `UserManager` — `create_user`, `create_superuser`
- [ ] 2.4 JWT sozlash: access 15 daq, refresh 30 kun, rotation + blacklist
- [ ] 2.5 Token payload: `user_id`, `role`, `tenant_id`
- [ ] 2.6 `POST /auth/login/` — phone + password
- [ ] 2.7 `POST /auth/refresh/`
- [ ] 2.8 `POST /auth/logout/` — refresh bekor qilish
- [ ] 2.9 `GET /auth/me/` — profil + rol + limit holati
- [ ] 2.10 Login rate limit (5/daqiqa/IP)
- [ ] 2.11 Argon2 password hasher
- [ ] 2.12 Testlar: login, refresh rotation, noto'g'ri parol, bloklangan foydalanuvchi

## Bosqich 3 — `apps/catalog` (mahsulot bazasi)

- [ ] 3.1 `Category` — parent (self FK), slug, sort_order
- [ ] 3.2 `Product` — AI atributlari bilan (fabric_type, pattern, style, transparency, density, composition, care, recommended_rooms, recommended_coef, default_width_m, is_sewing_required, segment, tags)
- [ ] 3.3 `ProductVariant` — sku, color_name, color_hex, width_m, price, price_unit, old_price, cost_price
- [ ] 3.4 `ProductImage` — product/variant, siqilgan o'lchamlar, is_primary
- [ ] 3.5 `Fason` shabloni
- [ ] 3.6 `FasonPart` — role, width_share, height_share, default_coef
- [ ] 3.7 `FasonAccessory` — category, default_qty, qty_formula
- [ ] 3.8 Indekslar: `sku`, `code`, `category`, `segment`
- [ ] 3.9 Read serializerlar (nested variant + rasm) va Write serializerlar
- [ ] 3.10 `cost_price` faqat admin'ga ko'rinadigan qilib yopish
- [ ] 3.11 `GET /catalog/categories/`
- [ ] 3.12 `GET /catalog/products/` — filtr: category, style, room, segment, price_unit, search, min_price, max_price
- [ ] 3.13 `GET /catalog/products/{id}/` — variant va rasmlar bilan
- [ ] 3.14 `GET /catalog/variants/{id}/`
- [ ] 3.15 `POST/PATCH/DELETE /catalog/products/` (manager+)
- [ ] 3.16 `POST/PATCH/DELETE /catalog/variants/` (manager+)
- [ ] 3.17 `POST /catalog/variants/bulk-price/` — foiz yoki summa bo'yicha ommaviy narx
- [ ] 3.18 `POST /catalog/products/{id}/images/` — multipart yuklash
- [ ] 3.19 `DELETE /catalog/images/{id}/`
- [ ] 3.20 Rasm siqish Celery task (thumbnail 300px, to'liq 1200px)
- [ ] 3.21 `POST /catalog/import/` — Excel/CSV import
- [ ] 3.22 `GET/POST/PATCH/DELETE /catalog/fasons/`
- [ ] 3.23 Seed skript: kategoriyalar, namuna mahsulot va aksessuarlar
- [ ] 3.24 N+1 nazorati (`assertNumQueries`) va 300 ms javob testi
- [ ] 3.25 Testlar: filtr, qidiruv, permission, tannarx yopiqligi

## Bosqich 4 — `apps/pricing` (narx va hisob)

- [ ] 4.1 `CalcRule` — key, value, unit, description, applies_to
- [ ] 4.2 `ServicePrice` — sewing, install, delivery, tape, hook, weight_tape
- [ ] 4.3 `DiscountTier` — min_amount, percent
- [ ] 4.4 `DiscountPolicy` — qo'lda chegirma chegaralari, stack_with_tier
- [ ] 4.5 `OrderDefaults` — prepayment_percent, delivery_amount, deadline_days
- [ ] 4.6 `ModelPricing` — LLM narxlari va usd_to_uzs kursi
- [ ] 4.7 Boshlang'ich qiymatlar migratsiyasi (coef_default, seam_allowance, hem_allowance, hook_step, round_area_to, round_total_to, min_order_amount, waste_warn_percent)
- [ ] 4.8 `calculator.py` — yuza hisobi (bo'lak, koeffitsient, zapas)
- [ ] 4.9 Narx birligi bo'yicha hisob: `per_sqm`, `per_piece`, `per_meter`
- [ ] 4.10 Chiqindi (waste) hisobi va `waste_warn_percent` ogohlantirishi
- [ ] 4.11 Xizmat qatorlari hisobi (tikuv, montaj, tasma, ilgich, yetkazish)
- [ ] 4.12 Chegirma qo'llash: tier tanlash + qo'lda chegirma chegarasi
- [ ] 4.13 Yaxlitlash tartibi (yuza → qator → jami)
- [ ] 4.14 `POST /calc/preview/` endpointi
- [ ] 4.15 `GET/PATCH /pricing/calc-rules/`
- [ ] 4.16 `GET/PATCH /pricing/services/`
- [ ] 4.17 `GET/POST/PATCH/DELETE /pricing/discount-tiers/`
- [ ] 4.18 `GET/PATCH /pricing/discount-policy/`
- [ ] 4.19 `GET/PATCH /pricing/order-defaults/`
- [ ] 4.20 `ModelPricing` CRUD (faqat admin)
- [ ] 4.21 `tests/fixtures/calc_cases.json` — 20 ta etalon misol (Go bilan umumiy)
- [ ] 4.22 Etalon testlar: 20 misol 1:1 mos kelishi
- [ ] 4.23 Chekka holat testlari: 10 bo'lakli parda, nol o'lcham, manfiy narx

## Bosqich 5 — `apps/knowledge` (sotuv bilimlari)

- [ ] 5.1 `KnowledgeRule` — kind, condition (JSON), recommendation, priority
- [ ] 5.2 `GET/POST/PATCH/DELETE /knowledge/rules/` (manager+)
- [ ] 5.3 Shartga mos qoidalarni tanlash selektori (priority bo'yicha)
- [ ] 5.4 Go'ga sinxronlash uchun serializatsiya formati
- [ ] 5.5 Testlar: shart moslashuvi, ustuvorlik tartibi

## Bosqich 6 — gRPC shartnoma va klient

- [ ] 6.1 `protos/alora.proto` yozilishi (Agent, Catalog, Backend servislari)
- [ ] 6.2 `scripts/gen_proto.sh` — `grpc_gen/` generatsiyasi
- [ ] 6.3 Proto'ni Go repo bilan umumiy qilish (submodule yoki CI ko'chirish)
- [ ] 6.4 `apps/chat/grpc_client.py` — ulanish pool'i, retry, deadline 60s, keep-alive
- [ ] 6.5 Go ishlamaganda tushunarli xato (503, "AI xizmati vaqtincha ishlamayapti")
- [ ] 6.6 `Catalog.Snapshot` server tomoni (sahifalab)
- [ ] 6.7 `Catalog.Watch` stream — delta push
- [ ] 6.8 `Backend.ReportUsage` qabul qilish
- [ ] 6.9 `Backend.SaveOrderDraft` qabul qilish
- [ ] 6.10 `Backend.LogMessage` qabul qilish
- [ ] 6.11 `Agent.Health` tekshiruvi `/health/` ichida
- [ ] 6.12 gRPC mock testlari

## Bosqich 7 — `apps/chat` (gateway)

- [ ] 7.1 `Conversation` modeli — session_id, mode, status, stage, context, order FK
- [ ] 7.2 `Message` modeli — role, content, tool_calls, tool_result, audio_url, tokenlar
- [ ] 7.3 Indekslar: `Message.conversation`, `Conversation.session_id`
- [ ] 7.4 `GET /conversations/` (employee — o'zi, manager — hammasi)
- [ ] 7.5 `POST /conversations/` — session_id generatsiya
- [ ] 7.6 `GET /conversations/{id}/messages/` — cursor pagination
- [ ] 7.7 `POST /conversations/{id}/messages/` — **SSE stream** (asosiy endpoint)
- [ ] 7.8 SSE oqim mantiqi: JWT → limit → rate limit → conversation → gRPC → frame
- [ ] 7.9 Klient uzilganda gRPC context cancel
- [ ] 7.10 `done` event'ida Message + UsageRecord saqlash (Celery)
- [ ] 7.11 `DELETE /conversations/{id}/` — arxivlash
- [ ] 7.12 `POST /conversations/{id}/reset/` — kontekst tozalash
- [ ] 7.13 `GET /conversations/{id}/transcript/` — manager to'liq o'qishi
- [ ] 7.14 `WS /ws/voice/{conversation_id}/` — ovozli kanal (Channels)
- [ ] 7.15 Chat rate limit (Redis, rol bo'yicha)
- [ ] 7.16 Async view ichida bloklovchi ORM chaqiruvi yo'qligini tekshirish
- [ ] 7.17 Testlar: SSE oqimi (gRPC mock), uzilish, limit 429, permission

## Bosqich 8 — `apps/orders` (buyurtmalar)

- [ ] 8.1 `Order` modeli — number, status, summalar, chegirma, avans, deadline
- [ ] 8.2 Buyurtma raqami generatori: `ALR-2026-000123` (poyga holatisiz)
- [ ] 8.3 `OrderMeasurement` — room_name, cornice_length_m, height_m, layers, coefficient
- [ ] 8.4 `OrderCurtainPart` — variant, role, o'lcham, koeffitsient, `price_per_sqm` snapshot
- [ ] 8.5 `OrderAccessory` — variant, qty, unit, `unit_price` snapshot
- [ ] 8.6 `OrderItem` — xizmat qatorlari, `name_snapshot`
- [ ] 8.7 Snapshot mantiqi: katalog o'zgarsa buyurtma o'zgarmasligi
- [ ] 8.8 Status mashinasi va ruxsat etilgan o'tishlar
- [ ] 8.9 `GET /orders/` — filtr: status, sana, xodim
- [ ] 8.10 `POST /orders/` — AI draft'idan buyurtma yaratish
- [ ] 8.11 `GET/PATCH /orders/{id}/`
- [ ] 8.12 `POST /orders/{id}/confirm/` — tasdiqlash
- [ ] 8.13 `POST /orders/{id}/status/` — izoh va sana bilan
- [ ] 8.14 `GET /orders/statuses/` — status ro'yxati va o'tishlar
- [ ] 8.15 `GET /orders/{id}/pdf/` — kommercheskiy taklif PDF
- [ ] 8.16 Buyurtma summasini `calculator.py` orqali qayta hisoblash
- [ ] 8.17 Employee faqat o'z buyurtmasini ko'rishi
- [ ] 8.18 Testlar: snapshot, status o'tishlari, summa mosligi, permission

## Bosqich 9 — `apps/usage` (limit va statistika)

- [ ] 9.1 `UsageRecord` — tokenlar, stt/tts, tool_calls, latency, cost_usd/uzs
- [ ] 9.2 `UsageDaily` rollup jadvali
- [ ] 9.3 `UsageLimit` — user yoki role, period, is_unlimited, max_*, on_exceed
- [ ] 9.4 Limit tekshirish mantiqi (shaxsiy > rol > cheksiz)
- [ ] 9.5 Xarajat hisobi `ModelPricing` bo'yicha (USD → UZS)
- [ ] 9.6 `GET /usage/summary/?period=day|week|month&user=`
- [ ] 9.7 `GET /usage/by-user/` — xodimlar reytingi
- [ ] 9.8 `GET /usage/conversations/` — eng qimmat suhbatlar
- [ ] 9.9 `GET /analytics/conversion/` — suhbat → buyurtma konversiyasi
- [ ] 9.10 `POST /team/employees/{id}/limit/` — `is_unlimited` toggle bilan
- [ ] 9.11 Statistika `UsageDaily` dan o'qilishi (xom jadvaldan emas)
- [ ] 9.12 Testlar: limit tugaganda 429, cheksiz rejim, rollup to'g'riligi

## Bosqich 10 — Jamoa boshqaruvi (manager paneli)

- [ ] 10.1 `GET /team/employees/` — xodimlar + bugungi faollik
- [ ] 10.2 `POST /team/employees/` — xodim qo'shish
- [ ] 10.3 `PATCH /team/employees/{id}/` — bloklash, rol, limit
- [ ] 10.4 `GET /team/employees/{id}/conversations/`
- [ ] 10.5 Ruxsatlar matritsasi bo'yicha to'liq test to'plami

## Bosqich 11 — System prompt boshqaruvi (admin)

- [ ] 11.1 `PromptVersion` modeli (versiya, matn, muallif, sana)
- [ ] 11.2 `GET /settings/prompt/` — joriy + tarix
- [ ] 11.3 `POST /settings/prompt/` — yangi versiya
- [ ] 11.4 `POST /settings/prompt/{version}/rollback/`
- [ ] 11.5 Prompt o'zgarganda Go'ga xabar berish
- [ ] 11.6 Testlar: faqat admin kirishi, rollback to'g'riligi

## Bosqich 12 — Katalog sinxronizatsiyasi (Django → Go)

- [ ] 12.1 `post_save` / `post_delete` signallari (Product, Variant, CalcRule, KnowledgeRule)
- [ ] 12.2 Redis pub/sub kanaliga delta e'lon qilish
- [ ] 12.3 Versiya hisoblagichi (Redis `INCR`)
- [ ] 12.4 `Catalog.Watch` stream orqali Go'ga push
- [ ] 12.5 Versiya uzilishida qayta snapshot mantiqi
- [ ] 12.6 Signal ichida og'ir ish yo'qligini tekshirish
- [ ] 12.7 Testlar: delta e'loni, versiya o'sishi

## Bosqich 13 — Fon vazifalari (Celery)

- [ ] 13.1 `save_usage_record`
- [ ] 13.2 `save_message`
- [ ] 13.3 `generate_conversation_title`
- [ ] 13.4 `daily_usage_rollup` (har kuni 00:05)
- [ ] 13.5 `archive_old_conversations` (haftalik, 6 oydan eski)
- [ ] 13.6 `check_limits_and_notify` (har soat)
- [ ] 13.7 `catalog_reindex`
- [ ] 13.8 `stock_low_alert`
- [ ] 13.9 Idempotentlik va retry testlari

## Bosqich 14 — Sifat, xavfsizlik, ishlash

- [ ] 14.1 Coverage ≥ 70% (pricing va permissions ≥ 90%)
- [ ] 14.2 Ruxsat testlari to'liq matritsa bo'yicha
- [ ] 14.3 `pip-audit` va `detect-secrets` CI'da
- [ ] 14.4 Log maskalash: token, parol, telefon
- [ ] 14.5 Fayl yuklash validatsiyasi (MIME, ≤ 10MB)
- [ ] 14.6 Yuk testi: 50 parallel chat sessiyasi
- [ ] 14.7 Gateway overhead ≤ 150 ms o'lchovi
- [ ] 14.8 Katalog API ≤ 300 ms o'lchovi
- [ ] 14.9 DB indekslarini `EXPLAIN` bilan tekshirish

## Bosqich 15 — Hujjat va yetkazish

- [ ] 15.1 OpenAPI sxemasi (`drf-spectacular`) + `/api/docs/`
- [ ] 15.2 `README.md` — o'rnatish, ishga tushirish, muhit o'zgaruvchilari
- [ ] 15.3 Mobil jamoa uchun API qo'llanmasi (xato kodlari, SSE formati)
- [ ] 15.4 Go jamoasi bilan proto va etalon test kelishuvi hujjati
- [ ] 15.5 Deploy qo'llanmasi va backup tartibi
- [ ] 15.6 Django admin — texnik zaxira sifatida minimal sozlash

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
