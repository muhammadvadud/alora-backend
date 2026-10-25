# Keyingi sotuv sayqali — 2026-10-25

Buyurtmachi qolgan kamchiliklarni birin-ketin tuzatishni davom ettirishni so'radi. Mahsulotning tarkib/parvarish/kelib chiqish ma'lumotlari hozir o'zgartirilmaydi; bu mavzu keyin alohida eslatiladi.

Ushbu bosqich:

1. Paketdagi tul rangini portyeradan alohida tanlash; mavjud rangga qat'iy moslik, topilmasa ochiq cheklov.
2. Yetkazish kiritilmagan, narxlangan yoki nol narxda kiritilgan holatlarni ajratish.
3. DB promptini cho'zmasdan qisqa javob, bitta savol va keraksiz tool chaqiruvini kamaytirish.

Avvalgi feat/25-sales-training branchida davom etiladi. Oldindan yangi DB backup: `/home/muhammadvadud/it/alora/backups/sales-followup-20261025/before-followup.dump`. Mahsulot/Fason/bilim importi qayta ishlatilmaydi; faqat versiyali prompt yangilanadi va eski prompt snapshoti olinadi.

Avval kalitsiz regressiyalar va repo tekshiruvlari bajariladi. Pullik API sinovlari faqat yakunda, oz sonli maqsadli holatlar bilan; avvalgi baho yangi tekshiruvsiz oshirilmaydi. Ovoz, mobil, umumiy billing va PII bo'yicha katta texnik ishlar alohida navbatda qoladi.

Mahsulot ma'lumotlari bo'yicha keyingi eslatma: yetkazib beruvchidan haqiqiy tarkib, yuvish yorlig'i va kelib chiqish hujjatlarini qaysi tartibda yig'ishni alohida kelishish.

## Birinchi bosqich natijasi

Prompt v4 bazada, 4709 belgi (oldingi 5693 dan 17% qisqa). Tul rangi portyeradan mustaqil; qat'iy rang filtri variantlar soni limitidan oldin ishlaydi. Aniq pushti nomi oq rang talabiga HEX yaqinligi bilan o'tkazilmaydi. Haqiqiy pushti HEX `#F7C8D0` noto'g'ri emas: avvalgi yaqinlik chegarasi oq bilan ham mos deb hisoblagan. Mahsulotdagi rang kodi o'zgartirilmadi. Mijoz aniq pushti so'rasa shu tanlov ustun.

Yetkazish holati display.delivery_status da: kiritilmagan, kiritilgan yoki ushbu hisobda narxi nol. Summa va formulalar o'zgarmadi. Price_quote so'ralmagan K kamaytirish tavsiyasini avtomatik qo'shmaydi. Og'ir 10 bo'lakli natija: curtain_calculate 2005 B, price_quote 1914 B — 2048 B limiti saqlandi.

Build/vet/lint/race, golden/e2e va yangi kalitsiz regressiyalar o'tdi. Yakunda faqat 2 ta DeepSeek foydalanuvchi navbati sinaldi: birinchisi rang yaqinligi muammosini ko'rsatdi, ikkinchisida standard/premiumdagi tul haqiqatan Oq qaytdi va javob yetkazish kiritilmaganini aytdi. Hisobiy qo'shimcha sarf $0.002531352; oldingi ish bilan jami $0.027471450. Baholash raqami shu ikki navbat asosida oshirilmadi.

Keyingi bosqich — PII: aniq ism/manzil/email maydonlari va eski suhbat tarixining modelga yuborilishidagi himoya. Ochiq matnda belgilanmagan har qanday ismni aniqlash to'liq NER talab qilishi mumkin; deterministic filtrning chegarasi sinovlarda va hisobotda ochiq qoladi. Narx/o'lcham va JSON/tool-call identifikatorlarini buzmaslik shart.

## Shaxsiy ma'lumot himoyasi

Markaziy filtr endi telefon bilan birga `ismim`, `mening ismim`, `mijozning ismi`, `меня зовут`, `ФИО`, aniq manzil belgilari va emailni yashiradi. Strukturali customer_name/address/email/phone maydonlari ham maskalanadi. Belgilanmagan har qanday ismni taxminan topish yoki barcha manzil shakllarini tushunish da'vosi yo'q. Manzil belgisidan keyingi maxfiy matn bir segment sifatida yopiladi; nuqtali qisqartmalarni to'liq NER kabi ajratmaydi.

Sessiya Store dekoratori eski tarix o'qilganda va yangi tarix yozilganda ishlaydi; matn qismlari, reasoning va tool arguments ham tekshiriladi. State'dagi erkin rang/qurilish/oyna nomlari ham qamraladi. Read paytida asl store yoki caller obyektlari o'zgarmaydi; tool-call ID va uning javob juftligi saqlanadi. Django'dagi asl suhbat yozuvlari va mavjud arxivlar o'chirilmaydi. ReAct yadrosi o'zgarmadi.

JSON `UseNumber` bilan ochiladi: katta butun son aniqligi yo'qolmaydi, narx/o'lcham stringlari telefon deb o'zgartirilmaydi, identifikatorlar buzilmaydi. Oddiy matndagi katta so'm summalari va pardaga oid ma'lumotlar uchun ham regressiya bor. O'zgarishsiz JSON qayta formatlanmaydi. Nomi/manzili aniq belgilangan test xabari gRPC chegarasida modelga masksiz o'tmagani kalitsiz fake streamer bilan tekshirildi; DeepSeek'ga yangi maxfiy test matni yuborilmadi.

Go build/vet/lint/race, golden/e2e va yangi PII/session/gRPC regressiyalari o'tdi. Keyingi texnik navbat: usage yozuvlari takrorlanishi va kichik USD xarajatining nolga yaxlitlanishi; mahsulot ma'lumotlari o'zgarishsiz qoladi.
