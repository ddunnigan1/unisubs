# Amara, universalsubtitles.org
#
# Copyright (C) 2014 Participatory Culture Foundation
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

"""externalsites.credit -- Add Amara credit to video on external sites

Right now the only site we handle is YouTube
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils import translation

from externalsites import google
from externalsites import models
from utils.text import fmt
from videos.models import VideoUrl, VIDEO_TYPE_YOUTUBE
from videos.templatetags.videos_tags import shortlink_for_video

import re

YOUTUBE_AMARA_CREDIT_TEXT = _('Help us caption & translate this video!')

def calc_credit_text(video):
    with translation.override(video.primary_audio_language_code or 'en'):
        return '%s\n\n%s' % (YOUTUBE_AMARA_CREDIT_TEXT,
                             shortlink_for_video(video))

def videourl_has_credit(video_url):
    return models.CreditedVideoUrl.objects.filter(video_url=video_url).exists()

def should_add_credit_to_video_url(video_url, account):
    return (isinstance(account, models.YouTubeAccount) and
            account.type != models.ExternalAccount.TYPE_TEAM)

def should_remove_credit_to_video_url(video_url, account):
    return should_add_credit_to_video_url(video_url, account)

def add_credit_to_video_url(video_url, account):
    """Add credit to a video on an external site

    This method checks if we have an account linked to the site and if so, we
    add credit to the description.  It will only add credit once per video
    URL.
    """
    creditedvideourl, created = models.CreditedVideoUrl.objects.get_or_create(
        video_url=video_url)
    if not created:
        return
    access_token = google.get_new_access_token(account.oauth_refresh_token)
    video_id = video_url.videoid
    credit_text = calc_credit_text(video_url.video)
    current_description = google.get_video_info(video_id).description
    if credit_text not in current_description:
        new_description = '%s\n\n%s' % (current_description, credit_text)
        google.update_video_description(video_id, access_token,
                                        new_description)

def remove_credit_to_video_url(video_url, account):
    if should_remove_credit_to_video_url(video_url, account):
        access_token = google.get_new_access_token(account.oauth_refresh_token)
        video_id = video_url.videoid
        current_description = google.get_video_info(video_id).description

        new_description = current_description.replace(YOUTUBE_AMARA_CREDIT_TEXT + "\n\n", '')

        protocol = getattr(settings, 'DEFAULT_PROTOCOL')
        domain = (settings.HOSTNAME).replace("www.",'')
        empty_short_link = u"{0}://{1}".format(unicode(protocol),
                                                  unicode(domain))
        # r'^v/\w+/$' is the regex for the video shortlink path
        shortlink_regex = re.escape(empty_short_link) + r'\/v\/\w+\/$'
        print("@@@@@@@@@@@")
        print(shortlink_regex)
        new_description = re.sub(shortlink_regex, '', new_description)

        google.update_video_description(video_id, access_token, new_description)

def remove_credit_from_synced_youtube_videos(owner):
    youtube_accounts = models.YouTubeAccount.objects.for_owner(owner)
    for account in youtube_accounts:
        video_urls = VideoUrl.objects.filter(type=VIDEO_TYPE_YOUTUBE,
                               owner_username=account.channel_id)
        for video_url in video_urls:
            remove_credit_to_video_url(video_url, account)
