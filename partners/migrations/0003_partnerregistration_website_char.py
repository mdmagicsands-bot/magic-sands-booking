from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("partners", "0002_partnerregistration_accepted_terms_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partnerregistration",
            name="website",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
