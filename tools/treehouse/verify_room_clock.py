"""Original clock click through completed time announcement."""
import argparse
from pathlib import Path
from verify_room_native_journey import DATA, verify

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(0 if verify(a.html, a.output, DATA/'room-native-journey-c',
        start='cloud-changed', stop='clock', portrait_frame=931) else 1)
