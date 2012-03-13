def handle_examine(inven):
    pass

class Inventory(object):
    def __init__(self, owner):
        self.owner = owner
        self.items = []

    def categorized_view(self):
        """ categorized_view() => {category :[items]}
        Returns list of items divided by category
        """
        result = {}
        for item in self.items:
            category = item.category
            if not category:
                continue #items without category shouldn't be displayed
            if not category in result:
                result[category] = []
            result[category].append(item)
        return result



