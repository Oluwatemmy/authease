from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_core', '0003_onetimepassword_created_at'),
    ]

    operations = [
        # Remove RegexValidator and increase max_length on OTP code
        migrations.AlterField(
            model_name='onetimepassword',
            name='code',
            field=models.CharField(max_length=10, unique=True),
        ),
        # Remove help_text from User email field
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=255, unique=True, verbose_name='Email Address'),
        ),
        # Revert last_login to inherited AbstractBaseUser field (nullable, no auto_now)
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last login'),
        ),
    ]
