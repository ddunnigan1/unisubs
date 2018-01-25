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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

"""externalsites.syncing.brightcove -- Sync subtitles to/from brightcove"""

import base64, json, requests
import babelsubs
from externalsites.exceptions import SyncingError
from utils.one_time_data import set_one_time_data

import logging
logger = logging.getLogger(__name__)

MEDIA_READ_URL = 'https://api.brightcove.com/services/library'
MEDIA_WRITE_URL = 'https://api.brightcove.com/services/post'

CMS_BASE_URL = 'https://cms.api.brightcove.com/v1'
INGEST_BASE_URL = 'https://ingest.api.brightcove.com/v1'
OAUTH_BASE_URL = 'https://oauth.brightcove.com/v3/access_token'

def _get_cms_token(client_id, client_secret):
    basic_auth = base64.encodestring('%s:%s' % (client_id, client_secret)).replace('\n','')
    headers = {
	'Authorization': 'Basic ' + basic_auth,
	'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    r = requests.post(OAUTH_BASE_URL, headers=headers, data=data)
    if r.status_code != 200:
        raise SyncingError("Error while retrieving CMS token: %s" % r.text)
    return json.loads(r.text)['access_token']

def _make_cms_request(account_id, client_id, client_secret, bc_video_id, language_code, subtitle_version=None):
    access_token = _get_cms_token(client_id, client_secret)
    authentication_header = {"Authorization": "Bearer " + access_token}
    r = requests.get(CMS_BASE_URL + "/accounts/" + account_id + "/videos/" + bc_video_id, headers=authentication_header)
    if r.status_code != 200:
        raise SyncingError("Error while retrieving Brightcove text tracks: %s" % r.text)
    tracks = json.loads(r.text)["text_tracks"]
    new_tracks = []
    for track in tracks:
        if language_code != track['srclang']:
            new_tracks.append(track)
    if len(tracks) != len(new_tracks):
        data_clean = {
            "text_tracks": new_tracks
        }
        r = requests.patch(CMS_BASE_URL + "/accounts/" + account_id + "/videos/" + bc_video_id,
                           headers=authentication_header,
                           data=json.dumps(data_clean))
        if r.status_code != 200:
            raise SyncingError("Error while removing old Brightcove text track: %s" % r.text)
    if subtitle_version is not None:
        subtitle_data = babelsubs.to(subtitle_version.get_subtitles(), "vtt", language=subtitle_version.language_code)
        url = set_one_time_data(subtitle_data)
        label = subtitle_version.get_language_code_display()
        data = {
            "text_tracks": [
                {
                    "url": url,
                    "srclang": language_code,
                    "kind": "captions",
                    "label": label
                }
            ]
        }
        r = requests.post(INGEST_BASE_URL + "/accounts/" + account_id + "/videos/" + bc_video_id + "/ingest-requests",
                          headers=authentication_header,
                          data=json.dumps(data))
        if r.status_code != 200:
            raise SyncingError("Error while adding new Brightcove text track: %s" % r.text)

def update_subtitles_cms(account_id, client_id, client_secret, bc_video_id, subtitle_version):
    _make_cms_request(account_id, client_id, client_secret, bc_video_id, subtitle_version.language_code, subtitle_version)

def delete_subtitles_cms(account_id, client_id, client_secret, bc_video_id, subtitle_language):
    _make_cms_request(account_id, client_id, client_secret, bc_video_id, subtitle_language.language_code)

def _make_write_request(write_token, method, **params):
    file_content = params.pop('file_content', None)
    data = {
        'method': method,
        'params': params,
    }
    data['params']['token'] = write_token

    if file_content is None:
        response = requests.post(MEDIA_WRITE_URL,
                                 data={'json': json.dumps(data) })
    else:
        response = requests.post(MEDIA_WRITE_URL,
                                 data={ 'JSONRPC': json.dumps(data) },
                                 files={ 'file': file_content})

    if not hasattr(response, 'json'):
        raise SyncingError("Invalid response data: %s" % response.content)

    response_data = response.json()
    if response_data.get('error') is not None:
        error = response_data['error']
        try:
            code = error['code']
            msg = error['message']
        except StandardError:
            raise SyncingError("Unknown error")
        else:
            raise SyncingError("%s: %s" % (code, msg))

def update_subtitles(write_token, video_id, video):
    _make_write_request(write_token, 'add_captioning', video_id=video_id,
                        caption_source={ 'displayName': 'Amara Captions', },
                        file_content=video.get_merged_dfxp())

def delete_subtitles(write_token, video_id):
    _make_write_request(write_token, 'delete_captioning', video_id=video_id)
