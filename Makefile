CXX = g++
CXXFLAGS += -O2
ROOTFLAGS := `root-config --cflags --libs`

HEPMCFLAGS := -I /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/hepmc/2.06.07/include/ -L /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/hepmc/2.06.07/lib -lHepMC -lHepMCfio
# HEPMCLIBS += -L /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/hepmc/2.06.07/lib -lHepMC -lHepMCfio
SOURCES = f2hepmc.C
EXECUTABLE = f2hepmc.exe
all:
	$(CXX) $(CXXFLAGS) $(SOURCES) $(ROOTFLAGS) $(HEPMCFLAGS) -o $(EXECUTABLE)
