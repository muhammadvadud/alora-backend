# Alora Backend — Go bilan Kelishuv (GO-CONTRACT)

**Kontrakt versiyasi:** 1.4.1 (2026-09-14) · proto paketi `alora.v1` (backward compatible)
**Yagona manba:** `protos/alora.proto`. Ushbu hujjat proto'da ifodalab bo'lmaydigan
semantikani (kalitlar, tartib, kim nimani hisoblaydi) belgilaydi.

---

## 1. Servislar va RPC'lar (gRPC)

### 1.1 Agent servisi (Django → Go)

| RPC | Turi | Vazifa |
|---|---|---|
| `Chat(ChatRequest) → stream ChatEvent` | server-streaming | Matnli suhbat |
| `VoiceChat(stream VoiceChunk) → stream VoiceEvent` | bidirectional | Ovozli suhbat |
| `ResetSession(ResetRequest) → ResetResponse` | unary | Sessiya kontekstini tozalash |
| `Health(Empty) → HealthResponse` | unary | Go agent sog'lig'i |

**`ChatRequest.context` — Django kafolatlaydigan kalitlar** (`apps/chat/services.build_agent_context`):

| Kalit | Qiymat | Go nima qiladi |
|---|---|---|
| `role` | `employee` \| `manager` \| `admin` | `price_quote` da qo'lda chegirma chegarasi (`DiscountPolicy.manual_max_percent_*`) |
| `customer_mode` | `"0"` \| `"1"` | `"1"` — qurilma mijoz qo'lida: prompt'ga "tannarx, ichki izoh, chegirma chegarasini aytma" bloki |
| `conversation_id` | Conversation UUID | `UsageRequest.conversation_id`, `MessageLogRequest.conversation_id` |
| `message_id` | *(rejalashtirilgan)* | idempotent usage uchun; hozircha bo'sh bo'lishi mumkin |
| `prompt_version` | *(ixtiyoriy)* | A/B: aniq prompt versiyasini ishlatish |

Metadata: Django gRPC serveri `Health` dan tashqari barcha RPC'larda `x-service-token`
(`AGENT_SERVICE_TOKEN`) ni tekshiradi. Django klient tomoni (`grpc_client.py`) barcha Agent
RPC'larida `x-service-token` (token bo'sh bo'lmasa) va `x-request-id` yuboradi; request ID
structlog contextvars'dan olinadi, bo'lmasa UUID yaratiladi.

**`ChatEvent.kind` qiymatlari va tartibi:**

```
start → (tool_call → tool_args → tool_result → products?)* → content* → stage → done
                                                                             ↘ error
```

| kind | Maydonlar | Django |
|---|---|---|
| `start`, `content`, `tool_call`, `tool_args`, `tool_result`, `error` | shablon bo'yicha | SSE'ga 1:1 |
| `thinking` | `content` | Go **yubormaydi** (mijoz rejimida sizib chiqmasin) |
| `products` | `products[]` (`ProductRef`) | SSE'ga 1:1 — mobil kartochka chizadi |
| `stage` | `content` = `need\|recommend\|measure\|calc\|variants\|order`, `result` = qisqa holat JSON | SSE'ga 1:1 **va** Celery `update_conversation_stage` → `Conversation.stage`, `Conversation.context["agent_state"]`. Noma'lum bosqich e'tiborsiz |
| `transcript` | `content` = STT matni | Faqat VoiceChat ichida; Django WS'ga 1:1 |
| `done` | `usage` | `save_message_and_usage` |

**`Usage.cost_usd` / `cost_uzs`:** Go **`0` yuboradi**. Narxni Django `ModelPricing`
bo'yicha `apps.usage.services.calculate_cost` hisoblaydi — narx jadvali bitta joyda.
Go faqat token sonlari, `stt_seconds`, `tts_chars`, `latency_ms`, `tool_calls_json` ni to'ldiradi.

### 1.2 Catalog servisi (Django → Go; server Django'da, Go klient)

| RPC | Vazifa |
|---|---|
| `Snapshot(SnapshotRequest) → CatalogSnapshot` | To'liq nusxa, sahifalab (`page_size` ≤ 1000) |
| `Watch(WatchRequest) → stream CatalogDelta` | Real vaqt delta oqimi |

**Snapshot tarkibi (kontrakt 1.1):**

| Maydon | Sahifa | Manba |
|---|---|---|
| `products[]` (+ `variants[]`, `image_urls[]`) | har sahifa | `Product`, `ProductVariant`, `ProductImage` (faqat `is_active`) |
| `categories[]` | **faqat birinchi** (`page_token=""`) | `Category` |
| `calc_rules[]` | faqat birinchi | `CalcRule` |
| `knowledge_rules[]` | faqat birinchi | `KnowledgeRule` |
| `service_prices[]` | faqat birinchi | `ServicePrice` (`is_active`) |
| `discount_tiers[]` | faqat birinchi | `DiscountTier` (`is_active`) |
| `discount_policy` | faqat birinchi | `DiscountPolicy` (singleton; yo'q bo'lsa maydon bo'sh) |
| `order_defaults` | faqat birinchi | `OrderDefaults` (singleton) |
| `fasons[]` (+ `parts[]`, `accessories[]`) | faqat birinchi | `Fason`, `FasonPart`, `FasonAccessory` |
| `prompt` | faqat birinchi | `PromptVersion` (`is_current=True`; yo'q bo'lsa bo'sh → Go fallback prompt) |

Go: birinchi sahifadan hamma narsani, keyingi sahifalardan faqat `products` ni oladi;
`next_page_token=""` bo'lguncha davom etadi; `version` birinchi sahifadagi qiymat.

**Sonlar:** eski maydonlar (`CatalogVariant.price`, `width_m`, `CatalogCalcRule.value`)
shartnoma qoidasi bo'yicha `double` bo'lib qoladi — Go ularni `decimal.NewFromFloat` emas,
`strconv.FormatFloat(v, 'f', -1, 64)` → `decimal.NewFromString` bilan oladi.
Kontrakt 1.1 da qo'shilgan barcha pul/foiz/ulush maydonlari **decimal matn** (`"12500.00"`).

**`cost_price` (tannarx) hech qachon snapshot/delta'ga tushmaydi** (rules §4.11).

**Delta (`CatalogDelta`):**

| `entity` | `tenant_id` | `payload_json` (create/update) | Go amali |
|---|---|---|---|
| `product` | tenant | `CatalogProduct` JSON (variantlar va rasmlar bilan) | butun mahsulotni almashtirish |
| `variant` | tenant | `CatalogVariant` JSON; delete'da `{"product_id"}` | mahsulot ichida variantni almashtirish/olib tashlash |
| `category` | tenant | `CatalogCategory` JSON | |
| `calc_rule` | `""` | `CatalogCalcRule` JSON (`entity_id` = UUID, kalit payload'da) | `key` bo'yicha almashtirish |
| `knowledge_rule` | `""` | `CatalogKnowledgeRule` JSON | |
| `service_price` | `""` | `CatalogServicePrice` JSON | `key` bo'yicha |
| `discount_tier` | `""` | `CatalogDiscountTier` JSON | `id` bo'yicha |
| `discount_policy` | `""` | `CatalogDiscountPolicy` JSON | butun obyektni almashtirish |
| `order_defaults` | `""` | `CatalogOrderDefaults` JSON | butun obyektni almashtirish |
| `fason` | tenant | `CatalogFason` JSON — **bo'lak/aksessuar o'zgarsa ham butun fason** | butun fasonni almashtirish |
| `prompt` | `""` | `CatalogPrompt` JSON | joriy promptni almashtirish |
| `catalog` | so'ralgan | bo'sh, `action="FULL_RESYNC"` | quyida |

`payload_json` — proto JSON (snake_case), Snapshot'dagi mos xabar bilan **bir xil**
(`apps/chat/grpc_server/catalog_payload.py` — ikkalasi uchun yagona manba).
`tenant_id=""` bo'lgan (global) delta'lar har qanday `WatchRequest.tenant_id` filtridan o'tadi.

**Redis:** kanal `alora:catalog:deltas`, versiya kaliti `alora:catalog:version` (`INCR`, monoton).

**Watch protokoli:**
1. Go `Watch(from_version=V)` ochadi (V — oxirgi qo'llangan versiya).
2. Django: `V < current` bo'lsa **bitta** `CatalogDelta{action:"FULL_RESYNC", entity:"catalog", version:current}`
   yuboradi va stream'ni **yopadi** (oraliq delta'lar Redis'da saqlanmaydi).
3. Go: `FULL_RESYNC` → `Snapshot` ni qayta oladi → yangi `version` bilan `Watch` ni qayta ochadi.
4. `V == current` bo'lsa stream ochiq turadi, yangi delta'lar `version > V` bo'lib keladi.
5. Go delta `version` ketma-ketligi uzilganini ko'rsa (kutilgan `V+1` emas) — 3-banddagi kabi resync.

### 1.3 Backend servisi (Go → Django, asinxron)

| RPC | Vazifa | Idempotentlik |
|---|---|---|
| `ReportUsage(UsageRequest) → Ack` | token/xarajat hisoboti (Celery `usage` navbati) | `message_id` + `session_id` |
| `SaveOrderDraft(OrderDraftRequest) → OrderDraftResponse` | AI qoralamasi → `Order(status=draft)`, `Conversation.order` bog'lanadi | Go **retry qilmaydi**; Django 5 daqiqa `session_id` + `items_json` hash bo'yicha idempotent |
| `LogMessage(MessageLogRequest) → Ack` | suhbat tarixi | `session_id` + rol + matn + tokenlar (`save_message` get_or_create) |

**`OrderDraftRequest.items_json` sxemasi** — `tests/fixtures/calc_cases.json` dagi `input`
bilan bir xil, ya'ni `apps.orders.services.create_order_from_draft` payload'i:

```json
{
  "measurements": [
    {"length": "3.000", "height": "2.500",
     "parts": [{"variant_id": "…", "role": "portyera", "width_m": "3.000", "height_m": "2.500", "coef": "2.500"}],
     "accessories": [{"variant_id": "…", "qty": "2"}]}
  ],
  "services": ["sewing", "tape", "hook"],
  "delivery": true,
  "discount_percent": "0"
}
```
Sonlar decimal matn. `customer_name`, `customer_phone`, `address`, `note` — alohida maydonlar
(LLM kontekstiga tushmaydi, Go ularni faqat shu RPC'ga uzatadi).
`SaveOrderDraft` `create_order_from_draft` orqali order yaratadi; bir xil `session_id` va
`items_json` 5 daqiqa ichida takrorlansa, mavjud order qaytariladi.

### 1.4 Pricing servisi (Go → Django, SINXRON)

`Pricing.CalcPreview` narx hisobini faqat Django'dagi yagona
`apps.pricing.services.calculator.calculate_preview` funksiyasiga uzatadi. Go
`payload_json` ichida `tests/fixtures/calc_cases.json` dagi `input` sxemasini yuboradi:
`measurements`, `services`, `delivery`, `discount_percent`. Muvaffaqiyatli javobdagi
`result_json` aynan shu fayldagi `expected` sxemasidir; barcha sonlar decimal matn.

Go faqat `UNAVAILABLE` holatida bir marta retry qiladi va RPC timeout'i 3 soniya.
`ValidationError` `error="Ma'lumotlar noto'g'ri"` hamda maydonlar bo'yicha
`error_fields_json`ga map qilinadi; noto'g'ri JSON umumiy `error` bilan qaytadi.
Kutilmagan server xatosida ichki tafsilotlar yuborilmaydi. Django gRPC serveri
`run_grpc` command orqali `[::]:9091` da ishlaydi va `x-service-token` interceptorini qo'llaydi.

**`CalcPreview.result_json` yig'indi maydonlari (1.4.1):** AI yig'indi hisoblamasligi
(qatorlarni o'zi qo'shib "jami ... so'm" demasligi) uchun tayyor summalar qaytariladi.

| Maydon | Qayerda | Ma'no |
|---|---|---|
| `parts_total` | har `measurements[i]` da | Shu o'lchamdagi barcha `parts[].line_total` yig'indisi |
| `measurement_total` | har `measurements[i]` da | `parts_total + accessories_total` (shu o'lcham uchun) |
| `parts_total` | ildizda | Barcha o'lchamlar bo'ylab bo'laklar yig'indisi |
| `accessories_total` | ildizda | Barcha o'lchamlar bo'ylab aksessuarlar yig'indisi |
| `services_total` | ildizda | Xizmat qatorlari (`line_total`) yig'indisi — `delivery` bundan tashqari |

`subtotal` va `total` foydalanuvchiga ko'rsatiladigan qat'iy qiymatlar bo'lib qoladi;
AI ularni qayta hisoblamaydi va `subtotal` o'rniga `parts_total`/`services_total`
kabi oraliq summalarni "jami" deb talqin qilmaydi (`delivery` subtotalga kirmaydi,
`total` chegirma va yaxlitlashdan keyin hisoblanadi). Barcha qiymatlar decimal matn.

### 1.5 VoiceChat metadata

Django `voice_chat_stream` har bir VoiceChat stream'ida mavjud `x-service-token` va
`x-request-id` ustiga quyidagi metadata'ni yuboradi: `x-session-id`, `x-user-id`,
`x-tenant-id`, `x-role`, `x-locale`, `x-customer-mode` (`"0"|"1"`) va
`x-conversation-id`. Bu kalitlardan biri yo'q bo'lsa, Go `InvalidArgument` qaytaradi.

Kirish audio formati `pcm_s16le` (16 kHz, mono) yoki `opus`; chiqish formati provider'ga
bog'liq va har bir event'dagi `audio_format` bilan ko'rsatiladi. `VoiceEvent.kind` qiymatlari:
`transcript|text|audio|error|done`; `chat_event` ichida umumiy `ChatEvent` bo'lishi mumkin.

---

## 2. Etalon test kelishuvi

`tests/fixtures/calc_cases.json` — Django va Go uchun **bir xil** fayl (sha256 CI'da
solishtiriladi). Django: `tests/pricing/test_reference_cases.py`; Go: `internal/curtains/calc_test.go`.
Formula (`apps/pricing/services/calculator.py`) o'zgarsa etalon fayl birga o'zgaradi va
Go jamoasiga xabar qilinadi. 20 ta holat, hammasi ±0 farq bilan o'tishi shart.

---

## 3. Proto'ni boshqarish

1. Faqat `protos/alora.proto` tahrirlanadi (shu repo).
2. `bash scripts/gen_proto.sh` → `grpc_gen/` yangilanadi.
3. `bash scripts/export_proto.sh <go_repo>` → Go repoda `proto/alora.proto` (diff ko'rsatadi).
4. Go: `buf generate` (`go_package = github.com/muhammadvadud/alora-agent/gen/alorav1;alorav1` —
   Go moduli shu nom bilan; o'zgarsa proto'dagi option birga o'zgaradi).
5. Backward compatibility: maydon raqami/tipi o'zgarmaydi, eski maydon o'chirilmaydi, faqat qo'shiladi.

## 4. Kontrakt o'zgarishlar jurnali

| Versiya | Sana | O'zgarish |
|---|---|---|
| 1.0 | 2026-09-08 | Dastlabki shartnoma: Agent, Catalog, Backend servislari |
| 1.1 | 2026-09-13 | `CatalogSnapshot` 8–13: `service_prices`, `discount_tiers`, `discount_policy`, `order_defaults`, `fasons`, `prompt`; yangi `Catalog*` xabarlari; delta payload'lari barcha entity'lar uchun; `ChatEvent.kind` ga `products`, `stage`; `context` kalitlari (`role`, `customer_mode`, `conversation_id`); `cost_*` faqat Django; `FULL_RESYNC` protokoli; `items_json` sxemasi; `go_package` tuzatildi; mahsulotdan boshqa ro'yxatlar faqat birinchi sahifada |
| 1.2 | 2026-09-13 | `Pricing.CalcPreview`; Django gRPC server bootstrap (`run_grpc`, 9091); server tomonida `x-service-token` interceptor |
| 1.3 | 2026-09-13 | `SaveOrderDraft` haqiqiy order yaratadi va Conversation bilan bog'lanadi; Django klient Agent RPC'lariga `x-service-token` va `x-request-id` metadata yuboradi; 5 daqiqalik idempotentlik |
| 1.4 | 2026-09-13 | VoiceChat metadata, `transcript` kind va transcript/audio/done WS oqimi |
| 1.4.1 | 2026-09-14 | `CalcPreview.result_json` ga tayyor yig'indilar qo'shildi: har `measurements[i]` uchun `parts_total`, `measurement_total`; ildizda `parts_total`, `accessories_total`, `services_total`. AI hisoblamasligi uchun tayyor. `subtotal`/`total` o'zgarmadi |
