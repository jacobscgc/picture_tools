import random


class TagCategories:

    colors = ['#ffdab9', '#8b7765', '#ffe4e1', '#000000', '#2f4f4f', '#696969', '#708090', '#191970', '#6495ed',
              '#483d8b', '#6a5acd', '#0000cd', '#00bfff', '#00ced1', '#00ffff', '#006400', '#556b2f', '#8fbc8f',
              '#3cb371', '#98fb98', '#7cfc00', '#32cd32', '#ffff00', '#ffd700', '#daa520', '#bc8f8f', '#8b4513',
              '#cd853f', '#a52a2a', '#fa8072', '#ffa500', '#ff8c00', '#f08080', '#ff0000', '#ff69b4', '#ff1493',
              '#b03060', '#d02090', '#ba55d3', '#a020f0']
    colors_used = []

    tag_categories = {}

    def __init__(self):
        pass

    def add_tag_category(self, category, col=None):
        """
        This function adds a new tag category to the tag categories dictionary.
        It updates the tag_categories dictionary.
        :param category: new tag category to be added (string)
        :param col: color string (optional)
        :return: Updates tag_categories dictionary.
        """
        if category not in self.tag_categories:
            if col is None:
                col = self.select_color()
            self.tag_categories[category] = col

    def remove_tag_category(self, category):
        """
        This function removes an existing category from the tag categories. It also frees the color used for that
        category. It updates the tag_categories dictionary.
        :param category: the tag category to be removed (string)
        :return: Updates tag_categories dictionary.
        """
        if category in self.tag_categories:
            self.free_color(category)
            del self.tag_categories[category]

    def change_tag_color(self, category, color):
        """
        This function replaces the color used currently for the category with the one provided in this function.
        It adds the supplied color to the colors_used list if not already present and removes the previously used
        color from this list (freeing it for subsequent use).
        :param category: the tag category for which the color should be replaced (string)
        :param color: the color which is to be used (string)
        :return: Updates the tag_categories dictionary.
        """
        if category in self.tag_categories:
            self.free_color(category)
            self.tag_categories[category] = color
            if color not in self.colors_used:
                self.colors_used.append(color)

    def rename_tag_category(self, old_category, new_category):
        """
        This function replaces an old category name with a new one.
        :param old_category: the old tag category to be replaced (string)
        :param new_category: the new tag category to replace it with (string)
        :return: Updates the tag_categories dictionary.
        """
        if old_category in self.tag_categories:
            col = self.tag_categories[old_category]
            del self.tag_categories[old_category]
            self.tag_categories[new_category] = col

    def free_color(self, category):
        """
        This function extract the color for a category and frees it for subsequent use again
        (if category is removed for example).
        :param category: the tag category for which the color should be freed again (string)
        :return: Updates the colors_used list.
        """
        if category in self.tag_categories:
            col = self.tag_categories[category]  # get used color
            self.colors_used = [i for i in self.colors_used if i != col]  # removes the color from the used colors

    def select_color(self):
        """
        This function selects a random color from the colors list if that color has not been used already.
        If all colors have been used once, it resets the colors_used list, re-using any previously used colors again.
        :return: A random unused color.
        """
        if len(self.colors_used) == len(self.colors):
            self.colors_used = []  # all colors have been used, reset colors_used.
        available_colors = [i for i in self.colors if i not in self.colors_used]
        col = random.choice(available_colors)
        self.colors_used.append(col)
        return col
