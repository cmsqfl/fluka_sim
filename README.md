# fluka simulation for QFL

How to run on lxplus:
1. Add `lxbatch` and `FLUPRO` to your `.bashrc` profile (modify accordingly)

    `export lxbatch=/afs/cern.ch/work/s/stepobr/lumi/lxbatch-2.x`
    
    `export FLUPRO=/afs/cern.ch/work/s/stepobr/fluka4-0.1`
    
2. Run `./compile.sh` to link fluka user routines to your fluka executable
3. Split your jobs with with `split.py` where 100 is number of primaries per job and 10 is the number of jobs

    `$lxbatch/split.py v37214light.inp 100 10`
4. Submit your jobs to CONDOR with `execute.py` with `$lxbatch/execute.py -e CMSpp -q tomorrow v37214light` the job flavour can be 
espresso = 20 minutes
microcentury = 1 hour
longlunch  = 2 hours
workday = 8 hours
tomorrow = 1 day
testmatch = 3 days
nextweek = 1 week


More info on CERN batch system here:

https://batchdocs.web.cern.ch/

5. Run `make` to get `f2hepmc` executable