var pyodide;

const snowfakery_ready_event = new Event("snowfakery_ready");

function loadLocal(package) {
  pyodide.loadPackage(new URL(package, document.baseURI));
}
async function main() {
  pyodide = await loadPyodide();
  var recipe_data;
  let load_recipe_data = fetch(
    "https://raw.githubusercontent.com/SFDO-Tooling/Snowfakery/main/examples/basic-salesforce.recipe.yml"
  )
    .then((response) => response.text())
    .then((data) => (recipe_data = data));

  await Promise.all([
    load_recipe_data,
    pyodide.loadPackage("micropip"),
    loadLocal("MarkupSafe-2.1.1-cp310-cp310-emscripten_wasm32.whl"),
    loadLocal("python_baseconv-1.2.2-py3-none-any.whl"),
    loadLocal("SQLAlchemy-1.4.36-cp310-cp310-emscripten_wasm32.whl"),
    pyodide.loadPackage(
      "https://files.pythonhosted.org/packages/bd/7f/b01c7bfc66b448867b0019b9407bd101a780c3d9e332dcac29c73fc0a039/snowfakery-3.1.0-py3-none-any.whl"
    ),
  ]);

  pyodide.globals.set("recipe_data", recipe_data);

  await pyodide.runPythonAsync(`
    import micropip

    await micropip.install(['pyyaml', 'faker', 'click', 'jinja2', 'pydantic'], keep_going=True)
    from io import StringIO
    from snowfakery import generate_data

    `);
  document.dispatchEvent(snowfakery_ready_event);
}
main();

function go() {
  let recipe_data = document.getElementById("myTextarea").value;
  pyodide.globals.set("recipe", recipe_data);
  out = pyodide.runPython(`
  from io import StringIO
  from snowfakery import generate_data

  out = StringIO()
  generate_data(StringIO(recipe), output_files=[out], output_format="txt")
  out.getvalue()
  `);
  document.getElementById("out").value = out;
}

function bench() {
  pyodide.runPythonAsync(`
  from io import StringIO
  import time
  from snowfakery import generate_data

  output_file = StringIO()
  x = time.time()
  generate_data(StringIO(recipe_data), target_number=[10000, "Account"], output_file = output_file, output_format="txt")
  print(time.time() - x)
  print(len(output_file.getvalue().split('\\n')))
      `);
  console.log("Running");
}
