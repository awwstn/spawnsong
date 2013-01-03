from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    return render_to_response(
        "MYAPPNAME/home.html",
        context_instance=RequestContext(request))

@login_required
def authed(request):
    return render_to_response(
        "MYAPPNAME/authed.html",
        context_instance=RequestContext(request))
