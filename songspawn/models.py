# Initial model outline, not tested yet

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
import datetime

class Artist(models.Model):
    artist = models.OneToOneField(Artist)
    
class Song(models.Model):
    """
    A song that a snippet comes from.

    In phase 1 each song has only one snippet, they're split out so we
    can add features later
    """
    artist = models.ForeignKey(Artist)
    
    created_at = models.DateTimeField(default=datetime.datetime.now)
    
    # TODO: Needs to be uploaded to a protected location. Maybe just
    # use a CharField with an S3 location in it?
    complete_audio = models.FieldField(null=True)
    completed_at = models.DateTimeField(null=True, help_text="The time at which the completed audio file was uploaded")
    
class Snippet(models.Model):
    """
    A snippet of a song on the site
    """
    song = models.ForeignKey(Song)
    title = models.CharField(max_length=255)
    state = models.CharField(max_length=20, choices=(("processing", "Processing"), ("ready", "Ready"), ("published", "Published")), default="processing")

    created_at = models.DateTimeField(default=datetime.datetime.now)

    image = models.ImageField(upload_to="snippets/images")
    audio = models.FieldField(upload_to="snippets/audio", null=True)
    echonest_data = models.JSONField(blank=True, help_text="Data received from Echonest about the snippet, used to find the beat locations for the visualisation")

    visualisation_effect = models.CharField(max_length=20, choices=(("pulsate", "Pulsate"), ("none", "None")), default="pulsate")
    
    def markReady(self, commit=True):
       assert self.state == "processing" 
       assert self.audio is not None, "Audio should be present before the snippet is marked as ready"
       self.state = "ready"
       if commit:
           self.save()
           
    def publish(self, commit=True):
       assert self.state == "ready" 
       self.state = "published"
       if commit:
           self.save()

    @property
    def price(self):
        return settings.SONG_PRICE
    
class Order(models.Model):
    "A pre-order or order for a song"
    song = models.ForeignKey(Song)
    purchaser = models.ForeignKey(User)
    price = models.IntegerField(help_text="Purchase price in cents")
    refunded = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=datetime.datetime.now)

    stripe_transaction_id = models.CharField(max_length=255)

class ArtistPayment(models.Model):
    "A payment that the system caluclated is owed to an artist"
    arist = models.ForeignKey(Artist)
    orders = models.ManyToManyField(Order)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    paid = models.BooleanField(default=False)

class Comment(models.Model):
    """
    A comment on a snippet.
    """
    user = models.ForeignKey(User)
    snippet = models.ForeignKey(Snippet)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    content = models.TextField()
    ip_address = models.GenericIPAddressField(_('IP address'), unpack_ipv4=True, blank=True, null=True)

    is_displayed = models.BooleanField(default=True)
    
