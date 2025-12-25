from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_contest_and_bet_contest"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="balance",
            field=models.DecimalField(decimal_places=2, default=1000, max_digits=10),
        ),
    ]
