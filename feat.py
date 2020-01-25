# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import xml.etree.cElementTree as ET
import re
import utils
import json
import os
from slugify import slugify
from wand.image import Image

stats = {"str":"Strength","dex":"Dexterity","con":"Constitution","int":"Intelligence","wis":"Wisdom","cha":"Charisma"}

def parseFeat(m, compendium, args):
    feat = ET.SubElement(compendium, 'feat')
    name = ET.SubElement(feat, 'name')
    name.text = m['name']

    prereqs = ET.SubElement(feat,'prerequisite')
    if 'prerequisite' in m:
        prereq = []
        for pre in m['prerequisite']:
            if 'ability' in pre:
                if type(pre['ability']) == list:
                    abilityor = []
                    if all(next(iter(v.values())) == next(iter(pre['ability'][0].values())) for v in pre['ability']):
                        for v in pre['ability']:
                            for s,val in v.items():
                                abilityor.append(stats[s])
                        prereq.append("{} {} or higher".format(" or ".join(abilityor),next(iter(pre['ability'][0].values()))))
                    else:
                        for v in pre['ability']:
                            for s,val in v.items():
                                abilityor.append("{} {} or higher".format(stats[k],val))
                        prereq.append(" or ".join(abilityor))
                else:
                    for k,v in pre['ability'].items():
                        prereq.append("{} {} or higher".format(stats[k],v))
            if 'spellcasting' in pre and pre['spellcasting']:
                prereq.append("The ability to cast at least one spell")
            if 'proficiency' in pre:
                for prof in pre['proficiency']:
                    for k,v in prof.items():
                        prereq.append("Proficiency with {} {}".format(v,k))
            if 'race' in pre:
                for r in pre['race']:
                    prereq.append("{}{}".format(r['name']," ({})".format(r['subrace']) if 'subrace' in r else "").title())
        prereqs.text = ", ".join(prereq)

    if 'entries' not in m:
        m['entries'] = []

    if 'source' in m:
        slug = slugify(m["name"])
        if args.addimgs and os.path.isdir("./img") and not os.path.isfile("./items/" + slug + ".png"):
            if not os.path.isdir("./items/"):
                os.mkdir("./items/")
            artworkpath = None
            if os.path.isfile("./img/items/" + m["name"] + ".jpg"):
                artworkpath = "./img/items/" + m["name"] + ".jpg"
            elif os.path.isfile("./img/items/" + m["name"] + ".png"):
                artworkpath = "./img/items/" + m["name"] + ".png"
            elif os.path.isfile("./img/items/" + m["source"] + "/" + m["name"] + ".png"):
                artworkpath = "./img/items/" + m["source"] + "/" + m["name"] + ".png"
            if artworkpath is not None:
                if args.verbose:
                    print("Converting Image: " + artworkpath)
                with Image(filename=artworkpath) as img:
                    img.format='png'
                    img.save(filename="./items/" + slug + ".png")
                    imagetag = ET.SubElement(feat, 'image')
                    imagetag.text = slug + ".png"
        elif args.addimgs and os.path.isfile("./items/" + slug + ".png"):
            imagetag = ET.SubElement(feat, 'image')
            imagetag.text = slug + ".png"

        #source = ET.SubElement(feat, 'source')
        sourcetext = "{} p. {}".format(
            utils.getFriendlySource(m['source']), m['page']) if 'page' in m and m['page'] != 0 else utils.getFriendlySource(m['source'])

        if 'otherSources' in m and m["otherSources"] is not None:
            for s in m["otherSources"]:
                sourcetext += ", "
                sourcetext += "{} p. {}".format(
                    utils.getFriendlySource(s["source"]), s["page"]) if 'page' in s and s["page"] != 0 else utils.getFriendlySource(s["source"])
        if 'entries' in m:
            if args.nohtml:
                m['entries'].append("Source: {}".format(sourcetext))
            else:
                m['entries'].append("<i>Source: {}</i>".format(sourcetext))
        else:
            if args.nohtml:
                m['entries'] = ["Source: {}".format(sourcetext)]
            else:
                m['entries'] = ["<i>Source: {}</i>".format(sourcetext)]
    bodyText = ET.SubElement(feat, 'text')
    bodyText.text = ""

    if 'ability' in m:
        for ability in m['ability']:
            for k,v in ability.items():
                if k in stats:
                    bonusmod = ET.SubElement(feat, 'modifier', {'category': 'ability score'})
                    bonusmod.text = "{} {:+d}".format(stats[k],v)
                elif k == 'choose':
                    for e in m['entries']:
                        if type(e) == dict and e['type'] == 'list':
                            if len(v["from"]) != 6:
                                e['items'].insert(0,"Increase your {} score by {}, to a maximum of 20".format(" or ".join([stats[x] for x in v["from"]]),v["amount"]))
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
                if 'name' in e:
                    if args.nohtml:
                        bodyText.text += "{}: ".format(e['name'])
                    else:
                        bodyText.text += "<b>{}:</b> ".format(e['name'])
                for sube in e["entries"]:
                    if type(sube) == str:
                        subentries.append(utils.fixTags(sube,m,args.nohtml))
                    elif type(sube) == dict and "text" in sube:
                        subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                    elif type(sube) == dict and sube["type"] == "list" and "style" in sube and sube["style"] == "list-hang-notitle":
                        for item in sube["items"]:
                            if type(item) == dict and 'type' in item and item['type'] == 'item':
                                if args.nohtml:
                                    subentries.append("• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)))
                                else:
                                    subentries.append("• <i>{}:</i> {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)))
                            else:
                                subentries.append("• {}".format(utils.fixTags(item,m,args.nohtml)))
                    elif type(sube) == dict and sube["type"] == "list":
                        for item in sube["items"]:
                            if type(item) == dict and "entries" in item:
                                ssubentries = []                    
                                for sse in item["entries"]:
                                    if type(sse) == str:
                                        ssubentries.append(utils.fixTags(sse,m,args.nohtml))
                                    elif type(sse) == dict and "text" in sse:
                                        ssubentries.append(utils.fixTags(sse["text"],m,args.nohtml))
                                    subentries.append("\n".join(ssubentries))
                            elif type(item) == dict and 'type' in item and item['type'] == 'item':
                                if args.nohtml:
                                    subentries.append("• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)))
                                else:
                                    subentries.append("• <i>{}:</i> {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)))
                            else:
                                subentries.append("• {}".format(utils.fixTags(item,m,args.nohtml)))
                bodyText.text += "\n".join(subentries) + "\n"
            else:
                if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                    for item in e["items"]:
                        if args.nohtml:
                            bodyText.text += "• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)) + "\n"
                        else:
                            bodyText.text += "• <i>{}:</i> {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)) + "\n"
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
                            bodyText.text += "• {}".format(utils.fixTags(item,m,args.nohtml)) + "\n"
                else:
                    bodyText.text += utils.fixTags(e,m,args.nohtml) + "\n"

    bodyText.text = bodyText.text.rstrip()
    for match in re.finditer(r'You gain proficiency in the ([^ ]*?)( and (.*?))? skill',bodyText.text):
        bonusmod = ET.SubElement(feat, 'proficiency')
        bonusmod.text = match.group(1)
        if match.group(2) and match.group(3):
            bonusmod.text = ", " + match.group(3)
