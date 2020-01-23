# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import xml.etree.cElementTree as ET
import json
import re
import sys
import os
import argparse
import copy
import requests

import utils
from monster import parseMonster
from item import parseItem
from spell import parseSpell
from cclass import parseClass

# Argument Parser
parser = argparse.ArgumentParser(
    description="Converts 5eTools json files to FC5 compatible XML files.")
parser.add_argument('inputJSON', nargs="*", type=str, help="5eTools inputs")
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
parser.add_argument(
    '--show-dupes',
    dest="showdupe",
    action='store_const',
    const=True,
    default=False,
    help="show duplicates (default: false)")
parser.add_argument(
    '--no-html',
    dest="nohtml",
    action='store_const',
    const=True,
    default=False,
    help="no html tags (default: false)")
parser.add_argument(
    '--images',
    dest="addimgs",
    action='store_const',
    const=True,
    default=False,
    help="copy images to compendium directories (default: false)")
parser.add_argument(
    '--futuristic-items',
    dest="futuristic",
    action='store_const',
    const=True,
    default=False,
    help="include futuristic items (default: false)")
parser.add_argument(
    '--modern-items',
    dest="modern",
    action='store_const',
    const=True,
    default=False,
    help="include modern items (default: false)")
parser.add_argument(
    '--renaissance-items',
    dest="renaissance",
    action='store_const',
    const=True,
    default=False,
    help="include renaissance items (default: false)")
parser.add_argument(
    '--update-data-from',
    dest="updatedata",
    action='store',
    default=None,
    nargs=1,
    help="update date from url")





args = parser.parse_args()

if args.updatedata:
    if not args.updatedata[0].startswith("http"):
        baseurl = "https://{}/data".format(args.updatedata[0].rstrip('/'))
    else:
        baseurl = "{}/data".format(args.updatedata[0].rstrip('/'))
    datadir = "data"
    classdir = os.path.join(datadir,"class")
    bestiarydir = os.path.join(datadir,"bestiary")
    spellsdir = os.path.join(datadir,"spells")
    items = [ 'items.json','items-base.json','magicvariants.json','vehicles.json','fluff-vehicles.json' ]

    try:
        if not os.path.exists(datadir):
            os.mkdir(datadir)
        if not os.path.exists(classdir):
            os.mkdir(classdir)
        if not os.path.exists(bestiarydir):
            os.mkdir(bestiarydir)
        if not os.path.exists(spellsdir):
            os.mkdir(spellsdir)

        for f in items:
            print("Downloading:","/"+f)
            req = requests.get(baseurl + "/"+f)
            with open(os.path.join(datadir,f), 'wb') as f:
                f.write(req.content)
                f.close()
        print("Downloading bestiary index:","/bestiary/index.json")
        req = requests.get(baseurl + "/bestiary/index.json")
        with open(os.path.join(bestiarydir,"index.json"), 'wb') as f:
            f.write(req.content)
            f.close()
        with open(os.path.join(bestiarydir,"index.json"),encoding='utf-8') as f:
            idx = json.load(f)
            f.close()
        for k,v in idx.items():
            print("Downloading source {}: {}".format(k,v))
            req = requests.get(baseurl + "/bestiary/" + v)
            with open(os.path.join(bestiarydir,v), 'wb') as f:
                f.write(req.content)
                f.close()
        print("Downloading bestiary fluff index:","/bestiary/fluff-index.json")
        req = requests.get(baseurl + "/bestiary/fluff-index.json")
        with open(os.path.join(bestiarydir,"fluff-index.json"), 'wb') as f:
            f.write(req.content)
            f.close()
        with open(os.path.join(bestiarydir,"fluff-index.json"),encoding='utf-8') as f:
            idx = json.load(f)
            f.close()
        for k,v in idx.items():
            print("Downloading fluff source {}: {}".format(k,v))
            req = requests.get(baseurl + "/bestiary/" + v)
            with open(os.path.join(bestiarydir,v), 'wb') as f:
                f.write(req.content)
                f.close()

        print("Downloading class index:","/class/index.json")
        req = requests.get(baseurl + "/class/index.json")
        with open(os.path.join(classdir,"index.json"), 'wb') as f:
            f.write(req.content)
            f.close()
        with open(os.path.join(classdir,"index.json"),encoding='utf-8') as f:
            idx = json.load(f)
            f.close()
        for k,v in idx.items():
            print("Downloading source {}: {}".format(k,v))
            req = requests.get(baseurl + "/class/" + v)
            with open(os.path.join(classdir,v), 'wb') as f:
                f.write(req.content)
                f.close()
        print("Downloading spells index:","/spells/index.json")
        req = requests.get(baseurl + "/spells/index.json")
        with open(os.path.join(spellsdir,"index.json"), 'wb') as f:
            f.write(req.content)
            f.close()
        with open(os.path.join(spellsdir,"index.json"),encoding='utf-8') as f:
            idx = json.load(f)
            f.close()
        for k,v in idx.items():
            print("Downloading source {}: {}".format(k,v))
            req = requests.get(baseurl + "/spells/" + v)
            with open(os.path.join(spellsdir,v), 'wb') as f:
                f.write(req.content)
                f.close()
    except Exception as e:
        print("Could not update data:",e)
    sys.exit()

excludedages = []
if not args.futuristic:
    excludedages.append('futuristic')
if not args.modern:
    excludedages.append('modern')
if not args.renaissance:
    excludedages.append('renaissance')

if args.combinedoutput:
    # Building XML file
    compendium = ET.Element(
        'compendium', {'version': "5", 'auto_indent': "NO"})
    mwins = 0
    mloss = 0
    mdupe = 0
    iwins = 0
    iloss = 0
    idupe = 0
    swins = 0
    sloss = 0
    sdupe = 0
    cwins = 0
    closs = 0
for file in args.inputJSON:
    with open(file,encoding='utf-8') as f:
        d = json.load(f)
        f.close()

    fluff = None

    if os.path.isfile(os.path.split(file)[0] + "/fluff-" + os.path.split(file)[1]):
        if args.verbose:
            print("Fluff file found:",os.path.split(file)[0] + "/fluff-" + os.path.split(file)[1])
        with open(os.path.split(file)[0] + "/fluff-" + os.path.split(file)[1],encoding='utf-8') as f:
            fluff = json.load(f)
            f.close()

    ignoreError = args.IE
    if not args.combinedoutput:
        # Building XML file
        compendium = ET.Element(
            'compendium', {
                'version': "5", 'auto_indent': "NO"})
        mwins = 0
        mloss = 0
        mdupe = 0
        iwins = 0
        iloss = 0
        idupe = 0
        swins = 0
        sloss = 0
        sdupe = 0
        cwins = 0
        closs = 0
    if 'monster' in d:
        for m in d['monster']:
            if m['name'] in ['Gar Shatterkeel','Shoalar Quanderil'] and m['source'] == 'LR':
                m['original_name']=m['name']
                m['name'] += "–"+utils.getFriendlySource(m['source'])
            if m['name'] in ['Harpy','Felidar','Kraken'] and m['source'] in ['PSX','PSZ']:
                m['original_name']=m['name']
                m['name'] += "–"+utils.getFriendlySource(m['source'])
            if m['name'] == 'Darathra Shendrel' and m['source'] == "SKT":
                m['original_name']=m['name']
                m['name'] += "–"+utils.getFriendlySource(m['source'])
            if m['name'] == "Demogorgon" and m['source'] == "HftT":
                m['original_name']=m['name']
                m['name'] += " (monstrosity)"
            if m['name'] == "Tressym" and m['source'] == "BGDIA":
                m['original_name']=m['name']
                m['name'] += " (monstrosity)"
            if m['name'] == "Amphisbaena" and m['source'] == "GoS":
                m['original_name']=m['name']
                m['name'] += " (monstrosity)"
            if m['name'] == "Large Mimic" and m['source'] == "RMBRE":
                m['original_name']=m['name']
                m['name'] += " (Multiattack)"
            if m['source'] == "UAArtificerRevisited":
                m['original_name']=m['name']
                m['name'] += " (Unearthed Arcana)"
            for xmlmon in compendium.findall("./monster[name='{}']".format(re.sub(r'\'','*',m['name']))):
                if args.verbose or args.showdupe:
                    print ("{0} in {1} is duplicate entry for {2} from {3}".format(m['name'],utils.getFriendlySource(m['source']),xmlmon.find('name').text,xmlmon.find('source').text))
                mdupe += 1
            if fluff is not None and 'monster' in fluff:
                if 'entries' in m:
                    m['entries'] += utils.appendFluff(fluff,m['name'])
                else:
                    m['entries'] = utils.appendFluff(fluff,m['name'])
                if 'image' not in m:
                    m['image'] = utils.findFluffImage(fluff,m['name'])
            if ignoreError:
                try:
                    parseMonster(m, compendium, args)
                    mwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    mloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseMonster(m, compendium, args)
                mwins += 1
    if 'vehicle' in d:
        for m in d['vehicle']:
            if m['source'].startswith("UA"):
                m['original_name'] = m['name']
                m['name'] += " (Unearthed Arcana)"
            for xmlmon in compendium.findall("./monster[name='{}']".format(re.sub(r'\'','*',m['name']))):
                if args.verbose or args.showdupe:
                    print ("{0} in {1} is duplicate entry for {2} from {3}".format(m['name'],utils.getFriendlySource(m['source']),xmlmon.find('name').text,xmlmon.find('source').text))
                mdupe += 1
            if fluff is not None and 'vehicle' in fluff:
                if 'entries' in m:
                    m['entries'] += utils.appendFluff(fluff,m['name'],'vehicle')
                else:
                    m['entries'] = utils.appendFluff(fluff,m['name'],'vehicle')
                if 'image' not in m:
                    m['image'] = utils.findFluffImage(fluff,m['name'],'vehicle')
            if 'alignment' not in m:
                m['alignment'] = [ 'U' ]
            if m['vehicleType'] == "INFWAR":
                m['type'] = "vehicle ({:,d} lb.)".format(m['weight'])
                m['ac'] = [ "{} (19 while motionless)".format(19+utils.getAbilityMod(m["dex"])) ]
                m['hp'] = { "special": "{} (damage threshold {}, mishap threshold {})".format(m['hp']['hp'],m['hp']['dt'],m['hp']['mt']) }
                if 'action' not in m:
                    m['action'] = m['actionStation']
                else:
                    m['action'] += m['actionStation']
                m['speed'] = "{} ft.".format(m['speed'])
            elif m['vehicleType'] == "SHIP":
                m['type'] = "vehicle ({} x {})".format(m['dimensions'][0],m['dimensions'][1])
                m['ac'] = [ m['hull']['ac'] ]
                m['hp'] = { "special": str(m['hull']['hp']) }
                if not 'trait' in m:
                    m['trait'] = []
                if 'hull' in m:
                    if args.nohtml:
                        m['trait'].append({
                            "name": "Hull",
                            "entries": [
                                " ",
                                "Armor Class: {}".format(m['hull']['ac']),
                                "Hit Points: {}{}{}".format(m['hull']['hp'],
                                        " (damage threshold {})".format(m['hull']['dt']) if 'dt' in m['hull'] else '',
                                        "; " + m['hull']['hpNote'] if 'hpNote' in m['hull'] else "")
                            ] })
                    else:
                        m['trait'].append({
                            "name": "Hull",
                            "entries": [
                                " ",
                                "<i>Armor Class:</i> {}\n".format(m['hull']['ac']),
                                "<i>Hit Points:</i> {}{}{}".format(m['hull']['hp'],
                                        " (damage threshold {})".format(m['hull']['dt']) if 'dt' in m['hull'] else '',
                                        "; " + m['hull']['hpNote'] if 'hpNote' in m['hull'] else "")
                            ] })
                if 'control' in m:
                    for c in m['control']:
                        if args.nohtml:
                            trait = {
                                "name": "Control:",
                                "entries": [
                                    "{}".format(c['name']),
                                    "Armor Class: {}".format(c['ac']),
                                    "Hit Points: {}{}{}".format(c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                     ]
                                }
                        else:
                            trait = {
                                "name": "Control:",
                                "entries": [
                                    "<i>{}</i>".format(c['name']),
                                    "<i>Armor Class:</i> {}".format(c['ac']),
                                    "<i>Hit Points:</i> {}{}{}".format(c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                     ]
                                }
                        if 'entries' in c:
                            trait['entries'] += c['entries']
                        m['trait'].append(trait)
                if 'movement' in m:
                    for c in m['movement']:
                        if args.nohtml:
                            trait = {
                                "name": "Movement:",
                                "entries": [
                                    "{}".format(c['name']),
                                    "Armor Class: {}".format(c['ac']),
                                    "Hit Points: {}{}{}".format(c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                    ]
                                }
                        else:
                            trait = {
                                "name": "Movement:",
                                "entries": [
                                    "<i>{}</i>".format(c['name']),
                                    "<i>Armor Class:</i> {}".format(c['ac']),
                                    "<i>Hit Points:</i> {}{}{}".format(c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                    ]
                                }
                        if 'locomotion' in c:
                            for l in c['locomotion']:
                                if args.nohtml:
                                    trait['entries'].append("Locomotion ({}): ".format(l['mode']) + "\n".join(l['entries']))
                                else:
                                    trait['entries'].append("<i>Locomotion ({}):</i> ".format(l['mode']) + "\n".join(l['entries']))
                        if 'entries' in c:
                            trait['entries'] += c['entries']
                        m['trait'].append(trait)
                if 'weapon' in m:
                    for c in m['weapon']:
                        if args.nohtml:
                            trait = {
                                "name": "Weapons:",
                                "entries": [
                                    "{}{}".format(c['name']," ({})".format(c["count"]) if 'count' in c else ""),
                                    "Armor Class: {}".format(c['ac']),
                                    "Hit Points: {}{}{}{}".format(
                                        c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        " each" if 'count' in c and c["count"] > 1 else "",
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                    ]
                                }
                        else:
                            trait = {
                                "name": "Weapons:",
                                "entries": [
                                    "<i>{}{}</i>".format(c['name']," ({})".format(c["count"]) if 'count' in c else ""),
                                    "<i>Armor Class:</i> {}".format(c['ac']),
                                    "<i>Hit Points:</i> {}{}{}{}".format(
                                        c['hp'],
                                        " (damage threshold {})".format(c['dt']) if 'dt' in c else '',
                                        " each" if 'count' in c and c["count"] > 1 else "",
                                        "; "+c['hpNote'] if 'hpNote' in c else '')
                                    ]
                                }
                        if 'entries' in c:
                            trait['entries'] += c['entries']
                        if 'action' not in m:
                            m['action'] = []
                        m['action'].append(trait)
                m['speed'] = "{} miles per hour ({} miles per day)".format(m['pace'],m['pace']*24)
            else:
                m['type'] = m['vehicleType']
                m['ac'] = "Unknown"
            if ignoreError:
                try:
                    parseMonster(m, compendium, args)
                    mwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    mloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseMonster(m, compendium, args)
                mwins += 1

    if 'spell' in d:
        for m in d['spell']:
            for xmlmon in compendium.findall("./spell[name='{}']".format(re.sub(r'\'','*',m['name']))):
                if args.verbose or args.showdupe:
                    print ("Found duplicate entry for {} from {}".format(m['name'],xmlmon.find('source').text))
                sdupe += 1

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
    if 'class' in d:
        for m in d['class']:
            if ignoreError:
                try:
                    parseClass(m, compendium, args)
                    cwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    closs += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseClass(m, compendium, args)
                cwins += 1
    if 'item' in d:
        for m in d['item']:
            if 'age' in m and m['age'].lower() in excludedages:
                if args.verbose:
                    print ("SKIPPING",m['age'],"ITEM:",m['name'])
                continue

            if m['name'] == "Trinket" and m['source'] == "CoS":
                m['name'] += " (Gothic)"
            elif m['name'] == "Trinket" and m['source'] == "EET":
                m['name'] += " (Elemental Evil)"
            elif m['name'] == "Trinket" and m['source'] == "AI":
                m['name'] += " (Acquisitions Incorporated)"
            elif m['name'] == "Ioun Stone" and m['source'] == "LLK":
                m['name'] += " (Kwalish)"

            for xmlmon in compendium.findall("./item[name='{}']".format(re.sub(r'\'','*',m['name']))):
                if args.verbose or args.showdupe:
                    print ("Found duplicate entry for {} from {}".format(m['name'],xmlmon.find('source').text))
                idupe += 1

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
    if 'itemGroup' in d:
        for m in d['itemGroup']:
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
            if 'age' in m and m['age'].lower() in excludedages:
                if args.verbose:
                    print ("SKIPPING",m['age'],"ITEM:",m['name'])
                continue
            if ignoreError:
                try:
                    parseItem(copy.deepcopy(m), compendium, args)
                    iwins += 1
                except Exception:
                    print("FAILED: " + m['name'])
                    iloss += 1
                    continue
            else:
                if args.verbose:
                    print("Parsing " + m['name'])
                parseItem(copy.deepcopy(m), compendium, args)
                iwins += 1
        with open("./data/magicvariants.json",encoding='utf-8') as f:
            mv = json.load(f)
            f.close()
        if 'variant' in mv:
            for v in mv['variant']:
                if 'age' in m and m['age'].lower() in excludedages:
                    if args.verbose:
                        print ("SKIPPING",m['age'],"ITEM:",m['name'])
                    continue
                if args.verbose:
                    print("Processing Variants: " + v['name'])
                for req in v['requires']:
                    for m in d['baseitem']:
                        if 'age' in m and m['age'].lower() in excludedages:
                            if args.verbose:
                                print ("SKIPPING",m['age'],"ITEM:",m['name'])
                            continue
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
                            if 'items' not in v:
                                v['items'] = []
                            if args.verbose:
                                print ("Creating",v['name'],"for",m['name'])
                            mm = copy.deepcopy(m)
                            if 'value' in mm:
                                del mm['value']
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
                                    v[inheritk] = inherit
                            v['items'].append(mm['name'])
                            if mm['name'] in mv['linkedLootTables']['DMG']:
                                if 'lootTables' not in mm:
                                    mm['lootTables'] = []
                                mm['lootTables'] += mv['linkedLootTables']['DMG'][mm['name']]
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
                if 'items' in v:
                    if ignoreError:
                        try:
                            parseItem(v, compendium, args)
                            iwins += 1
                        except Exception:
                            print("FAILED: " + v['name'])
                            iloss += 1
                            continue
                    else:
                        if args.verbose:
                            print("Parsing " + v['name'],len(v))
                        parseItem(v, compendium, args)
                        iwins += 1

    print("Done converting " + os.path.splitext(file)[0])

    if not args.combinedoutput:
        if mwins > 0 or mloss > 0:
            print("Converted {}/{} monsters (failed {})".format(mwins, mwins +
                                                            mloss, mloss) if ignoreError else "Converted {} monsters".format(mwins))
            if mdupe > 0: print(" ({} duplicate{})".format(mdupe,"s" if mdupe > 1 else ""))
        if swins > 0 or sloss > 0:
            print("Converted {}/{} spells (failed {})".format(swins, swins +
                                                            sloss, sloss) if ignoreError else "Converted {} spells".format(swins))
            if sdupe > 0: print(" ({} duplicate{})".format(sdupe,"s" if sdupe > 1 else ""))
        if cwins > 0 or closs > 0:
            print("Converted {}/{} classes (failed {})".format(cwins, cwins +
                                                            closs, closs) if ignoreError else "Converted {} classes".format(cwins))

        if iwins > 0 or iloss > 0:
            print("Converted {}/{} items (failed {})".format(iwins, iwins +
                                                            iloss, iloss) if ignoreError else "Converted {} items".format(iwins))
            if idupe > 0: print(" ({} duplicate{})".format(idupe,"s" if idupe > 1 else ""))
        # write to file
        tree = ET.ElementTree(utils.indent(compendium, 1))
        tree.write(
            os.path.splitext(file)[0] +
            ".xml",
            xml_declaration=True,
            short_empty_elements=False,
            encoding='utf-8')
if args.combinedoutput:
    if mwins > 0 or mloss > 0:
        print("Converted {}/{} monsters (failed {})".format(mwins, mwins + mloss,
                                                        mloss) if ignoreError else "Converted {} monsters".format(mwins))
        if mdupe > 0: print(" ({} duplicate{})".format(mdupe,"s" if mdupe > 1 else ""))
    if swins > 0 or sloss > 0:
        print("Converted {}/{} spells (failed {})".format(swins, swins + sloss,
                                                        sloss) if ignoreError else "Converted {} spells".format(swins))
        if sdupe > 0: print(" ({} duplicate{})".format(sdupe,"s" if sdupe > 1 else ""))
    if cwins > 0 or closs > 0:
        print("Converted {}/{} classes (failed {})".format(cwins, cwins + closs,
                                                        closs) if ignoreError else "Converted {} classes".format(cwins))
    if iwins > 0 or iloss > 0:
        print("Converted {}/{} items (failed {})".format(iwins, iwins + iloss,
                                                        iloss) if ignoreError else "Converted {} items".format(iwins))
        if idupe > 0: print(" ({} duplicate{})".format(idupe,"s" if idupe > 1 else ""))
    # write to file
    tree = ET.ElementTree(utils.indent(compendium, 1))
    tree.write(args.combinedoutput, xml_declaration=True, short_empty_elements=False, encoding='utf-8')
