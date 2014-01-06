from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Count
from django.db import transaction
import models
import forms
import json
from django.db.models import Q
import simplejson
import stripe
import urllib
import logging
from django.conf import settings
from registration.backends.simple.views import RegistrationView as SimpleRegistrationView

logger = logging.getLogger(__name__)

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
    snippets = models.Snippet.objects.visible_to(request.user).filter(state="published")
    return render_to_response(
        "spawnsong/frontpage.html",
        {
           "snippets": snippets
        },
        context_instance=RequestContext(request))

def _snippet_details_json(snippet):
    snippet_details = {
        "beats": snippet.beat_locations(),
        "title": snippet.title,
        "price": snippet.price,
        "visualisation_effect": snippet.visualisation_effect,
    };
    # JSON will be inserted into the HTML template, so need the
    # special encode to get rid of "</script>" in strings
    return simplejson.dumps(
        snippet_details,
        cls=simplejson.encoder.JSONEncoderForHTML)
    

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
        
    editable = request.user.is_authenticated() and snippet.song.artist.user == request.user,
    # edit mode is for editing the metadata
    edit_mode = editable and ("edit" in request.GET or snippet.state == "ready")
    deleteable = not models.Order.objects.filter(song=snippet.song).exists()
    if edit_mode:
        if request.method == "POST":
            if "delete" in request.POST and not deleteable:
                snippet.delete()
                return HttpResponseRedirect("/")
            form = forms.EditSnippetForm(request.POST, request.FILES, instance=snippet)
            if form.is_valid():
                form.save()
                if "publish" in request.POST:
                    snippet.publish()
                return HttpResponseRedirect(snippet.get_absolute_url())
        else:
            form = forms.EditSnippetForm(instance=snippet)
    else:
        form = None
        # Has a comment been posted?
        if request.method == "POST" and request.POST["badger"] == "":
            comment = request.POST["comment"]
            models.Comment.objects.create(user=request.user, snippet=snippet, content=comment, ip_address=get_client_ip(request))

                                    
    return render_to_response(
        "spawnsong/snippet.html",
        {
            "snippet_details_json": _snippet_details_json(snippet),
            "snippet": snippet,
            "editable": editable,
            "deleteable": deleteable,
            "edit_mode": edit_mode,
            "edit_form": form,
            "order_count": snippet.order_count(),
            "paymentsuccess": "paymentsuccess" in request.GET,
            "paymenterror": request.GET.get("paymenterror", None)
        },
        context_instance=RequestContext(request))

@login_required
def upload_full(request, snippet_id):
    snippet = get_object_or_404(
        models.Snippet.objects.visible_to(request.user), pk=snippet_id, song__artist__user=request.user)
    song = snippet.song
    uploaded = snippet.is_complete()
    if request.method == "POST":
        form = forms.UploadCompleteSongForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            song.queue_delivery()
            uploaded = True
    else:
        form = forms.UploadCompleteSongForm(instance=song)

    return render_to_response(
        "spawnsong/upload_full.html",
        {
            "uploaded": uploaded,
            "snippet_details_json": _snippet_details_json(snippet),
            "snippet": snippet,
            "form": form
        },
        context_instance=RequestContext(request))

def download_full(request, order_id, email, token):
    order = get_object_or_404(models.Order, pk=order_id, purchaser_email=email, security_token=token)
    # print "Going to get dowload url", order.song.get_download_url()
    return HttpResponseRedirect(order.song.get_download_url())

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
    snippets = models.Snippet.objects.visible_to(request.user).filter(song__artist=artist).select_related('song').filter(Q(state="published") | Q(state="ready"))
    return render_to_response(
        "spawnsong/user.html",
        {
           "artist": artist,
           "user": artist.user,
           "snippets": snippets
        },
        context_instance=RequestContext(request))

def purchase(request):
    token = request.POST["token"]
    email = request.POST["email"]
    snippet_id = request.POST["snippet_id"]
    snippet = get_object_or_404(models.Snippet, pk=snippet_id)

    if models.Order.objects.filter(purchaser_email=email, song=snippet.song).exists():
        return HttpResponseRedirect(snippet.get_absolute_url() + "?paymenterror=" + urllib.quote("You have already purchased this song!"))
        

    # First authorize the charge on the card with stripe
    try:
        charge = stripe.Charge.create(
            amount=snippet.price,
            currency=settings.CURRENCY,
            capture=False,
            card=token,
            description="Pre-order of '%s' (id %s) by %s" % (snippet.title, snippet.id, snippet.song.artist.get_display_name())
            )
    except stripe.CardError, e:
        logger.info("Card declined for %s buying %s" % (email,snippet.id))
        return HttpResponseRedirect(snippet.get_absolute_url() + "?paymenterror=" + urllib.quote("Sorry, your card has been declined"))
    except:
        logger.exception("Failed to process card")
        return HttpResponseRedirect(snippet.get_absolute_url() + "?paymenterror=" + urllib.quote("Sorry, there was an error processing your card"))

    try:
        with transaction.atomic():
            # Next create the order object in our db
            order = models.Order.objects.create(
                song=snippet.song, 
                purchaser=request.user if request.user.is_authenticated() else None,
                purchaser_email=email,
                price=snippet.price,
                stripe_transaction_id=charge.id)

            order.maybe_queue_delivery()

            # Capture the charge (actually charge the user)
            charge = charge.capture(amount=snippet.price)
            
            return HttpResponseRedirect(snippet.get_absolute_url() + "?paymentsuccess")
    except:
        logger.exception("Failed to capture charge")
        return HttpResponseRedirect(snippet.get_absolute_url() + "?paymenterror=" + urllib.quote("Sorry, there was an error processing your card"))

class RegistrationView(SimpleRegistrationView):
    def get_success_url(self, request, user):
        return ('/', (), {})
