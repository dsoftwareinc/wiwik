# Generated by Django 5.0 on 2023-12-21 10:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0013_answer_parent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="type",
            field=models.CharField(
                choices=[
                    ("a", "Article"),
                    ("q", "Question"),
                    ("h", "How to"),
                    ("d", "Discussion"),
                ],
                default="q",
                help_text="Post type",
                max_length=2,
            ),
        ),
    ]