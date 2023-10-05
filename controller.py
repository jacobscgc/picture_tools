from natsort import natsorted
import operator
import math
from PIL import Image, ImageTk

# Picture tools modules:
from image_catalog import ImageCatalog
from grid import Grid


class Controller:

    image_dict = {}  # keep track of the link between image_file_name (key) and image_id (value).

    def __init__(self):
        self.catalog = ImageCatalog()
        self.grid = Grid()

    def open_folder(self, folder_location):
        """
        This function sends a command to the image_catalog to import the images present in [folder_location].
        :param folder_location: Absolute path to folder location to import images from.
        """
        self.catalog.open_folder(folder_location)

    def retrieve_images_present_in_catalog(self, sort_images='date_taken'):
        """
        This function retrieves the image_file_names of the images present in the image_catalog. It returns a sorted
        list. Default sorting is on the date the image was taken.
        This function also (re-)creates a dictionary linking image_file_names to image_id's.
        :param sort_images: on what the images should be sorted ('date_taken' or 'image_file_name').
        :return: sorted image name list.
        """
        # Get images from image catalog:
        image_list = [(image_id, self.catalog.images[image_id].file_name, self.catalog.images[image_id].date_taken) for
                      image_id in self.catalog.images]
        # (re-)create a dictionary linking image_id's to image_file_names:
        self.image_dict = {}
        for entry in image_list:
            self.image_dict[entry[1]] = entry[0]
        # Sort:
        if sort_images == 'date_taken':
            image_list.sort(key=operator.itemgetter(2))  # sort on date
            image_list = [i[1] for i in image_list]
        else:
            image_list = [i[1] for i in image_list]
            image_list = natsorted(image_list)

        return image_list

    def retrieve_image_object(self, image_file_name):
        """Returns the image_object for a given image_file_name"""
        image_id = self.image_dict[image_file_name]

        return self.catalog.images[image_id]

    def retrieve_image(self, image_file_name, resolution):
        """
        This function retrieves an image object and resizes it to a certain resolution.
        It returns a PIL image.
        :param image_file_name: The image file name.
        :param resolution: The resolution to resize the image to.
        :return: PIL image object.
        """
        pil_image = None
        if image_file_name in self.image_dict:
            pil_image = self.scale_image(image_file_name, resolution)
            pil_image = ImageTk.PhotoImage(pil_image)
            
        return pil_image

    def retrieve_tags(self, image_file_name):
        """
        This function retrieves the tags for the image with image_file_name.
        It returns a dictionary of tags with [tag_category] = [xmin, ymin, xmax, ymax].
        """
        tags = None
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            tags = self.catalog.images[image_id].tags.tag_dict

        return tags

    def retrieve_tag_categories(self):
        """This function extracts all tag_categories present in the catalog and returns them as a list."""
        tag_dict = self.catalog.tag_categories.tag_categories
        category_list = [key for key, value in tag_dict.items()]

        return category_list

    def close_all_images(self):
        """Closes all images in the image catalog"""
        self.catalog.close_all_images()

    def retrieve_tag_category_color(self, tag_category):
        """
        Retrieves the color that belongs to a certain tag_category.
        :param tag_category: The tag_category.
        :return: The color (HEX).
        """
        return self.catalog.tag_categories.tag_categories[tag_category]

    def retrieve_image_date_taken(self, image_file_name):
        """
        This function gets the date the image was taken as a string and returns this string.
        :param image_file_name: image_file_name
        :return: datestring
        """
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            date_taken = self.catalog.images[image_id].date_taken
            return date_taken.strftime('%m/%d/%Y %H:%M:%S')

    def check_limit(self):
        """ This function checks whether the image limit has been reached. """
        if self.catalog.ulimit == self.catalog.images_loaded - 1:  # no more new images can be loaded
            return True
        else:
            return False

    def add_tag_category(self, tag_category, color=None):
        """
        This function sends a command to add a tag_category.
        """
        self.catalog.tag_categories.add_tag_category(tag_category, color)

    def remove_tag_category(self, tag_category):
        """
        This function sends a command to remove a tag_category.
        """
        self.catalog.tag_categories.remove_tag_category(tag_category)

    def extract_entries_for_tag_category(self, tag_category, delete=False, replace=False, replace_category=None):
        """Extracts number of times a tag of tag_category occurs and deletes tags if delete=True."""
        if delete:
            self.catalog.extract_entries_for_tag_category(tag_category, True)
        elif replace:
            count = self.catalog.extract_entries_for_tag_category(tag_category, False, True, replace_category)
            return count
        else:
            count = self.catalog.extract_entries_for_tag_category(tag_category, delete)
            return count

    def add_tag(self, image_file_name, tag_category, coordinates=None):
        """
        This function sends a command to add a tag to an image.
        :param image_file_name: The image_file_name of the image to tag.
        :param tag_category: The tag_category.
        :param coordinates: The coordinates of the tag (Optional).
        """
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            self.catalog.images[image_id].tags.add_tag(tag_category, coordinates)

    def remove_tag(self, image_file_name, tag_id):
        """
        This function removes a tag using its tag_id.
        :param image_file_name: the currently selected image from which to remove the tag
        :param tag_id: the tag_id of the tag to remove
        """
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            self.catalog.images[image_id].tags.remove_tag(tag_id)

    def modify_tag(self, image_file_name, tag_id, new_tag_category):
        """
        This function replaces the tag_category of a tag using its tag_id and a new_tag_category.
        :param image_file_name: the currently selected image from which to modify the tag
        :param tag_id: the tag_id of the tag to modify
        :param new_tag_category: the new tag_category to use
        """
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            self.catalog.images[image_id].tags.modify_tag(tag_id, new_tag_category)

    def scale_image(self, image_file_name, resolution):
        """
        Takes an PIL image as input and returns a resized image while keeping the aspect ratio.
        :param image_file_name: image_file_name
        :param resolution: resolution tuple, example: (1920, 1080)
        :return: resized PIL image instance
        """
        ratio, pil_image = self.calculate_ratio(image_file_name, resolution)
        if ratio is not None and pil_image is not None:
            resized_width = math.floor(ratio * pil_image.size[0])
            resized_height = math.floor(ratio * pil_image.size[1])

            if ratio < 1:  # downsizing, use ANTIALIAS
                pil_image = pil_image.resize((resized_width, resized_height), Image.LANCZOS)
            else:  # increasing size:
                pil_image = pil_image.resize((resized_width, resized_height), Image.BICUBIC)

            return pil_image

    def calculate_ratio(self, image_file_name, resolution):
        """
        Takes an PIL image as input and returns the ratio which should be used to resize the image while keeping its
        ratio.
        :param image_file_name: image_file_name
        :param resolution: resolution tuple, example: (1920, 1080)
        :return: ratio
        """
        ratio, pil_image = None, None
        if image_file_name in self.image_dict:
            image_id = self.image_dict[image_file_name]
            pil_image = self.catalog.images[image_id].IMG
            width, height = pil_image.size
            goal_width, goal_height = resolution[0], resolution[1]
            ratio_width = goal_width / width
            ratio_height = goal_height / height
            ratio = min([ratio_width, ratio_height])

        return ratio, pil_image

    def canvas_coords_to_image_coords(self, canvas_coords, canvas_grid_size, pil_image, ratio, image_size):
        """
        This function calls the grid method to calculate image coordinates from canvas coordinates.
        """
        return self.grid.canvas_coords_to_image_coords(canvas_coords, canvas_grid_size, pil_image, ratio, image_size)

    def image_coords_to_canvas_coords(self, image_coords, canvas_grid_size, pil_image, ratio):
        """
        This function calls the grid method to calculate canvas coordinates from image coordinates.
        """
        return self.grid.image_coords_to_canvas_coords(image_coords, canvas_grid_size, pil_image, ratio)

    def save_progress(self, save_location, settings):
        """
        Saves progress to file.
        """
        self.catalog.save_progress(save_location, settings)

    def load_savefile(self, savefile_location):
        """
        Loads progress from savefile.
        """
        selected_image, taglinewidth, savefile_location, min_tagsize, sorting_method = \
            self.catalog.load_savefile(savefile_location)

        return selected_image, taglinewidth, savefile_location, min_tagsize, sorting_method

    def write_to_csv(self, filename, data):
        """Writes data to a csv file."""
        self.catalog.file_access.write_to_csv(filename, data)

    def read_csv(self, filename, delimiter):
        """Reads data from a csv into a list."""
        data = self.catalog.file_access.read_csv(filename, delimiter)

        return data

    def export_tagged_images(self, save_location, tag_categories=None):
        """
        This function export all images with tags to a save_location and renames them. If save_location already
        contains images, it will continue numbering from where it was. Images without tags are not exported.
        """
        self.catalog.export_tagged_images(save_location, tag_categories=tag_categories, rename=True)

    def rename_tag_category(self, tag_category, new_tag_category):
        """Renames tag_category to new_tag_category"""
        self.catalog.tag_categories.rename_tag_category(tag_category, new_tag_category)

    def change_tag_category_color(self, tag_category, color):
        """Modifies the color of a tag_category"""
        self.catalog.tag_categories.change_tag_color(tag_category, color)

    def delete_image(self, selected_image, from_disk=False):
        """Deletes a single image from the image_list, also from disk if from_disk=True"""
        image_id = self.image_dict[selected_image]
        self.catalog.delete_image_from_catalog(image_id, from_disk)
