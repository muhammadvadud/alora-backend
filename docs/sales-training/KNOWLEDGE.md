# Bilim va katalog paketi

Paket: `apps/knowledge/data/sales_v1.json`, yakuniy versiya `2026.10.25.3`; joriy DB prompt v3.

- 118 ta yangi, manbasi ko'rsatilgan ixcham qoida; eng uzun qoida 234 belgi.
- 55 ta eski aniq tavsiya matni almashtirish ro'yxatida. Ular o'chirilmaydi, nofaol qilinadi.
- Managerning ro'yxatga kirmagan qoidalari, jumladan mijozga yo'nalish o'rniga quyosh tushishini so'rash istagi saqlanadi.
- 14 ta mavjud mahsulot kodi uchun tavsif, tavsiya etiladigan xona va o'zbek/rus atamalari boyitiladi. Narx, variant, rang, tarkib va tasdiqlangan care o'zgarmaydi. Ikki mavjud katalogda jami 28 mahsulot yozuvi.
- 10 ta fason shabloni har bir tegishli katalogga qo'shiladi: sodda neoklassik mehmonxona, yotoqxona modern/minimal, kelin-kuyov classic/modern, bolalar, qisqa oshxona, xay-tek, minimal mehmonxona va sodda ofis.
- Fasonlardagi K qiymati mavjud CalcRule kalitidan, u yo'q bo'lsa mavjud `coef_default`dan olinadi. To'qima narx, yangi mahsulot zaxirasi yoki tasdiqlanmagan parvarish yaratilmaydi.

Bu ishda yangi narxli SKU kiritilmadi: mahalliy ochiq e'lonlarda birlik/aniq variant tasdig'i yetarli bo'lmagan narxni Alora narxi deb yozish noto'g'ri bo'lardi. Mahsulot modelining mavjud yozuvlari boyitildi va yangi fasonlar qo'shiladi.

## Tozalangan xatolar

Eski qoidalar tul kunduzi mutlaqo ko'rinmaslik beradi, baxmal doim kimyoviy tozalanadi, polyester doim yuviladi, kelin-kuyov xonasi to'yxona, qimmatga qarshi tayyor standart parda taklif qilinadi, oddiy astar qoraytiradi degan xavfli umumlashtirishlarga olib kelishi mumkin edi.

Yangi paket funksiya va bezakni, mato va butun xonaning qorayishini, oddiy va blackout astarni, pogon metr va m²ni ajratadi. Didga oid tavsiyalar mutlaq qoida emas. Bolalar xavfsizligi va mahsulot yorlig'i ustuvor; narx va vakolat Django shartnomasidan olinadi.

## Joriy qilish va qaytarish

```sh
python manage.py train_sales
python manage.py train_sales --apply --snapshot /maxfiy-katalog/sales-before.json
python manage.py train_sales --rollback /maxfiy-katalog/sales-before.json
```

Birinchi buyruq dry-run: yozmaydi va LLM'ga murojaat qilmaydi. Import UUID kalitlari bilan idempotent; prompt matni o'zgarmasa yangi versiya yaratilmaydi. Snapshot 0600 ruxsat bilan avval yoziladi; mavjud snapshot ustiga yozilmaydi. Qaytarishda oldingi bilim/faollik, mahsulot metadata va prompt tiklanadi; yangi bilim/fasonlar o'chirilmay, nofaol qilinadi. To'liq DB dump oxirgi tiklash zaxirasi.

Snapshot/dump Git'ga yuklanmaydi. Dry-run va real qo'llash natijalari yakuniy hisobotga qo'shiladi.
