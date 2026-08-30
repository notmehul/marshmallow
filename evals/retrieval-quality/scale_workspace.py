#!/usr/bin/env python3
"""Deterministic seeded scaler: grow near-miss distractor tiers from the seed.

Mechanism (design doc, "Scaler" section): the seed workspace is copied
byte-identical, then whole parallel universes of 100 nodes each are cloned
from it. Clones keep structural vocabulary (piers, gates, vendors, berths,
overtime protocols) and re-coin entity names with partial token overlap:
shared first names, shared project-prefix shapes (P9-GATE becomes P14-GATE),
vendor-family names (Turnstile Dynamics becomes Turnbuckle Dynamics). Every
planted-fact anchor from bible.md is mutated systematically (dates shift by
whole weeks, quantities and spec codes change, anchor phrases are re-worded
with overlapping tokens) so clones attract lexical retrieval but can never
contain a labeled fact. Generation fails loudly if any anchor survives in a
clone or if the output workspace has doctor errors or quality warnings.

Same --rng-seed and seed workspace produce a byte-identical output tree:
all randomness flows through one random.Random(rng_seed) and every directory
listing is sorted.
"""

from __future__ import annotations

import argparse
import datetime
import random
import re
import shutil
import sys
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from markdown_graph import ID_PATTERN, graph_quality_warnings, validate_workspace  # noqa: E402

SEED_NODE_COUNT = 100
CLONE_DIRS = ("raw", "sources", "graph", "indexes", "projections")
WHITESPACE = re.compile(r"\s+")
FACT_ROW = re.compile(r"^\|\s*\*\*F\d{2}\*\*\s*\|")
BACKTICKED = re.compile(r"`([^`]+)`")
ISO_DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
TIME_OF_DAY = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b")
BARE_YEAR = re.compile(r"(?<!\d)2026(?!\d)")
MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)
MONTH_ABBREVS = {name[:3]: index for index, name in enumerate(MONTHS, start=1)}
MONTH_ABBREVS["sept"] = 9
MONTH_DAY = re.compile(
    r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True) + list(MONTH_ABBREVS)) + r") (\d{1,2})\b",
    re.IGNORECASE,
)

# People: (first name, seed surname, replace the bare surname too?). Bare
# replacement is off where the surname is also an English/domain word the
# seed uses in other senses (Crane the person vs the drydock crane).
PEOPLE = (
    ("Juno", "Castillo", True),
    ("Elena", "Vasquez", True),
    ("Elena", "Crane", False),
    ("Marcus", "Holt", True),
    ("Priya", "Nandakumar", True),
    ("Derek", "Blunt", False),
    ("Fatima", "Okonkwo", True),
    ("Glenn", "Wexler", True),
    ("Hana", "Suzuki", True),
    ("Victor", "Hale", False),
    ("Victor", "Dunn", True),
    ("Cal", "Donner", True),
    ("Jessamine", "Lee", False),
)

# One line word per universe; its lowercase form is the universe id suffix.
LINE_WORDS = (
    "Crest", "Mist", "Fog", "Wake", "Swell", "Drift", "Moor", "Quay", "Cove",
    "Reef", "Shoal", "Breaker", "Beacon", "Lantern", "Compass", "Fathom",
    "Keel", "Rudder", "Mast", "Bowline", "Marlin", "Tarpon", "Skiff", "Sloop",
    "Ketch", "Yawl", "Dory", "Clipper", "Schooner", "Brine", "Kelp", "Coral",
    "Pearl", "Ebb", "Squall", "Tempest", "Zephyr", "Boreal", "Austral",
    "Meridian", "Latitude", "Sound", "Strait", "Channel", "Inlet", "Lagoon",
    "Estuary", "Delta", "Basin", "Jetty", "Bollard", "Windrose", "Halcyon",
    "Norther", "Wester", "Easter",
)
SURNAMES = (
    "Aldana", "Beckett", "Cormier", "Delgado", "Espinoza", "Farrow",
    "Gallardo", "Herrera", "Ibarra", "Jansen", "Keating", "Lombardi",
    "Maddox", "Navarro", "Ochoa", "Pemberton", "Quintero", "Rowan",
    "Santiago", "Trevino", "Ellison", "Vartan", "Whitaker", "Yoshida",
    "Zamora", "Ashworth", "Barlow", "Calloway", "Draper", "Emerson",
)
VESSELS = (
    ("Cormorant", "CM"), ("Petrel", "PT"), ("Kittiwake", "KW"),
    ("Guillemot", "GM"), ("Sandpiper", "SP"), ("Fulmar", "FM"),
    ("Gannet", "GN"), ("Skua", "SK"), ("Puffin", "PF"), ("Avocet", "AV"),
    ("Dunlin", "DL"), ("Whimbrel", "WB"), ("Curlew", "CW"), ("Godwit", "GW"),
    ("Plover", "PV"), ("Merganser", "MG"), ("Grebe", "GB"), ("Bittern", "BT"),
)
PASSES = (
    ("Tide", "TP"), ("Dock", "DP"), ("Gull", "GP"), ("Wharf", "WP"),
    ("Ferry", "FP"), ("Ripple", "RP"), ("Current", "CP"), ("Marina", "MP"),
    ("Voyage", "VP"), ("Nautic", "NP"),
)
SURGES = (
    ("King", "KSB"), ("Flood", "FSB"), ("Gale", "GSB"), ("Peak", "PSB"),
    ("Crown", "CSB"), ("Bore", "BSB"), ("Rogue", "RSB"), ("Lunar", "LSB"),
)
CODENAMES = (
    "Kingtide", "Riptide", "Undertow", "Overfall", "Tidewrack", "Seastack",
    "Longshore", "Backwash", "Saltmark", "Foamline",
)
CONDOS = (
    "Dunecrest", "Seacliff", "Bayview", "Shorewind", "Saltmeadow",
    "Tidewater", "Wavecrest", "Sandpoint", "Gullwing", "Beachrow",
)
GATE_VENDORS = (
    "Turnbuckle", "Fairlead", "Windlass", "Davit", "Gantry", "Bulwark",
    "Halyard", "Lanyard", "Grommet", "Ratchet",
)
HOIST_VENDORS = (
    "Spanway", "Archway", "Causeway", "Trestleway", "Deckway", "Slipway",
    "Crossway", "Beamway", "Girderway", "Trussway",
)
MARINE_VENDORS = (
    "Kelbourne", "Kelsworth", "Kelford", "Kelmont", "Kelhaven", "Kelvane",
    "Kelbray", "Kelmore", "Keldon", "Kelstrand",
)
READINESS_WORDS = (
    "Dockside", "Quayside", "Wharfside", "Berthside", "Slipside", "Pierside",
    "Shoreside", "Deckside", "Portside", "Baywide",
)
HARBOR_ROUTES = (
    "Heron", "Osprey", "Falcon", "Pelican", "Seal", "Otter", "Orca",
    "Minke", "Sable", "Cedar",
)
ALLOYS = (
    ("5083", "5083-H116"), ("5052", "5052-H32"), ("7075", "7075-T651"),
    ("6082", "6082-T651"), ("5456", "5456-H117"), ("3003", "3003-H14"),
)
GANG_HOSES = ("100R5", "100R13", "100R16", "100R4")
GATE_HOSES = ("100R7", "100R3", "100R6", "100R17")
# 14 is excluded: "Pier 9 contractor badges" must never become
# "pier 14 contractor badges" (a planted-fact anchor).
PIER_NUMBERS = tuple(n for n in (2, 4, 6, 8, *range(10, 40)) if n != 14)
LANES = (("3", "three"), ("5", "five"), ("6", "six"), ("7", "seven"))
DECKHAND_SOURCES = (6, 7, 8)  # edited value is source - 1; both avoid 3 and 4
BADGE_COUNTS = (9, 11, 12, 13, 16, 17, 19, 21)
VEST_MINUTES = (25, 30, 35, 40, 50)
GANGWAY_WIDTHS = ("2.1", "2.8", "2.9", "3.1", "3.4", "3.6")
CHANGE_ORDER_CAPS = (15900, 17600, 21700, 24300, 26800)
CONTINGENCY_AMOUNTS = (39000, 48000, 55000, 71000, 83000)
MOBILIZATION_FEES = (39400, 45800, 48200, 52600)
DISCOUNT_PERCENTS = (8, 9, 14, 15, 18)

# Anchor-phrase mutations shared by every universe. Each entry breaks a
# planted-fact anchor phrase while keeping most of its tokens, which is what
# makes clones near-miss distractors instead of copies.
STATIC_REPLACEMENTS = (
    ("labels: [seed]", "labels: [distractor]"),
    ("single-contractor", "sole-contractor"),
    ("single contractor", "sole contractor"),
    ("scope divergence", "scope split"),
    ("float switch", "float sensor"),
    ("dive inspections", "dive surveys"),
    ("dive inspection", "dive survey"),
    ("thrust bearing", "shaft bearing"),
    ("hull penetration", "hull cut-in"),
    ("spot checks", "spot inspections"),
    ("spot check", "spot inspection"),
    ("simulation weekends", "rehearsal weekends"),
    ("simulation weekend", "rehearsal weekend"),
    ("manually edited", "hand edited"),
    ("coverage matrix", "duty matrix"),
    ("source notes", "field notes"),
    ("aluminum grating", "alloy grating"),
    ("commuter rush", "commuter peak"),
    ("order cap", "order ceiling"),
    ("mock-ups", "mockups"),
    ("mock-up", "mockup"),
    ("gangway width", "gangway span"),
    ("gate delivery", "gate shipment"),
    ("gangway delivery", "gangway shipment"),
    ("passenger notices", "passenger advisories"),
    ("passenger notice", "passenger advisory"),
    ("rollback token", "rollback key"),
    ("unauthorized vehicle", "unbadged vehicle"),
    ("temporary badges", "temp badges"),
    ("temporary badge", "temp badge"),
    ("fuel line purge", "fuel line flush"),
    ("fuel-line purge", "fuel-line flush"),
    ("mobilization fee", "mobilization charge"),
    ("night lighting upgrade", "night lighting refresh"),
    ("radio traffic", "radio chatter"),
    ("back-to-back shifts", "back-to-back stints"),
    ("shift bans", "stint bans"),
    ("shift ban", "stint ban"),
    ("sea trials", "harbor trials"),
    ("sea trial", "harbor trial"),
    ("contingencies", "reserves"),
    ("contingency", "reserve"),
    ("legacy barcode", "holdover barcode"),
    ("width confirmed", "width verified"),
    ("noise complaints", "noise grievances"),
    ("noise complaint", "noise grievance"),
    ("critical path", "critical track"),
    ("hydraulic hose", "hydraulic line"),
    ("load test certificate", "load rating certificate"),
    ("gangway load tests", "gangway load checks"),
    ("gangway load test", "gangway load check"),
    ("passenger use", "passenger boarding"),
    ("floodlight circuits", "floodlight loops"),
    ("floodlight circuit", "floodlight loop"),
    ("maintenance mode", "service mode"),
    ("gate commissioning", "gate activation"),
    ("after-action", "post-action"),
    ("ramp handover", "ramp handoff"),
    ("revenue service", "fare service"),
    ("gate vendor", "gate supplier"),
    ("gangway vendor", "gangway supplier"),
    ("gate retrofit", "gate-lane retrofit"),
    ("gangway replacement", "gangway renewal"),
    ("fare gate lanes", "fare-gate lanes"),
    ("fare gate lane", "fare-gate lane"),
)


def normalize(text: str) -> str:
    """Mirror scoring.normalize: lowercase and collapse whitespace."""

    return WHITESPACE.sub(" ", text.lower()).strip()


def planted_fact_anchors(bible_path: Path) -> list[str]:
    """Parse the F01-F48 anchor strings from the bible's planted-facts table."""

    anchors: list[str] = []
    rows = 0
    for line in bible_path.read_text(encoding="utf-8").splitlines():
        if not FACT_ROW.match(line):
            continue
        cells = line.split("|")
        if len(cells) < 5:
            raise ValueError(f"Malformed planted-fact row in {bible_path}: {line!r}")
        rows += 1
        anchors.extend(BACKTICKED.findall(cells[3]))
    if rows != 48:
        raise ValueError(f"Expected 48 planted-fact rows in {bible_path}, found {rows}")
    return anchors


def universe_spec(rng: random.Random, line_word: str) -> dict:
    surnames = rng.sample(SURNAMES, len(PEOPLE))
    pier_main, pier_3, pier_5, pier_7 = rng.sample(PIER_NUMBERS, 4)
    deck_source = rng.choice(DECKHAND_SOURCES)
    fee = rng.choice(MOBILIZATION_FEES)
    percent = rng.choice(DISCOUNT_PERCENTS)
    return {
        "line_word": line_word,
        "slug": line_word.lower(),
        "surnames": surnames,
        "pier_main": pier_main,
        "pier_3": pier_3,
        "pier_5": pier_5,
        "pier_7": pier_7,
        "vessel": rng.choice(VESSELS),
        "pass": rng.choice(PASSES),
        "surge": rng.choice(SURGES),
        "codename": rng.choice(CODENAMES),
        "condo": rng.choice(CONDOS),
        "gate_vendor": rng.choice(GATE_VENDORS),
        "hoist_vendor": rng.choice(HOIST_VENDORS),
        "marine_vendor": rng.choice(MARINE_VENDORS),
        "readiness": rng.choice(READINESS_WORDS),
        "route": rng.choice(HARBOR_ROUTES),
        "alloy": rng.choice(ALLOYS),
        "gang_hose": rng.choice(GANG_HOSES),
        "gate_hose": rng.choice(GATE_HOSES),
        "lanes": rng.choice(LANES),
        "deck_source": deck_source,
        "deck_edited": deck_source - 1,
        "badges": rng.choice(BADGE_COUNTS),
        "minutes": rng.choice(VEST_MINUTES),
        "width": rng.choice(GANGWAY_WIDTHS),
        "cap": rng.choice(CHANGE_ORDER_CAPS),
        "contingency": rng.choice(CONTINGENCY_AMOUNTS),
        "fee": fee,
        "percent": percent,
        "fee_discounted": fee * (100 - percent) // 100,
    }


def universe_replacements(spec: dict) -> list[tuple[str, str]]:
    """The full old-to-new phrase table for one universe (canonical casing)."""

    pairs: list[tuple[str, str]] = list(STATIC_REPLACEMENTS)
    for (first, last, replace_bare), surname in zip(PEOPLE, spec["surnames"]):
        if replace_bare:
            pairs.append((last, surname))
        else:
            pairs.append((f"{first} {last}", f"{first} {surname}"))
    for seed_pier, new_pier in (
        (9, spec["pier_main"]), (3, spec["pier_3"]), (5, spec["pier_5"]), (7, spec["pier_7"]),
    ):
        pairs.extend(
            (
                (f"piers {seed_pier}", f"piers {new_pier}"),
                (f"pier {seed_pier}", f"pier {new_pier}"),
                (f"pier-{seed_pier}", f"pier-{new_pier}"),
                (f"pier{seed_pier}", f"pier{new_pier}"),
                (f"p{seed_pier}", f"p{new_pier}"),
            )
        )
    pairs.append(("9b", f"{spec['pier_main']}b"))
    vessel_word, vessel_code = spec["vessel"]
    pass_word, pass_code = spec["pass"]
    surge_word, surge_code = spec["surge"]
    alloy_bare, alloy_full = spec["alloy"]
    lane_digit, lane_word = spec["lanes"]
    pairs.extend(
        (
            ("HarborLine", f"{spec['line_word']}Line"),
            ("Seaglass", vessel_word),
            ("SG-REFIT", f"{vessel_code}-REFIT"),
            ("HarborPass", f"{pass_word}Pass"),
            ("HP-MIGRATE", f"{pass_code}-MIGRATE"),
            ("Storm Surge", f"{surge_word} Surge"),
            ("SSB", surge_code),
            ("Highwater", spec["codename"]),
            ("Surfside", spec["condo"]),
            ("Turnstile", spec["gate_vendor"]),
            ("Bridgeway", spec["hoist_vendor"]),
            ("Kelwick", spec["marine_vendor"]),
            ("Terminal Readiness", f"{spec['readiness']} Readiness"),
            ("Friday Harbor", f"{spec['route']} Harbor"),
            ("6061-T6", alloy_full),
            ("6061", alloy_bare),
            ("100R2AT", spec["gang_hose"]),
            ("100R1AT", spec["gate_hose"]),
            ("4 lanes", f"{lane_digit} lanes"),
            ("four lanes", f"{lane_word} lanes"),
            ("four fare gate lanes", f"{lane_word} fare-gate lanes"),
            ("4 fare gate lanes", f"{lane_digit} fare-gate lanes"),
            ("four fare", f"{lane_word} fare"),
            ("4 deckhands", f"{spec['deck_source']} deckhands"),
            ("3 deckhands", f"{spec['deck_edited']} deckhands"),
            ("14 temporary badges", f"{spec['badges']} temp badges"),
            ("14 contractor", f"{spec['badges']} contractor"),
            ("14 temporary", f"{spec['badges']} temporary"),
            ("14 temp", f"{spec['badges']} temp"),
            ("14 badges", f"{spec['badges']} badges"),
            ("45 minutes", f"{spec['minutes']} minutes"),
            ("45-minute", f"{spec['minutes']}-minute"),
            ("45 min", f"{spec['minutes']} min"),
            ("2.4m", f"{spec['width']}m"),
            ("2.4", spec["width"]),
            ("$18,400", f"${spec['cap']:,}"),
            ("$18400", f"${spec['cap']}"),
            ("$1,840", f"${spec['cap'] // 10:,}"),
            ("$62,000", f"${spec['contingency']:,}"),
            ("$62000", f"${spec['contingency']}"),
            ("$41,200", f"${spec['fee']:,}"),
            ("$36,256", f"${spec['fee_discounted']:,}"),
            ("12%", f"{spec['percent']}%"),
        )
    )
    # Every spaced phrase also gets a hyphenated twin so slugs in ids, labels,
    # and [[links]] transform consistently with prose.
    hyphenated = [
        (old.replace(" ", "-"), new.replace(" ", "-"))
        for old, new in pairs
        if " " in old
    ]
    return pairs + hyphenated


def adapt_case(matched: str, canonical_old: str, replacement: str) -> str:
    if matched == canonical_old:
        return replacement
    if matched.islower():
        return replacement.lower()
    if matched.isupper():
        return replacement.upper()
    if matched.istitle():
        return replacement.title()
    if matched[:1].isupper() and replacement[:1].islower():
        return replacement[:1].upper() + replacement[1:]
    return replacement


class UniverseTransform:
    """One universe's deterministic text pipeline (phrases, dates, times)."""

    def __init__(self, spec: dict, universe_index: int) -> None:
        self.slug = spec["slug"]
        # 364 keeps weekdays aligned (52 weeks); +7 per universe keeps every
        # universe's calendar (and date-based source ids) distinct.
        self.delta = datetime.timedelta(days=364 + 7 * universe_index)
        self.year = str((datetime.date(2026, 6, 1) + self.delta).year)
        pairs = sorted(universe_replacements(spec), key=lambda pair: len(pair[0]), reverse=True)
        self.by_lower = {old.lower(): (old, new) for old, new in pairs}
        alternation = "|".join(re.escape(old) for old, _ in pairs)
        self.phrases = re.compile(rf"(?<![a-z0-9])(?:{alternation})(?![a-z0-9])", re.IGNORECASE)

    def _phrase(self, match: re.Match) -> str:
        canonical_old, replacement = self.by_lower[match.group(0).lower()]
        return adapt_case(match.group(0), canonical_old, replacement)

    def _iso_date(self, match: re.Match) -> str:
        try:
            date = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return match.group(0)
        return (date + self.delta).isoformat()

    def _month_day(self, match: re.Match) -> str:
        name, day = match.group(1), int(match.group(2))
        key = name.lower()
        month = MONTHS.index(key) + 1 if key in MONTHS else MONTH_ABBREVS[key]
        try:
            date = datetime.date(2026, month, day)
        except ValueError:
            return match.group(0)
        shifted = date + self.delta
        new_name = MONTHS[shifted.month - 1]
        if key not in MONTHS:
            new_name = new_name[:3]
        if name[0].isupper():
            new_name = new_name.capitalize()
        return f"{new_name} {shifted.day}"

    def _time(self, match: re.Match) -> str:
        hour = (int(match.group(1)) + 1) % 24
        width = len(match.group(1))
        return f"{hour:0{width}d}:{match.group(2)}"

    def apply(self, text: str) -> str:
        text = self.phrases.sub(self._phrase, text)
        text = ISO_DATE.sub(self._iso_date, text)
        text = MONTH_DAY.sub(self._month_day, text)
        text = TIME_OF_DAY.sub(self._time, text)
        return BARE_YEAR.sub(self.year, text)


def seed_workspace_files(seed_root: Path) -> list[Path]:
    files = [seed_root / "runtime.md"]
    for directory in CLONE_DIRS:
        files.extend(sorted((seed_root / directory).glob("*.md")))
    return [path for path in files if path.exists()]


def clone_universe(
    seed_root: Path,
    out_root: Path,
    transform: UniverseTransform,
    anchors: list[str],
) -> int:
    # Map every seed record stem to its transformed id, then suffix whole-id
    # occurrences so clone references stay inside the clone.
    stems: set[str] = set()
    for directory in CLONE_DIRS:
        for path in sorted((seed_root / directory).glob("*.md")):
            if path.name != "README.md":
                stems.add(path.stem)
    id_map = {stem: transform.apply(stem) for stem in sorted(stems)}
    if len(set(id_map.values())) != len(id_map):
        raise RuntimeError(f"Universe {transform.slug}: transformed ids collide")
    alternation = "|".join(
        re.escape(new_id) for new_id in sorted(id_map.values(), key=len, reverse=True)
    )
    suffix_pattern = re.compile(rf"(?<![a-z0-9-])(?:{alternation})(?![a-z0-9-])")
    suffix = lambda match: f"{match.group(0)}-{transform.slug}"  # noqa: E731

    written = 0
    normalized_anchors = [normalize(anchor) for anchor in anchors]
    for directory in CLONE_DIRS:
        for path in sorted((seed_root / directory).glob("*.md")):
            if path.name == "README.md":
                continue
            text = suffix_pattern.sub(suffix, transform.apply(path.read_text(encoding="utf-8")))
            haystack = normalize(text)
            leaked = [anchor for anchor in normalized_anchors if anchor in haystack]
            if leaked:
                raise RuntimeError(
                    f"Universe {transform.slug}: planted-fact anchors leaked into "
                    f"clone of {path.name}: {leaked}"
                )
            new_stem = f"{id_map[path.stem]}-{transform.slug}"
            if not ID_PATTERN.match(new_stem):
                raise RuntimeError(f"Universe {transform.slug}: invalid clone id {new_stem!r}")
            (out_root / directory / f"{new_stem}.md").write_text(text, encoding="utf-8")
            written += 1
    return written


def build_tier(seed_root: Path, target_nodes: int, rng_seed: int, out_root: Path) -> dict:
    seed_root = seed_root.resolve()
    if not (seed_root / "graph").is_dir():
        raise ValueError(f"Not a seed workspace (no graph/): {seed_root}")
    if target_nodes < 2 * SEED_NODE_COUNT or target_nodes % SEED_NODE_COUNT != 0:
        raise ValueError(
            f"--target-nodes must be a multiple of {SEED_NODE_COUNT}, at least "
            f"{2 * SEED_NODE_COUNT} (whole cloned universes); got {target_nodes}"
        )
    universes = target_nodes // SEED_NODE_COUNT - 1
    if universes > len(LINE_WORDS):
        raise ValueError(f"At most {len(LINE_WORDS)} universes supported; asked for {universes}")
    if out_root.exists() and any(out_root.iterdir()):
        raise ValueError(f"Output directory is not empty: {out_root}")

    anchors = planted_fact_anchors(seed_root / "bible.md")
    for directory in CLONE_DIRS:
        (out_root / directory).mkdir(parents=True, exist_ok=True)
    copied = 0
    for path in seed_workspace_files(seed_root):
        shutil.copyfile(path, out_root / path.relative_to(seed_root))
        copied += 1

    rng = random.Random(rng_seed)
    line_words = rng.sample(LINE_WORDS, universes)
    cloned = 0
    for index, line_word in enumerate(line_words):
        transform = UniverseTransform(universe_spec(rng, line_word), index)
        cloned += clone_universe(seed_root, out_root, transform, anchors)

    node_count = len(list((out_root / "graph").glob("*.md")))
    if node_count != target_nodes:
        raise RuntimeError(f"Expected {target_nodes} graph nodes, wrote {node_count}")
    errors = validate_workspace(out_root)
    warnings = graph_quality_warnings(out_root)
    if errors or warnings:
        raise RuntimeError(
            f"Generated tier is not doctor-clean: {len(errors)} errors, "
            f"{len(warnings)} warnings; first: {(errors + warnings)[0]}"
        )
    return {
        "target_nodes": target_nodes,
        "universes": universes,
        "seed_files_copied": copied,
        "clone_files_written": cloned,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Grow a distractor tier (200/1000/5000 nodes) from the pinned seed workspace."
    )
    parser.add_argument("--seed-workspace", type=Path, required=True, help="Pinned seed workspace directory.")
    parser.add_argument("--target-nodes", type=int, required=True, help="Total graph nodes in the tier (e.g. 200, 1000, 5000).")
    parser.add_argument("--rng-seed", type=int, required=True, help="RNG seed; same seed gives a byte-identical tree.")
    parser.add_argument("--out", type=Path, required=True, help="Output tier directory (must be empty; keep it out of the repo).")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    try:
        summary = build_tier(args.seed_workspace, args.target_nodes, args.rng_seed, args.out)
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    elapsed = time.perf_counter() - started
    print(
        f"{summary['target_nodes']} nodes ({summary['universes']} clone universes, "
        f"{summary['clone_files_written']} clone files, {summary['seed_files_copied']} seed files) "
        f"-> {args.out} in {elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
