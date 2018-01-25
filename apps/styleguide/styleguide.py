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

from collections import namedtuple
import os

from django.conf import settings
from django.template.loader import render_to_string
from markdown import markdown
import pykss
import yaml

CSS_ROOT = os.path.join(settings.PROJECT_ROOT, 'amara-assets/scss/')
TOC_PATH = os.path.join(CSS_ROOT, 'styleguide-toc.yml')

# Single example in a section
StyleGuideExample = namedtuple('StyleGuideExample', 'source styles')
# TOC item that refers to a single section
StyleGuideTOCItem = namedtuple('StyleGuideTOCItem', 'title section_id')
# TOC item that refers to a list of subitems
StyleGuideTOCList= namedtuple('StyleGuideTOCList', 'title children')

class StyleGuideSection(object):
    """Hanndle 1 section of the style guide.

    This class wraps the pykss Section class to provide the things we use in
    our styleguide HTML.
    """
    def __init__(self, pykss_section):
        self.setup_id(pykss_section)
        self.setup_title_description(pykss_section)
        self.setup_examples(pykss_section)
        self.render_content()

    def setup_id(self, pykss_section):
        self.id = 'section-' + pykss_section.section.replace('.', '-')

    def setup_title_description(self, pykss_section):
        if '\n' in pykss_section.description:
            title, description = pykss_section.description.split('\n', 1)
        else:
            title = pykss_section.description
            description = ''
        self.title = title.strip()
        self.description = markdown(description.strip())

    def setup_examples(self, pykss_section):
        self.examples = [
            StyleGuideExample(example.template, example.styles)
            for example in pykss_section.examples
        ]

    def render_content(self):
        self.content = render_to_string('styleguide/section.html', {
            'title': self.title,
            'description': self.description,
            'examples': self.examples,
        })

class StyleGuide(object):
    def __init__(self):
        self.pykss_parser = pykss.Parser(CSS_ROOT)
        self.sections = []
        self.walk_toc_file()

    def parse_toc_file(self):
        with open(TOC_PATH) as f:
            return yaml.load(f)

    def walk_toc_file(self):
        self.toc_parts = []
        self.toc_parts.append('<ul>')
        for node in self.parse_toc_file():
            self.toc_parts.append('<li>')
            self.walk_toc_node(node)
            self.toc_parts.append('</li>')
        self.toc_parts.append('</ul>')
        self.toc = ''.join(self.toc_parts)

    def walk_toc_node(self, node):
        if isinstance(node, list):
            # Handle a list of TOC items
            self.toc_parts.append(node[0])
            self.toc_parts.append('<ul>')
            for child in node[1:]:
                self.toc_parts.append('<li>')
                self.walk_toc_node(child)
                self.toc_parts.append('</li>')
            self.toc_parts.append('</ul>')
        else:
            # Handle a single TOC item
            section = StyleGuideSection(self.pykss_parser.sections[node])
            self.sections.append(section)
            link = ('<a class="styleGuide-navLink" href="#{id}">'
                    '{title}</a></li>').format(id=section.id,
                                               title=section.title)
            self.toc_parts.append(link)
