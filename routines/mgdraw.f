*$ CREATE MGDRAW.FOR
*COPY MGDRAW
*                                                                      *
*=== mgdraw ===========================================================*
*                                                                      *
      SUBROUTINE MGDRAW ( ICODE, MREG )

      INCLUDE 'dblprc.inc'
      INCLUDE 'dimpar.inc'
      INCLUDE 'iounit.inc'
*
*----------------------------------------------------------------------*
*                                                                      *
*     Copyright (C) 1990-2006      by        Alfredo Ferrari           *
*     All Rights Reserved.                                             *
*                                                                      *
*                                                                      *
*     MaGnetic field trajectory DRAWing: actually this entry manages   *
*                                        all trajectory dumping for    *
*                                        drawing                       *
*                                                                      *
*     Created on   01 march 1990   by        Alfredo Ferrari           *
*                                              INFN - Milan            *
*     Last change  05-may-06       by        Alfredo Ferrari           *
*                                              INFN - Milan            *
*                                                                      *
*----------------------------------------------------------------------*
*
      INCLUDE 'caslim.inc'
      INCLUDE 'comput.inc'
      INCLUDE 'sourcm.inc'
      INCLUDE 'fheavy.inc'
      INCLUDE 'flkstk.inc'
      INCLUDE 'genstk.inc'
      INCLUDE 'mgddcm.inc'
      INCLUDE 'paprop.inc'
      INCLUDE 'quemgd.inc'
      INCLUDE 'sumcou.inc'
      INCLUDE 'trackr.inc'
*
      DIMENSION DTQUEN ( MXTRCK, MAXQMG )
*
      CHARACTER*20 FILNAM
      CHARACTER REGIO1*8, REGIO2*8
      LOGICAL LFCOPE
      SAVE LFCOPE
      DATA LFCOPE / .FALSE. /
      RETURN


*============================================================
*  A. Kaminsky, Apr2020 (coronavirus time)
*
*  Dump of all particles entering and leaving region "Target"
*  Columns are the same as in FOCUS code with the fillowing correction
*  The very fist column (primary event) is negative is the particle
*  is comint into  Target, and is positive wheb it is leaving Target
*
*
      ENTRY BXDRAW ( ICODE, MREG, NEWREG, XSCO, YSCO, ZSCO )
*      WRITE(*,*) 'BXDRAW_KAM ',ICODE,MREG,NEWREG,JTRACK
      IF ( .NOT. LFCOPE ) THEN
         LFCOPE = .TRUE.
         FILNAM = CFDRAW
         OPEN ( UNIT = IODRAW, FILE = FILNAM, STATUS = 'NEW', FORM =
     & 'FORMATTED' )
      END IF


      IF (JTRACK.GT.ZERZER) THEN 
       IF (ETRACK.GT.AM(JTRACK)) THEN

            CALL GEOR2N (MREG,REGIO1,IERR)
            CALL GEOR2N (NEWREG,REGIO2,IERR)
         
        IF (IERR .NE. 0 ) STOP 
     &         "Error in name conversion"

         IF
     &       ( REGIO2(1:5).EQ."QLumi") THEN
             WRITE( IODRAW,100) NCASE, JTRACK, ETRACK,
     &           XSCO,YSCO,
     &           ZSCO,PTRACK,WTRACK,ATRACK, CMTRCK, CXTRCK,CYTRCK,CZTRCK
         ENDIF
	ENDIF      
      END IF  
  100 FORMAT(i7,i5,11e12.4)
      RETURN
*============================================================



      ENTRY EEDRAW ( ICODE )
      RETURN
      ENTRY ENDRAW ( ICODE, MREG, RULL, XSCO, YSCO, ZSCO )
      RETURN
      ENTRY SODRAW
      RETURN
      ENTRY USDRAW ( ICODE, MREG, XSCO, YSCO, ZSCO )
      RETURN
*=== End of subrutine Mgdraw ==========================================*
      END

