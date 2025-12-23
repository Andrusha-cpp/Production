from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("ends_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "winner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="won_contests",
                        to="core.candidate",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="contest",
            name="participants",
            field=models.ManyToManyField(blank=True, related_name="contests", to="core.candidate"),
        ),
        migrations.AddField(
            model_name="bet",
            name="contest",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bets",
                to="core.contest",
            ),
        ),
    ]
