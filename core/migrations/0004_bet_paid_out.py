from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_customuser_balance"),
    ]

    operations = [
        migrations.AddField(
            model_name="bet",
            name="paid_out",
            field=models.BooleanField(default=False),
        ),
    ]
