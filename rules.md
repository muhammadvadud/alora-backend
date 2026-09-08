# Alora Backend — Ishlab chiqish qoidalari (rules.md)

> Bu hujjat `plan/01-BACKEND-TZ.md` asosida yozilgan va **majburiy** hisoblanadi.
> Kod yozayotgan har bir dasturchi (yoki AI agent) shu qoidalarga rioya qiladi.
> Qoida bilan TZ ziddiyatga tushsa — TZ ustun, ammo o'zgarish shu faylga ham kiritiladi.

**Stack:** Python 3.12 · Django 5.x · DRF · PostgreSQL 16 · Redis · Celery · grpcio · Uvicorn (ASGI)

---

## 1. Umumiy tamoyillar

1. **Source of truth bitta.** Mahsulot, narx, koeffitsient va bilimlar bazasi faqat Django'da yashaydi. Go agent nusxa (cache) bilan ishlaydi.
2. **Hech qanday biznes-qiymat kodda hardcode qilinmaydi.** Koeffitsient, chegirma, avans foizi, zapas — hammasi `CalcRule` / `ServicePrice` / `DiscountPolicy` / `OrderDefaults` jadvallarida. Kodda faqat *formula* bo'ladi.
3. **Snapshot printsipi.** Buyurtmaga tushgan narx va nom o'sha paytdagi holatda ko'chiriladi. Katalog keyin o'zgarsa — eski buyurtma o'zgarmaydi.
4. **Mobil ilova yagona mijoz.** Alohida web-admin yo'q. Django admin faqat texnik zaxira.
5. **Go tashqariga chiqmaydi.** Mobil ilova faqat Django bilan gaplashadi; Go bilan aloqa faqat ichki gRPC.
6. **Ishlamayotgan narsa "bajarildi" deb belgilanmaydi.** `tasks.md` da belgi qo'yish uchun test o'tishi shart.

---

## 2. Loyiha tuzilmasi

```
alora-backend/
├── config/            # settings/{base,dev,prod}.py, asgi.py, wsgi.py, urls.py, celery.py
├── apps/
│   ├── common/        # BaseModel, pagination, permissions, exceptions, mixinlar
│   ├── accounts/      # Tenant, User, Role, JWT
│   ├── catalog/       # Category, Product, ProductVariant, ProductImage, Fason*
│   ├── pricing/       # CalcRule, ServicePrice, DiscountTier, DiscountPolicy, OrderDefaults, ModelPricing
│   ├── knowledge/     # KnowledgeRule
│   ├── chat/          # Conversation, Message, SSE gateway, gRPC client
│   ├── orders/        # Order, OrderMeasurement, OrderCurtainPart, OrderAccessory, OrderItem
│   └── usage/         # UsageRecord, UsageDaily, UsageLimit
├── grpc_gen/          # protodan generatsiya (qo'lda tahrirlanmaydi)
├── protos/            # alora.proto — Go bilan UMUMIY manba
├── tests/
├── scripts/           # entrypoint.sh, gen_proto.sh, seed.py
└── docker/
```

**App ichidagi tartib (majburiy):**

```
apps/<app>/
├── models.py          # faqat model + Meta + property; biznes-mantiq yo'q
├── serializers.py     # DRF serializerlar (read/write ajratilgan)
├── views.py           # ViewSet — ingichka, faqat orkestratsiya
├── services.py        # BIZNES-MANTIQ shu yerda
├── selectors.py       # murakkab o'qish so'rovlari (queryset yig'ish)
├── permissions.py
├── filters.py
├── tasks.py           # Celery
├── signals.py
├── urls.py
├── admin.py
└── migrations/
```

**Qoida:** view ichida 20 qatordan ko'p mantiq bo'lsa — `services.py` ga chiqariladi.
Model ichida DB bilan bog'liq bo'lmagan hisob-kitob yozilmaydi.

---

## 3. Modellar

1. Barcha modellar `apps.common.models.BaseModel` dan meros oladi:
   `id (UUIDv4, pk)`, `created_at`, `updated_at`, `is_active`.
2. Ko'p filialga tayyor bo'lish uchun biznes modellarda `tenant` (FK Tenant) bo'ladi. 1-bosqichda bitta tenant, lekin maydon **hozirdan** qo'yiladi.
3. Pul — faqat `DecimalField(max_digits=14, decimal_places=2)`. `FloatField` pul uchun **taqiqlanadi**.
4. O'lcham va koeffitsient — `DecimalField(max_digits=8, decimal_places=3)`.
5. `choices` — har doim `models.TextChoices` klassi orqali, magic string yozilmaydi.
6. Har bir FK'da `related_name` aniq beriladi; `on_delete` ongli tanlanadi (`PROTECT` — katalog/narx, `CASCADE` — bola yozuvlar).
7. Indekslar TZ 9-bo'limi bo'yicha majburiy: `Message.conversation`, `UsageRecord.created_at`, `ProductVariant.sku`, `Order.number`, `Conversation.session_id`.
8. Migratsiya nomi ma'noli bo'ladi: `0007_add_product_segment.py`.
9. Ma'lumot ko'chiruvchi migratsiya (data migration) alohida faylda, `RunPython` ikki tomonlama (forward + reverse).

---

## 4. API qoidalari

1. Barcha yo'llar: `/api/v1/...`. Versiya URL'da.
2. Autentifikatsiya: JWT Bearer. `access` 15 daqiqa, `refresh` 30 kun, rotation + blacklist yoqilgan.
3. Trailing slash saqlanadi (`/orders/`), DRF default'i bilan mos.
4. **Pagination:** barcha ro'yxatlar cursor-pagination (`apps.common.pagination.StandardCursorPagination`), default 20, max 100.
5. **Filtr va qidiruv:** `django-filter` + `?search=`. Har bir ro'yxat endpointida `search` bo'ladi.
6. **PATCH qisman yangilashni** qo'llab-quvvatlaydi (mobil formdan faqat o'zgargan maydon keladi).
7. **Xato formati yagona** (`apps.common.exceptions.custom_exception_handler`):

```json
{
  "detail": "Ma'lumotlar noto'g'ri",
  "code": "validation_error",
  "errors": { "price": "0 dan katta bo'lishi kerak" }
}
```

   Validatsiya xatolari **maydon bo'yicha** qaytadi — mobil ilova formda ko'rsatadi.
8. Xato matnlari **o'zbek tilida** (i18n uz/ru tayyorlab qo'yiladi).
9. Serializer ikkiga bo'linadi: `XxxReadSerializer` (nested, o'qish) va `XxxWriteSerializer` (yassi, yozish). N+1 ni oldini olish uchun `select_related` / `prefetch_related` selektorda beriladi.
10. `cost_price` (tannarx) **hech qachon** employee/manager javobiga tushmaydi va AI'ga yuborilmaydi — faqat `admin` roli ko'radi. Buni serializer darajasida test bilan qopla.
11. Rasm yuklashda server avtomatik siqadi: thumbnail 300px, to'liq 1200px (Celery task).

---

## 5. Ruxsatlar (permissions)

Rol iyerarxiyasi: `employee < manager < admin`.

| Guruh | employee | manager | admin |
|---|---|---|---|
| chat, katalog o'qish | ✅ | ✅ | ✅ |
| buyurtma yaratish | ✅ | ✅ | ✅ |
| katalog yozish, narx | ❌ | ✅ | ✅ |
| xodimlar, limit, usage | ❌ | ✅ | ✅ |
| calc-rules, knowledge | ❌ | ✅ | ✅ |
| system prompt, ModelPricing, tannarx | ❌ | ❌ | ✅ |

**Qoidalar:**
- Har bir ViewSet'da `permission_classes` **aniq** yoziladi; default'ga tayanilmaydi.
- Global default: `IsAuthenticated`. `AllowAny` faqat login/refresh'da.
- Obyekt darajasida: employee faqat **o'z** suhbati va **o'z** buyurtmasini ko'radi; manager — butun tenant'ni.
- Har bir yopiq endpoint uchun "employee kira olmaydi" testi **majburiy**.
- `tenant` filtri queryset darajasida avtomatik qo'llanadi (`TenantScopedQuerySetMixin`) — view'da unutib qo'yish mumkin bo'lmasin.

---

## 6. Hisob-kitob (calc) qoidalari

1. Formula **bitta joyda**: `apps/pricing/services/calculator.py`. `/calc/preview/` ham, buyurtma yaratish ham, Go uchun snapshot ham shu funksiyani ishlatadi.
2. Koeffitsientlar bazadan (`CalcRule`) o'qiladi, kodda raqam yozilmaydi.
3. Yaxlitlash tartibi qat'iy: yuza → `round_area_to`, qator summasi → 2 kasr, buyurtma jami → `round_total_to`. Yaxlitlash **oxirida**, oraliq natijalar to'liq aniqlikda.
4. Bir pardada 1..10 bo'lak (`OrderCurtainPart`) bo'lishi mumkin — har biri o'z koeffitsienti va o'z variantidan narxi bilan hisoblanadi.
5. Narx birligi: `per_sqm` (mato), `per_piece` (aksessuar), `per_meter` (bahroma, tasma). Har biri uchun alohida hisob yo'li.
6. Chegirma: mos keladigan **eng yuqori** `DiscountTier` qo'llanadi; qo'lda chegirma `DiscountPolicy.manual_max_percent_*` chegarasidan oshmaydi; `stack_with_tier=False` bo'lsa ustiga qo'shilmaydi.
7. **Etalon testlar:** `tests/pricing/test_reference_cases.py` — 20 ta misol JSON faylda (`tests/fixtures/calc_cases.json`). Bu fayl Go repo bilan **umumiy**; ikkala taraf ham shu fayldan o'tishi shart.
8. Formula o'zgarsa etalon fayl ham yangilanadi va Go jamoasiga xabar qilinadi.

---

## 7. Chat gateway (SSE) qoidalari

Ketma-ketlik qat'iy (TZ 5.2):

```
1. JWT tekshir → user, tenant
2. UsageLimit tekshir → tugagan bo'lsa 429 + tushunarli xabar
3. Rate limit (Redis)
4. Conversation topish/yaratish
5. gRPC Agent.Chat stream ochish (deadline 60s)
6. Har event'ni SSE frame qilib yozish (StreamingHttpResponse)
7. done event'ida: Message saqlash + UsageRecord yozish → Celery
8. Klient uzilsa gRPC stream bekor qilinadi (context cancel)
```

- Gateway view **async** bo'ladi; ichida bloklovchi ORM chaqiruvi bo'lmaydi (`sync_to_async` yoki async ORM).
- Go event'lari **1:1** o'tkaziladi, o'zgartirilmaydi.
- Go javob bermasa foydalanuvchiga: `"AI xizmati vaqtincha ishlamayapti"` (500 emas, 503).
- DB yozuvi javob oqimini **bloklamaydi** — hammasi Celery'ga.
- gRPC klient: ulanish pool'i, retry (3 marta, exponential backoff), keep-alive.

---

## 8. Celery qoidalari

1. Task **idempotent** bo'ladi — ikki marta ishlasa natija buzilmaydi.
2. Task argumentlari faqat oddiy tiplar (UUID string, int) — model obyekti uzatilmaydi.
3. Har task'da `bind=True`, `max_retries=3`, `autoretry_for`, `retry_backoff=True`.
4. Navbatlar: `default`, `usage` (tez, yuqori hajm), `heavy` (rollup, arxiv, rasm).
5. Beat jadvali `config/celery.py` da kod sifatida, TZ 8-bo'limiga mos.

---

## 9. Katalog sinxronizatsiyasi

- `post_save` / `post_delete` signal → Redis pub/sub kanaliga delta `{tenant_id, entity, id, action, version}`.
- `version` monoton o'sadi (Redis `INCR`). Go uzilish sezsa `Catalog.Snapshot` ni qayta chaqiradi.
- Snapshot sahifalab beriladi (10k+ mahsulot uchun).
- Signal ichida og'ir ish qilinmaydi — faqat delta e'lon qilinadi.

---

## 10. Kod sifati

1. **Format:** `ruff format` (line-length 100). **Lint:** `ruff check`. **Tip:** `mypy` (django-stubs, `strict_optional`).
2. `pre-commit` majburiy: ruff, ruff-format, mypy, migratsiya tekshiruvi, `detect-secrets`.
3. Type hint — barcha `services.py` va `selectors.py` funksiyalarida majburiy.
4. Docstring — public funksiya va murakkab mantiqda, **o'zbek tilida** qisqa izoh.
5. Nomlash: model `PascalCase`, funksiya/o'zgaruvchi `snake_case`, konstanta `UPPER_SNAKE`.
6. `print()` taqiqlanadi — `structlog` ishlatiladi.
7. Kodda `TODO` qoldirilsa — `tasks.md` ga ham qator qo'shiladi, aks holda qoldirilmaydi.
8. Fayl 400 qatordan oshsa bo'linadi (`services/` paketiga ajratiladi).

---

## 11. Testlar

1. `pytest` + `pytest-django` + `factory_boy` (fixture o'rniga fabrikalar).
2. **Coverage ≥ 70%** (TZ 10-bo'lim), `pricing` va `permissions` uchun ≥ 90%.
3. Majburiy test turlari:
   - model va biznes-mantiq — unit
   - `/calc/preview/` — 20 ta etalon misol
   - gateway — gRPC mock bilan SSE oqimi
   - permission — employee manager endpointiga kira olmasligi
   - limit — limit tugaganda 429
4. Test nomi hujjat bo'lib xizmat qiladi: `test_employee_cannot_change_price`.
5. Tashqi xizmat (gRPC, S3, SMS) testda **hech qachon** haqiqiy chaqirilmaydi.
6. `pytest -q` yashil bo'lmaguncha commit qilinmaydi.

---

## 12. Xavfsizlik

1. Sirlar `.env` da, repoga **hech qachon** tushmaydi. `.env.example` namuna sifatida saqlanadi.
2. `DEBUG=False` prod'da; `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` aniq ro'yxat.
3. Parol — Django hasher (Argon2 tavsiya). Login `phone` bo'yicha.
4. Rate limit: login (5/daqiqa/IP), chat (rol bo'yicha, Redis).
5. Log'ga token, parol, telefon to'liq yozilmaydi (maskalanadi).
6. Fayl yuklashda MIME va hajm tekshiriladi (rasm ≤ 10MB).
7. Har PR'da `detect-secrets` va `pip-audit` o'tadi.

---

## 13. Git qoidalari

1. Branch: `main` (barqaror) ← `feat/<qisqa-nom>`, `fix/<qisqa-nom>`, `chore/<qisqa-nom>`.
2. Commit **atomik** — bitta mantiqiy o'zgarish, bitta commit.
3. **Commit xabari o'zbek tilida**, Conventional Commits prefiksi bilan:

```
feat(catalog): mahsulot va variant modellari qo'shildi

Product, ProductVariant va ProductImage modellari TZ 3.2 bo'yicha
yozildi. Narx birligi per_sqm/per_piece/per_meter sifatida ajratildi,
tannarx maydoni faqat admin uchun ochiq qilindi.
```

4. Prefikslar: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`.
5. Sarlavha ≤ 72 belgi, buyruq ohangida emas — bajarilgan ish sifatida ("qo'shildi", "tuzatildi").
6. Commit xabarida **AI, Claude, Copilot va shunga o'xshash belgi bo'lmaydi**. `Co-Authored-By` yoki generator izohi yozilmaydi.
7. Push'dan oldin **har doim** `git pull --rebase origin <branch>`.
8. Migratsiya bilan model bir commit'da ketadi.
9. `tasks.md` dagi belgi shu ish bajarilgan commit **ichida** yangilanadi.

---

## 14. Deploy va muhit

1. `config/settings/` uch qismga bo'linadi: `base.py`, `dev.py`, `prod.py`. `DJANGO_SETTINGS_MODULE` env orqali.
2. Docker Compose: `postgres`, `redis`, `django (uvicorn)`, `celery-worker`, `celery-beat`, `go-agent`, `nginx`.
3. `scripts/entrypoint.sh` — `migrate` + `collectstatic` + server.
4. Log: `structlog` JSON → stdout; Sentry ulangan.
5. Health endpoint: `/health/` (DB, Redis, gRPC holati).
6. Backup: Postgres kunlik dump, media S3'da.

---

## 15. Ishlash talablari (nazorat qilinadi)

| Ko'rsatkich | Chegara |
|---|---|
| Gateway overhead (Django qatlami) | ≤ 150 ms |
| SSE birinchi belgi (Go javobidan keyin) | ≤ 50 ms |
| Katalog API javobi (100 mahsulot, keshsiz) | ≤ 300 ms |
| Parallel chat sessiya (1 instans) | ≥ 50 |

- Statistika xom `UsageRecord` dan emas, `UsageDaily` rollup'idan o'qiladi.
- Barcha ro'yxatlar cursor-pagination.
- 6 oydan eski suhbatlar arxiv jadvaliga ko'chiriladi.
- N+1 so'rov — `django-debug-toolbar` (dev) va `assertNumQueries` testi bilan ushlanadi.

---

## 16. Bajarilgan ishni belgilash tartibi

1. Ish boshlanganda `tasks.md` dagi qator `[~]` (jarayonda) qilinadi.
2. Ish tugab, test o'tgach `[x]` qilinadi va yoniga qisqa izoh yoziladi.
3. Shu o'zgarish **ish commit'ining ichida** ketadi — alohida "tasks yangilandi" commit'i qilinmaydi.
4. Yangi ish paydo bo'lsa `tasks.md` ga tegishli bosqichga qo'shiladi, o'ylab topilgan ish qo'shilmaydi.
