# Copyright (c) 2012-2016 Seafile Ltd.
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

# Get an instance of a logger
logger = logging.getLogger(__name__)

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
    code = request.GET.get('code', '')
    status = request.GET.get('status', '')
    if not code or not status:
        assert False, 'TODO'

    import urllib
    import urllib2

    url = 'https://alphalawyer.cn/ilaw//v2/weixinlogin/weixinLoginCallBackNew'
    values = {
        'code string': '6a929ae024564ae79b9bcbccdf21cc3e',
        'status string': '1488945821079',
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()

    logger.warn(the_page)
