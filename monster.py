import xml.etree.cElementTree as ET
import re
import utils
import json
import os
import copy
from slugify import slugify
#from wand.image import Image
from shutil import copyfile

def parseMonster(m, compendium, args):
    if m['name'] == "Demogorgon" and m['source'] == "HftT":
        m['name'] = "Demogorgon (monstrosity)"
    if '_copy' in m:
        if args.verbose:
            print("COPY: " + m['name'] + " from " + m['_copy']['name'] + " in " + m['_copy']['source'])
        xtrsrc = "./data/bestiary/bestiary-" + m['_copy']['source'].lower() + ".json"
        try:
            with open(xtrsrc) as f:
                d = json.load(f)
                f.close()
            mcpy = copy.deepcopy(m)
            for mn in d['monster']:
                if mn['name'] == mcpy['_copy']['name']:
                    if '_copy' in mn:
                        if args.verbose:
                            print("ANOTHER COPY: " + mn['name'] + " from " + mn['_copy']['name'] + " in " + mn['_copy']['source'])
                        xtrsrc2 = "./data/bestiary/bestiary-" + mn['_copy']['source'].lower() + ".json"
                        with open(xtrsrc2) as f:
                            d2 = json.load(f)
                            f.close()
                        for mn2 in d2['monster']:
                            if mn2['name'] == mn['_copy']['name']:
                                mn = copy.deepcopy(mn2)
                                break
                    m = copy.deepcopy(mn)
                    m['name'] = mcpy['name']
                    if 'isNpc' in mcpy:
                        m['isNpc'] = mcpy['isNpc']
                    m['source'] = mcpy['source']
                    if "otherSources" in mcpy:
                        m["otherSources"] = mcpy["otherSources"]
                    elif "otherSources" in m:
                        del m["otherSources"]
                    m['page'] = mcpy['page']
                    if '_mod' in mcpy['_copy']:
                        m = utils.modifyMonster(m,mcpy['_copy']['_mod'])
                    break
            if '_trait' in mcpy['_copy']:
                if args.verbose:
                    print("Adding extra traits for: " + mcpy['_copy']['_trait']['name'])
                traits = "./data/bestiary/traits.json"
                with open(traits) as f:
                    d = json.load(f)
                    f.close()
                for trait in d['trait']:
                    if trait['name'] == mcpy['_copy']['_trait']['name']:
                        if '_mod' in trait['apply']:
                            m = utils.modifyMonster(m,trait['apply']['_mod'])
                        if '_root' in trait['apply']:
                            for key in trait['apply']['_root']:
                                if key == "speed" and type(trait['apply']['_root'][key]) == int:
                                    for k2 in m['speed']:
                                            m['speed'][k2]=trait['apply']['_root'][key]
                                else:
                                    m[key] = trait['apply']['_root'][key]
        except IOError as e:
            if args.verbose:
                print ("Could not load additional source ({}): {}".format(e.errno, e.strerror))
            return
#    for eachmonsters in compendium.findall('monster'):
#        if eachmonsters.find('name').text == m['name']:
#            m['name'] = "{} (DUPLICATE IN {})".format(m['name'],m['source'])

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
        elif 'tags' in m['type']:
            subtypes = []
            for tag in m['type']['tags']:
                if not isinstance(tag, dict):
                    subtypes.append(tag)
                else:
                    subtypes.append(tag['prefix'] + tag['tag'])
            typ.text = "{} ({})".format(m['type']['type'], ", ".join(subtypes))
        else:
            typ.text = m['type']['type']
    else:
        typ.text = m['type']

    alignment = ET.SubElement(monster, 'alignment')
    if 'alignment' not in m:
        m['alignment'] = [ 'A' ]
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
                lis.append("walk " + str(value) + " ft.")
            elif key == "choose":
                value['from'].insert(-1, 'or')
                lis.append(
                    "{} {} ft. {}".format(
                        " ".join(
                            value['from']),
                        value['amount'],value['note']))
            else:
                lis.append("{} {} ft.".format(key, value))
        speed.text = ", ".join(lis)
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
        skills = []
        for key, value in m['skill'].items():
            if type(value) == str:
                skills.append("{} {}".format(str.capitalize(key), value))
            else:
                if key == "other":
                    for sk in value:
                        if "oneOf" in sk:
                            skills.append("plus one of the following: "+", ".join(["{} {}".format(str.capitalize(ook), oov) for ook, oov in sk["oneOf"].items()]))
        skill.text = ", ".join(skills)

    passive = ET.SubElement(monster, 'passive')
    passive.text = str(m['passive'])

    languages = ET.SubElement(monster, 'languages')
    if 'languages' in m:
        languages.text = ", ".join([x for x in m['languages']])

    cr = ET.SubElement(monster, 'cr')
    if 'cr' in m:
        if isinstance(m['cr'], dict):
            cr.text = str(m['cr']['cr'])
        else:
            cr.text = str(m['cr'])

    resist = ET.SubElement(monster, 'resist')
    if 'resist' in m:
        resistlist = utils.parseRIV(m, 'resist')
        resist.text = ", ".join(resistlist)

    immune = ET.SubElement(monster, 'immune')
    if 'immune' in m:
        immunelist = utils.parseRIV(m, 'immune')
        immune.text = ", ".join(immunelist)

    vulnerable = ET.SubElement(monster, 'vulnerable')
    if 'vulnerable' in m:
        vulnerablelist = utils.parseRIV(m, 'vulnerable')
        vulnerable.text = ", ".join(vulnerablelist)

    conditionImmune = ET.SubElement(monster, 'conditionImmune')
    if 'conditionImmune' in m:
        conditionImmunelist = utils.parseRIV(m, 'conditionImmune')
        conditionImmune.text = ", ".join(conditionImmunelist)

    senses = ET.SubElement(monster, 'senses')
    if 'senses' in m:
        senses.text = ", ".join([x for x in m['senses']])

    if 'source' in m:
        slug = slugify(m["name"])
        if args.addimgs and os.path.isdir("./img") and not os.path.isfile("./monsters/" + slug + ".png"):
            if not os.path.isdir("./monsters/"):
                os.mkdir("./monsters/")
            if 'image' in m:
                artworkpath = m['image']
            else:
                artworkpath = None
            if artworkpath and os.path.isfile("./img/" + artworkpath):
                artworkpath = "./img/" + artworkpath
            elif os.path.isfile("./img/bestiary/" + m["source"] + "/" + m["name"] + ".jpg"):
                artworkpath = "./img/bestiary/" + m["source"] + "/" + m["name"] + ".jpg"
            elif os.path.isfile("./img/bestiary/" + m["source"] + "/" + m["name"] + ".png"):
                artworkpath = "./img/bestiary/" + m["source"] + "/" + m["name"] + ".png"
            elif os.path.isfile("./img/" + m["source"] + "/" + m["name"] + ".png"):
                artworkpath = "./img/" + m["source"] + "/" + m["name"] + ".png"
            if artworkpath is not None:
                copyfile(artworkpath, "./monsters/" + slug + os.path.splitext(artworkpath)[1])
                imagetag = ET.SubElement(monster, 'image')
                imagetag.text = slug + os.path.splitext(artworkpath)[1]
#                with Image(filename=artworkpath) as img:
#                    img.format='png'
#                    img.save(filename="./monsters/" + slug + ".png")
#                    imagetag = ET.SubElement(monster, 'image')
#                    imagetag.text = slug + ".png"
        elif os.path.isfile("./monsters/" + slug + ".png"):
            imagetag = ET.SubElement(monster, 'image')
            imagetag.text = slug + ".png"

        sourcetext = "{} p. {}".format(
            utils.getFriendlySource(m['source']), m['page']) if 'page' in m and m['page'] != 0 else utils.getFriendlySource(m['source'])

        if 'otherSources' in m and m["otherSources"] is not None:
            for s in m["otherSources"]:
                if "source" not in s:
                    continue
                sourcetext += ", "
                sourcetext += "{} p. {}".format(
                    utils.getFriendlySource(s["source"]), s["page"]) if 'page' in s and s["page"] != 0 else utils.getFriendlySource(s["source"])
        #trait = ET.SubElement(monster, 'trait')
        #name = ET.SubElement(trait, 'name')
        #name.text = "Source"
        #text = ET.SubElement(trait, 'text')
        #text.text = sourcetext
    else:
        sourcetext = None


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
                elif "entries" in e:
                    text = ET.SubElement(trait, 'text')
                    subentries = []                    
                    for sube in e["entries"]:
                        if type(sube) == str:
                            subentries.append(utils.fixTags(sube,m,args.nohtml))
                        elif type(sube) == dict and "text" in sube:
                            subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                    text.text = "\n".join(subentries)
                else:
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        for item in e["items"]:
                            text = ET.SubElement(trait, 'text')
                            if args.nohtml:
                                text.text = "• {}: {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            else:
                                text.text = "• <i>{}:</i> {}".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                    elif type(e) == dict and e["type"] == "list":
                        for item in e["items"]:
                            text = ET.SubElement(trait, 'text')
                            text.text = "• {}".format(utils.fixTags(item,m,args.nohtml))
                    else:
                        text = ET.SubElement(trait, 'text')
                        text.text = utils.fixTags(e,m,args.nohtml)

    if 'action' in m and m['action'] is not None:
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
                    elif "entries" in e:
                        text = ET.SubElement(action, 'text')
                        subentries = []                    
                        for sube in e["entries"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                        text.text = "\n".join(subentries)
                    elif "items" in e:
                        text = ET.SubElement(action, 'text')
                        subentries = []                    
                        for sube in e["items"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                            elif type(sube) == dict and "name" in sube and "entry" in sube:
                                if args.nohtml:
                                    subentries.append("{}".format(utils.fixTags(sube["name"],m,args.nohtml)) + utils.fixTags(sube["entry"],m,args.nohtml))
                                else:
                                    subentries.append("<i>{}</i>".format(utils.fixTags(sube["name"],m,args.nohtml)) + utils.fixTags(sube["entry"],m,args.nohtml))
                        text.text = "\n".join(subentries)
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
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        text.text = ""
                        for item in e["items"]:
                            if args.nohtml:
                                text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            else:
                                text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                    elif type(e) == dict and e["type"] == "list":
                        text.text = ""
                        for item in e["items"]:
                            text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                    else:
                        text.text = utils.fixTags(e,m,args.nohtml)
                        for match in re.finditer(r'{@hit \+?(.*?)}.*?{@damage (.*?)}',e):
                            if match.group(1) and match.group(2):
                                attack = ET.SubElement(action, 'attack')
                                attack.text = "{}|{}|{}".format(utils.remove5eShit(t['name']),utils.fixTags(match.group(1),m,False),utils.fixTags(match.group(2),m,False))



    if 'reaction' in m and m['reaction'] is not None:
        for t in m['reaction']:
            action = ET.SubElement(monster, 'reaction')
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
                    elif "entries" in e:
                        text = ET.SubElement(action, 'text')
                        subentries = []                    
                        for sube in e["entries"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                        text.text = "\n".join(subentries)
                    elif "items" in e:
                        text = ET.SubElement(action, 'text')
                        subentries = []                    
                        for sube in e["items"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                        text.text = "\n".join(subentries)
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
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        text.text = ""
                        for item in e["items"]:
                            if args.nohtml:
                                text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            else:
                                text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                    elif type(e) == dict and e["type"] == "list":
                        text.text = ""
                        for item in e["items"]:
                            text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                    else:
                        text.text = utils.fixTags(e,m,args.nohtml)

    if 'variant' in m and m['variant'] is not None:
        for t in m['variant']:
            action = ET.SubElement(monster, 'action')
            name = ET.SubElement(action, 'name')
            name.text = "Variant: " + utils.remove5eShit(t['name'])
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
                    elif "entries" in e:
                        if "name" in e:
                            vaction = ET.SubElement(monster, 'action')
                            vname = ET.SubElement(vaction, 'name')
                            vname.text = utils.remove5eShit(e['name'])
                        else:
                            vaction = action
                        text = ET.SubElement(vaction, 'text')
                        subentries = []                    
                        for sube in e["entries"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                        text.text = "\n".join(subentries)
                    elif "items" in e:
                        if "name" in e:
                            vaction = ET.SubElement(monster, 'action')
                            vname = ET.SubElement(vaction, 'name')
                            vname.text = utils.remove5eShit(e['name'])
                        else:
                            vaction = action
                        text = ET.SubElement(vaction, 'text')
                        subentries = []                    
                        for sube in e["items"]:
                            if type(sube) == str:
                                subentries.append(utils.remove5eShit(sube))
                            elif type(sube) == dict and "text" in sube:
                                subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                        text.text = "\n".join(subentries)
                    elif e["type"] == "spellcasting":
                        scAction = ET.SubElement(monster, 'action')
                        scName = ET.SubElement(scAction, 'name')
                        scName.text = utils.remove5eShit(e['name'])
                        text = ET.SubElement(scAction, 'text')
                        text.text = "\n".join(utils.remove5eShit(x) for x in e["headerEntries"])
                        if "will" in e:
                            text = ET.SubElement(scAction, 'text')
                            text.text = "At will: " + ", ".join(utils.remove5eShit(x) for x in e["will"])
                        if "daily" in e:
                            for k in e["daily"]:
                                if k.endswith("e"):
                                    text = ET.SubElement(scAction, 'text')
                                    text.text = "{}/day each: {}".format(k[:-1],", ".join(utils.remove5eShit(x) for x in e["daily"][k]))
                                else:
                                    text = ET.SubElement(scAction, 'text')
                                    text.text = "{}/day: {}".format(k,", ".join(utils.remove5eShit(x) for x in e["daily"][k]))
                        if "footerEntries" in e:
                                text = ET.SubElement(scAction, 'text')
                                text.text = "\n".join(utils.remove5eShit(x) for x in e["footerEntries"])
                    else:
                        print(e)
                        for i in e["entries"]:
                            text = ET.SubElement(action, 'text')
                            if 'name' in i:
                                text.text = "{}{}".format(
                                    i['name'] + " ", utils.remove5eShit(i['entry']))
                            else:
                                text.text = "\n".join(
                                    utils.remove5eShit(x) for x in i)
                else:
                    text = ET.SubElement(action, 'text')
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        text.text = ""
                        for item in e["items"]:
                            if args.nohtml:
                                text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            else:
                                text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                    elif type(e) == dict and e["type"] == "list":
                        text.text = ""
                        for item in e["items"]:
                            text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                    else:
                        text.text = utils.fixTags(e,m,args.nohtml)


    if 'legendary' in m:
        legendary = ET.SubElement(monster, 'legendary')

        if "legendaryHeader" in m:
            for h in m['legendaryHeader']:
                text = ET.SubElement(legendary, 'text')
                text.text = utils.remove5eShit(h)
        else:
            text = ET.SubElement(legendary, 'text')
            if "isNamedCreature" in m and m['isNamedCreature']:
                text.text = "{0} can take {1:d} legendary action{2}, choosing from the options below. Only one legendary action can be used at a time and only at the end of another creature's turn. {0} regains spent legendary action{2} at the start of its turn.".format(m['name'].split(' ', 1)[0],len(m['legendary']),"s" if len(m['legendary']) > 1 else "")
            else:
                text.text = "The {0} can take {1:d} legendary action{2}, choosing from the options below. Only one legendary action can be used at a time and only at the end of another creature's turn. The {0} regains spent legendary action{2} at the start of its turn.".format(m['type'] if type(m['type']) == str else "{} ({})".format(m['type']['type'],", ".join(m['type']['tags'])),len(m['legendary']),"s" if len(m['legendary']) > 1 else "")
        for t in m['legendary']:
            legendary = ET.SubElement(monster, 'legendary')
            name = ET.SubElement(legendary, 'name')
            if 'name' not in t:
                t['name'] = ""
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
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        text.text = ""
                        for item in e["items"]:
                            if args.nohtml:
                                text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            else:
                                text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                    elif type(e) == dict and e["type"] == "list":
                        text.text = ""
                        for item in e["items"]:
                            text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                    else:
                        text.text = utils.fixTags(e,m,args.nohtml)

    if 'legendaryGroup' in m:
        with open("./data/bestiary/meta.json") as f:
            meta = json.load(f)
            f.close()
        for l in meta['legendaryGroup']:
            if l['name'] != m['legendaryGroup']['name']:
                continue
            if 'lairActions' in l:
                legendary = ET.SubElement(monster, 'legendary')
                name = ET.SubElement(legendary, 'name')
                name.text = "Lair Actions"
                for t in l['lairActions']:
                    if type(t) == str:
                        text = ET.SubElement(legendary, 'text')
                        text.text = utils.fixTags(t,m,args.nohtml)
                        continue
                    if 'name' in t:
                        name = ET.SubElement(legendary, 'name')
                        name.text = "Lair Action: " + utils.remove5eShit(t['name'])
                    if t['type'] == 'list':
                        for i in t['items']:
                            text = ET.SubElement(legendary, 'text')
                            text.text = "• " + utils.fixTags(i,m,args.nohtml)
                        continue
                    #legendary = ET.SubElement(monster, 'legendary')
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
                            if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                                text.text = ""
                                for item in e["items"]:
                                    if args.nohtml:
                                        text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                                    else:
                                        text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            elif type(e) == dict and e["type"] == "list":
                                text.text = ""
                                for item in e["items"]:
                                    text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                            else:
                                text.text = utils.fixTags(e,m,args.nohtml)

            if 'regionalEffects' in l:
                legendary = ET.SubElement(monster, 'legendary')
                name = ET.SubElement(legendary, 'name')
                name.text = "Regional Effects"
                for t in l['regionalEffects']:
                    if type(t) == str:
                        text = ET.SubElement(legendary, 'text')
                        text.text = utils.fixTags(t,m,args.nohtml)
                        continue
                    if 'name' in t:
                        name = ET.SubElement(legendary, 'name')
                        name.text = "Regional Effect: " + utils.remove5eShit(t['name'])
                    if t['type'] == 'list':
                        for i in t['items']:
                            text = ET.SubElement(legendary, 'text')
                            text.text = "• " + utils.fixTags(i,m,args.nohtml)
                        continue
                    #legendary = ET.SubElement(monster, 'legendary')
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
                            if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                                text.text = ""
                                for item in e["items"]:
                                    if args.nohtml:
                                        text.text += "• {}: {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                                    else:
                                        text.text += "• <i>{}:</i> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            elif type(e) == dict and e["type"] == "list":
                                text.text = ""
                                for item in e["items"]:
                                    text.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                            else:
                                text.text = utils.fixTags(e,m,args.nohtml)



    if 'spellcasting' in m:
        spells = []
        for s in m['spellcasting']:
            trait = ET.SubElement(monster, 'trait')
            name = ET.SubElement(trait, 'name')
            name.text = utils.remove5eShit(s['name'])
            for e in s['headerEntries']:
                text = ET.SubElement(trait, 'text')
                text.text = utils.fixTags(e,m,args.nohtml)

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
                        ", ".join([utils.fixTags(e,m,args.nohtml) for e in dailyspells])
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
                        ", ".join([utils.fixTags(e,m,args.nohtml) for e in spellbois])
                    for spl in spellbois:
                        search = re.search(
                            r'{@spell+ (.*?)(\|.*)?}', spl, re.IGNORECASE)
                        if search is not None:
                            spells.append(search.group(1))
                slotse = ET.SubElement(monster, 'slots')
                slotse.text = ", ".join(slots)
            if 'footerEntries' in s:
                for e in s['footerEntries']:
                    text = ET.SubElement(trait, 'text')
                    text.text = utils.fixTags(e,m,args.nohtml)

        spellse = ET.SubElement(monster, 'spells')
        spellse.text = ", ".join(spells)

    description = ET.SubElement(monster, 'description')
    description.text = ""
    if 'entries' in m:
       for t in m['entries']:
            if type(t) == str:
                description.text += utils.fixTags(t,m,args.nohtml) + "\n"
                continue
            if 'name' in t:
                description.text += "<b>{}:</b>\n".format(utils.remove5eShit(t['name']))
            if 'entries' in t:
                for e in t['entries']:
                    if isinstance(e, dict):
                        if "colLabels" in e:
                            description.text += " | ".join(
                                [utils.remove5eShit(x) for x in e['colLabels']]) + "\n"
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
                                description.text += " | ".join(rowthing) + "\n"
                        elif "entries" in e:
                            subentries = []                    
                            for sube in e["entries"]:
                                if type(sube) == str:
                                    subentries.append(utils.fixTags(sube,m,args.nohtml))
                                elif type(sube) == dict and "text" in sube:
                                    subentries.append(utils.fixTags(sube["text"],m,args.nohtml))
                            description.text += "\n".join(subentries)
                        elif "items" in e:
                            description.text += "\n".join([utils.fixTags(x,m,args.nohtml) for x in e["items"]])
                        else:
                            description.text += "{}".format(utils.fixTags(e,m,args.nohtml))
                        description.text += "\n"
                    else:
                        if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                            for item in e["items"]:
                                description.text += "• <b>{}:</b> {}\n".format(item["name"],utils.fixTags(item["entry"],m,args.nohtml))
                            description.text += "\n"
                        elif type(e) == dict and e["type"] == "list":
                            for item in e["items"]:
                                description.text += "• {}\n".format(utils.fixTags(item,m,args.nohtml))
                            description.text += "\n"
                        else:
                            description.text += utils.fixTags(e,m,args.nohtml)
                            description.text += "\n"

    description.text += "<i>Source: {}</i>".format(sourcetext)
    if args.nohtml:
        description.text = re.sub('</?(i|b|spell)>', '', description.text)
    environment = ET.SubElement(monster, 'environment')
    if 'environment' in m:
        environment.text = ", ".join([x for x in m['environment']])
    # print(m['name'])
