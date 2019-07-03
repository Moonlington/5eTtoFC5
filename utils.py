import re


def ordinal(n): return "%d%s" % (
    n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def parseRIV(m, t):
    lis = []
    for r in m[t]:
        if isinstance(r, dict):
            if 'special' in r:
                lis.append(r['special'])
            elif t in r:
                lis += parseRIV(r, t)
            elif 'resist' in r:
                lis += parseRIV(r, 'resist')
            else:
                lis.append(
                    "{}{}{}".format(
                        r['preNote'] +
                        " " if 'preNote' in r else "",
                        ", ".join(
                            [
                                x for x in r[t]]),
                        " " +
                        r['note'] if 'note' in r else ""))
        else:
            lis.append(r)
    return lis


def remove5eShit(s):
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
    s = re.sub(r'{@\w+ (.*?)(\|.*)?}', r'\1', s)
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
