class Tags:

    def __init__(self, tag_categories, image_size):
        self.tag_dict = {}
        self.tag_id = 0
        self.tag_categories = tag_categories
        # use the image_size to set a full_image_coordinates list to use when no coordinates have been provided to
        # create a tag (complete image is tagged):
        self.full_image_coordinates = [0, 0, image_size[0], image_size[1]]

    def add_tag(self, tag_category, coordinates=None):
        """
        This function adds a Tag object to the tag dictionary using a unique id
        (id's are unique for each image but not between images).
        If no coordinates are given, the size of the image is used (entire image is tagged).
        :param tag_category: A tag_category to add.
        :param coordinates: A list of image coordinates defining the bounding box of this tag [xmin, ymin, xmax, ymax]
        (Optional)
        :return: Adds a Tag object to the tag_dict.
        """
        if coordinates is None:
            coordinates = self.full_image_coordinates
        # Check whether tag_category already exists, if not, add:
        if tag_category not in self.tag_categories.tag_categories:
            self.tag_categories.add_tag_category(tag_category)
        tags = [(i.tag_category, i.coordinates) for i in self.tag_dict.values()]
        if (tag_category, coordinates) not in tags:  # only add when not already present
            self.tag_dict[self.tag_id] = Tag(tag_category, coordinates)
            self.tag_id += 1  # increment the id to keep them unique

    def remove_tag(self, tag_id):
        """
        This function deletes a Tag object from the tag_dict using [tag_id].
        :param tag_id: tag_id to delete
        :return: Deleted the tag_id from the tag_dict.
        """
        del self.tag_dict[tag_id]

    def modify_tag(self, tag_id, tag_category):
        """
        This function modifies the tag_category of the Tag object [tag_id].
        :param tag_id: tag_id of the Tag object to modify
        :param tag_category: new tag_category with which to replace the old one
        :return: Modified the tag_category.
        """
        tag_object = self.tag_dict[tag_id]
        tag_object.tag_category = tag_category
        self.tag_dict[tag_id] = tag_object


class Tag:

    def __init__(self, tag_category, coordinates):
        self.tag_category = tag_category
        self.coordinates = coordinates
