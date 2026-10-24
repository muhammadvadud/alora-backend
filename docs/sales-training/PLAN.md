# Parda sotuvchisi bilimlarini yaxshilash rejasi

Boshlanish: 2026-10-25 04:23, Asia/Tashkent. Ish oynasi: besh soatgacha, 09:23 gacha.
Branch: backend va agent repolarida `feat/25-sales-training`; `main`ga push yoki merge qilinmaydi.

## Maqsad va chegaralar

Asosiy ish — parda bo'yicha bilim, ehtiyojni aniqlash, mos variant tanlash, e'tirozga javob va savdoni yakunlash sifati. O'zbekiston bozoridagi tul, portyera, blackout/dimout, xay-tek, klassik/neoklassik, kelin-kuyov xonasi, balkon va mahalliy o'lchov/narx atamalari markazda bo'ladi. Mahsulot tavsiflari va fason modellari ham shu muhitga mos boyitiladi. DeepSeek modelining vaznlari qayta o'qitilmaydi: boshqariladigan bilimlar, versiyali system prompt va zarur tool yordamchilari yaxshilanadi. Bu farq yakuniy hisobotda aniq yoziladi.

90/100 — maqsad, oldindan berilgan natija emas. Yakuniy javobda haqiqiy o'lchov, o'tmagan ssenariylar va qolgan cheklovlar ko'rsatiladi. Ovoz, mobil UI, umumiy billing va deploy auditi bu ishning markazi emas.

## 0. Tiklash imkoniyati va boshlang'ich holat

- [x] Asosiy PostgreSQL bazasi custom-format `pg_dump` bilan olindi.
- [x] Dump boshqa vaqtinchalik bazaga xatosiz tiklandi; 57 bilim qoidasi tekshirildi; tekshiruv bazasi o'chirildi.
- [x] Backup va SHA256 manifest Git'dan tashqarida, faqat egasi o'qiydigan katalogda saqlandi: `/home/muhammadvadud/it/alora/backups/sales-training-20261025/`.
- [x] Eski knowledge/prompt holati va commit qilinmagan patchlar backup katalogiga saqlandi.
- [x] Ikki repoda alohida ish branchi ochildi. Mobil kodga tegilmaydi.

Agent repoda ish boshlanishidan oldin 37 ta tracked faylda va qo'shimcha untracked domen/tool testlarida o'zgarish bor edi. Ular ushbu ishda yozilgan deb ko'rsatilmaydi. Tekshirilgan boshlang'ich snapshot alohida commit bo'ladi; keyingi commitlar yangi o'zgarishlarni aniq ajratadi. `.forge`, `.env`, shaxsiy suhbatlar va DB dump Git'ga qo'shilmaydi.

## 1. Bilim auditi va manbalar

- [x] Bazadagi 57 qoida birma-bir ko'rildi.
- [ ] Xato yoki haddan tashqari qat'iy eski qoidalar aniq matn bo'yicha versiyali almashtirish ro'yxatiga olinadi; yozuvlar o'chirilmaydi.
- [ ] Birlamchi manbalardan yorug'lik/maxfiylik, o'lchov, osish/fason, mato parvarishi, bolalar xavfsizligi va issiqlik bo'yicha qisqa bilimlar tayyorlanadi.
- [ ] Har yangi qoidaga manba ID yoki loyiha muharrirlik siyosati belgilanadi. Tashqi do'kon narxlari va zaxirasi Alora katalogiga ko'chirilmaydi.

## 2. Bilim paketi va sotuv prompti

- [ ] Idempotent, dry-run va rollback imkoniyatli bilim paketi joriy qilinadi.
- [ ] Umumiy prompt ixcham bo'ladi; katta bilim bazasi har navbatga to'liq qo'shilmaydi.
- [ ] Xona/uslub va funksional talablar ajratiladi: blackout o'rniga semi taklif qilinsa cheklov yashirilmaydi.
- [ ] Narx, mato xususiyati, kafolat, muddat, chegirma va to'lov holati faqat tegishli ma'lumotdan olinadi.
- [ ] Bir savol, qisqa tavsiya, talabni qayta so'ramaslik, asosli e'tiroz yechimi va bosimsiz yakunlash o'rgatiladi.
- [ ] Sotuvchi va mijozga murojaat uslubi aniq ajratiladi; ruscha/o'zbek lotin/kirill qoidalari belgilanadi.

## 3. Faqat zarur texnik yordam

- [ ] Bilimni haqiqiy suhbat savoliga mos, qisqa va ko'p tilli olish tekshiriladi.
- [ ] Sotuvni bevosita buzadigan takroriy xizmat, paket tanlovining yo'qolishi va asossiz mahsulot tavsiyasi minimal doirada tuzatiladi.
- [ ] Yadro arxitekturasi, narx formulasi va ombor modeli o'zgartirilmaydi. Qoida o'zgarishi kerak bo'lsa avval `rules.md`ga sabab/ADR yoziladi.
- [ ] Yangi fason faqat mavjud va mos katalog qatlamlaridan tuziladi; ko'rinish uchun to'qima mahsulot, narx yoki soxta xususiyat yaratilmaydi.

## 4. Kalitsiz sifat tekshiruvi

- [ ] Bilim paketi validatsiyasi, idempotent import/rollback, prompt uzunligi, retrieval relevanti va sotuv regressiyalari uchun mazmunli testlar.
- [ ] Agent: build, vet, lint va race testlar. Backend: ruff, format, mypy, migratsiya tekshiruvi va pytest.
- [ ] Backend testlari asosiy DB va xizmatlardan ajratilgan muhitda bajariladi: Redis pub/sub orqali sinov ma'lumoti jonli katalogga aralashmaydi.
- [ ] Har mantiqiy tugallangan ish alohida Conventional Commit; `tasks.md` o'sha commitda yangilanadi.

## 5. Oxirgi cheklangan jonli API baholash

- [ ] Boshlanishdagi audit yozuvlari taqqoslash uchun ishlatiladi; yangi baseline uchun pulli so'rov sarflanmaydi.
- [ ] Jonli test faqat tayyor paket joriy qilingandan va kalitsiz testlar o'tgandan keyin.
- [ ] Pul chegarasi oldindan belgilanadi; hisob balansi maxfiy saqlanadi. Token sarfi har navbat bo'yicha jamlanadi, muvaffaqiyatsiz so'rovlar ham qayd etiladi.
- [ ] Kam sonli ko'p navbatli ssenariy: ehtiyoj/tanlov, qoraytirish/maxfiylik, o'lchov, budjet, parvarish, bolalar xavfsizligi, e'tiroz va buyurtma. Zarur bo'lsa faqat yiqilgan holat qayta sinaladi.
- [ ] Baholash: funksional moslik 25; fakt/narx/cheklov to'g'riligi 25; suhbat va e'tiroz 20; yakunlash/holat 15; til/ixchamlik 10; token tejamkorligi 5. Kritik to'qima narx yoki noto'g'ri tasdiq bo'lsa 90+ berilmaydi.

## Git va yakuniy topshirish

Mavjud bo'lmagan yangi remote branch birinchi pushda yaratiladi. Keyingi har pushdan oldin `git pull --rebase origin feat/25-sales-training` bajariladi. Pull paytida begona o'zgarishlar yo'qotilmaydi. Repo qoidalaridagi o'zbekcha, atomik commitlar va test talablari saqlanadi.

Ushbu katalogda `SOURCES.md`, `KNOWLEDGE.md`, `TECHNICAL-CHANGES.md`, `EVALUATION.md` va yakuniy `RESULTS.md` yuritiladi. Backup/rollback ko'rsatmasi, o'zgargan yozuvlar soni, commitlar, pulli so'rovlar soni va haqiqiy yakuniy baho yoziladi. Natija 90 ga yetmasa bu yashirilmaydi.
