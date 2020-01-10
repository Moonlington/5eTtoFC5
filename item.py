import xml.etree.cElementTree as ET
import re
import utils
import json
import os
from slugify import slugify
from wand.image import Image

excludedages = ['futuristic','modern','renaissance']
def parseItem(m, compendium, args):
    if 'age' in m and m['age'].lower() in excludedages:
        if args.verbose:
            print ("SKIPPING",m['age'],"ITEM:",m['name'])
        return
    if '_copy' in m:
        if args.verbose:
            print("COPY: " + m['name'] + " from " + m['_copy']['name'] + " in " + m['_copy']['source'])
        xtrsrc = "./data/items.json"
        try:
            with open(xtrsrc) as f:
                d = json.load(f)
                f.close()
            mcpy = m
            for mn in d['item']:
                itemfound = False
                if mn['name'] == mcpy['_copy']['name']:
                    m = mn
                    m['name'] = mcpy['name']
                    m['source'] = mcpy['source']
                    if "otherSources" in mcpy:
                        m["otherSources"] = mcpy["otherSources"]
                    m['page'] = mcpy['page']
                    if '_mod' in mcpy['_copy']:
                        m = utils.modifyItem(m,mcpy['_copy']['_mod'])
                    itemfound = True
                    break
            if not itemfound:
                print("Could not find ",mcpy['_copy']['name'])
        except IOError as e:
            if args.verbose:
                print ("Could not load additional source ({}): {}".format(e.errno, e.strerror))
            return

    itm = ET.SubElement(compendium, 'item')
    name = ET.SubElement(itm, 'name')
    name.text = m['name']

    heading = ET.SubElement(itm, 'heading')
    headings = []

    typ = ET.SubElement(itm, 'type')
    if 'type' in m:
        typ.text = m['type']
        if m['type'] == "AIR":
            typ.text = 'G'
        if m['type'] == "AT":
            typ.text = 'G'
        if m['type'] == "GS":
            typ.text = 'G'
        if m['type'] == "INS":
            typ.text = 'G'
        if m['type'] == "MNT":
            typ.text = 'G'
        if m['type'] == "OTH":
            typ.text = 'G'
        if m['type'] == "SCF":
            if 'rod' in m['name'].lower():
                typ.text = 'RD'
            elif 'wand' in m['name'].lower():
                typ.text = 'WD'
            elif 'staff' in m['name'].lower():
                typ.text = 'ST'
            typ.text = 'G'
        if m['type'] == "SHP":
            typ.text = 'G'
        if m['type'] == "T":
            typ.text = 'G'
        if m['type'] == "TAH":
            typ.text = 'G'
        if m['type'] == "TG":
            typ.text = 'G'
        if m['type'] == "VEH":
            typ.text = 'G'

    if 'wondrous' in m and m['wondrous']:
        headings.append("Wondrous item")
        if 'type' not in m:
            typ.text = 'W'

    if 'tier' in m: headings.append(m['tier']) 

    if 'curse' in m and m['curse']: headings.append("Cursed item")

    weight = ET.SubElement(itm, 'weight')
    if 'weight' in m: weight.text = str(m['weight'])

    rarity = ET.SubElement(itm, 'rarity')
    if 'rarity' in m:
        rarity.text = str(m['rarity'])
        if m['rarity'] != 'None' and m['rarity'] != 'Unknown': headings.append(m['rarity'])

    value = ET.SubElement(itm, 'value')
    if 'value' in m:
        if m['value'] >= 100:
            value.text = "{:g} gp".format(m['value']/100)
        elif m['value'] >= 10:
            value.text = "{:g} sp".format(m['value']/10)
        else:
            value.text = "{:g} cp".format(m['value'])

    prop = ET.SubElement(itm, 'property')
    if 'property' in m: prop.text = ",".join(m['property'])

    if 'staff' in m and m['staff']:
        headings.append('Staff')
        if 'type' not in m or m['type'] == 'SCF':
            typ.text = 'ST'

    if 'wand' in m and m['wand']:
        headings.append('Wand')
        if 'type' not in m or m['type'] == 'SCF':
            typ.text = 'WD'

    if 'weapon' in m and m['weapon'] and 'weaponCategory' in m:
        headings.append(m['weaponCategory'] + " Weapon")

    if 'type' in m:
        if m['type'] == 'LA':
            headings.append("Light Armor")
        elif m['type'] == 'MA':
            headings.append("Medium Armor")
        elif m['type'] == 'HA':
            headings.append("Heavy Armor")
        elif m['type'] == 'S':
            headings.append("Shield")
        elif m['type'] == 'SCF':
            headings.append("Spellcasting Focus")
        elif m['type'] == 'R':
            headings.append('Ranged Weapon')
        elif m['type'] == 'M':
            headings.append('Melee Weapon')
        elif m['type'] == 'A':
            headings.append('Ammunition')
        elif m['type'] == 'G':
            headings.append('Adventuring Gear')
        elif m['type'] == 'T':
            headings.append('Tools')
        elif m['type'] == 'AT':
            headings.append('Artisan Tools')
        elif m['type'] == 'GS':
            headings.append('Gaming Set')
        elif m['type'] == 'TG':
            headings.append('Trade Good')
        elif m['type'] == 'INS':
            headings.append('Instrument')
        elif m['type'] == 'MNT':
            headings.append('Mount')
        elif m['type'] == 'VEH':
            headings.append('Vehicle (land)')
        elif m['type'] == 'AIR':
            headings.append('Vehicle (air)')
        elif m['type'] == 'SHP':
            headings.append('Vehicle (water)')
        elif m['type'] == 'TAH':
            headings.append('Tack and Harness')
        elif m['type'] == 'OTH':
            headings.append('Other')
    attunement = ET.SubElement(itm, 'attunement')
    if 'reqAttune' in m:
        if m['reqAttune'] == True:
            attunement.text = "Requires Attunement"
        else:
            attunement.text = "Requires Attunement " + m['reqAttune']
        headings.append("({})".format(attunement.text))

    dmg1 = ET.SubElement(itm, 'dmg1')
    if 'dmg1' in m: dmg1.text = utils.remove5eShit(m['dmg1'])

    dmg2 = ET.SubElement(itm, 'dmg2')
    if 'dmg2' in m: dmg2.text = utils.remove5eShit(m['dmg2'])

    dmgType = ET.SubElement(itm, 'dmgType')
    if 'dmgType' in m: dmgType.text = m['dmgType']

    rng = ET.SubElement(itm, 'range')
    if 'range' in m: rng.text = m['range']

    ac = ET.SubElement(itm, 'ac')
    if 'ac' in m: ac.text = str(m['ac'])

    if 'poison' in m and m['poison']:
        headings.append('Poison')
        if 'type' not in m:
            typ.text = 'G'

    heading.text = ", ".join(headings)

    if 'source' in m:
        slug = slugify(m["name"])
        if os.path.isdir("./items/") and os.path.isdir("./img") and not os.path.isfile("./items/" + slug + ".jpg"):
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
                    img.format='jpeg'
                    img.save(filename="./items/" + slug + ".jpg")
                    imagetag = ET.SubElement(itm, 'image')
                    imagetag.text = slug + ".jpg"
        elif os.path.isfile("./items/" + slug + ".jpg"):
            imagetag = ET.SubElement(itm, 'image')
            imagetag.text = slug + ".jpg"

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
        source = ET.SubElement(itm, 'source')
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
    bodyText = ET.SubElement(itm, 'text')
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
