import xml.etree.cElementTree as ET
import json
import re
import sys
import os
import argparse

import utils
from monster import parseMonster

# Argument Parser
parser = argparse.ArgumentParser(
    description="Converts 5eTools json files to FC5 compatible XML files.")
parser.add_argument('inputJSON', nargs="+", type=str, help="5eTools inputs")
parser.add_argument(
    '--ignore',
    dest="IE",
    action='store_const',
    const=True,
    default=False,
    help="ignores errors (default: false)")
parser.add_argument(
    '-v',
    dest="verbose",
    action='store_const',
    const=True,
    default=False,
    help="verbose output (default: false)")
parser.add_argument(
    '-o',
    dest="combinedoutput",
    action='store',
    default=False,
    help="combines inputs into given output (default: false)")
args = parser.parse_args()

if args.combinedoutput:
    # Building XML file
    compendium = ET.Element(
        'compendium', {'version': "5", 'auto_indent': "NO"})
    wins = 0
    loss = 0

for file in args.inputJSON:
    with open(file) as f:
        d = json.load(f)
        f.close()

    ignoreError = args.IE
    if not args.combinedoutput:
        # Building XML file
        compendium = ET.Element(
            'compendium', {
                'version': "5", 'auto_indent': "NO"})
        wins = 0
        loss = 0
    for m in d['monster']:
        if ignoreError:
            try:
                parseMonster(m, compendium, args)
                wins += 1
            except Exception:
                print("FAILED: " + m['name'])
                loss += 1
                continue
        else:
            if args.verbose:
                print("Parsing " + m['name'])
            parseMonster(m, compendium, args)
            wins += 1
    print("Done converting " + os.path.splitext(file)[0])

    if not args.combinedoutput:
        print("Converted {}/{} monsters (failed {})".format(wins, wins +
                                                            loss, loss) if ignoreError else "Converted {} monsters".format(wins))
        # write to file
        tree = ET.ElementTree(utils.indent(compendium, 1))
        tree.write(
            os.path.splitext(file)[0] +
            ".xml",
            xml_declaration=True,
            encoding='utf-8')
if args.combinedoutput:
    print("Converted {}/{} monsters (failed {})".format(wins, wins + loss,
                                                        loss) if ignoreError else "Converted {} monsters".format(wins))
    # write to file
    tree = ET.ElementTree(utils.indent(compendium, 1))
    tree.write(args.combinedoutput, xml_declaration=True, encoding='utf-8')
