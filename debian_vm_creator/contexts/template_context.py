import jinja2

from ..helpers import AppException
from .base_context import BaseContext


class TemplateException(AppException):
    pass


class TemplateContext(BaseContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_options = {"undefined": jinja2.StrictUndefined, "keep_trailing_newline": True}

    def render(self, template, *args, **kwargs):
        try:
            return jinja2.Template(template, **self.template_options).render(*args, **kwargs)
        except jinja2.exceptions.UndefinedError as error:
            raise TemplateException("Template render error: {}".format(error))

    def render_to_file(self, template, filename, *args, **kwargs):
        filename = self.ctx.execution.chroot_path(filename)
        contents = self.render(template, *args, **kwargs)

        with open(filename, "w") as stream:
            stream.write(contents)
