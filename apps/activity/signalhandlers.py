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

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from activity.models import ActivityRecord
from comments.models import Comment
from subtitles.models import SubtitleLanguage
from teams.models import TeamVideo
from teams.signals import video_moved_from_team_to_team
from videos.models import Video
import videos.signals

@receiver(videos.signals.video_added)
def on_video_added(sender, **kwargs):
    ActivityRecord.objects.create_for_video_added(sender)

@receiver(videos.signals.language_changed)
def on_language_changed(sender, **wargs):
    ActivityRecord.objects.filter(video=sender).update(
        video_language_code=sender.primary_audio_language_code)

@receiver(post_save, sender=Comment)
def on_comment_save(instance, created, **kwargs):
    if not created:
        return
    if isinstance(instance.content_object, Video):
        ActivityRecord.objects.create_for_comment(instance.content_object,
                                                  instance)
    elif isinstance(instance.content_object, SubtitleLanguage):
        ActivityRecord.objects.create_for_comment(instance.content_object.video,
                                          instance,
                                          instance.content_object.language_code)

@receiver(post_save, sender=TeamVideo)
def on_team_video_save(instance, created, **kwargs):
    if created:
        ActivityRecord.objects.move_video_records_to_team(instance.video,
                                                          instance.team)

@receiver(pre_delete, sender=TeamVideo)
def on_team_video_delete(instance, **kwargs):
    ActivityRecord.objects.move_video_records_to_team(instance.video, None)

@receiver(video_moved_from_team_to_team)
def on_video_moved_from_team_to_team(destination_team, video, **kwargs):
    ActivityRecord.objects.move_video_records_to_team(video, destination_team)
