import os.path
import re
import subprocess
import sys

def runlist(filename, runlistName):
    """
    USE AND RESULTS
    ===============

    runlist takes a runlist file and a list name and executes the commands defined
    in that list. The runlist files contains commands that should be run and their
    parameters.

    RELEVANT PARAMETERS

    ===================

    --filename  ... The runlist.txt file containing runlists and their parameters.
    --runlistName  ... Name of the list inside runlist.txt to run.

    EXAMPLE USE
    ===========

    runlist filename="/Users/john/Documents/runlist.txt" runlistName="map_preprocess_fn_data"

    ---
    Written by Jure Demšar.
    """

    if not os.path.exists(filename):
        print "\n\n=====================================================\nERROR: runlist file does not exist [%s]" % (filename)
        raise RuntimeError("ERROR: runlist file not found: %s" % (filename))

    s = file(filename).read()

    # cleanup
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = re.sub("^#.*?\n", "", s)

    # split to settings and list
    s = s.split("---")

    try:
        # parameters string
        ps = s[0].split("\n")
        parameters = {}
        for line in ps:
            line = line.strip()

            # skip comments and empty lines
            if line=="" or line[0]=="#":
                continue
            
            # split line to setting and value
            lineSplit = line.split("=", 1)
            if len(lineSplit) != 2:
                print "\n\n=====================================================\nERROR: cannot parse line [%s]" % (line)
                raise ValueError("ERROR: cannot parse line [%s]" % (line))
            else:
                parameters[lineSplit[0]] = lineSplit[1]

        # find the list
        listFound = False
        for i in range(1, len(s)):
            # appropriate list already found
            if listFound:
                break

            # list string
            ls = s[i].split("\n")

            # find list name
            while len(ls) > 0:
                line = ls[0]
                ls.remove(line)
                line = line.strip()

                # skip comments and empty lines
                if line=="" or line[0]=="#":
                    continue

                # split line to setting and value
                lineSplit = line.split("=", 1)
                if len(lineSplit) != 2:
                    print "\n\n=====================================================\nERROR: cannot parse line [%s]" % (line)
                    raise ValueError("ERROR: cannot parse line [%s]" % (line))
                else:
                    lineSplit[0] = stripQuotes(lineSplit[0])
                    lineSplit[1] = stripQuotes(lineSplit[1])
                    # list found?
                    if lineSplit[0] == "list":
                        if lineSplit[1] == runlistName:
                            listFound = True
                        break
                    else:
                        print "\n\n=====================================================\nERROR: expeciting list name, found: [%s]" % (line)
                        raise ValueError("ERROR: expeciting list name, found: [%s]" % (line))

        if not listFound:
            print "\n\n=====================================================\nERROR: runlistName does not exist [%s]" % (runlistName)
            raise ValueError("ERROR: list not found: %s" % (runlistName))

        # parse list parameters
        while len(ls) > 0:
            line = ls[0]
            lineStrip = line.strip()

            # skip comments and empty lines
            if lineStrip=="" or lineStrip[0]=="#":
                continue

            # split line to setting and value
            lineSplit = lineStrip.split("=", 1)
            if len(lineSplit) != 2:
                print "\n\n=====================================================\nERROR: cannot parse line [%s]" % (line)
                raise ValueError("ERROR: cannot parse line [%s]" % (line))
            else:
                # parameter or command?
                if lineSplit[0] != "command":
                    parameters[lineSplit[0]] = lineSplit[1]
                    ls.remove(line)
                else:
                    break

        # parse commands
        commands = []
        # parse list parameters
        while len(ls) > 0:
            line = ls[0]
            ls.remove(line)
            line = line.strip()

            # skip comments and empty lines
            if line=="" or line[0]=="#":
                continue

            # split line to setting and value
            lineSplit = line.split("=", 1)
            if len(lineSplit) != 2:
                print "\n\n=====================================================\nERROR: cannot parse line [%s]" % (line)
                raise ValueError("ERROR: cannot parse line [%s]" % (line))
            else:
                # parameter or command
                if lineSplit[0] == "command":
                    lineSplit[0] = stripQuotes(lineSplit[0])
                    lineSplit[1] = stripQuotes(lineSplit[1])
                    command = { "name":lineSplit[1], "parameters":parameters.copy() }
                    commands.append(command)
                else:
                    commands[-1]["parameters"][lineSplit[0]] = lineSplit[1]

        # process commands
        for c in commands:
            # build command
            command = c["name"]
            for key in c["parameters"]:
                command += " " + key + "=" + c["parameters"][key]
            
            # run
            print "\n===> Running command\n%s" % c["name"]

            process = subprocess.Popen("mnap " + command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            # Poll process for new output until finished
            while True:
                nextline = process.stdout.readline()
                if nextline == '' and process.poll() is not None:
                    break
                sys.stdout.write(nextline)
                sys.stdout.flush()

            returnCode = process.returncode
            if returnCode:
                print "\n\n=====================================================\nERROR: Failed with error %s" % (returnCode)
                raise subprocess.CalledProcessError("ERROR: Failed with error %s" % (returnCode), command)
            else:
                print "\n===> Successful completion of command %s" % c["name"]

        print "\n===> Successful completion of runlist %s" % runlistName

    except:
        print "\n\n=====================================================\nERROR: There was an error with the runlist file: \n%s\n\n--------\nError raised:\n" % (filename)
        raise

def stripQuotes(string):
    string = string.strip("\"")
    string = string.strip("'")
    return string

runlist("/Users/jure/Documents/niutilities/runlist/runlist.txt", "test_list")