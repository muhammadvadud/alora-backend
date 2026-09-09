# Alora Backend — Go bilan Kelishuv (GO-CONTRACT)

Ushbu hujjat Django backend va Go mikroservisi o'rtasidagi kelishuv (shartnoma) va o'zaro hamkorlik protokollarini belgilaydi. Yagona manba `protos/alora.proto` hisoblanadi.

## 1. Servislar va RPC'lar ro'yxati (gRPC)

Barcha gRPC muloqoti `alora.v1` paketi orqali amalga oshadi.

### Agent Servisi (Django → Go)
Ovoz va matn chatini ta'minlash uchun.
- `rpc Chat(ChatRequest) returns (stream ChatEvent)`: Matnli suhbat uchun. Server-streaming orqali Go har bir voqeani (event) alohida yuboradi.
- `rpc VoiceChat(stream VoiceChunk) returns (stream VoiceEvent)`: Ovozli suhbat. Ikki tomonlama streaming (birectional) qilinadi.
- `rpc ResetSession(ResetRequest) returns (ResetResponse)`: Sessiya kontekstini xotiradan o'chirish va tozalash uchun.
- `rpc Health(Empty) returns (HealthResponse)`: Go agentning yashayotganligini va sog'lig'ini tekshirish uchun ishlatiladi.

### Catalog Servisi (Django → Go)
Katalogni sinxronizatsiya qilish uchun.
- `rpc Snapshot(SnapshotRequest) returns (CatalogSnapshot)`: Katalogning to'liq nusxasini (sahifalab) olish. Go agenti ishga tushganda yoki Redis bilan aloqa uzilib qolib, versiyalar nomuvofiqligi sezilsa chaqiradi.
- `rpc Watch(WatchRequest) returns (stream CatalogDelta)`: Real-vaqtda o'zgarishlar oqimini (delta stream) olish. Go backend buni uzluksiz ochib qo'yadi, Django uni Redis kanalidagi ma'lumotlar bilan ta'minlab turadi.

### Backend Servisi (Go → Django)
Go tomonidan Django'ga asinxron ravishda saqlash yoki jurnalga yozish so'rovlari.
- `rpc ReportUsage(UsageRequest) returns (Ack)`: AI tokenlari sarflangandan keyin va xarajatlar to'g'risida hisobot.
- `rpc SaveOrderDraft(OrderDraftRequest) returns (OrderDraftResponse)`: AI suhbat doirasida yaratgan buyurtma qoralamasini saqlash.
- `rpc LogMessage(MessageLogRequest) returns (Ack)`: Suhbat tarixini saqlab borish uchun xabar jurnalini yozib qo'yish.

## 2. Katalog Sinxronizatsiyasi: Redis kanallari va versiya kaliti

Katalog manbasi (source of truth) - faqat Django. Go agent doimo o'zida nusxani ushlab turadi (cache).
- Barcha `post_save` va `post_delete` signallarida Django Redis pub/sub kanaliga delta (`{tenant_id, entity, entity_id, action, version, payload_json}`) yuboradi.
- **Pub/Sub kanal nomi**: `alora:catalog:deltas`
- **Versiya kaliti**: `alora:catalog:version` (ushbu kalit INCR orqali monoton o'sib boradi)

**Watch jarayoni:**
Go agent ma'lum bir `from_version` (oxirgi olgan versiyasi) orqali `Watch` metodini chaqiradi. Agar `from_version` hozirgi Django versiyasidan kichik bo'lsa va deltalarni bittalab berib bo'lmasa, Django `FULL_RESYNC` amali orqali Go agentdan `Snapshot` qilishni so'raydi. Aks holda u oqimda yangi deltalarni yuborishda davom etadi.

## 3. Etalon Test Kelishuvi

Hisob-kitob (calc) qoidalari ikkala tomonda xatosiz, bir xil bo'lishini ta'minlash uchun **etalon testlar fayli** tuzilgan.

**Fayl yo'li**: `tests/fixtures/calc_cases.json`
Ushbu fayl Django repozitoriyasida ham, Go repozitoriyasida ham **mutlaqo bir xil (umumiy)** hisoblanadi. Ikkala tomon o'z testlarini shu JSON fayl asosida ishga tushiradi (Django'da `tests/pricing/test_reference_cases.py`). 
Agar formulada o'zgarish bo'lsa, etalon fayl birgalikda o'zgartiriladi. Hozirda loyihada etalon holatlar (20 ta misol) mavjud. Barcha holatlar muvaffaqiyatli o'tishi majburiydir.

## 4. Proto Faylini Boshqarish va Generatsiya

`protos/alora.proto` fayli ushbu Django repozitoriyasida yagona manba (source of truth) hisoblanadi. Agar proto fayliga o'zgartirish kiritish kerak bo'lsa, quyidagi tartibga rioya qilinishi majburiy:

1. **O'zgartirish kiritish**: Barcha o'zgarishlar faqatgina ushbu repozitoriyadagi `protos/alora.proto` fayliga kiritiladi.
2. **Python kodini generatsiya qilish**: Proto fayl o'zgartirilgandan so'ng, darhol Python gRPC stub'larini yangilash uchun `scripts/gen_proto.sh` skripti ishga tushirilishi kerak. Bu `grpc_gen/` papkasini yangilaydi.
3. **Go repozitoriyasiga uzatish**: Go (backend) repozitoriyasiga o'zgartirilgan proto faylni nusxalash uchun `scripts/export_proto.sh <go_repo_yoli>` yordamchi skripti ishlatiladi. Bu skript nusxa ustidan yozishdan oldin ikki fayl o'rtasidagi farqni ko'rsatib beradi.
4. **Go tarafida qayta generatsiya qilish**: Nusxa olingach, Go repozitoriyasi ichida protoc (yoki buf) orqali Go kodlari (`.pb.go` va `_grpc.pb.go`) qayta generatsiya qilinishi kerak (odatda Go loyihasining Makefile'ida belgilangan `make proto` yoki shunga o'xshash buyruq orqali).
5. **Versiyalash qoidasi**: Proto o'zgarishlari oldinga qarab mos keluvchi (backward compatible) bo'lishi qat'iyan talab qilinadi. Mavjud maydonlarning tiplari o'zgartirilmasligi yoki nomlari/indekslari o'chirilmasligi, faqatgina yangi maydonlar qo'shilishi kerak.
