from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0003_auto_20250101_0000'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprogress',
            name='user',
        ),
        migrations.AlterField(
            model_name='userprogress',
            name='session_key',
            field=models.CharField(max_length=40, db_index=True),
        ),
    ]
