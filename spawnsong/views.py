from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Count
import models
import forms
import json

class JsonResponse(HttpResponse):
    """
    JSON response
    """
    def __init__(self, content, mimetype='application/json', status=None, content_type=None):
        super(JsonResponse, self).__init__(
            content=json.dumps(content),
            mimetype=mimetype,
            status=status,
            content_type=content_type,
        )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def frontpage(request):
    snippets = models.Snippet.objects.visible_to(request.user)
    return render_to_response(
        "spawnsong/frontpage.html",
        {
           "snippets": snippets
        },
        context_instance=RequestContext(request))


def snippet(request, snippet_id):
    snippet = get_object_or_404(
        models.Snippet.objects.visible_to(request.user), pk=snippet_id)
    if snippet.state == "processing" or snippet.state == "processing_error":
        return render_to_response(
            "spawnsong/processing_upload.html",
            {
                "snippet": snippet
            },
            context_instance=RequestContext(request))
    if request.method == "POST" and request.POST["badger"] == "":
        comment = request.POST["comment"]
        models.Comment.objects.create(user=request.user, snippet=snippet, content=comment, ip_address=get_client_ip(request))
    return render_to_response(
        "spawnsong/snippet.html",
        {
            "beats_json": json.dumps(snippet.beat_locations()),
            "snippet": snippet,
            "editable": request.user.is_authenticated() and snippet.song.artist.user == request.user,
            "order_count": snippet.order_count()
        },
        context_instance=RequestContext(request))

@login_required
def upload(request):
    # Requests are sometimes the result of a normal form post and
    # sometimes the result of a XHR request
    form = forms.UploadSnippetForm()
    is_xhr = 'xhr' in request.POST
    if request.method == 'POST':
        print (request.POST, request.FILES)
        form = forms.UploadSnippetForm(request.POST, request.FILES)
        if form.is_valid():
            snippet = form.save(request.user)
            if is_xhr:
                return JsonResponse({"redirectTo": snippet.get_absolute_url()})
            else:
                return HttpResponseRedirect(snippet.get_absolute_url())
    else:
        form = forms.UploadSnippetForm()
    html = loader.render_to_string(
        "spawnsong/upload.html",
        {
           "form": form 
        },
        context_instance=RequestContext(request))
    if is_xhr:
        return JsonResponse({"html": html})
    else:
        return HttpResponse(html)

def user(request, username):
    artist = get_object_or_404(models.Artist, user__username=username)
    snippets = models.Snippet.objects.visible_to(request.user).filter(song__artist=artist).select_related('song')
    return render_to_response(
        "spawnsong/user.html",
        {
           "artist": artist,
           "user": artist.user,
           "snippets": snippets
        },
        context_instance=RequestContext(request))


    
