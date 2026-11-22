"""Generate distinct display names from combinations of first and last names."""
import itertools
import random

FIRST_NAMES = [
    "Alex", "Maria", "Jonas", "Priya", "Liam", "Sofia", "Noah", "Amara",
    "Lukas", "Elena", "Omar", "Hannah", "Mateo", "Yuki", "David", "Leila",
    "Felix", "Nora", "Samuel", "Ines",
]
LAST_NAMES = [
    "Becker", "Rossi", "Nguyen", "Okafor", "Larsen", "Silva", "Novak",
    "Haddad", "Meyer", "Tanaka", "Dubois", "Kowalski", "Garcia", "Lindqvist",
    "Fischer", "Moreau", "Petrov", "Jansen", "Keller", "Santos",
]


def generate_names(count, exclude=(), seed=None):
    """Return `count` unique "First Last" names, none of them in `exclude`.

    Meta only accepts letters and spaces in test-user names, so uniqueness
    comes from the combination itself rather than from a numeric suffix.
    """
    taken = set(exclude)
    pool = [
        f"{first} {last}"
        for first, last in itertools.product(FIRST_NAMES, LAST_NAMES)
        if f"{first} {last}" not in taken
    ]
    if count > len(pool):
        raise ValueError(
            f"Requested {count} names but only {len(pool)} unused combinations remain"
        )
    return random.Random(seed).sample(pool, count)
