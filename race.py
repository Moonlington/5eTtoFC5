# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import xml.etree.cElementTree as ET
import re
import utils
import json
import os
from slugify import slugify
from wand.image import Image

def parseRace(m, compendium, args):
    if '_copy' in m:
        if args.verbose:
            print("COPY: " + m['name'] + " from " + m['_copy']['name'] + " in " + m['_copy']['source'])
        xtrsrc = "./data/races.json"
        try:
            with open(xtrsrc) as f:
                d = json.load(f)
                f.close()
            mcpy = m
            for mn in d['race']:
                racefound = False
                if mn['name'] == mcpy['_copy']['name']:
                    m = mn
                    m['name'] = mcpy['name']
                    m['source'] = mcpy['source']
                    if "otherSources" in mcpy:
                        m["otherSources"] = mcpy["otherSources"]
                    m['page'] = mcpy['page']
                    if '_mod' in mcpy['_copy']:
                        m = utils.modifyItem(m,mcpy['_copy']['_mod'])
                    racefound = True
                    break
            if not racefound:
                print("Could not find ",mcpy['_copy']['name'])
        except IOError as e:
            if args.verbose:
                print ("Could not load additional source ({}): {}".format(e.errno, e.strerror))
            return

    race = ET.SubElement(compendium, 'race')
    name = ET.SubElement(race, 'name')
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
                    imagetag = ET.SubElement(race, 'image')
                    imagetag.text = slug + ".png"
        elif args.addimgs and os.path.isfile("./items/" + slug + ".png"):
            imagetag = ET.SubElement(race, 'image')
            imagetag.text = slug + ".png"

        #source = ET.SubElement(race, 'source')
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

    size = ET.SubElement(race, 'size')
    if m['size'] == 'V':
        size.text = 'M'
    else:
        size.text = m['size']
    
    speed = ET.SubElement(race, 'speed')
    if type(m['speed']) == dict:
        speed.text = str(m['speed']['walk'])
    elif m['speed'] != "Varies":
        speed.text = str(m['speed'])
    else:
        speed.text = "30"

    ability = ET.SubElement(race, 'ability')
    if 'ability' in m:
        abils = []
        for ab in m['ability']:
            for k,v in ab.items():
                if k != 'choose':
                    abils.append("{} {}".format(k,v).capitalize())
        ability.text = ", ".join(abils)


    prof = ET.SubElement(race, 'proficiency')
    if 'skillProficiencies' in m:
        profs = []
        for skill in m['skillProficiencies']:
            for k,v in skill.items():
                if k != 'choose' and k != 'tool':
                    if v:
                        profs.append(k.title())
        prof.text = ", ".join(profs)

    spell = ET.SubElement(race, 'spellAbility')
    trait = ET.SubElement(race, 'trait')
    name = ET.SubElement(trait, 'name')
    name.text = "Description"
    description = ET.SubElement(trait, 'text')
    description.text = ""
    
    if 'entries' in m:
        for e in m['entries']:
            if type(e) == dict:
                if 'name' in e:
                    trait = ET.SubElement(race, 'trait')
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
                                rowthing.append(utils.fixTags(str(r),m,args.nohtml))
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
                                if type(item) == dict and 'type' in item and (item['type'] == 'item' or item['type'] == 'itemSpell'):
                                    if args.nohtml:
                                        subentries.append("• {} {}".format(item["name"] if item["name"].endswith(':') else item["name"] + ':',utils.fixTags(item["entry"],m,args.nohtml)))
                                    else:
                                        subentries.append("• <i>{}</i> {}".format(item["name"] if item["name"].endswith(':') else item["name"] + ':',utils.fixTags(item["entry"],m,args.nohtml)))
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
                                            rowthing.append(utils.fixTags(str(r),m,args.nohtml))
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
                match = re.search(r'(\w+) is your spellcasting ability', text.text)
                if match:
                    spell.text = match.group(1)
            else:
                description.text += utils.fixTags(e,m,args.nohtml) + "\n"

    description.text = description.text.rstrip()
