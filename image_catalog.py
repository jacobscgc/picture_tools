import exifread
import os
import subprocess
from datetime import datetime
from natsort import natsorted

# Picture tools modules:
from data_access import ImageAccess
from data_access import FileAccess
from tag_categories import TagCategories
from image import Image


class ImageCatalog:

    def __init__(self):
        self.image_access = ImageAccess()
        self.file_access = FileAccess()
        self.tag_categories = TagCategories()
        self.images = {}  # catalog to save the image_objects in
        self.image_id = 0
        self.start_date, self.end_date = None, None  # used for date selection if applicable
        self.file_names = []  # list to make sure no duplicate filenames are entered into the catalog
        #subprocess.check_output("ulimit -n 4096", shell=True)  # increase ulimit
        #self.ulimit = eval(subprocess.check_output("ulimit -n", shell=True)[0:-1])  # check limit number of open files
        #self.ulimit = int(round(0.99 * self.ulimit))
        self.ulimit = 50000
        print(self.ulimit)
        self.images_loaded = 0

    def add_image(self, file_path, file_name, date_object):
        """
        This function adds an Image object to the image dictionary.
        :param file_path: Absolute path to folder containing the image.
        :param file_name: name of image file.
        :param date_object: date object for the image stating when it was taking (or file was created).
        :return: Adds Image object to the image dictionary.
        """
        if self.image_id <= self.ulimit:  # only add images if ulimit has not been reached
            self.file_names.append(file_name)
            image_object = Image(self.tag_categories, file_path, file_name, date_object)
            self.images[self.image_id] = image_object
            self.image_id += 1
            self.images_loaded += 1
        
    def save_image(self, image_id, fileloc=None):
        """
        This function saves the image. It saves the image to fileloc if given, otherwise it will overwrite the
        existing file.
        :param image_id: image_id of the image to save.
        :param fileloc: Absolute path to save the image file to.
        :return: Returns the return value of IMG.save (only used for unit-test)
        """
        image_object = self.images[image_id]
        if fileloc is None:
            return self.image_access.save_image(image_object)
        else:
            return self.image_access.save_image(image_object, fileloc)

    def close_all_images(self):
        """
        This function loops through all images in the image catalog and closes them. This can be used to free up
        resources again if files are no longer needed.
        """
        for key, value in self.images.items():
            value.IMG.close()

    def extract_date(self, file_location):
        """
        This function tries to extract the date when the image was taken from EXIF data. If there is no EXIF data
        available, the date that the file was created is used instead.
        :param file_location: Absolute file location.
        :return: datetime object and date_string.
        """
        f = open(file_location, 'rb')
        tags = exifread.process_file(f)
        if 'EXIF DateTimeOriginal' in tags:
            date_string = tags['EXIF DateTimeOriginal']
        else:  # If no EXIF data available, get date it was modified instead
            date_string = datetime.utcfromtimestamp(os.path.getmtime(file_location)).strftime('%Y:%m:%d %H:%M:%S')
        date_object, date_string = self.datestring_to_dateobject(date_string)

        return date_object, date_string

    @staticmethod
    def datestring_to_dateobject(date_string):
        """
        This function takes a date_string taken from either exif data or from when the file was created.
        It parses this string into a date object en returns that object. It also returns a simplified (only dd/mm/yyyy)
        date_string.
        :param date_string: A date_string in the form: 'yyyy:mm:dd HH:MM:SS'
        :return: date_object and simplified date_string
        """
        date_split = str(date_string).split(' ')[0]
        time_split = str(date_string).split(' ')[1]
        year, month, day = date_split.split(':')
        hour, minute, second = time_split.split(':')
        date_object = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        date_string = '{0}:{1}:{2}'.format(year, month, day)

        return date_object, date_string

    def set_date_range(self, start, end):
        """
        This function sets the start and end date used for the image imports.
        :param start: start date to use for selection (yyyy:mm:dd) (string)
        :param end: end date to use for selection (yyyy:mm:dd) (string)
        :return: date range has been set
        """
        if self.validate_date(start):
            self.start_date = start
        if self.validate_date(end):
            self.end_date = end

    def reset_date_range(self):
        """
        This function resets the start end end date so new imports do not use the range anymore.
        :return: resetted date range
        """
        self.start_date, self.end_date = None, None

    @staticmethod
    def validate_date(date_string):
        try:
            datetime.strptime(date_string, '%Y:%m:%d')
            return True
        except ValueError:
            return False

    def open_folder(self, folder_location):
        """
        This function imports all image files from a folder to a list. It then creates image objects for all images
        in the list that fall within the defined period if the start and end date have been set, and for all if no
        period has been set. It adds all created object to the images dictionary.
        :param folder_location: The location of the folder to import images from.
        :return: fills the images dictionary with the images present in the chosen folder.
        """
        images = self.image_access.import_images(folder_location)
        images = natsorted(images)  # sort filelist so that they are loaded as they would be sorted naturally
        for entry in images:
            if entry not in self.file_names:
                # get the date the image was taken (or created if exif data is missing)
                date_object, date_string = self.extract_date(folder_location + '/' + entry)
                if self.start_date is not None and self.end_date is not None:
                    if self.date_in_range(self.start_date, self.end_date, date_string):
                        self.add_image(folder_location, entry, date_object)
                else:  # no date selection
                    self.add_image(folder_location, entry, date_object)

    @staticmethod
    def date_in_range(start, end, date):
        """
        This function checks whether a date falls in the period [start:end].
        It returns True if it falls within this period, False otherwise.
        :param start: start of date range ; datestring (dd/mm/yyyy)
        :param end: end of date range ; datestring (dd/mm/yyyy)
        :param date: date to check whether between start and end ; datestring (dd/mm/yyyy)
        :return: True or False
        """
        value = False

        start = start.split(':')
        start = [int(i) for i in start]
        end = end.split(':')
        end = [int(i) for i in end]
        date = date.split(':')
        date = [int(i) for i in date]

        if start[0] <= date[0] <= end[0]:
            # if the year is within the range:
            if start[0] < date[0] < end[0]:
                # if the year is not equal to either start or end, return True
                value = True
            elif start[0] == date[0]:
                # if the start_year equals the year, check the month and day:
                if date[1] > start[1]:
                    value = True
                elif date[1] == start[1] and date[2] >= start[2]:  # same month, later day
                    value = True
            else:
                # year equals end_year, check the month and day:
                if date[1] <= end[1]:
                    value = True
                elif date[1] == end[1] and date[2] <= end[2]:
                    value = True

        return value

    def delete_image_from_catalog(self, image_id, delete_from_disk=False):
        """
        This function deletes an image from the image catalog.
        If delete_from_disk = True, the file will also be removed from disk.
        :param image_id: the image_id of the image to be deleted from the catalog
        :param delete_from_disk: if True, it deletes the image from disk.
        :return: deleted the image object from the image catalog (and optionally from disk).
        """
        # remove from the self.file_names list (so it can be added again if needed)
        file_name = self.images[image_id].file_name
        self.file_names = [i for i in self.file_names if i != file_name]
        if delete_from_disk:
            file_location = self.images[image_id].file_location
            self.file_access.delete_file_from_disk(file_location + '/' + file_name)
        del self.images[image_id]  # delete from image catalog
        self.images_loaded -= 1  # lower number of open images

    def save_progress(self, save_location, settings):
        """
        This function saves the current state to a csv file that can be restored later.
        It saves the image data to one file (the save_location) and the settings and tag_categories to a _settings.csv
        file.
        :param save_location: Absolute path to a save file location.
        :param settings: A list of lists containing settings to save [['taglinewidth', 3], ['selected_image', 'image1']]
        etc.
        :return: Save file and settings file have been written.
        """
        # Write all data to a list of strings, which will then be exported to csv.
        output_list = ['Image;Path;Date_time;Tags\n']  # create the list with an header
        for image_id in self.images:
            image = self.images[image_id]
            tags = image.tags.tag_dict
            tag_list = [(tags[i].tag_category, tags[i].coordinates) for i in tags]
            output_list.append('{0};{1};{2};{3}\n'.format(image.file_name, image.file_location, image.date_string,
                                                          tag_list))
        # Create a file location with '_settings' appended to contain the tag_categories etc.
        settings_save_location = '.'.join(save_location.split('.')[:-1]) + '_settings.csv'
        # Write all tag_categories created to the end of the save_file:
        for tag_category in self.tag_categories.tag_categories:
            color = self.tag_categories.tag_categories[tag_category]
            settings.append('TagCategory;{0};{1}\n'.format(tag_category, color))
        # Write the output_list to csv:
        self.file_access.write_to_csv(save_location, output_list)
        # Write the settings to csv:
        self.file_access.write_to_csv(settings_save_location, settings)

    def load_savefile(self, savefile_location):
        """
        This function loads a previously saved image catalog from a savefile.
        It restores the images and their labels and loads the created TagCategories.
        :param savefile_location: Absolute path to the savefile.
        :return: loads image catalog from file
        """
        settings_save_location = '.'.join(savefile_location.split('.')[:-1]) + '_settings.csv'
        savefile_data = self.file_access.read_csv(savefile_location, ';')
        settings_data = self.file_access.read_csv(settings_save_location, ';')
        # First import the settings (and the tag_categories):
        selected_image, taglinewidth, savefile_location, min_tagsize, sorting_method = None, 3, None, 0, 'file_name'
        for line in settings_data:
            if line[0] == 'TagCategory':  # restore tag_categories
                tag_category = line[1]
                color = line[2]
                self.tag_categories.add_tag_category(tag_category, color)
            if line[0] == 'selected_image':
                selected_image = line[1]
            if line[0] == 'taglinewidth':
                taglinewidth = line[1]
            if line[0] == 'savefile_location':
                savefile_location = line[1]
            if line[0] == 'min_tagsize':
                min_tagsize = int(line[1])
            if line[0] == 'sorting_method':
                sorting_method = line[1]
        # Next, import the images and their tags:
        for line in savefile_data:
            if line[0] != 'Image':  # not the header
                file_name, file_path, date_string, tags = line[0], line[1], line[2], eval(line[3])
                date_object, date_string = self.datestring_to_dateobject(date_string)
                image_id = self.image_id
                if file_name not in self.file_names:
                    self.add_image(file_path, file_name, date_object)
                    if image_id in self.images:  # check whether image object has been created
                        for tag in tags:
                            self.images[image_id].tags.add_tag(tag[0], tag[1])

        return selected_image, taglinewidth, savefile_location, min_tagsize, sorting_method

    def export_tagged_images(self, save_location, tag_categories=None, remove_original=False, rename=False, csv=True):
        """
        This function exports tagged images to the save_location.

        It creates a sub-folder for each tag_category where images have been tagged with the full image coordinates and
        puts those images in the folders.
        All other images (where coordinates < full image coordinates) are placed directly in the save_location.
        If both full image and smaller coordinates are used, the image is placed in the folder for the full image
        coordinates. When multiple categories with full image coordinates are present, the image will be copied to each
        of the full image tag category folders.

        If csv = True, a csv-file with tags is created in each folder with images so that they can be loaded again and
        manipulated later.

        A list of tag_categories can be provided to only export images that have certain tags ['tag_category1', '2' etc]

        If rename is set to 'yes', it will rename all images to numbers. It will first check whether there are already
        numbered images in the output folder, if so, it will continue numbering from the highest number. It will
        also check whether a tags csv file already exists. If so, it will append to this instead of creating a new one.

        If remove_original = True, the original image file is deleted after it has been copied to a new location.

        :param save_location: The absolute path to the folder where the images should be saved (does not need to exist)
        :param tag_categories: list of tag_categories to export (optional)
        :param remove_original: True or False (default = False)
        :param rename: True or False (default = False)
        :param csv: True or False (default = True)
        """
        header = "filename,width,height,class,xmin,ymin,xmax,ymax\n"
        # Create the output folder (if it already exists it will skip this step):
        self.file_access.create_folder(save_location)
        # Loop through all images and their tags to check whether certain tag_categories contain full_image coordinates:
        tag_categories_images = self.check_for_full_image_tags()
        if tag_categories is not None:
            for key in list(tag_categories_images):  # create a list to enable deleting on the way
                if key not in tag_categories:  # category not in export list:
                    del tag_categories_images[key]
        # Now, all entries in tag_categories_images contain a list of image_id's that should be copied to them.
        for tag_category in tag_categories_images:
            image_list = tag_categories_images[tag_category]
            if len(image_list) > 0:
                image_number = None
                if tag_category != 'no_full_size':
                    csv_loc = save_location + '/' + tag_category + '/tags.csv'
                    export_folder = save_location + '/' + tag_category
                    self.file_access.create_folder(export_folder)
                    if not self.file_access.file_exists(csv_loc) and csv:
                        self.file_access.write_to_csv(csv_loc, [header])
                    if rename:
                        image_number = self.check_for_previously_exported(export_folder)
                    self.process_image_export_list(image_list, csv_loc, export_folder, image_number, rename,
                                                   remove_original, csv)
                else:  # images without full_sized tags (but with smaller tags)
                    csv_loc = save_location + '/tags.csv'
                    export_folder = save_location
                    if not self.file_access.file_exists(csv_loc) and csv:
                        self.file_access.write_to_csv(csv_loc, [header])
                    if rename:
                        image_number = self.check_for_previously_exported(save_location)
                    self.process_image_export_list(image_list, csv_loc, export_folder, image_number, rename,
                                                   remove_original, csv)

    def process_image_export_list(self, image_list, csv_loc, export_folder, image_number, rename, remove_original, csv):
        """
        This function processes an image_list (containing image_id's) which need to be exported to the same folder.
        For these images, all images are copied to that folder and their tags are appended to the tags.csv file.
        If remove_original = True, the original image is deleted.
        :param image_list: list of image_id's
        :param csv_loc: Absolute location of the tags.csv file
        :param export_folder: Absolute location of the folder to export the images to.
        :param image_number: counter from which to start if images are to be renamed.
        :param rename: True or False (rename images or not)
        :param remove_original: True or False (remove original image or not)
        :param csv: True or False (write csv or not)
        :return: files have been exported.
        """
        for image_id in image_list:
            image = self.images[image_id]
            absolute_path = image.file_location + '/' + image.file_name
            if rename and image_number is not None:
                file_extension = image.file_name.split('.')[-1]
                file_name = str(image_number) + '.' + file_extension
                export_path = export_folder + '/' + file_name
                # Update the image_catalog for this image:
                image.file_location = export_folder
                image.file_name = file_name
                self.images[image_id] = image
                # Increment image number:
                image_number += 1
            else:
                export_path = export_folder + '/' + image.file_name
                file_name = image.file_name
            # copy the file to the proper location:
            self.file_access.copy_file(absolute_path, export_path)
            if remove_original:
                self.file_access.delete_file_from_disk(absolute_path)
            if csv:
                # Get all the tags for the image to export to csv:
                tags_to_csv = []
                tags = [(image.tags.tag_dict[i].tag_category, image.tags.tag_dict[i].coordinates) for i in
                        image.tags.tag_dict]
                for tag in tags:
                    tag_category = tag[0]
                    tag_coords = tag[1]
                    full_image_coords = [0, 0, image.size[0], image.size[1]]
                    if tag_coords != full_image_coords:  # don't export full image tags
                        csv_string = "{0},{1},{2},{3},{4},{5},{6},{7}\n".format(file_name, image.size[0], image.size[1],
                                                                                tag_category, tag_coords[0],
                                                                                tag_coords[1], tag_coords[2],
                                                                                tag_coords[3])
                        tags_to_csv.append(csv_string)
                # append them to the csv file:
                self.file_access.write_to_csv(csv_loc, tags_to_csv, 'a')

    def check_for_previously_exported(self, location):
        """
        This function checks for a location whether renamed images are already present there and returns the number
        where should be continued when adding new images.
        :param location: Absolute path to the folder to check.
        :return: number from which should be started when adding new renamed images.
        """
        image_number = 0
        image_list = self.image_access.import_images(location)
        if len(image_list) > 0:
            numbers = [int(i.split('.')[0]) for i in image_list]
            numbers.sort()
            image_number = numbers[-1] + 1

        return image_number

    def check_for_full_image_tags(self):
        """
        This function checks for all images whether full_sized tags have been created and if so, it adds its image_id
        to the list belonging to the tag_category. In the end, the tag_categories_images dictionary contains a list of
        all images that have a full_size tag for that category.
        (empty list if no images have a full_size tag for a certain category)
        :return: tag_categories_images dictionary
        """
        tag_categories_images = {}  # dictionary to save whether tag_categories are full_sized or not
        # First, set an empty list for all tag_categories:
        for tag_category in self.tag_categories.tag_categories:
            tag_categories_images[tag_category] = []
        # Add a no_full_size category to store the image_id's of the images that do have tags but no full_size tags:
        tag_categories_images['no_full_size'] = []
        # Next, loop through the images and add their image_id to the list of the tag_category if it has that
        # tag_category full_size tag:
        for image_id in self.images:
            image = self.images[image_id]
            full_size_list = self.extract_full_image_tags(image)
            for category in full_size_list:
                image_list = tag_categories_images[category]
                image_list.append(image_id)
                tag_categories_images[category] = image_list

        return tag_categories_images

    @staticmethod
    def extract_full_image_tags(image):
        """
        This function taken an image object and creates a list of tag_categories for which full image tags exist.
        :param image: image object of the Image class.
        :return: list of tag_categories for which it has full image tags.
        """
        full_image_tags = []
        tags = [(image.tags.tag_dict[i].tag_category, image.tags.tag_dict[i].coordinates) for i in image.tags.tag_dict]
        if len(tags) > 0:
            full_sized = False
            for tag in tags:
                if tag[1] == [0, 0, image.size[0], image.size[1]]:
                    full_image_tags.append(tag[0])
                    full_sized = True
            if not full_sized:  # tags are present but no full_sized ones
                full_image_tags.append('no_full_size')

        return full_image_tags

    def extract_entries_for_tag_category(self, tag_category, delete=False, replace=False, replace_category=None):
        """
        This function loops through the images and extracts their tags. It then checks whether there are any tags of
        the [tag_category] present. If so, it increments the counter by 1. If delete = True, it will also remove the
        tag. It returns the number of times this tag_category occured.
        :param tag_category: tag_category
        :param delete: True or False
        :param replace: whether to replace the tag_category with another one
        :param replace_category: the new category to replace with
        :return: count of occurences of tag_category tags.
        """
        count = 0
        for image_id in self.images:
            image = self.images[image_id]
            tags = [(i, image.tags.tag_dict[i].tag_category) for i in image.tags.tag_dict]  # extract tags
            for tag in tags:
                if tag[1] == tag_category:
                    count += 1
                    if delete:
                        self.images[image_id].tags.remove_tag(tag[0])  # remove the tag
                    elif replace and replace_category is not None:
                        self.images[image_id].tags.tag_dict[tag[0]].tag_category = replace_category  # replace category
        if not delete:
            return count
