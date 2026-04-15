# Single parsing pipeline: typed text -> structured dict for build_command_from_parse_result.

from modules.command_parser import CommandParser


class IntentParser(CommandParser):
    """Same rules as CommandParser; name marks the intent step before CommandRouter."""
