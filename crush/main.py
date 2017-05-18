# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2017 <contact@redhat.com>
#
# Author: Loic Dachary <loic@dachary.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import argparse
import collections
import logging
import textwrap

from crush import Crush
from crush import analyze
from crush import compare
from crush import optimize

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')

log = logging.getLogger('crush')


class Main(object):

    def __init__(self):
        self.create_parser()

        if self.parser.get_default('backward_compatibility') is None:
            self.parser.set_defaults(backward_compatibility=False)

        self.parser.add_argument(
            '-v', '--verbose',
            action='store_true', default=None,
            help='be more verbose',
        )

        self.parser.add_argument(
            '--debug',
            action='store_true', default=None,
            help='debugging output, very verbose',
        )

        self.subparsers = self.parser.add_subparsers(
            title='subcommands',
            description='valid subcommands',
            help='sub-command -h',
        )

        analyze.Analyze.set_parser(self.subparsers, self.hook_analyze_args)
        compare.Compare.set_parser(self.subparsers, self.hook_compare_args)
        optimize.Optimize.set_parser(self.subparsers, self.hook_optimize_args)

    def create_parser(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent("""\
            A library to control placement in a hierarchy
            """))

    def __getstate__(self):
        return (self.argv,)

    def __setstate__(self, state):
        self.__init__()
        self.parse(state[0])

    def clone(self):
        raise Exception('not implemented')

    def parse(self, argv):
        self.argv = argv
        self.args = self.parser.parse_args(argv)

        if self.args.debug:
            level = logging.DEBUG
        elif self.args.verbose:
            level = logging.WARNING
        else:
            level = logging.INFO
        if log.getEffectiveLevel() == 0 or log.getEffectiveLevel() > level:
            log.setLevel(level)

    @staticmethod
    def get_trimmed_argv(to_parser, args):
        options = []
        positionals = []
        dest2option = {}
        known_dests = []
        for action in to_parser._actions:
            option = list(filter(lambda o: o in to_parser._option_string_actions,
                                 action.option_strings))
            if len(option) > 0:
                dest2option[action.dest] = option[0]
            known_dests.append(action.dest)
        v = collections.OrderedDict(sorted(vars(args).items(),
                                           key=lambda t: t[0]))
        for (key, value) in v.items():
            log.debug('get_trimmed_argv: checking ' +
                      str(key) + "=" + str(value))
            if key not in known_dests:
                log.debug('get_trimmed_argv: skip unknown ' + str(key))
                continue
            if key in dest2option:
                option = dest2option[key]
                action = to_parser._option_string_actions[option]
                if value != action.default:
                    if action.nargs is None or action.nargs == 1:
                        options.extend([option, str(value)])
                    elif action.nargs == 0:
                        options.append(option)
            else:
                log.debug('get_trimmed_argv: positional ' +
                          str(key) + "=" + str(value))
                positionals.extend(value)
        return options + positionals

    def constructor(self, argv):
        self.parse(argv)
        return self.args.func(self.args, self)

    def main(self, argv):
        return self.constructor(argv).run()

    def hook_analyze_args(self, parser):
        pass

    def hook_compare_args(self, parser):
        pass

    def hook_optimize_args(self, parser):
        pass

    def hook_create_values(self):
        values = range(0, self.args.values_count)
        return dict(zip(values, values))

    def convert_to_crushmap(self, crushmap):
        c = Crush(verbose=self.args.debug,
                  backward_compatibility=self.args.backward_compatibility)
        c.parse(crushmap)
        return c.get_crushmap()

    def crushmap_to_file(self, crushmap):
        c = Crush(verbose=self.args.debug,
                  backward_compatibility=self.args.backward_compatibility)
        c.parse(crushmap)
        c.to_file(self.args.out_path)
