# Zarur texnik o'zgarishlar

Asosiy maqsad bilim/sotuv sifati; umumiy infratuzilma kamchiliklarini tuzatish bu ishga qo'shilmaydi.

## Bilimni joriy qilish

`backend/apps/knowledge/services.py` va `train_sales` command'i versiyali paketni tekshiradi, dry-run beradi, oldingi holatni snapshot qiladi va transaction ichida bilim/mahsulot/fason/promptni joriy qiladi. Ommaviy importdan keyin katalog to'liq yangilanadi. Narx formulasi, proto va DB modeli o'zgarmaydi.

## Token sarfi

Go promptidagi inline bilim ko'pi bilan 8 qoida va jami 2000 belgi. Qoida yarim jumlada kesilmaydi; qolgan bilim kerak bo'lganda olinadi. Lookup bir chaqiruvda ko'pi bilan 6 qoida beradi. Prompt va lookup shartlari bir domen matcher'idan foydalanadi.

Oldingi 50 qoidali standart limit ko'paygan bilim bazasini har navbatda yuborishga va tez byudjet tugashiga olib kelardi. Yangi limit bilim soni o'sganda promptni cheklangan tutadi. Agentning ReAct yadrosi o'zgartirilmagan.

## Ko'p tilli bilim

Qidiruv o'zbek lotin/kirill va ruscha so'zlarni til sinonimlari orqali tenglashtiradi. Masalan ruscha yuvish/parvarish yoki bolalar shnuri savoli o'zbekcha bilimga yetadi. Xona state'da hali yo'q bo'lsa query'dagi aniq xona ma'nosi mos qoidani topishga yordam beradi; allaqachon aniqlangan boshqa xonani query o'zboshimchalik bilan almashtirmaydi.

`knowledge_lookup` hisob va buyurtma bosqichida ham mavjud: mijoz hisobdan keyin parvarish yoki xavfsizlikni so'rashi tabiiy.

## Tekshiruv holati

Paketning 10 ta kalitsiz testi o'tdi. Backend umumiy toza test bazasida 465 test o'tdi, coverage 87%. Test Redis alohida konteynerda: real katalogga test deltalari chiqmaydi. Yangi Python modullari ruff/format/mypy tekshiruvlaridan o'tdi. Butun backend lint/type tekshiruvida avvalgi modullarga tegishli muammolar ham qayd etildi; ular alohida baseline bilan ajratiladi.

## Sotuvni buzgan yordamchi oqimlar

`price_quote` xizmatlar ro'yxati bilan montaj/karniz bayrog'i birga kelganda kalitlarni yakunda ham takrorsiz qiladi. Django narx formulasi o'zgarmaydi.

`order_draft(option_tier=...)` tayyor paket snapshotini ishlatadi. Tanlangan segment persistent state va promptda saqlanadi, qoralama bosqichi `order`ga o'tadi. Xuddi shu paketni qayta tanlash o'zgartirilgan taklifni yo'qotmaydi. Yangi hisob esa avvalgi taklifni tozalaydi. `build_options` va prompt tanlovdan keyin uchta tool bilan hisobni qayta qurishni buyurmaydi.

Mahsulot kartochkasiga katalogdagi haqiqiy fabric_type, tarkib, care va qisqa tavsif qo'shildi; yo'q maydonlar taxmin bilan to'ldirilmaydi. Mahalliy/ruscha aliaslar mahsulot qidiruvida ishlaydi. Aniq blackout filtri semi mahsulot bilan to'ldirilmaydi; ko'p qatlamli qidiruvda blackout talabi yordamchi tulga ko'chirilmaydi.

Fason lookup o'lcham ma'lum bo'lsa tayyor bo'lak eni/balandligini beradi: model ulushlarni o'zi ko'paytirmaydi. Premium fasonning kant/lambrekan/dekor rollariga tasodifiy portyera matosi qo'yilmaydi. Tavsiya matni mavjud bo'lmagan lambrekanni barcha premium paketga va'da qilmaydi.

Texnik fallback prompt 1830 belgiga qisqardi; sotuv siyosati versiyali DB promptida. Agent yadrosi, proto va pul formulalari o'zgarmadi.

30 ta tabiiy o'zbek lotin/kirill va rus savoli bilan real 118 qoidali paketning top-6 retrieval tekshiruvi o'tdi. Bu javob sifatining o'zi emas, kerakli bilim modelga yetishi tekshiruvi. Savol matnidagi qo'shtirnoq sifatidagi apostrof so'zga yopishib qolishi tuzatildi. Tul maxfiyligi va plita xavfsizligi umumiy faktlari state hali aniqlanmaganida ham olinadi.

Yakuniy API baholash va sarf natijalari `EVALUATION.md`ga yoziladi.
