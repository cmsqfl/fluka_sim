#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
FOCUS - FLUKA for CMS Users | PH-CMX-DS | BRIL Radiation Simulation
European Organization for Nuclear Research (CERN)

authors: Slawomir Tadeja (2013)
         Tim Cooijmans (2014)

contact:
http://hypernews.cern.ch/HyperNews/CMS/get/bril-radiation-simulation.html
"""

from __future__ import print_function
def warn(*objs):
    print(*objs, file=sys.stderr)

import string
import numbers
import itertools as it
import re
import os
import sys
import shutil
import tempfile
from optparse import OptionParser
import util as ut
import traceback

VERSION="""
2.x""".strip()
ut.require_version_match(VERSION)

DEFAULT_NPRIMARIES = 100
DEFAULT_NSPLITS = 10

RE_ITERATE = re.compile(r"^\*[ ]?#lxbatch\s+iterate\s+(?P<path>\S+)\s*$", flags=re.MULTILINE)

def prepare_card_iterators(contents):
    iterators = {}
    for match in RE_ITERATE.finditer(contents):
        path = match.group("path")
        if path in iterators:
            raise RuntimeError("path %s used more than once in *#lxbatch iterate directive" % path)
        iterators[path] = open(path, "r")
    warn("importing cards from files: %s" % iterators.keys())
    return iterators

def insert_iterated_cards(contents, iterators):
    def iterated_card(match):
        path = match.group("path")
        try:
            return iterators[path].next()
        except StopIteration:
            raise RuntimeError("not enough cards in %s" % path)
    return RE_ITERATE.sub(iterated_card, contents)

def make_copies(path_prefix, undoers, input_base, identifiers, seeds, nprimaries):
    with open(os.path.join(path_prefix, "%s.inp" % input_base), 'r') as file:
        contents = file.read()
    contents = ut.set_nprimaries(contents, nprimaries)
    card_iterators = prepare_card_iterators(contents)
    for seed, identifier in zip(seeds, identifiers):
        contents2 = contents
        contents2 = insert_iterated_cards(contents2, card_iterators)
        contents2 = ut.set_seed(contents2, seed)
        output = '%s_%s.inp' % (input_base, identifier)
        warn(output)
        path = os.path.join(path_prefix, output)
        with open(path, 'w') as file:
            file.write(contents2)
        undoers.append(lambda: os.remove(path))

def process_arguments():
    parser = OptionParser(usage="usage: %prog main_input_file.inp [NPRIMARIES [NSPLITS]]",
                          version="%prog "+VERSION,
                          description="Split FLUKA simulation into jobs for submission to LXBATCH",
                          epilog=("NPRIMARIES specifies the number of primaries to simulate "
                                  "in each job; NSPLITS specifies the number of jobs to create. "
                                  "The jobs get consecutive random seeds counting up from the"
                                  "seed found in main_input_file.inp."))
    (options, args) = parser.parse_args()

    if len(args) < 1:
        sys.exit(parser.get_usage())

    input_base = re.sub(r'\.inp$', '', args[0])

    nprimaries = int(args[1]) if len(args) > 1 else DEFAULT_NPRIMARIES
    nsplits    = int(args[2]) if len(args) > 2 else DEFAULT_NSPLITS

    return (input_base, nprimaries, nsplits, options)

def prepare_replace(path_prefix, undoers, input_base, existing_jobs):
    if existing_jobs:
        tempdir = tempfile.mkdtemp(prefix="split_replaced_", dir=path_prefix)
        warn("moving old jobs into %s..." % tempdir)
        for path in existing_jobs:
            shutil.move(path, tempdir)
        def undoer():
            for path in existing_jobs:
                shutil.move(os.path.join(tempdir, os.path.basename(path)), path_prefix)
            os.rmdir(tempdir)
        undoers.append(undoer)

    seed_base = ut.get_seed_from_input(os.path.join(path_prefix, "%s.inp" % input_base))

    identifiers = ut.generate_identifiers()
    seeds = ut.generate_seeds(seed_base)

    return (identifiers, seeds)

def prepare_union(path_prefix, undoers, input_base, existing_jobs, identifier_base):
    max_used_seed = max(ut.get_seed_from_input(path) for path in existing_jobs)
    seed_base = ut.get_seed_from_input(os.path.join(path_prefix, "%s.inp" % input_base))
    seed_base = max(seed_base, max_used_seed + 1)

    identifiers = it.islice(ut.generate_identifiers(identifier_base), 1, None)
    seeds = ut.generate_seeds(seed_base)

    return (identifiers, seeds)

def main(undoers, path_prefix=os.getcwd()):
    input_base, nprimaries, nsplits, options = process_arguments()

    warn('splitting %s.inp into %i jobs simulating %i primaries each' % (input_base, nsplits, nprimaries))

    existing_jobs = sorted(ut.find_jobs(path_prefix, input_base))
    if existing_jobs:
        warn("Possible leftovers from a previous split were found:")
        for path in existing_jobs:
            warn("\t%s" % path)

        identifier_base = ut.get_identifier_from_filename(sorted(existing_jobs)[-1], input_base)

        warn("Possible leftovers from a previous split were found.  Do you want to replace "
             "this set with the new set of jobs, or do you want the union of the two sets?\n\n"
             "(In the former case, the files listed above will be moved out of the way to "
             "a subdirectory.  In the latter case, the files will stay and the newly "
             " generated files will be named counting up from \"%s\".)" % identifier_base)
        choice = ut.query_choice("replace union".split(), "replace")

        if choice == "replace":
            identifiers, seeds = prepare_replace(path_prefix, undoers, input_base, existing_jobs)
        elif choice == "union":
            identifiers, seeds = prepare_union(path_prefix, undoers, input_base, existing_jobs, identifier_base)
    else:
        identifiers, seeds = prepare_replace(path_prefix, undoers, input_base, [])

    identifiers = it.islice(identifiers, 0, nsplits)
    seeds       = it.islice(seeds,       0, nsplits)
    make_copies(path_prefix, undoers, input_base, identifiers, seeds, nprimaries)

if __name__ == '__main__':
    undoers = []
    try:
        main(undoers)
    except Exception:
        warn("an error occurred; reverting filesystem state...")
        try:
            for undoer in reversed(undoers):
                undoer()
        except:
            warn("an error occurred while trying to revert filesystem state.")
            raise
        raise
