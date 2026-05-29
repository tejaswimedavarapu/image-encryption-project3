"""
UI Utilities - Handles console output with colors and formatting
Provides a nice CLI experience similar to the original Node.js version.
"""

import click
from contextlib import contextmanager
import sys


def welcome():
    """Display welcome banner."""
    click.echo()
    click.echo(click.style("╔═══════════════════════════════════════════╗", fg='green', bold=True))
    click.echo(click.style("║", fg='green', bold=True) + click.style("  imcrypt  ", fg='white', bold=True, bg='green') + click.style("  v2.0.0 (Python Edition)            ║", fg='green', bold=True))
    click.echo(click.style("║  Secure Image Encryption CLI              ║", fg='green'))
    click.echo(click.style("║  by theninza <https://theninza.me>        ║", fg='green'))
    click.echo(click.style("╚═══════════════════════════════════════════╝", fg='green', bold=True))
    click.echo()


def success(title: str, message: str):
    """Display success message."""
    click.echo()
    click.echo(click.style("✔ ", fg='green', bold=True) + click.style(title, fg='green', bold=True))
    click.echo(click.style(message, fg='white'))
    click.echo()


def error(title: str, message: str):
    """Display error message."""
    click.echo()
    click.echo(click.style("✖ ", fg='red', bold=True) + click.style(title, fg='red', bold=True))
    click.echo(click.style(message, fg='red'))
    click.echo()


def warning(message: str):
    """Display warning message."""
    click.echo(click.style("⚠ ", fg='yellow', bold=True) + click.style(message, fg='yellow'))


def info(message: str):
    """Display info message."""
    click.echo(click.style("ℹ ", fg='blue') + click.style(message, fg='blue'))


@contextmanager
def spinner(message: str):
    """
    Context manager for showing a spinner with a message.

    Usage:
        with spinner("Doing something...") as s:
            # do work
            s.ok("Done!")
    """
    class Spinner:
        def __init__(self, msg):
            self.msg = msg
            self._done = False
            click.echo(click.style("⟳ ", fg='cyan') + click.style(msg, fg='cyan'), nl=False)
            sys.stdout.flush()

        def ok(self, success_msg: str):
            if not self._done:
                click.echo("" + click.style("✔ ", fg='green', bold=True) + click.style(success_msg, fg='green'))
                self._done = True

        def fail(self, error_msg: str):
            if not self._done:
                click.echo("" + click.style("✖ ", fg='red', bold=True) + click.style(error_msg, fg='red'))
                self._done = True

    s = Spinner(message)
    try:
        yield s
        if not s._done:
            s.ok(message.replace("...", " completed"))
    except Exception as e:
        if not s._done:
            s.fail(str(e))
        raise
