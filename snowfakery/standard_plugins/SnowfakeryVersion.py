from snowfakery import SnowfakeryPlugin
from snowfakery.plugins import PluginOption

plugin_options_version = (
    "snowfakery.standard_plugins.SnowfakeryVersion.snowfakery_version"
)


class SnowfakeryVersion(SnowfakeryPlugin):
    allowed_options = [
        PluginOption(plugin_options_version, int),
    ]
