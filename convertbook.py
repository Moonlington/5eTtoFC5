# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import xml.etree.cElementTree as ET
import json
import re
import sys
import os
import tempfile
import shutil
import argparse
import uuid
import copy
import utils
import time
# Argument Parser
parser = argparse.ArgumentParser(
    description="Converts 5eTools json files to FC5 compatible XML files.")
parser.add_argument(
    '--book',
    dest="book",
    action='store',
    default=False,
    help="id for book to convert")
parser.add_argument(
    '-v',
    dest="verbose",
    action='store_const',
    const=True,
    default=False,
    help="verbose output (default: false)")
parser.add_argument(
    '-o',
    dest="output",
    action='store',
    default=None,
    help="output into given output (default: book-[id].module)")

args = parser.parse_args()

tempdir = tempfile.mkdtemp(prefix="ddbtoxml_")


numbers = ['zero','one','two','three','four']
stats = {"str":"Strength","dex":"Dexterity","con":"Constitution","int":"Intelligence","wis":"Wisdom","cha":"Charisma"}

def fixTags(s):
    s = re.sub(r'{@([bi]) (.*?)}',r'<\1>\2</\1>', s)
    s = re.sub(r'{@spell (.*?)}', r'<spell>\1</spell>', s)
    s = re.sub(r'{@link (.*?)\|(.*?)?}', r'<a href="\2">\1</a>', s)
    def createMLinks(matchobj):
        return "<a href=\"/monster/{}\">{}</a>".format(matchobj.group(1),matchobj.group(2))
    s = re.sub(r'{@creature (.*?)\|\|(.*?)?}', createMLinks, s)
    def createMLink(matchobj):
        return "<a href=\"/monster/{}\">{}</a>".format(matchobj.group(1),matchobj.group(1).title())
    s = re.sub(r'{@creature (.*?)}', createMLink, s)
    def createILink(matchobj):
        return "<a href=\"/item/{}\">{}</a>".format(matchobj.group(1),matchobj.group(1).title())
    s = re.sub(r'{@item (.*?)(\|.*?)?}', createILink, s)
    def createCLink(matchobj):
        return "<a href=\"/page/{}\">{}</a>".format(matchobj.group(1),matchobj.group(1).title())
    s = re.sub(r'{@class (.*?)}', createCLink, s)
    s = re.sub(r'{@condition (.*?)}', createCLink, s)

    if '{@' in s:
        s = utils.remove5eShit(s)

    if re.search(r'{[@=](.*?)}',s):
        s = fixTags(s)
    return s

def processSection(order,d,mod,parentuuid=None,parentname=None):
    suborder = 0
    sectionuuid = str(uuid.uuid4())
    if parentuuid:
        page = ET.SubElement(module, 'page', { 'id': sectionuuid, 'parent': parentuuid, 'sort': str(order)})
    else:
        page = ET.SubElement(module, 'page', { 'id': sectionuuid, 'sort': str(order) })
    name = ET.SubElement(page,'name')
    name.text = d['name']
    content = ET.SubElement(page,'content')
    if parentuuid:
        content.text = "<h2>{}</h2>\n".format(d['name'])
    else:
        content.text = "<h1>{}</h1>\n".format(d['name'])
    slug = ET.SubElement(page,'slug')
    slug.text = d['name']
    if d['name'] == "Classes" and args.book.lower() == 'phb':
        add_fluff = ['barbarian','bard','cleric','druid','fighter','monk','paladin','ranger','rogue','sorcerer','warlock','wizard']
        for fl in add_fluff:
            with open("./data/class/class-{}.json".format(fl),encoding='utf-8') as f:
                fluff = json.load(f)
                f.close()
            for cl in fluff['class']:
                if cl['name'].lower() == fl:
                    for f in cl['fluff']:
                        if 'source' in f and f['source'] != 'PHB':
                            continue
                        classentries = []
                        for e in f['entries']:
                            if type(e) == dict and 'source' in e and e['source'] != 'PHB':
                                continue
                            classentries.append(copy.deepcopy(e))
                        classfeatures = {
                            "type": "entries",
                            "name": "Class Features",
                            "entries": [
                                "As a {}, you gain the following class features.".format(cl['name']),
                            ]
                        }
                        classfeatures['entries'].append({
                            "type": "entries",
                            "name": "Hit Points",
                            "entries": [
                                { "type": "entries", "name": "Hit Dice:", "entries": [
                                    "{}d{} per {} level".format(cl['hd']['number'],cl['hd']['faces'],cl['name'].lower())
                                ] },
                                { "type": "entries", "name": "Hit Points at 1st Level:", "entries": [
                                    "{} + your Constitution modifier".format(cl['hd']['faces'])
                                ] },
                                { "type": "entries", "name": "Hit Points at Higher Levels:", "entries": [
                                    "{}d{} (or {:.0}) + your Constitution modifier per {} level after 1st".format(cl['hd']['number'],cl['hd']['faces'],(cl['hd']['faces']/2)+1,cl['name'].lower())
                                ] }
                            ]
                        })
                        classfeatures['entries'].append({
                            "type": "entries",
                            "name": "Proficiencies",
                            "entries": [
                                { "type": "entries", "name": "Armor:", "entries": [
                                    re.sub(r'(light|medium|heavy),',r'\1 armor,',", ".join(cl['startingProficiencies']['armor'])).capitalize() if 'armor' in cl['startingProficiencies'] else "None"
                                ] },
                                { "type": "entries", "name": "Weapons:", "entries": [
                                    re.sub(r'(simple|martial),',r'\1 weapons,',", ".join(cl['startingProficiencies']['weapons'])).capitalize() if 'weapons' in cl['startingProficiencies'] else "None"
                                ] },
                                { "type": "entries", "name": "Tools:", "entries": [
                                    ", ".join(cl['startingProficiencies']['tools']) if 'tools' in cl['startingProficiencies'] else "None"
                                ] },
                                { "type": "entries", "name": "Saving Thows:", "entries": [
                                    ", ".join([stats[x] for x in cl["proficiency"]])
                                ] },
                                { "type": "entries", "name": "Skills:", "entries": [
                                    "Choose any {}".format(numbers[cl["skills"]["choose"]["count"]]) if "skills" in cl and "choose" in cl["skills"] and len(cl["skills"]["choose"]["from"]) == 18 else "Choose {} from {}".format(numbers[cl["skills"]["choose"]["count"]],"{}, and {}".format(", ".join(cl["skills"]["choose"]["from"][:-1]),cl["skills"]["choose"]["from"][-1])) if "skills" in cl else "None"
                                ] }
                            ]
                        })
                        if 'subclasses' in cl:
                            subclasses = []
                            for sc in cl["subclasses"]:
                                if 'source' in sc and sc['source'] != "PHB":
                                    continue
                                for scf in sc["subclassFeatures"]:
                                    subclasses.append({
                                        "name": sc["name"],
                                        "type": "entries",
                                        "entries": copy.deepcopy(scf)
                                    })
                            classfeatures['entries'].append({
                                "type": "entries",
                                "name": cl["subclassTitle"] if "subclassTitle" in cl else "Subclasses",
                                "entries": subclasses
                            })

                        classentries.append(classfeatures)
                        for e in cl['classFeatures']:
                            if type(e) == dict and 'source' in e and e['source'] != 'PHB':
                                continue
                            if type(e) == list:
                                for i in e:
                                    if 'source' not in i or i['source'] == 'PHB':
                                        entry = copy.deepcopy(i)
                                        if 'type' not in entry:
                                            entry['type'] = "entries"
                                        classentries.append(entry)
                                continue
                            entry = copy.deepcopy(e)
                            if type(e) == dict and 'type' not in entry:
                                entry['type'] = "entries"
                            classentries += entry
                        d['entries'].append({
                                "type": "section",
                                "name": cl['name'],
                                "entries": classentries
                            })
    if d['name'] == "Races" and args.book.lower() == 'phb':
        with open("./data/fluff-races.json",encoding='utf-8') as f:
            fluff = json.load(f)
            f.close()
        for race in fluff['race']:
            if 'source' in race and race['source'] != 'PHB':
                continue
            elif re.match(r'.*? \(.*?\)',race['name']):
                continue
            entries = copy.deepcopy(race['entries'])
            if 'images' in race:
                entries = race['images'] + entries
            with open("./data/races.json",encoding='utf-8') as f:
                rd = json.load(f)
                f.close()
            for r in rd['race']:
                if 'source' in race and race['source'] != 'PHB':
                    continue
                if r['name'] != race['name']:
                    continue

                rdata = r
                traits = []
                if race['name'] == "Dwarf":
                    traits.append("Your dwarf character has an assortment of inborn abilities, part and parcel of dwarven nature.")
                if race['name'] == "Elf":
                    traits.append("Your elf character has a variety of natural abilities, the result of thousands of years of elven refinement.")
                if race['name'] == "Halfling":
                    traits.append("Your halfling character has a number of traits in common with all other halflings.")
                if race['name'] == "Human":
                    traits.append("It's hard to make generalizations about humans, but your human character has these traits.")
                if race['name'] == "Dragonborn":
                    traits.append("Your draconic heritage manifests in a variety of traits you share with other dragonborn.")
                if race['name'] == "Gnome":
                    traits.append("Your gnome character has certain characteristics in common with all other gnomes.")
                if race['name'] == "Half-Elf":
                    traits.append("Your half-elf character has some qualities in common with elves and some that are unique to half-elves.")
                if race['name'] == "Half-Orc":
                    traits.append("Your half-orc character has certain traits deriving from your orc ancestry.")
                if race['name'] == "Tiefling":
                    traits.append("Tieflings share certain racial traits as a result of their infernal descent.")

                subtraits = []
                if 'ability' in r:
                    scoreincrease = []
                    if race['name'] == 'Human':
                        scoreincrease.append = ("Your ability scores each increase by 1.")
                    else:
                        for ability in r['ability']:
                            for stat,val in ability.items():
                                if stat in stats.keys():
                                    scoreincrease.append("your {} score increases by {}".format(stats[stat],val))
                                elif stat == "choose":
                                    scoreincrease.append("{} other ability scores of your choice increase by {}".format(numbers[val['count']],val['amount'] if 'amount' in val else 1))
                    subtraits.append({ "type": "entries", "name": "Ability Score Increase", "entries": ["{}, and {}.".format(", ".join(scoreincrease[:-1]),scoreincrease[-1]).capitalize() if len(scoreincrease) > 1 else scoreincrease[0].capitalize()] })

                if 'entries' in r:
                    hasspeed = False
                    sizepos = 0
                    i = 0
                    for e in r['entries']:
                        i += 1
                        if 'name' in e and e['name'] == "Size":
                            sizepos = i
                        if 'speed' in r and 'name' in e and e['name'] == "Speed":
                            hasspeed = True
                            if type(e['entries'][0]) == str:
                                e['entries'][0] = "Your base walking speed is {} feet. {}".format(r['speed'],e['entries'][0])
                            else:
                                e['entries'].insert(0,"Your base walking speed is {} feet.".format(r['speed']))
                    if not hasspeed:
                        r['entries'].insert(sizepos,{ "type": "entries", "name": "Speed", "entries": ["Your base walking speed is {} feet.".format(r['speed'])] } )
                    subtraits += r['entries']

                traits.append({ "type": "entries", "entries": subtraits })
                for r in fluff['race']:
                    if 'source' in r and r['source'] != 'PHB':
                        continue
                    subracere = re.match(r'{} \((.*?)\)'.format(race['name']),r['name'])
                    if subracere:
                        subracename = subracere.group(1)
                        subrace = copy.deepcopy(r['entries'])
                        if 'images' in r:
                            subrace = r['images'] + entries
                        for rs in rdata['subraces']:
                            if 'source' in race and race['source'] != 'PHB':
                                continue
                            if rs['name'] != subracename:
                                continue
                            else:
                                subracetraits = []
                                if 'ability' in r:
                                    scoreincrease = []
                                    for ability in r['ability']:
                                        for stat,val in ability.items():
                                            if stat in stats.keys():
                                                scoreincrease.append("your {} score increases by {}".format(stats[stat],val))
                                            elif stat == "choose":
                                                scoreincrease.append("{} other ability scores of your choice increase by {}".format(numbers[val['count']],val['amount'] if 'amount' in val else 1))
                                subracetraits.append({ "type": "entries", "name": "Ability Score Increase", "entries": ["{}, and {}.".format(", ".join(scoreincrease[:-1]),scoreincrease[-1]).capitalize() if len(scoreincrease) > 1 else scoreincrease[0].capitalize()] })
                                if 'entries' in rs:
                                        subrace.append({
                                            "type": "entries",
                                            "entries": subracetraits + rs['entries']
                                        })
                        if subracename == "Drow":
                            subracename = "Dark Elf (Drow)"
                        else:
                            subracename = "{} {}".format(subracename,race['name'])
                        traits.append({
                                "type": "entries",
                                "name": subracename,
                                "entries": subrace
                            })
                entries.append({
                            "type": "entries",
                            "name": "{} Traits".format(race['name']),
                            "entries": traits
                    })
                if race['name'] == "Human":
                    entries.append({
                        "type": "inset",
                        "name": "Variant Human Traits",
                        "entries": [
                            "If your campaign uses the optional feat rules fram chapter 5, your Dungeon Master might allow these variant traits, all of which replace the human's Ability Score Increase trait.",
                            { "type": "entries", "name": "Ability Score Increase", "entries": [ "Two different ability scores of your choice increase by 1." ] },
                            { "type": "entries", "name": "Skills", "entries": [ "You gain proficiency in one skill of your choice." ] },
                            { "type": "entries", "name": "Feat", "entries": [ "You gain one feat of your choice." ] }
                        ] } )           
                break

            d['entries'].append({
                    "type": "section",
                    "name": race['name'],
                    "entries": entries
                })
    if d['name'] == "Backgrounds" and args.book.lower() == 'phb':
        with open("./data/fluff-backgrounds.json",encoding='utf-8') as f:
            fluff = json.load(f)
            f.close()
        with open("./data/backgrounds.json",encoding='utf-8') as f:
            bgs = json.load(f)
            f.close()
        for bg in fluff['background']:
            if 'source' in bg and bg['source'] != 'PHB':
                continue
            elif re.match(r'Variant .*? \(.*?\)',bg['name']):
                continue
            entries = copy.deepcopy(bg['entries'])
            for bgd in bgs['background']:
                if bgd['name'] != bg['name']:
                    continue
                elif 'entries' in bgd:
                    entries += bgd['entries']
            for bgv in fluff['background']:
                if re.match(r'Variant {} \(.*?\)'.format(bg['name']),bgv['name']):
                    variant = copy.deepcopy(bgv['entries'])
                    for bgvd in bgs['background']:
                        if bgvd['name'] != bgv['name']:
                            continue
                        elif 'entries' in bgvd:
                            variant += bgvd['entries']
                    entries.append({
                            "type": "entries",
                            "name": bgv['name'],
                            "entries": variant
                        })
            d['entries'].append({
                    "type": "section",
                    "name": bg['name'],
                    "entries": entries
                })

    if d['name'] == "Conditions" and args.book.lower() == 'phb':
        with open("./data/conditionsdiseases.json",encoding='utf-8') as f:
            conditions = json.load(f)
            f.close()
        for cond in conditions['condition']:
            if cond['source'] != 'PHB':
                continue
            entries = copy.deepcopy(cond['entries'])
            if os.path.isfile("./img/conditionsdiseases/PHB/{}.png".format(cond['name'].lower())):
                entries.append({
                        "type": "image",
                        "href": {
                            "type": "internal",
                            "path": "conditionsdiseases/PHB/{}.png".format(cond['name'].lower())
                            }
                        })
            d['entries'].append({
                "type": "section",
                "name": cond['name'],
                "entries": entries
                })

    if d['name'] == "Feats" and args.book.lower() == 'phb':
        with open("./data/feats.json",encoding='utf-8') as f:
            feats = json.load(f)
            f.close()
        for feat in feats['feat']:
            if feat['source'] != 'PHB':
                continue
            entries = copy.deepcopy(feat['entries'])
            prereq = []
            if 'prerequisite' in feat:
                for pre in feat['prerequisite']:
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
                                prereq.append("Proficiency with {} {}".format(k,v))
                entries.insert(0,"<i>Prerequisite: {}</i>".format(", ".join(prereq)))
            d['entries'].append({
                "type": "section",
                "name": feat['name'],
                "entries": entries
                })

    for e in d['entries']:
        if type(e) == dict:
            if e['type'] == 'insetReadaloud':
                content.text += "<blockquote class=\"read\">\n"
                for x in e['entries']:
                    content.text += "<p>{}</p>\n".format(fixTags(x))
                content.text += "</blockquote>\n"
            elif e['type'] == 'inset':
                content.text += "<blockquote>\n"
                if 'name' in e:
                    content.text += "<h3>{}</h3>\n".format(e['name'])
                for x in e['entries']:
                    content.text += getEntry(x)
                content.text += "</blockquote>\n"
            elif e['type'] == 'abilityGeneric':
                content.text += "<p class=\"text-center\">{}</p>\n".format(fixTags(e['text']))
            elif e['type'] == 'abilityDc':
                content.text += "<p class=\"text-center\"><b>{} save DC</b> = 8 + your proficiency bonus + your {} modifier</p>\n".format(e['name']," modifier + your ".join([stats[x] for x in e["attributes"]]))
            elif e['type'] == 'entries':
                if 'name' in e:
                    if parentuuid:
                        content.text += "<h2>{}</h2>\n".format(e['name'])
                    else:
                        content.text += "<h3>{}</h3>\n".format(e['name'])
                for se in e['entries']:
                    if type(se) == dict:
                        if 'type' not in se:
                            se['type'] = "entries"
                        if se['type'] == "list":
                            content.text += "<ul>\n"
                            for i in se['items']:
                                content.text += "<li>{}</li>".format(getEntry(i))
                            content.text += "</ul>\n"
                        elif se['type'] == "entries":
                            if 'name' in se:
                                if parentuuid:
                                    content.text += "<h4>{}</h4>\n".format(se['name'])
                                else:
                                    content.text += "<h3>{}</h3>\n".format(se['name'])
                            for see in se['entries']:
                                if type(see) == dict:
                                    content.text += getEntry(see)
                                else:
                                    content.text += "<p>{}</p>".format(fixTags(see))
                        elif se['type'] == 'inset':
                            content.text += "<blockquote>\n"
                            if 'name' in se:
                                content.text += "<h4>{}</h4>\n".format(se['name'])
                            for x in se['entries']:
                                content.text += getEntry(x)
                            content.text += "</blockquote>\n"
                        elif se['type'] == 'abilityGeneric':
                            content.text += "<p class=\"text-center\">{}</p>\n".format(fixTags(se['text']))
                        elif se['type'] == 'abilityDc':
                            content.text += "<p class=\"text-center\"><b>{} save DC</b> = 8 + your proficiency bonus + your {} modifier</p>\n".format(se['name']," modifier + your ".join([stats[x] for x in se["attributes"]]))
                        elif se['type'] == 'table':
                            content.text += getTable(se)
                        elif se['type'] == 'tableGroup':
                            content.text += "\n".join([getTable(x) for x in se['tables']])
                        elif se['type'] == 'image':
                            content.text += "<img src=\"{}\">\n".format(os.path.basename(se['href']['path']))
                            shutil.copy("./img/" + se['href']['path'],os.path.join(tempdir,os.path.basename(se['href']['path'])))
                        elif se['type'] == 'options':
                            for x in se['entries']:
                                content.text += getEntry(x)
                        elif se['type'] == 'inlineBlock':
                            content.text += "<blockquote>\n"
                            content.text += "<p>\n"
                            content.text += " ".join([re.sub(r'</?p>','',getEntry(x)) for x in se['entries']])
                            content.text += "</p>\n"
                            content.text += "</blockquote>\n"
                        elif se['type'] == 'inline':
                            content.text += "<p>\n"
                            content.text += " ".join([re.sub(r'</?p>','',getEntry(x)) for x in se['entries']])
                            content.text += "</p>\n"
                        elif se['type'] == 'quote':
                            content.text += "<p><i>{}</i></p><span class=\"text-right\">&mdash;{}<i>{}</i></span>".format("<br>".join(se['entries']),se['by'],', '+se['from'] if 'from' in se else '')
                        else:
                            print("TODO: entries type:",se['type'])
                    else:
                        content.text += "<p>{}</p>".format(fixTags(se))
            elif e['type'] == 'list':
                content.text += "<ul>\n"
                for i in e['items']:
                    content.text += "<li>{}</li>".format(getEntry(i))
                content.text += "</ul>\n"
            elif e['type'] == 'table':
                content.text += getTable(e)
            elif e['type'] == 'tableGroup':
                content.text += "\n".join([getTable(x) for x in e['tables']])
            elif e['type'] == 'section':
                suborder += 1
                subpage = processSection(suborder,e,mod,sectionuuid,d['name'])
                if d['name'] != "Classes" and d['name'] != "Conditions":
                    content.text += "\n<a href=\"/page/{}\">{}</a>\n<br>\n".format(subpage,e['name'])
            elif e['type'] == 'image':
                content.text += "<img src=\"{}\">\n".format(os.path.basename(e['href']['path']))
                shutil.copy("./img/" + e['href']['path'],os.path.join(tempdir,os.path.basename(e['href']['path'])))
            elif e['type'] == 'gallery':
                for image in e['images']:
                    content.text += "<img src=\"{}\">\n".format(os.path.basename(image['href']['path']))
                    shutil.copy("./img/" + image['href']['path'],os.path.join(tempdir,os.path.basename(image['href']['path'])))
            elif e['type'] == 'inlineBlock':
                content.text += "<blockquote>\n"
                content.text += "<p>\n"
                content.text += " ".join([re.sub(r'</?p>','',getEntry(x)) for x in e['entries']])
                content.text += "</p>\n"
                content.text += "</blockquote>\n"
            elif e['type'] == 'quote':
                content.text += "<blockquote>\n"
                for x in e['entries']:
                    content.text += getEntry(x)
                content.text += "</blockquote>\n"
            elif e['type'] == 'inline':
                content.text += "<p>\n"
                content.text += " ".join([re.sub(r'</?p>','',getEntry(x)) for x in e['entries']])
                content.text += "</p>\n"
            else:
                print("TODO: entry type:",e['type'])
        else:
            content.text += "<p>{}</p>".format(fixTags(e))
    if parentname:
        content.text += "<br>\n<a href=\"/page/{}\">{}</a>\n<br>\n".format(parentname,parentname)
    content.text = content.text.rstrip()
    return d['name']

def getEntry(e):
    if type(e) == dict:
        if 'source' in e and e['source'].lower() != args.book:
            return ""
        content = ""
        if 'name' in e:
            content += "<h4>{}</h4>\n".format(e['name'])
        if 'type' not in e and 'entries' in e:
            e['type'] = 'entries'
        if e['type'] == "list":
            content += "<ul>\n"
            for i in e['items']:
                if type(i) == dict:
                    content += "<li><b>{}</b> {}</li>".format(i['name'],fixTags(i['entry']))
                else:
                    content += "<li>{}</li>\n".format(fixTags(i))
            content += "</ul>\n"
            return content
        elif e['type'] == "entries" or e['type'] == "patron" or e['type'] == "options":
            if 'name' in e and type(e['entries'][0]) == str:
                e['entries'][0] = "<b>{}</b> {}".format(e['name'],e['entries'][0])
            elif 'name' in e:
                e['entries'].insert(0,"<b>{}</b> ".format(e['name']))
            return getEntry(e['entries'])
        elif e['type'] == "table":
            return getTable(e)
        elif e['type'] == "inset":
            content += "<blockquote>\n"
            if 'name' in e:
                content += "<h4>{}</h4>\n".format(e['name'])
            for x in e['entries']:
                content += getEntry(x)
            content += "</blockquote>\n"
            return content
        elif e['type'] == "item":
            return "<b>{}</b> {}".format(e['name'],fixTags(e['entry']))
        elif e['type'] == "tableGroup":
            for table in e['tables']:
                content += getTable(table)
            return content
        elif e['type'] == "link":
            return "<a href=\"{}\">{}</a>".format(e['href']['path'],e['text'])
        elif e['type'] == "abilityGeneric":
            return "<p class=\"text-center\">{}</p>\n".format(fixTags(e['text']))
        elif e['type'] == "abilityDc":
            return "<p class=\"text-center\"><b>{} save DC</b> = 8 + your proficiency bonus + your {} modifier</p>\n".format(e['name']," modifier + your ".join([stats[x] for x in e["attributes"]]))
        elif e['type'] == "abilityAttackMod":
            return "<p class=\"text-center\"><b>{} attack modifier</b> = your proficiency bonus + your {} modifier</p>\n".format(e['name']," modifier + your ".join([stats[x] for x in e["attributes"]]))
        elif e['type'] == 'image':
            shutil.copy("./img/" + e['href']['path'],os.path.join(tempdir,os.path.basename(e['href']['path'])))
            return "<img src=\"{}\">\n".format(os.path.basename(e['href']['path']))
        elif e['type'] == 'inline':
            content += "<p>\n"
            content += " ".join([re.sub(r'</?p>','',getEntry(x)) for x in se['entries']])
            content += "</p>\n"
            return content
        elif e['type'] == 'cell':
            if 'exact' in e['roll']:
                return "{}".format(e['roll']['exact'])
            elif 'min' in e['roll'] and 'max' in e['roll']:
                return "{}-{}".format(e['roll']['min'],e['roll']['max'])
        elif e['type'] == 'quote':
            return "<p><i>{}</i></p><span class=\"text-right\">&mdash;{}<i>{}</i></span>".format("<br>".join(e['entries']),e['by'],', '+e['from'] if 'from' in e else '')
        else:
            print("Dont know",e['type'])
            print(e)
            return "UNKNOWN"
    elif type(e) == list:
        itemlist = []
        for i in e:
            itemlist.append(getEntry(i))
        return "\n".join(itemlist)
    elif e == "":
        return " &nbsp; "
    else:
        return "<p>{}</p>".format(fixTags(str(e)))

def getTable(e):
    content = "<table>\n"
    if 'caption' in e:
        content += "<caption>{}</caption>\n".format(fixTags(e['caption']))
    if 'colLabels' in e:
        content += "<thead><tr>\n"
        for i in range(len(e['colLabels'])):
            content += "<td style=\"{}\">{}</td>".format(e['colStyles'][i],fixTags(e['colLabels'][i]))
        content += "</thead></tr>\n"
    content += "<tbody>\n"
    for row in e['rows']:
        if type(row) == dict:
            content += "<tr class=\"{}\">\n".format(row['style'])
            for rc in row['row']:
                content += "<td>{}</td>\n".format(getEntry(rc))
        else:
            content += "<tr>\n"
            for rc in row:
                content += "<td>{}</td>\n".format(getEntry(rc))
        content += "</tr>\n"
    content += "</tbody>\n"
    content += "</table>\n"
    return content

with open("./data/books.json",encoding='utf-8') as f:
        b = json.load(f)
        f.close()

for book in b['book']:
    if not args.book:
        print("{:8s}: {}".format(book["id"],book["name"]))
        continue
    elif args.book.lower() != book["id"].lower():
        continue

    with open("./data/book/book-{}.json".format(book["id"].lower())) as f:
        data = json.load(f)
        f.close()

    module = ET.Element(
        'module', { 'id': book["id"] + " " + book["name"],'version': "{:.0f}".format(time.time()) } )
    name = ET.SubElement(module, 'name')
    name.text = book['name']
    author = ET.SubElement(module, 'author')
    author.text = book['author']
    category = ET.SubElement(module, 'category')
    category.text = "rules"
    code = ET.SubElement(module, 'code')
    code.text = book['id']
    image = ET.SubElement(module, 'image')
    image.text = os.path.basename(book['image'])
    shutil.copy("./img/" + book['image'],os.path.join(tempdir,os.path.basename(book['image'])))
    slug = ET.SubElement(module, 'slug')
    slug.text = book['name']
    description = ET.SubElement(module, 'description')
    description.text = "By {}\nPublished {}".format(book['author'],book['published'])

    order = 0
    for d in data['data']:
        if d['type'] == "section":
            order += 1
            processSection(order,d,module)
        else:
            print("Need to handle type: ",data['type'])



if args.book:
    # write to file
    tree = ET.ElementTree(utils.indent(module, 1))
    tree.write(os.path.join(tempdir,"module.xml"), xml_declaration=True, short_empty_elements=False, encoding='utf-8')

    zipfile = shutil.make_archive("module","zip",tempdir)
    if args.output:
        os.rename(zipfile,args.output)
    else:
        os.rename(zipfile,"book-{}.module".format(args.book))
