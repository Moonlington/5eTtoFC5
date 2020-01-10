import xml.etree.cElementTree as ET
import re
import utils
import json
import os

def parseSpell(m, compendium, args):
    spell = ET.SubElement(compendium, 'spell')
    name = ET.SubElement(spell, 'name')
    name.text = m['name']

    level = ET.SubElement(spell, 'level')
    level.text = str(m['level'])

    school = ET.SubElement(spell, 'school')
    if m['school'] == 'E':
        school.text = 'EN'
    elif m['school'] == 'V':
        school.text = 'EV'
    else:
        school.text = m['school']

    if os.path.isdir("./spells/"):
        image = ET.SubElement(spell, 'image')
        if m['school'] == 'E':
            image.text = "enchantment.png"
        elif m['school'] == 'V':
            image.text = "evocation.png"
        elif m['school'] == 'A':
            image.text = "abjuration.png"
        elif m['school'] == 'C':
            image.text = "conjuration.png"
        elif m['school'] == 'D':
            image.text = "divination.png"
        elif m['school'] == 'I':
            image.text = "illusion.png"
        elif m['school'] == 'N':
            image.text = "necromancy.png"
        elif m['school'] == 'T':
            image.text = "transmutation.png"

    ritual = ET.SubElement(spell, 'ritual')
    if "meta" in m and "ritual" in m["meta"] and m["meta"]["ritual"]:
        ritual.text = "YES"
    else:
        ritual.text = "NO"

    time = ET.SubElement(spell, 'time')
    times = []
    for t in m["time"]:
        ttxt = "{} {}".format(t["number"],t["unit"])
        if t["unit"] == "bonus":
            ttxt += " action"
        if t["number"] > 1:
            ttxt += "s"
        times.append(ttxt)
    time.text = ", ".join(times)

    srange = ET.SubElement(spell, 'range')
    if m["range"]["type"] == "point":
        if "amount" not in m["range"]["distance"]:
            srange.text = m["range"]["distance"]["type"].title()
        else:
            srange.text = "{} {}".format(m["range"]["distance"]["amount"],m["range"]["distance"]["type"])
    elif m["range"]["type"] == "special":
        srange.text = "Special"
    else:
        srange.text = "{} {} {}".format(m["range"]["distance"]["amount"],m["range"]["distance"]["type"],m["range"]["type"])

    components = ET.SubElement(spell, 'components')
    if "components" in m:
        componentsList = []
        for c in m["components"]:
            if type(m["components"][c]) is bool:
                componentsList.append(c.upper())
            elif type(m["components"][c]) is dict:
                componentsList.append("{} ({})".format(c.upper(),m["components"][c]["text"]))
            else:
                componentsList.append("{} ({})".format(c.upper(),m["components"][c]))
        components.text = ", ".join(componentsList)

    duration = ET.SubElement(spell, 'duration')
    durations = []
    for d in m["duration"]:
        if d["type"] == "timed":
            if "concentration" in d:
                dtxt = "Concentration, up to {} {}".format(d["duration"]["amount"],d["duration"]["type"])
            else:
                dtxt = "{} {}".format(d["duration"]["amount"],d["duration"]["type"])
            if d["duration"]["amount"] > 1: dtxt += 's'
        elif d["type"] == "permanent":
            dtxt = "Until " + " or ".join(d["ends"])
            dtxt = dtxt.replace("dispel","dispelled")
            dtxt = dtxt.replace("trigger","triggered")
        elif d["type"] == "instant":
            dtxt = "Instantaneous"
        else:
            dtxt = d["type"]
        durations.append(dtxt)
    duration.text = ", ".join(durations)
    classes = ET.SubElement(spell, 'classes')
    classlist = []
    if "classes" in m and "fromClassList" in m["classes"]:
        for c in m["classes"]["fromClassList"]:
        	classlist.append(c["name"])
    if "classes" in m and "fromSubclass" in m["classes"]:
        for c in m["classes"]["fromSubclass"]:
        	classlist.append("{} ({})".format(c["class"]["name"],c["subclass"]["name"]))
    classes.text = ", ".join(classlist)

    if 'source' in m:
        allbooks = [ "./data/books.json", "./data/adventures.json" ]
        srcfound = True
        if m["source"] == "TftYP":
            m["source"] = "Tales from the Yawning Portal"
        elif m["source"] == "PSA":
            m["source"] = "Plane Shift: Amonkhet"
        elif m["source"] == "PSD":
            m["source"] = "Plane Shift: Dominaria"
        elif m["source"] == "PSI":
            m["source"] = "Plane Shift: Innistrad"
        elif m["source"] == "PSK":
            m["source"] = "Plane Shift: Kaladesh"
        elif m["source"] == "PSX":
            m["source"] = "Plane Shift: Ixalan"
        elif m["source"] == "PSZ":
            m["source"] = "Plane Shift: Zendikar"
        elif m["source"] == "Mag":
            m["source"] = "Dragon Magazine"
        elif m["source"] == "MFF":
            m["source"] = "Mordenkainen’s Fiendish Folio"
        elif m["source"] == "Stream":
            m["source"] = "Livestream"
        elif m["source"].startswith("UA"):
            m["source"] = re.sub(r"(\w)([A-Z])", r"\1 \2", m["source"])
            m["source"] = re.sub(r"U A", r"Unearthed Arcana: ", m["source"])
        else:
            srcfound = False
        for books in allbooks:
            if srcfound:
                break
            try:
                with open(books) as f:
                    bks = json.load(f)
                    f.close()
                key = list(bks.keys())[0]
                for bk in bks[key]:
                    if bk['source'] == m['source']:
                        m["source"] = bk['name']
                        srcfound = True
                        break
            except IOError as e:
                if args.verbose:
                    print ("Could not determine source friendly names ({}): {}".format(e.errno, e.strerror))
        if not srcfound and args.verbose:
            print("Could not find source: " + m['source'])
        source = ET.SubElement(spell, 'source')
        source.text = "{} p. {}".format(
            m['source'], m['page']) if 'page' in m and m['page'] != 0 else m['source']

        if 'otherSources' in m and m["otherSources"] is not None:
            allbooks = [ "./data/books.json", "./data/adventures.json" ]
            srcfound = True
            for s in m["otherSources"]:
                if "source" not in s:
                    continue
                if s["source"] == "TftYP":
                    s["source"] = "Tales from the Yawning Portal"
                elif s["source"] == "PSA":
                    s["source"] = "Plane Shift: Amonkhet"
                elif s["source"] == "PSD":
                    s["source"] = "Plane Shift: Dominaria"
                elif s["source"] == "PSI":
                    s["source"] = "Plane Shift: Innistrad"
                elif s["source"] == "PSK":
                    s["source"] = "Plane Shift: Kaladesh"
                elif s["source"] == "PSX":
                    s["source"] = "Plane Shift: Ixalan"
                elif s["source"] == "PSZ":
                    s["source"] = "Plane Shift: Zendikar"
                elif s["source"] == "Mag":
                    s["source"] = "Dragon Magazine"
                elif s["source"] == "MFF":
                    s["source"] = "Mordenkainen’s Fiendish Folio"
                elif s["source"] == "Stream":
                    s["source"] = "Livestream"
                elif s["source"].startswith("UA"):
                    s["source"] = re.sub(r"(\w)([A-Z])", r"\1 \2", s["source"])
                    s["source"] = re.sub(r"U A", r"Unearthed Arcana: ", s["source"])
                else:
                    srcfound = False
                for books in allbooks:
                    if srcfound:
                        break
                    try:
                        with open(books) as f:
                            bks = json.load(f)
                            f.close()
                        key = list(bks.keys())[0]
                        for bk in bks[key]:
                            if bk['source'] == s["source"]:
                                s["source"] = bk['name']
                                srcfound = True
                                break
                    except IOError as e:
                        if args.verbose:
                            print ("Could not determine source friendly names ({}): {}".format(e.errno, e.strerror))
                if not srcfound and args.verbose:
                    print("Could not find source: " + s["source"])
                source.text += ", "
                source.text += "{} p. {}".format(
                    s["source"], s["page"]) if 'page' in s and s["page"] != 0 else s["source"]
        if 'entries' in m:
            m['entries'].append("<i>Source: {}</i>".format(source.text))
        else:
            m['entries'] = ["<i>Source: {}</i>".format(source.text)]

    bodyText = ET.SubElement(spell, 'text')
    bodyText.text = ""

    if 'entries' in m:
        for e in m['entries']:
            if "colLabels" in e:
                bodyText.text += " | ".join([utils.remove5eShit(x)
                                        for x in e['colLabels']])
                bodyText.text += "\n"
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
                            rowthing.append(utils.remove5eShit(str(r)))
                    bodyText.text += " | ".join(rowthing) + "\n"
            elif "entries" in e:
                subentries = []                    
                for sube in e["entries"]:
                    if type(sube) == str:
                        subentries.append(utils.remove5eShit(utils.fixTags(sube,m)))
                    elif type(sube) == dict and "text" in sube:
                        subentries.append(utils.remove5eShit(utils.fixTags(sube["text"],m)))
                bodyText.text += "\n".join(subentries)
            else:
                if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                    for item in e["items"]:
                        bodyText.text += "{}: {}".format(item["name"],utils.remove5eShit(utils.fixTags(item["entry"],m))) + "\n"
                elif type(e) == dict and e["type"] == "list":
                    for item in e["items"]:
                        if "entries" in item:
                            subentries = []                    
                            for sube in item["entries"]:
                                if type(sube) == str:
                                    subentries.append(utils.remove5eShit(utils.fixTags(sube,m)))
                                elif type(sube) == dict and "text" in sube:
                                    subentries.append(utils.remove5eShit(utils.fixTags(sube["text"],m)))
                                    bodyText.text += "\n".join(subentries) + "\n"
                        else:
                            bodyText.text += "{}".format(utils.remove5eShit(utils.fixTags(item,m))) + "\n"
                else:
                    bodyText.text += utils.remove5eShit(utils.fixTags(e,m)) + "\n"
