# vim: set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab : #
import re
import math
import copy
import json
from slugify import slugify

def ordinal(n): return "%d%s" % (
    n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def parseRIV(m, t):
    lis = []
    for r in m[t]:    
        if isinstance(r, dict):
            if 'special' in r:
                lis.append(r['special'])
#            elif t in r:
#                lis += parseRIV(r, t)
#            elif 'resist' in r:
#                lis += parseRIV(r, 'resist')
            else:
                riv = []
                for x in r[t]:
                    if isinstance(x, dict) and t in x:
                        if len(riv) > 0:
                            riv[-1] += "; {}{}{}".format(
                                x['preNote'] +
                                " " if 'preNote' in x else "",
                                ", ".join(parseRIV(x, t)),
                                " " +
                                x['note'] if 'note' in x else "")
                        else:
                            riv.append(
                            "{}{}{}".format(
                                x['preNote'] +
                                " " if 'preNote' in x else "",
                                ", ".join(parseRIV(x, t)),
                                " " +
                                x['note'] if 'note' in x else ""))
                    else:
                        riv.append(x)
                if len(lis) > 0:
                    lis[-1] += "; {}{}{}".format(
                            r['preNote'] +
                            " " if 'preNote' in r else "",
                            ", ".join(riv),
                            " " +
                            r['note'] if 'note' in r else "")

                else:
                    lis.append(
                        "{}{}{}".format(
                            r['preNote'] +
                            " " if 'preNote' in r else "",
                            ", ".join(riv),
                            " " +
                            r['note'] if 'note' in r else ""))
        else:
            lis.append(r)
    return lis


def remove5eShit(s):
    if type(s) == int or type(s) == float:
        return str(s)
    s = re.sub(r'{@dc (.*?)}', r'DC \1', s)
    s = re.sub(r'{@hit \+?(.*?)}', r'+\1', s)
    s = re.sub(r'{@atk mw}', r'Melee Weapon Attack:', s)
    s = re.sub(r'{@atk rw}', r'Ranged Weapon Attack:', s)
    s = re.sub(r'{@atk ms}', r'Melee Spell Attack:', s)
    s = re.sub(r'{@atk rs}', r'Ranged Spell Attack:', s)
    s = re.sub(r'{@atk mw,rw}', r'Melee or Ranged Weapon Attack:', s)
    s = re.sub(r'{@atk r}', r'Ranged Attack:', s)
    s = re.sub(r'{@atk m}', r'Melee Attack:', s)
    s = re.sub(r'{@h}', r'', s)
    s = re.sub(r'{@recharge (.*?)}', r'(Recharge \1-6)', s)
    s = re.sub(r'{@recharge}', r'(Recharge 6)', s)
    s = re.sub(r'{@dice (.*?)(\|.*?)}', r'\1', s)
    s = re.sub(r'{@scaledice (.*?)\|(.*?)\|(.*?)}', r'\3', s)
    s = re.sub(r'{@scaledamage (.*?)\|(.*?)\|(.*?)}', r'\3', s)
    s = re.sub(r'{@table (.*?)\|(.*?)\|(.*?)}', r'\3', s)
    s = re.sub(r'{@filter (.*?)(\|.*?)?}', r'\1', s)
    s = re.sub(r'{@\w+ ([^{]*?)(\|[^{]*?)?}', r'\1', s)
    s = re.sub(r'{@\w+ ((.*?|{.*?})?)(\|(.*?|{.*?})?)?}', r'\1', s)
    return s.strip()


def indent(elem, level=0):
    i = "\n" + level * "  "
    j = "\n" + (level - 1) * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


def convertSize(s):
    return {
        'T': "Tiny",
        'S': "Small",
        'M': "Medium",
        'L': "Large",
        'H': "Huge",
        'G': "Gargantuan",
    }[s]


def convertAlign(s):
    if isinstance(s, dict):
        if 'special' in s:
            return s['special']
        else:
            if 'chance' in s:
                return " ".join(
                    [convertAlign(x) for x in s['alignment']]) + " ({}%)".format(s['chance'])
            return " ".join([convertAlign(x) for x in s['alignment']])
    else:
        alignment = s.upper()
        return {"L": "Lawful",
                "N": "Neutral",
                "NX": "Neutral (Law/Chaos axis)",
                "NY": "Neutral (Good/Evil axis)",
                "C": "Chaotic",
                "G": "Good",
                "E": "Evil",
                "U": "Unaligned",
                "A": "Any alignment",
                }[alignment]


def convertAlignList(s):
    if len(s) == 1:
        return convertAlign(s[0])
    elif len(s) == 2:
        return " ".join([convertAlign(x) for x in s])
    elif len(s) == 3:
        if "NX" in s and "NY" in s and "N" in s:
            return "Any Neutral Alignment"
    elif len(s) == 5:
        if "G" not in s:
            return "Any Non-Good Alignment"
        elif "E" not in s:
            return "Any Non-Evil Alignment"
        elif "L" not in s:
            return "Any Non-Lawful Alignment"
        elif "C" not in s:
            return "Any Non-Chaotic Alignment"
    elif len(s) == 4:
        if "L" not in s and "NX" not in s:
            return "Any Chaotic Alignment"
        if "G" not in s and "NY" not in s:
            return "Any Evil Alignment"
        if "C" not in s and "NX" not in s:
            return "Any Lawful Alignment"
        if "E" not in s and "NY" not in s:
            return "Any Good Alignment"

def modifyMonster(m,mods):
    for mod in mods:
        if mod == '*':
            if mods[mod]["mode"] == "replaceTxt":
                mr = mods[mod]["replace"]
                mw = mods[mod]["with"]
                mf = ""
                if "flags" in mods[mod]:
                    mf = mods[mod]["flags"]
                m = modRepl(m,mr,mw,mf)
        elif mod == 'trait' or mod == 'action' or mod == 'reaction' or mod == 'legendary':
            if mod not in m:
                m[mod] = []
        elif mod == 'spellcasting' or mod == 'languages' or mod == 'resist' or mod == "variant" or mod == "immune" or mod == "conditionImmune" or mod == "vulnerable":
            if mod not in m:
                m[mod] = []
            m[mod] = modList(m[mod],mods[mod])
        elif mod == "hp":
            if mods[mod]["mode"] == "scalarMultProp":
                if mods[mod]["floor"]:
                    m["hp"][mods[mod]["prop"]] = math.floor(m["hp"][mods[mod]["prop"]] * mods[mod]["scalar"])
                else:
                    m["hp"][mods[mod]["prop"]] = round(m["hp"][mods[mod]["prop"]] * mods[mod]["scalar"])
            else:
                print("Unhandled HP mode:", mods[mod]["mode"])
        elif mod == 'skill' or mod == 'save':
            if mod not in m:
                continue
            if mods[mod]["mode"] == "scalarAddProp":
                if mods[mod]["prop"] == "*":
                    for s in m[mod]:
                        m[mod][s] = "{:+d}".format(int(m[mod][s])+mods[mod]["scalar"])
                else:
                    m[mod][mods[mod]["prop"]] = "{:+d}".format(int(m[mod][mods[mod]["prop"]])+mods[mod]["scalar"])
            else:
                print("Unhandled " + mod + " mode:", mods[mod]["mode"])
        elif mod == '_':
            mod_s = []
            if type(mods[mod]) == list:
                mod_s.extend(mods[mod])
            else:
                mod_s.append(mods[mod])
            for ms in mod_s:
                if ms["mode"] == "addSenses":
                    if 'senses' not in m:
                        m["senses"] = []
                    if type(ms["senses"]) == list:
                        for i in range(len(ms["senses"])):
                            m["senses"].append("{} {} ft.".format(ms["senses"][i]["type"],ms["senses"][i]["range"]))
                    else:
                        m["senses"].append("{} {} ft.".format(ms["senses"]["type"],ms["senses"]["range"]))
                elif ms["mode"] == "scalarMultXp":
                    m["cr"] = multiCR(m["cr"],ms["scalar"])
                elif ms["mode"] == "maxSize":
                    sizes = [ 'T', 'S', 'M', 'L', 'H', 'G' ]
                    if sizes.index(ms["max"]) < sizes.index(m["size"]):
                        m["size"] = ms["max"]
                elif ms["mode"] == "addSkills":
                    if 'skill' not in m:
                        m["skill"] = {}
                    for skill in ms["skills"]:
                        m["skill"][skill] = '{:+d}'.format(ms["skills"][skill])
                elif ms["mode"] == "addSpells":
                    if "spells" in ms:
                        for slevel in ms["spells"]:
                            if slevel not in m["spellcasting"][0]["spells"]:
                                m["spellcasting"][0]["spells"][slevel] = { "spells": [] }
                            for spell in ms["spells"][slevel]["spells"]:
                                if spell not in m["spellcasting"][0]["spells"][slevel]["spells"]:
                                    m["spellcasting"][0]["spells"][slevel]["spells"].append(spell)
                    else:
                        if "will" in ms:
                            spell_type = "will"
                            for spell in ms[spell_type]:
                                if spell not in m["spellcasting"][0][spell_type]:
                                    m["spellcasting"][0][spell_type].append(spell)
                        else:
                            spell_type = "daily"
                            for slevel in ms[spell_type]:
                                for spell in ms[spell_type][slevel]:
                                    if spell not in m["spellcasting"][0][spell_type][slevel]:
                                        m["spellcasting"][0][spell_type][slevel].append(spell)
                elif ms["mode"] == "replaceSpells":
                    if "spells" in ms:
                        for slevel in ms["spells"]:
                            for spell in ms["spells"][slevel]:
                                if spell["replace"] not in m["spellcasting"][0]["spells"][slevel]["spells"]:
                                    m["spellcasting"][0]["spells"][slevel]["spells"].append(spell["with"])
                                else:
                                    for i in range(len(m["spellcasting"][0]["spells"][slevel]["spells"])):
                                        if m["spellcasting"][0]["spells"][slevel]["spells"][i] == spell["replace"]:
                                            m["spellcasting"][0]["spells"][slevel]["spells"][i] = spell["with"]
                    else:
                        if "will" in ms:
                            spell_type = "will"
                            for spell in ms[spell_type]:
                                if spell["replace"] not in m["spellcasting"][0][spell_type]:
                                    m["spellcasting"][0][spell_type].append(spell["with"])
                                else:
                                    for i in range(len(m["spellcasting"][0][spell_type])):
                                        if m["spellcasting"][0][spell_type][i] == spell["replace"]:
                                            m["spellcasting"][0][spell_type][i] == spell["with"]

                        else:
                            spell_type = "daily"
                            for slevel in ms[spell_type]:
                                for spell in ms[spell_type][slevel]:
                                    if spell["replace"] not in m["spellcasting"][0][spell_type][slevel]:
                                        m["spellcasting"][0][spell_type][slevel].append(spell["with"])
                                    else:
                                        for i in range(len(m["spellcasting"][0][spell_type][slevel])):
                                            if m["spellcasting"][0][spell_type][slevel][i] == spell["replace"]:
                                                m["spellcasting"][0][spell_type][slevel][i] == spell["with"]
                else:
                    print("Unhandled _ mod: " + ms["mode"])
                    print(m["name"],m["source"])
        else:
            print("Unhandled mod: " + mod)
            print(m["name"],m["source"])
    return m

def modifyItem(m,mods):
    for mod in mods:
        if mod == 'entries':
            if mod not in m:
                m[mod] = []
            m[mod] = modList(m[mod],mods[mod])
        else:
            print("Unhandled mod: " + mod)
    return m

def modTraits(trait,mod):
    print(trait,mod)
    if type(mod) == list:
        for mt in range(len(mod)):
            trait = modTraits(trait,mod[mt])
    else:
        if mod == "remove":
            del trait[:]
        elif mod['mode'] == "prependArr":
            if type(mod['items']) == list:
                for item in reversed(mod['items']):
                    trait.insert(0,item)
            else:
                trait.insert(0,mod['items'])
        elif mod['mode'] == "insertArr":
            trait.insert(mod['index'],mod['items'])
        elif mod['mode'] == "appendArr":
            if type(mod['items']) == list:
                trait.extend(mod['items'])
            else:
                trait.append(mod['items'])
        elif mod['mode'] == "replaceOrAppendArr" or mod['mode'] == "replaceArr":
            for t in range(len(trait)):
                if trait[t]['name'] == mod['replace']:
                    del trait[t]
                    if type(mod["items"]) == list:
                        for item in mod["items"]:
                            trait.insert(t,item)
                    else:
                        trait.insert(t,mod["items"])
                    break
        elif mod['mode'] == "removeArr":
            trait = [ t for t in trait if t['name'] not in mod['names'] ]
        elif mod['mode'] == 'replaceTxt':
            for t in trait:
                f = ""
                if "flags" in mod:
                    f = mod["with"]
                t["entries"] = modRepl(t["entries"],mod["replace"],mod["with"],f)
        elif mod['mode'] == 'scalarAddHit':
            for t in range(len(trait)):
                for i in range(len(trait[t]["entries"])):
                    for match in re.finditer(r'{@hit ([-+0-9]*)}',trait[t]["entries"][i]):
                        toHit = int(match.group(1)) + mod['scalar']
                        trait[t]["entries"][i] = modRepl(trait[t]["entries"][i],match.group(0),"{{@hit {:+d}}}".format(toHit),"")
        elif mod['mode'] == 'scalarAddDc':
            for t in range(len(trait)):
                for i in range(len(trait[t]["entries"])):
                    for match in re.finditer(r'{@dc ([-+0-9]*)}',trait[t]["entries"][i]):
                        dc = int(match.group(1)) + mod['scalar']
                        trait[t]["entries"][i] = modRepl(trait[t]["entries"][i],match.group(0),"{{@dc {:d}}}".format(dc),"")
        else:
            print("Unhandled tmode: " + mod['mode'],mod)
    return trait

def modList(items,mod):
    if type(mod) == list:
        for mt in range(len(mod)):
            items = modList(items,mod[mt])
    else:
        if mod == "remove":
            del items[:]
        elif mod['mode'] == "appendArr":
            if type(mod["items"]) == list:
                items.extend(mod["items"])
            else:
                items.append(mod['items'])
        elif mod['mode'] == "replaceOrAppendArr" or mod['mode'] == "replaceArr":
            for i in range(len(items)):
                if 'name' in items[i] and items[i]['name'] == mod['replace']:
                    del items[i]
                    if type(mod["items"]) == list:
                        for item in mod["items"]:
                            items.insert(i,item)
                    else:
                        items.insert(i,mod["items"])
                    break
        elif mod['mode'] == "removeArr":
            if 'names' in mod:
                items = [ item for item in items if item not in mod['names'] ]
            elif 'items' in mod:
                items = [ item for item in items if item not in mod['items'] ]
            else:
                print("Unhandled mode: " + mod['mode'],mod)
        elif mod['mode'] == 'insertArr':
            if type(mod['items']) == list:
                for item in reversed(mod['items']):
                    items.insert(mod['index'],item)
            else:
                items.insert(mod['index'],mod['items'])
        elif mod['mode'] == 'scalarAddHit':
            for i in range(len(items)):
                if type(items[i]) == dict and "entries" in items[i]:
                    for e in range(len(items[i]["entries"])):
                        if type(items[i]["entries"][e]) == dict and "entries" in items[i]["entries"][e]:
                            for e2 in range(len(items[i]["entries"][e]["entries"])):
                                for match in re.finditer(r'{@hit ([-+0-9]*)}',items[i]["entries"][e]["entries"][e2]):
                                    toHit = int(match.group(1)) + mod['scalar']
                                    items[i]["entries"][e]["entries"][e2] = modRepl(items[i]["entries"][e]["entries"][e2],match.group(0),"{{@hit {:+d}}}".format(toHit),"")
                        else:
                            for match in re.finditer(r'{@hit ([-+0-9]*)}',items[i]["entries"][e]):
                                toHit = int(match.group(1)) + mod['scalar']
                                items[i]["entries"][e] = modRepl(items[i]["entries"][e],match.group(0),"{{@hit {:+d}}}".format(toHit),"")
                elif type(items[i]) == dict and "headerEntries" in items[i]:
                    for e in range(len(items[i]["headerEntries"])):
                        for match in re.finditer(r'{@hit ([-+0-9]*)}',items[i]["headerEntries"][e]):
                            toHit = int(match.group(1)) + mod['scalar']
                            items[i]["headerEntries"][e] = modRepl(items[i]["headerEntries"][e],match.group(0),"{{@hit {:+d}}}".format(toHit),"")
                else:
                    for match in re.finditer(r'{@hit ([-+0-9]*)}',items[i]):
                        toHit = int(match.group(1)) + mod['scalar']
                        items[i] = modRepl(items[i],match.group(0),"{{@hit {:+d}}}".format(toHit),"")
        elif mod['mode'] == 'scalarAddDc':
            for i in range(len(items)):
                if type(items[i]) == dict and "entries" in items[i]:
                    for e in range(len(items[i]["entries"])):
                        if type(items[i]["entries"][e]) == dict and "entries" in items[i]["entries"][e]:
                            for e2 in range(len(items[i]["entries"][e]["entries"])):
                                for match in re.finditer(r'{@dc ([-+0-9]*)}',items[i]["entries"][e]["entries"][e2]):
                                    dc = int(match.group(1)) + mod['scalar']
                                    items[i]["entries"][e]["entries"][e2] = modRepl(items[i]["entries"][e]["entries"][e2],match.group(0),"{{@dc {:+d}}}".format(dc),"")
                        else:
                            for match in re.finditer(r'{@dc ([-+0-9]*)}',items[i]["entries"][e]):
                                dc = int(match.group(1)) + mod['scalar']
                                items[i]["entries"][e] = modRepl(items[i]["entries"][e],match.group(0),"{{@dc {:d}}}".format(dc),"")
                elif type(items[i]) == dict and "headerEntries" in items[i]:
                    for e in range(len(items[i]["headerEntries"])):
                        for match in re.finditer(r'{@dc ([-+0-9]*)}',items[i]["headerEntries"][e]):
                            dc = int(match.group(1)) + mod['scalar']
                            items[i]["headerEntries"][e] = modRepl(items[i]["headerEntries"][e],match.group(0),"{{@dc {:d}}}".format(dc),"")
                else:
                    for match in re.finditer(r'{@dc ([-+0-9]*)}',items[i]):
                        dc = int(match.group(1)) + mod['scalar']
                        items[i] = modRepl(items[i],match.group(0),"{{@dc {:d}}}".format(dc),"")
        else:
            print("Unhandled mode: " + mod['mode'],mod)
    return items

def modRepl(s,r,w,f):
    if type(s) == str:
        if "i" in f:
            repl = re.compile(r,re.IGNORECASE)
        else:
            repl = re.compile(r)
        s = repl.sub(w,s)
    elif type(s) == list:
        for i in range(len(s)):
            s[i] = modRepl(s[i],r,w,f)
    elif type(s) == dict:
        for i in s:
            s[i] = modRepl(s[i],r,w,f)
    return s

def fixTags(s,m,nohtml=False):
    if '×' in s:
        s=s.replace('×','x')
    if '{=' in s:
        def propRepl(matchobj):
            if matchobj.group(1) in m:
                flags = matchobj.group(2)
                repl = m[matchobj.group(1)]
                if not flags == None:
                    if 'a' in flags:
                        if repl[0].lower() in 'aeiou':
                            repl = 'an'
                        else:
                            repl = 'a'
                    if 'l' in flags:
                        repl = repl.lower()
                    if 't' in flags:
                        repl = repl.title()
                return repl
            else:
                return matchobj.group(1)
        s = re.sub(r'{=(.*?)([/].*?)?}', propRepl, s)
    if not nohtml:
        s = re.sub(r'{@([bi]) (.*?)}',r'<\1>\2</\1>', s)
        s = re.sub(r'{@italic (.*?)}',r'<i>\1</i>', s)
        s = re.sub(r'{@spell (.*?)}', r'<spell>\1</spell>', s)
        s = re.sub(r'{@link (.*?)\|(.*?)?}', r'<a href="\2">\1</a>', s)
        def createMLink(matchobj):
            return "<a href=\"/monster/{}\">{}</a>".format(slugify(matchobj.group(1)),matchobj.group(2))
        s = re.sub(r'{@creature (.*?)\|\|(.*?)?}', createMLink, s)
        s = re.sub(r'{@creature (.*?)}', r'<monster>\1</monster>', s)
        s = re.sub(r'{@item (.*?)(\|.*?)?}', r'<item>\1</item>', s)
    else:
        s = re.sub(r'{@link (.*?)\|(.*?)?}', r'\1 (\2)', s)

    if '{@' in s:
        s = remove5eShit(s)

    if '<$' not in s:
        return s

    name = m['name']
    if 'isNpc' in m and m['isNpc']:
        nameparts = name.split(" ")
        name = nameparts[0]
    s = re.sub(re.escape('<$title_name$>'), name, s)
    s = re.sub(re.escape('<$short_name$>'), name, s)
    s = re.sub(re.escape('<$damage_avg__2.5+str$>'), "{:d}".format(math.floor(2.5+getAbilityMod(m["str"]))), s)
    s = re.sub(re.escape('<$damage_mod__str$>'), " {:+d}".format(getAbilityMod(m["str"])) if getAbilityMod(m["str"]) != 0 else "", s)
    s = re.sub(re.escape('<$spell_dc__cha$>'), "{:d}".format(8+crToP(m["cr"])+getAbilityMod(m["cha"])), s)
    s = re.sub(re.escape('<$to_hit__str$>'), "{:+d}".format(crToP(m["cr"])+getAbilityMod(m["str"])), s)

    if re.search(r'{[@=](.*?)}',s):
        s = fixTags(s,m)

    return s

def crToP(cr):
    if "/" in cr:
        fraction = list(map(float,cr.split("/",2)))
        cr = fraction[0]/fraction[1]
    else:
        cr = float(cr)
    return math.ceil(1+cr/4)

def getAbilityMod(score):
    return math.floor((float(score)-10)/2)

def multiCR(cr,scale):
    if type(cr) == dict:
        for k in cr:
            cr[k] = multiCR(cr[k],scale)
    else:
        if "/" in cr:
            fraction = list(map(float,cr.split("/",2)))
            cr = fraction[0]/fraction[1]
        else:
            cr = float(cr)
        cr = cr * scale
        if cr < 0.125:
            cr = "0"
        elif cr < 0.25:
            cr = "1/8"
        elif cr < 0.5:
            cr = "1/4"
        elif cr < 1:
            cr = "1/2"
        else:
            cr = '{:.0f}'.format(cr)
    return cr

def appendFluff(fluff,m,t='monster',nohtml=False):
    entries = []
    for f in fluff[t]:
        if f['name'] == m:
            if 'entries' in f:
                for e in f['entries']:
                    if type(e) == dict and 'entries' in e and any('entries' in se for se in e['entries']):
                        for se in e['entries']:
                            if type(se) == dict and 'entries' in se:
                                if 'name' in se:
                                    if nohtml:
                                        entries.append("{}".format(se['name']))
                                    else:
                                        entries.append("<b>{}</b>".format(se['name']))
                                entries += (se['entries'])
                    else:
                        entries.append(e)
            elif "_copy" in f:
                entries = appendFluff(fluff,f['_copy']['name'])
            if "_appendCopy" in f:
                entries = entries + appendFluff(fluff,f['_appendCopy']['name'])
    return entries

def findFluffImage(fluff,m,t='monster'):
    for f in fluff[t]:
        if f['name'] == m:
            if 'images' in f:
                for image in f['images']:
                    if 'href' in image and 'path' in image['href']:
                        return image['href']['path']
            elif "_copy" in f:
                return findFluffImage(fluff,(f['_copy']['name']))
    return None


def getFriendlySource(source):
    friendly = source
    allbooks = [ "./data/books.json", "./data/adventures.json" ]
    srcfound = True
    if source == "TftYP":
        friendly = "Tales from the Yawning Portal"
    elif source == "PSA":
        friendly = "Plane Shift: Amonkhet"
    elif source == "PSD":
        friendly = "Plane Shift: Dominaria"
    elif source == "PSI":
        friendly = "Plane Shift: Innistrad"
    elif source == "PSK":
        friendly = "Plane Shift: Kaladesh"
    elif source == "PSX":
        friendly = "Plane Shift: Ixalan"
    elif source == "PSZ":
        friendly = "Plane Shift: Zendikar"
    elif source == "Mag":
        friendly = "Dragon Magazine"
    elif source == "MFF":
        friendly = "Mordenkainen’s Fiendish Folio"
    elif source == "Stream":
        friendly = "Livestream"
    elif source == "EEPC":
        friendly = "Elemental Evil Player's Companion"
    elif source == "RoTOS":
        friendly = "The Rise of Tiamat Online Supplement"
    elif source == "EET":
        friendly = "Elemental Evil: Trinkets"
    elif source == "UAWGE":
        friendly = "Wayfinder's Guide to Eberron"
    elif source == "SADS":
        friendly = "Sapphire Anniversary Dice Set"
    elif source == "AWM":
        friendly = "Adventure with Muk"
    elif source == "OGA":
        friendly = "One Grung Above"
    elif source == "Twitter":
        friendly = "Twitter"
    elif source.startswith("UA"):
        friendly = re.sub(r"(\w)([A-Z])", r"\1 \2", friendly)
        friendly = re.sub(r"U A", r"Unearthed Arcana: ", friendly)
    elif source.startswith("AL"):
        friendly = re.sub(r"(\w)([A-Z])", r"\1 \2", friendly)
        friendly = re.sub(r"A L", r"Adventurers League: ", friendly)
    else:
        srcfound = False
    for books in allbooks:
        if srcfound:
            break
        try:
            with open(books,encoding='utf-8') as f:
                bks = json.load(f)
                f.close()
            key = list(bks.keys())[0]
            for bk in bks[key]:
                if bk['source'] == source:
                    friendly = bk['name']
                    srcfound = True
                    break
        except IOError as e:
            print ("Could not determine source friendly names ({}): {}".format(e.errno, e.strerror))
    if not srcfound:
        print("Could not find source: " + source)
    return friendly
