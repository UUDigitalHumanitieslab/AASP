# Generated by Django 3.2.8 on 2021-10-20 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aaspitem',
            name='arff_file',
            field=models.FileField(default=None, null=True, upload_to='input_files'),
        ),
    ]
