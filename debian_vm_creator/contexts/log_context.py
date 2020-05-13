import click

from .base_context import BaseContext


class LogContext(BaseContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color_error = "red"
        self.color_message = "cyan"
        self.color_debug = "blue"

    def error(self, template, *args, **kwargs):
        click.secho(template.format(*args, **kwargs), fg=self.color_error, err=True)
        return self

    def message(self, template, *args, **kwargs):
        click.secho(template.format(*args, **kwargs), fg=self.color_message)
        return self

    def debug(self, template, *args, **kwargs):
        if self.ctx.global_config.debug:
            click.secho(template.format(*args, **kwargs), fg=self.color_debug, dim=True)
        return self
