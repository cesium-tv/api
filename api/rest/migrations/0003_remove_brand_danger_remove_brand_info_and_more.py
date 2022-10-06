# Generated by Django 4.0.7 on 2022-09-15 00:52

import django.core.validators
from django.db import migrations, models
import rest.models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0002_brand_channel_oauth2client_platform_tag_video_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='brand',
            name='danger',
        ),
        migrations.RemoveField(
            model_name='brand',
            name='info',
        ),
        migrations.RemoveField(
            model_name='brand',
            name='primary',
        ),
        migrations.RemoveField(
            model_name='brand',
            name='success',
        ),
        migrations.RemoveField(
            model_name='brand',
            name='warning',
        ),
        migrations.AddField(
            model_name='brand',
            name='colors',
            field=models.JSONField(default={'black': '#0a0a0a', 'black-bis': '#121212', 'black-ter': '#242424', 'blue': '#485fc7', 'cyan': '#3e8ed0', 'green': '#48c78e', 'grey': '#7a7a7a', 'grey-dark': '#4a4a4a', 'grey-darker': '#363636', 'grey-light': '#b5b5b5', 'grey-lighter': '#dbdbdb', 'grey-lightest': '#ededed', 'orange': '#ff470f', 'purple': '#b86bff', 'red': '#f14668', 'turquoise': '#00d1b2', 'white': '#ffffff', 'white-bis': '#fafafa', 'white-ter': '#f5f5f5', 'yellow': '#ffe08a'}, null=True),
        ),
        migrations.AlterField(
            model_name='brand',
            name='favicon',
            field=rest.models.ImageField(null=True, upload_to=rest.models.get_file_name, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['ico', 'png'])]),
        ),
        migrations.AlterField(
            model_name='brand',
            name='logo',
            field=rest.models.ImageField(upload_to=rest.models.get_file_name),
        ),
        migrations.AlterField(
            model_name='brand',
            name='scheme',
            field=models.CharField(choices=[(None, None), ('light', 'light'), ('dark', 'dark')], default='light', max_length=5),
        ),
        migrations.AlterField(
            model_name='brand',
            name='theme_css',
            field=rest.models.FileField(upload_to='', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['css'])]),
        ),
    ]