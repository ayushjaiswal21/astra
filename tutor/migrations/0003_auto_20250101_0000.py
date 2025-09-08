from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('tutor', '0002_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprogress',
            name='session_key',
            field=models.CharField(default='', max_length=40, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userprogress',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tutor.userprofile'),
        ),
        migrations.AlterUniqueTogether(
            name='userprogress',
            unique_together={('session_key', 'lesson')},
        ),
    ]
