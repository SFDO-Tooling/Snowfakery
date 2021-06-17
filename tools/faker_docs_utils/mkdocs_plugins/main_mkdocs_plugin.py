from pathlib import Path
import sys
import os
from unittest.mock import patch
from functools import lru_cache

from mkdocs.plugins import BasePlugin
from faker.factory import Factory


class Plugin(BasePlugin):
    def on_config(self, config):
        pass

    def on_pre_build(self, config):
        root_dir = Path(__file__).parent.parent.parent.parent
        faker_docs_dir = root_dir / "docs/fakedata"
        faker_docs_dir.mkdir(exist_ok=True)
        new_sys_path = [*sys.path, str(root_dir)]
        print("Note: Hiding warnings during build", __file__)

        # make modules available
        sys_path_patch = patch.object(sys, "path", new_sys_path)

        # speed up a critical function
        lru_patch = patch(
            "faker.factory.Factory._get_provider_class",
            lru_cache(maxsize=10_000)(Factory._get_provider_class),
        )

        with sys_path_patch, lru_patch:
            from tools.faker_docs_utils.faker_markdown import (
                generate_markdown_for_all_locales,
                generate_markdown_for_fakers,
                generate_locales_index,
            )

            fakerdocs_md_header = (
                root_dir / "tools/faker_docs_utils/fakedata_header_full.md"
            )
            main_header = Path(fakerdocs_md_header).read_text()
            fakerdocs_md = root_dir / "docs/fakedata.md"
            with fakerdocs_md.open("w") as f:
                generate_markdown_for_fakers(f, "en_US", main_header)

            build_locales_env = os.environ.get("SF_MKDOCS_BUILD_LOCALES")
            if build_locales_env:
                build_locales = build_locales_env != "False"
            else:
                build_locales = self.config.get("build_locales")

            if build_locales:
                generate_markdown_for_all_locales(faker_docs_dir)
                generate_locales_index("docs/locales.md")
