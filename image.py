from PIL import Image as PilImage

# Picture tools modules:
from tags import Tags


class Image:

    def __init__(self, tag_categories, file_path, file_name, date_taken):
        self.file_location = file_path
        self.file_name = file_name
        self.IMG = PilImage.open(self.file_location + '/' + self.file_name)
        self.date_taken = date_taken
        self.date_string = self.date_taken.strftime('%Y:%m:%d %H:%M:%S')
        self.size = self.IMG.size
        self.tags = Tags(tag_categories, self.size)  # create a Tags object to save the tags for this image

    def crop(self, crop_coordinates):
        """
        This function crops the image using crop_coordinates, where crop_coordinates represent the part of the image
        to be kept.
        :param crop_coordinates: list of coordinates [xmin, ymin, xmax, ymax]
        :return: image has been cropped.
        """
        crop_section = (crop_coordinates[0], crop_coordinates[1], crop_coordinates[2], crop_coordinates[3])
        self.IMG = self.IMG.crop(crop_section)

    def rotate(self, direction):
        """
        This function rotates the image 90 degrees to the left or right.
        Image is not saved automatically! Call save_image from the image_catalog to save the rotated image.
        :param direction: 'left' or 'right'
        :return: rotated image
        """
        if direction == 'left':
            self.IMG = self.IMG.rotate(90, expand=1)
        if direction == 'right':
            self.IMG = self.IMG.rotate(-90, expand=1)
