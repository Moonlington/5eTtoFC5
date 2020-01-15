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

    if args.addimgs and os.path.isdir("./spells/"):
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
            if m["range"]["distance"]["amount"] == 1 and m["range"]["distance"]["type"][-1:] == 's':
                srange.text = srange.text[:-1]
    elif m["range"]["type"] == "special":
        srange.text = "Special"
    else:
        dtype = m["range"]["distance"]["type"]
        if dtype == "feet":
            dtype = "foot"
        elif dtype[-1:] == 's':
            dtype = dtype[:-1]
        srange.text = "Self ({}-{} {})".format(m["range"]["distance"]["amount"],dtype,m["range"]["type"])

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

    if "entriesHigherLevel" in m:
        if "entries" not in m: m["entries"] = []
        for higher in m["entriesHigherLevel"]:
            if args.nohtml:
                m["entries"].append("{}:".format(higher["name"]))
            else:
                m["entries"].append("<b>{}:</b>".format(higher["name"]))
            m["entries"] += higher["entries"]

    if 'source' in m:
        source = ET.SubElement(spell, 'source')
        source.text = "{} p. {}".format(
            utils.getFriendlySource(m['source']), m['page']) if 'page' in m and m['page'] != 0 else utils.getFriendlySource(m['source'])

        if 'otherSources' in m and m["otherSources"] is not None:
            for s in m["otherSources"]:
                if "source" not in s:
                    continue
                source.text += ", "
                source.text += "{} p. {}".format(
                    utils.getFriendlySource(s["source"]), s["page"]) if 'page' in s and s["page"] != 0 else utils.getFriendlySource(s["source"])
        if 'entries' in m:
            if args.nohtml:
                m['entries'].append("Source: {}".format(source.text))
            else:
                m['entries'].append("<i>Source: {}</i>".format(source.text))
        else:
            if args.nohtml:
                m['entries'] = "Source: {}".format(source.text)
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
                        subentries.append(utils.fixTags(sube,m,args.nohtml))
                    elif type(sube) == dict and "text" in sube:
                        subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                if 'name' in e:
                    if args.nohtml:
                        bodyText.text += "{}: ".format(e['name'])
                    else:
                        bodyText.text += "<i>{}:</i> ".format(e['name'])
                bodyText.text += "\n".join(subentries) + "\n"
            else:
                if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                    for item in e["items"]:
                        bodyText.text += "• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)) + "\n"
                elif type(e) == dict and e["type"] == "list":
                    for item in e["items"]:
                        if "entries" in item:
                            subentries = []                    
                            for sube in item["entries"]:
                                if type(sube) == str:
                                    subentries.append(utils.fixTags(sube,m,args.nohtml))
                                elif type(sube) == dict and "text" in sube:
                                    subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                                    bodyText.text += "\n".join(subentries) + "\n"
                        else:
                            bodyText.text += "• {}".format(utils.fixTags(item,m,args.nohtml)) + "\n"
                else:
                    bodyText.text += utils.fixTags(e,m,args.nohtml) + "\n"
