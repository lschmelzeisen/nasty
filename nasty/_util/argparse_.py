import argparse

from overrides import overrides


# Adapted from: https://stackoverflow.com/a/9643162/211404
class SingleMetavarHelpFormatter(argparse.HelpFormatter):
    @overrides
    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar

        result = ", ".join(action.option_strings)
        if action.nargs != 0:
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            result += " " + args_string
        return result
