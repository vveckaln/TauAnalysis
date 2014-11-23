#ifndef _PhysicsObject_hh
#define _PhysicsObject_hh

#include "LIP/TauAnalysis/interface/llvvObjects.h"
#include "TLorentzVector.h"
#include "TVectorD.h"


class Object
{
public:
  Object();
  virtual ~Object();
  virtual void ls() const = 0;
};

class PhysicsObject: public Object, public TLorentzVector
{
public:
  PhysicsObject();
  PhysicsObject(const TLorentzVector * const, const TVectorD * const);
  PhysicsObject(const LorentzVector );
  PhysicsObject(const LorentzVectorF );

  static const char* title;
  virtual void ls() const = 0;
  virtual void ListLorentzVector() const;
  virtual PhysicsObject &operator += (const TLorentzVector); 
  virtual PhysicsObject &operator -= (const TLorentzVector); 

  virtual ~PhysicsObject();
};

class Lepton: public PhysicsObject
{
public:
  TString title;
  Lepton();
  Lepton(const TLorentzVector * const, const TVectorD * cons);
  Lepton(const LorentzVector);
  Lepton(const LorentzVectorF);
  virtual void ls() const;
  char charge;
  double relative_isolation;
  virtual ~Lepton();
};

class Electron: public Lepton
{
public:
  static const char* title;
  Electron();
  Electron(const TLorentzVector * const, const TVectorD * const);
  Electron(const llvvLepton);
  virtual void ls() const;
  double relative_isolation;
  ~Electron();
  
};

class Muon: public Lepton
{
public:
  static const char * title;
  Muon();
  Muon(const TLorentzVector * const, const TVectorD * const);
  Muon(const llvvLepton);

  virtual void ls() const;
  double relative_isolation;
  ~Muon();
};

class Tau: public Lepton
{
public:
  static const char * title;
  Tau();
  Tau(const TLorentzVector * const, const TVectorD * const);
  Tau(const llvvTau);

  virtual void ls() const;
  ~Tau();
};

class Jet: public PhysicsObject
{
public:
  Jet();
  Jet(const TLorentzVector * const, const TVectorD * const);
  Jet(const llvvJetExt);
  double GetPt() const;
  virtual void ls() const;
  bool BTagSFUtil_isBtagged;
  double genJetPt;
  int genflav;
  double CSV_discriminator;
  double jetpgid;
  bool isBtagged;
  ~Jet();
};

class MET: public PhysicsObject
{
public:
  MET();
  MET(const TLorentzVector * const, const TVectorD *const);
  MET(const llvvMet);
  virtual void ls() const;
  ~MET();
};

class Vertex: public Object
{
public:
  Vertex();
  virtual void ls() const;
  virtual ~Vertex();
};

#endif

