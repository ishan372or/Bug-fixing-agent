__all__ = ["BugFixAgent"]


def __getattr__(name: str):
    if name == "BugFixAgent":
        from .api import BugFixAgent

        return BugFixAgent

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
