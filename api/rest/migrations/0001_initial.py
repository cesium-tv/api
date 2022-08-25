# Generated by Django 4.0.7 on 2022-08-25 05:09

import colorfield.fields
from django.conf import settings
import django.contrib.postgres.fields.citext
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rest.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS "citext"'),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(max_length=32, unique=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('is_confirmed', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='sites.site')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'unique_together': {('email', 'site')},
            },
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('logo', models.ImageField(upload_to='')),
                ('bgcolor', colorfield.fields.ColorField(default='#000000', image_field=None, max_length=18, samples=None)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('url', models.URLField()),
                ('cursor', models.JSONField(blank=True, null=True)),
                ('options', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', django.contrib.postgres.fields.citext.CITextField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('poster', models.URLField()),
                ('duration', models.PositiveIntegerField()),
                ('fps', models.PositiveSmallIntegerField()),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='rest.channel')),
                ('tags', models.ManyToManyField(related_name='tagged', to='rest.tag')),
            ],
            options={
                'unique_together': {('channel', 'title')},
            },
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SiteOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=64, null=True, verbose_name='app title')),
                ('menu', rest.models.ChoiceArrayField(base_field=models.CharField(choices=[('options', 'Options'), ('subscriptions', 'Subscriptions'), ('again', 'Watch again'), ('latest', 'Latest'), ('oldies', 'Oldies'), ('home', 'Home'), ('search', 'Search')], max_length=32), size=None)),
                ('default_lang', models.CharField(max_length=2)),
                ('auth_backend', rest.models.ModuleAttributeField(blank=True, choices=[('TimcastBackend', 'TimcastBackend')], max_length=32, module='rest.auth.backends', null=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sites', to='rest.brand')),
                ('site', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='sites.site')),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('url', models.URLField(unique=True)),
                ('options', models.JSONField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('sites', models.ManyToManyField(to='sites.site')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.AddField(
            model_name='channel',
            name='publisher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='rest.publisher'),
        ),
        migrations.CreateModel(
            name='VideoSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('width', models.PositiveSmallIntegerField()),
                ('height', models.PositiveSmallIntegerField()),
                ('url', models.URLField()),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='rest.video')),
            ],
            options={
                'unique_together': {('video', 'url'), ('video', 'width', 'height')},
            },
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='UserPlay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cursor', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='played', to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plays', to='rest.video')),
            ],
            options={
                'unique_together': {('user', 'video')},
            },
        ),
        migrations.CreateModel(
            name='UserLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('like', models.SmallIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked', to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='rest.video')),
            ],
            options={
                'unique_together': {('user', 'video')},
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to='rest.channel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribed', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'channel')},
            },
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
    ]
