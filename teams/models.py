from django.db import models
from django.utils.text import slugify

from teams.utils import get_upload_path


class Season(models.Model):
    name = models.CharField(max_length=9)

    def __str__(self):
        return self.name


class Base(models.Model):
    uid = models.CharField(max_length=10, unique=True)
    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=30, unique=True)
    logo = models.ImageField(upload_to=get_upload_path, null=True, blank=True)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__slug = self.slug

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug or self.__slug != self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class Country(Base):
    class Meta:
        verbose_name_plural = 'Countries'


class Competition(Base):
    country = models.ForeignKey(
        to=Country,
        on_delete=models.CASCADE,
        related_name='competitions',
    )
    season = models.ForeignKey(
        to=Season,
        on_delete=models.CASCADE,
        related_name='competitions',
    )


class Team(Base):
    country = models.ForeignKey(
        to=Country,
        on_delete=models.CASCADE,
        related_name='teams',
    )
    competitions = models.ManyToManyField(
        to=Competition,
        related_name='teams',
    )
