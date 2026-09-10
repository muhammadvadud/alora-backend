# ALORA — Umumiy Texnik Topshiriq (Master TZ)

**Loyiha:** Alora — parda savdosi do'koni uchun AI sotuvchi-yordamchi
**Versiya:** 1.0 (2026-08-30)
**Hujjatlar:** ushbu fayl (umumiy) + `01-BACKEND-TZ.md` + `02-AI-TZ.md` + `03-MOBILE-TZ.md`

---

## 1. Loyihaning mohiyati

Alora — ChatGPT/Claude ko'rinishidagi chat ilova, lekin **faqat parda sotishga** ixtisoslashgan.
Foydalanuvchi — **mijoz emas, do'kondagi sotuvchi**. AI sotuvchining "aqlli hamkasbi": mijoz bilan
suhbat davomida savol beradi, fason va mato tavsiya qiladi, o'lchamdan material hisoblaydi, narx
chiqaradi, 3 xil variant tayyorlaydi va buyurtma qoralamasini shakllantiradi.

**Asosiy qiymat:** yangi sotuvchi ham 10 yillik tajribali usta darajasida tavsiya bera oladi.

### 1.1 Nima QILADI
- Mijoz ehtiyojini savol-javob orqali aniqlaydi (xona turi, yorug'lik, uslub, rang, budjet, o'lcham)
- Do'konda **mavjud** mahsulotlar ichidan mos variantlarni tanlaydi
- Parda materialini (metr), aksessuarlarni va tikuv hajmini hisoblaydi
- To'liq narxni chiqaradi: mato + tikuv + tasma + karniz + montaj + qo'shimchalar
- Arzon / o'rtacha / premium — 3 ta variant tayyorlaydi
- Buyurtma qoralamasini (draft) tuzadi, sotuvchi tasdiqlaydi
- Ovoz bilan gaplashadi (sotuvchi qo'li band bo'lganda — o'lchov olayotganda)

### 1.2 Nima QILMAYDI
- Ochiq internetda mijozga xizmat ko'rsatmaydi (faqat do'kon ichida, sotuvchi qurilmasida)
- O'zi mustaqil buyurtma tasdiqlamaydi — **yakuniy tasdiq har doim sotuvchida**
- Bazada yo'q mahsulotni o'ylab topmaydi (hallucination taqiqlanadi — tool natijasidan tashqari narx aytmaydi)
- To'lov qabul qilmaydi (1-bosqichda)

### 1.3 Foydalanuvchilar va rollar

| Rol | Kim | Imkoniyatlar |
|---|---|---|
| `employee` | Sotuvchi | AI chat (matn + ovoz), o'z suhbatlari tarixi, buyurtma qoralamasi yaratish |
| `manager` | Do'kon rahbari | `employee` hamma imkoniyatlari + **mahsulot bazasi va narxlarni boshqarish (mobil ilovada)**, xodimlar, har bir xodimning token/xarajat statistikasi, suhbatlarni ko'rish, limit qo'yish, buyurtmalar |
| `admin` | Texnik admin | `manager` + system prompt, LLM sozlamalari, tannarx, ModelPricing |

**Mijoz rejimi:** sotuvchi o'z planshetida "Mijoz rejimi"ni yoqib, qurilmani mijozga uzatishi mumkin.
Bu rejimda faqat chat ko'rinadi (narx tannarxi, ichki izohlar, admin tugmalar yashiriladi).
Ochiq sayt yoki App Store'dagi ommaviy ilova **YO'Q**.

---

## 2. Arxitektura

### 2.1 Umumiy sxema

```
┌──────────────────────┐
│  Flutter mobil app   │  sotuvchi telefoni / plansheti
│  chat + ovoz + katalog│
└───────────┬──────────┘
            │ HTTPS: REST (auth, katalog, buyurtma)
            │ SSE/WebSocket: chat streaming
            ▼
┌──────────────────────────────────────────┐
│  Django backend (ASGI — Uvicorn)         │
│  ├─ Auth / JWT / RBAC                     │
│  ├─ Mahsulot bazasi + variantlar          │  ← haqiqat manbai (source of truth)
│  ├─ Narx va hisob koeffitsientlari        │
│  ├─ Buyurtmalar                            │
│  ├─ Token/xarajat hisobi va limitlar      │
│  ├─ Admin panel (Django admin + manager UI)│
│  └─ Chat gateway (Go'ga proxy)            │
└───────────┬──────────────────────┬───────┘
            │ gRPC                 │ gRPC (CatalogSync push)
            │ server-streaming     │
            ▼                      ▼
┌──────────────────────────────────────────┐
│  Go AI agent (UzStack/agent asosida)     │
│  ├─ ReAct sikli + Event oqimi             │
│  ├─ Tool'lar (katalog, hisob, narx, order)│
│  ├─ Katalog cache/replika (Django'dan)    │
│  ├─ LLM: DeepSeek (asosiy) / Claude/OpenAI│
│  ├─ STT / TTS (ovoz)                      │
│  └─ Sessiya tarixi (Postgres)             │
└───────────┬──────────────────────────────┘
            │
      ┌─────┴─────┬──────────┐
      ▼           ▼          ▼
  PostgreSQL   Redis    LLM/STT/TTS API
  (umumiy)    (cache)   (tashqi)
```

### 2.2 Nega shunday (qarorlar va sabablar)

**1) Django — gateway.**
Butun trafik Django orqali o'tadi: auth, RBAC, limit tekshiruvi, audit log bir joyda.
Go xizmati tashqi internetga **umuman ochilmaydi** (faqat ichki tarmoq).
Buning uchun Django **ASGI** (Uvicorn/Daphne) rejimida ishlaydi — SSE/WebSocket proxy qilish uchun shart.
`StreamingHttpResponse` + async view ishlatiladi.

**2) Django ↔ Go — gRPC.**
- Chat: `Agent.Chat` — **server-streaming RPC**. Go har bir Event'ni (`content`, `tool_call`, `tool_result`, `done`) alohida message qilib yuboradi, Django ularni SSE frame'ga o'girib mobilga uzatadi.
- Sabab: SSE-over-HTTP proxy'ga nisbatan gRPC'da tip xavfsizligi (proto shartnoma), backpressure, keep-alive va reconnect tayyor.

**3) Katalogni Go tarafda cache qilish (MUHIM tuzatish).**
Naiv variant: Go har `product_search` tool chaqiruvida Django'ga gRPC yuboradi.
Muammo: bitta AI javobida 3-6 ta tool chaqiruvi bo'ladi → har biri Django→DB→Django→Go sakrash → javob 2-4 soniya sekinlashadi va Django yuklamasi ortadi.

Yechim:
- Go ishga tushganda `Catalog.Snapshot` RPC bilan butun katalogni oladi (mahsulot + variant + narx qoidalari + koeffitsientlar).
- Keyin `Catalog.Watch` **server-streaming** RPC ochiq turadi. Django'da mahsulot o'zgarsa (`post_save` signal → Redis pub/sub → gRPC stream) Go'ga delta yuboriladi.
- Tool'lar **lokal xotiradan** ishlaydi → javob millisekundlarda.
- Aloqa uzilsa: Go 30 soniyada qayta ulanadi, snapshot'ni yangilaydi. Snapshot yoshi (`age`) 10 daqiqadan oshsa AI javobiga "narxlar yangilanmayotgan bo'lishi mumkin" ogohlantirishi qo'shiladi va manager'ga alert ketadi.

**4) Go → Django gRPC faqat yozish uchun:**
`UsageReport` (token/xarajat), `OrderDraft` (buyurtma qoralamasi), `ConversationLog` (suhbat metadatasi).
Bular **asinxron** (fire-and-forget + retry queue) — AI javobini kutib turmaydi.

**5) Sessiya tarixi.**
Shablondagi `session.Store` interfeysi saqlanadi, `NewPostgres` ishlatiladi. Jadval kengaytiriladi:
`session_id`, `message JSONB`, + `user_id`, `tenant_id`, `created_at`. Manager suhbatni Django orqali o'qiydi.

### 2.3 Texnologiyalar

| Qatlam | Texnologiya |
|---|---|
| Mobil | Flutter 3.x, Dart, Riverpod, Dio, `flutter_sound`/`record`, `just_audio` |
| Backend | Python 3.13, Django 5.x, DRF, Django ASGI (Uvicorn), Celery, `grpcio` |
| AI | Go 1.26, CloudWeGo Eino, `UzStack/agent` shabloni, `google.golang.org/grpc` |
| DB | PostgreSQL 16 (umumiy), Redis 7 (cache, pub/sub, Celery broker) |
| LLM | DeepSeek (asosiy: `deepseek-v4-pro`), Claude/OpenAI — config bilan almashadi |
| Ovoz | STT: Whisper API / Gemini; TTS: ElevenLabs yoki Google TTS (o'zbek ovozi) |
| Fayl | S3-mos xotira (mahsulot rasmlari, audio) |
| Deploy | Docker Compose (start), keyin Kubernetes; Nginx/Caddy |
| Monitoring | Sentry, Prometheus + Grafana, structured log (slog / structlog) |

---

## 3. Asosiy biznes oqimi (sotuv sikli)

AI suhbatni 7 bosqichli sotuv siklida olib boradi. Har bosqichda **holat (state)** saqlanadi.

```
1. SALOM/EHTIYOJ  → 2. TAVSIYA  → 3. O'LCHOV  → 4. HISOB
                                                    ↓
7. BUYURTMA  ←  6. TANLOV  ←  5. VARIANTLAR (3 ta)
```

### 1-bosqich: Ehtiyojni aniqlash
AI ketma-ket (bir vaqtda BITTA savol) aniqlaydi:
- **Xona turi:** mehmonxona / yotoqxona / kelin-kuyov xonasi / bolalar xonasi / oshxona / ofis / zal
- **Yorug'lik:** xona yorug'roq bo'lsinmi yoki qorong'iroq? Deraza qaysi tomonga qaraydi (janub → issiq/yorqin → blackout kerak; shimol → yengil tul)
- **Mato bezagi:** gulli / gulsiz (tekis) / geometrik / jakkard
- **Uslub:** klassik / zamonaviy / hi-tech / minimalizm / sharqona / provans
- **Xona rangi:** devor, mebel, pol rangi (parda ranggi shularga moslanadi)
- **Deraza konstruksiyasi:** rom soni, eshik/balkon bormi, karniz bormi yoki kerakmi, shift balandligi, deraza devordan qancha uzoq
- **Budjet:** taxminiy summa yoki "arzonroq/o'rtacha/qimmatroq"

> AI hech qachon 5 ta savolni birdaniga bermaydi. Real sotuvchi kabi bittalab so'raydi va
> javobdan keyin qisqa izoh beradi ("Janubga qaragan bo'lsa, kunduzi issiq bo'ladi — blackout astar tavsiya qilaman").

### 2-bosqich: Fason va mato tavsiyasi
- Bilimlar bazasi (`knowledge base`) + mahsulot katalogi asosida 2-4 ta fason taklif qilinadi
- Har tavsiya **sababi bilan**: "Hi-tek mehmonxonaga gulsiz, tekis mato — rim pardasi yoki to'g'ri portyera. Devor och kulrang bo'lgani uchun bir ton to'qroq grafit rang uyg'un keladi."
- Mahsulot rasmi ilovada ko'rsatiladi (AI `product_id` qaytaradi, Flutter kartochka chizadi)

### 3-bosqich: O'lchov
AI so'raydi: **karniz uzunligi (yoki deraza eni)**, **kerakli balandlik** (karnizdan poligacha / deraza tokchasigacha), **qavat/qatlam soni** (tul + portyera + lambrekan).
Noaniq bo'lsa o'lchash usulini tushuntiradi ("karnizni devordan devorgacha o'lchang, deraza emas").

### 4-bosqich: Hisob-kitob (`curtain_calculate` tool)
Material va aksessuar miqdori hisoblanadi. **Bu bosqichda ham tavsiya davom etadi:**
- "Bu mato eni 280 sm — balandligingiz 260 sm, ya'ni chiqindi kam chiqadi va chok ham kerak emas"
- "Burma koeffitsientini 3.0 dan 2.5 ga tushirsak, ko'rinish deyarli bir xil, lekin 1.2 mln so'm tejaladi"
- "Bu mato 1 m² — 180 000 so'm. Yoniga o'xshash 140 000 so'mligi ham bor, farqi faqat tarkibida"

### 5-bosqich: 3 ta variant
| Variant | Mantiq |
|---|---|
| **Arzon** | Bitta matodan sodda fason, eng past narxli mos mato, K=2.0, oddiy tasma, mavjud karniz |
| **O'rtacha** | Sifat/narx balansi, koeffitsient 2.5, tul + portyera |
| **Premium** | Ko'p matoli fason (kant, ikkinchi rang, lambrekan), yuqori segment, K=3.0, astar, yangi karniz + montaj |

Har variant uchun: mahsulotlar ro'yxati, metrlar, bo'linma narxlar, **jami summa**.

### 6-bosqich: Tanlov va tuzatish
Mijoz "biroz arzonroq" desa — AI qaysi qismni o'zgartirish mumkinligini aytadi (mato, koeffitsient, lambrekandan voz kechish).

### 7-bosqich: Buyurtma qoralamasi
`order_draft` tool: mijoz ismi, telefon, manzil, o'lchamlar, mahsulotlar, jami summa, avans, muddat.
Sotuvchi ilovada ko'radi → tahrirlaydi → **"Tasdiqlash"** bosadi → Django'da haqiqiy `Order` yaratiladi.

---

## 4. Hisob-kitob mexanizmi (Calculation Engine)

> **Muhim:** formulalar kodga qattiq yozilmaydi. Barcha koeffitsient va narxlar Django admin'da
> tahrirlanadigan `CalcRule` / `ServicePrice` obyektlarida saqlanadi va Go'ga sinxronlanadi.
> Buyurtmachi hisoblash uslubini keyin batafsil o'rgatganda — faqat qiymat/qoida qo'shiladi, kod o'zgarmaydi.

### 4.0 To'rtta asosiy qoida (buyurtmachi tasdiqladi)

**1) Tayyor parda sotilmaydi.** Har bir buyurtma — o'lchov bo'yicha tikiladi. Ya'ni hisob doim
mato + tikuv + aksessuar + xizmatlardan yig'iladi, "dona narxi" degan tushuncha yo'q.

**2) Narx metr kvadrat (m²) bo'yicha.** Mato pog'onali metr bilan emas, **yuza** bilan hisoblanadi.
Shuning uchun asosiy o'lchov birligi — `m²`, mahsulot variantida narx `narx/m²` ko'rinishida saqlanadi.

**3) Bitta parda — bir nechta matodan.** Fason va derazaning joylashuviga qarab bitta pardada
**1 tadan 10 tagacha** har xil mato ishlatilishi mumkin (asosiy portyera, tul, ikkinchi rang,
kant/chiziq, lambrekan bo'laklari, dekor qo'shimchalar). Ba'zi pardalar esa bitta materialdan iborat.

**4) Matodan tashqari bezak va furnitura ham bor.** Parda ilgichlari va dekorativ gullar,
broshka, podxvat (parda ushlagich), kisti, bahroma, halqa, magnit ushlagich va shunga o'xshashlar.
Bular **dona** yoki **metr** bilan sotiladi (m² emas) va hisobga alohida qatorlar bo'lib kiradi.

Demak hisob **bir bosqichli emas, kompozitsion**: parda = bo'laklar to'plami, har bo'lak alohida
hisoblanadi va oxirida yig'iladi.

### 4.1 Kompozitsiya modeli

```
Buyurtma
└── O'lchov (bitta deraza / xona)     L, H, karniz, izoh
    └── Parda (fason)                  masalan "ikki rangli portyera + tul + lambrekan"
        ├── Bo'lak 1  asosiy portyera   mato A · o'z eni va balandligi · K      [m²]
        ├── Bo'lak 2  ikkinchi rang     mato B · eni 0.4 m chiziq · K           [m²]
        ├── Bo'lak 3  tul               mato C · butun eni · K                  [m²]
        ├── Bo'lak 4  lambrekan         mato D · balandligi 0.45 m · K          [m²]
        └── Bezaklar                    gul ×2 · podxvat ×2 · bahroma 4.2 m     [dona / metr]
```

Har bo'lakda:
| Maydon | Ma'nosi |
|---|---|
| `variant_id` | qaysi mato (rang va narxi bilan) |
| `role` | portyera · tul · lambrekan · kant · dekor · astar |
| `width_m` | shu bo'lak egallaydigan karniz kengligi (butun `L` yoki uning bir qismi) |
| `height_m` | shu bo'lakning balandligi (butun `H` yoki lambrekan kabi qisman) |
| `coefficient` | shu bo'lakning burma koeffitsienti (tul odatda portyeradan yuqori) |

### 4.2 Formulalar

**Bitta bo'lak uchun:**
```
burma eni    B = width_m × K
hisob bal.   Hp = height_m + p          p — podgib (yuqori + past)
yuza         S = B × Hp                 [m²]
mato narxi   P = S × narx_1m2
```

**Parda (bitta deraza) uchun:**
```
S_total = Σ S_i                          barcha bo'laklar yuzasi
P_fabric = Σ (S_i × narx_1m2_i)          har mato o'z narxida
```

**Chiqindi tekshiruvi (ogohlantirish uchun, narxga qo'shilmaydi):**
Mato rulon eni `W` bilan kelgani uchun kesishda chiqindi bo'ladi.
`Hp > W` bo'lsa bo'lak panellarga bo'linadi (chok kerak):
```
N = ceil( B / (W − 2s) )          panellar soni
S_cut = N × Hp × W                 aslida kesiladigan yuza
chiqindi% = (S_cut − S) / S_cut
```
Chiqindi 20% dan oshsa AI ogohlantiradi va **boshqa eni bo'lgan matoni** yoki
**bo'lakni boshqacha yo'naltirishni** taklif qiladi.

**Bezak va furnitura** (dona yoki metr bilan, yuzaga bog'liq emas):
```
P_decor = Σ (qty_i × narx_i)
```
Misol: dekorativ gul ×2 (har biri 85 000), podxvat ×2 (120 000), bahroma 4.2 m (35 000/m)
→ 170 000 + 240 000 + 147 000 = **557 000 so'm**.
Miqdor ba'zan avtomatik: `per_side` — har tomonga 1 ta (ya'ni 2 ta), `per_meter` — `L` bo'yicha.

**Xizmatlar va texnik aksessuarlar** (bo'laklar yig'indisidan keyin, bitta deraza bo'yicha):
```
Tikuv       P_sewing  = (L × K) × tikuv_1m      yoki   S_total × tikuv_1m2   ← qoidaga qarab
Tasma       T = L × K                            metr
Halqa       C = ceil(L × K / qadam)              qadam ≈ 0.10 m
Astar       alohida bo'lak sifatida kiritiladi (o'z yuzasi bilan)
Karniz      P_rod     = L × karniz_1m            yangi karniz kerak bo'lsa
Montaj      P_install = L × montaj_1m            yoki belgilangan summa
```

**Yakuniy summa (butun buyurtma bo'yicha):**
```
subtotal  = Σ (har deraza: P_fabric + P_decor + P_sewing + P_acc + P_rod + P_install)
chegirma  = manager qoidasi bo'yicha (4.4)
delivery  = manager kiritadi yoki default
TOTAL     = subtotal − chegirma + delivery
avans     = TOTAL × avans%                        manager kiritadi yoki default
qoldiq    = TOTAL − avans
```

### 4.3 Qoidalar va tekshiruvlar
- `L`: 0.5–15 m, `H`: 0.5–6 m — chegaradan chiqsa AI qayta so'raydi
- Bo'laklarning `width_m` yig'indisi `L` dan oshmasligi kerak (qatlamlar bundan mustasno:
  tul va portyera bir vaqtda butun `L` ni egallaydi — ular **qatlam**, bo'lak emas)
- Har bo'lakda mato tanlangani shart; tanlanmagan bo'lak narxga kirmaydi va AI buni aytadi
- Bezak (gul, podxvat, kisti) ixtiyoriy — AI uslubga qarab taklif qiladi, lekin majburlamaydi
- Narxni **faqat tool** hisoblaydi; AI o'z boshidan ko'paytirmaydi

### 4.4 Chegirma, avans, yetkazib berish (buyurtmachi tasdiqladi)
- **Chegirma foizini manager kiritadi.** Bundan tashqari **summaga qarab o'sadigan** bosqichli
  chegirma bo'ladi — masalan 5 mln dan yuqori 3%, 10 mln dan yuqori 5%, 20 mln dan yuqori 8%.
  Bosqichlar va foizlar — manager panelida tahrirlanadi (`DiscountTier`).
- **Avans foizini manager kiritadi**; kiritmasa `CalcRule.default_prepayment_pct` ishlaydi.
- **Yetkazib berish narxini manager kiritadi**; kiritmasa `ServicePrice.delivery` default qiymati.
- Sotuvchi (`employee`) chegirmani faqat manager belgilagan **yuqori chegaragacha** bera oladi.

### 4.5 Yaxlitlash
Yuza 0.1 m² gacha yuqoriga, summa 1000 so'mgacha yaxlitlanadi (qoidalar `CalcRule` da).

### 4.6 Ombor qoldig'i — v1 da yo'q
Buyurtmachi tasdiqladi: v1 da ombor qoldig'i hisobga olinmaydi. `stock_check` tool'i,
`stock_qty` maydoni va "omborda yetmaydi" ogohlantirishlari **v1 dan chiqarildi** (v2 ga qoldirildi).

## 5. Bilimlar bazasi (sotuv aqli)

AI "mukammal sotuvchi" bo'lishi uchun kerak bo'lgan bilim **kodda emas, bazada** saqlanadi
(`KnowledgeRule` jadvali) — do'kon egasi yangi qoida qo'sha oladi.

Qoida turlari:
| Tur | Misol |
|---|---|
| Xona → fason | Mehmonxona + klassik → portyera + tul + lambrekan, K=2.5-3.0 |
| Xona → fason | Oshxona → kalta parda / rim pardasi, K=2.0 |
| Xona → fason | Kelin-kuyov xonasi → yorqin, atlas/velvet, gulli, lambrekanli, K=3.0 |
| Yorug'lik → mato | Janubga qaragan → blackout yoki qalin astar |
| Uslub → bezak | Hi-tech / minimalizm → gulsiz, tekis, geometrik; rim yoki rulon parda |
| Rang uyg'unligi | Devor och → parda 1-2 ton to'q; mebel yorqin → parda neytral |
| Konstruksiya | Balkon eshigi bor → bir tomoni ochiladigan, podxvat bilan |
| Konstruksiya | Shift balandligi 3 m+ → vertikal chiziqli mato, uzun portyera |
| Qarshi e'tiroz | "Qimmat" → koeffitsientni tushirish / lambrekandan voz kechish / arzonroq analog |

Bu qoidalar Go tarafda **system prompt'ga dinamik qo'shiladi** (yoki `knowledge_lookup` tool orqali olinadi —
hajmi kattalashsa ikkinchi variant).

---

## 6. Ovoz bilan ishlash

**Tanlangan yechim: server tomonda STT + TTS (1-bosqich).**

```
Sotuvchi mikrofonga gapiradi
  → Flutter: audio yozadi (Opus/WAV 16kHz), VAD bilan sukut aniqlanadi
  → Django gateway (WebSocket) → Go
  → STT (Whisper/Gemini, uz+ru) → matn
  → ReAct agent → javob matni stream bo'lib chiqadi
  → TTS (jumla-jumla, chunk bo'lib) → audio stream
  → Flutter: kelgan audio bo'laklarini ketma-ket ijro etadi
```

Talablar:
- **Push-to-talk** va **erkin suhbat** rejimlari
- Javob matni ekranda ham ko'rinadi (audio bilan parallel)
- Gapni bo'lish (barge-in): foydalanuvchi gapira boshlasa TTS to'xtaydi
- O'zbek tili (lotin/kirill) + rus tili aralash gapirishni tushunish
- Raqamlarni to'g'ri o'qish: "2 500 000 so'm" → "ikki million besh yuz ming so'm"
- Ovoz xarajati ham token hisobiga qo'shiladi (STT: daqiqa, TTS: belgi)

2-bosqichda realtime speech-to-speech API'ga o'tish mumkin — arxitektura buni to'sib qo'ymaydi.

---

## 7. Token va xarajat nazorati

Har bir AI javobidan keyin Go → Django `UsageReport` yuboradi:
```
user_id, conversation_id, message_id, provider, model,
prompt_tokens, completion_tokens, cached_tokens, reasoning_tokens,
stt_seconds, tts_chars, latency_ms, tool_calls[], cost_usd, cost_uzs
```

Manager panelida:
- Xodim bo'yicha: bugun / hafta / oy — xabarlar soni, tokenlar, xarajat
- Suhbat bo'yicha: eng qimmat suhbatlar
- Limit: xodimga kunlik/oylik token yoki summa limiti; **har bir xodimga alohida** qo'yiladi va
  xohlagan xodimga **cheksiz** (limitsiz) qilib belgilanadi. Limit tugasa chat bloklanadi va manager'ga xabar
- Konversiya: nechta suhbat buyurtmaga aylandi (sotuv samaradorligi)

Narx jadvali (`ModelPricing`) Django admin'da — provider narxi o'zgarsa kod tegilmaydi.

---

## 8. Xavfsizlik

- JWT (access 15 daq / refresh 30 kun), refresh rotation
- Go xizmati faqat ichki tarmoqda; gRPC — mTLS yoki service-token
- Rol asosida ruxsat (DRF permission klasslari)
- Mijoz shaxsiy ma'lumotlari (ism, telefon) — faqat Django'da, LLM'ga **yuborilmaydi**
  (buyurtmada AI'ga `customer_ref` beriladi, telefon raqami emas)
- Prompt injection himoyasi: tool natijalari va mahsulot tavsiflari — ma'lumot, buyruq emas
- Audit log: kim qachon narxni o'zgartirdi, kim buyurtma tasdiqladi
- Rate limit: foydalanuvchiga daqiqada N ta xabar

---

## 9. Bosqichlar (Roadmap)

### 0-bosqich — Tayyorgarlik (1 hafta)
- Repo tuzilmasi (`alora-backend`, `alora-agent`, `alora-mobile`), CI, Docker Compose
- Proto shartnomani yakunlash (`alora.proto`)
- Do'kondan real ma'lumot yig'ish: mahsulot ro'yxati, narxlar, hisoblash qoidalari, rasmlar

### 1-bosqich — MVP (3-4 hafta)
- Django: user/rol, mahsulot+variant, narx qoidalari, admin panel, JWT
- Go: shablonni Alora'ga moslash, `product_search` + `curtain_calculate` + `price_quote` tool'lari, gRPC server
- Flutter: login, matnli chat (SSE streaming), mahsulot kartochkasi
- **Natija:** sotuvchi matn orqali AI bilan ishlab, narx chiqara oladi

### 2-bosqich — To'liq sotuv sikli (3 hafta)
- 3 ta variant generatsiyasi, buyurtma qoralamasi va tasdiqlash
- Bilimlar bazasi (`KnowledgeRule`) va tavsiya sifatini oshirish
- Mobil boshqaruv paneli (manager): mahsulot/narx CRUD, xodimlar, token/xarajat statistikasi, limitlar, suhbatlarni ko'rish
- Katalog sinxronizatsiyasi (`Catalog.Watch`)

### 3-bosqich — Ovoz (2-3 hafta)
- STT/TTS integratsiyasi, WebSocket ovoz kanali
- Flutter ovoz UI, barge-in, push-to-talk

### 4-bosqich — Sayqal (davomiy)
- Mijoz rejimi, PDF taklif (kommercheskoye predlojeniye), Telegram'ga yuborish
- Oflayn rejim (katalog keshi), analitika, A/B prompt testlari
- Rasm bo'yicha tavsiya (mijoz xona rasmini yuboradi → AI rang/uslub taklif qiladi)

---

## 10. Qabul mezonlari (Definition of Done)

1. Sotuvchi 5 daqiqada mijozga to'liq 3 variantli taklif chiqara oladi
2. AI hech qachon bazada yo'q mahsulot yoki narxni aytmaydi (100 ta test suhbatida 0 ta hallucination)
3. Hisob natijasi qo'lda hisoblangan natija bilan mos (20 ta etalon misolda ±0 farq)
4. Birinchi belgi (first token) 2 soniyadan tez chiqadi
5. Ovozli javob 3 soniya ichida eshitila boshlaydi
6. Manager har bir xodimning token sarfini real vaqtda ko'radi
7. Ilova internet uzilganda ham oxirgi suhbat va katalogni ko'rsatadi

---

## 11. Risklar

| Risk | Ta'sir | Yechim |
|---|---|---|
| DeepSeek o'zbek tilida zaif tavsiya beradi | Yuqori | Provider config bilan almashadi; 50 ta etalon suhbatda A/B test; kerak bo'lsa Claude'ga o'tish |
| Hisob qoidalari murakkab va o'zgaruvchan | Yuqori | Formulalar admin'da sozlanadi; har o'zgarish uchun test-keys |
| Katalog Go cache'i eskiradi | O'rta | `Catalog.Watch` + snapshot yoshi nazorati + alert |
| LLM xarajati kutilganidan ko'p | O'rta | Prompt caching, `max_history` cheklovi, xodim limitlari |
| O'zbek TTS ovozi sun'iy eshitiladi | O'rta | Bir nechta provider sinovi; matn rejimi doim zaxira |
| Django ASGI'da SSE proxy muammosi | O'rta | Yuklama testi; kerak bo'lsa Nginx darajasida Go'ga to'g'ridan-to'g'ri yo'naltirish (auth subrequest bilan) |

---

## 12. Aniqlangan qarorlar va qolgan savollar

Buyurtmachi javob bergan qarorlar (2026-08-31):

| # | Savol | Qaror |
|---|---|---|
| 1 | Hisoblash uslubi | Tayyor parda sotilmaydi; mato narxi **m² bo'yicha**; bitta pardada **1–10 ta mato**; ustiga **bezak va furnitura** (gul, podxvat, kisti, bahroma) dona/metr bilan → kompozitsion hisob (4-bo'lim) |
| 2 | Buyurtma qayerga ketadi | Tizim ichidagi **`Order` modeliga** tushadi, statuslar bilan boshqariladi |
| 3 | Ombor qoldig'i | v1 da **yo'q** |
| 4 | Filiallar | v1 da **yo'q** (bitta do'kon; `tenant_id` sxemada qoladi, lekin ishlatilmaydi) |
| 5 | Chegirma | Foizni **manager kiritadi**; summaga qarab o'sadigan bosqichli chegirma ham manager qo'lida |
| 6 | Xodimlar soni | ~5 tadan **20–50 tagacha** — tizim shu miqyosga moslab loyihalanadi |
| 7 | Avans va yetkazib berish | **Manager kiritadi**, kiritmasa default qiymat ishlaydi |
| 8 | Limit | Manager limitni **har bir xodimga alohida** qo'yadi; xohlagan xodimga **cheksiz** qilib belgilashi mumkin |

**Miqyos talabi (6-javobdan kelib chiqib):** 50 xodim × kuniga ~30 suhbat = oyiga ~45 000 suhbat.
Shunga qarab: barcha ro'yxatlar cursor-pagination bilan, `UsageRecord` kunlik rollup jadvaliga
yig'iladi (statistika xom jadvaldan hisoblanmaydi), suhbat tarixi arxivlanadi, gRPC ulanishlari pool'da.

### Hali aniqlanmagan (hisoblash uslubini o'rgatganingizda hal bo'ladi)
1. **Yuza qanday olinadi:** `B × Hp` (toza kerakli yuza) bo'yichami, yoki rulondan kesilgan
   haqiqiy yuza (chiqindi bilan) bo'yichami? — hozircha toza yuza olindi, chiqindi ogohlantirish sifatida.
2. **Ko'p matoli fasonda bo'lak o'lchamlari** qanday aniqlanadi: har bo'lakka alohida o'lchov
   beriladimi, yoki fason shabloni foiz ulush bilan bo'ladimi (masalan kant = balandlikning 15%)?
3. **Tikuv narxi** nima bo'yicha: `L × K` (tayyor parda uzunligi) yoki `S_total` (yuza) yoki bo'lak soni bo'yicha?
4. **Bezaklarning miqdori** odatda qanday belgilanadi — sotuvchi qo'lda kiritadimi, yoki fasonga
   biriktirilgan standart to'plam bormi (masalan "bu fasonda doim 2 ta gul va 2 ta podxvat")?
