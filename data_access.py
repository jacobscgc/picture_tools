import os
from shutil import copyfile, move


class ImageAccess:

    file_extensions = ['JPG', 'jpg', 'jpeg', 'tiff', 'tif', 'png', 'PNG']

    def __init__(self):
        pass

    def import_images(self, folder_location):
        """
        This function imports all image files with an extension present in the file_extension list into a list and
        returns this list.
        :param folder_location: The location of the folder to import images from.
        :return: list of image files present in that folder
        """
        files = []
        if folder_location is not None and folder_location != '':
            files = [f for f in os.listdir(folder_location) if os.path.isfile(os.path.join(folder_location, f)) and
                     f.split('.')[-1] in self.file_extensions]

        return files

    @staticmethod
    def save_image(image, location=None):
        """
        This function saves an image object to disk. If location is given, it writes a new file in that location.
        Otherwise, it will overwrite the original file.
        :param image: Image object.
        :param location: (Optional) file location to save the file to.
        :return: Returns the return value of IMG.save (only used for unit-test)
        """
        if location is None:
            location = image.file_location + '/' + image.file_name

        return image.IMG.save(location)


class FileAccess:

    def __init__(self):
        pass

    @staticmethod
    def write_to_csv(filename, data, mode='w'):
        """
        This function writes the content of data to a csv file (filename).
        data should contain a single string per line that is to be written to file, were the delimiter chosen and the
        newline character is included. A header can be used as the first entry of data if so desired.
        Example of data:
        [
            "filename, size, width, height\n",
            "image1, 343, 1920, 1080\n",
            "image1, 234, 1920, 1080\n"
        ]
        :param filename: The absolute path to the file to be written.
        :param data: The data to be written as a list of strings, where each string represents a single line in the csv.
        The data list can contain an header as the first string.
        :param mode: mode to write the csv ('w' or 'r'), default = 'w'
        :return: A csv-file written to disk.
        """
        csv = open(filename, mode)
        for line in data:
            csv.write(line)

    @staticmethod
    def read_csv(filename, delimiter):
        """
        This function imports a csv file with a certain delimiter to a list of lists, where each list contains a
        single line.
        Example:
        Input:      filename, size, width, height
                    image1, 343, 1920, 1080
                    image2, 234, 1920, 1080
        Output:
        [
            ['filename', 'size', 'width', 'height'],
            ['image1', 343, 1920, 1080],
            ['image2', 234, 1920, 1080]
        ]
        :param filename: The absolute path to the file to be opened.
        :param delimiter: The delimiter used as a string (example: ',' or ';').
        :return: A list of lists.
        """
        data = []
        if os.path.exists(filename):
            csv = open(filename, 'r')
            for line in csv:
                line = line.rstrip()
                split_line = line.split(delimiter)
                data.append(split_line)
        return data

    @staticmethod
    def delete_file_from_disk(filename):
        """
        This function deletes the file given from the disk.
        :param filename: The absolute path of the file to be deleted.
        :return: None, a file has been deleted.
        """
        if os.path.exists(filename):
            os.remove(filename)

    @staticmethod
    def create_folder(folder_name):
        """
        This function creates a folder (folder_name).
        :param folder_name: The absolute path of the folder to be created.
        :return: None, a folder has been created.
        """
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

    @staticmethod
    def copy_file(origin_path, goal_path):
        """
        This function copies a file from the origin_path to the goal_path. The original is not removed.
        :param origin_path: The absolute path to the file to be copied.
        :param goal_path: The absolute path to where the file should be copied.
        :return: None, the file has been copied.
        """
        if os.path.exists(origin_path):
            copyfile(origin_path, goal_path)

    @staticmethod
    def move_file(origin_path, goal_path):
        """
        This function moves a file from the origin_path to the goal_path.
        :param origin_path: The absolute path to the file to be moved.
        :param goal_path: The absolute path to where the file should be moved.
        :return: None, the file has been moved.
        """
        if os.path.exists(origin_path):
            move(origin_path, goal_path)

    @staticmethod
    def file_exists(path):
        """
        This function checks whether a file exists and returns True if it exists and False if not.
        :param path: Absolute path to file.
        :return: True or False
        """
        if os.path.exists(path):
            return True
        else:
            return False
