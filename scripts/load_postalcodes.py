#!/usr/bin/env python3
"""Load postalcodes CSV into the postalcodes database.

CSV format (semicolon-separated):
  straat;huisnummer;huisletter;huisnummertoevoeging;postcode;woonplaats;gemeente;provincie;lat;lon

huisletter + huisnummertoevoeging are concatenated into 'toevoeging',
then appended to huisnummer with a dash to match the API query format:
  99      → 99
  105  1  → 105-1
  112 A   → 112-A
  99  B 1 → 99-B1

Usage:
  python load_postalcodes.py <csv_file> [--dry-run] [--truncate]
"""

import argparse
import csv
import os
import sys
import tempfile
import time

import sqlalchemy as sa


COLUMNS = ["postcode", "huisnummer", "straat", "buurt", "wijk",
           "woonplaats", "gemeente", "provincie", "latitude", "longitude"]


def build_huisnummer(huisnummer, huisletter, huisnummertoevoeging):
    """Combine huisnummer + huisletter + huisnummertoevoeging into one field.

    Uppercased to match MySQL's case-insensitive primary key collation.
    """
    toevoeging = f"{huisletter}{huisnummertoevoeging}".upper()
    if toevoeging:
        return f"{huisnummer}-{toevoeging}"
    return huisnummer


def transform_csv_to_tsv(csv_file, tsv_file):
    """Stream CSV → deduped TSV for LOAD DATA. Returns (unique, dupes, skipped)."""
    seen = set()
    skipped = 0
    dupes = 0
    unique = 0

    with open(csv_file, "r", encoding="utf-8") as fin:
        reader = csv.DictReader(fin, delimiter=";")
        for row in reader:
            postcode = row.get("postcode", "").strip()
            huisnummer_raw = row.get("huisnummer", "").strip()
            if not postcode or not huisnummer_raw:
                skipped += 1
                continue

            huisletter = row.get("huisletter", "").strip()
            toevoeging = row.get("huisnummertoevoeging", "").strip()
            huisnummer = build_huisnummer(huisnummer_raw, huisletter, toevoeging)

            key = (postcode, huisnummer)
            if key in seen:
                dupes += 1
                continue
            seen.add(key)

            fields = [
                postcode,
                huisnummer,
                row.get("straat", "").strip(),
                "",  # buurt
                "",  # wijk
                row.get("woonplaats", "").strip(),
                row.get("gemeente", "").strip(),
                row.get("provincie", "").strip(),
                row.get("lat", "0").strip(),
                row.get("lon", "0").strip(),
            ]
            tsv_file.write("\t".join(fields) + "\n")
            unique += 1

    return unique, dupes, skipped


def load_with_load_data(engine, tsv_path, truncate):
    """Use LOAD DATA LOCAL INFILE for maximum speed."""
    col_list = ", ".join(COLUMNS)
    with engine.begin() as conn:
        if truncate:
            print("Truncating postalcodes table...")
            conn.execute(sa.text("TRUNCATE TABLE postalcodes"))

        print("Disabling keys...")
        conn.execute(sa.text("ALTER TABLE postalcodes DISABLE KEYS"))

        print("Loading with LOAD DATA LOCAL INFILE...")
        t0 = time.time()
        conn.execute(sa.text(
            f"LOAD DATA LOCAL INFILE :path INTO TABLE postalcodes "
            f"FIELDS TERMINATED BY '\\t' "
            f"LINES TERMINATED BY '\\n' "
            f"({col_list})"
        ), {"path": tsv_path})
        elapsed = time.time() - t0

        print("Enabling keys (rebuilding indexes)...")
        t1 = time.time()
        conn.execute(sa.text("ALTER TABLE postalcodes ENABLE KEYS"))
        idx_time = time.time() - t1

    return elapsed, idx_time


def load_with_inserts(engine, csv_file, truncate, batch_size):
    """Fallback: batch INSERT via SQLAlchemy."""
    meta = sa.MetaData()
    table = sa.Table("postalcodes", meta, autoload_with=engine)

    seen = set()
    skipped = 0
    dupes = 0

    with engine.begin() as conn:
        if truncate:
            print("Truncating postalcodes table...")
            conn.execute(sa.text("TRUNCATE TABLE postalcodes"))

        conn.execute(sa.text("ALTER TABLE postalcodes DISABLE KEYS"))

        batch = []
        inserted = 0
        t0 = time.time()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                postcode = row.get("postcode", "").strip()
                huisnummer_raw = row.get("huisnummer", "").strip()
                if not postcode or not huisnummer_raw:
                    skipped += 1
                    continue

                huisletter = row.get("huisletter", "").strip()
                toevoeging = row.get("huisnummertoevoeging", "").strip()
                huisnummer = build_huisnummer(huisnummer_raw, huisletter, toevoeging)

                key = (postcode, huisnummer)
                if key in seen:
                    dupes += 1
                    continue
                seen.add(key)

                batch.append({
                    "postcode": postcode,
                    "huisnummer": huisnummer,
                    "straat": row.get("straat", "").strip(),
                    "buurt": "",
                    "wijk": "",
                    "woonplaats": row.get("woonplaats", "").strip(),
                    "gemeente": row.get("gemeente", "").strip(),
                    "provincie": row.get("provincie", "").strip(),
                    "latitude": float(row.get("lat", 0)),
                    "longitude": float(row.get("lon", 0)),
                })

                if len(batch) >= batch_size:
                    conn.execute(table.insert(), batch)
                    inserted += len(batch)
                    batch = []
                    elapsed = time.time() - t0
                    rate = inserted / elapsed if elapsed > 0 else 0
                    print(f"  {inserted:>12,} inserted  ({rate:,.0f} rows/s)")

            if batch:
                conn.execute(table.insert(), batch)
                inserted += len(batch)

        print("Enabling keys (rebuilding indexes)...")
        conn.execute(sa.text("ALTER TABLE postalcodes ENABLE KEYS"))

    elapsed = time.time() - t0
    print(f"CSV totals: {inserted + dupes + skipped:,} rows, {inserted:,} unique, {dupes} duplicates, {skipped} skipped")
    return inserted, elapsed


def main():
    parser = argparse.ArgumentParser(description="Load postalcodes CSV into MySQL")
    parser.add_argument("csv_file", help="Path to the semicolon-separated CSV file")
    parser.add_argument("--db-uri", help="SQLAlchemy database URI (default: from .env SQLALCHEMY_BINDS_POSTALCODES)")
    parser.add_argument("--dry-run", action="store_true", help="Parse and count rows without inserting")
    parser.add_argument("--truncate", action="store_true", help="TRUNCATE the table before loading")
    parser.add_argument("--no-load-data", action="store_true",
                        help="Use INSERT batches instead of LOAD DATA LOCAL INFILE")
    parser.add_argument("--batch-size", type=int, default=10000,
                        help="Rows per INSERT batch when using --no-load-data (default: 10000)")
    args = parser.parse_args()

    # Resolve DB URI
    db_uri = args.db_uri
    if not db_uri:
        try:
            from dotenv import dotenv_values
            env = dotenv_values(".env")
            db_uri = env.get("SQLALCHEMY_BINDS_POSTALCODES")
        except ImportError:
            pass
    if not db_uri:
        print("ERROR: No database URI. Pass --db-uri or set SQLALCHEMY_BINDS_POSTALCODES in .env")
        sys.exit(1)

    print(f"Database: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")
    print(f"CSV file: {args.csv_file}")

    if args.dry_run:
        seen = set()
        count = 0
        dupes = 0
        with open(args.csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                postcode = row.get("postcode", "").strip()
                huisnummer_raw = row.get("huisnummer", "").strip()
                if not postcode or not huisnummer_raw:
                    continue
                huisletter = row.get("huisletter", "").strip()
                toevoeging = row.get("huisnummertoevoeging", "").strip()
                huisnummer = build_huisnummer(huisnummer_raw, huisletter, toevoeging)
                key = (postcode, huisnummer)
                if key in seen:
                    dupes += 1
                    continue
                seen.add(key)
                count += 1
                if count <= 10:
                    straat = row.get("straat", "").strip()
                    woonplaats = row.get("woonplaats", "").strip()
                    print(f"  {postcode} {huisnummer:>10s}  {straat}, {woonplaats}")
        if count > 10:
            print(f"  ... and {count - 10:,} more")
        print(f"Total: {count:,} unique rows ({dupes} duplicates)")
        return

    # Enable local_infile in the connection URI
    if not args.no_load_data:
        sep = "&" if "?" in db_uri else "?"
        db_uri_load = db_uri + sep + "local_infile=1"
    else:
        db_uri_load = db_uri

    engine = sa.create_engine(db_uri_load)

    if args.no_load_data:
        print(f"Method: INSERT batches ({args.batch_size:,} per batch)")
        inserted, elapsed = load_with_inserts(engine, args.csv_file, args.truncate, args.batch_size)
        rate = inserted / elapsed if elapsed > 0 else 0
        print(f"Done. Loaded {inserted:,} rows in {elapsed:.1f}s ({rate:,.0f} rows/s)")
    else:
        # Transform CSV → temp TSV, then LOAD DATA LOCAL INFILE
        print("Method: LOAD DATA LOCAL INFILE")
        print("Transforming CSV → TSV...")
        t0 = time.time()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False, encoding="utf-8") as tmp:
            tsv_path = tmp.name
            unique, dupes, skipped = transform_csv_to_tsv(args.csv_file, tmp)
        transform_time = time.time() - t0
        tsv_size = os.path.getsize(tsv_path) / (1024 * 1024)
        print(f"  {unique:,} unique rows, {dupes} duplicates, {skipped} skipped ({transform_time:.1f}s, {tsv_size:.0f} MB)")

        try:
            load_time, idx_time = load_with_load_data(engine, tsv_path, args.truncate)
            rate = unique / load_time if load_time > 0 else 0
            total_time = transform_time + load_time + idx_time
            print(f"Done. Loaded {unique:,} rows in {total_time:.1f}s "
                  f"(transform {transform_time:.1f}s + load {load_time:.1f}s + index {idx_time:.1f}s, "
                  f"{rate:,.0f} rows/s load)")
        finally:
            os.unlink(tsv_path)


if __name__ == "__main__":
    main()
