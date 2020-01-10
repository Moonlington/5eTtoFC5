import xml.etree.cElementTree as ET
import json
import re
import sys
import os
import argparse
import copy

import utils
from monster import parseMonster
from item import parseItem
from spell import parseSpell

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
    mwins = 0
    mloss = 0
    iwins = 0
    iloss = 0
    swins = 0
    sloss = 0
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
        mwins = 0
        mloss = 0
        iwins = 0
        iloss = 0
        swins = 0
        sloss = 0
    if 'monster' in d:
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
    if 'spell' in d:
        for m in d['spell']:
            if ignoreError:
                try:
                    parseSpell(m, compendium, args)
                    swins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    sloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseSpell(m, compendium, args)
                swins += 1
    if 'item' in d:
        for m in d['item']:
            if ignoreError:
                try:
                    parseItem(m, compendium, args)
                    iwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    iloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseItem(m, compendium, args)
                iwins += 1
    if 'baseitem' in d:
        for m in d['baseitem']:
            if ignoreError:
                try:
                    parseItem(m, compendium, args)
                    iwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    iloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseItem(m, compendium, args)
                iwins += 1
        with open("./data/magicvariants.json") as f:
            mv = json.load(f)
            f.close()
        if 'variant' in mv:
            for v in mv['variant']:
                if args.verbose:
                    print("Processing Variants: " + v['name'])
                for req in v['requires']:
                    for m in d['baseitem']:
                        itemMatch = False
                        for k in req:
                            if k in m and m[k] == req[k]:
                                itemMatch = True
                            else:
                                itemMatch = False
                        if 'excludes' in v:
                            for ex in v['excludes']:
                                if type(v['excludes'][ex]) == list:
                                    if any(sub in m[ex] for sub in v['excludes'][ex]): itemMatch = False
                                elif ex in m and type(v['excludes'][ex]) != str:
                                    if v['excludes'][ex] == m[ex]:
                                        itemMatch = False
                                elif ex in m and v['excludes'][ex] in m[ex]:
                                    itemMatch = False
                        if not itemMatch:
                            continue
                        else:
                            if args.verbose:
                                print ("Creating",v['name'],"for",m['name'])
                            mm = copy.deepcopy(m)
                            mm['baseName'] = mm['name']
                            #if 'entries' in v and 'entries' in m:
                            #    mm['entries'] = v['entries'] + m['entries']
                            #elif 'entries' in v :
                            #    mm['entries'] = [] + v['entries']
                            for inheritk in v['inherits']:
                                inherit = copy.deepcopy(v['inherits'][inheritk])
                                if inheritk == 'entries' and 'entries' in mm:
                                    mm['entries'] += inherit
                                elif inheritk == 'entries':
                                    mm['entries'] = inherit 
                                elif inheritk == 'namePrefix':
                                    mm['name'] = inherit + mm['name']
                                elif inheritk == 'nameSuffix':
                                    mm['name'] = mm['name'] + inherit
                                else:
                                    mm[inheritk] = inherit

                        if ignoreError:
                            try:
                                parseItem(mm, compendium, args)
                                iwins += 1
                            except Exception:
                                print("FAILED: " + mm['name'])
                                iloss += 1
                                continue
                        else:
                            if args.verbose:
                                print("Parsing " + mm['name'],len(mm))
                            parseItem(mm, compendium, args)
                            iwins += 1
    print("Done converting " + os.path.splitext(file)[0])

    if not args.combinedoutput:
        if mwins > 0 or mloss > 0:
            print("Converted {}/{} monsters (failed {})".format(mwins, mwins +
                                                            mloss, mloss) if ignoreError else "Converted {} monsters".format(mwins))
        if swins > 0 or sloss > 0:
            print("Converted {}/{} spells (failed {})".format(swins, swins +
                                                            sloss, sloss) if ignoreError else "Converted {} spells".format(swins))
        if iwins > 0 or iloss > 0:
            print("Converted {}/{} items (failed {})".format(iwins, iwins +
                                                            iloss, iloss) if ignoreError else "Converted {} items".format(iwins))

        # write to file
        tree = ET.ElementTree(utils.indent(compendium, 1))
        tree.write(
            os.path.splitext(file)[0] +
            ".xml",
            xml_declaration=True,
            encoding='utf-8')
if args.combinedoutput:
    if mwins > 0 or mloss > 0:
        print("Converted {}/{} monsters (failed {})".format(mwins, mwins + mloss,
                                                        mloss) if ignoreError else "Converted {} monsters".format(mwins))
    if swins > 0 or sloss > 0:
        print("Converted {}/{} spells (failed {})".format(swins, swins + sloss,
                                                        sloss) if ignoreError else "Converted {} spells".format(swins))
    if iwins > 0 or iloss > 0:
        print("Converted {}/{} items (failed {})".format(iwins, iwins + iloss,
                                                        iloss) if ignoreError else "Converted {} items".format(iwins))
    # write to file
    tree = ET.ElementTree(utils.indent(compendium, 1))
    tree.write(args.combinedoutput, xml_declaration=True, encoding='utf-8')
