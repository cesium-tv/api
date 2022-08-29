import os
from django.conf import settings
from django.db import migrations, models
from django.contrib.auth import get_user_model
import django.db.models.deletion
import django.utils.timezone
import rest.models

PUBLISHERS = [
    {
        'pk': 1,
        'name': 'Timcast',
        'url': 'https://timcast.com/',
    },
]

PLATFORMS = [
    {
        'pk': 1,
        'name': 'Timcast',
        'crawler': 'TimcastCrawler',
    },
    {
        'pk': 2,
        'name': 'PeerTube',
        'crawler': 'PeerTubeCrawler',
    }
]

CHANNELS = [
    {
        'pk': 1,
        'publisher_id': 1,
        'platform_id': 1,
        'name': 'IRL',
        'url': 'https://timcast.com/members-area/section/timcast-irl/',
        'extern_id': 'timcast-irl',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/timcast-irl/',
                r'^https://timcast.com/members-area/.*member-podcast',
            ],
            'credentials': {
                'username': 'env[TIMCAST_USERNAME]',
                'password': 'env[TIMCAST_PASSWORD]',
            },
        },
    },
    {
        'pk': 2,
        'publisher_id': 1,
        'platform_id': 1,
        'name': 'Green Room',
        'url': 'https://timcast.com/members-area/section/green-room/',
        'extern_id': 'green-room',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/green-room/',
                r'^https://timcast.com/members-area/.*green-room',
            ],
            'credentials': {
                'username': 'env[TIMCAST_USERNAME]',
                'password': 'env[TIMCAST_PASSWORD]',
            },
        },
    },
    {
        'pk': 3,
        'publisher_id': 1,
        'platform_id': 1,
        'name': 'Tales From the Inverted World',
        'url': 'https://timcast.com/members-area/section/tales-from-the-inverted-world/',
        'extern_id': 'tales-from-the-inverted-world',
        'options': {
            'depth': None,
            'limit': None,
            'whitelist': [
                r'^https://timcast.com/members-area/section/tales-from-the-inverted-world/',
                r'^https://timcast.com/members-area/',
            ],
            'credentials': {
                'username': 'env[TIMCAST_USERNAME]',
                'password': 'env[TIMCAST_PASSWORD]',
            },
        },
    },
    {
        'pk': 4,
        'publisher_id': 1,
        'platform_id': 2,
        'name': 'Ben''s Favorites',
        'extern_id': "btimby_channel",
        'url': 'http://cesium.tv/',
        'options': {
            'credentials': {
                'username': 'env[PEERTUBE_USERNAME]',
                'password': 'env[PEERTUBE_PASSWORD]',
            }
        },
    },
]


def create_superuser(apps, schema_editor):
    User = get_user_model()

    DJANGO_SU_USERNAME = os.getenv('DJANGO_SU_USERNAME')
    DJANGO_SU_EMAIL = os.getenv('DJANGO_SU_EMAIL')
    DJANGO_SU_PASSWORD = os.getenv('DJANGO_SU_PASSWORD')

    if not DJANGO_SU_USERNAME or not DJANGO_SU_PASSWORD:
        return

    superuser = User.objects.create_superuser(
        pk=1,
        site_id=1,
        username=DJANGO_SU_USERNAME,
        email=DJANGO_SU_EMAIL,
        password=DJANGO_SU_PASSWORD)
    superuser.save()


def delete_superuser(apps, schema_editor):
    User.objects.using(db_alias).get(pk=1).delete()


def create_publishers(apps, schema_editor):
    Publisher = apps.get_model('rest', 'Publisher')
    User = apps.get_model('rest', 'User')
    Site = apps.get_model('sites', 'Site')
    db_alias = schema_editor.connection.alias
    publisher = Publisher.objects.using(db_alias).create(**PUBLISHERS[0])
    publisher.users.add(User.objects.using(db_alias).get(pk=1))
    publisher.sites.add(Site.objects.using(db_alias).get(pk=1))


def delete_publishers(apps, schema_editor):
    Publisher = apps.get_model('rest', 'Publisher')
    db_alias = schema_editor.connection.alias
    Publisher.objects.using(db_alias).get(pk=PUBLISHERS[0]['pk']).delete()


def create_platforms(apps, schema_editor):
    Platform = apps.get_model('rest', 'Platform')
    db_alias = schema_editor.connection.alias
    for platform in PLATFORMS:
        Platform.objects.using(db_alias).create(**platform)


def delete_platforms(apps, schema_editor):
    Platform = apps.get_model('rest', 'Platform')
    db_alias = schema_editor.connection.alias
    for platform in PLATFORMS:
        Platform.objects.using(db_alias).get(pk=platform['pk']).delete()


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


def create_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    db_alias = schema_editor.connection.alias
    Site.objects.using(db_alias).create(
        pk=1,
        domain='cesium.tv',
        name='cesium.tv',
    )


def delete_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    db_alias = schema_editor.connection.alias
    Site.objects.using(db_alias).filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rest', '0001_initial'),
    ]

    operations = [
        # NOTE: This goes into the initial migration:
        # migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS "citext"'),

        # Add User
        migrations.RunPython(create_superuser, delete_superuser),

        # Modify Site
        migrations.RunPython(create_site, delete_site),

        # Add publishers
        migrations.RunPython(create_publishers, delete_publishers),

        # Add publishers
        migrations.RunPython(create_platforms, delete_platforms),

        # Add channels
        migrations.RunPython(create_channel, delete_channel),
    ]
