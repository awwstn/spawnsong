from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
import models
from mutagen.mp3 import MP3, HeaderNotFoundError, InvalidMPEGHeader
from django.conf import settings
import os
import re

# Based on http://stackoverflow.com/a/5785711/65130
class MP3FileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        self.max_file_size = kwargs.pop('max_file_size', None)
        self.max_audio_length = kwargs.pop('max_audio_length', None)
        self.max_audio_length_display = kwargs.pop('max_audio_length_display', self.max_audio_length)
        super(MP3FileField, self).__init__(*args, **kwargs)
    
    def clean(self, tmp_file, initial=None):
        super(MP3FileField, self).clean(tmp_file, initial)
    
        if self.max_file_size and tmp_file.size > self.max_file_size:
            raise forms.ValidationError("File is too large.")
    
        file_path = os.path.join(settings.FILE_UPLOAD_TEMP_DIR,tmp_file.name)
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in tmp_file.chunks():
                    destination.write(chunk)
            audio = MP3(file_path)
    
            if self.max_audio_length and audio.info.length > self.max_audio_length:
                raise forms.ValidationError("Maximum length for audio is %d seconds (%d seconds uploaded)" % (self.max_audio_length_display,audio.info.length))
        except (HeaderNotFoundError, InvalidMPEGHeader):
            raise forms.ValidationError("File is not valid MP3 CBR/VBR format.")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
            tmp_file.seek(0)
        return tmp_file

# Used in both edit and upload forms
def _clean_genres(self):
    return " ".join("#" + genre.strip() for genre in re.split(r"(?:#|,|\s| )+", self.cleaned_data["genres"]) if genre.strip())

class EditSnippetForm(forms.ModelForm):
    title = forms.CharField(max_length=100)
    image = forms.ImageField(label="Change Image", widget=forms.widgets.FileInput)
    visualisation_effect = forms.ChoiceField(choices=(("pulsate", "Pulsate"), ("none", "None")))
    genres = forms.CharField(max_length=255, help_text="eg #hip-hop #electronic", required=False)

    clean_genres = _clean_genres

    class Meta:
        model = models.Snippet
        fields = ("title", "image", "genres", "visualisation_effect")

class UploadCompleteSongForm(forms.ModelForm):
    complete_audio = MP3FileField(label="Upload Complete Song", widget=forms.widgets.FileInput, max_file_size=settings.FULL_SONG_FILESIZE_LIMIT)

    class Meta:
        model = models.Song
        fields = ("complete_audio",)
        
class UploadSnippetForm(forms.Form):
    title = forms.CharField(max_length=100)
    audio = MP3FileField(label="Upload %ss Snippet" % (settings.SNIPPET_LENGTH_LIMIT,), widget=forms.widgets.FileInput, max_audio_length=settings.SNIPPET_LENGTH_LIMIT+1, max_audio_length_display=settings.SNIPPET_LENGTH_LIMIT)
    image = forms.ImageField()
    visualisation_effect = forms.ChoiceField(choices=(("pulsate", "Pulsate"), ("none", "None")))
    genres = forms.CharField(max_length=255, help_text="eg #hip-hop #electronic", required=False)
    
    def __init__(self, *args, **kwargs):
        super(UploadSnippetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'upload'
        self.helper.form_class = ''
        self.helper.form_method = 'post'
        self.helper.form_action = '.'

        # self.helper.add_input(Submit('submit', 'Submit'))

    clean_genres = _clean_genres

    def save(self, user):
        artist, _ignore = models.Artist.objects.get_or_create(user=user)
        song = models.Song.objects.create(artist=artist)
        snippet = models.Snippet.objects.create(
            song=song,
            title=self.cleaned_data["title"],
            uploaded_audio=self.cleaned_data["audio"],
            genres=self.cleaned_data["genres"],
            image=self.cleaned_data["image"],
            visualisation_effect=self.cleaned_data["visualisation_effect"])
        snippet.process_uploaded_audio()
        return snippet
