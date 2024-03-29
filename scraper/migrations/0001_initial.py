# Generated by Django 3.0.7 on 2021-02-27 10:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdFile',
            fields=[
                ('id', models.AutoField(db_column='AdFile_ID', primary_key=True, serialize=False)),
                ('ad_filepath', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CreativeInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ad_id', models.CharField(max_length=32)),
                ('advertiser_id', models.CharField(max_length=32)),
                ('transparency_url', models.CharField(max_length=128)),
                ('direct_ad_url', models.TextField(null=True)),
                ('scraped', models.BooleanField(default=False)),
                ('was_available', models.BooleanField(null=True)),
                ('regions', models.CharField(max_length=128)),
                ('unable_to_scrape_reason', models.CharField(max_length=64, null=True)),
                ('processed', models.BooleanField(default=False)),
                ('AdFile_ID', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='scraper.AdFile')),
            ],
            options={
                'unique_together': {('ad_id', 'advertiser_id')},
            },
        ),
    ]
