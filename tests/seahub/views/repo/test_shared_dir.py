import os
from django.core.urlresolvers import reverse
from django.test import TestCase

from seahub.share.models import FileShare
from seahub.test_utils import Fixtures

class SharedDirTest(TestCase, Fixtures):
    def setUp(self):
        share_file_info = {
            'username': 'test@test.com',
            'repo_id': self.repo.id,
            'path': '/',
            'password': None,
            'expire_date': None,
        }
        self.fs = FileShare.objects.create_dir_link(**share_file_info)

    def tearDown(self):
        self.remove_repo()

    def test_can_render(self):
        resp = self.client.get(
            reverse('view_shared_dir', args=[self.fs.token])
        )
        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'view_shared_dir.html')

        self.assertContains(resp, '<h2>%s</h2>' % self.repo.name)

        zip_url = 'href="?p=/&dl=1"'
        self.assertContains(resp, zip_url)

    def test_can_download(self):
        dl_url = reverse('view_shared_dir', args=[self.fs.token]) + \
            '?p=/&dl=1'
        resp = self.client.get(dl_url)
        self.assertEqual(302, resp.status_code)
        assert '8082/files/' in resp.get('location')

    def test_view_raw_file_via_shared_dir(self):
        resp = self.client.get(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.file + '&raw=1'
        )

        assert '8082' in resp['location']

class EncryptSharedDirTest(TestCase, Fixtures):
    def setUp(self):
        share_file_info = {
            'username': 'test@test.com',
            'repo_id': self.repo.id,
            'path': '/',
            'password': '12345678',
            'expire_date': None,
        }
        self.fs = FileShare.objects.create_dir_link(**share_file_info)

        self.sub_dir = self.folder
        self.sub_file = self.file
        self.filename= os.path.basename(self.file)

    def tearDown(self):
        self.remove_repo()

    def test_can_render(self):
        resp = self.client.get(
            reverse('view_shared_dir', args=[self.fs.token])
        )
        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'share_access_validation.html')
        self.assertContains(resp, 'Please input the password')

    def test_can_decrypt(self):
        resp = self.client.post(
            reverse('view_shared_dir', args=[self.fs.token]), {
                'password': '12345678'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'view_shared_dir.html')
        self.assertContains(resp, '<h2>%s</h2>' % self.repo.name)

    def test_wrong_password(self):
        resp = self.client.post(
            reverse('view_shared_dir', args=[self.fs.token]), {
                'password': '1234567'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'share_access_validation.html')
        self.assertContains(resp, 'Please enter a correct password')

    def test_can_visit_sub_dir_without_passwd(self):
        resp = self.client.post(
            reverse('view_shared_dir', args=[self.fs.token]), {
                'password': '12345678'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'view_shared_dir.html')
        self.assertContains(resp, '<h2>%s</h2>' % self.repo.name)

        resp = self.client.get(
            reverse('view_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_dir
        )
        self.assertEqual(200, resp.status_code)
        self.assertTemplateNotUsed(resp, 'share_access_validation.html')
        self.assertTemplateUsed(resp, 'view_shared_dir.html')

    def test_view_file_via_shared_dir(self):
        resp = self.client.post(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file, {
                'password': '12345678'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateNotUsed(resp, 'share_access_validation.html')
        self.assertTemplateUsed(resp, 'shared_file_view.html')
        self.assertContains(resp, '%s</h2>' % self.filename)

        resp = self.client.get(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file
        )
        self.assertEqual(200, resp.status_code)
        self.assertTemplateNotUsed(resp, 'share_access_validation.html')
        self.assertTemplateUsed(resp, 'shared_file_view.html')
        self.assertContains(resp, '%s</h2>' % self.filename)

    def test_view_raw_file_via_shared_dir(self):
        resp = self.client.post(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file, {
                'password': '12345678'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateNotUsed(resp, 'share_access_validation.html')
        self.assertTemplateUsed(resp, 'shared_file_view.html')
        self.assertContains(resp, '%s</h2>' % self.filename)

        resp = self.client.get(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file + '&raw=1'
        )

        assert '8082' in resp['location']

    def test_view_file_via_shared_dir_without_password(self):
        resp = self.client.get(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file
        )
        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'share_access_validation.html')

        resp = self.client.post(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file)

        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'share_access_validation.html')

    def test_view_file_via_shared_dir_with_wrong_password(self):
        resp = self.client.post(
            reverse('view_file_via_shared_dir', args=[self.fs.token]) + '?p=' + self.sub_file, {
                'password': '1234567'
            }
        )

        self.assertEqual(200, resp.status_code)
        self.assertTemplateUsed(resp, 'share_access_validation.html')
        self.assertContains(resp, 'Please enter a correct password')
