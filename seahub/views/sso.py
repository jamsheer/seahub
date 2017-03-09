# Copyright (c) 2012-2016 Seafile Ltd.
# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

from seahub import auth
from seahub.base.accounts import User
from seahub.profile.models import Profile
from seahub.utils import render_error

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
    state = request.GET.get('state', '')
    if not code or not state:
        assert False, 'TODO'

    import json
    import urllib
    import urllib2

    url = 'https://test.alphalawyer.cn/ilaw//v2/weixinlogin/weixinLoginCallBackNew'
    values = {
        'code': code,
        'state': state,
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    logger.warn(the_page)
    json_res = json.loads(the_page)

    succeed = json_res['succeed']
    if succeed is True:
        result = json_res['result']
        first = result['first']
        if first is True:
            return render_error(request, u'请先去alpha激活帐号 https://www.alphalawyer.cn')
        else:
            auth_resp_dto = result['authResponseDto']
            res_code = auth_resp_dto.get('resultCode')
            pic = auth_resp_dto.get('pic')
            mail = auth_resp_dto.get('mail')
            # username = auth_resp_dto.get('username')
            name = auth_resp_dto.get('name')
            user_id = auth_resp_dto.get('userId')  # unique
            token = auth_resp_dto.get('token')
            refresh_token = auth_resp_dto.get('refreshToken')

            # create new account if possible
            logger.warn('user id: %s' % user_id)
            assert user_id is not None
            username = user_id + '@ifile.com'

            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                user = None

            if user is None:
                user = User.objects.create_user(email=username, is_active=True)
                user.set_unusable_password()

            if name:
                Profile.objects.add_or_update(username, name)

            request.user = user
            auth.login(request, user)
            return HttpResponseRedirect('/')

    else:
        # login failed
        assert False, '2'




    logger.warn(the_page)

    return HttpResponse('')
