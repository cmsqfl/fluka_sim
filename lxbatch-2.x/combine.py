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

import sys
import os
import re
import subprocess
import shutil
import tempfile
import fnmatch
from glob import glob
from optparse import OptionParser
import util as ut

VERSION="""
2.x""".strip()
ut.require_version_match(VERSION)

# map from scoring designators to combiner executables
COMBINERS = dict(
    usrtrack='ustsuw',
    usrcoll='ustsuw',
    usrbdx='usxsuw',
    usryield='usysuw',
    usrbin='usbsuw',
    resnucle='usrsuw',
    )
    
def read_scorings(stream):
    if stream == sys.stdin:
        warn("reading scorings from stdin...")
    scorings = {}
    for line in stream:
        line = line.strip()
        # ignore empty lines
        if not line:
            continue
        extension, scoring = line.split()
        scorings[extension] = scoring.lower()
    return scorings

# call the combiner executable.  fluka's combiners use an ad-hoc interface;
# input files are presented on stdin, each path on a line by itself, followed
# by an empty line and finally the path to the output file.
def combine(scoring, infiles, outfile, flupro):
    combiner = os.path.join(flupro, 'flutil', COMBINERS[scoring])
    warn('input files: %s' % infiles)
    warn('output file: %s' % outfile)
    warn('combiner: %s' % combiner)
    pipe = subprocess.Popen(combiner, stdin=subprocess.PIPE)
    pipe.communicate('%s\n\n%s\n' % ('\n'.join(infiles), outfile))

def process_arguments():
    parser = OptionParser(usage="usage: %prog main_input_file.inp scorings_file",
                          version="%prog "+VERSION,
                          description="Submit split FLUKA simulation to LXBATCH",
                          epilog=("Combines FLUKA results from split jobs using the "
                                  "appropriate combiners.  Processes ZIP files in the "
                                  "current directory named main_input_file_<counter>.zip"
                                  "\n\n"
                                  "The desired FLUKA outputs and their interpretation "
                                  "are read from scorings_file.  For example,"
                                  "\n"
                                  "\t$ cat scorings"
                                  "\t31 USRBIN"
                                  "\t21 USRBDX"
                                  "\t22 USRBDX"
                                  "\t$ combine.py main_input_file.inp scorings"
                                  "\n"
                                  "will treat the *_fort.31 (respectively *_fort.21, "
                                  "*_fort.22) files found in the ZIP files as USRBIN "
                                  "(USRBDX, USRBDX) files, combining them using the "
                                  "'usbsuw' ('usxsuw', 'ustsuw') tool."
                                  "\n\n"
                                  "Results will be output to files in the current "
                                  "directory."))
    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        sys.exit(parser.get_usage())

    input_base = re.sub(r'\.inp$', '', args[0])
    scorings_filename = args[1]
    
    return (input_base, scorings_filename, options)

def main():
    input_base, scorings_filename, options = process_arguments()

    directory = os.getcwd()
    flupro = os.getenv('FLUPRO')

    if not flupro:
        sys.exit('FLUPRO environment variable not set')

    warn('directory: %s' % directory)
    warn('user: %s' % os.getenv('LOGNAME'))
    warn('FLUPRO: %s' % flupro)

    zips = ut.find_job_results(directory, input_base)
    warn('zip files to process: %s' % zips)

    with open(scorings_filename, 'r') as scorings_file:
        scorings = read_scorings(scorings_file)
    warn('scorings: %s' % scorings)
    
    if not zips or not scorings:
        sys.exit('nothing to do.')
        
    # process each type of file one by one to minimize space usage.
    for extension in scorings:
        # unzip to temporary directory (in current directory to stay on same device)
        tempdir = os.path.basename(tempfile.mkdtemp(dir=directory))
        try:
            for zip in zips:
                # there will be duplicates in these zips when the execution was
                # done locally; on lxplus we get a brand new working directory
                # for each job.
                subprocess.call(('unzip', '-q', zip, '*fort.%s' % extension, '-d', tempdir))
            infiles = glob(os.path.join(tempdir, '*'))
            outfile = '%s_%s_%s' % (input_base, scorings[extension], extension)
            combine(scorings[extension], infiles, outfile, flupro)
        finally:
            shutil.rmtree(tempdir)

if __name__ == '__main__':
    main()
