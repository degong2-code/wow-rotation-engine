"""Demonstrate tri-state evaluation of selected V11-derived semantic contracts.

This is deliberately not a rotation recommendation application.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .contracts import applicable,validate_catalog

def main():
    parser=argparse.ArgumentParser(description='Evaluate example contract conditions offline')
    parser.add_argument('--context',type=Path,required=True,help='Input combat context JSON')
    args=parser.parse_args()
    errors=validate_catalog()
    if errors:raise SystemExit('Contract validation failed: '+'; '.join(errors))
    context=json.loads(args.context.read_text(encoding='utf8'))
    print(json.dumps(applicable(context),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
