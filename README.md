# 5eTtoFC5

**5eTtoFC5** is a script for converting 5eTools monsters to Lion's Den Fight Club 5 compatible xml files. The usage is explained like this:

```bash
$ ./python convert.py --help
usage: convert.py [-h] [--ignore] [-v] [-o COMBINEDOUTPUT]
                  inputJSON [inputJSON ...]

Converts 5eTools json files to FC5 compatible XML files.

positional arguments:
  inputJSON          5eTools inputs

optional arguments:
  -h, --help         show this help message and exit
  --ignore           ignores errors (default: false)
  -v                 verbose output (default: false)
  -o COMBINEDOUTPUT  combines inputs into given output (default: false)
```

## Example

```bash
$ ./python convert.py -o "output.xml" "monstermanual.json" "volosguide.json"
Done converting monstermanual
Done converting volosguide
Converted 456 monsters
```

## Version

* Version 1.0

## Contact

### Developer

* Discord: **Flore#0001**
