from snowfakery import SnowfakeryPlugin


class RecipeStateDemo(SnowfakeryPlugin):
    class Functions:
        def show_recipe_state(self, _):
            print(dir(self.context))
            breakpoint()
            child_index = self.context.child_index
            current_obj_id = self.context.this.id
            fake_name = self.context.fake.Name()
            return f"""child_index: {child_index}
                    current_obj_id: {current_obj_id}
                    fake_name: {fake_name}"""
