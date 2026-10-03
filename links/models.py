from django.db import models

# Create your models here.
class ShortenedURL(models.Model):
    code=models.CharField(max_length=32, unique=True)
    url=models.URLField(max_length=2000)
    created_at=models.DateTimeField(auto_now_add=True)
    expiration_date=models.DateTimeField(null=True, blank=True)

class Click(models.Model):
    shorter_url=models.ForeignKey(ShortenedURL, on_delete=models.CASCADE, related_name='clicks')
    clicked_at=models.DateTimeField(auto_now_add=True)
    client_info=models.TextField(blank=True,default='')
    referring_url=models.TextField(blank=True,default='')