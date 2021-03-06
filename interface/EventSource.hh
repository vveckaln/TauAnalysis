#ifndef _EventSource_hh
#define _EventSource_hh
#include "LIP/TauAnalysis/interface/EventBuffer.hh"
#include "LIP/TauAnalysis/interface/EventSink.hh"
#include <iostream>
using namespace std;
template<class TEventOutput>
class EventSource{
public:
  EventSource(EventSink<TEventOutput> *sink){
    this -> next_processor_stage = sink;
  }
  EventSink<TEventOutput> * next_processor_stage;
  EventBuffer<TEventOutput> *output_buffer;
  void ContinueReportToNextStage(){
  if (next_processor_stage != NULL) next_processor_stage -> Report();
  }
  void ProceedToNextStage(){
    if (next_processor_stage != NULL){
     	next_processor_stage -> input_buffer = output_buffer;
	next_processor_stage -> Run();
    }
  }
  virtual ~EventSource(){
    if (next_processor_stage != NULL) delete next_processor_stage;
  }
};
#endif
