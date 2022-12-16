import unittest
from unittest import mock
from PIL import Image
import numpy as np
from datetime import datetime

# Own modules (to be tested)
from image_catalog import ImageCatalog


class TestFunctions(unittest.TestCase):

    @staticmethod
    def return_input(in_var):
        """
        This function takes a variable as input and returns this variable again.
        It is used in mock constructors to check that the proper input has been given.
        :return: in_var
        """
        return in_var

    @staticmethod
    def create_image(filepath):
        """
        This function creates a simple image by converting a numpy array into a PIL image object.
        This can be used to test functionality of other aspect of picture tools.
        :return: PIL image object
        """
        # Create an array of only zero's:
        pixels = np.zeros((300, 300, 3))
        for i in range(300):
            for a in range(300):
                if i <= 150 and a <= 150:
                    pixels[i, a] = [255, 0, 0]
                elif a <= 150 < i:
                    pixels[i, a] = [0, 255, 0]
                elif i <= 150 < a:
                    pixels[i, a] = [0, 0, 255]
                else:
                    pixels[i, a] = [255, 255, 255]
        # Create an image from the array:
        im = Image.fromarray(pixels.astype('uint8'), 'RGB')
        im.filename = filepath

        return im

    # create a mock decorator for image.PilImage.open (in image.py) which returns the above created image instead
    @mock.patch('image.PilImage.open')
    def test_add_image(self, mock_pil_image):
        """
        This function tests add_image() from image_catalog.py
        So basically it tests whether the creation of an object of the Image class can be performed succesfully through
        calling add_image in the ImageCatalog.
        It creates an ImageCatalog object and then adds a PIL image object to the image catalog using the above
        described mock decorator. Adding one image to the catalog should lead to a catalog.images dictionary of length
        1. This is asserted.
        """
        mock_pil_image.side_effect = self.create_image
        catalog = ImageCatalog()
        date_taken = datetime(3000, 1, 1, 12, 00, 00)
        file_location = '/home/fakepath/'
        filename = 'fakefile1.jpg'
        catalog.add_image(file_location, filename, date_taken)

        # check that the image object is created correctly:
        self.assertEqual(file_location, catalog.images[0].file_location)  # check file location
        self.assertEqual(filename, catalog.images[0].file_name)  # check filename
        self.assertEqual(date_taken, catalog.images[0].date_taken)  # check datetime object
        self.assertEqual('3000:01:01 12:00:00', catalog.images[0].date_string)  # check date string
        self.assertEqual((300, 300), catalog.images[0].size)  # check that the size has been set correctly
        self.assertEqual(0, len(catalog.images[0].tags.tag_dict))  # check that an empty tag dictionary has been created
        self.assertEqual(1, len(catalog.images))  # check that only 1 object has been created
        # confirm that the right file was opened:
        self.assertEqual(file_location + '/' + filename, catalog.images[0].IMG.filename)

    @mock.patch('image.PilImage.Image.save')  # mock object for the PIL.Image.Image.save method in image.py
    @mock.patch('image.PilImage.open')  # mock object for the PIL.Image.open method in image.py
    def test_save_image(self, mock_pil_open, mock_save):
        """
        This function tests the save_image() function in image_catalog.py and data_acces.py.
        It uses a mock function to get a PIL image object and uses a second mock method to return the save location
        instead of actually calling the PIL save method. It then tests:
        1) Whether the save-method is actually called
        2) Whether the location with which the method is called is correct.
        """
        mock_pil_open.side_effect = self.create_image  # replaces the PIL open method with our create_image method
        mock_save.side_effect = self.return_input  # replaces the save method with return_input()
        catalog = ImageCatalog()
        # Add 2 fake files to the catalog:
        date_taken = datetime(3000, 1, 1, 12, 00, 00)
        catalog.add_image('/home/chris.jacobs', 'file1', date_taken)
        catalog.add_image('/home/chris.jacobs', 'file2.jpg', date_taken)
        # Try to save with and without location:
        location = '/home/chris.jacobs/Documents/file.jpg'
        # file1 should have image_id = 0 and file2 image_id = 1
        self.assertEqual('/home/chris.jacobs/file1', catalog.save_image(0))  # without save_location
        self.assertEqual(location, catalog.save_image(1, location))  # with save_location

    @mock.patch('image_catalog.open', return_value=None)  # replace the python open method by making it return None
    @mock.patch('image_catalog.exifread.process_file', return_value=tags{'2018:12:08 10:41:16'})
    def test_extract_date(self, mock_open, mock_exifread):
        catalog = ImageCatalog()
        date_object, date_string = catalog.extract_date('/home/chris.jacobs/Documents/DeepLearning/Data/LosseFotos/IMG_20181208_104117.jpg')


if __name__ == '__main__':
    unittest.main()
