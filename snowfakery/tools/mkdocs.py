import sys
from pathlib import Path
from importlib import import_module
from unittest.mock import patch

from mkdocs.plugins import BasePlugin
import mkdocs


class Plugin(BasePlugin):
    config_scheme = (
        ("build_locales", mkdocs.config.config_options.Type(bool, default=False)),
    )

    def on_config(self, config):
        """Look for and load main_mkdocs_plugin in tools/faker_docs_utils/mkdocs_plugins.py
        This bootstrap plugin is needed because that other one is never "installed"
        It is just present in the repo. So it can't have an official entry point
        in setup.py.
        """
        docs_dir = config["docs_dir"]
        plugins_dir = Path(docs_dir).parent / "tools/faker_docs_utils/mkdocs_plugins"
        new_sys_path = [*sys.path, str(plugins_dir)]
        with patch.object(sys, "path", new_sys_path):
            module = import_module("main_mkdocs_plugin")
            main_plugin = module.Plugin()
            config["plugins"]["main_mkdocs_plugin"] = main_plugin
            main_plugin.config = self.config
            main_plugin.on_config(config)
