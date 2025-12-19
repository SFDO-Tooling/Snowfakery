from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginOption

plugin_options_version = (
    "snowfakery.standard_plugins.SnowfakeryVersion.snowfakery_version"
)


class SnowfakeryVersion(SnowfakeryPlugin):
    allowed_options = [
        PluginOption(plugin_options_version, int),
    ]

    def custom_functions(self, *args, **kwargs):
        """This plugin doesn't provide custom functions, only options."""
        return type("EmptyFunctions", (), {})()
