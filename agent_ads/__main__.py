import argparse
import csv
import os
import sys

from .commands import add_commands, run
from .core import AdServer


def demo():
    s = AdServer()
    s.add(
        "Casa Azul Hotel",
        "Casa Azul Hotel, Alfama - from $140",
        ["hotel_booking"],
        ["lisbon", "hotel", "alfama"],
        2.50,
        50,
        0.8,
        price=140,
    )
    s.add(
        "Grand Ritz",
        "Grand Ritz Lisbon - from $420",
        ["hotel_booking"],
        ["lisbon", "luxury", "hotel"],
        6.00,
        200,
        0.9,
        price=420,
    )
    s.add("CheapFlights", "Flights to anywhere!", ["flight_booking"], ["flights"], 9.00, 500, 0.6)
    s.add(
        "Lisbon Hostel",
        "Lisbon Hostel - from $35",
        ["hotel_booking"],
        ["lisbon", "hostel", "cheap"],
        1.20,
        20,
        0.7,
        price=35,
    )
    res = s.auction(
        "hotel in Lisbon under 200",
        "hotel_booking",
        {"max_price": 200},
        organic=["Memmo Alfama", "Lisbon Hostel - from $35"],
    )
    for w in res["sponsored"]:
        print(f"[{w['label']}] {w['offer']}  (cpc ${w['cpc']}, relevance {w['relevance']})")
    for o in res["organic"]:
        print(f"           {o}")
    print(res["disclosure"])
    s.click(res["sponsored"][0]["impression_id"])
    s.convert(res["sponsored"][0]["impression_id"], 280)
    for row in s.report():
        print(row)


def build_parser():
    ap = argparse.ArgumentParser(prog="agent-ads")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    add_commands(sub)
    return ap


def _run(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.cmd != "demo":
        return run(a)
    demo()
    return 0


def main(argv=None):
    """Run the CLI; a bad input file or argument exits 2 with a one-line error instead of a traceback.

    Set AGENT_ECONOMY_DEBUG=1 to see the full traceback.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    try:
        return _run(argv)
    except (OSError, ValueError, KeyError, csv.Error) as e:
        if os.environ.get("AGENT_ECONOMY_DEBUG"):
            raise
        msg = e.args[0] if isinstance(e, KeyError) and e.args else e
        print(f"error: {msg}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
