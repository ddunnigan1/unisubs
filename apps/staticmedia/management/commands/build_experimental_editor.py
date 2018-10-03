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

import datetime
import mimetypes
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import boto3

from staticmedia import bundles

class Command(BaseCommand):
    help = """Upload editor code to s3 as the experimental editor"""

    def handle(self, *args, **options):
        client = boto3.client('s3',
                              aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        self.upload(client, 'editor.js', 'application/javascript')
        self.upload(client, 'editor.css', 'text/css')
        self.upload_static_dir(client, 'images')

    def upload(self, client, bundle_name, mime_type):
        bundle = bundles.get_bundle(bundle_name)
        client.put_object(
            Bucket=settings.STATIC_MEDIA_EXPERIMENTAL_EDITOR_BUCKET,
            Key='experimental/{}/{}'.format(bundle.bundle_type, bundle_name),
            ContentType=bundle.mime_type,
            ACL='private',
            Body=bundle.build_contents())
        print('* {}'.format(bundle_name))

    def upload_static_dir(self, client, subdir):
        directory = os.path.join(settings.STATIC_ROOT, subdir)
        for dirpath, dirs, files in os.walk(directory):
            for filename in files:
                path = os.path.join(dirpath, filename)
                s3_path = os.path.relpath(path, settings.STATIC_ROOT)
                self.upload_static_file(client, path, s3_path)

    def upload_static_file(self, client, path, s3_path):
        put_kwargs = dict(
            Bucket=settings.STATIC_MEDIA_EXPERIMENTAL_EDITOR_BUCKET,
            Key='experimental/{}'.format(s3_path),
            CacheControl='max-age %d' % (3600 * 24 * 365 * 1),
            Expires=datetime.datetime.now() + datetime.timedelta(days=365),
            ACL='private',
            Body=open(path).read())
        content_type, encoding = mimetypes.guess_type(path)
        if content_type:
            put_kwargs['ContentType'] = content_type
        client.put_object(**put_kwargs)
        print('* {}'.format(s3_path))
