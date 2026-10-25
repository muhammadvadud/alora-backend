# Yakuniy natija

2026-10-25, Asia/Tashkent. Matnli parda sotuv yordamchisi bilim/prompt/tool dalillari orqali yaxshilandi. Sinov doirasidagi ekspert bahosi **91/100**. Model vaznlari fine-tuning qilinmadi. Narx formulalari va mobil kod o'zgarmadi.

## Nima joriy qilindi

| Narsa | Natija |
|---|---|
| Bilim | 118 yangi manbali qoida; 55 eski umumlashtirish nofaol; jami 175 yozuv, 119 faol |
| Mahsulot | 14 mavjud kod, ikki katalogda 28 yozuv tavsifi/xonasi/o'zbek-rus atamalari boyitildi; narx/variant/tarkib/care saqlandi |
| Fason | 10 yangi shablon ikki katalogga: jami 20 qo'shildi, faol soni 6 dan 26 ga chiqdi |
| Prompt | DB prompt v3, 5693 belgi; texnik fallback 3418 dan 1830 belgiga qisqardi |
| Token | Inline ko'pi bilan 8 qoida/2000 belgi; lookup ko'pi bilan 6 qoida |
| Sotuv oqimi | Tanlov snapshoti, persistent tanlangan paket, order bosqichi, takrorsiz xizmatlar |
| Dalil | Mahsulot care/tarkibi, paket rangi/shaffofligi va budjet taqqoslashi tool'da aniq ko'rinadi |

Mazmun O'zbekiston sharoitiga mos: tul/portyera/blekaut/xay-tek, kelin-kuyov xonasi, mahalliy o'lchov birliklari, so'm, mavjud rels/tul, quyosh va chang, sodda/neoklassik/minimal fasonlar. Mahalliy sahifalardagi tasdiqlanmagan variant narxlari Alora narxi sifatida ko'chirilmadi; yangi narxli SKU to'qilmadi.

## Tekshiruv

24 jonli API navbati, 12 guruh, 24 done/0 error; asosiy fokus mijozda. Yakuniy holatning bahosi va tuzatilgan dastlabki xatolar [EVALUATION.md](EVALUATION.md) va [to'liq transkript](EVALUATION-TRANSCRIPT.md)da. Pullik sinovlar tayyorlashdan keyin o'tkazildi; topilgan xatolargagina qayta sinov qilindi. Sinovning 12 suhbatini keyin arxivladim, o'chirmadim. Vaqtinchalik test bazasi va alohida test Redis olib tashlandi; asosiy xizmatlar ishlamoqda.

Hisobiy DeepSeek xarajati **$0.024940098**, rejalangan $0.028 dan kam. 30/30 korpus retrieval savoli; backend 466 test, 86% coverage; Go build/vet/lint/race, golden va e2e toza. Yangi Python modullari scoped ruff/format/mypy dan o'tdi. Butun backenddagi 5 lint, 8 format fayli va 10 fayldagi 33 type muammosi oldingi kodga tegishli; yangi bilim modullari bilan aralashtirilmadi. O'sha fayllar `main`dan o'zgarmagani tekshirildi.

## Git

Backend va agent branchi: **feat/25-sales-training**. Har tugallangan mantiqiy bosqich commit qilinib origin'ga push qilindi; keyingi pushlardan oldin pull --rebase bajarildi. `main`ga merge yoki push qilinmadi.

- [Backend branch](https://github.com/muhammadvadud/alora-backend/tree/feat/25-sales-training)
- [Agent branch](https://github.com/muhammadvadud/alora-ai/tree/feat/25-sales-training)

Agentning ish boshlanishidan avvalgi 37 tracked fayl va mavjud yangi testlardagi o'zgarishlari `4cb1250` baseline commitida alohida saqlandi. Yangi ish bilan chalkashtirilmadi. Mobilning avvalgi o'zgarishlari va backend `static/` papkasi tegilmagan. Muhit yuritadigan `.forge/.context-monitor-state.json` Git'ga olinmadi.

## Backup va qaytarish

Maxfiy katalog: `/home/muhammadvadud/it/alora/backups/sales-training-20261025/` (0700).

- `alora-before-training.dump`: o'zgarishlardan AVVAL olindi, alohida bazaga tiklab tekshirildi; SHA256SUMS mavjud.
- `sales-pack-before-apply.json`: bilim/mahsulot/fason/promptning birinchi muvaffaqiyatli importdan avvalgi snapshoti.
- `sales-pack-before-refinement.json`, `sales-pack-before-v3.json`: keyingi prompt bosqichlari oldidagi snapshotlar.
- `alora-after-training.dump`: yangi holatning qo'shimcha backupi; katalog ro'yxati pg_restore bilan o'qildi.
- `trained-evaluation.jsonl`: raw API dalili. Balans fayllari, oldingi knowledge/katalog va foydalanuvchining avvalgi patchlari ham maxfiy katalogda.

Bilim/katalogni birinchi holatga qaytarish uchun snapshotni konteynerga nusxalab, `python manage.py train_sales --rollback /maxfiy-yo‘l/sales-pack-before-apply.json` ishlatiladi. Buyruq faol admin muallifini tanlaydi, eski yozuvlarni tiklaydi, yangi bilim/fasonlarni nofaol qiladi; hech narsani majburan o'chirmaydi. Bu ma'lumot rollbacki, Git kodini qaytarmaydi. Yangi suhbat bilan qayta tekshirish kerak; eski sessiyalardagi tanlov snapshotlari tarixiy hisob bo'lib qoladi. To'liq DB dump restore'i keyingi ma'lumotlarni ham almashtirgani uchun avtomatik bajarilmadi.

## Keyingi sifat ishlari

Rang va didni avtomatik paketda yanada yaxshi uyg'unlashtirish, javobni qisqartirish, ortiqcha savol/taklifni kamaytirish va yetkazish kiritilmaganligini aniqroq ifodalash qoladi. Yetkazib beruvchidan haqiqiy tarkib/parvarish ma'lumotlari olinsa katalog boyitilishi mumkin. Alohida texnik audit kamchiliklari ushbu sotuv bahosi bilan yopilmadi.

Manbalar: [SOURCES.md](SOURCES.md). Bilim paketi: [KNOWLEDGE.md](KNOWLEDGE.md). Zarur texnik o'zgarishlar: [TECHNICAL-CHANGES.md](TECHNICAL-CHANGES.md).
