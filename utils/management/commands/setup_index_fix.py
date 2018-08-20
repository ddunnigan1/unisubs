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

"""
Fix the setup index code situation

With south, we ran this command setup_indexes to setup indexes that django
didn't handle natively.

With django migrations, we can make this command a regular migration.

The issue is that for production/staging/dev, the SQL code has already run,
but the migration isn't logged in the system.

The other issue is that when we first created the indexes, we needed to make
them MyISAM tables.  But now that we're using a newer mysql version, we can
use InnoDB like all the other tables.  The last issue is that the setup
indexes code removed the foreign key constraint from videos_videoindex to
videos_video.

This command fixes all the above issues.

After running this command, the videos_videoindex table should look like this:


CREATE TABLE `videos_videoindex` (
  `video_id` int(11) NOT NULL,
  `text` longtext CHARACTER SET utf8 COLLATE utf8_unicode_ci,
  PRIMARY KEY (`video_id`),
  FULLTEXT KEY `ft_text` (`text`),
  CONSTRAINT `videos_videoindex_video_id_3142f0647972eaeb_fk_videos_video_id` FOREIGN KEY (`video_id`) REFERENCES `videos_video` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = "Adds indexes that have to be defined with raw SQL commands"
    def handle(self, **options):
        call_command('migrate', 'videos', fake=True)
        cursor = connection.cursor()
        cursor.execute(
            'ALTER TABLE videos_videoindex ADD CONSTRAINT '
            'videos_videoindex_video_id_3142f0647972eaeb_fk_videos_video_id '
            'FOREIGN KEY (`video_id`) REFERENCES `videos_video` (`id`)')
