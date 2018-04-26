# Amara, universalsubtitles.org
# 
# Copyright (C) 2012 Participatory Culture Foundation
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

import re
import urllib

from base import VideoType, VideoTypeError
from django.conf import settings
from django.utils.html import strip_tags

# wistia.WISTIA_API_KEY = getattr(settings, 'WISTIA_API_KEY')
# wistia.WISTIA_API_SECRET = getattr(settings, 'WISTIA_API_SECRET')

WISTIA_REGEX = re.compile(r'https?://(.+)?(wistia\.com|wi\.st|wistia\.net)/(medias|embed/iframe)/(?P<video_id>\w+)')
WISTIA_OEMBED_API_URL = 'http://fast.wistia.com/oembed?embedType=seo&url='

class WistiaVideoType(VideoType):

    abbreviation = 'W'
    name = 'Wistia.com'   
    site = 'wistia.com'
    linkurl = None

    def __init__(self, url):
        self.url = url
        self.videoid = self._get_wistia_id(url)
        # not sure why this is being done, it breaks external URL
        self.linkurl = url.replace('/embed/', '/medias/')
        try:
            self.shortmem = get_shortmem(url)
        except:
            # we're not raising an error here because it 
            # disallows us from adding private Wistia videos.
            pass
        
    @property
    def video_id(self):
        return self.videoid
    
    def convert_to_video_url(self):
        return "https://fast.wistia.net/embed/iframe/%s" % self.videoid

    @classmethod
    def matches_video_url(cls, url):
        return bool(WISTIA_REGEX.match(url))

    def set_values(self, video_obj, user, team, video_url):
        try:
            video_obj.thumbnail = get_thumbnail_url(self.url, self.shortmem) or ''
            video_obj.small_thumbnail = get_small_thumbnail_url(self.url, self.shortmem) or ''
            video_obj.title = scrape_title(self.url, self.shortmem)
            video_obj.description = strip_tags(scrape_description(self.url, self.shortmem))
        except Exception:
            # in case the Wistia video is private.
            pass
    
    def _get_wistia_id(self, video_url):
        return WISTIA_REGEX.match(video_url).groupdict().get('video_id')

def get_shortmem(url):
    shortmem = {}
    video_id = WISTIA_REGEX.match(url).groupdict()['video_id']
    apiurl = '%s?%s' % (WISTIA_OEMBED_API_URL, urllib.quote(url))
    finalexcept = None

    backoff = random_exponential_backoff(2)

    for i in range(3):
        try:
            reponse = urllib.urlopen(apiurl)
            api_raw_data = response.read()
            api_data = json.loads(api_raw_data)
        except Exception as e:
            finalexcept = e
            continue
        else:
            shortmem['oembed'] = api_data
            break

        backoff.next()

    if 'oembed' in shortmem:
        return shortmem

    errmsg = u'Wistia API error : '
    if finalexcept is not None:
        """if isinstance(finalexcept, urllib.HTTPError):
            errmsg += finalexcept.code + " - " + HTTPResponseMessages[ finalexcept.code ][0]
        elif isinstance(finalexcept, urllib.URLError):
            errmsg += "Could not connect - " + finalexcept.reason
        else:"""
        errmsg += str(finalexcept)
    else:
        errmsg += u' Unrecognized error. Sorry about that, chief.'

    return None

def random_exponential_backoff(denominator):
    i = 1.0
    while True:
        sleep_range = (i ** 2) / denominator
        sleep_time = random.uniform(0, sleep_range)
        time.sleep(sleep_time)
        i += 1
        yield sleep_time

def parse_api(scraper_func, shortmem=None):
    def new_scraper_func(url, shortmem={}, *args, **kwargs):
        if not shortmem:
            shortmem = get_shortmem(url)
        return scraper_func(url, shortmem=shortmem, *args, **kwargs)
    return new_scraper_func

def returns_unicode(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        result = scraper_func(url, shortmem=shortmem, *args, **kwargs)

        if result is not None:
            if not isinstance(result, unicode):
                if shortmem and shortmem.has_key('base_etree'):
                    encoding = shortmem['base_etree'].docinfo.encoding
                else:
                    encoding = 'utf8'
                return result.decode(encoding)
            elif isinstance(result, _ElementUnicodeResult):
                return unicode(result)
            else:
                return result

    return new_scraper_func

@parse_api
@returns_unicode
def scrape_title(url, shortmem={}):
    try:
        return shortmem['oembed']['title'] or u''
    except KeyError:
        return u''

@parse_api
@returns_unicode
def scrape_description(url, shortmem={}):
    try:
        description = shortmem['oembed']['title'] # No desc provided in oembed. Use title.
    except KeyError:
        description = ''
    return util.clean_description_html(description)

@parse_api
@returns_unicode
def get_thumbnail_url(url, shortmem={}):
    return shortmem['oembed']['thumbnail_url']

@parse_api
@returns_unicode
def get_duration(url, shortmem={}):
    return shortmem['oembed']['duration']
