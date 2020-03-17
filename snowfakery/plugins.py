import snowfakery


class SnowfakeryPlugin:
    """Base class for all plugins.

    Currently plugins can declare new functions. Over time new superpowers
    for plugins will be introduced.

    Plugins generally look like this:

    class MyPlugin:
        class Functions: # must be named `Functions`.
            def func1(self, arg1, arg2, arg3=default):
                return something()

    This function would be invoked through the name `MyPlugin.func1()`

    Despite the name, the Functions namespace could also include
    constants or other namespaces, if that is useful to you.

    A RuntimeContext object is supplied on `self.context` but its
    interface is not stable yet. Use at your own risk.
    """

    def custom_functions(
        self,
        context: "snowfakery.data_generator_runtime.RuntimeContext",
        *args,
        **kwargs
    ):
        "Instantiate, contextualize and return a function library"
        functions = self.Functions()
        functions.context = context
        return functions
