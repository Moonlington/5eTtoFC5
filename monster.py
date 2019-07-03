import xml.etree.cElementTree as ET
import re
import utils


def parseMonster(m, compendium, args):
    if '_copy' in m:
        if args.verbose:
            print("COPY: " + m['name'])
        return
    monster = ET.SubElement(compendium, 'monster')
    name = ET.SubElement(monster, 'name')
    name.text = m['name']
    size = ET.SubElement(monster, 'size')
    size.text = m['size']

    typ = ET.SubElement(monster, 'type')
    if isinstance(m['type'], dict):
        if 'swarmSize' in m['type']:
            typ.text = "swarm of {} {}s".format(
                utils.convertSize(m['size']), m['type']['type'])
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
    alignment.text = utils.convertAlignList(m['alignment'])

    ac = ET.SubElement(monster, 'ac')
    acstr = []
    for acs in m['ac']:
        if isinstance(acs, dict):
            if 'from' in acs:
                acstr.append("{} ({})".format(
                    acs['ac'], utils.remove5eShit(acs['from'][0])))
            elif 'condition' in acs:
                acstr.append("{} ({})".format(
                    acs['ac'], utils.remove5eShit(acs['condition'])))
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
                lis.append(
                    "{} {} ft.".format(
                        ", ".join(
                            value['from']),
                        value['amount']))
            else:
                lis.append("{} {} ft.".format(key, value))
        speed.text = "; ".join(lis)
    else:
        speed.text = ", ".join(
            [
                "{} {} ft.".format(
                    key,
                    value['number'] if isinstance(
                        value,
                        dict) else value) for key,
                value in m['speed'].items() if not isinstance(
                    value,
                    bool)])

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
        save.text = ", ".join(["{} {}".format(str.capitalize(
            key), value) for key, value in m['save'].items()])

    skill = ET.SubElement(monster, 'skill')
    if 'skill' in m:
        skill.text = ", ".join(["{} {}".format(str.capitalize(
            key), value) for key, value in m['skill'].items()])

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
        resistlist = utils.parseRIV(m, 'resist')
        resist.text = "; ".join(resistlist)

    immune = ET.SubElement(monster, 'immune')
    if 'immune' in m:
        immunelist = utils.parseRIV(m, 'immune')
        immune.text = "; ".join(immunelist)

    vulnerable = ET.SubElement(monster, 'vulnerable')
    if 'vulnerable' in m:
        vulnerablelist = utils.parseRIV(m, 'vulnerable')
        vulnerable.text = "; ".join(vulnerablelist)

    conditionImmune = ET.SubElement(monster, 'conditionImmune')
    if 'conditionImmune' in m:
        conditionImmunelist = utils.parseRIV(m, 'conditionImmune')
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
            name.text = utils.remove5eShit(t['name'])
            for e in t['entries']:
                if "colLabels" in e:
                    text = ET.SubElement(trait, 'text')
                    text.text = " | ".join([utils.remove5eShit(x)
                                            for x in e['colLabels']])
                    for row in e['rows']:
                        rowthing = []
                        for r in row:
                            if isinstance(r, dict) and 'roll' in r:
                                rowthing.append(
                                    "{}-{}".format(
                                        r['roll']['min'],
                                        r['roll']['max']) if 'min' in r['roll'] else str(
                                        r['roll']['exact']))
                            else:
                                rowthing.append(utils.remove5eShit(r))
                        text = ET.SubElement(trait, 'text')
                        text.text = " | ".join(rowthing)
                else:
                    text = ET.SubElement(trait, 'text')
                    text.text = utils.remove5eShit(e)

    if 'action' in m:
        for t in m['action']:
            action = ET.SubElement(monster, 'action')
            name = ET.SubElement(action, 'name')
            name.text = utils.remove5eShit(t['name'])
            for e in t['entries']:
                if isinstance(e, dict):
                    if "colLabels" in e:
                        text = ET.SubElement(action, 'text')
                        text.text = " | ".join(
                            [utils.remove5eShit(x) for x in e['colLabels']])
                        for row in e['rows']:
                            rowthing = []
                            for r in row:
                                if isinstance(r, dict) and 'roll' in r:
                                    rowthing.append(
                                        "{}-{}".format(
                                            r['roll']['min'],
                                            r['roll']['max']) if 'min' in r['roll'] else str(
                                            r['roll']['exact']))
                                else:
                                    rowthing.append(utils.remove5eShit(r))
                            text = ET.SubElement(action, 'text')
                            text.text = " | ".join(rowthing)
                    else:
                        for i in e["items"]:
                            text = ET.SubElement(action, 'text')
                            if 'name' in i:
                                text.text = "{}{}".format(
                                    i['name'] + " ", utils.remove5eShit(i['entry']))
                            else:
                                text.text = "\n".join(
                                    utils.remove5eShit(x) for x in i)
                else:
                    text = ET.SubElement(action, 'text')
                    text.text = utils.remove5eShit(e)

    if 'legendary' in m:
        for t in m['legendary']:
            legendary = ET.SubElement(monster, 'legendary')
            name = ET.SubElement(legendary, 'name')
            name.text = utils.remove5eShit(t['name'])
            for e in t['entries']:
                if isinstance(e, dict):
                    if "colLabels" in e:
                        text = ET.SubElement(legendary, 'text')
                        text.text = " | ".join(
                            [utils.remove5eShit(x) for x in e['colLabels']])
                        for row in e['rows']:
                            rowthing = []
                            for r in row:
                                if isinstance(r, dict) and 'roll' in r:
                                    rowthing.append(
                                        "{}-{}".format(
                                            r['roll']['min'],
                                            r['roll']['max']) if 'min' in r['roll'] else str(
                                            r['roll']['exact']))
                                else:
                                    rowthing.append(utils.remove5eShit(r))
                            text = ET.SubElement(legendary, 'text')
                            text.text = " | ".join(rowthing)
                    else:
                        for i in e["items"]:
                            text = ET.SubElement(legendary, 'text')
                            text.text = "{} {}".format(
                                i['name'], utils.remove5eShit(i['entry']))
                else:
                    text = ET.SubElement(legendary, 'text')
                    text.text = utils.remove5eShit(e)

    if 'spellcasting' in m:
        spells = []
        for s in m['spellcasting']:
            trait = ET.SubElement(monster, 'trait')
            name = ET.SubElement(trait, 'name')
            name.text = utils.remove5eShit(s['name'])
            for e in s['headerEntries']:
                text = ET.SubElement(trait, 'text')
                text.text = utils.remove5eShit(e)

            if "will" in s:
                text = ET.SubElement(trait, 'text')
                willspells = s['will']
                text.text = "At will: " + \
                    ", ".join([utils.remove5eShit(e) for e in willspells])
                for spl in willspells:
                    search = re.search(
                        r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                    if search is not None:
                        spells.append(search.group(1))

            if "daily" in s:
                for timeframe, lis in s['daily'].items():
                    text = ET.SubElement(trait, 'text')
                    dailyspells = lis
                    t = "{}/day{}: ".format(timeframe[0],
                                            " each" if len(timeframe) > 1 else "")
                    text.text = t + \
                        ", ".join([utils.remove5eShit(e) for e in dailyspells])
                    for spl in dailyspells:
                        search = re.search(
                            r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                        if search is not None:
                            spells.append(search.group(1))

            if "spells" in s:
                slots = []
                for level, obj in s['spells'].items():
                    text = ET.SubElement(trait, 'text')
                    spellbois = obj['spells']
                    t = "• {} level ({} slots): ".format(
                        utils.ordinal(
                            int(level)),
                        obj['slots'] if 'slots' in obj else 0) if level != "0" else "Cantrips (at will): "
                    if level != "0":
                        slots.append(
                            str(obj['slots'] if 'slots' in obj else 0))
                    text.text = t + \
                        ", ".join([utils.remove5eShit(e) for e in spellbois])
                    for spl in spellbois:
                        search = re.search(
                            r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                        if search is not None:
                            spells.append(search.group(1))
                slotse = ET.SubElement(monster, 'slots')
                slotse.text = ", ".join(slots)

        spellse = ET.SubElement(monster, 'spells')
        spellse.text = ", ".join(spells)

    environment = ET.SubElement(monster, 'environment')
    if 'environment' in m:
        environment.text = ", ".join([x for x in m['environment']])
    # print(m['name'])
