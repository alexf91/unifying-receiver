#!/usr/bin/env python

import sys

if __name__ == '__main__':
    inpath  = sys.argv[1]
    outpath = sys.argv[2]

    infile  = open(inpath, 'rb')
    outfile = open(outpath, 'w')

    for b in infile.read():
        outfile.write(str(b))

    infile.close()
    outfile.close()
