#include "LIP/TauAnalysis/interface/GlobalVariables.hh"

namespace gVariables
{
  bool           gnoUncertainties;
  bool           geChONmuChOFF;
  bool           gIsData;
  double         gXSection;
  bool           gDebug; 
  unsigned char  gmctruthmode;
  unsigned char  gfile_split;
  unsigned char  gsegment;
  vector<int>    gjacknifeCfg; 
  TString        gInputFileName; 
  TString        gOutputFileName;
  TString        gBaseDirectoryName; 
  TString        gOutputDirectoryName;
  TString        gspyOutputArea;
  TString        gsubArea;
  vector<double> dataPileupDistributionDouble; 
  vector<double> singleLepDataPileupDistributionDouble; 
} 
