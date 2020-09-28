import sys
import os
import re
import subprocess
import fnmatch
import numbers
import logging

VERSION="""
2.x""".strip()

def require_version_match(other_version):
    if VERSION != other_version:
        sys.exit("version mismatch; your installation of the LXBATCH scripts may be corrupted")

# FIXED format is assumed for the START and RANDOMIZE cards
CARD_WIDTH = 72
WHAT_WIDTH = 10

def get_WHAT(card, index):
    return card[index*WHAT_WIDTH:(index+1)*WHAT_WIDTH]

def set_WHAT(card, index, value):
    # ensure line long enough
    card = card.ljust(CARD_WIDTH, ' ')
    # format numbers correctly
    if isinstance(value, numbers.Number):
        value = str(float(value))
        if len(value) > WHAT_WIDTH:
            if value.endswith(".0"):
                value = value[:-2]
    if len(value) > WHAT_WIDTH:
        sys.exit("WHAT overflow trying to set WHAT(%i) of '%s' to '%s'" % (index, card.strip(), value))
    value = value.rjust(WHAT_WIDTH, ' ')
    return card[:index*WHAT_WIDTH] + value + card[(index+1)*WHAT_WIDTH:]

REGEX_START    = re.compile(r'^START\b.*$',    flags=re.MULTILINE)
REGEX_RANDOMIZ = re.compile(r'^RANDOMIZ\b.*$', flags=re.MULTILINE)

IWHAT_NPRIMARIES = 1
IWHAT_RANDOMSEED = 2

def set_nprimaries(input, nprimaries):
    return re.sub(REGEX_START, lambda match: set_WHAT(match.group(0), IWHAT_NPRIMARIES, nprimaries), input)

def get_seed(input):
    assume_zero = False
    match = re.search(REGEX_RANDOMIZ, input)
    if match:
        what = get_WHAT(match.group(0), IWHAT_RANDOMSEED)
        try:
            seed = int(float(what))
        except ValueError:
            logging.warning("could not parse random seed '%s' in input file, assuming 0" % what)
            return 0
    else:
        logging.warning("could not find a random seed in input file, assuming 0")
        return 0
    return seed

def set_seed(input, seed):
    input, n = re.subn(REGEX_RANDOMIZ, lambda match: set_WHAT(match.group(0), IWHAT_RANDOMSEED, seed), input)
    if n == 0:
        raise ValueError("no RANDOMIZ card found in the input")
    return input

def get_seed_from_input(path):
    with open(path, 'r') as file:
        contents = file.read()
    return get_seed(contents)

def generate_seeds(base=0):
    seed = base
    while True:
        yield seed
        seed += 1

def generate_identifiers(base="aaaa"):
    a, z = ord('a'), ord('z')
    ks = [ord(c) - a for c in base]
    while True:
        yield ''.join(chr(a+k) for k in ks)
        # increment ks with rollover
        for i in reversed(xrange(len(ks))):
            ks[i] += 1
            if ks[i] > z - a:
                ks[i] = 0
            else:
                break

def get_identifier_from_filename(fn, input_base):
    match = re.match(get_job_filename_regex(input_base), fn)
    return match.group('counter')

def find_jobs(path_prefix, input_base):
    return [fn for fn in os.listdir(path_prefix)
            if get_job_filename_regex(input_base).match(fn)]

def extensionless_filename(fn):
    return os.path.splitext(os.path.basename(fn))[0]

def get_job_filename_regex(input_base):
    return re.compile('%s_(?P<counter>[a-z]{4}).inp' % re.escape(input_base))

# calls an external program and get its output.  like subprocess.check_output,
# but backported.
def check_output(cmd, *args, **kwargs):
    p = subprocess.Popen(cmd, *args, stdout=subprocess.PIPE, **kwargs)
    return p.communicate()[0]

# returns a list of paths of files in the zip with the given name.
def files_in_zip(fn):
    return check_output(('zipinfo', '-1', fn)).splitlines()

# conditions for a file to be relevant
def is_job_result(fn, input_base):
    if not fn.startswith('results_%s_' % input_base):
        return False
    if not fn.endswith('.zip'):
        return False
    if not os.path.isfile(fn):
        return False
    # zips containing a directory matching fluka_* correspond to failed runs
    if any(fnmatch.filter(files_in_zip(fn), 'fluka_*')):
        logging.warning("not processing failed job %s" % fn)
        return False
    return True

def find_job_results(directory, input_base):
    return [fn for fn in os.listdir(directory) if is_job_result(fn, input_base)]

def have_results_for(directory, input):
    return os.path.isfile("results_%s.zip" % extensionless_filename(input))

def query_choice(options, default):
    assert(default in options)
    prompt = "Please enter one of %s (default=%s): " % (options, default)
    while True:
        sys.stdout.write(prompt)
        choice = raw_input().strip().lower()
        if choice == '':
            choice = default
        # ensure unambiguous
        candidates = [option for option in options if option.lower().startswith(choice)]
        if len(candidates) == 1:
            return candidates[0]
