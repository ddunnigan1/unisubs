# Amara, universalsubtitles.org
#
# Copyright (C) 2018 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from django.db import models

from .const import NotificationType
from auth.models import CustomUser as User
from utils import dates
from utils.enum import EnumField

class LastSentNotification(models.Model):
    user = models.ForeignKey(User)
    type = EnumField(NotificationType)
    datetime = models.DateTimeField()

    class Meta:
        unique_together = [
            ('user', 'type'),
        ]

    @classmethod
    def update(cls, notification_type, user):
        cls.objects.update_or_create(
            type=notification_type, user=user,
            defaults={ 'datetime': dates.now() })

