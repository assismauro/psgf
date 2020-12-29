import goslate
import os

import argparse

def ProcessCmdLine():
    parser = argparse.ArgumentParser(description="PrevFogo WebServices.")
    parser.add_argument("-lo", "--locale", help="output locale")
    return parser.parse_args()

if __name__ == '__main__':
    args = ProcessCmdLine()

    gs = goslate.Goslate()

    outputfile = r'translations\{0}\LC_MESSAGES\messages.po'.format(args.locale)

    with open(outputfile) as f:
        output = [line.rstrip() for line in f]

    updated = []

    pair = False
    for line in output:
        if not(line.startswith('msgid') or line.startswith('msgstr')):
            updated.append(line)
        else:
            if pair:
                if line.startswith('msgstr'):
                    msgstr = line.replace('msgstr','').strip()
                    if msgstr.replace('"','') == '':
                        updated.append('msgstr "{0}"'.format(gs.translate(msgid, args.locale)))
                    else:
                        updated.append('msgstr {0}'.format(msgstr))
                pair=False
            if line.startswith('msgid'):
                msgid = line.replace('msgid','').strip()
                pair = True
