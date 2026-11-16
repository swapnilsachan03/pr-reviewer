class ReviewSkipped(Exception):
    """Expected reason to stop (draft, too large, stale). Not a failure; exit 0."""
