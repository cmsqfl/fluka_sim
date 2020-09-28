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

from string import Template
from fnmatch import fnmatch
import subprocess
from subprocess import Popen
from optparse import OptionParser
import re
import os
import sys
import time

import util as ut

VERSION="""
2.x""".strip()
ut.require_version_match(VERSION)

#template for .sub files       
SUBMIT_TEMPLATE_ = Template("""executable \t\t = CONDORcluster${file_name_noextension}/script_${file_name_noextension}.sh
output \t\t\t = ${file_name_noextension}.$$(ClusterId).$(ProcId).out
error \t\t\t = ${file_name_noextension}.$$(ClusterId).$(ProcId).err
log \t\t\t = ${file_name_noextension}.$$(ClusterId).$(ProcId).log

universe \t\t = vanilla
+JobFlavour \t\t = "${job_flavour}"
initialdir \t\t = ${current_dir}/CONDORcluster${file_name_noextension}
transfer_input_files \t = ${current_dir}/${file_name}, ${current_dir}/${executable}, ${current_dir}/LBQ-KEK.MAP, ${current_dir}/cmssw501.fieldmap

queue""")

#template for .sh file
EXE_SCRIPT_TEMPLATE_ = Template("""#!/bin/bash
set -e
export LX_ORIGIN=${current_dir}
export LX_INPUT_BASE=${input_base}
export LX_INPUT="$${LX_INPUT_BASE}.inp"
export LX_EOS=/afs/cern.ch/project/eos/installation/cms/bin/eos.select
export LX_FLOPTS=
source /cvmfs/sft.cern.ch/lcg/contrib/gcc/9.2.0/x86_64-centos7/setup.sh

# copy input file, custom executable (if any) and FLUPRO over to avoid crashes
# due to AFS being temporarily inaccessible.
# cp "$${LX_ORIGIN}/$${LX_INPUT}" ./
if [[ "${executable}" ]]
then
  export LX_FLOPTS="-e ${executable}"
fi
export FLUPRO=/afs/cern.ch/work/s/stepobr/fluka4-0.1

# begin before hooks
${before}
# end before hooks

$$FLUPRO/bin/rfluka $$LX_FLOPTS -M 1 "$$LX_INPUT" || true

#zip -r "results_$${LX_INPUT_BASE}.zip" *"$${LX_INPUT_BASE}"* *"$${LX_INPUT_BASE}001_fort"* *"ran$${LX_INPUT_BASE}"* fluka_*/

#mv "results_$${LX_INPUT_BASE}.zip" $$LX_ORIGIN
rm "$${LX_INPUT_BASE}001.log*"
rm "$${LX_INPUT_BASE}001.out*"
rm "$${LX_INPUT_BASE}001.err*"
rm "$${LX_INPUT_BASE}001_fort*"
rm "ran$${LX_INPUT_BASE}"*"
cp "*_KAM" /eos/cms/store/user/stepobr/fluka/

# begin after hooks
${after}
# end after hooks
    """)

#template for running locally
BASH_TEMPLATE_ = Template("""
set -e
export LX_ORIGIN=${current_dir}
export LX_INPUT_BASE=${input_base}
export LX_INPUT="$${LX_INPUT_BASE}.inp"
export LX_EOS=/afs/cern.ch/project/eos/installation/cms/bin/eos.select
export LX_FLOPTS=

if [[ "${executable}" ]]
then
  export LX_FLOPTS="-e ${executable}"
fi
export FLUPRO=/afs/cern.ch/work/s/stepobr/fluka4-0.1

# begin before hooks
${before}
# end before hooks

$$FLUPRO/bin/rfluka $$LX_FLOPTS -M 1 "$$LX_INPUT" || true


#zip -r "results_$${LX_INPUT_BASE}.zip" *"$${LX_INPUT_BASE}"* *fort* "ran$${LX_INPUT_BASE}"* fluka_*/
#cp "results_$${LX_INPUT_BASE}.zip" "$${LX_ORIGIN}/"

rm *"$${LX_INPUT_BASE}001_fort"*
rm *"ran$${LX_INPUT_BASE}"*

# begin after hooks
${after}
# end after hooks
    """)

def ensure_seeds_unique(path_prefix, inputs):
    seeds = set(ut.get_seed_from_input(os.path.join(path_prefix, input)) for input in inputs)
    if len(seeds) != len(inputs):
        sys.exit("Duplicate seeds found. Please investigate manually (e.g., grep RANDOMIZ main_input_file_*.inp).")

def process_arguments(path_prefix):
    parser = OptionParser(usage="usage: %prog [options] main_input_file.inp [specific files...]",
                          version="%prog "+VERSION,
                          description="Submit split FLUKA simulation to LXBATCH",
                          epilog=("Unless specific files are specified, the split files "
                                  " are assumed to reside in the current directory and be"
                                  " named main_input_file_<counter>.inp\n"
                                  "The jobs, when complete, will write their results into"
                                  " result files named results_main_input_file_<counter>.zip"))
    parser.add_option("-q", "--run-queue", dest="job_flavour", default="tomorrow",
                      choices="espresso microcentury longlunch workday tomorrow testmatch nextweek".split(),
                      help="submit to run queue QUEUE", metavar="QUEUE")
    parser.add_option("-e", "--executable", dest="executable", default="",
                      help="passed on to rfluka", metavar="FILE")
    parser.add_option("-L", "--run-locally", action="store_true", dest="run_locally",
                      help="run the job locally (for debugging)")
    parser.add_option("--unless-finished", action="store_true", dest="unless_finished",
                      help="run only jobs for which there is not a results file present")
    (options, args) = parser.parse_args()
    
    if len(args) < 1:
        sys.exit(parser.get_usage())

    input_base = re.sub(r'\.inp$', '', args[0])

    if len(args) < 2:
        inputs = ut.find_jobs(path_prefix, input_base)
    else:
        inputs = args[1:]

    return (options, inputs)

re_before_after = re.compile(r"^\*[ ]?#lxbatch\s+(?P<time>before|after)\s+(?P<command>.*)$")
def get_before_after(path_prefix, input):
    commands = {}
    with open(os.path.join(path_prefix, input), "r") as infile:
        for line in infile:
            match = re_before_after.match(line)
            if match:
                commands.setdefault(match.group("time"), []).append(match.group("command"))
    return commands.get("before", []), commands.get("after", [])

def main(path_prefix=os.getcwd()):
    options, inputs = process_arguments(path_prefix)

    if not os.getenv('FLUPRO'):
        sys.exit('FLUPRO environment variable not set')

    warn('directory: %s' % path_prefix)
    warn('FLUPRO: %s' % os.getenv('FLUPRO'))
    warn('Job Flavour: %s' % options.job_flavour)
    warn('inputs (%d):' % len(inputs))

    if not inputs:
        sys.exit('nothing to do.')

    ensure_seeds_unique(path_prefix, inputs)

    #Prepare folders for STDOUT, STDERR, log, .sh files
    for input in inputs:
        foldername = "CONDORcluster"+ut.extensionless_filename(input)
        commandfolder = ['mkdir',] + [foldername]
        Popen(commandfolder, stdin=subprocess.PIPE)

    for input in inputs:
        if options.unless_finished and ut.have_results_for(path_prefix, input):
            warn("not submitting finished job %s" % input)
            continue

        before, after = get_before_after(path_prefix, input)

        extensionless_filename = ut.extensionless_filename(input)
        file_dir = "CONDORcluster" + extensionless_filename
        full_file_dir = os.path.join(path_prefix, file_dir)
        script_name = "script_"+ut.extensionless_filename(input)+".sh"
        submit_name = "submit_"+ut.extensionless_filename(input)+".sub"
                        
        exescript = EXE_SCRIPT_TEMPLATE_.safe_substitute(current_dir=path_prefix,
                                                         input_base=extensionless_filename,
                                                         executable=options.executable,
                                                         flupro=os.getenv('FLUPRO'),
                                                         before="\n".join(before),
                                                         after="\n".join(after))

        subscript = SUBMIT_TEMPLATE_.safe_substitute(file_name_noextension=extensionless_filename,
                                                     job_flavour=options.job_flavour,
                                                     current_dir=path_prefix,
                                                     file_name= input,
                                                     executable=options.executable)
       
        with open(os.path.join(full_file_dir, script_name), "w+") as inscript:
            inscript.write(exescript)

        with open(os.path.join(path_prefix, submit_name), "w+") as insub:
            insub.write(subscript)
 
        warn('\t%s' % input)

        # show the user the commands embedded in the input file, in hopes that
        # they will double-check whether it matches their expectations and does
        # not include malicious code
        
        if before:
            warn("  *#lxbatch before:")
            for s in before:
                warn("    %s" % s)
        if after:
            warn("  *#lxbatch after:")
            for s in after:
                warn("    %s" % s)

        command = ['condor_submit',] + [submit_name]
        
        if options.run_locally:
            bashscript = BASH_TEMPLATE_.safe_substitute(current_dir=path_prefix,
                                                        input_base=extensionless_filename,
                                                        executable=options.executable,
                                                        before="\n".join(before),
                                                        after="\n".join(after))
            warn('running locally, command would have been: %s' % command)
            warn('running locally, script would have been:\n%s' % exescript)
            warn('running locally:')
            command = ['bash']
            process = Popen(command, stdin=subprocess.PIPE)
            process.communicate(bashscript)
        else:
            Popen(command, stdin=subprocess.PIPE)
            
        time.sleep(8)

if __name__ == '__main__':
    main()

