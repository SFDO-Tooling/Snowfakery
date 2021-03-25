from snowfakery.plugins import ParserMacroPlugin
from snowfakery.data_generator_runtime_object_model import (
    ObjectTemplate,
    FieldFactory,
    SimpleValue,
    ReferenceValue,
)
from snowfakery import data_gen_exceptions as exc


class Salesforce(ParserMacroPlugin):
    def SpecialObject(self, context, args) -> ObjectTemplate:
        """Currently there is only one special object defined: PersonContact"""
        sobj, nickname = self._parse_special_args(args)
        line_info = context.line_num()
        if sobj == "PersonContact":
            return self._render_person_contact(context, sobj, nickname, line_info)
        else:
            raise exc.DataGenError(
                f"Unknown special object '{sobj}'. Did you mean 'PersonContact'?",
                None,
                None,
            )

    def _render_person_contact(self, context, sobj, nickname, line_info):
        """Generate the code to render a person contact as CCI expects.

        Code generation is a better strategy for this than a runtime
        plugin because some analysis of the table structures happens
        at parse time.
        """
        fields = [
            FieldFactory(
                "IsPersonAccount",
                SimpleValue("true", **line_info),
                **line_info,
            ),
            FieldFactory(
                "AccountId",
                ReferenceValue("reference", ["Account"], **line_info),
                **line_info,
            ),
        ]
        new_template = ObjectTemplate(
            sobj,
            filename=line_info["filename"],
            line_num=line_info["line_num"],
            nickname=nickname,
            fields=fields,
        )
        context.register_template(new_template)
        return new_template

    def _parse_special_args(self, args):
        """Parse args of SpecialObject"""
        nickname = None
        if isinstance(args, str):
            sobj = args
        elif isinstance(args, dict):
            sobj = args["name"]
            if not isinstance(sobj, str):
                raise exc.DataGenError(
                    f"`name` argument should be a string {sobj}: {type(sobj)}"
                )
            nickname = args.get("nickname")
            if nickname and not isinstance(nickname, str):
                raise exc.DataGenError(
                    f"`nickname` argument should be a string {nickname}: {type(sobj)}"
                )

        return sobj, nickname
