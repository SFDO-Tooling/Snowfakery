from os import fsdecode
from numbers import Number
from datetime import date
from contextlib import contextmanager
from collections import namedtuple
from pathlib import Path
from typing import IO, List, Dict, Union, Tuple, Any, Iterable, Sequence, Mapping

import yaml
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.error import YAMLError

from .data_generator_runtime_object_model import (
    ObjectTemplate,
    VariableDefinition,
    FieldFactory,
    SimpleValue,
    StructuredValue,
    ReferenceValue,
    Statement,
)

from snowfakery.plugins import resolve_plugin
import snowfakery.data_gen_exceptions as exc

SHARED_OBJECT = "#SHARED_OBJECT"

TemplateLike = Union[ObjectTemplate, StructuredValue]
###
#   The entry point to this is parse_recipe

LineTracker = namedtuple("LineTracker", ["filename", "line_num"])


class ParseResult:
    def __init__(
        self, options, tables: Mapping, statements: Sequence, plugins: Sequence = ()
    ):
        self.options = options
        self.tables = tables
        self.statements = statements
        self.templates = [obj for obj in statements if isinstance(obj, ObjectTemplate)]
        self.plugins = plugins


class TableInfo:
    """Information we can infer about the table schema based on the templates.

    Note that a table can be referred to in more than one place, so this class
    unifies what we know about it.
    """

    def __init__(self, name):
        self.name = name
        self.fields = {}
        self.friends = {}
        self._templates = []

    def register(self, template: ObjectTemplate) -> None:
        self.fields.update(
            {
                field.name: field
                for field in template.fields
                if not field.name.startswith("__")
            }
        )
        self.friends.update(
            {
                friend.tablename: friend
                for friend in template.friends
                if hasattr(friend, "tablename")
            }
        )
        self._templates.append(template)

    def __repr__(self) -> str:
        return f"<TableInfo fields={list(self.fields.keys())} friends={list(self.friends.keys())} templates={len(self._templates)}>"


class ParseContext:
    current_parent_object = None

    def __init__(self):
        self.macros = {}
        self.plugins = []
        self.line_numbers = {}
        self.options = []
        self.table_infos = {}

    def line_num(self, obj=None) -> Dict:
        if not obj:
            obj = self.current_parent_object
            assert obj

        # dicts should have __line__ keys
        try:
            return obj["__line__"]._asdict()
        except TypeError:
            pass

        # strings (and perhaps some other non-dict objects) should be tracked in
        # the line_numbers system
        try:
            my_line_num = self.line_numbers.get(id(obj))
            if my_line_num and my_line_num != SHARED_OBJECT:
                return my_line_num._asdict()
        except KeyError:
            pass

        assert obj != self.current_parent_object  # check for no infinite loop
        return self.line_num(self.current_parent_object)

    @contextmanager
    def change_current_parent_object(self, obj: Dict):
        _old_parsed_template = self.current_parent_object
        self.current_parent_object = obj
        try:
            yield
        except exc.DataGenError:
            raise
        except Exception as e:
            raise exc.DataGenSyntaxError(str(e), **self.line_num()) from e
        finally:
            self.current_parent_object = _old_parsed_template

    def register_template(self, template: ObjectTemplate) -> None:
        """Register templates for later use.

        We register templates so we can get a list of all fields that can
        be generated. This can be used to create a dynamic schema.
        """
        table_info = self.table_infos.get(template.tablename, None) or TableInfo(
            template.tablename
        )
        self.table_infos[template.tablename] = table_info
        table_info.register(template)


def removeline_numbers(dct: Dict) -> Dict:
    return {i: dct[i] for i in dct if i != "__line__"}


def parse_structured_value_args(
    args, context: ParseContext
) -> Union[List, Dict, SimpleValue, StructuredValue, ObjectTemplate]:
    """Structured values can be dicts or lists containing simple values or further structure."""
    if isinstance(args, dict):
        with context.change_current_parent_object(args):
            return {
                name: parse_field_value(name, arg, context, False)
                for name, arg in args.items()
                if name != "__line__"
            }
    elif isinstance(args, list):
        return [
            parse_field_value(f"List element {i}", arg, context, False)
            for i, arg in enumerate(args)
        ]
    else:
        return parse_field_value("", args, context, False)


def parse_structured_value(
    name: str, field: Dict, context: ParseContext
) -> StructuredValue:
    """Parse something that might look like:

    {'choose': ['Option1', 'Option2', 'Option3', 'Option4'], '__line__': 9}

    or

    {'random_number': {'min': 10, 'max': 20, '__line__': 10} , '__line__': 9}
    """
    top_level = removeline_numbers(field).items()
    if not top_level:
        raise exc.DataGenSyntaxError(
            f"Strange datastructure ({field})", **context.line_num(field)
        )
    elif len(top_level) > 1:
        raise exc.DataGenSyntaxError(
            f"Extra keys for field {name} : {top_level}", **context.line_num(field)
        )
    [[function_name, args]] = top_level
    args = parse_structured_value_args(args, context)
    if function_name == "reference":
        return ReferenceValue(function_name, args, **context.line_num(field))
    else:
        return StructuredValue(function_name, args, **context.line_num(field))


def parse_field_value(
    name: str, field, context: ParseContext, allow_structured_values=True
) -> Union[SimpleValue, StructuredValue, ObjectTemplate]:
    if isinstance(field, (str, Number, date, type(None))):
        return SimpleValue(field, **(context.line_num(field) or context.line_num()))
    elif isinstance(field, dict) and field.get("object"):
        with context.change_current_parent_object(field):
            return parse_object_template(field, context)
    elif isinstance(field, dict):
        return parse_structured_value(name, field, context)
    elif isinstance(field, list) and len(field) == 1 and isinstance(field[0], dict):
        # unwrap a list of a single item in this context because it is
        # a mistake and we can infer their real meaning
        return parse_field_value(name, field[0], context)
    else:
        raise exc.DataGenSyntaxError(
            f"Unknown field {type(field)} type for {name}. Should be a string or 'object': \n {field} ",
            **(context.line_num(field) or context.line_num()),
        )


def parse_field(name: str, definition, context: ParseContext) -> FieldFactory:
    assert name, name
    return FieldFactory(
        name,
        parse_field_value(name, definition, context),
        **context.line_num(definition),
    )


def parse_fields(fields: Dict, context: ParseContext) -> List[FieldFactory]:
    with context.change_current_parent_object(fields):
        if not isinstance(fields, dict):
            raise exc.DataGenSyntaxError(
                "Fields should be a dictionary (should not start with -) ",
                **context.line_num(),
            )
        return [
            parse_field(name, definition, context)
            for name, definition in fields.items()
            if name != "__line__"
        ]


def parse_friends(friends: List, context: ParseContext) -> List[Statement]:
    return parse_statement_list(friends, context)


def parse_count_expression(yaml_sobj: Dict, sobj_def: Dict, context: ParseContext):
    sobj_def["count_expr"] = parse_field_value("count", yaml_sobj["count"], context)


def include_macro(
    name: str, context: ParseContext, parent_macros=()
) -> Tuple[List[FieldFactory], List[TemplateLike]]:
    macro = context.macros.get(name)
    if not macro:
        raise exc.DataGenNameError(
            f"Cannot find macro named {name}", **context.line_num()
        )
    parsed_macro = parse_element(
        macro, "macro", {}, {"fields": Dict, "friends": List, "include": str}, context
    )
    fields = parsed_macro.fields or {}
    friends = parsed_macro.friends or []
    fields, friends = parse_fields(fields, context), parse_friends(friends, context)
    if name in parent_macros:
        idx = parent_macros.index(name)
        raise exc.DataGenError(
            f"Macro `{name}` calls `{'` which calls `'.join(parent_macros[idx+1:])}` which calls `{name}`",
            **context.line_num(macro),
        )
    parse_inclusions(macro, fields, friends, context, parent_macros + (name,))
    return fields, friends


def parse_inclusions(
    yaml_sobj: Dict,
    fields: List,
    friends: List,
    context: ParseContext,
    parent_macros=(),
) -> None:
    inclusions: Iterable[str] = [
        x.strip() for x in yaml_sobj.get("include", "").split(",")
    ]
    inclusions = filter(None, inclusions)
    for inclusion in inclusions:
        include_fields, include_friends = include_macro(
            inclusion, context, parent_macros
        )
        fields.extend(include_fields)
        friends.extend(include_friends)


def parse_object_template(yaml_sobj: Dict, context: ParseContext) -> ObjectTemplate:
    parsed_template: Any = parse_element(
        dct=yaml_sobj,
        element_type="object",
        mandatory_keys={},
        optional_keys={
            "fields": Dict,
            "friends": List,
            "include": str,
            "nickname": str,
            "just_once": bool,
            "count": (str, int, dict),
        },
        context=context,
    )

    assert yaml_sobj
    with context.change_current_parent_object(yaml_sobj):
        sobj_def = {}
        sobj_def["tablename"] = parsed_template.object
        fields: List
        friends: List
        sobj_def["fields"] = fields = []
        sobj_def["friends"] = friends = []
        parse_inclusions(yaml_sobj, fields, friends, context)
        fields.extend(parse_fields(parsed_template.fields or {}, context))
        friends.extend(parse_friends(parsed_template.friends or [], context))
        sobj_def["nickname"] = parsed_template.nickname
        sobj_def["just_once"] = parsed_template.just_once or False
        sobj_def["line_num"] = parsed_template.line_num.line_num
        sobj_def["filename"] = parsed_template.line_num.filename

        count_expr = yaml_sobj.get("count")

        if count_expr is not None:
            parse_count_expression(yaml_sobj, sobj_def, context)
        new_template = ObjectTemplate(**sobj_def)
        context.register_template(new_template)
        return new_template


def parse_variable_definition(
    yaml_sobj: Dict, context: ParseContext
) -> VariableDefinition:
    parsed_template: Any = parse_element(
        yaml_sobj,
        "var",
        {},
        {
            "value": (str, int, dict, list),
        },
        context,
    )

    assert yaml_sobj
    with context.change_current_parent_object(yaml_sobj):
        sobj_def = {}
        sobj_def["varname"] = parsed_template.var
        var_def_expr = yaml_sobj.get("value")

        sobj_def["expression"] = parse_field_value("value", var_def_expr, context)
        new_def = VariableDefinition(**sobj_def)
        return new_def


def parse_statement_list(
    statements: List[dict], context: ParseContext
) -> List[Statement]:
    parsed_statements = []
    for obj in statements:
        assert isinstance(obj, dict), obj
        if obj.get("object"):
            object_template = parse_object_template(obj, context)
            parsed_statements.append(object_template)
        elif obj.get("var"):
            variable_definition = parse_variable_definition(obj, context)
            parsed_statements.append(variable_definition)
        else:
            assert 0  # pragma: no cover

    return parsed_statements


def yaml_safe_load_with_line_numbers(
    filestream: IO[str], filename: str
) -> Tuple[object, Dict]:
    loader = yaml.SafeLoader(filestream)
    line_numbers: Dict[Any, LineTracker] = {}

    def compose_node(parent, index):
        # the line number where the previous token has ended (plus empty lines)
        line = loader.line
        node = Composer.compose_node(loader, parent, index)
        node.__line__ = line + 1
        return node

    def construct_mapping(node, deep=False):
        mapping = SafeConstructor.construct_mapping(loader, node, deep=deep)
        mapping["__line__"] = LineTracker(filename, node.__line__)
        return mapping

    def construct_scalar(node):
        scalar = SafeConstructor.construct_scalar(loader, node)
        key = id(scalar)
        if not line_numbers.get(key):
            line_numbers[key] = LineTracker(filename, node.__line__)
        else:
            line_numbers[key] = SHARED_OBJECT
        return scalar

    loader.compose_node = compose_node  # type: ignore
    loader.construct_mapping = construct_mapping  # type: ignore
    loader.construct_scalar = construct_scalar  # type: ignore
    return loader.get_single_data(), line_numbers


class DictValuesAsAttrs:
    pass


def parse_element(
    dct: Dict,
    element_type: str,
    mandatory_keys: Dict,
    optional_keys: Dict,
    context: ParseContext,
) -> Any:
    expected_keys = {
        **mandatory_keys,
        **optional_keys,
        "__line__": LineTracker,
        element_type: str,
    }
    rc_obj: Any = DictValuesAsAttrs()
    rc_obj.line_num = dct["__line__"]
    with context.change_current_parent_object(dct):
        for key in dct:
            key_definition = expected_keys.get(key)
            if not key_definition:
                raise exc.DataGenError(
                    f"Unexpected key: {key}", **context.line_num(key)
                )
            else:
                value = dct[key]
                if not isinstance(value, key_definition):
                    raise exc.DataGenError(
                        f"Expected `{key}` to be of type {key_definition} instead of {type(value)}.",
                        **context.line_num(dct),
                    )
                else:
                    setattr(rc_obj, key, value)

        missing_keys = set(mandatory_keys) - set(dct.keys())
        if missing_keys:
            raise exc.DataGenError(
                f"Expected to see `{missing_keys}` in `{element_type}``.",
                **context.line_num(dct),
            )
        defaulted_keys = set(optional_keys) - set(dct.keys())
        for key in defaulted_keys:
            setattr(rc_obj, key, None)

        return rc_obj


def relpath_from_inclusion_element(
    inclusion: Dict, context: ParseContext
) -> Tuple[Path, LineTracker]:
    # should be a two-element dict: {'include_file': 'foo.yml', "__line__": 5}
    inclusion_parsed: Any = parse_element(inclusion, "include_file", {}, {}, context)
    relpath = inclusion_parsed.include_file
    linenum = inclusion_parsed.line_num or LineTracker("unknown", -1)
    assert not relpath.startswith("/")  # only relative paths
    return Path(relpath), linenum


def parse_included_file(
    parent_path: Path, inclusion: Dict, context: ParseContext
) -> List[Dict]:
    relpath, linenum = relpath_from_inclusion_element(inclusion, context)
    inclusion_path = parent_path.parent / relpath
    # someday add a check that we don't go outside of the project dir
    if not inclusion_path.exists():
        raise exc.DataGenError(
            f"Cannot load include file {inclusion_path}", **linenum._asdict()
        )
    with inclusion_path.open() as f:
        incl_objects = parse_file(f, context)
        return incl_objects


def parse_included_files(path: Path, data: List, context: ParseContext):
    file_inclusions = [obj for obj in data if obj.get("include_file")]

    templates = []
    for fi in file_inclusions:
        templates.extend(parse_included_file(path, fi, context))
    return templates


collection_rules = {
    "option": "option",
    "include_file": "include_file",
    "macro": "macro",
    "plugin": "plugin",
    "object": "statement",
    "var": "statement",
}


def categorize_top_level_objects(data: List, context: ParseContext):
    """Look at all of the top-level declarations and categorize them"""
    top_level_collections: Dict = {
        "option": [],
        "include_file": [],
        "macro": [],
        "plugin": [],
        "statement": [],  # objects with side-effects
    }
    assert isinstance(data, list)
    for obj in data:
        if not isinstance(obj, dict):
            raise exc.DataGenSyntaxError(
                f"Top level elements in a data generation template should all be dictionaries, not {obj}",
                **context.line_num(data),
            )
        obj_category = None
        for declaration, category in collection_rules.items():
            typ = obj.get(declaration)
            if typ:
                if obj_category:
                    raise exc.DataGenError(
                        f"Top level element seems to match two name patterns: {declaration, obj_category}",
                        **context.line_num(obj),
                    )
                obj_category = category
        if obj_category:
            top_level_collections[obj_category].append(obj)
        else:
            raise exc.DataGenError(
                f"Unknown object type {obj}", **context.line_num(obj)
            )
    return top_level_collections


def parse_top_level_elements(path: Path, data: List, context: ParseContext):
    top_level_objects = categorize_top_level_objects(data, context)
    statements: List[ObjectTemplate] = []
    statements.extend(parse_included_files(path, data, context))
    context.options.extend(top_level_objects["option"])
    context.macros.update({obj["macro"]: obj for obj in top_level_objects["macro"]})
    context.plugins.extend(
        [
            resolve_plugin(obj["plugin"], obj["__line__"])
            for obj in top_level_objects["plugin"]
        ]
    )
    statements.extend(top_level_objects["statement"])
    return statements


def parse_file(stream: IO[str], context: ParseContext) -> List[Dict]:
    stream_name = getattr(stream, "name", None)
    if stream_name:
        path = Path(fsdecode(stream.name)).absolute()
    else:
        path = Path("<stream>")
    try:
        data, line_numbers = yaml_safe_load_with_line_numbers(stream, str(path))
    except YAMLError as y:
        raise exc.DataGenYamlSyntaxError(
            str(y),
            str(path),
            y.problem_mark.line + 1,
        )
    context.line_numbers.update(line_numbers)

    if not isinstance(data, list):
        raise exc.DataGenSyntaxError(
            "Generator file should be a list (use '-' on top-level lines)",
            stream_name,
            1,
        )

    statements = parse_top_level_elements(path, data, context)

    return statements


def parse_recipe(stream: IO[str]) -> ParseResult:
    context = ParseContext()
    objects = parse_file(stream, context)
    statements = parse_statement_list(objects, context)
    tables = context.table_infos
    tables = {
        name: value
        for name, value in context.table_infos.items()
        if not name.startswith("__")
    }

    return ParseResult(context.options, tables, statements, plugins=context.plugins)
