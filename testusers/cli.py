"""Create, list and delete Meta test users for your own app.

    python -m testusers.cli create --count 5
    python -m testusers.cli list
    python -m testusers.cli delete --all
"""
import argparse
import os
import sys

from .graph import GraphClient, GraphError
from .names import generate_names
from .tracker import Tracker

MAX_PER_RUN = 50  # Meta caps test users per app; keep single runs modest.


def _client():
    app_id, secret = os.environ.get("META_APP_ID"), os.environ.get("META_APP_SECRET")
    if not app_id or not secret:
        sys.exit("Set META_APP_ID and META_APP_SECRET in the environment.")
    return GraphClient(app_id, secret, os.environ.get("META_GRAPH_VERSION") or None)


def cmd_create(args, client=None):
    if not 1 <= args.count <= MAX_PER_RUN:
        sys.exit(f"--count must be between 1 and {MAX_PER_RUN}")
    client = client or _client()
    tracker = Tracker(args.output)
    permissions = [p for p in args.permissions.split(",") if p]
    names = generate_names(args.count, exclude=tracker.names(), seed=args.seed)
    created = 0
    try:
        for name in names:
            user = client.create_test_user(name, permissions)
            tracker.add(name, user)
            created += 1
            print(f"[{created}/{args.count}] created {name} (id {user.get('id')})")
    except GraphError as exc:
        print(f"Stopped after {created} of {args.count}: {exc}", file=sys.stderr)
        return 1
    finally:
        # Save even on failure so already-created users are never lost.
        tracker.save()
    print(f"Tracker saved to {args.output}")
    return 0


def cmd_list(args, client=None):
    client = client or _client()
    users = list(client.list_test_users())
    for user in users:
        print(user.get("id"))
    print(f"{len(users)} test user(s)")
    return 0


def cmd_delete(args, client=None):
    client = client or _client()
    tracker = Tracker(args.output)
    ids = [u["id"] for u in client.list_test_users()] if args.all else args.ids
    if not ids:
        print("Nothing to delete.")
        return 0
    failed = 0
    try:
        for user_id in ids:
            try:
                client.delete_test_user(user_id)
                tracker.mark_deleted(user_id)
                print(f"deleted {user_id}")
            except GraphError as exc:
                failed += 1
                print(f"could not delete {user_id}: {exc}", file=sys.stderr)
    finally:
        if tracker.path.exists():
            tracker.save()
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default="test_users.xlsx", help="Excel tracker path")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create N test users")
    create.add_argument("--count", type=int, required=True)
    create.add_argument("--permissions", default="", help="comma-separated permissions to grant")
    create.add_argument("--seed", type=int, default=None, help="make name selection reproducible")
    create.set_defaults(func=cmd_create)

    sub.add_parser("list", help="list the app's test users").set_defaults(func=cmd_list)

    delete = sub.add_parser("delete", help="delete test users")
    group = delete.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--ids", nargs="+")
    delete.set_defaults(func=cmd_delete)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
