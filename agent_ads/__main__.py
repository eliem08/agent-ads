import argparse
import sys

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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="agent-ads")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    ap.parse_args(argv)
    demo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
