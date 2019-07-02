import xml.etree.cElementTree as ET
import json
import re
import sys
import os
import argparse

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def parseRIV(m, t):
    lis = []
    for r in m[t]:
        if isinstance(r, dict):
            if 'special' in r:
                lis.append(r['special'])
            elif t in r:
                lis += parseRIV(r,t)
            elif 'resist' in r:
                lis += parseRIV(r, 'resist')
            else:
                lis.append("{}{}{}".format(r['preNote']+" " if 'preNote' in r else "",
                                                    ", ".join([x for x in r[t]]), " "+r['note'] if 'note' in r else ""))
        else:
            lis.append(r)
    return lis

def remove5eShit(s):
    s = re.sub(r'{@dc (.*?)}', r'DC \1', s)
    s = re.sub(r'{@hit \+?(.*?)}', r'+\1', s)
    s = re.sub(r'{@atk mw}', r'Melee Weapon Attack:', s)
    s = re.sub(r'{@atk rw}', r'Ranged Weapon Attack:', s)
    s = re.sub(r'{@atk ms}', r'Melee Spell Attack:', s)
    s = re.sub(r'{@atk rs}', r'Ranged Spell Attack:', s)
    s = re.sub(r'{@atk mw,rw}', r'Melee or Ranged Weapon Attack:', s)
    s = re.sub(r'{@atk r}', r'Ranged Attack:', s)
    s = re.sub(r'{@atk m}', r'Melee Attack:', s)
    s = re.sub(r'{@h}', r'', s)
    s = re.sub(r'{@recharge (.*?)}', r'(Recharge \1-6)', s)
    s = re.sub(r'{@recharge}', r'(Recharge 6)', s)
    s = re.sub(r'{@\w+ (.*?)(\|.*)?}', r'\1', s)
    return s.strip()


def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


def convertSize(s):
    return {
        'T': "Tiny",
        'S': "Small",
        'M': "Medium",
        'L': "Large",
        'H': "Huge",
        'G': "Gargantuan",
    }[s]


def convertAlign(s):
    if isinstance(s, dict):
        if 'special' in s:
            return s['special']
        else:
            if 'chance' in s:
                return " ".join([convertAlign(x) for x in s['alignment']]) + " ({}%)".format(s['chance'])
            return " ".join([convertAlign(x) for x in s['alignment']])
    else:
        alignment = s.upper()
        return {"L": "Lawful",
                "N": "Neutral",
                "NX": "Neutral (Law/Chaos axis)",
                "NY": "Neutral (Good/Evil axis)",
                "C": "Chaotic",
                "G": "Good",
                "E": "Evil",
                "U": "Unaligned",
                "A": "Any alignment",
                }[alignment]


def convertAlignList(s):
    if len(s) == 1:
        return convertAlign(s[0])
    elif len(s) == 2:
        return " ".join([convertAlign(x) for x in s])
    elif len(s) == 3:
        if "NX" in s and "NY" in s and "N" in s:
            return "Any Neutral Alignment"
    elif len(s) == 5:
        if not "G" in s:
            return "Any Non-Good Alignment"
        elif not "E" in s:
            return "Any Non-Evil Alignment"
        elif not "L" in s:
            return "Any Non-Lawful Alignment"
        elif not "C" in s:
            return "Any Non-Chaotic Alignment"
    elif len(s) == 4:
        if not "L" in s and not "NX"in s:
            return "Any Chaotic Alignment"
        if not "G" in s and not "NY"in s:
            return "Any Evil Alignment"
        if not "C" in s and not "NX"in s:
            return "Any Lawful Alignment"
        if not "E" in s and not "NY"in s:
            return "Any Good Alignment"

def parseMonster(m, compendium):
    if '_copy' in m:
        return
    monster = ET.SubElement(compendium, 'monster')
    name = ET.SubElement(monster, 'name')
    name.text = m['name']
    size = ET.SubElement(monster, 'size')
    size.text = m['size']

    typ = ET.SubElement(monster, 'type')
    if isinstance(m['type'], dict):
        if 'swarmSize' in m['type']:
            typ.text = "swarm of " + \
                convertSize(m['size'])+" " + m['type']['type'] + "s"
        else:
            subtypes = []
            for tag in m['type']['tags']:
                if not isinstance(tag, dict):
                    subtypes.append(tag)
                else:
                    subtypes.append(tag['prefix'] + tag['tag'])
            typ.text = "{} ({})".format(m['type']['type'], ", ".join(subtypes))
    else:
        typ.text = m['type']

    alignment = ET.SubElement(monster, 'alignment')
    alignment.text = convertAlignList(m['alignment'])

    ac = ET.SubElement(monster, 'ac')
    acstr = []
    for acs in m['ac']:
        if isinstance(acs, dict):
            if 'from' in acs:
                acstr.append("{} ({})".format(
                    acs['ac'], remove5eShit(acs['from'][0])))
            elif 'condition' in acs:
                acstr.append("{} ({})".format(
                    acs['ac'], remove5eShit(acs['condition'])))
        else:
            acstr.append(str(acs))
    ac.text = ", ".join(acstr)

    hp = ET.SubElement(monster, 'hp')
    if "special" in m['hp']:
        hp.text = m['hp']['special']
    else:
        hp.text = "{} ({})".format(m['hp']['average'], m['hp']['formula'])

    speed = ET.SubElement(monster, 'speed')
    if 'choose' in m['speed']:
        lis = []
        for key, value in m['speed'].items():
            if key == "walk":
                lis.append(str(value) + " ft.")
            elif key == "choose":
                value['from'].insert(-1, 'or')
                lis.append("{} {} ft.".format(", ".join(value['from']), value['amount']))
            else:
                lis.append("{} {} ft.".format(key, value))
        speed.text = "; ".join(lis)
    else:
        speed.text = ", ".join(["{} {} ft.".format(key, value['number'] if isinstance(value, dict) else value)
                                for key, value in m['speed'].items() if not isinstance(value, bool)])

    statstr = ET.SubElement(monster, 'str')
    statstr.text = str(m['str'])
    statdex = ET.SubElement(monster, 'dex')
    statdex.text = str(m['dex'])
    statcon = ET.SubElement(monster, 'con')
    statcon.text = str(m['con'])
    statint = ET.SubElement(monster, 'int')
    statint.text = str(m['int'])
    statwis = ET.SubElement(monster, 'wis')
    statwis.text = str(m['wis'])
    statcha = ET.SubElement(monster, 'cha')
    statcha.text = str(m['cha'])

    save = ET.SubElement(monster, 'save')
    if 'save' in m:
        save.text = ", ".join(["{} {}".format(str.capitalize(key), value)
                            for key, value in m['save'].items()])

    skill = ET.SubElement(monster, 'skill')
    if 'skill' in m:
        skill.text = ", ".join(["{} {}".format(str.capitalize(key), value)
                                for key, value in m['skill'].items()])

    passive = ET.SubElement(monster, 'passive')
    passive.text = str(m['passive'])

    languages = ET.SubElement(monster, 'languages')
    if 'languages' in m:
        languages.text = ", ".join([x for x in m['languages']])

    cr = ET.SubElement(monster, 'cr')
    if isinstance(m['cr'], dict):
        cr.text = str(m['cr']['cr'])
    else:
        cr.text = str(m['cr'])

    resist = ET.SubElement(monster, 'resist')
    if 'resist' in m:
        resistlist = parseRIV(m, 'resist')
        resist.text = "; ".join(resistlist)

    immune = ET.SubElement(monster, 'immune')
    if 'immune' in m:
        immunelist = parseRIV(m, 'immune')
        immune.text = "; ".join(immunelist)

    vulnerable = ET.SubElement(monster, 'vulnerable')
    if 'vulnerable' in m:
        vulnerablelist = parseRIV(m,'vulnerable')
        vulnerable.text = "; ".join(vulnerablelist)

    conditionImmune = ET.SubElement(monster, 'conditionImmune')
    if 'conditionImmune' in m:
        conditionImmunelist = parseRIV(m, 'conditionImmune')
        conditionImmune.text = "; ".join(conditionImmunelist)

    senses = ET.SubElement(monster, 'senses')
    if 'senses' in m:
        senses.text = ", ".join([x for x in m['senses']])

    if 'source' in m:
        trait = ET.SubElement(monster, 'trait')
        name = ET.SubElement(trait, 'name')
        name.text = "Source"
        text = ET.SubElement(trait, 'text')
        text.text = "{} p. {}".format(
            m['source'], m['page']) if 'page' in m and m['page'] != 0 else m['source']
    if 'trait' in m:
        for t in m['trait']:
            trait = ET.SubElement(monster, 'trait')
            name = ET.SubElement(trait, 'name')
            name.text = remove5eShit(t['name'])
            for e in t['entries']:
                if "colLabels" in e:
                    text = ET.SubElement(trait, 'text')
                    text.text = " | ".join([remove5eShit(x) for x in e['colLabels']])
                    for row in e['rows']:
                            rowthing = []
                            for r in row:
                                if isinstance(r, dict) and 'roll' in r:
                                    rowthing.append("{}-{}".format(r['roll']['min'], r['roll']['max']) if 'min' in r['roll'] else str(r['roll']['exact']))
                                else:
                                    rowthing.append(remove5eShit(r))
                            text = ET.SubElement(trait, 'text')
                            text.text = " | ".join(rowthing)
                else:
                    text = ET.SubElement(trait, 'text')
                    text.text = remove5eShit(e)

    if 'action' in m:
        for t in m['action']:
            action = ET.SubElement(monster, 'action')
            name = ET.SubElement(action, 'name')
            name.text = remove5eShit(t['name'])
            for e in t['entries']:
                if isinstance(e, dict):
                    if "colLabels" in e:
                        text = ET.SubElement(action, 'text')
                        text.text = " | ".join([remove5eShit(x) for x in e['colLabels']])
                        for row in e['rows']:
                            rowthing = []
                            for r in row:
                                if isinstance(r, dict) and 'roll' in r:
                                    rowthing.append(
                                        "{}-{}".format(r['roll']['min'], r['roll']['max']) if 'min' in r['roll'] else str(r['roll']['exact']))
                                else:
                                    rowthing.append(remove5eShit(r))
                            text = ET.SubElement(action, 'text')
                            text.text = " | ".join(rowthing)
                    else:
                        for i in e["items"]:
                            text = ET.SubElement(action, 'text')
                            if 'name' in i:
                                text.text = "{}{}".format(i['name']+" ", remove5eShit(i['entry']))
                            else:
                                text.text = "\n".join(remove5eShit(x) for x in i)
                else:
                    text = ET.SubElement(action, 'text')
                    text.text = remove5eShit(e)

    if 'legendary' in m:
        for t in m['legendary']:
            legendary = ET.SubElement(monster, 'legendary')
            name = ET.SubElement(legendary, 'name')
            name.text = remove5eShit(t['name'])
            for e in t['entries']:
                if isinstance(e, dict):
                    if "colLabels" in e:
                        text = ET.SubElement(legendary, 'text')
                        text.text = " | ".join(
                            [remove5eShit(x) for x in e['colLabels']])
                        for row in e['rows']:
                            rowthing = []
                            for r in row:
                                if isinstance(r, dict) and 'roll' in r:
                                    rowthing.append(
                                        "{}-{}".format(r['roll']['min'], r['roll']['max']) if 'min' in r['roll'] else str(r['roll']['exact']))
                                else:
                                    rowthing.append(remove5eShit(r))
                            text = ET.SubElement(legendary, 'text')
                            text.text = " | ".join(rowthing)
                    else:
                        for i in e["items"]:
                            text = ET.SubElement(legendary, 'text')
                            text.text = "{} {}".format(
                                i['name'], remove5eShit(i['entry']))
                else:
                    text = ET.SubElement(legendary, 'text')
                    text.text = remove5eShit(e)

    if 'spellcasting' in m:
        spells = []
        for s in m['spellcasting']:
            trait = ET.SubElement(monster, 'trait')
            name = ET.SubElement(trait, 'name')
            name.text = remove5eShit(s['name'])
            for e in s['headerEntries']:
                text = ET.SubElement(trait, 'text')
                text.text = remove5eShit(e)

            if "will" in s:
                text = ET.SubElement(trait, 'text')
                willspells = s['will']
                text.text = "At will: " + \
                    ", ".join([remove5eShit(e) for e in willspells])
                for spl in willspells:
                    search = re.search(
                        r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                    if search != None:
                        spells.append(search.group(1))

            if "daily" in s:
                for timeframe, lis in s['daily'].items():
                    text = ET.SubElement(trait, 'text')
                    dailyspells = lis
                    t = "{}/day{}: ".format(timeframe[0],
                                            " each" if len(timeframe) > 1 else "")
                    text.text = t + \
                        ", ".join([remove5eShit(e) for e in dailyspells])
                    for spl in dailyspells:
                        search = re.search(
                            r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                        if search != None:
                            spells.append(search.group(1))

            if "spells" in s:
                slots = []
                for level, obj in s['spells'].items():
                    text = ET.SubElement(trait, 'text')
                    spellbois = obj['spells']
                    t = "• {} level ({} slots): ".format(
                        ordinal(int(level)), obj['slots'] if 'slots' in obj else 0) if level != "0" else "Cantrips (at will): "
                    if level != "0":
                        slots.append(
                            str(obj['slots'] if 'slots' in obj else 0))
                    text.text = t + \
                        ", ".join([remove5eShit(e) for e in spellbois])
                    for spl in spellbois:
                        search = re.search(
                            r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                        if search != None:
                            spells.append(search.group(1))
                slotse = ET.SubElement(monster, 'slots')
                slotse.text = ", ".join(slots)

        spellse = ET.SubElement(monster, 'spells')
        spellse.text = ", ".join(spells)

    environment = ET.SubElement(monster, 'environment')
    if 'environment' in m:
        environment.text = ", ".join([x for x in m['environment']])
    # print(m['name'])

# Argument Parser
parser = argparse.ArgumentParser(description="Converts 5eTools json files to FC5 compatible XML files.")
parser.add_argument('inputJSON', nargs="+", type=str, help="5eTools inputs")
parser.add_argument('--ignore', dest="IE", action='store_const', const=True, default=False, help="ignores errors (default: false)")
parser.add_argument('-v', dest="verbose", action='store_const', const=True, default=False, help="verbose output (default: false)")
parser.add_argument('-o', dest="combinedoutput", action='store', default=False, help="combines inputs into given output (default: false)")
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
        compendium = ET.Element('compendium', {'version': "5", 'auto_indent': "NO"})
        wins = 0
        loss = 0
    for m in d['monster']:
        if ignoreError:
            try:
                parseMonster(m, compendium)
                wins += 1
            except Exception:
                print("FAILED: " + m['name'])
                loss += 1
                continue
        else:
            if args.verbose: 
                print("Parsing " + m['name'])
            parseMonster(m, compendium)
            wins += 1
    print("Done converting " + os.path.splitext(file)[0])

    if not args.combinedoutput:
        print("Converted {}/{} monsters (failed {})".format(wins,wins+loss,loss) if ignoreError else "Converted {} monsters".format(wins))
        # write to file
        tree = ET.ElementTree(indent(compendium, 1))
        tree.write(os.path.splitext(file)[0] + ".xml", xml_declaration=True, encoding='utf-8')
if args.combinedoutput:
    print("Converted {}/{} monsters (failed {})".format(wins,wins+loss,loss) if ignoreError else "Converted {} monsters".format(wins))
    # write to file
    tree = ET.ElementTree(indent(compendium, 1))
    tree.write(args.combinedoutput, xml_declaration=True, encoding='utf-8')
