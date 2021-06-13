from tools.faker_docs_utils.faker_markdown import generate_markdown_for_fakers


outfile = "docs/fakedata/en_US.md"
with open(outfile, "w") as o:
    generate_markdown_for_fakers(o, "en_US")

outfile = "docs/fakedata/fr_FR.md"
with open(outfile, "w") as o:
    generate_markdown_for_fakers(o, "fr_FR")

print("DONE", outfile)
