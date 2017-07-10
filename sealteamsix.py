################################################################################
# Operation: CryoSnake                                                         #
#                                                                              #
# Mission: A set of parameters has been taken hostage by the spectrometer. The #
# console has been booby trapped by Bruker engineers and is highly confusing.  #
# The main objective is to locate the parameters and deliver them unharmed to  #
# the extraction point. Good luck!                                             #
#                                                                              #
################################################################################
# Written by Jacob Brady (2017)                                                #
################################################################################
import os
import re
import sys
import subprocess as sp
from time import localtime, strftime
from string import Template
from math import log10 as log

# compiles pp in order that format.ased is created
XCMD("ased")
# gets target temperature for probe
XCMD("teget")

if os.getlogin() == 'jbrady':
    path = "./testfiles"
    def GETPAR(string):
        #print(string)
        return("0.0")
    def GETPAR2(string):
        return("0.0")
else:
    cwd = CURDATA()
    # version of TopSpin being run
    version = os.getcwd().split("/")[2]
    path = os.path.join(os.path.join(cwd[-1],cwd[0]),cwd[1])
    outname = "params.txt"
    if os.path.exists(os.path.join(path,outname)):
        fullpath = os.path.join(path,outname)
        sp.call("cp %s %s"%(fullpath,fullpath+".old"),shell=True)
    
    outfile = open(os.path.join(path,outname),"w")
    outfile.write(os.path.join(path,outname)+"\n")

# get the temperature after TEGET is run
acqu_fil = open(os.path.join(path,"acqus"),"r")
lines = acqu_fil.readlines()
for line in lines:
    if "##$TE=" in line:
        temp = float(line.split("=")[1])
        temp_c = temp - 273.15

# Templates for rendering parameters
power_template = Template(" $pulse $watt $dB :$alias")
#pulse_template = Template(" $pulse $duration $watt $dB :$alias")
pulse_template = Template(" $pulse $duration :$alias")
delay_template = Template(" $delay $duration :$alias")
grad_template = Template(" GP$axis$number $percent :$alias")
cnst_template = Template(" CNST$number $value :$alias")
loop_template = Template(" L$number $value :$alias")
cpd_template = Template(" CPDPRG$number $name $pcpd :$alias")
shape_template = Template(" SPNAM$number $pulse SPOFF$number=$spoff SPOAL$number=$spoal:$alias")

# paths
va_path = "/opt/%s/exp/stan/nmr/lists/va"%version
vd_path = "/opt/%s/exp/stan/nmr/lists/vd"%version
vc_path = "/opt/%s/exp/stan/nmr/lists/vc"%version
vp_path = "/opt/%s/exp/stan/nmr/lists/vp"%version
ph_path = "/opt/%s/exp/stan/nmr/lists/ph"%version
diff_path = ""

# parameter lists
lists = [("VALIST",va_path),
         ("VCLIST",vc_path),
         ("VDLIST",vd_path),
         ("VPLIST",vp_path),
         ("PHLIST",ph_path),
         ]
for i in range(1,9):
    fpath = "/opt/%s/exp/stan/nmr/lists/f%d"%(version,i)
    name = "FQ%dLIST"%i
    lists.append((name,fpath))

# number of aq dimensions
ndims = len([i for i in os.listdir(path) if "acqu" in i and not i.endswith("s")])
#print("ndims =%d"%ndims)
#ndims = int(GETPAR("AQ_mod"))

# conversion dicts
FnTYPE = {"0":"Traditional(planes)",
          "1":"Points(full)",
          "2":"NUS",
          "3":"Projection"}
          
FnMODE = {"0":"",
          "1":"QF",
          "2":"QSEQ",
          "3":"TPPI",
          "4":"STATES",
          "5":"STATES-TPPI",
          "6":"ECHO-ANTIECHO",
          }
          
AQ_mod = {"0":"qf",
          "1":"qsim",
          "2":"qseq",
          "3":"DQD",
          "4":"parallelQsim",
          "5":"parallelDQD"
          }
          
DIGMOD = {"0":"analog",
          "1":"digital",
          "2":"baseopt"
          }
          
def write_top(plist):
    for i in plist:
        outfile.write(i+"\n")
		         
def get_lists(lists):
    for i in lists:
        name = GETPAR(i[0])
        path = i[1]
        if name != "":
            path_name = os.path.join(path,name)
            if os.path.exists(path_name):
                f = open(os.path.join(path,name),"r")
                string = f.read()
                outfile.write("\n" + i[0] + " - " + name + "\n")
                outfile.write(string+"\n")
                outfile.write(newsec+"\n")
                f.close()	
            else:
                outfile.write("\n"+name+"\n")
                outfile.write("Could not find %s in %s\n"%(name,path))
                outfile.write(newsec+"\n")
				
#def get_spnams():
#	string = ""
#	spnams = [(num,i) for num,i in enumerate(GETPAR("SPNAM").split()) if i != "<>"]			
#	for num,sp in spnams:
#		string+="%d=%s "%(num,sp)
#	outfile.write(string+"\n")
								
#First params to be printed
dim = " %-16s"%"AXIS"
td   = " %-16s"%"TD (points)"
#sw ppm
sw   = " %-16s"%"SW (ppm)"
#sw hz
sw_h = " %-16s"%"SW (Hz)"
#nuc
nuc1 = " %-16s"%"NUC"
#sf01
sfo1 = " %-16s"%"SFO1 (MHz)"
#bf1
bf1  = " %-16s"%"BF1 (MHz)"
#O1
o1   = " %-16s"%"O1 (Hz)"
o1ppm   = " %-16s"%"O1 (ppm)"
#AQ
aq = " %-16s"%"AQ (ms)"
#fn_mode 
fnmod= " %-16s"%"FnMODE"

# Getting params for each dim
dims = range(1,ndims+1)[::-1]
 
for i in dims:
    dim  += " %-16s"%("F"+str(i))
    td   += " %-16s"%GETPAR("TD",i)
    sw   += " %-16.3f"%float(GETPAR("SW",i))
    sw_h += " %-16.3f"%float(GETPAR("SW_h",i))
    nuc1 += " %-16s"%(GETPAR("NUC1",i))
    sfo1 += " %-16.3f"%float(GETPAR("SFO1",i))
    bf1_ = float(GETPAR("BF1",i))
    bf1  += " %-16.3f"%bf1_
    # changed to GETPAR2 since GETPAR does not work
    o1_ = float(GETPAR2("%d O1"%i))
    o1   += " %-16.3f"%o1_
    o1ppm += " %-16.3f"%(o1_/bf1_)
    aq += " %-16.3f"%(float(GETPAR("AQ",i))*1000.)
    fnmod+= " %-16s"%FnMODE.get(GETPAR("FnMODE",i),"")
	
# put params in list
top_list = [dim,nuc1,td,sw,sw_h,sfo1,bf1,o1,o1ppm,aq,fnmod]
newsec = "------------------------------------------"
outfile.write(newsec+"\n")
outfile.write(" %s\n"%GETPAR("PULPROG"))
write_top(top_list)
outfile.write(newsec+"\n")
#outfile.write(" DEC = %s\n"%GETPAR("CPDPRG"))
#get_spnams()

params = ["ZGOPTNS","AQ_mod","NS","DS","RG","DE","DW","DIGMOD","FnTYPE"]
nus_params = ["NusAMOUNT","NusSEED","NusPOINTS","NUSLIST"]
# for loop below the GETPAR command is used since the GETPAR2 command gives incorrect information
for i in params:
    if GETPAR(i) is None:
        pass 
    else:
        if i == "FnTYPE":
            string = " %-16s =  %-16s"% (i,FnTYPE.get(GETPAR(i),"Unknown"))
            outfile.write(string+"\n")
            # write out NUS params
            if FnTYPE.get(GETPAR(i)) is "NUS":
                head = " %-16s "% "NUS parameters"
                outfile.write(newsec+"\n")
                outfile.write(head+"\n")
                for i in nus_params:
                    string = " %-16s =  %-16s"% (i,GETPAR(i))
                    outfile.write(string+"\n")    
        elif i == "AQ_mod":
            string = " %-16s =  %-16s"% (i,AQ_mod.get(GETPAR(i),"Unknown"))
            outfile.write(string+"\n")
        elif i == "DIGMOD":
            string = " %-16s =  %-16s"% (i,DIGMOD.get(GETPAR(i),"Unknown"))
            outfile.write(string+"\n")
        else:
            string=" %-16s =  %-16s"% (i,GETPAR(i))
            outfile.write(string+"\n")
# print temperature
string = " %-16s =  %-16.2f K (%.2f C)"% ("TE",temp,temp_c)
outfile.write(string+"\n")

def match(regex,key):
    regex = re.compile(regex)
    re_match = regex.match(key)
    return regex, re_match

def find_blocks(path,pattern):
    file_string = open(path,"r").read()
    dic = {}
    param_dic = dict(pulses=[],shapes=[],delays=[],gradients=[],powers=[],constants=[],decoupling=[])
    for i in pattern.findall(file_string):
        key = i[1]
        items = [i.strip("\t").split() for i in i[2].split("\n")]
        items = dict([(i[0],i[1:]) for i in items if i[0] != "END"])
        dic[key] = items
        
        # regex for pulses
        pulse_re, pulse_match = match("P(\d+)",key)
        # regex for delays
        delay_re, delay_match = match("D(\d+)",key)
        # regex for power levels
        db_re, db_re_match = match("(S?PL?W)(\d+)",key)
        # regex for gradients
        gd_re, gd_re_match = match("GP([XYZ])(\d+)",key)
        # regex for constants
        #cnst_re, cnst_re_match = match("(?i)cnst(\d+)",key)
        cnst_re, cnst_re_match = match("CNST(\d+)",key)
        loop_re, loop_re_match = match("L(\d+)",key)
        # regex for decoupling prog
        pcpd_re, pcpd_re_match = match("PCPD(\d)",key)
        cpdprg_re, cpdprg_re_match = match("CPDPRG\[(\d)\]",key)
        # shape pulse files and params
        spoff_re, spoff_re_match = match("SPOFFS(\d+)",key)
        spoal_re, spoal_re_match = match("SPOAL(\d+)",key)
                                                                
        if pulse_match is not None:
            duration = GETPAR("P %s"%pulse_match.group(1))
            watt = 0
            dB = 0
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = pulse_template.substitute(pulse="%-4s"%key,
        	                                  duration="%-8s"%duration,
        	                                  watt=watt,
        	                                  alias=alias,
        	                                  dB=dB)
            #param_dic["pulses"].append(dict(name=key,duration=duration,
            #      watt=watt,alias=alias,dB=dB,string=string))
            param_dic["pulses"].append(dict(name=key,duration=duration,
                  alias=alias,string=string))

        if delay_match is not None:
            duration = GETPAR("D %s"%delay_match.group(1))
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = delay_template.substitute(delay="%-4s"%key,
                    duration="%-8s"%duration,alias=alias)
            #print(string)
            param_dic["delays"].append(dict(name=key,duration=duration,
                      alias=alias,string=string))

        if db_re_match is not None:
            fullname = db_re_match.group(0)
       	    name = db_re_match.group(1)
            plw = GETPAR("%s %s"%(db_re_match.group(1),db_re_match.group(2)))
            plw = float(plw)

            if plw == 0:
                pldb = 1000.
            else:
                pldb = -10.*log(float(plw))
                
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = power_template.substitute(pulse ="%-6s"%fullname,
                    watt ="%8.3e"%plw, dB="%8.3f"%pldb,alias = alias)
            #print(string)
            param_dic["powers"].append(dict(name=fullname,watt=plw,
                dB=pldb,alias=alias,string=string))
            
          
        if gd_re_match is not None:
            name = gd_re_match.group(0)
            axis = gd_re_match.group(1)
            number = int(gd_re_match.group(2))
            percent = GETPAR("GP%s %d"%(axis, number))
            if percent == "0":
                pass
            else:
                alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
                string = grad_template.substitute(axis=axis,number=number, percent=("%4s"%percent)+" %", alias=alias)
                #print(string)
                param_dic["gradients"].append(dict(name=name,axis=axis,
                    number=number,percent=percent,alias=alias,string=string))
            
        if cnst_re_match is not None:
            name = cnst_re_match.group(0)
            number = int(cnst_re_match.group(1))
            value = GETPAR2("CNST %d"%(number))
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = cnst_template.substitute(number=number, value=value, alias=alias)
            #print(string)
            param_dic["constants"].append(dict(name=name,number=number,
                value=value,alias=alias,string=string))
                
        if loop_re_match is not None:
            name = loop_re_match.group(0)
            number = int(loop_re_match.group(1))
            value = GETPAR2("L %d"%(number))
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = loop_template.substitute(number=number, value=value, alias=alias)
            #print(string)
            param_dic["constants"].append(dict(name=name,number=number,
                value=value,alias=alias,string=string))
        
        if cpdprg_re_match is not None:
            #print("FOUND CPDPRG")
            number = int(cpdprg_re_match.group(1))
            name = GETPAR2("CPDPRG %d"%number)
            if name in ["cwp","cw.cpd"]:
                # only print pcpd if required
                pcpd = ""
            else:
            	  pcpd = GETPAR2("PCPD %d"%number)
            alias = "%-s"%" ".join(i for i in items.get("TEXT",""))
            string = cpd_template.substitute(name=name, number=number, pcpd=pcpd, alias=alias)
            #print(string)
            param_dic["decoupling"].append(dict(name=name,number=number,
                pcpd=pcpd,alias=alias,string=string))
                          
        if spoff_re_match is not None:
       	    number = int(spoff_re_match.group(1))
       	    name = GETPAR2("SPNAM %d"%number)
       	    spoff = GETPAR2("SPOFFS %d"%number)
       	    spoal = GETPAR2("SPOAL %d"%number)
       	    string = shape_template.substitute(pulse="%20s"%name,number=number,\
        	                                     spoff="%-4s"%spoff,spoal="%-4s"%spoal,alias=alias)
       	    param_dic["shapes"].append(dict(pulse=name,number=number,
                spoff=spoff,spoal=spoal,alias=alias,string=string))
                
    return dic,param_dic

def output_params(param_dic,fhandle,keys=None):
    if keys is None:
        keys = param_dic.keys()
    for k in keys:
        fhandle.write(newsec+"\n")
        fhandle.write("            "+k+"\n")
        fhandle.write(newsec+"\n")
        for i in sorted(param_dic[k],key=lambda x: (re.match("(\D+)\d+",x["string"]).group(1),\
                                                int(re.match("\D+(\d+)",x["string"]).group(1)))):
            fhandle.write(i["string"]+"\n")
         
##############################################
pattern = re.compile("([T_]*NAME\t{2}(.+)\n)((\t{2}(.+)\n)+END)",re.M)
ased_path = os.path.join(path,"format.ased")
dic, params = find_blocks(ased_path,pattern)
keys = ["delays","pulses","powers","shapes","gradients","constants","decoupling"]
output_params(params,outfile,keys)
outfile.write(newsec+"\n")
get_lists(lists)
outfile.write(newsec+"\n")
outfile.close()
#sp.call("gedit %s"%os.path.join(path,outname),shell=True)
header = strftime("%a, %d %b %Y %H:%M:%S", localtime())
# if you don't want to print just add any argument on the cmdline
if len(sys.argv)>1:
    pass
else:
    sp.call("enscript -fCourier8 %s --header='%s'"%(os.path.join(path,outname),header),shell=True)
print("DO NOT CLOSE THIS TERMINAL! TOPSPIN RUNNING HERE!")
