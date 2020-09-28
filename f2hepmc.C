// Reads the output from Fluka and converts it to the HepMC format
// Can search output with "glob" for any directories, starting from "CONDOR"
// In that case, use it with "glob" as input
// Stepan Obraztsov 25.09.2020

#include <iostream>
#include <fstream>
#include <istream>
#include <string>
#include <glob.h>
#include "HepMC/GenEvent.h"
#include "HepMC/IO_GenEvent.h"

using namespace std;
using namespace HepMC;

int fluka2pdg (int part){
    if (part == 7) return 22;
    else if (part == 8) return 2112;
    else if (part == 3) return 11;
    else if (part == 4) return -11;
    else if (part == 14) return -211;
    else if (part == 16) return -321;  
    else if (part == 1) return 2212; 
    else if (part == 25) return -311; 
    else if (part == 13) return 211; 
    else if (part == 10) return -13; 
    else if (part == 2) return -2212; 
    else {
      cout<<" unknown PDG ID = "<<part<<endl;
      return 0;
    }
}

void f2hepmc(
    std::string infile = "in",
    std::string outfile = "out",
    int firstevent = 1)
{
 	HepMC::IO_GenEvent* output = new HepMC::IO_GenEvent("Fluka_ASCII.dat", std::ios::out);
 
  glob_t globbuf;
  vector<string> inputfiles; 
  if (infile=="glob"){
    int err = glob("CONDOR*/*KAM", 0, NULL, &globbuf);
    if(err == 0)
    {
        for (size_t i = 0; i < globbuf.gl_pathc; i++)
        {
            //printf("%s\n", globbuf.gl_pathv[i]);
            inputfiles.push_back(globbuf.gl_pathv[i]);
        }

        globfree(&globbuf);
    }
  }
  else {
  inputfiles.push_back(infile);
  }

	int ev,part;
  float x,y,z,energy,p,r,age,path,cx,cy,cz;
  int ev_temp = -1;  

  GenEvent* event;
  event = new GenEvent(0,-666); //don't know how to get rid of the first empty event in the file
  event->use_units(HepMC::Units::GEV, HepMC::Units::MM);

  for (int i = 0; i<inputfiles.size(); i++){
  std::ifstream in;
  in.open(inputfiles[i]);
  cout<<"reading inputfile "<<inputfiles[i]<<endl;
  while (in.good()) {
      in >> ev >> part >> energy >>  x >> y >>z >> p >> r >> age >>path >> cx >> cy >>cz;
      if (ev_temp!=ev){
       output->write_event(event);
       event->clear();
       event = new GenEvent(0,ev+i*100);
       event->use_units(HepMC::Units::GEV, HepMC::Units::MM);
       ev_temp = ev;
      }
       GenVertex*  vertex = new GenVertex(FourVector(x*10,y*10,z*10,age));
       event->add_vertex(vertex);
       GenParticle* particle = new GenParticle( FourVector(p*cx,p*cy,p*cz,energy), fluka2pdg(part),1 );
       vertex->add_particle_out(particle);
     }
     output->write_event(event);
  }
}

int main(int argc, char *argv[])
{ 
  argc = argc;  
  f2hepmc(argv[1],argv[2],atoi(argv[3]));
  return 0;
}