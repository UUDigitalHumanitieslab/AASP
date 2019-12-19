from django.db import models

class AASPItem(models.Model):
    speaker = models.CharField(max_length=100)
    item_id = models.CharField(max_length=100)
    wav_file = models.FileField()
    text_grid_file = models.FileField()
