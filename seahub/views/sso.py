# Copyright (c) 2012-2016 Seafile Ltd.
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

def sso(request):
    if getattr(settings, 'ENABLE_SHIB_LOGIN', False):
        return HttpResponseRedirect(request.GET.get("next", reverse('libraries')))

    if getattr(settings, 'ENABLE_KRB5_LOGIN', False):
        return HttpResponseRedirect(request.GET.get("next", reverse('libraries')))

    if getattr(settings, 'ENABLE_ADFS_LOGIN', False):
        return HttpResponseRedirect(reverse('saml2_login'))

def shib_login(request):
    return sso(request)

from django.shortcuts import render_to_response
from django.template import RequestContext

def weixin_login(request):
    return render_to_response('weixin_login.html', {},
                              context_instance=RequestContext(request))

def weixin_login_callback(request):
    assert False, 'TODO'
