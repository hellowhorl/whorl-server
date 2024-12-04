# Generated by Django 5.0.6 on 2024-06-07 11:39

import pgtrigger.compiler
import pgtrigger.migrations
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Inventory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("item_name", models.CharField(max_length=255)),
                ("item_qty", models.FloatField()),
                ("item_weight", models.FloatField()),
                ("item_bulk", models.FloatField()),
                ("item_consumable", models.BooleanField()),
                ("item_bin", models.BinaryField()),
            ],
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="inventory",
            trigger=pgtrigger.compiler.Trigger(
                name="decrement_item_qty_trigger",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func="\n        BEGIN\n            IF NEW.item_qty = 0 THEN\n                DELETE FROM inventory_inventory WHERE item_id = OLD.item_id;\n            END IF;\n            RETURN NEW;\n        END;\n        ",
                    hash="0ffc34705e964dc4195bc987a484dde9cedb4b78",
                    operation="UPDATE",
                    pgid="pgtrigger_decrement_item_qty_trigger_c958b",
                    table="inventory_inventory",
                    when="BEFORE",
                ),
            ),
        ),
    ]
