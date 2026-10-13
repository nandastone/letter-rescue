"""Compare the earned plane prize through ordinary drag and release inputs."""
from pathlib import Path
import argparse
from verify_room_native_journey import verify, DATA

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if verify(a.html,a.output,DATA/"plane-native-journey-a") else 1)
