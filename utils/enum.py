# Amara, universalsubtitles.org
#
# Copyright (C) 2017 Participatory Culture Foundation
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
utils.enum -- Enum handling
"""

from __future__ import absolute_import

from django.db import models
from south.modelsinspector import add_introspection_rules

RAISE_KEY_ERROR = object()

class EnumMember(object):
    def __init__(self, enum_name, name, label, number):
        self.enum_name = enum_name
        self.name = name
        self.slug = name.lower().replace('_', '-')
        self.label = label
        self.number = number

    def __unicode__(self):
        return unicode(self.label)

    def __repr__(self):
        return "{}.{}".format(self.enum_name, self.name)

    def __eq__(self, other):
        if isinstance(other, EnumMember):
            return self.number == other.number
        elif isinstance(other, basestring):
            return self.slug == other
        elif isinstance(other, (int, long)):
            return self.number == other
        else:
            return False

    def choice(self):
        return (self.number, self.label)

    def slug_choice(self):
        return (self.slug, self.label)

class Enum(object):
    """
    Enum -- Handle Enumerations

    This class solves a common problem:  We want to enumerate a simple set of
    possible values for an attribute, function argument, or something similar.
    For each of those values we want to support several representations:

      - Python object -- for using in code
      - label -- for displaying the value in the UI
      - slug -- for API interactions
      - integer -- for storing in the database

    Args:
        enum_name: Name for the enumeration as a whole.  This should match the
            variable name for enum -- compare to the first argument of
            namedtuple
        members: List of (name, label) pairs for each member value.  name
            should be in UPPER_CASE style.  label should either be unicode, or
            a ugettext_lazy object

    For each member in members, we will create a EnumMember object.  These
    have the following attributes:

        name: variable name of the enum.
        number: 1-based index for the member
        label: human-readable string to display
        slug: machine-friendly string to use for API values, JSON
            representations, etc.

    Enums can be acessed in several ways:
        - Enum.NAME
        - Enum.lookup_slug()
        - Enum.lookup_number()

    Example::

        >>> Flavors = Enum('Flavors', [
        ...     ('VANILLA', u'Vanilla'),
        ...     ('CHOCOLATE', u'Chocolate'),
        ...     ('ROCKY_ROAD', u'Rocky road'),
        ... ])
        >>> Flavors.VANILLA
        Flavors.VANILLA
        >>> Flavors.VANILLA.label
        u'Vanilla'
        >>> Flavors.CHOCOLATE.number
        2
        >>> Flavors.ROCKY_ROAD.slug
        'rocky-road'
        >>> Flavors.lookup_slug('rocky-road')
        Flavors.ROCKY_ROAD
        >>> Flavors.lookup_number(2)
        Flavors.CHOCOLATE
        >>> Flavors.lookup_slug('rocky-road').label
        u'Rocky road'
    """
    def __init__(self, enum_name, members):
        self.enum_name = enum_name
        self.members = []
        self.slug_map = {}
        self.number_map = {}
        for name, label in members:
            self.add_member(name, label)

    def add_member(self, name, label):
        number = len(self.members) + 1
        member = EnumMember(self.enum_name, name, label, number)
        setattr(self, name, member)
        self.slug_map[member.slug] = member
        self.number_map[member.number] = member
        self.members.append(member)

    def lookup_slug(self, slug, default=RAISE_KEY_ERROR):
        if default is RAISE_KEY_ERROR:
            return self.slug_map[slug]
        else:
            return self.slug_map.get(slug, default)

    def lookup_number(self, number, default=RAISE_KEY_ERROR):
        if default is RAISE_KEY_ERROR:
            return self.number_map[number]
        else:
            return self.number_map.get(number, default)

    def choices(self):
        return [member.choice() for member in self]

    def slug_choices(self):
        return [member.slug_choice() for member in self]

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

class EnumField(models.PositiveSmallIntegerField):
    """
    Store enum values in a database field.
    """
    # FIXME: merge this code with codefield.CodeField

    __metaclass__ = models.SubfieldBase

    def __init__(self, enum=None, **kwargs):
        if enum is None:
            # Note, enum=None doesn't really make any sense, but we need to
            # allow it to make south migrations work
            enum = Enum('FakeEnum', [])
        super(EnumField, self).__init__(**kwargs)
        self.enum = enum

    def get_default(self):
        if self.has_default() and isinstance(self.default, EnumMember):
            return self.default.number
        else:
            return super(EnumField, self).get_default()

    @property
    def choices(self):
        return self.enum.choices()

    def value_from_object(self, obj):
        value = getattr(obj, self.attname)
        return value.number if isinstance(value, EnumMember) else value

    @property
    def raw_default(self):
        if isinstance(self.default, EnumMember):
            return self.default.number
        else:
            return self.default

    def db_type(self, connection):
        return 'tinyint UNSIGNED' # 256 values should be enough for our enums

    def contribute_to_class(self, cls, name):
        super(EnumField, self).contribute_to_class(cls, name)
        setattr(cls, '{}_choices'.format(name), self.enum.slug_choices)

    def to_python(self, value):
        if isinstance(value, basestring):
            if value.isdigit():
                return self.enum.lookup_number(int(value))
            else:
                return self.enum.lookup_slug(value)
        elif isinstance(value, (int, long)):
            return self.enum.lookup_number(value)
        else:
            return value

    def get_prep_value(self, value):
        if value is None:
            return None
        elif isinstance(value, (int, long)):
            return value
        elif isinstance(value, basestring):
            return self.enum.lookup_slug(value).number
        else:
            return value.number

add_introspection_rules([
    (
        [EnumField],
        [],
        {
            'default': ['raw_default', {}],
        }
    ),
], [
    "^utils\.enum\.EnumField$",
])
