from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rest.models


CHANNELS = [
    {
        'pk': 1,
        'platform_id': 1,
        'name': 'IRL',
        'url': 'https://timcast.com/members-area/section/timcast-irl/',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/timcast-irl/',
                r'^https://timcast.com/members-area/.*member-podcast',
            ],
        },
    },
    {
        'pk': 2,
        'platform_id': 1,
        'name': 'Green Room',
        'url': 'https://timcast.com/members-area/section/green-room/',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/green-room/',
                r'^https://timcast.com/members-area/.*green-room',
            ],
        },
    },
    {
        'pk': 3,
        'platform_id': 1,
        'name': 'Tales From the Inverted World',
        'url': 'https://timcast.com/members-area/section/tales-from-the-inverted-world/',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/tales-from-the-inverted-world/',
                r'^https://timcast.com/members-area/',
            ],
        },
    },
]


def create_platform(apps, schema_editor):
    Platform = apps.get_model('rest', 'Platform')
    db_alias = schema_editor.connection.alias
    Platform.objects.using(db_alias).create(
        pk = 1,
        name = 'Timcast',
        url = 'https://timcast.com/',
        options = {
            'login': {
                'url': 'https://timcast.com/login/',
                'username': ('#user_login', 'env[TIMCAST_USERNAME]'),
                'password': ('#user_pass', 'env[TIMCAST_PASSWORD]'),
                'submit': '#wp-submit',
            }
        },
    )


def delete_platform(apps, schema_editor):
    Platform = apps.get_model('rest', 'Platform')
    db_alias = schema_editor.connection.alias
    Platform.objects.using(db_alias).get(pk=1).delete()


def create_channel(apps, schema_editor):
    Channel = apps.get_model('rest', 'Channel')
    db_alias = schema_editor.connection.alias
    for channel in CHANNELS:
        Channel.objects.using(db_alias).create(**channel)


def delete_channel(apps, schema_editor):
    Channel = apps.get_model('rest', 'Channel')
    db_alias = schema_editor.connection.alias
    ids = [c['pk'] for c in CHANNELS]
    Channel.objects.using(db_alias).get(pk__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0002_channel_platform_uservideo_video_uservideo_video_and_more'),
    ]

    operations = [
        # Add platforms
        migrations.RunPython(create_platform, delete_platform),

        # Add channels
        migrations.RunPython(create_channel, delete_channel),
    ]
