from utils.enum import Enum
from django.utils.translation import ugettext_lazy as _

NotificationType = Enum('NotificationType', [
    ('ROLE_CHANGED', _('Role changed')),
    ('TEAM_INVITATION', _('Team invitation')),
    ('NEW_ACTIVE_ASSIGNMENT', _(u'New active assignment')),
    ('REQUEST_UPDATED', _(u'Request updated')),
    ('REQUEST_COMPLETED', _(u'Request completed by team')),
    ('REQUEST_SENDBACK', _(u'Request sent back to team')),
    ('AVAILABLE_ASSIGNMENTS_TRANSCRIPTION',
     _(u'Transcription assignment available')),
    ('AVAILABLE_ASSIGNMENTS_TRANSLATION',
     _(u'Translation assignment available')),
    ('AVAILABLE_ASSIGNMENTS_REVIEW', _(u'Review assignment available')),
    ('AVAILABLE_ASSIGNMENTS_APPROVAL', _(u'Approval assignment available')),
    ('AVAILABLE_ASSIGNMENTS_EVALUATION', _(u'Evaluation assignment available')),
])


__all__ = [
    'NotificationType',
]
