from utils.enum import Enum
from django.utils.translation import ugettext_lazy as _

NotificationType = Enum('NotificationType', [
    ('ROLE_CHANGED', _('Role changed')),
    ('TEAM_INVITATION', _('Team invitation')),
    ('NEW_ACTIVE_ASSIGNMENT', _(u'New active assignment')),
    ('REQUEST_UPDATED', _(u'Request updated')),
    ('REQUEST_COMPLETED', _(u'Request completed by team')),
    ('REQUEST_SENDBACK', _(u'Request sent back to team')),
])


__all__ = [
    'NotificationType',
]
