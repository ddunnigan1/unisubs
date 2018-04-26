# Amara, universalsubtitles.org
#
# Copyright (C) 2016 Participatory Culture Foundation
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

"""utils.frontend -- frontend-related classes

This module contains a few utility classes that's used by the view code.
"""

from __future__ import absolute_import

from datetime import timedelta

from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

from utils.dates import now
from utils.text import fmt

SECONDS_IN_A_DAY = 60.0 * 60.0 * 24.0

def date(dt):
    """Format a date."""
    return u'{}/{}/{}'.format(dt.month, dt.day, dt.year)

def elapsed_time(when):
    """
    Format the amount of time that has passed

    Args:
        when (datetime/timedelta): time to display.  If this is a
            datetime, then we will display the time between now and it.  If
            it's a timedelta, then we use that directly
    """
    if isinstance(when, timedelta):
        delta = when
        dt = now() - timedelta
    else:
        delta = now() - when
        dt = when
    if delta.days < 0:
        return _('now')
    elif delta.days < 1:
        if delta.seconds < 60:
            return _('now')
        elif delta.seconds < 60 * 60:
            minutes = int(round(delta.seconds / 60.0))
            return fmt(ungettext(u'%(count)s minute ago',
                                 u'%(count)s minutes ago',
                                 minutes),
                       count=minutes)
        else:
            hours = int(round(delta.seconds / 60.0 / 60.0))
            return fmt(ungettext(u'%(count)s hours ago',
                                 u'%(count)s hours ago',
                                 hours),
                       count=hours)
    elif delta.days < 7:
        days = int(round(delta.days + delta.seconds / SECONDS_IN_A_DAY))
        return fmt(ungettext('%(count)s day ago',
                             '%(count)s days ago',
                             days), count=days)
    else:
        return date(dt)

def datetime(when):
    if isinstance(when, timedelta):
        dt = now() - timedelta
    else:
        dt = when
    if dt is None:
        return ''
    return dt.strftime("%b %-d, %Y, %-I:%M %p")

def due_date(deadline, when, hypothetical=False):
    """Get text to display a due date

    Args:
        deadline (unicode): name of the thing that's due ("request",
            "assignment", etc)
        when (datetime/timedelta): time to display.  If this is a
            datetime, then we will display the time between now and it.  If
            it's a timedelta, then we use that directly
        hypothetical: Use for a hypothetical due date.  We will display "would
            be due" instead of "due"
    """
    if isinstance(when, timedelta):
        delta = when
        dt = now() + when
    else:
        delta = when - now()
        dt = when
    if delta.days < 0:
        count = None
        if hypothetical:
            msg = _('%(deadline)s would be due now')
        else:
            msg = _('%(deadline)s due now')
    elif delta.days < 1:
        if delta.seconds < 60:
            count = None
            if hypothetical:
                msg = _('%(deadline)s would be due now')
            else:
                msg = _('%(deadline)s due now')
        elif delta.seconds < 60 * 60:
            count = int(round(delta.seconds / 60.0))
            if hypothetical:
                msg = ungettext(u'%(deadline)s would be due in %(count)s minute',
                                u'%(deadline)s would be due in %(count)s minutes',
                                count)
            else:
                msg = ungettext(u'%(deadline)s due in %(count)s minute',
                                u'%(deadline)s due in %(count)s minutes',
                                count)
        else:
            count = int(round(delta.seconds / 60.0 / 60.0))
            if hypothetical:
                msg = ungettext(u'%(deadline)s would be due in %(count)s hours',
                                u'%(deadline)s would be due in %(count)s hours',
                                count)
            else:
                msg = ungettext(u'%(deadline)s due in %(count)s hours',
                                u'%(deadline)s due in %(count)s hours',
                                count)
    elif delta.days < 7:
        count = int(round(delta.days + delta.seconds / SECONDS_IN_A_DAY))
        if hypothetical:
            msg = ungettext('%(deadline)s would be due in %(count)s day',
                            '%(deadline)s would be due in %(count)s days',
                            count)
        else:
            msg = ungettext('%(deadline)s due in %(count)s day',
                            '%(deadline)s due in %(count)s days',
                        count)
    else:
        count = None
        if hypothetical:
            msg = _(u'%(deadline)s would be due %(date)s')
        else:
            msg = _(u'%(deadline)s due %(date)s')
    # Note: We're not sure where the deadline label will end up in the final
    # string, so we lowercase it, interplate the string, then capitalize the
    # whole thing.
    msg = fmt(msg, deadline=deadline.lower(), count=count, date=date(dt))
    return msg.capitalize()

__all__ = [
    'date', 'elapsed_time', 'due_date',
]
