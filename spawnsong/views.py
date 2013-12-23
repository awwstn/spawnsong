from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
import models
import forms

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def authed(request):
    return render_to_response(
        "spawnsong/authed.html",
        context_instance=RequestContext(request))

def frontpage(request):
    return render_to_response(
        "spawnsong/home.html",
        context_instance=RequestContext(request))


def snippet(request, snippet_id):
    snippet = get_object_or_404(
        models.Snippet.objects.visible_to(request.user), pk=snippet_id)
    if request.method == "POST" and request.POST["badger"] == "":
        comment = request.POST["comment"]
        models.Comment.objects.create(user=request.user, snippet=snippet, content=comment, ip_address=get_client_ip(request))
    return render_to_response(
        "spawnsong/snippet.html",
        {
            "snippet": snippet,
            "editable": request.user.is_authenticated() and snippet.song.artist.user == request.user,
            "order_count": snippet.order_count()
        },
        context_instance=RequestContext(request))

@login_required
def upload(request):
    form = forms.UploadSnippetForm()
    if request.method == 'POST':
        form = forms.UploadSnippetForm(request.POST, request.FILES)
        if form.is_valid():
            snippet = form.save(request.user)
            return HttpResponseRedirect(snippet.get_absolute_url())
    else:
        form = forms.UploadSnippetForm()
    return render_to_response(
        "spawnsong/upload.html",
        {
           "form": form 
        },
        context_instance=RequestContext(request))

def user(request, username):
    pass


    
