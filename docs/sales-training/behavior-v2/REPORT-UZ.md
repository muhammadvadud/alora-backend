# Parda sotuv yordamchisi: xulq-atvor bahosi

Sana: 2026-10-26. Baholash faqat suhbat sifati va sotuvdagi ishonchlilikka tegishli; build, lint va testlar ballga kiritilmagan.

## Baho: 84/100

| Yo'nalish | Ball | Dalil |
|---|---:|---|
| Narx va xizmatlar | 23/30 | To'liq 40 navbatli v8 sinovida maydon, xizmat, jami va avans izohlari ko'p hollarda to'g'ri. v9 ning 02_sale navbatida mijoz faqat tikuv so'ragan bo'lsa-da, AI `tape` va `hook`ni ham hisobga qo'shdi: jami 60 000 so'm ortiq chiqdi. |
| Katalog dalili va halollik | 18/20 | Noma'lum tarkib, kelib chiqish va parvarish bo'yicha kafolat bermadi. Biroq v8 dagi allergiya javobida matoni terida sinashni tavsiya qildi; bu tasdiqlanmagan va takrorlanmasligi kerak. |
| Holat, budjet va qoralama | 19/20 | Budjet/o'lchov tuzatishlarini saqladi, buyurtma qoralamasini tasdiqlangan buyurtmadan ajratdi, pul olinmaganini to'g'ri bildirdi. |
| O'lchov va bichish ehtiyotkorligi | 12/15 | Oyna eni bilan karnizni farqladi. v8 dagi rulon savolida aniq bichish yo'nalishi/chok bo'yicha ortiqcha taxminli shartli maslahat berdi. |
| Muloqot va sotuvga moslik | 8/10 | O'zbek, kirill va rus tillarida, odatda ixcham javob berdi. Ba'zi navbatlarda hisobga aloqasiz qo'shimcha savol berdi. |
| Ishonchlilik | 4/5 | v8 to'liq suhbatlarda 40/40 javob, bo'sh javob yoki API xatosi yo'q. v9 run provayder balans xatosi bilan uzildi. |

## Sinov qamrovi

- `results-v8-complete.jsonl`: 22 ssenariy, 40/40 navbat. Bu yakunlangan, ammo keyin qo'shilgan v9/v10 tuzatishlaridan oldingi run; shu sababli u yangi prompt versiyasining bahosi emas.
- `results-v9-partial.jsonl`: 4 ssenariy, 8 yozuv; `04_missing` birinchi navbatida bo'sh javob. Agent logi DeepSeek hisobida `402 Insufficient Balance` ko'rsatdi. 02_sale da xizmatlar ortiqcha qo'shilgani dalillandi.
- v10 prompt va bilim qoidalari snapshot bilan bazaga qo'llandi; ushbu versiya to'liq API orqali qayta baholanmadi. `train_sales --guidance-only` preview: 122 qoida, prompt 5,971 belgi, mahsulot/fason importi 0.

84 ball v8 to'liq run va v9 da ko'rilgan moliyaviy xato asosidagi qo'lda rubrika bahosi. v10 ni sinamasdan 90+ deb belgilashga dalil yetarli emas. To'liq yangi baho uchun DeepSeek hisob balansini to'ldirgach 40 navbatli runni aynan v10 da qayta bajarish kerak.
