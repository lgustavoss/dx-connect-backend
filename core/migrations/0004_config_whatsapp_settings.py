from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_config_appearance_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="config",
            name="whatsapp_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]


