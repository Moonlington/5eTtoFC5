# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import xml.etree.cElementTree as ET
import re
import utils
import json
import os
from slugify import slugify
from wand.image import Image

def parseBackground(m, compendium, args):
    bg = ET.SubElement(compendium, 'background')
    name = ET.SubElement(bg, 'name')
    name.text = m['name']

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
                    imagetag = ET.SubElement(bg, 'image')
                    imagetag.text = slug + ".png"
        elif args.addimgs and os.path.isfile("./items/" + slug + ".png"):
            imagetag = ET.SubElement(bg, 'image')
            imagetag.text = slug + ".png"

        #source = ET.SubElement(bg, 'source')
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

    prof = ET.SubElement(bg, 'proficiency')
    if 'skillProficiencies' in m:
        profs = []
        for skill in m['skillProficiencies']:
            for k,v in skill.items():
                if k != 'choose':
                    if v:
                        profs.append(k.title())
        prof.text = ", ".join(profs)

    trait = ET.SubElement(bg, 'trait')
    name = ET.SubElement(trait, 'name')
    name.text = "Description"
    description = ET.SubElement(trait, 'text')
    description.text = ""

    if 'entries' in m:
        for e in m['entries']:
            if type(e) == dict:
                if 'name' in e:
                    trait = ET.SubElement(bg, 'trait')
                    name = ET.SubElement(trait, 'name')
                    name.text = e['name']
                    text = ET.SubElement(trait, 'text')
                    text.text = ""
                else:
                    text = description
                if "colLabels" in e:
                    text.text += " | ".join([utils.remove5eShit(x)
                                            for x in e['colLabels']])
                    text.text += "\n"
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
                        text.text += " | ".join(rowthing) + "\n"
                elif "entries" in e:
                    subentries = []
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
                        else:
                            if "colLabels" in sube:
                                tabletext = ""
                                tabletext += " | ".join([utils.remove5eShit(x)
                                                        for x in sube['colLabels']])
                                tabletext += "\n"
                                for row in sube['rows']:
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
                                    tabletext += " | ".join(rowthing) + "\n"
                                subentries.append(tabletext)

                    text.text += "\n".join(subentries) + "\n"
                else:
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        for item in e["items"]:
                            if 'entries' in item and 'entry' not in item:
                                item['entry'] = ", ".join(item['entries'])
                            if args.nohtml:
                                text.text += "• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)) + "\n"
                            else:
                                text.text += "• <i>{}:</i> {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml)) + "\n"
                    elif type(e) == dict and e["type"] == "list":
                        for item in e["items"]:
                            if "entries" in item:
                                subentries = []                    
                                for sube in item["entries"]:
                                    if type(sube) == str:
                                        subentries.append(utils.fixTags(sube,m,args.nohtml))
                                    elif type(sube) == dict and "text" in sube:
                                        subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                                    text.text += "\n".join(subentries) + "\n"
                            else:
                                text.text += "• {}".format(utils.fixTags(item,m,args.nohtml)) + "\n"
            else:
                description.text += utils.fixTags(e,m,args.nohtml) + "\n"

    description.text = description.text.rstrip()
