# ADR-001: Narx va AI sozlamalarini global saqlash

- **Holat:** Qabul qilingan
- **Sana:** 2026-09-10

## Kontekst

Alora hozircha bitta do'kon uchun ishlab chiqilmoqda va bitta serverga deploy
qilinadi. Shu sababli narx qoidalari hamda AI bilan bog'liq sozlamalar amalda
bitta do'kon tomonidan ishlatiladi.

## Qaror

`CalcRule`, `ServicePrice`, `DiscountTier`, `DiscountPolicy`, `OrderDefaults`,
`ModelPricing`, `KnowledgeRule`, `PromptVersion` va `UsageLimit` modellari
ataylab global, ya'ni `BaseModel` asosida va tenantsiz, qoladi.

Bu modellar hozircha `TenantScopedModel` orqali tenantga bog'lanmaydi. Qaror
koddagi modul hujjatlari va Django system check orqali ham qayd etiladi.

## Sabab

Bitta tenant mavjud bo'lganda tenantlashtirish hech qanday qo'shimcha himoya
bermaydi, lekin migratsiyalar va kodning murakkabligini oshiradi. Hozirgi
deploy modeli uchun global sozlamalar sodda va yetarli.

## Oqibatlar va xavf

Ikkinchi do'kon yoki filial qo'shilsa, bu qaror **qayta ko'rib chiqilishi
shart**. Aks holda A do'kon chegirma siyosatini o'zgartirganda B do'konning
narxlari ham o'zgaradi va ma'lumot buzilishi yuz beradi.

Qayta ko'rib chiqish sharti: `Tenant.objects.count() > 1`.

## Kelajakdagi migratsiya rejasi

Tenantlashtirish zarur bo'lganda migratsiya uch bosqichda bajariladi:

1. Modellarga nullable `tenant` maydoni qo'shiladi.
2. Mavjud yozuvlar uchun tenant qiymati backfill qilinadi.
3. Backfill tekshirilgach, maydon `NOT NULL` qilinadi.

`null=False` maydonini bitta migratsiyada birdan qo'shish mumkin emas.
