from django.core.management.base import BaseCommand
from django.db import connection

import optionalapps

class Command(BaseCommand):
    help = "Adds indexes that have to be defined with raw SQL commands"
    def handle(self, **options):
        cursor = connection.cursor()
        self.setup_videourl_index(cursor)
        self.setup_video_fulltext_index(cursor)
        self.setup_user_collation(cursor)
        optionalapps.exec_repository_scripts('setup_indexes.py',
                                             globals(), locals())

    def setup_videourl_index(self, cursor):
        cursor.execute('ALTER TABLE videos_videourl '
                       'ADD INDEX url_prefix (url(255))')

    def setup_video_fulltext_index(self, cursor):
        # Setup a fulltext index on the text column for VideoIndex.  We need
        # to do a few things here:
        #   - Drop foreign keys
        #   - Switch to a MyISAM table
        #   - Use a case-insensitive collation
        #   - Add the actual index

        cursor.execute('SELECT constraint_name '
                       'FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE '
                       'WHERE table_name="videos_videoindex" AND '
                       'referenced_table_name IS NOT NULL')
        for row in cursor.fetchall():
            cursor.execute('ALTER TABLE videos_videoindex '
                           'DROP FOREIGN KEY `{}`'.format(row[0]))
        cursor.execute('ALTER TABLE videos_videoindex ENGINE=MyISAM')
        cursor.execute('ALTER TABLE videos_videoindex '
                       'ADD FULLTEXT INDEX ft_text (text)')
        cursor.execute('ALTER TABLE videos_videoindex '
                       'MODIFY text LONGTEXT '
                       'CHARACTER SET utf8 COLLATE utf8_unicode_ci')

    def setup_user_collation(self, cursor):
        cursor.execute('ALTER TABLE auth_user MODIFY first_name varchar(30) '
                       'CHARACTER SET utf8 COLLATE utf8_general_ci')
        cursor.execute('ALTER TABLE auth_user MODIFY last_name varchar(30) '
                       'CHARACTER SET utf8 COLLATE utf8_general_ci')
