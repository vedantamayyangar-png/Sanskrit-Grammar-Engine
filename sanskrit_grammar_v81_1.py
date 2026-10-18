#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public v8.1 entry point for the Sanskrit grammar pipeline.

Machine-facing JSON keys remain stable for programmatic compatibility.
All human-visible labels are emitted in Sanskrit under labels_sa structures.
"""
import argparse, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description='संस्कृत-व्याकरण १०+१-अङ्ग-सञ्चिका v8.1')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('validate',help='JSON-प्रमाणीकरणम्'); a.add_argument('json_file')
    u=sub.add_parser('upgrade',help='पुरातन-सञ्चिकायाः v8.1 रूपे परिवर्तनम्'); u.add_argument('json_file'); u.add_argument('output_file')
    a=sub.add_parser('audit',help='गुणवत्ता-परीक्षणम्'); a.add_argument('json_file')
    args=p.parse_args()
    if args.cmd=='validate':
        return subprocess.call([sys.executable,str(HERE/'validate_grammar_v81.py'),args.json_file])
    if args.cmd=='upgrade':
        return subprocess.call([sys.executable,str(HERE/'upgrade_grammar_json_v81.py'),args.json_file,args.output_file])
    if args.cmd=='audit':
        return subprocess.call([sys.executable,str(HERE/'validate_grammar_v81.py'),args.json_file])
if __name__=='__main__': sys.exit(main())
