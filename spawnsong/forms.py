from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
import models


class EditSnippetForm(forms.ModelForm):
    title = forms.CharField(max_length=100)
    image = forms.ImageField(label="Change Image", widget=forms.widgets.FileInput)
    visualisation_effect = forms.ChoiceField(choices=(("pulsate", "Pulsate"), ("none", "None")))

    class Meta:
        model = models.Snippet
        fields = ("title", "image", "visualisation_effect")

class UploadSnippetForm(forms.Form):
    title = forms.CharField(max_length=100)
    audio = forms.FileField()
    image = forms.ImageField()
    visualisation_effect = forms.ChoiceField(choices=(("pulsate", "Pulsate"), ("none", "None")))
    
    def __init__(self, *args, **kwargs):
        super(UploadSnippetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'upload'
        self.helper.form_class = ''
        self.helper.form_method = 'post'
        self.helper.form_action = '.'

        # self.helper.add_input(Submit('submit', 'Submit'))

    def save(self, user):
        artist, _ignore = models.Artist.objects.get_or_create(user=user)
        song = models.Song.objects.create(artist=artist)
        snippet = models.Snippet.objects.create(
            song=song,
            title=self.cleaned_data["title"],
            uploaded_audio=self.cleaned_data["audio"],
            image=self.cleaned_data["image"],
            visualisation_effect=self.cleaned_data["visualisation_effect"])
        snippet.process_uploaded_audio()
        return snippet
