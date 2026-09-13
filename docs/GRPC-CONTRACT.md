# gRPC Shartnoma — Go bilan umumiy qilish tartibi

## Yagona manba

gRPC shartnoma **faqat bitta faylda** saqlanadi:

```
protos/alora.proto
```

Ikkinchi nusxa (Go repo yoki boshqa joyda) **taqiqlanadi**. Shartnoma o'zgarganda
ikki taraf ham qayta generatsiya qiladi.

---

## Proto'ni Go repo bilan qanday umumiy qilish

### Usul: CI ko'chirish (tavsiya etiladi)

1. Django repo'da `protos/alora.proto` — yagona manba.
2. CI pipeline (GitHub Actions) `protos/alora.proto` faylini Go repo'ga ko'chiradi.
3. Go repo'da `make generate` yoki `buf generate` avtomatik ishlaydi.
4. Django'da `scripts/gen_proto.sh` ishlatiladi.

```
┌──────────────┐     CI push      ┌──────────────┐
│  Django repo  │ ──────────────→ │   Go repo     │
│  protos/      │                 │  proto/       │
│  alora.proto  │                 │  alora.proto  │
└──────────────┘                  └──────────────┘
       │                                 │
       ▼ gen_proto.sh                    ▼ buf generate / protoc
  grpc_gen/                          gen/
  _pb2.py, _pb2_grpc.py             *.go
```

### Muqobil: Git submodule

Agar repolar bir GitHub org'da bo'lsa, Go repo'da Django repo'ni
submodule sifatida qo'shish mumkin. Lekin bu murakkabroq — CI ko'chirish
oddiy va ishonchliroq.

---

## Shartnoma o'zgarganda ikkala taraf nima qilishi

### 1. O'zgarish kiritish

1. `protos/alora.proto` faylini tahrirlash.
2. Yangi maydonlar yoki xizmatlar qo'shish.
3. **Eski maydonlar o'chirilmaydi** (backward compatibility).

### 2. Django tarafida

```bash
# Proto'dan Python kodini qayta generatsiya qilish
bash scripts/gen_proto.sh

# Testlarni ishga tushirish
pytest tests/chat/ -q
```

### 3. Go tarafida

```bash
# Proto'dan Go kodini qayta generatsiya qilish
buf generate   # yoki protoc ishlatiladi

# Testlarni ishga tushirish
go test ./...
```

### 4. Tekshirish

1. Ikkala tarafda testlar o'tishi shart.
2. CamelCase/snake_case mosligini tekshirish (proto'da hammasi snake_case).
3. Backward compatibility: eski klientlar yangi server bilan ishlay olishi kerak.

---

## Versiyalash tartibi

### Proto versiyasi

- `package alora.v1;` — hozirgi versiya.
- Katta o'zgarishlar (breaking change) bo'lsa `v2` ga o'tiladi.
- Minor o'zgarishlar (yangi maydon, yangi method) v1 ichida qilinadi.

### Versiya raqami (catalog sync)

- `CatalogSnapshot.version` — monoton o'sadigan raqam (Redis `INCR`).
- Go `Watch` stream'dan qachon uzilsa, qayta ulanganda `from_version` beriladi.
- `from_version` joriy versiyadan kichik bo'lsa Django `FULL_RESYNC` delta'sini yuborib
  stream'ni yopadi — Go to'liq `Snapshot` oladi va Watch'ni qayta ochadi
  (protokol: `GO-CONTRACT.md` §1.2). Oraliq delta'lar Redis'da saqlanmaydi.
- Kontrakt semantikasi (context kalitlari, kind'lar, payload tarkibi) versiyalanadi:
  `GO-CONTRACT.md` §4 jurnali (hozir 1.1).

---

## Backward compatibility qoidalari

1. **Maydon raqamlari o'zgarmaydi** — yangi maydon qo'shilganda eski raqamdan davom etiladi.
2. **Eski maydonlar o'chirilmaydi** — `deprecated` deb belgilanadi.
3. **Yangi method qo'shilishi mumkin** — eski metodlar saqlanadi.
4. **Enum qiymatlari qo'shiladi** — eski qiymatlar o'chirilmaydi.
5. **Message tuzilmasi kengaytiriladi** — eski klientlar yangi maydonlarni e'tiborsiz qoldiradi.

---

## Generatsiya qilish

### Django (Python)

```bash
# grpcio-tools talab qilinadi (pyproject.toml da bor)
bash scripts/gen_proto.sh
```

### Go

```bash
# buf (https://buf.build) yoki protoc + Go pluginlari
buf generate
```

---

## Test etalonlari

`tests/fixtures/calc_cases.json` fayli ham Go repo bilan **umumiy**.
Ikkala taraf shu fayldagi misollar bo'yicha bir xil natija berishi shart.
Fayl o'zgarsa Go jamoasiga xabar qilinadi.
