#!/bin/sh
$FLUPRO/bin/fff routines/mhcos.f
$FLUPRO/bin/fff routines/mgdraw.f
$FLUPRO/bin/fff routines/fieldi.f
$FLUPRO/bin/fff routines/lbqfin.f
$FLUPRO/bin/fff routines/lbqfld.f
$FLUPRO/bin/fff routines/litwod.f
$FLUPRO/bin/fff routines/magfld.f
$FLUPRO/bin/fff routines/usrglo.f

$FLUPRO/bin/ldpmqmd -o CMSpp -m fluka routines/fieldi.o routines/lbqfin.o routines/lbqfld.o routines/litwod.o routines/magfld.o routines/mhcos.o routines/mgdraw.o routines/usrglo.o
#drop magnetic field for now
#$FLUPRO/bin/ldpmqmd -o CMSpp -m fluka routines/mhcos.o routines/mgdraw.o