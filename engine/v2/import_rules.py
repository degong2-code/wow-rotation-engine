"""Import trusted guide HTML into candidate rules with non-destructive defaults."""
import argparse
import json
from .rules import write_all
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--force',action='store_true',help='Overwrite modified candidate files (explicit destructive re-import)')
    args=p.parse_args()
    print(json.dumps(write_all(overwrite=args.force),ensure_ascii=False,indent=2))
