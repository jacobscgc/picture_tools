import os
import sys
from tkinter import *
from tkinter import messagebox as ms
from tkfilebrowser import askopendirname, askopenfilename, asksaveasfilename
import math

# Picture tools modules:
from controller import Controller


class Application(Frame):

    canvas, wt, status = None, None, None
    image_list, tag_list = None, None
    image_scrollbar, tag_scrollbar = None, None
    pil_image, origX, origY, zoomcycle, zoom_factor = None, None, None, 0, 1
    selected_image, win_w, win_h = None, None, None  # keep track of active image / window size to deal with resizing
    selected_tag, active_tag_id = None, None
    savefile_location = None
    min_tagsize = 0
    sorting_method = 'file_name'

    # variables for drawing tags:
    drawing = False
    control_pressed = False
    start_x, start_y, x, y, coords, rect = None, None, 0, 0, None, None
    cross_line1, cross_line2 = None, None

    def __init__(self, master=None):
        self.controller = Controller()
        Frame.__init__(self, master)
        self.viewmethods = ViewMethods(self.master, self.controller)
        self.importexport = ImportExportMethods(self.master, self.controller, self.viewmethods)
        self.tagmethods = TagMethods(self.master, self.controller, self.viewmethods)
        self.master.rowconfigure(0, weight=3)
        self.master.rowconfigure(1, weight=1)
        self.master.rowconfigure(2, weight=0)
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=0)
        self.master.columnconfigure(2, weight=9)
        self.grid(sticky=W+E+N+S)

        self.cwd = os.getcwd()

        self.setup_gui()
        self.set_keybindings()

        self.taglinewidth = 3

        self.master.bind("<Configure>", lambda e: self.window_resized())

    def setup_gui(self):

        # Create a canvas where the images are displayed:
        self.canvas = Canvas(self.master, bg='black', bd=10, cursor='cross', relief='ridge')
        self.canvas.bind("<Control_L>", self.on_control_press)
        self.canvas.bind("<Control_R>", self.on_control_press)
        self.canvas.bind("<Control-Motion>", self.on_control_move)
        self.master.bind("<KeyRelease-Control_L>", lambda e: self.on_control_release())
        self.master.bind("<KeyRelease-Control_R>", lambda e: self.on_control_release())
        self.canvas.bind("<Control-ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", lambda e: self.on_button_release())
        self.canvas.grid(row=0, rowspan=2, column=2, sticky=W+E+N+S)
        self.canvas.update()
        self.origX = self.canvas.xview()[0]
        self.origY = self.canvas.yview()[0]
        self.win_w, self.win_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        txt = 'Picture Tools'
        self.wt = self.canvas.create_text(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2, text=txt,
                                          font=('', 30), fill='white')

        # Add a status, which displays which image is currently loaded at the bottom of the screen:
        self.status = Label(self.master, text='Current Image: None', bg='gray',
                            font=('Ubuntu', 15), bd=2, fg='black', relief='sunken', anchor=W)
        self.status.grid(row=2, column=2, sticky=W+E+N+S)

        # Create a scrollbar and a tag_categories_list to scroll through the images:
        self.image_scrollbar = Scrollbar(self.master)
        self.image_scrollbar.grid(row=0, column=1, sticky=W+E+N+S)
        self.image_list = Listbox(self.master, yscrollcommand=self.image_scrollbar.set, selectmode=BROWSE,
                                  exportselection=0)
        self.image_list.bind('<<ListboxSelect>>', lambda e: self.set_active_image())
        self.image_list.grid(row=0, column=0, sticky=W+E+N+S)
        self.image_scrollbar.config(command=self.image_list.yview)

        # Create a scrollbar and a tag_categories_list to scroll through the tags:
        self.tag_scrollbar = Scrollbar(self.master)
        self.tag_scrollbar.grid(row=1, column=1, rowspan=2, sticky=W+E+N+S)
        self.tag_list = Listbox(self.master, yscrollcommand=self.tag_scrollbar.set, selectmode=BROWSE,
                                exportselection=0)
        self.tag_list.bind('<<ListboxSelect>>', lambda e: self.tag_select())
        self.tag_list.grid(row=1, column=0, rowspan=2, sticky=W+E+N+S)
        self.image_scrollbar.config(command=self.image_list.yview)

        # Add a menu bar:
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = Menu(menubar)
        file_menu.add_command(label='Open Image Folder', command=self.import_images_from_folder)
        file_menu.add_command(label='Save Project (Ctrl + s)', command=self.save_progress)
        file_menu.add_command(label='Save Project As..', command=self.save_as)
        file_menu.add_command(label='Load Project (Ctrl + o)', command=self.load_savefile)
        file_menu.add_command(label='Export Settings', command=self.export_settings)
        file_menu.add_command(label='Import Settings', command=self.import_settings)
        file_menu.add_command(label='Export Tagged Images', command=self.export_tagged_images)
        file_menu.add_command(label='Export Images of Single Tag Category', command=self.export_images_one_tag_category)
        file_menu.add_command(label='Reset Picture Tools', command=self.reset_picture_tools)
        file_menu.add_command(label='Quit', command=sys.exit)
        menubar.add_cascade(label="File", menu=file_menu)

        options_menu = Menu(self.master)
        options_menu.add_command(label='Sort images on date', command=self.sort_images_on_date)
        options_menu.add_command(label='Sort images on filename', command=self.sort_images_on_filename)
        options_menu.add_command(label='Delete currently selected image (Ctrl + Del)', command=self.delete_single_image)
        options_menu.add_command(label='Delete currently selected image from disk (Ctrl + Shift + Del)',
                                 command=self.delete_single_image_from_disk)
        menubar.add_cascade(label="Options", menu=options_menu)

        tags_menu = Menu(self.master)
        tags_menu.add_command(label='Add Tag Category', command=self.viewmethods.add_tag_category)
        tags_menu.add_command(label='Remove Tag Category', command=self.remove_tag_category)
        tags_menu.add_command(label='Modify a tags Tag Category', command=self.modify_tag_category)
        tags_menu.add_command(label='Replace Tag Category name', command=self.rename_tag_category)
        tags_menu.add_command(label='Replace Tag Category color', command=self.change_tag_category_color)
        tags_menu.add_command(label='Change bounding box linewidth', command=self.alter_tag_line_width)
        tags_menu.add_command(label='Export tags', command=self.export_tags)
        tags_menu.add_command(label='Load tags', command=self.load_tags)
        menubar.add_cascade(label='Tags', menu=tags_menu)

        keybindings_menu = Menu(self.master)
        keybindings_menu.add_command(label='Show Key-Bindings', command=self.show_keybindings)
        menubar.add_cascade(label='Key-Bindings', menu=keybindings_menu)

    def set_keybindings(self):
        """
        This functions sets all keybindings related to the main window (canvas specific keybindings etc. set elsewhere).
        """
        self.master.bind('f', lambda event: self.highlight_active_image())
        self.master.bind('<Control-s>', lambda event: self.save_progress())
        self.master.bind('<Control-o>', lambda event: self.load_savefile())
        self.master.bind('<Control-r>', lambda event: self.delete_selected_tag())
        self.master.bind('r', lambda event: self.modify_tag_category())
        self.master.bind('<Control-Delete>', lambda event: self.delete_single_image())
        self.master.bind('<Control-Shift-Delete>', lambda event: self.delete_single_image_from_disk())
        self.master.bind('t', lambda event: self.add_full_image_tag())
        # Control zoom-level:s
        self.master.bind("<MouseWheel>", self.zoom)
        # Keybindings to scroll over an image:
        self.master.bind('w', lambda event: self.scroll_up())
        self.master.bind('s', lambda event: self.scroll_down())
        self.master.bind('a', lambda event: self.scroll_left())
        self.master.bind('d', lambda event: self.scroll_right())
        self.master.bind('c', lambda event: self.recenter_canvas())

    def reset_picture_tools(self):
        """This function resets picture tools (clears image-list etc.)"""
        # Loop through the image list and close all previously opened images (otherwise the number of opened images will
        # stay high):
        self.controller.close_all_images()
        self.controller = Controller()
        self.viewmethods = ViewMethods(self.master, self.controller)
        self.importexport = ImportExportMethods(self.master, self.controller, self.viewmethods)
        self.tagmethods = TagMethods(self.master, self.controller, self.viewmethods)
        self.canvas.delete(ALL)
        self.image_list.delete(0, END)
        self.tag_list.delete(0, END)
        self.selected_image = None
        self.selected_tag, self.active_tag_id = None, None
        self.savefile_location = None
        self.pil_image = None
        # Remove all tag_categories:
        tag_categories = self.controller.retrieve_tag_categories()
        for tag_category in tag_categories:
            self.controller.remove_tag_category(tag_category)
        txt = 'Picture Tools'
        self.wt = self.canvas.create_text(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2, text=txt,
                                          font=('', 30), fill='white')
        self.status['text'] = 'Current Image: None'

    def add_full_image_tag(self):
        """This function adds a full-image tag to the selected image"""
        if self.selected_image is not None:
            # Get tag_category to add:
            gettag = GetTag(self.master, self.controller)
            self.master.wait_window(gettag.top2)
            tag_category = gettag.value
            if tag_category is not None:
                self.controller.add_tag(self.selected_image, tag_category)
                if self.sorting_method == 'file_name':
                    self.sort_images_on_filename()
                else:
                    self.sort_images_on_date()
                self.show_image()

    def show_keybindings(self):
        KeyBindings(self.master)

    def delete_single_image(self):
        """Deletes a single image from the image_list"""
        if self.selected_image is not None:
            self.controller.delete_image(self.selected_image)
            self.reset_image_list()

    def delete_single_image_from_disk(self):
        """Deletes the selected image from the image_list and from the harddisk"""
        if self.selected_image is not None:
            self.controller.delete_image(self.selected_image, True)
            self.reset_image_list()

    def import_images_from_folder(self):
        """ Import images."""
        self.importexport.import_images_from_folder(self.image_list)
        if self.controller.check_limit():
            ms.showinfo("Error", "System maximum number of open files has been reached, no new images can be added.")

    def save_as(self):
        """ This function resets self.savefile_location in case a new savefile is requested. """
        self.savefile_location = None
        self.save_progress()

    def save_progress(self):
        """ This function saves the current project to file."""
        self.savefile_location = self.importexport.save_progress(self.savefile_location, self.taglinewidth,
                                                                 self.selected_image, self.min_tagsize)

    def load_savefile(self):
        """
        This function loads a project from a savefile.
        """
        a, b, c, d, e, f = self.importexport.load_savefile(self.image_list)
        if self.controller.check_limit():
            ms.showinfo("Error", "System maximum number of open files has been reached, no new images can be added.")
        if a is not None:
            self.selected_image, self.taglinewidth, self.savefile_location = a, b, c
            self.min_tagsize, self.image_list, self.sorting_method = d, e, f
            self.activate_image()

    def export_settings(self):
        """ Exports the settings to file. """
        self.importexport.export_settings(self.taglinewidth, self.min_tagsize, self.sorting_method)

    def import_settings(self):
        """ Imports settings. """
        self.taglinewidth, self.min_tagsize = self.importexport.import_settings()

    def export_tags(self):
        """This function exports the tags to a tensorflow-friendly csv-file"""
        self.importexport.export_tags(self.min_tagsize)

    def load_tags(self):
        """This function loads tags from a csv-file"""
        self.importexport.load_tag_file()
        self.show_image()

    def export_tagged_images(self):
        """ This function export all images that have tags to a folder."""
        save_location = self.viewmethods.ask_directory(self.master, txt='Please select folder to export the images to')
        self.controller.export_tagged_images(save_location)
        # Refill the image_list because images have been renamed:
        self.sort_images_on_filename()
        self.selected_image = self.image_list.get(0)
        self.activate_image()

    def export_images_one_tag_category(self):
        """This function exports the images for one certain tag_category to a folder on the computer"""
        # Get tag_category to export:
        gettag = GetTag(self.master, self.controller)
        self.master.wait_window(gettag.top2)
        tag_category = [gettag.value]  # as a list
        # Get save location:
        save_location = self.viewmethods.ask_directory(self.master, txt='Please select folder to export the images to')
        self.controller.export_tagged_images(save_location, tag_categories=tag_category)
        # Refill the image_list because images have been renamed:
        self.sort_images_on_filename()
        self.selected_image = self.image_list.get(0)
        self.activate_image()

    def rename_tag_category(self):
        """This function replaces a tag_category name with a new one"""
        # Get tag_category to rename:
        gettag = GetTag(self.master, self.controller)
        self.master.wait_window(gettag.top2)
        tag_category = gettag.value
        # Get value to rename it with:
        userinput = UserInput(self.master, 'Please enter a new name for the tag category')
        self.master.wait_window(userinput.top5)
        new_tag_category = userinput.value
        # Check whether there are any tags for this tag_category in the current catalog images and ifso replace:
        count = self.controller.extract_entries_for_tag_category(tag_category, False, True, new_tag_category)
        self.controller.rename_tag_category(tag_category, new_tag_category)  # replace in TagCategories
        # Print message how many were replaced:
        ms.showinfo("{0} tags of tag_category {1} were renamed to {2}.".format(count, tag_category, new_tag_category))

    def modify_tag_category(self):
        """This function modifies the tag_category for a certain tag (keeping the coordinates)"""
        self.set_active_tag()
        if self.active_tag_id is not None:
            # Get tag_category to replace the old one with:
            gettag = GetTag(self.master, self.controller)
            self.master.wait_window(gettag.top2)
            new_tag_category = gettag.value
            if new_tag_category is not None:
                # Modify tag_category:
                self.controller.modify_tag(self.selected_image, self.active_tag_id, new_tag_category)
                self.viewmethods.sort_images(self.image_list, self.sorting_method)
                self.show_image()  # remake image

    def change_tag_category_color(self):
        """This function replaces the color used for a tag_category"""
        # Get tag_category to replace the color of:
        gettag = GetTag(self.master, self.controller)
        self.master.wait_window(gettag.top2)
        tag_category = gettag.value
        # Get the new color:
        userinput = UserInput(self.master, 'Please enter a HEX color')
        self.master.wait_window(userinput.top5)
        color = userinput.value
        # Replace:
        self.controller.change_tag_category_color(tag_category, color)
        self.show_image()

    def remove_tag_category(self):
        """This function removes a tag_category"""
        # Get tag_category to remove:
        gettag = GetTag(self.master, self.controller)
        self.master.wait_window(gettag.top2)
        tag_category = gettag.value
        # Check whether there are any tags for this tag_category in the current catalog images:
        count = self.controller.extract_entries_for_tag_category(tag_category)
        # Ask userconfirmation if count > 0:
        if count > 0:  # there are tags for this tag_category:
            confirm = UserConfirmation(self.master, '{0} occurences of {1} found, are you sure you want to delete the '
                                                    'tag_category (and tags with this '
                                                    'tag_category)?'.format(count, tag_category))
            self.master.wait_window(confirm.top6)  # wait for response
            if confirm.value:
                self.controller.extract_entries_for_tag_category(tag_category, True)  # delete them
                self.controller.remove_tag_category(tag_category)
        else:
            self.controller.extract_entries_for_tag_category(tag_category, True)  # delete tag_category
            self.controller.remove_tag_category(tag_category)
        self.show_image()

    def scroll_left(self):
        self.canvas.xview_scroll(-1, "units")

    def scroll_right(self):
        self.canvas.xview_scroll(1, "units")

    def scroll_down(self):
        self.canvas.yview_scroll(1, "units")

    def scroll_up(self):
        self.canvas.yview_scroll(-1, "units")

    def zoom(self, event):
        if event.delta == 120:
            # zooming out
            if self.zoomcycle != 5:
                self.zoomcycle += 1
            if self.selected_image is not None:
                self.show_image()
        else:
            # zooming in
            if self.zoomcycle != 0:
                self.zoomcycle -= 1
            if self.zoomcycle == 0:
                self.recenter_canvas()
            if self.selected_image is not None:
                self.show_image()

    def recenter_canvas(self):
        self.canvas.xview_moveto(self.origX)
        self.canvas.yview_moveto(self.origY)

    def activate_image(self):
        """
        This function displays the currently selected_tag image (sets it as active).
        """
        if self.selected_image is not None:
            # This function sets an image as the active image (displays it).
            self.show_image()
            index = self.image_list.get(0, "end").index(self.selected_image)
            self.image_list.selection_set(index)  # sets this index as selected_tag
            self.image_list.activate(index)  # sets this index as active (highlight it)
            self.image_list.see(index)  # makes sure that the highlighted item is visible in the listbox
            self.image_list.focus()

    def reset_image_list(self):
        """This function resets the image_list and sorts it. Call when changes to image_list have been made."""
        if self.sorting_method == 'file_name':
            self.sort_images_on_filename()
        else:
            self.sort_images_on_date()

    def sort_images_on_date(self):
        """ Sorts the image_list on the date taken. """
        self.sorting_method = 'date_taken'
        self.image_list = self.viewmethods.sort_images(self.image_list, self.sorting_method)

    def sort_images_on_filename(self):
        """ Sorts the image_list on the filename. """
        self.sorting_method = 'file_name'
        self.image_list = self.viewmethods.sort_images(self.image_list, self.sorting_method)

    def set_active_image(self):
        """
        This function sets an image to active when selected_tag in the image_list (tag_categories_list).
        :return: active image
        """
        self.selected_image = self.viewmethods.get_selected_item(self.image_list)
        self.show_image()

    def set_active_tag(self):
        """ This function sets an tag to active when selected_tag in the tag_list (tag_categories_list). """
        self.active_tag_id = self.tagmethods.set_active_tag(self.tag_list)

    def delete_selected_tag(self):
        """This function deletes the currently selected tag"""
        self.set_active_tag()
        if self.active_tag_id is not None:
            self.controller.remove_tag(self.selected_image, self.active_tag_id)
            self.viewmethods.sort_images(self.image_list, self.sorting_method)
            self.show_image()  # remake image

    def tag_select(self):
        """
        This function sets a tag to active, assining it's tag_id to self.active_tag_id and highlighting the
        bounding box in red.
        """
        if self.selected_tag is not None:
            self.canvas.delete(self.selected_tag)
        self.set_active_tag()
        if self.active_tag_id is not None:
            tag_dictionary = self.controller.retrieve_tags(self.selected_image)
            coords = tag_dictionary[self.active_tag_id].coordinates
            if coords is not None:
                # convert image tag coordinates to canvas tag coordinates:
                resolution = (math.floor(self.canvas.winfo_width() * self.zoom_factor),
                              math.floor(self.canvas.winfo_height() * self.zoom_factor))
                ratio, pil_image = self.controller.calculate_ratio(self.selected_image, resolution)
                canvas_grid_size = (self.canvas.winfo_width(), self.canvas.winfo_height())
                tags = self.controller.image_coords_to_canvas_coords(coords, canvas_grid_size, pil_image, ratio)
                self.selected_tag = self.canvas.create_rectangle(tags[0], tags[1], tags[2], tags[3],
                                                                 width=self.taglinewidth, outline='red',
                                                                 dash=(2, 10))

    def show_image(self):
        """
        This function get the current canvas size and then retrieves a pil_image object resized to the canvas size.
        It then displays the active image.
        :return: shows image.
        """
        # Determine whether we need to zoom:
        zoomlist = {0: 1, 1: 1.5, 2: 2, 3: 3, 4: 4, 5: 5}
        self.zoom_factor = zoomlist[self.zoomcycle]
        resolution = (math.floor(self.canvas.winfo_width() * self.zoom_factor),
                      math.floor(self.canvas.winfo_height() * self.zoom_factor))
        # Get the image (need to keep an reference to the image [self.pil_image] or the image won't show):
        self.pil_image = self.controller.retrieve_image(self.selected_image, resolution)
        tag_dictionary = self.controller.retrieve_tags(self.selected_image)
        if self.pil_image is not None:
            # Delete the current items on the canvas:
            self.canvas.delete(ALL)
            # Clear the tag_list:
            self.tag_list.delete(0, END)
            # Display the image:
            center = (math.floor(self.canvas.winfo_width() / 2), math.floor(self.canvas.winfo_height() / 2))
            self.canvas.create_image(center[0], center[1], anchor=CENTER, image=self.pil_image)
            self.status['text'] = 'Current Image: ' + self.selected_image + '    Date Taken: ' + \
                                  self.controller.retrieve_image_date_taken(self.selected_image)
            # Add the tags:
            ratio, pil_image = self.controller.calculate_ratio(self.selected_image, resolution)
            for key, value in tag_dictionary.items():
                tag_category, tag_coords = value.tag_category, value.coordinates
                # convert image tag coordinates to canvas tag coordinates:
                canvas_grid_size = (self.canvas.winfo_width(), self.canvas.winfo_height())
                tag_coords = self.controller.image_coords_to_canvas_coords(tag_coords, canvas_grid_size, pil_image,
                                                                           ratio)
                # Add it to the tag_list and draw a rectangle:
                self.tag_list.insert(END, '{0}_{1}'.format(key, tag_category))
                col = self.controller.retrieve_tag_category_color(tag_category)
                self.canvas.create_rectangle(tag_coords[0], tag_coords[1], tag_coords[2], tag_coords[3],
                                             tag=tag_category, width=self.taglinewidth, outline=col)
        self.highlight_active_image()

    def window_resized(self):
        """
        This function re-creates the image if the window has been resized.
        """
        win_width, win_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if self.win_w is not None:
            if win_width != self.win_w or win_height != self.win_h:
                self.show_image()
        self.win_w, self.win_h = win_width, win_height

    def draw_cross(self, x, y):
        """This function draws a cross on the canvas to show where the tag will be drawn"""
        width, height = self.canvas.winfo_width() * self.zoom_factor, self.canvas.winfo_height() * self.zoom_factor
        # Calculate x0, y0, x1, y1 to enable the lines to be drawn outside the regular canvas area when zoomed.
        # Meaning that x0, y0 can be < 0 and x1, y1 can be larger than canvas width / height:
        x0 = math.floor((self.canvas.winfo_width() / 2) - (width / 2))
        x1 = math.floor((self.canvas.winfo_width() / 2) + (width / 2))
        y0 = math.floor((self.canvas.winfo_height() / 2) - (height / 2))
        y1 = math.floor((self.canvas.winfo_height() / 2) + (height / 2))
        self.cross_line1 = self.canvas.create_line(x0, y, x1, y, fill='green', width=2)
        self.cross_line2 = self.canvas.create_line(x, y0, x, y1, fill='green', width=2)

    def on_control_press(self, event):
        """
        This function draws a cross to the edges of the canvas when control is pressed.
        """
        if self.cross_line1 is not None:
            self.canvas.delete(self.cross_line1)
            self.canvas.delete(self.cross_line2)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.draw_cross(x, y)

    def on_control_move(self, event):
        """
        This function draws a cross to the edges of the canvas when dragging the mouse and control is pressed.
        """
        if self.cross_line1 is not None:
            self.canvas.delete(self.cross_line1)
            self.canvas.delete(self.cross_line2)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.draw_cross(x, y)

    def on_control_release(self):
        """
        This function removes the green cross from the canvas once the control has been released.
        """
        if self.cross_line1 is not None:
            self.canvas.delete(self.cross_line1)
            self.canvas.delete(self.cross_line2)

    def on_button_press(self, event):
        # This function responds when control + mouse button 1 are pressed
        self.drawing = True
        self.control_pressed = True
        # save mouse drag start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

        # create rectangle:
        self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, outline='red')

    def on_move_press(self, event):
        """
        This function responds to mouse movement on the canvas if a tag is being drawn.
        """
        if self.drawing:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            if self.cross_line1 is not None:
                self.canvas.delete(self.cross_line1)
                self.canvas.delete(self.cross_line2)
            self.draw_cross(x, y)
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)

            # expand rectangle as you drag the mouse
            self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
            self.coords = [self.start_x, self.start_y, cur_x, cur_y]

    def on_button_release(self):
        """
        This function process what has been drawn on the canvas (a tag) once it is done (mouse release).
        """
        if self.cross_line1 is not None:
            self.canvas.delete(self.cross_line1)
            self.canvas.delete(self.cross_line2)
        # If control was pressed, create a Tag:
        if self.drawing and self.control_pressed and self.selected_image is not None:
            # First, correct the order of the coordinates, which is dependent on the drawing direction:
            xmin, xmax = min([self.coords[0], self.coords[2]]), max([self.coords[0], self.coords[2]])
            ymin, ymax = min([self.coords[1], self.coords[3]]), max([self.coords[1], self.coords[3]])
            canvas_coords = [xmin, ymin, xmax, ymax]
            # Next, get the size of the canvas and of the resized image (current size):
            resolution = (self.canvas.winfo_width() * self.zoom_factor, self.canvas.winfo_height() * self.zoom_factor)
            ratio, pil_image = self.controller.calculate_ratio(self.selected_image, resolution)
            # Retrieve the image coordinates for these canvas coordinates:
            canvas_grid_size = (self.canvas.winfo_width(), self.canvas.winfo_height())
            image_size = self.controller.retrieve_image_object(self.selected_image).size
            image_coords = self.controller.canvas_coords_to_image_coords(canvas_coords, canvas_grid_size,
                                                                         pil_image, ratio, image_size)
            # Make sure that there is a selected_tag image
            if self.selected_image is None:
                ms.showinfo("Error", "Please select an image in the image list first.")
            else:
                # Get the tag which should be used
                gettag = GetTag(self.master, self.controller)
                self.master.wait_window(gettag.top2)
                tag = gettag.value
                if tag is not None:
                    self.controller.add_tag(self.selected_image, tag, image_coords)
                    self.show_image()

        # Set the drawing and control pressed to false again:
        self.drawing = False
        self.control_pressed = False

    def highlight_active_image(self):
        """
        This function highlights the active image in the image_list.
        """
        selected_image = self.selected_image
        if selected_image is not None:
            index = self.image_list.get(0, "end").index(selected_image)  # searches index to find the selected_image
            # TODO: if image cannot be found, do not show an image. (check return value .get function)
            self.image_list.selection_set(index)  # sets this index as selected_tag
            self.image_list.activate(index)  # sets this index as active (highlight it)
            self.image_list.see(index)  # makes sure that the highlighted item is visible in the tag_categories_list
            self.image_list.focus()

    def add_tag_category(self, tag_category):
        """ Adds a tag category. """
        self.controller.add_tag_category(tag_category)

    def alter_tag_line_width(self):
        """
        This function alters the linewidth used for the bounding boxes of tags.
        """
        linewidth = TagLineWidth(self.master)
        self.master.wait_window(linewidth.top3)
        self.taglinewidth = linewidth.value
        if self.selected_image is not None:
            self.show_image()


class ImportExportMethods:

    def __init__(self, master, controller, viewmethods):
        self.master = master
        self.controller = controller
        self.viewmethods = viewmethods

    def import_images_from_folder(self, image_list):
        """
        This function imports a folder into the image catalog and refreshes all images present in the image_list.
        :param image_list: listbox image_list
        :return: Updated image_list.
        """
        # First, ask the user for a directory to import images from:
        folder_location = self.viewmethods.ask_directory(self.master,
                                                         txt='Please select a folder to import images from.')
        if folder_location != '':
            # Next, import these images into the image catalog:
            self.controller.open_folder(folder_location)
            # Retrieve all images currently present in the tag_categories_list:
            images = self.controller.retrieve_images_present_in_catalog(sort_images='file_name')
            # Finally, empty the image_list tag_categories_list and refill with the returned images.
            image_list.delete(0, END)  # clear the image_list
            for image_name in images:
                image_list.insert(END, image_name)

        return image_list

    def save_progress(self, savefile_location, taglinewidth, selected_image, min_tagsize):
        """
        This function saves the current project to file.
        """
        if savefile_location is None:
            # First, get a location for the savefile.
            savefile_location = asksaveasfilename(self.master, defaultext='.csv',
                                                  initialfile='picture_tools_savefile.csv',
                                                  title='Please provide a save file name in .csv format')
        if savefile_location is not None and savefile_location != '':
            # Save progress:
            settings = ['taglinewidth;{0}\n'.format(taglinewidth), 'selected_image;{0}\n'.format(selected_image),
                        'savefile_location;{0}\n'.format(savefile_location),
                        'min_tagsize;{0}\n'.format(min_tagsize)]
            self.controller.save_progress(savefile_location, settings)

        return savefile_location

    def load_savefile(self, image_list):
        """
        This function loads a project from a savefile.
        """
        savefile_loc = askopenfilename(self.master, title='Please provide a .csv save file (savefile.csv)')
        if savefile_loc != '':  # check that return value is not empty
            selected_image, taglinewidth, savefile_location, min_tagsize, sorting_method = \
                self.controller.load_savefile(savefile_loc)
            # add images to the image_list and sort:
            image_list = self.viewmethods.sort_images(image_list, sorting_method)
        else:
            selected_image, taglinewidth, savefile_location = None, None, None
            min_tagsize, image_list, sorting_method = None, None, None
        return selected_image, taglinewidth, savefile_location, min_tagsize, image_list, sorting_method

    def export_settings(self, taglinewidth, min_tagsize, sorting_method):
        """
        This function saves the current settings (tag_categories, taglinewidth) so that they can be loaded again for
        a new project independent of earlier used images.
        """
        filename = asksaveasfilename(self.master, defaultext='.csv', initialfile='picture_tools_settings.csv',
                                     title='Please provide a save file name in .csv format')
        if filename != '':  # check that return value is not empty
            settings = ['taglinewidth;{0}\n'.format(taglinewidth),
                        'min_tagsize;{0}\n'.format(min_tagsize),
                        'sorting_method;{0}\n'.format(sorting_method)]
            tag_categories = self.controller.catalog.tag_categories.tag_categories
            for tag_category in tag_categories:
                color = tag_categories[tag_category]
                settings.append('TagCategory;{0};{1}\n'.format(tag_category, color))
            self.controller.write_to_csv(filename, settings)

    def import_settings(self):
        """
        This function imports settings from a previously exported settings (tag_categories, taglinewidth) file.
        """
        settings_location = askopenfilename(self.master, title='Please provide a .csv settings file')
        taglinewidth, min_tagsize = 3, 0
        if settings_location != '':  # check that return value is not empty
            data = self.controller.read_csv(settings_location, ';')
            for line in data:
                if line[0] == 'taglinewidth':
                    taglinewidth = line[1]
                if line[0] == 'TagCategory':
                    self.controller.add_tag_category(line[1], line[2])
                if line[0] == 'min_tagsize':
                    min_tagsize = int(line[1])

        return taglinewidth, min_tagsize

    def export_tags(self, min_tagsize):
        """This function exports the tags to a tensorflow-friendly csv-file"""
        # First, ask for a filename to save the file to:
        csv_file_loc = asksaveasfilename(self.master, defaultext='.csv', initialfile='exported_tags.csv',
                                         title='Please provide a save file name in .csv format (exported_tags.csv)')
        if csv_file_loc != '':  # check that return value is not empty
            data = ["filename,width,height,class,xmin,ymin,xmax,ymax,difficult\n"]
            images = self.controller.catalog.images
            for image_id in images:
                image = images[image_id]
                image_size = image.IMG.size
                tags = image.tags.tag_dict
                for key, value in tags.items():
                    tag_description = value.tag_category
                    tag_coords = value.coordinates
                    tagsize = (tag_coords[2] - tag_coords[0]) * (tag_coords[3] - tag_coords[1])
                    if tagsize > min_tagsize:  # tag area is larger than minimum size
                        data.append("{0},{1},{2},{3},{4},{5},{6},{7},0\n".format(image.file_name, image_size[0],
                                                                                 image_size[1], tag_description,
                                                                                 tag_coords[0], tag_coords[1],
                                                                                 tag_coords[2], tag_coords[3]))
            self.controller.write_to_csv(csv_file_loc, data)
            ms.showinfo("Done", "Exported tags.")

    def load_tag_file(self):
        """
        This function imports tags from a comma-delimited tag file (as generated by export_tags and tensorflow) and
        adds these to the images.
        """
        # First, ask for the location of the save file:
        tag_file_loc = askopenfilename(self.master, title='Please provide a .csv tag file.')
        if tag_file_loc != '':
            tags = self.controller.read_csv(tag_file_loc, ',')
            for line in tags:
                    if line[0] != 'filename':
                        image = line[0]
                        tag = line[3]
                        coords = [int(line[4]), int(line[5]), int(line[6]), int(line[7])]
                        # check whether tag already present is performed in '.add_tag()'
                        self.controller.add_tag(image, tag, coords)


class AddTag:

    value = None

    def __init__(self, master):
        top = self.top = Toplevel(master)
        self.l1 = Label(top, text="Enter new tag")
        self.l1.pack()
        self.e = Entry(top)
        self.e.pack()
        self.b = Button(top, text='Ok', command=self.cleanup)
        self.b.pack()
        self.b2 = Button(top, text='Cancel', command=self.self_destroy)

        self.top.bind('<Return>', lambda e: self.cleanup())

    def cleanup(self):
        self.value = self.e.get()
        self.top.destroy()

    def self_destroy(self):
        self.top.destroy()


class GetTag(Frame):

    value, tag_categories_list = None, None
    button, button2, button3 = None, None, None
    new_tags = []
    key_combination = None

    def __init__(self, master, controller):
        super().__init__()
        self.controller = controller

        # Get all tags present in the image_catalog:
        self.tags = self.controller.catalog.tag_categories.tag_categories
        self.top2 = Toplevel(master)
        self.top2.focus()  # Set the focus to this window so it registers key strokes.
        self.viewmethods = ViewMethods(self.top2, self.controller)
        Frame.__init__(self, self.top2)
        self.grid(sticky=W + E + N + S)
        self.l1 = Label(self.top2)
        self.l1.grid()
        for i in range(10):  # bind all numeric keys
            self.top2.bind(str(i), self.bound)
        self.top2.bind('+', lambda e: self.select_tag_category())
        self.create_popup()

    def bound(self, event):
        value = self.process_keysym(event.keysym)
        if value is not None:  # only accept numeric input
            if self.key_combination is None:
                self.key_combination = value
            else:
                self.key_combination = int(str(self.key_combination) + str(value))

    def select_tag_category(self):
        if self.key_combination is not None:
            self.value = self.get_selected_item()
            self.cleanup()

    def get_selected_item(self):
        """
        This function takes a numeric input (self.key_combination) and finds which tag_category is prepended with that
        number. It returns that tag_category.
        :return: The selected_tag item in the tag_categories_list as string.
        """
        selected_item = None
        for i, listbox_entry in enumerate(self.tag_categories_list.get(0, END)):
            listbox_number = listbox_entry.split('_')[0]
            try:
                key_combination = int(listbox_number)
            except ValueError:
                key_combination = None
            if key_combination == self.key_combination:
                selected_item = listbox_entry

        return selected_item

    @staticmethod
    def process_keysym(keysym):
        """
        This function parses the keyboard input to return a numeric value for entries given with the keypad.
        If the entry is not from the keypad, None is returned.
        :param keysym: keyboard entry value (KP_1 etc.)
        :return: numeric value (1) or None if no keypad entry has been given.
        """
        value = None
        try:
            value = int(keysym)
        except ValueError:
            pass
        return value

    def cancel(self):
        self.value = None
        self.top2.destroy()

    def create_popup(self):
        self.button2 = Button(self.top2, text='Add Tag', command=self.add_tag)
        self.button2.grid(row=0, column=0, sticky=W + E + N + S)
        # create a tag_categories_list to show the tags:
        self.tag_categories_list = Listbox(self.top2, exportselection=0)
        self.tag_categories_list.grid(row=1, column=0, sticky=W + E + N + S)
        tags = [key for key in self.tags]
        tags = sorted(tags)
        for x in tags:
            self.tag_categories_list.insert(END, x)
        self.button = Button(self.top2, text='Enter', command=self.cleanup)
        self.button.grid(row=2, column=0, sticky=W + E + N + S)
        self.button3 = Button(self.top2, text='Cancel', command=self.cancel)
        self.button3.grid(row=3, column=0, sticky=W + E + N + S)
        self.top2.bind('<Return>', lambda e: self.cleanup())
        self.top2.bind('t', lambda e: self.add_tag())
        self.tag_categories_list.bind('<<ListboxSelect>>', lambda e: self.get_value_lb())

    def cleanup(self):
        self.top2.destroy()

    def get_value_lb(self):
        self.value = self.viewmethods.get_selected_item(self.tag_categories_list)

    def add_tag(self):
        self.viewmethods.add_tag_category()
        # destroy and recreate the option list to include the added tag:
        self.tag_categories_list.destroy()
        self.button.destroy()
        self.button2.destroy()
        self.button3.destroy()
        self.create_popup()


class TagMethods:

    def __init__(self, master, controller, viewmethods):
        self.master = master
        self.controller = controller
        self.viewmethods = viewmethods

    def set_active_tag(self, tag_list):
        """
        This function sets an tag to active when selected_tag in the tag_list (tag_categories_list).
        :param tag_list: tag_list listbox.
        :return active_tag_id: the id of the active tag.
        """
        active_tag_id = None
        selected_tag = self.viewmethods.get_selected_item(tag_list)
        if selected_tag is not None:
            tag_id = selected_tag.split('_')[0]
            try:
                active_tag_id = int(tag_id)
            except ValueError:
                active_tag_id = None

        return active_tag_id


class ViewMethods:

    def __init__(self, master, controller):
        self.master = master
        self.controller = controller

    @staticmethod
    def get_selected_item(listbox):
        """
        This function takes a tag_categories_list as input and extracts the selected_tag item in that
        tag_categories_list from it.
        :param listbox: Tkinter tag_categories_list object.
        :return: The selected_tag item in the tag_categories_list as string.
        """
        selected_item = None
        if listbox.size() > 0:
            index = listbox.curselection()
            if index != ():
                selected_item = str((listbox.get(index)))  # gets the currently selected_tag image.
        return selected_item

    def add_tag_category(self):
        """
        Adds a tag category to the tag_categories.
        """
        # Get a value from the User
        gettag = AddTag(self.master)
        self.master.wait_window(gettag.top)
        if gettag.value is not None:
            self.controller.add_tag_category(gettag.value)  # add tag_category to the tag_categories

    @staticmethod
    def ask_directory(master, txt="Please select a folder."):
        """
        This function asks the user for an input directory and returns the path to this directory.
        :param master: master tk-object to bind it to.
        :param txt= (Optional) text to display when asking for an directory.
        :return: Filepath to the directory.
        """
        return askopendirname(master, title=txt)

    def sort_images(self, image_list, sorting_method):
        """
        Sorts the image_list on the filename.
        """
        images = self.controller.retrieve_images_present_in_catalog(sort_images=sorting_method)
        image_list = self.fill_image_list(images, image_list)

        return image_list

    def fill_image_list(self, images, image_list):
        """This function clears the image_list and refills it with the images provided"""
        # Finally, empty the image_list tag_categories_list and refill with the returned images.
        image_list.delete(0, END)  # clear the tag_categories_list
        for image_name in images:
            image_list.insert(END, image_name)
            # Check whether full_image tags are present, if so, give the image background color in the image_list:
            image = self.controller.retrieve_image_object(image_name)
            full_image_tags = self.controller.catalog.extract_full_image_tags(image)
            # full_image_tags now also contains bounding_box_tags, remove these:
            full_image_tags = [i for i in full_image_tags if i != 'no_full_size']
            if len(full_image_tags) > 0:  # full image tags present:
                image_list.itemconfig(END, background='spring green')

        return image_list


class TagLineWidth:
    value = None

    def __init__(self, master):
        top = self.top3 = Toplevel(master)
        self.l1 = Label(top, text="Enter a value for the bounding-box line width (0-10)")
        self.l1.pack()
        self.e = Entry(top)
        self.e.pack()
        self.b = Button(top, text='Ok', command=self.cleanup)
        self.b.pack()

        self.top3.bind('<Return>', lambda e: self.cleanup())

    def cleanup(self):
        value = self.e.get()
        try:
            int(value)
        except ValueError:
            ms.showinfo("Error", "No valid number has been entered.")
            self.top3.destroy()
        self.value = value
        self.top3.destroy()


class KeyBindings:

    def __init__(self, master):
        top = self.top4 = Toplevel(master)
        self.l1 = Label(top, text="Key-Bindings")
        self.l1.pack()
        keybindings = """
        General:

        Ctrl + s\t\t\tSave
        Ctrl + o\t\t\tLoad save file
        Ctrl + Del\t\t\tDelete current image from image list
        Ctrl + Shift + Del\t\tDelete current image from disk
        f\t\t\t\tJump to active image in image list
        Down arrow key\t\tNext image in the list (image list needs to be active, press f)
        Up arrow key\t\t\tPrevious image in the list (image list needs to be active, press f)

        Zooming:

        Ctrl + MouseWheel\t\tZoom in or out
        w\t\t\t\tMove up in zoomed image
        s\t\t\t\tMove down in zoomed image
        a\t\t\t\tMove left in zoomed image
        d\t\t\t\tMove right in zoomed image
        c\t\t\t\tRe-center the image

        Tags:
        
        When adding a tag, a pop-up appears. Tag_category can be selected in 2 ways:
        1) by selecting it in the list
        2) by binding it to a numeric code
        
        To bind a tag_category to a keypad numeric code, prepend the tag_category with '<code>_' when adding a new
        tag_category. For example, bind the code 1144 to tag_category 'AND' > 1144_AND
        Now, when the pop-up is active, press 1144 and then the + key to add this tag.
        
        t\t\t\t\tAdd full image tag.
        Ctrl + Left mouse button\t\tCreate bounding-box tag in image (drag mouse)   
        Ctrl + r\t\t\tDelete selected tag
        r\t\t\t\tModify Tag_category of selected tag
        """

        self.label = Label(top, text=keybindings, font=('Times', 12), justify=LEFT)
        self.label.pack()
        self.b = Button(top, text='Ok', command=self.cleanup)
        self.b.pack()
        self.top4.bind('<Return>', lambda e: self.cleanup())

    def cleanup(self):
        self.top4.destroy()


class UserInput:
    value = None

    def __init__(self, master, message):
        top = self.top5 = Toplevel(master)
        self.l1 = Label(top, text=message)
        self.l1.pack()
        self.e = Entry(top)
        self.e.pack()
        self.b = Button(top, text='Enter', command=self.cleanup)
        self.b.pack()

        self.top5.bind('<Return>', lambda e: self.cleanup())

    def cleanup(self):
        value = self.e.get()
        self.value = value
        self.top5.destroy()


class UserConfirmation:
    value = None

    def __init__(self, master, message):
        top = self.top6 = Toplevel(master)
        self.l1 = Label(top, text=message)
        self.l1.pack()
        self.b1 = Button(top, text='Confirm', command=self.confirm)
        self.b1.pack()
        self.b2 = Button(top, text='Cancel', command=self.cancel)
        self.b2.pack()

    def confirm(self):
        self.value = True
        self.top6.destroy()

    def cancel(self):
        self.value = False
        self.top6.destroy()
