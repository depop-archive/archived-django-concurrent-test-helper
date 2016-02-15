from django.db import models


class Semaphore(models.Model):
    locked = models.BooleanField(default=False)
    count = models.PositiveSmallIntegerField(default=0)
