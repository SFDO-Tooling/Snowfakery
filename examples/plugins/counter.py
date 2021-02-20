from snowfakery.plugins import SnowfakeryPlugin


class CountUpPlugin(SnowfakeryPlugin):
    class Functions:
        all_counters = {}

        def counter(self):
            unique_id = self.context.unique_context_identifier()
            self.all_counters[unique_id] = self.all_counters.get(unique_id, 0) + 1
            return self.all_counters[unique_id]
