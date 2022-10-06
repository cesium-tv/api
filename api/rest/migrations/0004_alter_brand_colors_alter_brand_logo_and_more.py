# Generated by Django 4.0.7 on 2022-10-06 05:24

from django.db import migrations, models
import rest.models


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0003_remove_brand_danger_remove_brand_info_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='colors',
            field=models.JSONField(default={'black': '#0a0a0a', 'black_bis': '#121212', 'black_ter': '#242424', 'blue': '#485fc7', 'cyan': '#3e8ed0', 'green': '#48c78e', 'grey': '#7a7a7a', 'grey_dark': '#4a4a4a', 'grey_darker': '#363636', 'grey_light': '#b5b5b5', 'grey_lighter': '#dbdbdb', 'grey_lightest': '#ededed', 'orange': '#ff470f', 'purple': '#b86bff', 'red': '#f14668', 'turquoise': '#00d1b2', 'white': '#ffffff', 'white_bis': '#fafafa', 'white_ter': '#f5f5f5', 'yellow': '#ffe08a'}, null=True),
        ),
        migrations.AlterField(
            model_name='brand',
            name='logo',
            field=rest.models.ImageField(null=True, upload_to=rest.models.get_file_name),
        ),
        migrations.AlterField(
            model_name='brand',
            name='scheme',
            field=models.CharField(blank=True, choices=[(None, None), ('light', 'light'), ('dark', 'dark')], max_length=5, null=True),
        ),
    ]
