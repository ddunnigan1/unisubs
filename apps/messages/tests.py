# -*- coding: utf-8 -*-
# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.
import datetime
from django.core import mail
from django.urls import reverse
from django.test import TestCase

from auth.models import CustomUser as User, EmailConfirmation
from messages.models import Message
from subtitles import models as sub_models
from subtitles.pipeline import add_subtitles
from teams import tasks as team_tasks
from teams.forms import InviteForm
from teams.models import (
    Team, TeamMember, Application, Workflow, TeamVideo, Task, Setting, Invite,
    Application
)
from teams.moderation_const import WAITING_MODERATION
from utils import send_templated_email
from utils.factories import *
from videos.models import Video
from videos.tasks import video_changed_tasks
import messages.tasks

class MessageTest(TestCase):
    def setUp(self):
        self.author = UserFactory()
        self.subject = "Let's talk"
        self.body = "Will you please help me out with Portuguese trans?"
        self.user = UserFactory()
        mail.outbox = []


    def _create_message(self, to_user, message_type='M', reply_to=None):
        self.message = Message(user=to_user,
                           author=self.author,
                           subject=self.subject,
                           message_type=message_type,
                           content=self.body)
        if reply_to is not None:
            if reply_to.thread:
                self.message.thread = reply_to.thread
            else:
                self.message.thread = reply_to.pk
        self.message.save()
        return self.message

    def _send_email(self, to_user):
        send_templated_email(to_user, "test email", "messages/email/email-confirmed.html", {})

    def test_message_cleanup(self):
        self._create_message(self.user)
        self.assertEquals(Message.objects.filter(user=self.user).count(), 1)
        Message.objects.cleanup(0)
        self.assertEquals(Message.objects.filter(user=self.user).count(), 0)
        self._create_message(self.user)
        self.assertEquals(Message.objects.filter(user=self.user).count(), 1)
        Message.objects.filter(user=self.user).update(created=datetime.datetime.now() - datetime.timedelta(days=5))
        Message.objects.cleanup(6)
        self.assertEquals(Message.objects.filter(user=self.user).count(), 1)
        Message.objects.cleanup(4, message_type='S')
        self.assertEquals(Message.objects.filter(user=self.user).count(), 1)
        Message.objects.cleanup(4, message_type='M')
        self.assertEquals(Message.objects.filter(user=self.user).count(), 0)

    def test_message_threads(self):
        m = self._create_message(self.user)
        self._create_message(self.user, reply_to=m)
        self._create_message(self.user, reply_to=m)
        n = self._create_message(self.user, reply_to=m)
        n = self._create_message(self.user, reply_to=n)
        n = self._create_message(self.user, reply_to=n)
        self._create_message(self.user)
        self._create_message(self.user)
        self.assertEquals(Message.objects.thread(n, self.user).count(), 6)
        self.assertEquals(Message.objects.thread(m, self.user).count(), 6)

    def test_previous_message_in_thread(self):
        m = self._create_message(self.user)
        n = self._create_message(self.user, reply_to=m)
        o = self._create_message(self.user, reply_to=n)
        p = self._create_message(self.user, reply_to=m)
        q = self._create_message(self.user, reply_to=n)
        self._create_message(self.user)
        self._create_message(self.user)
        self.assertEquals(Message.objects.previous_in_thread(m, self.user), None)
        self.assertEquals(Message.objects.previous_in_thread(n, self.user), m)
        self.assertEquals(Message.objects.previous_in_thread(o, self.user), n)
        self.assertEquals(Message.objects.previous_in_thread(p, self.user), o)
        self.assertEquals(Message.objects.previous_in_thread(q, self.user), p)

    def test_thread_tips(self):
        m = self._create_message(self.user)
        n = self._create_message(self.user, reply_to=m)
        o = self._create_message(self.user, reply_to=n)
        self.assertEquals(Message.objects.thread(o, self.user).count(), 3)
        self.assertEquals(Message.objects.for_user(self.user).count(), 3)
        self.assertEquals(Message.objects.for_user(self.user, thread_tip_only=True).count(), 1)
        self.assertEquals(Message.objects.for_author(m.author, thread_tip_only=True).count(), 1)
        self.assertEquals(Message.objects.get(id=m.id).has_reply_for_author, True)
        self.assertEquals(Message.objects.get(id=n.id).has_reply_for_author, True)
        self.assertEquals(Message.objects.get(id=o.id).has_reply_for_author, False)
        self.assertEquals(Message.objects.get(id=m.id).has_reply_for_user, True)
        self.assertEquals(Message.objects.get(id=n.id).has_reply_for_user, True)
        self.assertEquals(Message.objects.get(id=o.id).has_reply_for_user, False)
        o.delete_for_user(o.user)
        self.assertEquals(Message.objects.get(id=n.id).has_reply_for_user, False)
        p = self._create_message(self.user)
        self.assertEquals(Message.objects.for_user(self.user, thread_tip_only=True).count(), 2)
        
    def test_send_email_to_allowed_user(self):
        self.user.notify_by_email = True
        self.user.save()
        assert self.user.is_active and self.user.email

        self._send_email(self.user)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_to_optout_user(self):
        self.user.notify_by_email = False
        self.user.save()
        assert self.user.is_active and self.user.email

        self._send_email(self.user)
        self.assertEquals(len(mail.outbox), 0)

    def test_message_to_optout_user(self):
        self.user.notify_by_message = False
        self.user.notify_by_email = False
        self.user.save()
        self._send_email(self.user)
        self._create_message(self.user)
        self.assertEquals(len(mail.outbox), 0)
        self.assertEquals(Message.objects.unread().filter(user=self.user).count(), 0)
        self.assertEquals(Message.objects.filter(user=self.user).count(), 1)

    def test_member_join(self):
        def _get_counts(member):
            email_to = "%s" %( member.user.email)
            return Message.objects.filter(user=member.user).count() , \
                len([x for x in mail.outbox if email_to in x.recipients()])


        team , created= Team.objects.get_or_create(name='test', slug='test')
        # creates dummy users:
        for x in xrange(0,5):
            user = UserFactory(
                username="test%s" % x,
                email = "test%s@example.com" % x,
            )
            tm = TeamMember(team=team, user=user)
            if x == 0:
                tm.role = TeamMember.ROLE_OWNER
                owner = tm
            elif x == 1:
                tm.role = TeamMember.ROLE_ADMIN
                admin = tm
            elif x == 2:
                tm.role = TeamMember.ROLE_MANAGER
                manager = tm
            elif x == 3:
                tm.role = TeamMember.ROLE_CONTRIBUTOR
                contributor = tm
            if x < 4:
                # don't save the last role until we have counts
                tm.save()
            else:
                tm.role= TeamMember.ROLE_CONTRIBUTOR

        # now make sure we count previsou messages
        owner_messge_count_1, owner_email_count_1 = _get_counts(owner)
        admin_messge_count_1, admin_email_count_1 = _get_counts(admin)
        manager_messge_count_1, manager_email_count_1 = _get_counts(manager)
        contributor_messge_count_1, contributor_email_count_1 = _get_counts(contributor)
        # save the last team member and check that each group has appropriate counts
        tm.save()
        messages.tasks.team_member_new(tm.pk)
        # owner and admins should receive email + message
        owner_messge_count_2, owner_email_count_2 = _get_counts(owner)
        self.assertEqual(owner_messge_count_1 + 1, owner_messge_count_2)
        self.assertEqual(owner_email_count_1 + 1, owner_email_count_2)
        admin_messge_count_2, admin_email_count_2 = _get_counts(admin)
        self.assertEqual(admin_messge_count_1 + 1, admin_messge_count_2)
        self.assertEqual(admin_email_count_1 + 1, admin_email_count_2)
        # manager shoud not
        manager_messge_count_2, manager_email_count_2 = _get_counts(manager)
        self.assertEqual(manager_messge_count_1 , manager_messge_count_2)
        self.assertEqual(manager_email_count_1 , manager_email_count_2)
        # contributor shoud not
        contributor_messge_count_2, contributor_email_count_2 = _get_counts(contributor)
        self.assertEqual(contributor_messge_count_1 , contributor_messge_count_2)
        self.assertEqual(contributor_email_count_1 , contributor_email_count_2)

    def test_application_new(self):
        def _get_counts(member):
            email_to = "%s" %(member.user.email)
            return Message.objects.filter(user=member.user).count() , \
                len([x for x in mail.outbox if email_to in x.recipients()])


        team , created= Team.objects.get_or_create(name='test', slug='test')
        applying_user = UserFactory()
        # creates dummy users:
        for x in xrange(0,4):
            user = UserFactory(
                username="test%s" % x,
                email = "test%s@example.com" % x,
                notify_by_email = True,
                notify_by_message = True,
            )
            tm = TeamMember(team=team, user=user)
            if x == 0:
                tm.role = TeamMember.ROLE_OWNER
                owner = tm
            elif x == 1:
                tm.role = TeamMember.ROLE_ADMIN
                admin = tm
            elif x == 2:
                tm.role = TeamMember.ROLE_MANAGER
                manager = tm
            elif x == 3:
                tm.role = TeamMember.ROLE_CONTRIBUTOR
                contributor = tm
            tm.save()

        # now make sure we count previsou messages
        owner_messge_count_1, owner_email_count_1 = _get_counts(owner)
        admin_messge_count_1, admin_email_count_1 = _get_counts(admin)
        manager_messge_count_1, manager_email_count_1 = _get_counts(manager)
        contributor_messge_count_1, contributor_email_count_1 = _get_counts(contributor)

        # now delete and check numers
        app = Application.objects.create(team=team,user=applying_user)
        app.save()
        messages.tasks.application_sent.run(app.pk)
        # owner and admins should receive email + message
        owner_messge_count_2, owner_email_count_2 = _get_counts(owner)
        self.assertEqual(owner_messge_count_1 + 1, owner_messge_count_2)
        self.assertEqual(owner_email_count_1 + 1, owner_email_count_2)
        admin_messge_count_2, admin_email_count_2 = _get_counts(admin)
        self.assertEqual(admin_messge_count_1 + 1, admin_messge_count_2)
        self.assertEqual(admin_email_count_1 + 1, admin_email_count_2)
        # manager shoud not
        manager_messge_count_2, manager_email_count_2 = _get_counts(manager)
        self.assertEqual(manager_messge_count_1 , manager_messge_count_2)
        self.assertEqual(manager_email_count_1 , manager_email_count_2)
        # contributor shoud not
        contributor_messge_count_2, contributor_email_count_2 = _get_counts(contributor)
        self.assertEqual(contributor_messge_count_1 , contributor_messge_count_2)
        self.assertEqual(contributor_email_count_1 , contributor_email_count_2)


    def test_account_verified(self):
       user = UserFactory(notify_by_email=True)
       c = EmailConfirmation.objects.send_confirmation(user)
       num_emails = len(mail.outbox)
       num_messages = Message.objects.filter(user=user).count()
       EmailConfirmation.objects.confirm_email(c.confirmation_key)
       self.assertEqual(num_emails +1, len(mail.outbox))
       self.assertEqual(num_messages +1,
                        Message.objects.filter(user=user).count())

    def test_team_inviation_sent(self):
        team = TeamFactory(name='test', slug='test')
        owner = TeamMemberFactory(team=team, role=TeamMember.ROLE_OWNER)
        applying_user = UserFactory()
        applying_user.notify_by_email = True
        applying_user.save()
        mail.outbox = []
        message = "Will you be my valentine?"
        f = InviteForm(user=owner.user, team=team,data={
            'username': applying_user.username,
            "role":"admin",
            "message": message,
        })
        f.is_valid()
        f.save()
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn(applying_user.email, msg.to[0] )
        self.assertIn(message, msg.body, )

    def test_send_message_view(self):
        to_user = UserFactory()
        user = UserFactory(username='username')
        user.notify_by_email = True
        user.set_password('username')
        user.save()
        mail.outbox = []
        self.client.login(username='username', password='username')
        self.client.post(reverse('messages:new'), {"user":to_user.pk, "subject": "hey", 'content':'test'})
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertTrue(to_user.email in m.to)


    def test_messages_remain_after_team_membership(self):
        # Here's the scenario:
        # User is invited to a team
        # - User accepts invitation
        # - Message for the invitation gets deleted -> wrong!
        user = UserFactory(notify_by_message=True)
        owner = UserFactory(notify_by_message=True)
        team = Team.objects.create(name='test-team', slug='test-team', membership_policy=Team.APPLICATION)

        invite_form = InviteForm(team, owner, {
            'username': user.username,
            'message': 'Subtitle ALL the things!',
            'role':'contributor',
        })
        invite_form.is_valid()
        self.assertFalse(invite_form.errors)
        self.assertEquals(Message.objects.for_user(user).count(), 0)
        invite = invite_form.save()
        # user has the invitation message on their inbox now
        self.assertEquals(Message.objects.for_user(user).count(), 1)
        invite_message = Message.objects.for_user(user)[0]
        # now user accepts invite
        invite.accept()
        # he should be a team memebr
        self.assertTrue(team.members.filter(user=user).exists())
        # message should be still on their inbos
        self.assertIn(invite_message, Message.objects.for_user(user))


class TeamBlockSettingsTest(TestCase):
    def test_block_settings_for_team(self):
        team = TeamFactory()

        owner = UserFactory(
            notify_by_email=True,
            notify_by_message=True)
        TeamMemberFactory(team=team, user=owner,
                          role=TeamMember.ROLE_OWNER)

        user = UserFactory(notify_by_email=True)
        member = TeamMemberFactory(team=team, user=user)

        team_video = TeamVideoFactory(team=team)
        video = team_video.video

        invite = Invite.objects.create(team=team, user=user, author=owner)

        task_assigned = Task.objects.create(team=team, team_video=team_video,
                                            type=10, assignee=member.user)

        subs = [
            (0, 1000, 'Hello', {}),
            (2000, 5000, 'world.', {})
        ]
        sv = add_subtitles(video, 'en', subs)
        task_with_version = Task.objects.create(team=team,
                                                team_video=team_video,
                                                type=10,
                                                assignee=member.user,
                                                new_subtitle_version=sv,
                                                language='en')

        to_test = (
            ("block_invitation_sent_message",
             messages.tasks.team_invitation_sent,
             (invite.pk,)),

            ("block_application_sent_message",
             messages.tasks.application_sent,
             (Application.objects.get_or_create(team=team, note='', user=user)[0].pk,)),

            ("block_application_denided_message",
             messages.tasks.team_application_denied,
             (Application.objects.get_or_create(team=team, note='', user=user)[0].pk,)),

            ("block_team_member_new_message",
             messages.tasks.team_member_new,
             (member.pk, )),

            ("block_team_member_leave_message",
             messages.tasks.team_member_leave,
             (team.pk,member.user.pk )),

            ("block_task_assigned_message",
             messages.tasks.team_task_assigned,
             (task_assigned.pk,)),

            ("block_reviewed_and_published_message",
             messages.tasks.reviewed_and_published,
             (task_with_version.pk,)),

            ("block_reviewed_and_pending_approval_message",
             messages.tasks.reviewed_and_pending_approval,
             (task_with_version.pk,)),
            
            ("block_reviewed_and_sent_back_message",
             messages.tasks.reviewed_and_sent_back,
             (task_with_version.pk,)),

            ("block_approved_message",
             messages.tasks.approved_notification,
             (task_with_version.pk,)),

        )
        for setting_name, function, args in to_test:
            team.settings.all().delete()
            Message.objects.all().delete()
            if setting_name == 'block_application_sent_message':
                pass
            function.run(*args)
            self.assertTrue(Message.objects.count() > 0,
                "%s is off, so this message should be sent" % setting_name)
            Setting.objects.create(team=team, key=Setting.KEY_IDS[setting_name])
            Message.objects.all().delete()
            function.run(*args)
            self.assertEquals(Message.objects.all().count(), 0,
                "%s is on, so this message should *not * be sent" % setting_name)

        # add videos notification is a bit different
        setting_name = "block_new_video_message"
        Setting.objects.create(team=team, key=Setting.KEY_IDS[setting_name])
        team_tasks.add_videos_notification_daily()
        self.assertEquals(Message.objects.all().count(), 0,
            "%s is on, so this message should *not * be sent" % setting_name)
