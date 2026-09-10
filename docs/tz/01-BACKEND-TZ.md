# ALORA — Backend TZ (Django)

**Repo:** `alora-backend`
**Stack:** Python 3.12 · Django 5.x · DRF · PostgreSQL 16 · Redis · Celery · grpcio · Uvicorn (ASGI)

---

## 1. Backend'ning roli

1. **Haqiqat manbai (source of truth):** mahsulotlar, variantlar, narxlar, hisob koeffitsientlari, bilimlar bazasi
2. **Gateway:** mobil ilova ↔ Go AI agent orasidagi yagona darvoza (auth, limit, log, streaming proxy)
3. **Boshqaruv:** foydalanuvchilar, rollar, buyurtmalar, token/xarajat statistikasi
4. **Admin panel:** do'kon egasi va texnik admin uchun

Go xizmati tashqi internetga chiqmaydi. Mobil ilova **faqat** Django bilan gaplashadi.

---

## 2. Loyiha tuzilmasi

```
alora-backend/
├── config/                  # settings (base/dev/prod), asgi.py, urls.py, celery.py
├── apps/
│   ├── accounts/            # User, Role, JWT, xodim boshqaruvi
│   ├── catalog/             # Category, Product, ProductVariant, Fabric, Accessory, Stock
│   ├── pricing/             # PriceRule, CalcRule, Discount, ModelPricing
│   ├── knowledge/           # KnowledgeRule (sotuv bilimlari)
│   ├── chat/                # Conversation, Message, gateway view (SSE/WS), gRPC client
│   ├── orders/              # Order, OrderItem, OrderMeasurement, OrderDraft
│   ├── usage/               # UsageRecord, UsageLimit, statistika
│   └── common/              # base model, pagination, permissions, exceptions, utils
├── grpc_gen/                # protodan generatsiya qilingan Python kod
├── protos/                  # alora.proto (Go bilan UMUMIY — bitta manba)
└── tests/
```

**Umumiy qoida:** `protos/alora.proto` — bitta fayl, ikkala repoga (Go va Django) submodule yoki CI orqali ko'chiriladi. Shartnoma o'zgarsa ikkala taraf ham qayta generatsiya qiladi.

---

## 3. Ma'lumotlar modeli

Barcha modellar `BaseModel` dan meros: `id (UUID)`, `created_at`, `updated_at`, `is_active`.
Ko'p filialli kelajak uchun `tenant_id` maydoni bor (1-bosqichda default bitta tenant).

### 3.1 accounts

```python
class User(AbstractBaseUser):
    phone          # unique, login uchun
    full_name
    role           # choices: employee | manager | admin
    tenant         # FK Tenant
    is_active
    last_login_at
    device_id      # oxirgi qurilma (ixtiyoriy)

class Tenant:       # do'kon / filial
    name, address, phone, currency (default UZS), timezone
```
Auth: **telefon + parol** (SMS-OTP 2-bosqichda). JWT: `access` 15 daq, `refresh` 30 kun, rotation yoqilgan.
Token payload'da: `user_id`, `role`, `tenant_id`.

### 3.2 catalog — mahsulot bazasi

> Talab: bitta mahsulotning **rang / narx / o'lcham** bo'yicha bir nechta varianti bo'ladi.
> Shuning uchun **Product (umumiy)** + **ProductVariant (sotiladigan birlik)** sxemasi.

```python
class Category:
    name, slug, parent (FK self, nullable), sort_order
    # misol: Pardalar > Portyera, Tul, Rim parda, Rulon parda, Lambrekan
    #        Karnizlar, Aksessuarlar, Xizmatlar (tikuv, montaj)

class Product:
    category       # FK
    name           # "Velvet Milano"
    code           # ichki artikul (unique)
    description    # matn — AI shundan foydalanadi
    # --- AI uchun tavsif atributlari (tavsiya sifati shularga bog'liq) ---
    fabric_type    # velvet | jakkard | atlas | len | organza | blackout | vualь ...
    pattern        # plain (gulsiz) | floral (gulli) | geometric | striped | jacquard
    style          # classic | modern | hi_tech | minimal | oriental | provence
    transparency   # transparent | semi | blackout
    density        # g/m² (ixtiyoriy)
    composition    # "70% polyester, 30% viskoza"
    care           # yuvish tavsiyasi
    recommended_rooms   # M2M yoki JSON: [living, bedroom, kids, kitchen, wedding, office]
    recommended_coef    # tavsiya etilgan burma koeffitsienti (2.0 / 2.5 / 3.0)
    default_width_m     # rulon eni: 1.40 / 2.80 / 3.00
    is_sewing_required  # tikuv kerakmi
    segment        # economy | standard | premium   ← 3 variant generatsiyasi uchun MUHIM
    tags           # JSON, erkin teglar
    sort_order, is_active

class ProductVariant:        # aynan SOTILADIGAN birlik
    product        # FK
    sku            # unique
    color_name     # "Grafit", "Bej", "Oq"
    color_hex      # #4A4A4A — ilovada rang doirasi ko'rsatish uchun
    width_m        # bu variantning rulon eni (product'dan farq qilishi mumkin)
    price          # Decimal — narx (UZS)
    price_unit     # per_sqm  → MATOLAR uchun (asosiy holat)
                   # per_piece → aksessuar: gul, broshka, podxvat, halqa, kisti
                   # per_meter → bahroma, tasma, gruz lenta kabi o'lchanadigan bezaklar
    old_price      # chegirma ko'rsatish uchun (nullable)
    cost_price     # tannarx — FAQAT manager ko'radi, AI'ga yuborilmaydi
    is_active
    # v2 uchun qoldirildi (v1 da ishlatilmaydi): stock_qty, stock_status, lead_time_days

class ProductImage:
    product / variant   # variantga bog'lansa rang bo'yicha rasm
    image, alt, sort_order, is_primary
```

**Nega shunday:** AI `product_search` qilganda `Product` darajasida filtrlaydi (uslub, xona, bezak),
narx va rangni esa `ProductVariant` beradi. "Bitta mahsulot — har xil rang va narx" talabi shu bilan qoplanadi.

**Narx birligi.** Tayyor parda sotilmaydi, hamma narsa o'lchov bo'yicha tikiladi.
**Mato — m² bo'yicha** (`per_sqm`); pog'onali metr narxi saqlanmaydi, `width_m` faqat
kesish/chiqindi tekshiruvi uchun kerak.
**Aksessuarlar — dona yoki metr bo'yicha** (`per_piece` / `per_meter`): parda ilgichlari va
dekorativ gullar, broshka, podxvat (parda ushlagich), kisti, bahroma, halqa, magnit ushlagich.
Bular alohida kategoriya (`Aksessuarlar`) va o'z variantlariga ega (rang, o'lcham, narx) —
mato bilan bir xil `Product/ProductVariant` sxemasida yashaydi, faqat `price_unit` boshqacha.

### 3.2.1 Fason va parda kompozitsiyasi

Bitta pardada **1 tadan 10 tagacha** har xil mato ishlatilishi mumkin (asosiy portyera, tul,
ikkinchi rang, kant, lambrekan bo'laklari). Shuning uchun fason — bo'laklar to'plami:

```python
class Fason:  # tayyor shablon (ixtiyoriy, AI tez taklif qilishi uchun)
    name  # "Ikki rangli portyera + tul + lambrekan"
    style, rooms  # qaysi uslub va xonalarga mos
    image  # namuna rasm
    part_count  # nechta matodan iborat
    is_active


class FasonPart:  # shablondagi bitta bo'lak
    fason  # FK
    role  # portyera | tul | lambrekan | kant | dekor | astar
    name  # "chap tomon kant"
    width_share  # karniz kengligining ulushi: 1.0 = butun L, 0.15 = 15%
    height_share  # balandlik ulushi: 1.0 = butun H, 0.2 = lambrekan
    default_coef  # shu bo'lakning burma koeffitsienti (tul odatda yuqoriroq)
    sort_order
```
```python
class FasonAccessory:  # shablonga kiradigan aksessuar (ixtiyoriy)
    fason  # FK
    category  # gul | broshka | podxvat | kisti | bahroma | halqa | magnit
    default_qty  # dona soni yoki metr; "juft" bo'lsa 2
    qty_formula  # ixtiyoriy: "per_side" (har tomonga 1 ta), "per_meter" (L bo'yicha)
```

`Fason` — majburiy emas: AI bo'laklarni erkin ham yig'a oladi. Shablon shunchaki tez yo'l.
Haqiqiy buyurtmadagi bo'laklar `OrderCurtainPart`, aksessuarlar esa `OrderAccessory` da
saqlanadi (3.6-bo'lim).

### 3.3 pricing — narx va hisob qoidalari

```python
class CalcRule:  # hisoblash koeffitsientlari (admin tahrirlaydi)
    key  # unique: "coef_default", "seam_allowance", "hem_allowance",
    #         "hook_step", "round_area_to", "round_total_to",
    #         "min_order_amount", "waste_warn_percent"
    value  # Decimal
    unit  # m | % | dona | so'm
    description  # admin uchun izoh
    applies_to  # JSON shart: {"style": "classic"} — bo'sh bo'lsa umumiy


class ServicePrice:  # xizmat narxlari
    key  # sewing_per_m | sewing_per_sqm | install_per_m | install_flat |
    # delivery | tape_per_m | hook_each | weight_tape_per_m
    name, price, unit, is_active


class DiscountTier:  # summaga qarab O'SADIGAN chegirma — manager kiritadi
    min_amount  # masalan 5 000 000
    percent  # masalan 3
    is_active
    # manager bosqichlarni o'zi qo'shadi/o'chiradi; mos keladigan eng yuqori bosqich qo'llanadi


class DiscountPolicy:  # umumiy chegirma qoidasi (bitta yozuv)
    manual_max_percent_employee  # sotuvchi qo'lda necha % gacha bera oladi
    manual_max_percent_manager  # manager necha % gacha
    stack_with_tier  # bosqichli chegirma ustiga qo'lda qo'shiladimi (default: yo'q)


class OrderDefaults:  # manager kiritmasa ishlatiladigan qiymatlar (bitta yozuv)
    prepayment_percent  # default avans foizi, masalan 50
    delivery_amount  # default yetkazib berish narxi
    deadline_days  # default tayyorlash muddati (kun)


class ModelPricing:  # LLM narxi (xarajat hisoblash uchun)
    provider  # deepseek | openai | claude
    model  # deepseek-v4-pro
    input_per_1m  # $ / 1M token
    output_per_1m
    cached_input_per_1m
    stt_per_minute
    tts_per_1k_chars
    usd_to_uzs  # kurs
```

### 3.4 knowledge — sotuv bilimlari

```python
class KnowledgeRule:
    kind  # room_style | light | color | construction | objection | general
    condition  # JSON: {"room": "wedding", "style": "classic"}
    recommendation  # matn: AI shu matnni tavsiyaga asos qiladi
    priority  # yuqori raqam — birinchi
    is_active
```
Bu qoidalar Go'ga sinxronlanadi va system prompt'ga qo'shiladi (yoki `knowledge_lookup` tool orqali olinadi).

### 3.5 chat

```python
class Conversation:
    user  # FK — kim olib borgan
    tenant
    session_id  # Go agentdagi sessiya ID (unique)
    title  # AI birinchi xabardan generatsiya qiladi
    mode  # seller | customer  (mijoz rejimi)
    status  # active | archived
    stage  # need | recommend | measure | calc | variants | order
    context  # JSON — yig'ilgan ma'lumot (xona, uslub, o'lcham, budjet)
    order  # FK Order (nullable) — konversiya o'lchash uchun
    started_at, last_message_at


class Message:
    conversation
    role  # user | assistant | tool | system
    content
    tool_calls  # JSON
    tool_result  # JSON
    audio_url  # ovozli xabar bo'lsa
    tokens_in, tokens_out
    created_at
```
> Eslatma: Go tarafda ham `chat_messages` (Eino `schema.Message` JSONB) jadvali bor — u **model konteksti** uchun.
> Django'dagi `Message` — **biznes ko'rinishi** (manager o'qishi, analitika). Ikkalasi `session_id` orqali bog'lanadi.
> Takrorlanish ataylab: Go tez ishlashi, Django esa boy so'rovlar qilishi kerak.

### 3.6 orders

```python
class Order:
    number  # ALR-2026-000123
    conversation  # FK (nullable)
    user  # sotuvchi
    customer_name, customer_phone, address
    status  # draft | confirmed | measuring | production | ready | installing |
    # completed | cancelled
    subtotal
    discount_percent, discount_amount  # manager/sotuvchi kiritadi yoki DiscountTier bo'yicha
    discount_source  # tier | manual
    delivery_amount  # manager kiritadi yoki OrderDefaults
    total
    prepayment_percent, prepayment, balance
    payment_status  # unpaid | prepaid | paid
    deadline_date
    note
    confirmed_by, confirmed_at


class OrderMeasurement:  # bitta buyurtmada bir nechta deraza bo'lishi mumkin
    order
    room_name  # "Mehmonxona"
    cornice_length_m, height_m
    layers  # JSON: ["tul", "portyera", "lambrekan"]
    coefficient
    note


class OrderCurtainPart:  # ★ bitta pardadagi bitta mato bo'lagi (1 tadan 10 tagacha)
    measurement  # FK OrderMeasurement
    variant  # FK ProductVariant
    role  # portyera | tul | lambrekan | kant | dekor | astar
    width_m  # shu bo'lak egallaydigan karniz kengligi
    height_m  # shu bo'lakning balandligi
    coefficient  # burma koeffitsienti
    area_sqm  # hisoblangan yuza (m²)
    price_per_sqm  # SNAPSHOT
    total
    sort_order


class OrderAccessory:  # ★ pardaga qo'shiladigan bezak va furnitura
    measurement  # FK OrderMeasurement (yoki butun buyurtmaga — nullable)
    variant  # FK ProductVariant (gul, broshka, podxvat, kisti, bahroma, halqa)
    qty  # dona yoki metr
    unit  # piece | meter
    unit_price  # SNAPSHOT
    total


class OrderItem:  # xizmat qatorlari (tikuv, montaj, yetkazish)
    order, measurement
    service_key  # sewing / install / delivery / tape / hook — xizmat bo'lsa
    name_snapshot  # narx va nom SNAPSHOT — keyin baza o'zgarsa buyurtma o'zgarmaydi
    qty, unit, unit_price, total
```
**Muhim:** buyurtmadagi narx va nom **snapshot** qilinadi. Katalogda narx o'zgarsa eski buyurtma o'zgarmaydi.

### 3.7 usage

```python
class UsageRecord:
    user, conversation, message_id
    provider, model
    prompt_tokens, completion_tokens, cached_tokens, reasoning_tokens
    stt_seconds, tts_chars
    tool_calls  # JSON: ["product_search", "curtain_calculate"]
    latency_ms
    cost_usd, cost_uzs
    created_at  # indexed


class UsageLimit:
    user  # FK — HAR BIR XODIMGA ALOHIDA (asosiy holat)
    role  # yoki butun rol uchun umumiy qoida (user bo'sh bo'lsa)
    period  # daily | monthly
    is_unlimited  # ★ True bo'lsa cheklov umuman qo'llanmaydi (manager xohlagan xodimga qo'yadi)
    max_tokens, max_cost_uzs, max_messages  # is_unlimited=False bo'lsa ishlaydi
    on_exceed  # warn | block
    is_active


# Ustuvorlik: xodimning shaxsiy limiti > rol limiti > limit yo'q (cheksiz).
# Manager panelida har xodim satrida "Cheksiz" toggle'i bor.
```

---

## 4. gRPC shartnoma (Django ↔ Go)

`protos/alora.proto` — qisqacha eskiz:

```protobuf
syntax = "proto3";
package alora.v1;

service Agent {
  // Chat: server-streaming — Go har Event'ni alohida yuboradi
  rpc Chat(ChatRequest) returns (stream ChatEvent);
  // Ovoz: ikki tomonlama stream (audio kirish ↔ audio+matn chiqish)
  rpc VoiceChat(stream VoiceChunk) returns (stream VoiceEvent);
  rpc ResetSession(ResetRequest) returns (ResetResponse);
  rpc Health(Empty) returns (HealthResponse);
}

service Catalog {                     // Django → Go: ma'lumot yetkazish
  rpc Snapshot(SnapshotRequest) returns (CatalogSnapshot);
  rpc Watch(WatchRequest) returns (stream CatalogDelta);   // push yangilanish
}

service Backend {                     // Go → Django: yozish (asinxron)
  rpc ReportUsage(UsageRequest) returns (Ack);
  rpc SaveOrderDraft(OrderDraftRequest) returns (OrderDraftResponse);
  rpc LogMessage(MessageLogRequest) returns (Ack);
}

message ChatRequest {
  string session_id = 1;
  string user_id = 2;
  string tenant_id = 3;
  string message = 4;
  string locale = 5;              // uz | ru
  map<string,string> context = 6; // stage, mijoz rejimi va h.k.
}

message ChatEvent {
  string kind = 1;      // start|thinking|content|tool_call|tool_args|tool_result|done|error
  string content = 2;
  string tool = 3;
  string args = 4;
  string result = 5;
  string error = 6;
  Usage usage = 7;      // done event'ida to'ldiriladi
  repeated ProductRef products = 8;  // ilovada kartochka chizish uchun
}
```

**Django tarafda:** `apps/chat/grpc_client.py` — ulanish pool'i, retry, deadline (60s), keep-alive.
Go ishlamasa foydalanuvchiga tushunarli xato: "AI xizmati vaqtincha ishlamayapti".

---

## 5. REST API (mobil ilova uchun)

Barcha yo'llar: `/api/v1/...`, JWT `Authorization: Bearer <token>`.

### 5.1 Auth
| Method | Endpoint | Izoh |
|---|---|---|
| POST | `/auth/login/` | phone + password → access/refresh |
| POST | `/auth/refresh/` | refresh → yangi juftlik |
| POST | `/auth/logout/` | refresh bekor qilish |
| GET | `/auth/me/` | profil + rol + limit holati |

### 5.2 Chat (gateway)
| Method | Endpoint | Izoh |
|---|---|---|
| GET | `/conversations/` | suhbatlar ro'yxati (o'zi uchun; manager — hamma) |
| POST | `/conversations/` | yangi suhbat (session_id generatsiya) |
| GET | `/conversations/{id}/messages/` | tarix (paginated) |
| POST | `/conversations/{id}/messages/` | **SSE stream** — asosiy chat endpoint |
| DELETE | `/conversations/{id}/` | arxivlash |
| POST | `/conversations/{id}/reset/` | kontekstni tozalash |
| WS | `/ws/voice/{conversation_id}/` | ovozli suhbat kanali |

**SSE oqimi formati** (Go Event'lari 1:1 o'tkaziladi):
```
data: {"kind":"start"}
data: {"kind":"tool_call","tool":"product_search"}
data: {"kind":"tool_result","tool":"product_search","result":"{...}"}
data: {"kind":"content","content":"Mehmonxona"}
data: {"kind":"content","content":" uchun"}
data: {"kind":"done","usage":{...},"products":[...]}
```

**Gateway view mantiqi (async):**
```
1. JWT tekshir → user, tenant
2. UsageLimit tekshir → limit tugagan bo'lsa 429 + tushunarli xabar
3. Rate limit (Redis)
4. Conversation topish/yaratish
5. gRPC Agent.Chat stream ochish
6. Har event'ni SSE frame qilib yozish (StreamingHttpResponse)
7. done event'ida: Message saqlash + UsageRecord yozish (Celery task)
8. Klient uzilsa gRPC stream'ni bekor qilish (context cancel)
```

### 5.3 Katalog (ilovada ko'rish uchun)
| Method | Endpoint |
|---|---|
| GET | `/catalog/categories/` |
| GET | `/catalog/products/?category=&style=&room=&segment=&price_unit=&search=&min_price=&max_price=` |
| GET | `/catalog/products/{id}/` (variantlar + rasmlar bilan) |
| GET | `/catalog/variants/{id}/` |

### 5.4 Buyurtmalar
| Method | Endpoint | Izoh |
|---|---|---|
| GET | `/orders/` | ro'yxat, filtr: status, sana, xodim |
| POST | `/orders/` | AI draft'idan buyurtma yaratish |
| GET/PATCH | `/orders/{id}/` | ko'rish/tahrirlash |
| POST | `/orders/{id}/confirm/` | tasdiqlash (status → confirmed) |
| POST | `/orders/{id}/status/` | statusni o'zgartirish (izoh va sana bilan) |
| GET | `/orders/statuses/` | status ro'yxati va ruxsat etilgan o'tishlar |
| GET | `/orders/{id}/pdf/` | kommercheskoye taklif PDF |

### 5.5 Manager paneli
| Method | Endpoint | Izoh |
|---|---|---|
| GET | `/team/employees/` | xodimlar + bugungi faollik |
| POST | `/team/employees/` | xodim qo'shish |
| PATCH | `/team/employees/{id}/` | bloklash, rol, limit |
| GET | `/usage/summary/?period=day|week|month&user=` | tokenlar, xarajat, xabarlar |
| GET | `/usage/by-user/` | xodimlar bo'yicha reyting |
| GET | `/usage/conversations/` | eng qimmat suhbatlar |
| GET | `/analytics/conversion/` | suhbat → buyurtma konversiyasi |

### 5.6 Hisob (ilova o'zi ham hisoblay olishi uchun — ixtiyoriy)
| Method | Endpoint |
|---|---|
| POST | `/calc/preview/` | `{measurements:[{length, height, parts:[{variant_id, role, width_m, height_m, coef}], accessories:[{variant_id, qty}]}], services, discount_percent, delivery}` → yuza, chiqindi, bo'linma narxlar, jami |

Bu endpoint **Go bilan bir xil formulani** ishlatishi shart. Shuning uchun formulalar `CalcRule`'da
saqlanadi va ikkala taraf ham shu qiymatlarni o'qiydi. Etalon testlar ikkala tarafda bir xil natija berishini tekshiradi.

---

## 6. Boshqaruv paneli — mobil ilovada

> **Muhim:** alohida web-admin sayt YO'Q. Manager va admin butun boshqaruvni **mobil ilova ichida** qiladi.
> Shuning uchun katalogni **yozish (CRUD) endpointlari REST orqali to'liq ochiladi** va
> mobil ilova uchun qulay qilib loyihalanadi (rasm yuklash, ommaviy narx o'zgartirish, tez qidiruv).

Django admin faqat **texnik zaxira** sifatida qoladi (dasturchi uchun: migratsiya, tuzatish, ommaviy import).
Biznes foydalanuvchi unga kirmaydi.

### 6.1 Katalog boshqaruvi (manager/admin, mobil)
| Method | Endpoint | Izoh |
|---|---|---|
| POST/PATCH/DELETE | `/catalog/products/` , `/{id}/` | mahsulot qo'shish/tahrirlash |
| POST/PATCH/DELETE | `/catalog/variants/` , `/{id}/` | rang/narx/o'lcham varianti |
| POST | `/catalog/variants/bulk-price/` | tanlanganlarga foiz yoki summa bo'yicha narx o'zgartirish |
| POST | `/catalog/products/{id}/images/` | rasm yuklash (multipart, telefon kamerasidan) |
| DELETE | `/catalog/images/{id}/` | rasm o'chirish |
| POST | `/catalog/import/` | Excel/CSV import (ixtiyoriy, dastlabki to'ldirish uchun) |

Mobil UX talablari backend tomondan:
- Rasm serverda avtomatik siqiladi (thumbnail 300px, to'liq 1200px) — mobil trafik tejaladi
- Barcha ro'yxatlar `?search=` va cursor pagination bilan
- `PATCH` qisman yangilashni qo'llab-quvvatlaydi (mobil formda faqat o'zgargani yuboriladi)
- Validatsiya xatolari **maydon bo'yicha** qaytadi (mobil form ostida ko'rsatish uchun):
  `{"errors": {"price": "0 dan katta bo'lishi kerak"}}`

### 6.2 Narx va hisob qoidalari (mobil)
| Method | Endpoint |
|---|---|
| GET/PATCH | `/pricing/calc-rules/` , `/{key}/` |
| GET/PATCH | `/pricing/services/` , `/{key}/` |
| GET/POST/PATCH/DELETE | `/pricing/discount-tiers/` | summaga qarab o'sadigan bosqichlar |
| GET/PATCH | `/pricing/discount-policy/` | qo'lda chegirma chegaralari |
| GET/PATCH | `/pricing/order-defaults/` | avans %, yetkazish, muddat |
| GET/POST/PATCH/DELETE | `/catalog/fasons/` |

Har qoidada `description` bor — mobil ilovada tushuntirish matni sifatida ko'rsatiladi
(manager "seam_allowance nima?" deb o'ylamasligi uchun).

### 6.3 Bilimlar bazasi (mobil)
| Method | Endpoint |
|---|---|
| GET/POST/PATCH/DELETE | `/knowledge/rules/` |

Manager "shu xonaga shu fasonni tavsiya qil" degan qoidani telefondan qo'sha oladi.

### 6.4 System prompt (faqat admin)
| Method | Endpoint |
|---|---|
| GET | `/settings/prompt/` (joriy + versiyalar tarixi) |
| POST | `/settings/prompt/` (yangi versiya) |
| POST | `/settings/prompt/{version}/rollback/` |

### 6.5 Xodimlar va nazorat (manager)
5.5-bo'limdagi endpointlar. Qo'shimcha mobil uchun:
| Method | Endpoint | Izoh |
|---|---|---|
| GET | `/team/employees/{id}/conversations/` | xodimning suhbatlari |
| GET | `/conversations/{id}/transcript/` | suhbatni to'liq o'qish (manager) |
| POST | `/team/employees/{id}/limit/` | limit o'rnatish; `{"is_unlimited": true}` — cheksiz qilish |

**Ruxsatlar matritsasi**
| Endpoint guruhi | employee | manager | admin |
|---|---|---|---|
| chat, katalog o'qish | ✅ | ✅ | ✅ |
| buyurtma yaratish | ✅ | ✅ | ✅ |
| katalog yozish, narx | ❌ | ✅ | ✅ |
| xodimlar, limit, usage | ❌ | ✅ | ✅ |
| calc-rules, knowledge | ❌ | ✅ | ✅ |
| system prompt, ModelPricing, tannarx | ❌ | ❌ | ✅ |

## 7. Katalog sinxronizatsiyasi (Django → Go)

```
Product/Variant/CalcRule/KnowledgeRule saqlansa
   → post_save signal
   → Redis pub/sub kanaliga delta (tenant_id, entity, id, action)
   → Django gRPC Catalog.Watch stream'i orqali Go'ga push
   → Go lokal cache'ini yangilaydi
```
- Go ishga tushganda `Catalog.Snapshot` chaqiradi (butun katalog, versiya raqami bilan)
- Har delta'da `version` oshadi; Go versiyada uzilish sezsa qayta snapshot oladi
- Snapshot hajmi katta bo'lsa (10k+ mahsulot) — sahifalab (pagination) beriladi

---

## 8. Fon vazifalari (Celery)
| Task | Davriylik |
|---|---|
| `save_usage_record` | har javobdan keyin (queue) |
| `save_message` | har javobdan keyin |
| `generate_conversation_title` | birinchi javobdan keyin |
| `daily_usage_rollup` | har kuni 00:05 — `UsageDaily` jadvaliga yig'adi |
| `archive_old_conversations` | haftalik |
| `check_limits_and_notify` | har soat |
| `catalog_reindex` | mahsulot o'zgarganda |
| `stock_low_alert` | har kuni |

---

## 9. Ishlash talablari
- Gateway overhead (Django qatlami) ≤ 150 ms
- SSE'da birinchi belgi: Go javobidan keyin ≤ 50 ms
- Katalog API javobi ≤ 300 ms (100 mahsulot, keshsiz)
- 50 ta parallel chat sessiyasini ko'tarish (1 ta instans)
- **Miqyos:** 20–50 faol xodim, oyiga ~45 000 suhbat. Shuning uchun:
  statistika xom `UsageRecord` dan emas, kunlik `UsageDaily` rollup jadvalidan o'qiladi;
  barcha ro'yxatlar cursor-pagination; 6 oydan eski suhbatlar arxiv jadvaliga ko'chiriladi
- DB: `Message.conversation`, `UsageRecord.created_at`, `ProductVariant.sku` bo'yicha indeks

---

## 10. Testlar
- Model va biznes-mantiq: unit test (pytest-django)
- `/calc/preview/` — 20 ta etalon misol (Go bilan bir xil natija)
- Gateway: gRPC mock bilan SSE oqimi testi
- Permission testlari: employee manager endpointlariga kira olmasligi
- Limit testi: limit tugaganda 429
- Coverage ≥ 70%

---

## 11. Deploy
```yaml
services: postgres, redis, django (uvicorn), celery-worker, celery-beat, go-agent, nginx
```
- `.env` orqali sozlash, sirlar repoga tushmaydi
- Migratsiyalar avtomatik (`entrypoint.sh`)
- Backup: Postgres kunlik dump, media S3'da
- Log: structlog JSON → fayl/ELK; Sentry
