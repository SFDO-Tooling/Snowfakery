import os
from glob import glob
from pathlib import Path
from unittest import mock

from snowfakery import generate_data


class TestContinuity:
    @mock.patch.dict(os.environ, {"SNOWFAKERY_DETERMINISTIC_FAKE": "True"})
    def test_files(self, tmpdir):
        errors = []
        for file in glob("**/*.recipe.yml", recursive=True):
            if "ContactsForAccounts.recipe.yml" in file:
                continue
            outfile = Path(file.replace("recipe.yml", "recipe.out.txt"))
            tempfile = Path(tmpdir) / "temp_recipe.out.txt"
            tempfile = tempfile
            generate_data(
                yaml_file=file,
                output_file=tempfile,
            )
            new_data = tempfile.read_text()
            if outfile.exists():
                prev_data = outfile.read_text()
                if prev_data != new_data:
                    newoutfile = Path(file.replace("recipe.yml", "recipe.out.new.txt"))
                    newoutfile.write_text(new_data)
                    errors.append((outfile, newoutfile))
            else:
                outfile.write_text(new_data)

        if errors:
            print()
            print(" == Files that changed ==")
            for old, new in errors:
                print(old, "->", new)
                # os.system(f"diff {old} {new}")
            raise AssertionError()
