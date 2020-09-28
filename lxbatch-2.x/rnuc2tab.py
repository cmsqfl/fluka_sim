#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

from __future__ import print_function
def warn(*objs):
    print(*objs, file=sys.stderr)
import sys
import os
import re
from glob import glob
from optparse import OptionParser
import numpy
from string import Template


#Template for LaTeX table
LaTemplate = Template("""\\begin{tabular}{l|c|c|c}
     \hline
     \hline

     Region          & \multicolumn{3}{l}{   } \\\\ [2ex]

     Composition     & \multicolumn{3}{l}{   } \\\\
     {}              & \multicolumn{3}{l}{   } \\\\ [2ex]

     \hline
     \hline

     Residual Nuclei & Nuclide    & Activity [Bq/cm$^3$] & Half-Life \\\\

     \hline
     \hline

${TABLE}

     \hline
     \hline
\end{tabular}
""")

def find_nuclide(Z):
    symbol = ['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si',
              'P','S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni',
              'Cu','Zn','Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb',
              'Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe',
              'Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho',
              'Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au',
              'Hg','Tl','Pb','Bi','Po','At','Rn','Fr','Ra','Ac','Th','Pa','U',
              'Np','Pu','Am','Cm','Bk','Cf','Es','Fm']
    return symbol[Z-1]

#Conditions for a file to be relevant:
#1. Has to begin with inputbasename_resnucle_
#2. Has to finish tab.lis
#3. Has to be in the correct directory
def is_rnc_result(fn, input_base):
    if not fn.startswith('%s_resnucle_' % input_base):
        return False
    if not fn.endswith('_tab.lis'):
        return False
    if not os.path.isfile(fn):
        return False
    return True



#Find the files to be processed
def find_files(directory, input_base):
    return [fn for fn in os.listdir(directory) if is_rnc_result(fn, input_base)]


def process_arguments(path_prefix):
    parser = OptionParser(usage="usage: %prog [options] main_input_file.inp [specific files...]",
                          description="Transform FLUKA RESNUCLe .tab.lis files in compact tables",
                          epilog=("rnuc2tab takes all the RESNUCLe tab.lis files obtained "
                                  "as FLUKA output and orders them in  csv format "
                                  "or in a simple .tex file ready to be used as LaTeX table."
                                  "\n\n"
                                  "Results will be output to files in the current "
                                  "directory."))
    parser.add_option("-t", "--table-type", dest="opt_table", default="csv",
                      choices="csv tex".split(),
                      help="Type of output: csv or tex file")

    (options, args) = parser.parse_args()    

    #Not correct number of arguments is specified
    if len(args) < 1:
        sys.exit(parser.get_usage())

    #Take the base of the input name and the option for the table
    input_base = re.sub(r'\.inp$', '', args[0])

    #No specific files are selected
    if len(args) < 2:
        res_files = find_files(path_prefix, input_base)
    else:
        res_files = args[1:]

    tab_option = options.opt_table

    return (res_files, tab_option)



def actsort(A0, Z0, Bq0, err0):
    indexes = numpy.argsort(numpy.array(Bq0))
    indexes[:] = indexes[::-1]
    A0 = [A0[jj] for jj in indexes]
    Z0 = [Z0[jj] for jj in indexes]
    Bq0 = [Bq0[jj] for jj in indexes]
    err0 = [err0[jj] for jj in indexes] 
     
    return (A0, Z0, Bq0, err0)


def main():
    directory = os.getcwd()
    warn('Directory: %s' % directory)
    warn('User: %s' % os.getenv('LOGNAME'))

    res_files, tab_option = process_arguments(directory)

    #If no files have to be processed, exit
    if not res_files:
        sys.exit('Nothing to do.')

    warn('RESNUCLe files to process: \n%s\n' % res_files)
        
    for res in res_files:
        A = []
        Z = []
        Bq = []
        err = []
        A_iso = []
        Z_iso = []
        Bq_iso = []
        err_iso =[]
        iso_flag = 0
        with open(res) as fin:
            for i,lines in enumerate(fin):
                #First three lines are always text
                if i > 2:
                    #Split the lines removing spaces
                    #Ignore isomers (line starts with #)
                    line = lines.split()
                    if line[0] != '#':
                        if line[2] != '0.000':
                            if iso_flag == 0:
                                A.append(int(line[0]))
                                Z.append(int(line[1]))
                                Bq.append(float(line[2]))
                                err.append(float(line[3]))
                            if iso_flag ==1:
                                A_iso.append(int(line[0]))
                                Z_iso.append(int(line[1]))
                                Bq_iso.append(float(line[3]))
                                err_iso.append(float(line[4]))                            
                    else:
                        iso_flag = 1
                        continue
        #Sort by activity in descending order
        A, Z, Bq, err = actsort(A, Z, Bq, err)
        A_iso, Z_iso, Bq_iso, err_iso = actsort(A_iso, Z_iso, Bq_iso, err_iso)
        outname = re.sub('\_tab.lis$','',res)
        if tab_option == 'csv':
            outname = outname + '.csv'
            with open(outname, 'w') as fout:
                for i in range (len(A)):
                    if i==0:
                        fout.write("Z, A, Activity Bq, Error, Isotope  \n")
                    textline = "%s, %s, %s, %s\n" % (Z[i], A[i], Bq[i], err[i])
                    fout.write(textline)
                for i in range (len(A_iso)):
                    textline = "%s, %s, %s, %s, %s\n" % (Z_iso[i], A_iso[i], Bq_iso[i], err_iso[i], 1)
                    fout.write(textline)                            
        else:
            tabletext = [None]*(len(A)+len(A_iso))
            outname = outname + '.tex'
            for i in range (len(A)):
                tabletext[i] = ('{:4s} {:2s} {:12s} {:2s}'.format(' ','{}',' ','& '))
                nuc_text = '$^{'+ str(A[i]) + '}$' + find_nuclide(Z[i])
                tabletext[i] = tabletext[i] + '{:10s} {:2s}'.format(nuc_text, '& ')
                tabletext[i] = tabletext[i] + '{:20s} {:9s}'.format(str(Bq[i]),'& {}')
                tabletext[i] = tabletext[i] + "\\\\ \n"               
            for i in range (len(A),len(A)+len(A_iso)):
                tabletext[i] = ('{:4s} {:2s} {:12s} {:2s}'.format(' ','{}',' ','& '))
                nuc_text = '$^{'+ str(A_iso[i-len(A)]) + 'm}$' + find_nuclide(Z_iso[i-len(A)])
                tabletext[i] = tabletext[i] + '{:10s} {:2s}'.format(nuc_text, '& ')
                tabletext[i] = tabletext[i] + '{:20s} {:9s}'.format(str(Bq_iso[i-len(A)]),'& {}')
                tabletext[i] = tabletext[i] + "\\\\ \n"  
            tabletext = ''.join(tabletext)    
            LaTable = LaTemplate.safe_substitute(TABLE = tabletext)
            with open(outname, 'w') as fout:
                fout.write(LaTable)


if __name__ == '__main__':
    main()
