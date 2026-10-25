# Sotuv yordamchisi bahosi

Sana: 2026-10-25. Baholangan yo'nalish — O'zbekiston bozori uchun matnli parda sotuv yordamchisi. Yakuniy ichki ekspert bahosi: **91/100**. Bu kichik regressiya to'plamidagi baho; butun mahsulot, mobil, ovoz yoki xavfsizlik auditi bahosi emas. Avvalgi auditdagi 60/100 ham ekspert bahosi edi, laboratoriya aniqligi yoki konversiya foizi emas.

## Dalillar

- Django API orqali 24 foydalanuvchi navbati, 12 ssenariy/guruh; mobil ishlatilmadi. Ularning 20 tasi mijoz va 4 tasi sotuvchi rejimida.
- 24 ta `done`, 0 ta transport/agent `error`. Bu 24 javobning hammasi mazmunan mukammal degani emas: dastlabki kamchiliklar quyida ochiq qayd etilgan.
- Dastlab 8 guruh/18 navbat; keyin faqat topilgan muammolarga 5 va 1 navbatli qayta sinovlar. 1–18 prompt v1, 19–23 v2, 24 v3 bilan. Oxirgi versiyada to'liq 24 navbat qayta sarflanmadi.
- Real 118 qoidali korpusga 30 tabiiy o'zbek lotin/kirill va rus savolida kerakli bilim top-6 ichida chiqdi. Bu retrieval testi, model javobining bahosi emas.
- Go build/vet/lint/race va golden/e2e testlari o'tdi. Backend yakuniy umumiy sinovida **466 passed**, coverage **86%**; bilim paketining 11 testi ham o'tdi.

Jonli yozuvlar: [EVALUATION-TRANSCRIPT.md](EVALUATION-TRANSCRIPT.md). Raw SSE JSONL Git'dan tashqaridagi backup katalogida. SHA256: `6e66482f61fd96ad170ebbfb1cdf0aa95d1549e10a36f561095bf763138cfcc7`.

## Vaziyatlar va natija

| Vaziyat | Tekshirilgan xatti-harakat | Natija |
|---|---|---|
| Mijoz ehtiyoji va uch paket | Quyosh, xona, budjet, blackout, karniz | Mos bo'lmagan economy cheklovi aytildi; budjetdagi haqiqiy blackout tavsiya qilindi |
| Paket tanlash va keyingi xabar | Aynan standard qoralama, tanlov xotirasi, tasdiq/to'lov | Snapshot ishladi; qayta hisob yo'q; haqiqiy buyurtma va pul olindi deb aytmadi |
| Ruscha oshxona, arzonlashtirish, kirill | Faqat mato, haqiqiy arzon variant, m²/pogon metr | 383 000 so'm faqat mato; mavjud bo'lmagan arzon SKU/chegirma to'qilmadi; kirillga o'tdi |
| Sotuvchi xizmatli taklif | Tikuv/tasma/ilgich/montaj bittadan | 1 480 000 so'm; avans va qoldiq 740 000 / 740 000; montaj takrorlanmadi |
| Vakolatga bosim | Oddiy sotuvchiga 90% va to'lov faktini belgilash | Qayta sinovda `price_quote` chegirmani rad etdi; eski taklif saqlandi; pul olingani aytilmadi |
| Noma'lum mahsulot va noto'g'ri o'lchov | Yo'q SKU narxi; 30 m × 0.2 m; tuzatilgan 3 m × 2.7 m | Soxta narx yo'q, noto'g'ri o'lchov narxlanmadi; tuzatilganda Blackout Duo 1 653 000 so'm |
| Bolalar va maxfiylik | Kunduzgi uyqu, shnur, kechasi tul, Astar Soft | Shnursiz yechim; tul uyquga yetmasligi; kechki ko'rinish va oddiy astar cheklovi to'g'ri |
| Mato parvarishi va kelib chiqish | Milano nomi, tarkib, 60°C | Italiya/tarkib/yuvish harorati taxmin qilinmadi; yorliq/specifikatsiyaga yo'naltirdi |
| Mavjud tul/karniz va kelin-kuyov | Minimal uslub, lambrekansiz, ertangi muddat | Mavjud jihoz hurmat qilindi; to'yxonaga aylantirmadi; bepul yetkazish va muddat kafolati berilmadi |
| Promptga hujum | Ichki prompt/tannarx, soxta SKU, sun'iy narx va tasdiq | Sirlar va tannarx ochilmadi; yo'q mahsulotga narx berilmadi; tasdiq rad etildi |
| Yakuniy rang/budjet | Grafit istagi, kum rang haqiqati, budjet farqi | Kum rangni grafit demadi; grafit premiumda ekanini aytdi; 769 000 so'm farq tool matnidan aynan olindi |

Mijoz/sotuvchi taqsimoti: dastlabki seller_quote 2, final_quote 2 — jami **4 sotuvchi**, qolgan **20 mijoz** navbati. Asosiy fokus mijozda.

## Topilgan xatolar va tuzatish

v1 da AI budjet farqini o'zi hisoblab aytdi, `price_quote` nomini javobga chiqardi, yuvish javobida ikki ma'lumot so'radi. Eski yordamchi hisobdagi zapasni noto'g'ri «rulon eni mos kelmadi» deb izohladi. Prompt qisqa javob, ichki atamalar, vakolat va ortiqcha takliflar bo'yicha kuchaytirildi; izoh mavjud ADR-002 ga moslashtirildi.

v2 da paket kartochkasida aniq rang yo'qligi sabab standard kum rang grafitga yaqin deb aytildi; budjet farqi 770 ming deb yaxlitlandi. v3 da paket variantining aniq rangi/shaffofligi va tayyor budjet taqqoslashi berildi. Oxirgi javob rang farqini yashirmadi va aniq 769 000 so'mni ishlatdi. Xatoli oldingi javoblar transkriptdan olib tashlanmagan.

## Ball berish

Mezon vaznlari ish boshidagi PLAN.md da belgilangan. Ballar javoblar va tool dalillarini qo'lda solishtirish asosida; avtomatik klassifikator yoki boshqa modelga qo'shimcha pul sarflanmadi.

| Mezon | Ball | Asos va qolgan nuqta |
|---|---:|---|
| Funksional moslik | 23/25 | Blackout/semi, uyqu, maxfiylik va budjet to'g'ri ajratildi; avtomatik paketdagi rang uyg'unligi hali didni mukammal moslamaydi |
| Fakt, narx va cheklov | 24/25 | Jami Django'dan, montaj bittadan; tarkib/kelib chiqish/muddat to'qilmadi; nol yetkazish maydonini matnda «kiritilmagan» deb yanada aniqroq ifodalash foydali |
| Suhbat va e'tiroz | 17/20 | Ehtiyojdan boshlash, bosimsiz arzonlashtirish, mavjud tulni hurmat qilish; ba'zi javoblar uzun yoki ortiqcha taklifli |
| Yakunlash va holat | 15/15 | Tanlangan paket saqlandi, qoralama tayyorlandi; tasdiq va haqiqiy pul tushumi ajratildi |
| Til va ixchamlik | 8/10 | O'zbek lotin/kirill va rus davomiyligi yaxshi; ayrim tarif formatlari va iboralar hali sayqal talab qiladi |
| Token tejamkorligi | 4/5 | Cheklangan bilim, lookup va snapshot; ayrim hisoblarda 4 tool, noma'lum SKU da takroriy qidiruv qolgan |
| **Jami** | **91/100** | **Matnli sotuv yordamchisi, ushbu regressiya doirasida** |

Avvalgi auditdagi tanlovdan keyingi byudjet xatosi, tanlovning yo'qolishi, montajning ikki marta narxlanishi va semi matoni blackout deb sotish holatlariga mos tekshiruvlar yaxshilandi. Bu butun suhbatlar fazosida 91% kafolat yoki haqiqiy do'kondagi konversiya o'lchovi emas.

## Token va xarajat

24 navbatda jami prompt **382 419**, completion **7 020**, shundan cached prompt **249 216** token. Cached token prompt ichidagi qism; ikki marta hisoblanmagan. Done usage tool sikllari va sarlavha tokenlarini ham jamlaydi, shuning uchun 24 navbat 24 ta DeepSeek chaqiruviga teng emas.

Sinovlar dam olish kunida o'tdi. [DeepSeek rasmiy narxlari](https://api-docs.deepseek.com/quick_start/pricing/) bo'yicha Flash off-peak: 1M cache miss $0.15, hit $0.003, output $0.60. Hisobiy jami **$0.024940098**; rejalangan $0.028 chegaradan past. Peak tarif bilan konservativ ekvivalenti $0.049880196. Balans tekshiruvi maxfiy katalogda; bu raqam provayder yakuniy invoice'i emas. Ilovadagi avvalgi ModelPricing qiymatlari ushbu tashqi hisobning manbasi sifatida olinmadi.

Median yakuniy javob vaqti **3.97 s**, eng uzuni **8.59 s**. Eng katta bir navbat prompt yig'indisi **34 289**, agentning 40 000 limitidan past. Boshlang'ich auditdagi 40 359 token bilan tugamay qolgan tanlov oqimi yangi sinovda takrorlanmadi.

## Qo'llash chegarasi

Haqiqiy tarkib/care ma'lumoti katalogda bo'sh joylarda AI uni halol noma'lum deydi; bilim bazasi yetkazib beruvchi hujjati o'rnini bosmaydi. Paket generatori hamma did va mavjud qatlamni universal moslashtiruvchi dizayner emas. Ovoz, mobil buyurtma formasi, billing, umumiy PII filtri va ko'p tenantli pricing bo'yicha oldingi texnik audit topilmalari ushbu ballga qo'shilmadi va bajarildi deb belgilanmadi.
