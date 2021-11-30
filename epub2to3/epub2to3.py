#! /usr/bin/env python3
"""Epub 2 to Epub 3 conversion workflow.
"""
#
# Copyright (C) 2021, Johan van der Knijff, Koninklijke Bibliotheek
#  National Library of the Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import io
import json
import argparse
import subprocess as sub
from epubcheck import EpubCheck
from . import config as config

scriptPath, scriptName = os.path.split(sys.argv[0])

# Fix empty scriptName if isolyzer is called from Java/Jython
if len(scriptName) == 0:
    scriptName = 'epub2to3'

__version__ = '0.0.1'

# Create parser
parser = argparse.ArgumentParser(
    description="Epub 2 to epub 3 conversion workflow")


def printWarning(msg):
    """Print warning to stderr"""
    msgString = ("User warning: " + msg + "\n")
    sys.stderr.write(msgString)


def errorExit(msg):
    """Print warning to stderr and exit"""
    msgString = ("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = fileIn + " does not exist"
        errorExit(msg)


def launchSubProcess(args):
    """Launch subprocess and return exit code, stdout and stderr"""
    try:
        # Execute command line; stdout + stderr redirected to objects
        # 'output' and 'errors'.
        # Setting shell=True avoids console window poppong up with pythonw
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, shell=False)
        output, errors = p.communicate()

        # Decode to UTF8
        outputAsString = output.decode('utf-8')
        errorsAsString = errors.decode('utf-8')

        exitStatus = p.returncode

    except Exception:
        # I don't even want to to start thinking how one might end up here ...

        exitStatus = -99
        outputAsString = ""
        errorsAsString = ""

    return(p, exitStatus, outputAsString, errorsAsString)


def convertEpub(epubIn, dirOut):
    """Convert Epub 2 to epub 3 with dp2 tool"""
    args = [dp2Binary]
    args.append(''.join(['--ws_timeup']))
    args.append(''.join(['0']))
    args.append(''.join(['epub2-to-epub3']))
    args.append(''.join(['--source']))
    args.append(''.join([epubIn]))
    args.append(''.join(['--output']))
    args.append(''.join([dirOut]))
    p, status, out, err = launchSubProcess(args)
    return p, status, out, err


def parseCommandLine():
    """Parse command line"""
    # Add arguments
    parser.add_argument('dirIn',
                        action="store",
                        type=str,
                        help="input directory")
    parser.add_argument('dirOut',
                        action="store",
                        type=str,
                        help="output directory")
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__)

    # Parse arguments
    args = parser.parse_args()

    return args


def main():
    """Main workflow"""

    # Get config
    global dp2Binary
    dp2Binary = config.dp2Binary

    if not os.path.isfile(dp2Binary):
        msg = ('dp 2 binary does not exist!')
        errorExit(msg)

    # Get input from command line
    args = parseCommandLine()
    dirIn = os.path.abspath(args.dirIn)
    dirOut = os.path.abspath(args.dirOut)

    epubs = os.listdir(dirIn)

    ecList = []

    for epub in epubs:
        success = True
        epubIn = os.path.join(dirIn, epub)
        epubOut = os.path.join(dirOut, 'output-dir', epub)

        convP, convStatus, convOut, convErr = convertEpub(epubIn, dirOut)
        if convP.returncode != 0:
            success = False

        # Analyse output file with Epubcheck
        if success:
            ecOut = EpubCheck(epubOut)
            ecOutMessages = ecOut.messages

            ecResults = {}
            ecResults['file'] = epubOut
            ecResults['valid'] = ecOut.valid
            messages = []
            for ecOutMessage in ecOutMessages:
                message = {}
                message['id'] = ecOutMessage.id
                message['level'] = ecOutMessage.level
                message['location'] = ecOutMessage.location
                message['message'] = ecOutMessage.message
                messages.append(message)
                print(ecOutMessage.message)
            
            ecResults['messages'] = messages
            ecList.append(ecResults)

    # Write EPUBCheck output to JSON file
    ecOutFile = os.path.join(dirOut, "epubcheck.json")
    try:
        with io.open(ecOutFile, 'w', encoding='utf-8') as f:
            json.dump(ecList, f, indent=4, sort_keys=True)
    except IOError:
        errorExit('error while writing epubcheck output file')

if __name__ == "__main__":
    main()
