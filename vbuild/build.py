import sys, os, subprocess
def help():
    print """Vbuild V0.1:
Usage: vbuild [file.v]"""
    sys.exit(1)
def extract_deps(filename):
    f = open(filename.strip(), "r")
    line = f.readline()
    f.close()
    if line[:7] == "//deps:" or line[:7] == "--deps:":
        line = line[7:]
        files = [f.strip() for f in line.strip().split(',')]
        filelist = [filename]
        for f in files:
            filelist += extract_deps(f)
        return filelist
        
    else:
        return [filename]
def convert_to_verilog(filename):
    if os.path.isfile(filename + ".v"):
        vlogtime = os.path.getmtime(filename + ".v")
        vhdltime = os.path.getmtime(filename + ".vhd")
        if vlogtime > vhdltime: # if verilog file is newer
            return None
    convertcmd = ["vhd2vl", filename + ".vhd", filename + ".v"]
    print "Converting " + file + " to verilog"
    os.system(" ".join(convertcmd))

def convert(filelist):
    files = []
    for file in filelist:
        fsplit = os.path.splitext(file)
        if fsplit[1] == ".vhd":
            convert_to_verilog(fsplit[1])
            files.append(fsplit[0] + ".v")
        else:
            files.append(file)
    return files

def files_newer_than(mtime, files):
    for file in files:
        fstrip = file.strip()
        if os.path.isfile(fstrip) and os.path.getmtime(fstrip) <= mtime:
            pass
        else:
            print fstrip
            return False
    return True
buildcommand = """
yosys -p "synth_ice40 -abc2 -blif {0}" {1}
"""
def build():
    """vbuild build file.v will look at the first line of the file,
    if it contains // deps: x.v, y.v, z.v it will pass those files to yosys too,
    otherwise, it will call yosys with the filename, followed by arachne-pnr and icepack
    """
    if len(sys.argv) != 3:
        help()
    fname = sys.argv[2]
    deps = convert(extract_deps(fname))
    rawfile = os.path.splitext(fname)[0]
    outputfile = rawfile + ".blif"
    command = buildcommand.format(outputfile," ".join(deps))
    os.system(command)
    pnrcommand = ["arachne-pnr","-q","-p",rawfile + ".pcf", outputfile, "-o", rawfile + ".txt"]
    os.system(" ".join(pnrcommand))
    icepackcmd = ["icepack", rawfile + ".txt", rawfile + ".bin"]
    os.system(" ".join(icepackcmd))

def install():
    if len(sys.argv) != 3:
        help()
    fname = sys.argv[2]
    rawname = os.path.splitext(fname)[0]
    if os.path.isfile(rawname + ".bin"):
        mtime = os.path.getmtime(rawname + ".bin")
        if files_newer_than(mtime,convert(extract_deps(fname))):
            pass
        else:
            print "Building " + rawname + ".bin"
    else:
        print "Building " + rawname + ".bin"
        build() 
    timecmd = ["icetime","-r",rawname + ".rpt","-d hx1k", "-p", rawname+".pcf", rawname+".txt"]
    os.system(" ".join(timecmd))
    progcmd = ["iceprog",rawname + ".bin"]
    os.system(" ".join(progcmd))

def test():
    if len(sys.argv) != 3:
        help()
    fname = sys.argv[2] 
    rawname = os.path.splitext(fname)[0]
    deps = convert(extract_deps(fname))
    testcmd = ["iverilog", "-Wall","-D SIMULATION", "-o", rawname + ".iv"] + deps
    if os.system(" ".join(testcmd)) == 0 and \
        os.system("vvp " +rawname + ".iv") == 0 and \
        os.system("rm "+rawname+".iv") == 0:
            print "Test Succeeded!"
    else:
        print "Test FAILURE"
        sys.exit(1)

formalcmd = """
read_verilog -formal {0}
prep -top {1}
flatten
sat -ignore_unknown_cells -prove-asserts -set-assumes -show-ports -tempinduct -verify -set-assumes -dump_vcd {1}.vcd
"""
def formal():
    if len(sys.argv) != 3:
        help()
    fname = sys.argv[2]
    rawname = os.path.splitext(fname)[0]
    deps = convert(extract_deps(fname))
    if os.system("echo '" + formalcmd.format(" ".join(deps),rawname) +"' | yosys ") == 0:
        print "Test PASSED"
    else:
        print "Test FAILED"
        sys.exit(1)

smtcmd = """
read_verilog -formal {0}
prep -top {1}
memory -nordff
write_smt2 {1}.smt2"""
def smt2():
    if len(sys.argv) != 4:
        help()
    solver = sys.argv[3]
    fname = sys.argv[2]
    rawname = os.path.splitext(fname)[0]
    deps = convert(extract_deps(fname))
    os.system("echo '" + smtcmd.format(" ".join(deps),rawname) +"' | yosys -q")  
    if os.system("yosys-smtbmc -t 7 -s {0} {1}.smt2".format(solver,rawname)) == 0 and \
        os.system("yosys-smtbmc -t 7 -i -s {0} {1}.smt2".format(solver,rawname)) == 0 and \
        os.system("yosys-smtbmc -t 7 -c -s {0} {1}.smt2".format(solver,rawname)) == 0:
            print "Test PASSED"
    else:
        print "Test FAILED"
        sys.exit(1)




def main():
    if len(sys.argv) < 2:
        help()
    arg = sys.argv[1]
    if arg == "build":
        build()
    elif arg == "install":
        install()
    elif arg == "test":
        test()
    elif arg == "formal":
        formal()
    elif arg == "smt2":
        smt2()
    else:
        help()
        
if __name__ == "__main__":
    main()

