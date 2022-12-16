import math


class Grid:
    
    def __init__(self):
        pass

    @staticmethod
    def canvas_coords_to_image_coords(canvas_coords, canvas_grid_size, pil_image, ratio, image_size):
        """
        This function transforms canvas coordinates to image coordinates.
        :param canvas_coords: canvas coordinates as a list [xmin, ymin, xmax, ymax]
        :param canvas_grid_size: canvas size as tuple (width, height)
        :param pil_image: pil_image of the image on the canvas (resized image)
        :param ratio: the ratio used to scale the original image to fit the canvas
        :param image_size: tuple of imagesize (width, height)
        :return: image coordinates (xmin, ymin, xmax, ymax)
        """
        xmin, xmax = canvas_coords[0], canvas_coords[2]
        ymin, ymax = canvas_coords[1], canvas_coords[3]
        # Calculate how big the resized image and canvas are:
        resized_width = math.floor(ratio * pil_image.size[0])
        resized_height = math.floor(ratio * pil_image.size[1])
        # Now we have the canvas coordinates, but we need to translate them to the image coordinates
        canvas_center = (math.floor(canvas_grid_size[0] / 2), math.floor(canvas_grid_size[1] / 2))
        image_center = (math.floor(resized_width / 2), math.floor(resized_height / 2))
        # Calculate difference canvas center and image center:
        xdiff = canvas_center[0] - image_center[0]
        ydiff = canvas_center[1] - image_center[1]
        # Correct canvas coordinates for this difference to get image coordinates:
        xmin_image, xmax_image = xmin - xdiff, xmax - xdiff
        ymin_image, ymax_image = ymin - ydiff, ymax - ydiff
        # Now we have the coordinates in the image (of the scaled image, so zoomed if image was zoomed):
        image_coords = [xmin_image, ymin_image, xmax_image, ymax_image]
        # correct coords back to original image using the ratio used to scale the image:
        corrected_coords = [math.floor(i / ratio) for i in image_coords]
        # Make sure that the coordinates do not fall below 0 and that the coordinates are not larger than the
        # width/height of the image (if bounding box has been drawn outside the image):
        if corrected_coords[0] < 0:
            corrected_coords[0] = 0
        if corrected_coords[1] < 0:
            corrected_coords[1] = 0
        if corrected_coords[2] > image_size[0]:  # larger than width of image
            corrected_coords[2] = image_size[0]
        if corrected_coords[3] > image_size[1]:  # larger than height of image
            corrected_coords[3] = image_size[1]

        return corrected_coords

    @staticmethod
    def image_coords_to_canvas_coords(image_coords, canvas_grid_size, pil_image, ratio):
        """
        This function transforms image coordinates to canvas coordinates.
        :param image_coords: image coordinates as a list [xmin, ymin, xmax, ymax]
        :param canvas_grid_size: canvas size as tuple (width, height)
        :param pil_image: pil_image of the image on the canvas (resized image)
        :param ratio: the ratio used to scale the original image to fit the canvas
        :return: image coordinates (xmin, ymin, xmax, ymax)
        """
        xmin, xmax = math.floor(image_coords[0] * ratio), math.floor(image_coords[2] * ratio)
        ymin, ymax = math.floor(image_coords[1] * ratio), math.floor(image_coords[3] * ratio)
        # Calculate how big the resized image is:
        resized_width = math.floor(ratio * pil_image.size[0])
        resized_height = math.floor(ratio * pil_image.size[1])
        # Now we have the image coordinates, but we need to translate them to the canvas coordinates
        canvas_center = (math.floor(canvas_grid_size[0] / 2), math.floor(canvas_grid_size[1] / 2))
        image_center = (math.floor(resized_width / 2), math.floor(resized_height / 2))
        # See how much the image coordinates moved from the center point to the measured point.
        # These coordinates show the number of pixels to move from the center to the measured points.
        xmin_moved, xmax_moved = xmin - image_center[0], xmax - image_center[0]
        ymin_moved, ymax_moved = ymin - image_center[1], ymax - image_center[1]
        # Next, move the same number of pixels from the image_center to find the location on the image:
        xmin_image, xmax_image = canvas_center[0] + xmin_moved, canvas_center[0] + xmax_moved
        ymin_image, ymax_image = canvas_center[1] + ymin_moved, canvas_center[1] + ymax_moved
        # Now we have the coordinates in the image:
        canvas_coords = [xmin_image, ymin_image, xmax_image, ymax_image]

        return canvas_coords
