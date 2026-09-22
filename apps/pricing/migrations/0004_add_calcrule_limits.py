from decimal import Decimal

from django.db import migrations

LIMIT_RULES: list[dict[str, object]] = [
    {
        "key": "max_cornice_length_m",
        "value": Decimal("15.000"),
        "unit": "m",
        "description": "Karnizning maksimal uzunligi (m)",
        "applies_to": {},
    },
    {
        "key": "min_cornice_length_m",
        "value": Decimal("0.500"),
        "unit": "m",
        "description": "Karnizning minimal uzunligi (m)",
        "applies_to": {},
    },
    {
        "key": "max_height_m",
        "value": Decimal("6.000"),
        "unit": "m",
        "description": "Pardaning maksimal balandligi (m)",
        "applies_to": {},
    },
    {
        "key": "min_height_m",
        "value": Decimal("0.500"),
        "unit": "m",
        "description": "Pardaning minimal balandligi (m)",
        "applies_to": {},
    },
    {
        "key": "max_coef",
        "value": Decimal("4.000"),
        "unit": "coef",
        "description": "Maksimal burma koeffitsienti",
        "applies_to": {},
    },
    {
        "key": "min_coef",
        "value": Decimal("1.000"),
        "unit": "coef",
        "description": "Minimal burma koeffitsienti",
        "applies_to": {},
    },
]


def forwards(apps, schema_editor):
    CalcRule = apps.get_model("pricing", "CalcRule")
    for rule in LIMIT_RULES:
        CalcRule.objects.get_or_create(key=rule["key"], defaults=rule)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("pricing", "0003_alter_calcrule_value_and_more")]

    operations = [migrations.RunPython(forwards, backwards)]
