
#!/bin/sh
$FLUPRO/bin/fff -b -N fieldi.f
$FLUPRO/bin/fff -b -N lbqfin.f
$FLUPRO/bin/fff -b -N lbqfld.f
$FLUPRO/bin/fff -b -N litwod.f
$FLUPRO/bin/fff -b -N magfld.f
$FLUPRO/bin/fff -b -N mhcos.f
$FLUPRO/bin/fff -b -N usrglo.f

$FLUPRO/bin/ldpmqmd -o CMSpp -m fluka fieldi.o lbqfin.o lbqfld.o litwod.o magfld.o mhcos.o usrglo.o
