#!/usr/bin/env python3
"""
Training Changes Migration Script - February 2026

Based on TRAINING_CHANGES_PLAN.md.
Requires the admin API to be running and a valid JWT token.

Uses proper API enrollment operations (not bulk-move) so that
email notifications are sent to students and trainers.

Safeguards:
    - Verifies enrollment lists match before making changes
    - Warns about students not in the plan (enrolled since backup)
    - Idempotent: skips already-completed operations on resume
    - Non-fatal errors: logs failures and continues
    - Production confirmation required for non-localhost URLs

Usage:
    python migrate_trainings.py --base-url http://localhost:5001
    python migrate_trainings.py --base-url https://bcourse-app.bgwlan.nl --confirm
"""

import argparse
import sys

import jwt
import requests
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Configuration — from TRAINING_CHANGES_PLAN.md
# ---------------------------------------------------------------------------

NEW_TRAININGS = [
    {
        "name": "Ademcirkel 13 Mar 2026",
        "trainingtype_id": 4,
        "max_participants": 14,
        "active": True,
        "apply_policies": True,
        "trainer_ids": [1, 10, 11],  # Brendan Bank, Esther de Vries, Jaron Salem
        "events": [{"start_time": "2026-03-13T09:30:00", "end_time": "2026-03-13T12:15:00", "location_id": 1}],
    },
    {
        "name": "Ademcirkel 8 May 2026",
        "trainingtype_id": 4,
        "max_participants": 16,
        "active": True,
        "apply_policies": True,
        "trainer_ids": [1, 10, 11],  # Brendan Bank, Esther de Vries, Jaron Salem
        "events": [{"start_time": "2026-05-08T09:30:00", "end_time": "2026-05-08T12:15:00", "location_id": 1}],
    },
    {
        "name": "Bonding 17 Apr 2026",
        "trainingtype_id": 1,
        "max_participants": 14,
        "active": True,
        "apply_policies": True,
        "trainer_ids": [1, 9, 11],  # Brendan Bank, Hans van Wechem, Jaron Salem
        "events": [{"start_time": "2026-04-17T07:30:00", "end_time": "2026-04-17T13:30:00", "location_id": 1}],
    },
]

# (source_training_id, index into NEW_TRAININGS, student_ids)
MOVES = [
    (31, 0, [33, 35, 7, 41, 55, 32, 47, 89, 93, 91, 79, 92, 101, 104]),
    (37, 1, [33, 26, 28, 35, 7, 41, 55, 32, 53, 65, 47, 46, 91, 79, 76, 101, 23]),
    (36, 2, [33, 1, 28, 35, 7, 41, 55, 26, 32, 53, 47, 74, 34, 91, 76, 93, 31, 101]),
]

DEACTIVATE = [31, 36, 37]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_token(secret_key, user_id=108, email="brendan.bank@gmail.com"):
    payload = {
        "user_id": user_id,
        "email": email,
        "role": "db-admin",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=86400),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def api(method, url, token, json_data=None, fatal=True):
    """Make an API request. Returns (response_json, None) on success,
    or (None, error_string) on failure. Exits on fatal errors."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.request(method, url, headers=headers, json=json_data, timeout=30)
    except requests.RequestException as e:
        err = f"Request failed: {e}"
        if fatal:
            print(f"  FATAL: {err}")
            sys.exit(1)
        return None, err

    if resp.status_code == 204:
        return None, None
    if resp.status_code >= 400:
        err = f"HTTP {resp.status_code}: {resp.text[:200]}"
        if fatal:
            print(f"  FATAL: {err}")
            sys.exit(1)
        return None, err
    return resp.json(), None


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_enrollments(base, token):
    """Compare hardcoded student lists against live enrollment data.
    Returns True if safe to proceed, False if mismatches found."""
    print("\n=== VERIFY ENROLLMENT LISTS ===")
    ok = True

    for source_id, target_idx, expected_ids in MOVES:
        # Get all enrollments for this training
        enrollments, err = api("GET", f"{base}/trainings/{source_id}/enrollments", token)
        if err:
            print(f"  ERROR: Cannot read enrollments for training {source_id}: {err}")
            ok = False
            continue

        live_ids = {e["student_id"] for e in enrollments}
        expected_set = set(expected_ids)

        missing = expected_set - live_ids
        extra = live_ids - expected_set

        if missing:
            print(f"  WARNING Training {source_id}: {len(missing)} students in script "
                  f"but NOT enrolled on server: {sorted(missing)}")
            print(f"    These de-enrollments will fail (404). They will be skipped.")
            ok = False

        if extra:
            extra_details = []
            for e in enrollments:
                if e["student_id"] in extra:
                    extra_details.append(f"{e['student_name']} (id={e['student_id']}, "
                                         f"status={e['status']})")
            print(f"  WARNING Training {source_id}: {len(extra)} students enrolled on server "
                  f"but NOT in script (enrolled since backup?):")
            for d in extra_details:
                print(f"    - {d}")
            print(f"    These students will NOT be migrated.")

        if not missing and not extra:
            print(f"  Training {source_id}: OK ({len(expected_ids)} students match)")

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run training migration plan")
    parser.add_argument("--base-url", required=True, help="Base URL (e.g. http://localhost:5001)")
    parser.add_argument("--secret-key", help="SECRET_KEY for JWT generation (reads from .env if omitted)")
    parser.add_argument("--token", help="Pre-generated JWT token (skips token generation)")
    parser.add_argument("--dry-run", action="store_true", help="Verify pre-state only, don't make changes")
    parser.add_argument("--confirm", action="store_true",
                        help="Required for non-localhost URLs (production safety)")
    args = parser.parse_args()

    base = args.base_url.rstrip("/") + "/admin-api"

    # Production safety check
    is_production = "localhost" not in args.base_url and "127.0.0.1" not in args.base_url
    if is_production and not args.dry_run:
        if not args.confirm:
            print(f"ERROR: Running against non-local URL: {args.base_url}")
            print("Add --confirm to proceed. Make sure you have:")
            print("  1. Stopped the scheduler (sudo systemctl stop bcourse-scheduler.service)")
            print("  2. Made a fresh database backup")
            print("  3. Verified the enrollment lists with --dry-run first")
            sys.exit(1)
        print(f"*** PRODUCTION MODE: {args.base_url} ***")
        print("Make sure the scheduler is STOPPED to prevent interference.")
        resp = input("Type 'yes' to continue: ")
        if resp.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    # Get token
    if args.token:
        token = args.token
    elif args.secret_key:
        token = generate_token(args.secret_key)
    else:
        try:
            from dotenv import dotenv_values
            env = dotenv_values(".env")
            secret = env.get("SECRET_KEY", "").strip('"')
            token = generate_token(secret)
        except Exception as e:
            print(f"Cannot read SECRET_KEY from .env: {e}")
            print("Pass --secret-key or --token explicitly.")
            sys.exit(1)

    # Verify auth works
    print("=== VERIFY AUTH ===")
    r, err = api("GET", f"{base}/trainings/31", token)
    if err:
        print(f"  Auth failed: {err}")
        sys.exit(1)
    print(f"  Auth OK (reached training {r['id']})")

    # Pre-state
    print("\n=== PRE-STATE ===")
    for tid in [31, 36, 37]:
        t, _ = api("GET", f"{base}/trainings/{tid}", token)
        print(f"  Training {t['id']} ({t['name']}): active={t['active']}, "
              f"enrolled={t['enrollment_count']}, waitlist={t['waitlist_count']}, max={t['max_participants']}")

    # Verify enrollment lists match
    lists_ok = verify_enrollments(base, token)

    if args.dry_run:
        if lists_ok:
            print("\n--- DRY RUN: all checks passed, safe to run ---")
        else:
            print("\n--- DRY RUN: WARNINGS found above, review before running ---")
        return

    if not lists_ok:
        print("\nWARNING: Enrollment list mismatches detected (see above).")
        resp = input("Continue anyway? Mismatched students will be skipped. Type 'yes': ")
        if resp.strip().lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    # Step 1: Create new trainings (with enough capacity for all students)
    print("\n=== CREATE TRAININGS ===")
    new_ids = []
    for idx, spec in enumerate(NEW_TRAININGS):
        num_students = max(
            (len(sids) for src, tidx, sids in MOVES if tidx == idx),
            default=0,
        )
        create_spec = dict(spec)
        if num_students > spec["max_participants"]:
            create_spec["max_participants"] = num_students
            print(f"  (temporarily setting max_participants={num_students} "
                  f"for {spec['name']} to fit all {num_students} students)")
        t, err = api("POST", f"{base}/trainings/", token, create_spec)
        if err:
            print(f"  FATAL: Failed to create training: {err}")
            sys.exit(1)
        new_ids.append(t["id"])
        trainers = ", ".join(tr["name"] for tr in t.get("trainers", []))
        print(f"  {spec['name']} (max {spec['max_participants']}) -> ID {t['id']}"
              f"{f'  trainers: {trainers}' if trainers else ''}")

    # Step 2: De-enroll from old trainings, enroll into new trainings
    print("\n=== MIGRATE PARTICIPANTS ===")
    errors = []
    for source_id, target_idx, student_ids in MOVES:
        target_id = new_ids[target_idx]
        print(f"\n  --- Training {source_id} -> {target_id} ---")

        # De-enroll each student (sends cancellation emails)
        derolled = 0
        for sid in student_ids:
            _, err = api("DELETE", f"{base}/trainings/{source_id}/enrollments/{sid}",
                         token, fatal=False)
            if err:
                # Check if already de-enrolled (idempotent)
                if "404" in str(err):
                    print(f"    Student {sid}: already de-enrolled from {source_id} (skipped)")
                else:
                    errors.append(f"De-enroll student {sid} from {source_id}: {err}")
                    print(f"    ERROR de-enrolling student {sid}: {err}")
                continue
            derolled += 1
        print(f"  De-enrolled {derolled}/{len(student_ids)} students from training {source_id}")

        # Enroll each student into new training (sends confirmation emails)
        enrolled = 0
        for sid in student_ids:
            _, err = api("POST", f"{base}/trainings/{target_id}/enrollments",
                         token, {"student_id": sid}, fatal=False)
            if err:
                # Check if already enrolled (idempotent)
                if "409" in str(err) or "already enrolled" in str(err).lower():
                    print(f"    Student {sid}: already enrolled in {target_id} (skipped)")
                else:
                    errors.append(f"Enroll student {sid} into {target_id}: {err}")
                    print(f"    ERROR enrolling student {sid}: {err}")
                continue
            enrolled += 1
        print(f"  Enrolled {enrolled}/{len(student_ids)} students into training {target_id}")

    # Step 3: Set correct max_participants on new trainings
    print("\n=== SET CORRECT MAX_PARTICIPANTS ===")
    for idx, spec in enumerate(NEW_TRAININGS):
        target_id = new_ids[idx]
        t, _ = api("PUT", f"{base}/trainings/{target_id}", token, {
            "max_participants": spec["max_participants"],
        })
        print(f"  Training {t['id']} ({t['name']}): max_participants={t['max_participants']}")

    # Step 4: Deactivate old trainings
    print("\n=== DEACTIVATE ===")
    for tid in DEACTIVATE:
        t, _ = api("PATCH", f"{base}/trainings/{tid}/deactivate", token)
        print(f"  Training {t['id']} ({t['name']}): active={t['active']}")

    # Step 5: Final verification
    print("\n=== FINAL STATE ===")
    print("New trainings:")
    for tid in new_ids:
        t, _ = api("GET", f"{base}/trainings/{tid}", token)
        print(f"  Training {t['id']} ({t['name']}): "
              f"enrolled={t['enrollment_count']}, waitlist={t['waitlist_count']}, "
              f"max={t['max_participants']}, spots={t['spots_available']}")
    print("Old trainings:")
    for tid in DEACTIVATE:
        t, _ = api("GET", f"{base}/trainings/{tid}", token)
        print(f"  Training {t['id']} ({t['name']}): active={t['active']}, enrolled={t['enrollment_count']}")

    # Error summary
    if errors:
        print(f"\n=== ERRORS ({len(errors)}) ===")
        for e in errors:
            print(f"  - {e}")
        print("\nMigration completed WITH ERRORS. Review above and fix manually.")
    else:
        print("\n=== DONE (no errors) ===")


if __name__ == "__main__":
    main()
