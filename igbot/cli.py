"""Post a picture to your Instagram professional account.

    python -m igbot.cli --image-url https://example.com/photo.jpg --caption "Hello"
"""
import argparse
import os
import sys

from .client import InstagramBot, InstagramError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image-url", required=True, help="public HTTPS URL of a JPEG")
    parser.add_argument("--caption", default="")
    parser.add_argument("--alt-text", default="")
    args = parser.parse_args(argv)

    if not args.image_url.startswith("https://"):
        sys.exit("--image-url must be a public https:// URL (Instagram downloads it).")
    user_id, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    if not user_id or not token:
        sys.exit("Set IG_USER_ID and IG_ACCESS_TOKEN in the environment.")

    bot = InstagramBot(
        user_id, token, os.environ.get("IG_API_BASE") or "https://graph.instagram.com"
    )
    try:
        media_id, permalink = bot.post_photo(args.image_url, args.caption, args.alt_text)
    except InstagramError as exc:
        print(f"Post failed: {exc}", file=sys.stderr)
        return 1
    print(f"Posted media {media_id} {permalink}".rstrip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
