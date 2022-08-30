# Generated by Django 4.0.7 on 2022-08-30 03:47

import authlib.oauth2.rfc6749.models
import colorfield.fields
from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.citext
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import rest.models
import uuid


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
                ('favicon', models.ImageField(null=True, upload_to=rest.models.get_file_name, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['ico'])])),
                ('logo', models.ImageField(upload_to=rest.models.get_file_name)),
                ('bgcolor', colorfield.fields.ColorField(default='#000000', image_field=None, max_length=18, samples=None, verbose_name='Background color')),
                ('fgcolor', colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=18, samples=None, verbose_name='Foreground color')),
                ('actcolor', colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=18, samples=None, verbose_name='Active color')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('url', models.URLField()),
                ('extern_id', models.CharField(max_length=128, unique=True)),
                ('extern_cursor', models.JSONField(blank=True, null=True)),
                ('options', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OAuth2Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.UUIDField(blank=True, default=uuid.uuid4, unique=True)),
                ('client_secret', models.UUIDField(blank=True, default=uuid.uuid4)),
                ('client_name', models.CharField(max_length=120)),
                ('website_uri', models.URLField(max_length=256, null=True)),
                ('description', models.TextField(null=True)),
                ('redirect_uris', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=256), size=None)),
                ('default_redirect_uri', models.CharField(max_length=256, null=True)),
                ('scope', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=24), null=True, size=None)),
                ('response_types', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), null=True, size=None)),
                ('grant_types', rest.models.ChoiceArrayField(base_field=models.CharField(choices=[('authorization_code', 'authorization_code'), ('refresh_token', 'refresh_token'), ('password', 'password'), ('device_code', 'device_code')], max_length=32), default=rest.models.grant_types_default, size=None)),
                ('token_endpoint_auth_method', models.CharField(choices=[('client_secret_post', 'client_secret_post'), ('client_secret_basic', 'client_secret_basic')], default='client_secret_post', max_length=120)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'OAuth2 Client',
            },
            bases=(rest.models.HashidsModelMixin, models.Model, authlib.oauth2.rfc6749.models.ClientMixin),
        ),
        migrations.CreateModel(
            name='OAuth2DeviceCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=rest.models.get_random_code, max_length=8, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('crawler', rest.models.ModuleAttributeField(choices=[('PeerTubeCrawler', 'PeerTubeCrawler'), ('RumbleCrawler', 'RumbleCrawler'), ('TimcastCrawler', 'TimcastCrawler')], max_length=32, module_name='vidsrc.crawl')),
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
                ('extern_id', models.CharField(max_length=128, unique=True)),
                ('title', models.CharField(max_length=256)),
                ('poster', models.URLField()),
                ('duration', models.PositiveIntegerField()),
                ('original', models.JSONField(blank=True, null=True)),
                ('total_plays', models.PositiveIntegerField(default=0)),
                ('total_likes', models.PositiveIntegerField(default=0)),
                ('total_dislikes', models.PositiveIntegerField(default=0)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='rest.channel')),
                ('tags', models.ManyToManyField(related_name='tagged', to='rest.tag')),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SiteOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=64, null=True, verbose_name='app title')),
                ('menu', rest.models.ChoiceArrayField(base_field=models.CharField(choices=[('options', 'Options'), ('subscriptions', 'Subscriptions'), ('again', 'Watch again'), ('latest', 'Latest'), ('oldies', 'Oldies'), ('home', 'Home'), ('search', 'Search'), ('resume', 'Resume')], max_length=32), size=None)),
                ('default_lang', models.CharField(max_length=2)),
                ('auth', rest.models.ModuleAttributeField(blank=True, choices=[('PeerTubeAuth', 'PeerTubeAuth'), ('RumbleAuth', 'RumbleAuth'), ('TimcastAuth', 'TimcastAuth')], max_length=32, module_name='vidsrc.auth', null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sites', to='rest.brand')),
                ('site', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='sites.site')),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('url', models.URLField()),
                ('options', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('sites', models.ManyToManyField(to='sites.site')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='OAuth2UserCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=rest.models.get_random_code, max_length=8, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='oauth2_user_codes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OAuth2Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_type', models.CharField(max_length=40)),
                ('access_token', models.CharField(max_length=255, unique=True)),
                ('refresh_token', models.CharField(db_index=True, max_length=255)),
                ('scope', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=24), null=True, size=None)),
                ('revoked', models.BooleanField(default=False)),
                ('issued_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_in', models.IntegerField(default=0)),
                ('client', models.ForeignKey(db_column='client', on_delete=django.db.models.deletion.CASCADE, to='rest.oauth2client', to_field='client_id')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model, authlib.oauth2.rfc6749.models.TokenMixin),
        ),
        migrations.CreateModel(
            name='OAuth2Code',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=120, unique=True)),
                ('redirect_uri', models.TextField(null=True)),
                ('response_type', models.TextField(null=True)),
                ('scope', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=24), null=True, size=None)),
                ('auth_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('nonce', models.CharField(max_length=120, null=True)),
                ('client', models.ForeignKey(db_column='client', on_delete=django.db.models.deletion.CASCADE, to='rest.oauth2client', to_field='client_id')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            bases=(rest.models.HashidsModelMixin, models.Model, authlib.oauth2.rfc6749.models.AuthorizationCodeMixin),
        ),
        migrations.AddField(
            model_name='channel',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='rest.platform'),
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
                ('height', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('fps', models.PositiveSmallIntegerField()),
                ('size', models.PositiveBigIntegerField(blank=True, null=True)),
                ('url', models.URLField()),
                ('original', models.JSONField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='rest.video')),
            ],
            options={
                'unique_together': {('video', 'width', 'height'), ('video', 'url')},
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
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
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
        migrations.AlterUniqueTogether(
            name='channel',
            unique_together={('publisher', 'name')},
        ),
    ]
