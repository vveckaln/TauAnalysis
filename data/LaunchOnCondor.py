import getopt
import urllib
import string
import os
import sys
import glob
import fnmatch
import commands
import re

CopyRights  = '####################################\n'
CopyRights += '#        LaunchOnFarm Script       #\n'
CopyRights += '#     Loic.quertenmont@cern.ch     #\n'
CopyRights += '#            April 2010            #\n'
CopyRights += '####################################\n'

Farm_Directories  = []
Path_Cmd          = ''
Path_Shell        = ''
Path_Log          = ''
Path_Cfg          = ''
Path_Out          = ''
Jobs_Count        = 0
Jobs_Name         = ''
Jobs_Index        = ''
Jobs_Seed	  = 0
Jobs_NEvent	  =-1
Jobs_Skip         = 0
Jobs_Queue        = '2nd'
Jobs_LSFRequirement = '"type==SLC5_64&&pool>30000"'
Jobs_Inputs	  = []
Jobs_FinalCmds    = []
Jobs_RunHere      = 0
Jobs_EmailReport = False

useLSF = True
useLIP = True


def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)



def usage() :
      print 'LaunchOnCondor [options]'
#      print '   -j json file with lumi info'
#      print '   -o output file'
      print 'is an interface to submit jobs to LSF/Condor batch in a high-level way'


def CreateTheConfigFile(argv):
        global Jobs_Name
        global Jobs_Index
	global Jobs_Count
	global Jobs_Seed
	global Jobs_Skip
	global Jobs_NEvent
	global Jobs_Inputs
        global Jobs_FinalCmds
	global Path_Cfg
	global CopyRights
        Path_Cfg   = Farm_Directories[1]+Jobs_Index+Jobs_Name+'_cfg.py'

	config_file=open(argv[1],'r')
	config_txt   = '\n\n' + CopyRights + '\n\n'
	config_txt  += config_file.read()
	config_file.close()
	i = 2
	while i < len(argv)-1:
		config_txt = config_txt.replace(argv[i],argv[i+1])
		i+=2

	#Default Replacements
	config_txt = config_txt.replace("XXX_I_XXX"   		,"%04i"%Jobs_Count)
        config_txt = config_txt.replace("XXX_PATH_XXX"		,os.getcwd())
        config_txt = config_txt.replace("XXX_OUTPUT_XXX"        ,Jobs_Name)
        config_txt = config_txt.replace("XXX_NAME_XXX"  	,Jobs_Index+Jobs_Name)
	config_txt = config_txt.replace("XXX_SEED_XXX"  	,str(Jobs_Seed+Jobs_Count))
        config_txt = config_txt.replace("XXX_NEVENTS_XXX"	,str(Jobs_NEvent))
        config_txt = config_txt.replace("XXX_SKIP_XXX"     	,str(Jobs_Skip))
	if Jobs_Count < len(Jobs_Inputs):
		config_txt = config_txt.replace("XXX_INPUT_XXX"         ,Jobs_Inputs[Jobs_Count])

	config_file=open(Path_Cfg,'w')
	config_file.write(config_txt)
	config_file.close()

def CreateTheShellFile(argv):
	global Path_Shell
	global Path_Cfg
	global CopyRights	
	global Jobs_RunHere
	global Jobs_FinalCmds
        global absoluteShellPath
        Path_Shell = Farm_Directories[1]+'script'+Jobs_Index+Jobs_Name+'.sh'
        function_argument=''
        for i in range(2,len(argv)):
                function_argument+="%s" % argv[i]
                if i != len(argv)-1:
                        function_argument+=', '

	shell_file=open(Path_Shell,'w')
	shell_file.write('#! /bin/sh\n')
	shell_file.write(CopyRights + '\n')
        shell_file.write('pwd\n')
	shell_file.write('export SCRAM_ARCH='+os.getenv("SCRAM_ARCH","slc5_amd64_gcc462")+'\n')
        shell_file.write('export BUILD_ARCH='+os.getenv("BUILD_ARCH","slc5_amd64_gcc462")+'\n')
        shell_file.write('export VO_CMS_SW_DIR='+os.getenv("VO_CMS_SW_DIR","/nfs/soft/cms")+'\n')
	#shell_file.write('source /nfs/soft/cms/cmsset_default.sh\n')
	shell_file.write('cd ' + os.getcwd() + '\n')
	shell_file.write('eval `scramv1 runtime -sh`\n')

	if   argv[0]=='BASH':                 
		if Jobs_RunHere==0:
                	shell_file.write('cd -\n')
                shell_file.write(argv[1] + " %s\n" % function_argument)
        elif argv[0]=='ROOT':
     	        function_argument='('+function_argument+')'
		if Jobs_RunHere==0:
                	shell_file.write('cd -\n')
	        shell_file.write('root -l -b << EOF\n')
	        shell_file.write('   TString makeshared(gSystem->GetMakeSharedLib());\n')
	        shell_file.write('   TString dummy = makeshared.ReplaceAll("-W ", "-Wno-deprecated-declarations -Wno-deprecated ");\n')
                shell_file.write('   TString dummy = makeshared.ReplaceAll("-Wshadow ", " -std=c++0x ");\n')
                shell_file.write('   cout << "Compilling with the following arguments: " << makeshared << endl;\n')
	        shell_file.write('   gSystem->SetMakeSharedLib(makeshared);\n')
		shell_file.write('   gSystem->SetIncludePath( "-I$ROOFITSYS/include" );\n')  
                shell_file.write('   .x %s+' % argv[1] + function_argument + '\n')
	        shell_file.write('   .q\n')
	        shell_file.write('EOF\n\n')
        elif argv[0]=='FWLITE':                 
                function_argument='('+function_argument+')'
		if Jobs_RunHere==0:
                	shell_file.write('cd -\n')
	        shell_file.write('root -l -b << EOF\n')
                shell_file.write('   TString makeshared(gSystem->GetMakeSharedLib());\n')
                shell_file.write('   TString dummy = makeshared.ReplaceAll("-W ", "-Wno-deprecated-declarations -Wno-deprecated ");\n')
                shell_file.write('   TString dummy = makeshared.ReplaceAll("-Wshadow ", " -std=c++0x ");\n')
                shell_file.write('   cout << "Compilling with the following arguments: " << makeshared << endl;\n')
                shell_file.write('   gSystem->SetMakeSharedLib(makeshared);\n')
                shell_file.write('   gSystem->SetIncludePath("-I$ROOFITSYS/include");\n')
	        shell_file.write('   gSystem->Load("libFWCoreFWLite");\n')
	        shell_file.write('   AutoLibraryLoader::enable();\n')
	        shell_file.write('   gSystem->Load("libDataFormatsFWLite.so");\n')
	        shell_file.write('   gSystem->Load("libAnalysisDataFormatsSUSYBSMObjects.so");\n')
	        shell_file.write('   gSystem->Load("libDataFormatsVertexReco.so");\n')
	        shell_file.write('   gSystem->Load("libDataFormatsHepMCCandidate.so");\n')
                shell_file.write('   gSystem->Load("libPhysicsToolsUtilities.so");\n')
                shell_file.write('   gSystem->Load("libdcap.so");\n')
                shell_file.write('   .x %s+' % argv[1] + function_argument + '\n')
	        shell_file.write('   .q\n')
	        shell_file.write('EOF\n\n')
        elif argv[0]=='CMSSW':
		CreateTheConfigFile(argv);
		if Jobs_RunHere==0:
			shell_file.write('cd -\n')
		shell_file.write('cmsRun ' + os.getcwd() + '/'+Path_Cfg + '\n')
        elif argv[0]=='LIP':        
                CreateTheConfigFile(argv);
                if Jobs_RunHere==0:
                        shell_file.write('cd -\n')
                shell_file.write('cmsRun ' + os.getcwd() + '/'+Path_Cfg + '\n')
	else:
		print #Program to use is not specified... Guess it is bash command		
                shell_file.write('#Program to use is not specified... Guess it is bash command\n')
		shell_file.write(argv[1] + " %s\n" % function_argument)

        for i in range(len(Jobs_FinalCmds)):
                #shell_file.write('echo ' + Jobs_FinalCmds[i]+'\n')
		shell_file.write(Jobs_FinalCmds[i]+'\n')
        if Jobs_RunHere==0:
           outDir = Farm_Directories[3]
           if(not os.path.isabs(Path_Shell)): outDir = os.getcwd()+'/'+outDir;
 	   shell_file.write('mv '+ Jobs_Name+'* '+outDir+'\n')
	shell_file.close()
	os.system("chmod 777 "+Path_Shell)


def CreateTheCmdFile():
        global useLSF
        global useLIP
        global Path_Cmd
        global CopyRights
        Path_Cmd   = Farm_Directories[1]+Jobs_Name+'.cmd'
	cmd_file=open(Path_Cmd,'w')

	if useLSF:
		cmd_file.write(CopyRights + '\n')
	else:
            if(not useLIP):
		cmd_file.write('Universe                = vanilla\n')
		cmd_file.write('Environment             = CONDORJOBID=$(Process)\n')
		cmd_file.write('notification            = Error\n')
		#code specific for louvain
		if(commands.getstatusoutput("uname -n")[1].find("ucl.ac.be")!=-1):
        		cmd_file.write('requirements            = (CMSFARM=?=True)&&(Memory > 200)\n')
		else:
			cmd_file.write('requirements            = (Memory > 200)\n')
		cmd_file.write('should_transfer_files   = YES\n')
		cmd_file.write('when_to_transfer_output = ON_EXIT\n')
	cmd_file.close()

def AddJobToCmdFile():
        global useLSF
        global useLIP
	global Path_Shell
        global Path_Cmd
        global Path_Out
	global Path_Log
        global absoluteShellPath
        global Jobs_EmailReport
        Path_Log   = Farm_Directories[2]+Jobs_Index+Jobs_Name
        Path_Out   = Farm_Directories[3] + Jobs_Index + Jobs_Name
        cmd_file=open(Path_Cmd,'a')
	if useLSF:
               absoluteShellPath = Path_Shell;
               if(not os.path.isabs(absoluteShellPath)): absoluteShellPath= os.getcwd() + "/"+absoluteShellPath
	       temp = "bsub -q " + Jobs_Queue + " -R " + Jobs_LSFRequirement + " -J " + Jobs_Name+Jobs_Index
	       if(not Jobs_EmailReport):
	         absoluteOutPath = Path_Out
	         if(not os.path.isabs(absoluteOutPath)):
	           absoluteOutPath = os.getcwd() + "/" + Path_Out
	         temp = temp + " -oo " + absoluteOutPath + ".cout"
	       temp = temp + " '" + absoluteShellPath + "'\n"
	       cmd_file.write(temp)
#               cmd_file.write("bsub -q " + Jobs_Queue + " -J " + Jobs_Name+Jobs_Index + " '" + os.getcwd() + "/"+Path_Shell + " 0 ele'\n")
	else:
            if(not useLIP):
        	cmd_file.write('\n')
	        cmd_file.write('Executable              = %s\n'     % Path_Shell)
        	cmd_file.write('output                  = %s.out\n' % Path_Log)
	        cmd_file.write('error                   = %s.err\n' % Path_Log)
#        	cmd_file.write('log                     = %s.log\n' % Path_Log)
                cmd_file.write('log                     = /dev/null\n') 
	        cmd_file.write('Queue 1\n')
            else:
                absoluteShellPath = Path_Shell;
                if(not os.path.isabs(absoluteShellPath)): absoluteShellPath= os.getcwd() + "/" + absoluteShellPath
                cmd_file.write("qsub " + absoluteShellPath + "\n")
        cmd_file.close()

def CreateDirectoryStructure(FarmDirectory):
        global Jobs_Name
        global Farm_Directories
	Farm_Directories = [FarmDirectory+'/', FarmDirectory+'/inputs/', FarmDirectory+'/logs/', FarmDirectory+'/outputs/']
        for i in range(0,len(Farm_Directories)):
		if os.path.isdir(Farm_Directories[i]) == False:
	        	os.system('mkdir -p ' + Farm_Directories[i])

def SendCluster_LoadInputFiles(path, NJobs):
        global Jobs_Inputs
	input_file  = open(path,'r')
	input_lines = input_file.readlines()
	input_file.close()
	#input_lines.sort()
	
	BlockSize = (len(input_lines)/NJobs)
	LineIndex  = 0
	JobIndex   = 0
	BlockIndex = 0	
	Jobs_Inputs = [""]
	while LineIndex < len(input_lines):
		Jobs_Inputs[JobIndex] += input_lines[LineIndex]
		LineIndex +=1
		BlockIndex+=1
		if BlockIndex>BlockSize:
			BlockIndex = 0
			JobIndex  += 1
			Jobs_Inputs.append("")
	return JobIndex+1

def SendCluster_Create(FarmDirectory, JobName):
	global useLSF
        global useLIP
	global Jobs_Name
	global Jobs_Count
        global Farm_Directories

	#determine if the submission system is LSF batch or condor
	command_out = commands.getstatusoutput("bjobs")[1]
        command_lip = commands.getstatusoutput("qstat")[1]
	if(command_out.find("command not found")<0): useLSF = True
	else:				  	     useLSF = False;
        if(command_lip.find("command not found")<0): useLIP = True
        else:                                        useLIP = False;
	Jobs_Name  = JobName
	Jobs_Count = 0
        CreateDirectoryStructure(FarmDirectory)
        CreateTheCmdFile()

def SendCluster_Push(Argv):
        global Farm_Directories
        global Jobs_Count
        global Jobs_Index
	global Path_Shell
	global Path_Log

	Jobs_Index = "%04i_" % Jobs_Count
        if Jobs_Count==0 and (Argv[0]=="ROOT" or Argv[0]=="FWLITE"):                
                #First Need to Compile the macro --> Create a temporary shell path with no arguments
                print "Compiling the Macro..."
                CreateTheShellFile([Argv[0],Argv[1]])
                os.system('sh '+Path_Shell)
                os.system('rm '+Path_Shell)
		print "Getting the jobs..."
	print Argv
        CreateTheShellFile(Argv)
        AddJobToCmdFile()
	Jobs_Count = Jobs_Count+1

def SendCluster_Submit():
        global useLSF
        global useLIP
	global CopyRights
        global Jobs_Count
        global Path_Cmd

	if useLSF:
		os.system("sh " + Path_Cmd)
        elif useLIP:
                os.system("sh " + Path_Cmd)
	else:
		os.system("condor_submit " + Path_Cmd)  

	print '\n'+CopyRights
	print '%i Job(s) has/have been submitted on the Computing Cluster' % Jobs_Count

def SendSingleJob(FarmDirectory, JobName, Argv):
	SendCluster_Create(FarmDirectory, JobName, Argv)
	SendCluster_Push(FarmDirectory, JobName, Argv)
	SendCluster_Submit(FarmDirectory, JobName,Argv)

def SendCMSJobs(FarmDirectory, JobName, ConfigFile, InputFiles, NJobs, Argv):
	SendCluster_Create(FarmDirectory, JobName)
	NJobs = SendCluster_LoadInputFiles(InputFiles, NJobs)
	for i in range(NJobs):
        	LaunchOnCondor.SendCluster_Push  (["CMSSW", ConfigFile])
	LaunchOnCondor.SendCluster_Submit()



def GetListOfFiles(Prefix, InputPattern, Suffix):
      List = []

      if(InputPattern.find('/store/cmst3')==0) :
         index = InputPattern.rfind('/')
         Listtmp = commands.getstatusoutput('cmsLs ' + InputPattern[0:index] + ' | awk \'{print $5}\'')[1].split('\n')
         pattern = InputPattern[index+1:len(InputPattern)]
         for file in Listtmp:
            if fnmatch.fnmatch(file, pattern): List.append(InputPattern[0:index]+'/'+file)
      elif(InputPattern.find('/castor/')==0):
         index = InputPattern.rfind('/')
         Listtmp = commands.getstatusoutput('rfdir ' + InputPattern[0:index] + ' | awk \'{print $9}\'')[1].split('\n')
         pattern = InputPattern[index+1:len(InputPattern)]
         for file in Listtmp:
            if fnmatch.fnmatch(file, pattern): List.append(InputPattern[0:index]+'/'+file)
      else :
         List = glob.glob(InputPattern)

      List = sorted(List)
      for i in range(len(List)):
         List[i] = Prefix + List[i] + Suffix
      return natural_sort(List)


def ListToString(InputList):
   outString = ""
   for i in range(len(InputList)):
      outString += InputList[i]
   return outString

def ListToFile(InputList, outputFile):
   out_file=open(outputFile,'w')
   for i in range(len(InputList)):
      out_file.write('     ' + InputList[i] + '\n')
   out_file.close()

def FileToList(path):
   input_file  = open(path,'r')
   input_lines = input_file.readlines()
   input_file.close()
   input_lines.sort()
   return natural_sort(input_lines)






def SendCMSMergeJob(FarmDirectory, JobName, InputFiles, OutputFile, KeepStatement):
        SendCluster_Create(FarmDirectory, JobName)
        Temp_Cfg   = Farm_Directories[1]+Jobs_Index+Jobs_Name+'_TEMP_cfg.py'

	if len(InputFiles)==0:
		print 'Empty InputFile List for Job named "%s", Job will not be submitted' % JobName
		return

        InputFilesString = ''
        InputFiles = natural_sort(InputFiles)
        for i in range(len(InputFiles)):
		InputFilesString += "process.source.fileNames.extend([" + InputFiles[i].replace(',',' ') + '])\n'


	cfg_file=open(Temp_Cfg,'w')
        cfg_file.write('import FWCore.ParameterSet.Config as cms\n')
        cfg_file.write('process = cms.Process("Merge")\n')
        cfg_file.write('\n')
        cfg_file.write('process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )\n')
        cfg_file.write('process.load("FWCore.MessageService.MessageLogger_cfi")\n')
        cfg_file.write('\n')
        cfg_file.write('process.MessageLogger.cerr.FwkReport.reportEvery = 50000\n')
        cfg_file.write('process.source = cms.Source("PoolSource",\n')
        cfg_file.write('   skipBadFiles = cms.untracked.bool(True),\n')
        cfg_file.write('   duplicateCheckMode = cms.untracked.string("noDuplicateCheck"),\n')
        cfg_file.write('   fileNames = cms.untracked.vstring(\n')
        cfg_file.write('   )\n')
        cfg_file.write(')\n')
        cfg_file.write('\n')
#        cfg_file.write('process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(10) )\n')
        cfg_file.write('%s\n' % InputFilesString)
        cfg_file.write('process.OUT = cms.OutputModule("PoolOutputModule",\n')
        cfg_file.write('    outputCommands = cms.untracked.vstring(%s),\n' % KeepStatement)
        cfg_file.write('    eventAutoFlushCompressedSize=cms.untracked.int32(15*1024*1024),\n')
        cfg_file.write('    fileName = cms.untracked.string(%s)\n' % OutputFile)
        cfg_file.write(')\n')
        cfg_file.write('\n')
        cfg_file.write('process.endPath = cms.EndPath(process.OUT)\n')
	cfg_file.close()
        SendCluster_Push  (["CMSSW", Temp_Cfg])
        SendCluster_Submit()
        os.system('rm '+ Temp_Cfg)





