import xml.etree.cElementTree as ET
import re
import utils
import json
import os
from slugify import slugify
from wand.image import Image

def parseClass(m, compendium, args):
#    for eachClasss in compendium.findall('Class'):
#        if eachClasss.find('name').text == m['name']:
#            m['name'] = "{} (DUPLICATE IN {})".format(m['name'],m['source'])
    Class = ET.SubElement(compendium, 'class')
    name = ET.SubElement(Class, 'name')
    name.text = m['name']
    hd = ET.SubElement(Class, 'hd')
    hd.text = str(m['hd']['faces'])
    saveProficiency = []
    if "str" in m['proficiency']:
        saveProficiency.append("Strength")
    if "dex" in m['proficiency']:
        saveProficiency.append("Dexterity")
    if "con" in m['proficiency']:
        saveProficiency.append("Constitution")
    if "int" in m['proficiency']:
        saveProficiency.append("Intelligence")
    if "wis" in m['proficiency']:
        saveProficiency.append("Wisdom")
    if "cha" in m['proficiency']:
        saveProficiency.append("Charisma")
    proficiency = ET.SubElement(Class, 'proficiency')
    proficiencyList = []
    numSkills = ET.SubElement(Class, 'numSkills')
    for skill in m['startingProficiencies']['skills']:
        if 'choose' in skill and 'from' in skill['choose']:
            skillList = skill['choose']['from']
            proficiencyList = saveProficiency + skillList
            proficiencytext = ", ".join(proficiencyList).title()
            proficiency.text = proficiencytext
            numberofSkills = str(skill['choose']['count'])
            numSkills.text = str(skill['choose']['count'])
    spellAbility = ET.SubElement(Class, 'spellAbility')
    spellcastingAbility = None
    if (spellcastingAbility is None):
        if 'spellcastingAbility' in m:
            if m['spellcastingAbility'] == "str":
                spellcastingAbility = "Strength"
            elif m['spellcastingAbility'] == "dex":
                spellcastingAbility = "Dexterity"
            elif m['spellcastingAbility'] == "con":
                spellcastingAbility = "Constitution"
            elif m['spellcastingAbility'] == "int":
                spellcastingAbility = "Intelligence"
            elif m['spellcastingAbility'] == "wis":
                spellcastingAbility = "Wisdom"
            elif m['spellcastingAbility'] == "cha":
                spellcastingAbility = "Charisma"
        else:
            spellcastingAbility = ""
            ET.tostring(ET.fromstring('<mytag/>'), short_empty_elements=False)
    spellAbility.text = spellcastingAbility
        
    StartingFeature = ET.SubElement(Class, 'feature')
    SFName = ET.SubElement(StartingFeature, 'name')
    SFName.text = "Starting " + m['name']
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = "As a 1st-level " + m['name'] + ", you begin play with " + str(
        m['hd']['faces']) + "+your Constitution modifier hit points."
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = ""
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = "You are proficient with the following items, in addition to any proficiencies provided by your race or background."
    SFText = ET.SubElement(StartingFeature, 'text')
    if "armor" in m['startingProficiencies']:
        armortext = ", ".join(m['startingProficiencies']['armor'])
    else:
        armortext = "none"
    SFText.text = "&#8226; Armor: " + armortext.title()
    SFText = ET.SubElement(StartingFeature, 'text')
    if "weapons" in m['startingProficiencies']:
        weapontext = ", ".join(m['startingProficiencies']['weapons'])
    else:
        weapontext = "none"
    SFText.text = "&#8226; Weapons: " + weapontext.title()
    SFText = ET.SubElement(StartingFeature, 'text')
    if "tools" in m['startingProficiencies']:
        SFText.text = "&#8226; Tools: " + ", ".join(m['startingProficiencies']['tools']).title()
    else:
        SFText.text = "&#8226; Tools: None"
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = "&#8226; Skills: Choose " + numberofSkills + " from " + ", ".join(skillList).title()
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = ""
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = "You begin play with the following equipment, in addition to any equipment provided by your background."
    for startingEquipment in m['startingEquipment']['default']:
        SFText = ET.SubElement(StartingFeature, 'text')
        SFText.text = "&#8226; " + utils.remove5eShit(startingEquipment)
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = ""
    if "goldAlternative" in m['startingEquipment']:
        SFText = ET.SubElement(StartingFeature, 'text')
        SFText.text = "Alternatively, you may start with " + utils.remove5eShit(
            m['startingEquipment']['goldAlternative']).replace('Ã—','x') + " gp and choose your own equipment."
        SFText = ET.SubElement(StartingFeature, 'text')
        SFText.text = ""
    SFText = ET.SubElement(StartingFeature, 'text')
    SFText.text = "Source: " + m['source']
    armor = ET.SubElement(Class, 'armor')
    armor.text = armortext
    weapons = ET.SubElement(Class, 'weapons')
    weapons.text = weapontext
    tools = ET.SubElement(Class, 'tools')
    if "tools" in m['startingProficiencies']:
        tools.text = ", ".join(m['startingProficiencies']['tools'])
    else:
        tools.text = "none"
    if "goldAlternative" in m['startingEquipment']:
        wealth = ET.SubElement(Class, 'wealth')
        wealth.text = str(utils.remove5eShit(m['startingEquipment']['goldAlternative']).replace('Ã—','x'))
    level = 0
    currentsubclassfeature = 0
    for classFeatures in m['classFeatures']:
        level += 1
        for cFeat in classFeatures:
            myattributes = {"level": str(level)}
            autolevel = ET.SubElement(Class, 'autolevel', myattributes)
            Feature = ET.SubElement(autolevel, 'feature')
            Fname = ET.SubElement(Feature, 'name')
            Fname.text = cFeat['name']
            print(cFeat['name'])
            for e in cFeat['entries']:
                if "entries" in e:
                    text = ET.SubElement(Feature, 'text')
                    subentries = []                    
                    for sube in e["entries"]:
                        if type(sube) == str:
                            subentries.append(utils.remove5eShit(utils.fixTags(sube,m)))
                        elif type(sube) == dict and "text" in sube:
                            subentries.append(utils.remove5eShit(utils.fixTags(sube["text"],m)))
                    text.text = "\n".join(subentries)
                else:
                    if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                        for item in e["items"]:
                            text = ET.SubElement(Feature, 'text')
                            text.text = "{}: {}".format(item["name"],utils.remove5eShit(utils.fixTags(item["entry"],m)))
                    elif type(e) == dict and e["type"] == "list":
                        for item in e["items"]:
                            text = ET.SubElement(Feature, 'text')
                            text.text = "{}".format(utils.remove5eShit(utils.fixTags(item,m)))
                    else:
                        text = ET.SubElement(Feature, 'text')
                        text.text = utils.remove5eShit(utils.fixTags(e,m))
                if 'gainSubclassFeature' in cFeat and cFeat['gainSubclassFeature']:
                    print("Gain a Subclass Feature")
                    currentsubclassfeature += 1
                    for subclass in m['subclasses']:
                        if 'name' in subclass:
                            numberofsubclasses = 1
                            if currentsubclassfeature==1:
                                autolevel = ET.SubElement(Class, 'autolevel', myattributes)
                                featureattributes={"optional": "YES"}
                                subclassOut = ET.SubElement(autolevel, 'feature',featureattributes)
                                text = ET.SubElement(subclassOut, 'name')
                                text.text = subclass['name']
                            for subclassFeature in subclass['subclassFeatures']:
                                for entries in subclassFeature:
                                    numberofsubclasses += 1
                                    for e in entries['entries']:
                                        if type(e) == str:
                                            
                                            text = ET.SubElement(subclassOut, 'text')
                                            text.text = e
                                        if "entries" in e:
                                            if numberofsubclasses-1 == currentsubclassfeature and currentsubclassfeature == 1:
                                                autolevel = ET.SubElement(Class, 'autolevel', myattributes)
                                                featureattributes={"optional": "YES"}
                                                subclassOut = ET.SubElement(autolevel, 'feature',featureattributes)
                                                text = ET.SubElement(subclassOut, 'name')
                                                text.text=e['name'] + ' (' + subclass['name'] + ')'
                                                for e in e['entries']:
                                                    if "colLabels" in e:
                                                        text = ET.SubElement(subclassOut, 'text')
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
                                                            text = ET.SubElement(subclassOut, 'text')
                                                            text.text = " | ".join(rowthing)
                                                    elif "entries" in e:
                                                        text = ET.SubElement(subclassOut, 'text')
                                                        subentries = []                    
                                                        for sube in e["entries"]:
                                                            if type(sube) == str:
                                                                subentries.append(utils.remove5eShit(utils.fixTags(sube,m)))
                                                            elif type(sube) == dict and "text" in sube:
                                                                subentries.append(utils.remove5eShit(utils.fixTags(sube["text"],m)))
                                                        text.text = "\n".join(subentries)
                                                    else:
                                                        if type(e) == dict and e["type"] == "list" and "style" in e and e["style"] == "list-hang-notitle":
                                                            for item in e["items"]:
                                                                text = ET.SubElement(subclassOut, 'text')
                                                                text.text = "{}: {}".format(item["name"],utils.remove5eShit(utils.fixTags(item["entry"],m)))
                                                        elif type(e) == dict and e["type"] == "list":
                                                            for item in e["items"]:
                                                                text = ET.SubElement(subclassOut, 'text')
                                                                text.text = "{}".format(utils.remove5eShit(utils.fixTags(item,m)))
                                                        else:
                                                            text = ET.SubElement(subclassOut, 'text')
                                                            text.text = utils.remove5eShit(utils.fixTags(e,m))
