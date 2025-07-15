from django.db import models

# Create your models here.



class User(models.Model):
    tg_id = models.BigIntegerField(unique=True)  # Telegram ID
    first_name = models.CharField(max_length=255, blank=True, null=True)
    
class ChannelsToSubscribe(models.Model):
    link = models.CharField(max_length=255)
    name= models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.link

    class Meta:
        db_table = 'bot_user'
        verbose_name = "Channel to Subscribe"
        verbose_name_plural = "Channels to Subscribe"