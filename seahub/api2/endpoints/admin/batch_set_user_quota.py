# Copyright (c) 2012-2016 Seafile Ltd.

import logging
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.translation import ugettext as _

from seaserv import seafile_api

from seahub.api2.authentication import TokenAuthentication
from seahub.api2.throttling import UserRateThrottle
from seahub.api2.utils import api_error

from seahub.base.accounts import User
from seahub.utils.file_size import get_file_size_unit

logger = logging.getLogger(__name__)

# user fields returned by admin users api
# {
#     "email": "email",
#     "name": "email2nickname(email)",
#     "contact_email": Profile.objects.get_contact_email_by_user(email),
#     "is_admin": True, # False
#     "active": True, # False
#     "role": "default", # guest
#     "quota_total": 100000,
#     "quota_used": 50000,
#     "created_at": "2017-02-23T15:51:21+08:00",
#     "last_login": "2017-02-27T15:51:21+08:00",
# }


class AdminUsersBatch(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    throttle_classes = (UserRateThrottle,)
    permission_classes = (IsAdminUser,)

    def post(self, request):
        """ Set user quota / delete users in batch.

        Permission checking:
        1. admin user.
        """

        # argument check
        emails = request.POST.getlist('email', None)
        if not emails:
            error_msg = 'email invalid.'
            return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

        operation = request.POST.get('operation', None)
        if operation not in ('set-quota', 'delete-user'):
            error_msg = "operation can only be 'set-quota' or 'delete-user'."
            return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

        result = {}
        result['failed'] = []
        result['success'] = []

        existed_users = []
        for email in emails:
            try:
                user = User.objects.get(email=email)
                existed_users.append(user)
            except User.DoesNotExist:
                result['failed'].append({
                    'email': email,
                    'error_msg': 'User %s not found.' % email
                    })
                continue

        if operation == 'set-quota':
            quota_total_mb = request.POST.get('quota_total', None)
            if not quota_total_mb:
                error_msg = 'quota_total invalid.'
                return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

            try:
                quota_total_mb = int(quota_total_mb)
            except ValueError:
                error_msg = _('must be an integer that is greater than or equal to 0.')
                return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

            if quota_total_mb < 0:
                error_msg = _('Space quota is too low (minimum value is 0)')
                return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

            quota_total_byte = quota_total_mb * get_file_size_unit('MB')

            for user in existed_users:
                email = user.email
                try:
                    seafile_api.set_user_quota(email, quota_total_byte)
                except Exception as e:
                    logger.error(e)
                    result['failed'].append({
                        'email': email,
                        'error_msg': 'Internal Server Error'
                        })
                    continue

                result['success'].append({
                    'email': email,
                    'quota_total': seafile_api.get_user_quota(email),
                })

        if operation == 'delete-user':
            for user in existed_users:
                email = user.email
                try:
                    user.delete()
                except Exception as e:
                    logger.error(e)
                    result['failed'].append({
                        'email': email,
                        'error_msg': 'Internal Server Error'
                        })
                    continue

                result['success'].append({
                    'email': email,
                })

        return Response(result)
