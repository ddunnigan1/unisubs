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

from optparse import make_option

from django.core.management.base import BaseCommand

from utils import tasks

class Command(BaseCommand):
    help = u'Run a test task'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--number', default=1,
                            type=int, help='Number of tasks to run')
        parser.add_argument('-d', '--delay', default=None,
                            type=int, help='Seconds to delay the execution')
        parser.add_argument('-f', '--fail', action='store_true',
                            help='Simulate an exception')

    def handle(self, **options):
        if options['fail']:
            job_func = tasks.test_failure
        else:
            job_func = tasks.test
        for i in range(options['number']):
            if options['delay'] is None:
                job = job_func.delay()
            else:
                job = job_func.enqueue_in(options['delay'])
            print 'Job: {}'.format(job.id)
