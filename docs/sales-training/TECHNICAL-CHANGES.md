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

Qolgan zarur sotuv yordamchilari va yakuniy sinov dalillari ish tugashi bilan shu faylga qo'shiladi.
