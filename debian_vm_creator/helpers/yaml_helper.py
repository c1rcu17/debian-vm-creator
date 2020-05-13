import click
import yaml

from .exception_helper import AppException

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper  # type: ignore
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader  # type: ignore


class YamlException(AppException):
    pass


def yaml_load(*, stream=None, file_name=None):
    if stream is None:
        if file_name is None:
            raise YamlException("Nothing to load")

        with open(file_name, "r") as file_descriptor:
            return yaml_load(stream=file_descriptor, file_name=file_name)

    try:
        return yaml.load(stream, Loader=Loader)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as error:
        parse_source = "file: " + file_name if file_name is not None else type(stream).__name__
        raise YamlException("Could not parse {}: {}".format(parse_source, error))


def yaml_dump(data, *, stream=None, file_name=None):
    if stream is None and file_name is not None:
        with open(file_name, "w") as file_descriptor:
            return yaml_dump(data, stream=file_descriptor, file_name=file_name)

    return yaml.dump(data, stream=stream, Dumper=Dumper)


class YamlFileParamType(click.File):
    name = "yamlfile"

    def __init__(self):
        super().__init__()

    def convert(self, value, param, ctx):
        file_descriptor = super().convert(value, param, ctx)

        try:
            return yaml_load(stream=file_descriptor, file_name=value)
        except (YamlException) as error:
            return self.fail(error, param, ctx)


YAML_FILE = YamlFileParamType()
