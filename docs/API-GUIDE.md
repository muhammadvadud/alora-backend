# Alora Backend API Qo'llanmasi

Ushbu hujjat mobil ilova va boshqa mijozlar uchun Alora backend API bilan ishlash bo'yicha qo'llanma hisoblanadi.

Backend faqat mobil klient uchun; CORS ataylab sozlanmagan. Web klient qo'shilsa django-cors-headers o'rnatilib MIDDLEWARE ga CommonMiddleware'dan oldin ulanishi kerak.

## 1. Autentifikatsiya

Tizimda **JWT (JSON Web Token)** asosida autentifikatsiya qilinadi.
- **Access token**: 15 daqiqa amal qiladi.
- **Refresh token**: 30 kun amal qiladi.
- Tizim rotation (aylanish) va blacklist (qora ro'yxat) mexanizmlarini qo'llab-quvvatlaydi. Ya'ni, tizimdan chiqqanda (`logout`) refresh token qora ro'yxatga tushadi.

So'rov yuborishda header'da tokenni ko'rsatish kerak:
`Authorization: Bearer <access_token>`

## 2. Rollar va Ruxsatlar Matritsasi

Tizimda 3 ta asosiy rol bor iyerarxiya bo'yicha: `employee` < `manager` < `admin`.

| Guruh | employee | manager | admin |
|---|---|---|---|
| Chat, katalog o'qish | ✅ | ✅ | ✅ |
| Buyurtma yaratish | ✅ | ✅ | ✅ |
| Katalog yozish, narx | ❌ | ✅ | ✅ |
| Xodimlar, limit, usage | ❌ | ✅ | ✅ |
| Calc-rules, knowledge | ❌ | ✅ | ✅ |
| System prompt, ModelPricing, tannarx | ❌ | ❌ | ✅ |

Qo'shimcha qoidalar:
- `employee` faqat **o'z** suhbati va **o'z** buyurtmalarini ko'radi.
- `manager` butun tenant'ni (o'z do'konini) ko'ra oladi.

## 3. Barcha Endpointlar Ro'yxati

Asosiy prefiks: `/api/v1/`

### Autentifikatsiya (`/api/v1/auth/`)
- `POST /api/v1/auth/login/` - Tizimga kirish va tokenlar olish
- `POST /api/v1/auth/refresh/` - Refresh token orqali yangi access token olish
- `POST /api/v1/auth/logout/` - Tizimdan chiqish (tokenni qora ro'yxatga kiritish)
- `GET /api/v1/auth/me/` - O'z ma'lumotlarini olish

### Jamoa (`/api/v1/team/`)
- `GET, POST /api/v1/team/employees/` - Xodimlar ro'yxati va yangi xodim qo'shish
- `GET, PATCH, DELETE /api/v1/team/employees/{id}/` - Xodim ma'lumotlarini olish, o'zgartirish, o'chirish

### Katalog (`/api/v1/catalog/`)
- `GET, POST /api/v1/catalog/categories/` - Kategoriyalar
- `GET, PATCH, DELETE /api/v1/catalog/categories/{id}/` - Kategoriya boshqaruvi
- `GET, POST /api/v1/catalog/products/` - Mahsulotlar
- `GET, PATCH, DELETE /api/v1/catalog/products/{id}/` - Mahsulot boshqaruvi
- `GET, POST /api/v1/catalog/variants/` - Mahsulot variantlari
- `GET, PATCH, DELETE /api/v1/catalog/variants/{id}/` - Variant boshqaruvi
- `GET, POST /api/v1/catalog/images/` - Rasmlar
- `GET, PATCH, DELETE /api/v1/catalog/images/{id}/` - Rasm boshqaruvi
- `GET, POST /api/v1/catalog/fasons/` - Fasonlar
- `GET, PATCH, DELETE /api/v1/catalog/fasons/{id}/` - Fason boshqaruvi
- `POST /api/v1/catalog/import/` - Katalogni import qilish

Import `multipart/form-data` orqali `.csv` yoki `.xlsx` fayl qabul qiladi. Ustunlar:
`product_code`, `product_name`, `category_slug`, `style`, `pattern`, `segment`,
`recommended_rooms`, `variant_sku`, `color_name`, `price`, `price_unit`, `width_m`,
`is_active`. `dry_run=true` yozuvlarni saqlamasdan tekshiradi; fayl 5 MB va 5000 qatordan
oshmasligi kerak.

### Buyurtmalar (`/api/v1/orders/`)
- `GET, POST /api/v1/orders/` - Buyurtmalar ro'yxati va yaratish
- `GET, PATCH, DELETE /api/v1/orders/{id}/` - Buyurtma boshqaruvi
- `POST /api/v1/orders/{id}/confirm/` - Buyurtmani tasdiqlash
- `POST /api/v1/orders/{id}/status/` - Buyurtma holatini o'zgartirish
- `GET /api/v1/orders/{id}/statuses/` - Holatlar tarixi
- `GET /api/v1/orders/{id}/pdf/` - Kommercheskiy taklifni PDF formatida yuklab olish

### Hisob-kitob va Narxlar (`/api/v1/`)
- `GET, PATCH /api/v1/calc-rules/` - Hisoblash qoidalari
- `GET, PATCH /api/v1/services/` - Xizmat narxlari
- `GET, PATCH /api/v1/discount-policy/` - Chegirma siyosati
- `GET, PATCH /api/v1/order-defaults/` - Buyurtma standartlari
- `GET, POST /api/v1/discount-tiers/` - Chegirma bosqichlari
- `GET, PATCH, DELETE /api/v1/discount-tiers/{id}/` - Chegirma bosqichlari boshqaruvi
- `GET, POST /api/v1/model-pricings/` - Model narxlari
- `GET, PATCH, DELETE /api/v1/model-pricings/{id}/` - Model narxlari boshqaruvi
- `POST /api/v1/calc/preview/` - Buyurtma narxini oldindan hisoblash (kalkulyator)

### Suhbat / Chat (`/api/v1/`)
- `GET, POST /api/v1/conversations/` - Suhbatlar ro'yxati va yangi suhbat yaratish
- `GET, DELETE /api/v1/conversations/{id}/` - Suhbat haqida ma'lumot olish yoki o'chirish
- `POST /api/v1/conversations/{id}/reset/` - Suhbat kontekstini tozalash
- `GET /api/v1/conversations/{id}/transcript/` - Suhbatning to'liq transcriptini olish
- `GET /api/v1/conversations/{id}/messages/` - Suhbat xabarlarini olish (ro'yxat, GET)
- `POST /api/v1/conversations/{id}/messages/` - Suhbatga yangi xabar yuborish (SSE Stream orqali javob qaytadi)

### Bilimlar bazasi (`/api/v1/knowledge/`)
- `GET, POST /api/v1/knowledge/rules/` - Bilimlar bazasi qoidalari ro'yxati va yaratish
- `GET, PATCH, DELETE /api/v1/knowledge/rules/{id}/` - Bilimlar qoidasi boshqaruvi

### Sozlamalar (`/api/v1/settings/`)
- `GET, POST /api/v1/settings/prompt/` - System prompt versiyalari ro'yxati va yaratish
- `GET, PATCH, DELETE /api/v1/settings/prompt/{id}/` - System prompt boshqaruvi
- `POST /api/v1/settings/prompt/{id}/rollback/` - Oldingi prompt versiyasiga qaytarish

### Tahliliy Ma'lumotlar (`/api/v1/`)
- `GET, POST /api/v1/usage/` - Ishlatilgan resurslar ro'yxati
- `GET /api/v1/usage/{id}/` - Ishlatish ma'lumoti detali
- `GET, POST /api/v1/analytics/` - Analitika ma'lumotlari
- `GET /api/v1/analytics/{id}/` - Analitika detali

## 4. Cursor Pagination Formati

Tizimda barcha ro'yxatlar **Cursor Pagination** (`StandardCursorPagination`) yordamida sahifalanadi. 
Bu an'anaviy sahifalash (page/limit) emas, balki elementning cursor qiymatiga asoslanadi.

- Odatiy elementlar soni: 20 ta
- Maksimal elementlar soni: 100 ta
- Sahifalash tartibi: `-created_at` (eng yangilari oldin)
- Qidiruv (masalan `?search=xyz`) va URL param orqali `page_size` uzatish mumkin.

**Javob formati:**
```json
{
  "next": "http://api.alora.uz/api/v1/products/?cursor=cj0xJnA9MjAyNi...",
  "previous": null,
  "results": [
    {
       "id": "uuid",
       ...
    }
  ]
}
```

## 5. Yagona Xato Formati va Kodlari

Loyiha bo'ylab barcha xatolar DRF Exception Handler orqali yagona formatga keltiriladi.
Xatolar 3 qismdan iborat bo'ladi:
- `detail`: Odam o'qishi uchun tushunarli o'zbekcha matn.
- `code`: Xatolikning mashina o'qishi uchun formati (enum/string).
- `errors`: Serializer validatsiya xatolari yuz berganda qaysi maydonda qanday xatolik bo'lgani haqida tafsilotlar.

**Namunaviy xato:**
```json
{
  "detail": "Ma'lumotlar noto'g'ri",
  "code": "validation_error",
  "errors": {
    "price": "0 dan katta bo'lishi kerak",
    "variants.0.color_name": "Rang kiritilishi shart"
  }
}
```

**Asosiy xato kodlari (code):**
| Xato turi | Code | Detail matni (namuna) |
|---|---|---|
| Validatsiya | `validation_error` | "Ma'lumotlar noto'g'ri" |
| Autentifikatsiya yo'q | `not_authenticated` | "Tizimga kirish talab qilinadi" |
| Parol/Login xato | `authentication_failed` | "Kirish ma'lumotlari noto'g'ri" |
| Ruxsat yo'q | `permission_denied` | "Bu amal uchun ruxsat yo'q" |
| Topilmadi (404) | `not_found` | "Topilmadi" |
| Noto'g'ri metod | `method_not_allowed` | "Bu usul qo'llab-quvvatlanmaydi" |
| Noto'g'ri JSON | `parse_error` | "So'rov formati noto'g'ri" |
| Limit tugadi | `throttled` | "So'rovlar soni cheklangan" |
| Boshqa / Server xatosi | `error` | "Kutilmagan xatolik yuz berdi" |

## 6. Chat SSE Oqim Formati (Server-Sent Events)

Yangi xabar yuborish `POST /api/v1/conversations/{id}/messages/` orqali JSON yuborilgach, server **SSE oqimi** qaytaradi (`content_type="text/event-stream"`). Ilova ushbu oqimni tinglashi kerak.

Har bir voqea qatori gRPC xabarining JSON formatiga aylantirilgan shaklidir. 

**Voqea turlari (kind):**
- `start` - AI javobni boshladi.
- `thinking` - AI o'ylashni / qadamlarni boshladi.
- `content` - Matn ko'rinishida tokenlar kelyapti (`content` maydonida).
- `tool_call` - AI qandaydir asbobni ishlatmoqchi (`tool` maydonida asbob nomi).
- `tool_args` - Asbobning argumentlari kelyapti (`args` maydoni).
- `tool_result` - Asbob o'z ishini tugatib natija berdi (`result` maydoni).
- `done` - Javob berish tugatildi, hamma tokenlar tugadi. Bu hodisada qo'shimcha mahsulot tavsiyalari (`products`) va token xarajatlari (`usage`) kelishi mumkin.
- `error` - Bajarish vaqtida xatolik yuz berdi (`detail` yoki `error` maydonida).

**Oqim (stream) dagi `data:` freym formati:**
```text
data: {"kind": "start"}

data: {"kind": "content", "content": "Salom! "}

data: {"kind": "content", "content": "Sizga qanday yordam bera olaman?"}

data: {"kind": "tool_call", "tool": "search_catalog"}

data: {"kind": "done", "usage": {"prompt_tokens": 12, "completion_tokens": 5, ...}, "products": [...]}
```

Agar serverda xatolik kuzatilsa, masalan AI xizmati ishlamayotgan bo'lsa:
```text
data: {"kind": "error", "detail": "AI xizmati vaqtincha ishlamayapti"}
```
Xabarning oqimi `done` yoki `error` qabul qilingach avtomatik tugaydi. Mijoz tomon xuddi shu oqimni tugatishi yoki uzib qo'yishi mumkin, bu holda backend ham jarayonni bekor qiladi.
