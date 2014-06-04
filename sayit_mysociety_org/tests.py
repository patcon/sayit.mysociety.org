import re
import urlparse

from django.core import mail
from django.contrib.auth import get_user_model

from instances.tests import InstanceTestCase


class ShareInstanceTests(InstanceTestCase):
    def test_share_form_exists(self):
        resp = self.client.get('/instance/share')
        self.assertContains(resp, 'Share your instance', status_code=200)

    def test_share_with_existing_user(self):
        sharee = get_user_model().objects.create_user(
            'sharee', email='sharee@example.com')
        resp = self.client.post('/instance/share',
                                {'email': 'sharee@example.com'})

        self.instance.users.get(pk=sharee.id)
        self.assertRedirects(resp, '/instance/shared', status_code=302)

    def test_share_with_unknown_user(self):
        resp = self.client.post('/instance/share',
                                {'email': 'newsharee@example.com'})

        sharee = get_user_model().objects.get(email='newsharee@example.com')
        self.instance.users.get(pk=sharee.id)
        self.assertRedirects(resp, '/instance/shared', status_code=302)

        invite_message = mail.outbox[0]

        # Verify that the subject of the first message is correct.
        self.assertEqual(
            invite_message.subject,
            '[example.com] You have been invited to SayIt'
            )

        # Get the link out of the invitation email
        link = re.search(r'http://.*/\n', invite_message.body).group(0)
        path = urlparse.urlsplit(link).path

        self.client.logout()
        resp = self.client.get(path)
        self.assertContains(resp, 'Accept invitation')

        resp = self.client.post(
            path,
            {'password1': 'password', 'password2': 'password'},
            )
        self.assertRedirects(resp, '/', status_code=302)

        # Check we can log out and in again with the new credentials
        self.client.logout()
        self.assertTrue(
            self.client.login(
                email='newsharee@example.com', password='password')
            )

    def test_share_with_unknown_user_long_email(self):
        resp = self.client.post(
            '/instance/share',
            {'email': 'what_a_long_email_address@example.com'},
            )

        sharee = get_user_model().objects.get(
            email='what_a_long_email_address@example.com')
        self.instance.users.get(pk=sharee.id)
        self.assertRedirects(resp, '/instance/shared', status_code=302)

        # Verify that the subject of the first message is correct.
        self.assertEqual(
            mail.outbox[0].subject,
            '[example.com] You have been invited to SayIt'
            )