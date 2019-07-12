#pylint: disable=invalid-name,too-many-public-methods,too-many-arguments,non-parent-init-called,R0902,too-many-branches,C0302
import os
import numpy as np

try:
    import qtconsole.inprocess
    from PyQt5.QtCore import pyqtSignal
    from PyQt5.QtWidgets import QWidget, QSizePolicy, QVBoxLayout
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar2
except ImportError:
    from PyQt4.QtGui import QWidget, QSizePolicy, QVBoxLayout
    from PyQt4.QtCore import pyqtSignal
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar2

from matplotlib.figure import Figure
import matplotlib.image

MplLineStyles = ['-', '--', '-.', ':', 'None', ' ', '']
MplLineMarkers = [
    ". (point         )",
    "* (star          )",
    "x (x             )",
    "o (circle        )",
    "s (square        )",
    "D (diamond       )",
    ", (pixel         )",
    "v (triangle_down )",
    "^ (triangle_up   )",
    "< (triangle_left )",
    "> (triangle_right)",
    "1 (tri_down      )",
    "2 (tri_up        )",
    "3 (tri_left      )",
    "4 (tri_right     )",
    "8 (octagon       )",
    "p (pentagon      )",
    "h (hexagon1      )",
    "H (hexagon2      )",
    "+ (plus          )",
    "d (thin_diamond  )",
    "| (vline         )",
    "_ (hline         )",
    "None (nothing    )"]

# Note: in colors, "white" is removed
MplBasicColors = [
    "black",
    "red",
    "blue",
    "green",
    "cyan",
    "magenta",
    "yellow"]


class MplGraphicsView2D(QWidget):
    """ A combined graphics view including matplotlib canvas and
    a navigation tool bar

    Note: Merged with HFIR_Powder_Reduction.MplFigureCAnvas
    """
    def __init__(self, parent):
        """ Initialization
        """
        # Initialize parent
        super(MplGraphicsView2D, self).__init__(parent)

        # set up canvas
        self._myCanvas = Qt4Mpl2DCanvas(self)
        self._myToolBar = MyNavigationToolbar(self, self._myCanvas)

        # state of zoom
        self._isZoomedFromHome = False   # figure is zoomed from home
        self._mousePressedInZoom = False  # flag that the zoom key is pressed down

        # X and Y limit with home button
        self._homeXYLimit = None  # if used, it shall be a 4-element list as min x, max x, min y, max y
        self._zoomInXRange = None  # if used, it shall be a 4-element list as min x, max x, min y, max y

        # set up layout
        self._vBox = QVBoxLayout(self)
        self._vBox.addWidget(self._myCanvas)
        self._vBox.addWidget(self._myToolBar)

        # list of arrows
        self._arrowList = list()

        #
        self._hasImage = False

        return

    def add_arrow(self, start_x, start_y, stop_x, stop_y):
        """ add an arrow to the image
        :param start_x:
        :param start_y:
        :param stop_x:
        :param stop_y:
        :return:
        """
        arrow = self._myCanvas.add_arrow(start_x, start_y, stop_x, stop_y)
        self._arrowList.append(arrow)

        return

    def add_image(self, image_file_name):
        """ Add an image to canvas by file
        """
        # check
        if os.path.exists(image_file_name) is False:
            raise RuntimeError("Image file %s does not exist." % image_file_name)

        self._myCanvas.add_image_file(image_file_name)

        return

    def add_2d_plot(self, array2d, x_min, x_max, y_min, y_max, y_tick_label=None, plot_type='image'):
        """
        Add a 2D image to canvas
        :param array2d: numpy 2D array
        :param x_min:
        :param x_max:
        :param y_min:
        :param y_max:
        :param y_tick_label:
        :param plot_type:s
        :return:
        """
        # obsoleted: self._myCanvas.addPlot2D(array2d, x_min, x_max, y_min, y_max, hold_prev_image, y_tick_label)

        if plot_type == 'image':
            # regular image
            self._myCanvas.add_image_plot(array2d, x_min, x_max, y_min, y_max, yticklabels=y_tick_label)
        elif plot_type == 'scatter':
            # 2D scatters
            self._myCanvas.add_scatter_plot(array2d)
        else:
            raise RuntimeError('Plot type {} of type {} is not supported.  Present supported plot types include '
                               'image and scatter of type string'.format(plot_type, type(plot_type)))

        self._hasImage = True

        return

    @property
    def canvas(self):
        """ Get the canvas
        :return:
        """
        return self._myCanvas

    def clear_canvas(self):
        """ Clear canvas
        """
        # clear all the records
        # to-be-filled

        # about zoom
        # to-be-filled

        self._myCanvas.clear_canvas()

        return

    def draw(self):
        """ Draw to commit the change
        """
        return self._myCanvas.draw()

    def evt_toolbar_home(self):
        """ event triggered as home is pressed in tool bar
        @return:
        """
        # turn off zoom mode
        self._isZoomedFromHome = False
        self._mousePressedInZoom = False

        # reset zoom in X range
        self._zoomInXRange = None

        print ('[DB...FIND] Tool Bar Home Triggered')

        return

    def evt_view_updated(self):
        """ Event handling as canvas size updated
        :return:
        """
        print ('[DB...FIND] View is updated.  From {}'.format(self.__class__.__name__))

        # # update the indicator
        # new_x_range = self.getXLimit()
        # new_y_range = self.getYLimit()
        #
        # self._myIndicatorsManager.update_indicators_range(new_x_range, new_y_range)
        # for indicator_key in self._myIndicatorsManager.get_live_indicator_ids():
        #     canvas_line_id = self._myIndicatorsManager.get_canvas_line_index(indicator_key)
        #     data_x, data_y = self._myIndicatorsManager.get_data(indicator_key)
        #     self.updateLine(canvas_line_id, data_x, data_y)
        # # END-FOR

        return

    def evt_zoom_pressed(self):
        """ event triggered as when mouse key is pressed down while the zoom button is in pressed-down state
        It is paired with evt_press_released
        :return:
        """
        self._mousePressedInZoom = True

        return

    def evt_zoom_released(self):
        """ event for zoom is release
        @return:
        """
        self._mousePressedInZoom = True
        # zoom-in range
        if self.has_image_on_canvas():
            self._zoomInXRange = self.current_x_range()

        return

    def getLastPlotIndexKey(self):
        """ Get ...
        """
        return self._myCanvas.getLastPlotIndexKey()

    def current_x_range(self):
        """ Get limit of Y-axis
        :return: 2-tuple as xmin, xmax
        """
        return self._myCanvas.getXLimit()

    def getYLimit(self):
        """ Get limit of Y-axis
        """
        return self._myCanvas.getYLimit()

    def get_y_min(self):
        """
        Get the minimum Y value of the plots on canvas
        :return:
        """
        if len(self._statDict) == 0:
            return 1E10

        line_id_list = self._statDict.keys()
        min_y = self._statDict[line_id_list[0]][2]
        for i_plot in range(1, len(line_id_list)):
            if self._statDict[line_id_list[i_plot]][2] < min_y:
                min_y = self._statDict[line_id_list[i_plot]][2]

        return min_y

    def get_y_max(self):
        """
        Get the maximum Y value of the plots on canvas
        :return:
        """
        if len(self._statDict) == 0:
            return -1E10

        line_id_list = self._statDict.keys()
        max_y = self._statDict[line_id_list[0]][3]
        for i_plot in range(1, len(line_id_list)):
            if self._statDict[line_id_list[i_plot]][3] > max_y:
                max_y = self._statDict[line_id_list[i_plot]][3]

        return max_y

    def has_image_on_canvas(self):
        """ state whether there is an image plot on canvas
        @return:
        """
        return self._hasImage

    def move_indicator(self, line_id, dx, dy):
        """
        Move the indicator line in horizontal
        :param line_id:
        :param dx:
        :return:
        """
        # Shift value
        self._myIndicatorsManager.shift(line_id, dx=dx, dy=dy)

        # apply to plot on canvas
        if self._myIndicatorsManager.get_line_type(line_id) < 2:
            # horizontal or vertical
            canvas_line_index = self._myIndicatorsManager.get_canvas_line_index(line_id)
            vec_x, vec_y = self._myIndicatorsManager.get_data(line_id)
            self._myCanvas.updateLine(ikey=canvas_line_index, vecx=vec_x, vecy=vec_y)
        else:
            # 2-way
            canvas_line_index_h, canvas_line_index_v = self._myIndicatorsManager.get_canvas_line_index(line_id)
            h_vec_set, v_vec_set = self._myIndicatorsManager.get_2way_data(line_id)

            self._myCanvas.updateLine(ikey=canvas_line_index_h, vecx=h_vec_set[0], vecy=h_vec_set[1])
            self._myCanvas.updateLine(ikey=canvas_line_index_v, vecx=v_vec_set[0], vecy=v_vec_set[1])

        return

    def plot_image(self, data_set_dict):
        """ Plot 2D data as a contour plot
        :param data_set_dict: dictionary such that
        :return:
        """
        # Check inputs
        assert isinstance(data_set_dict, dict), 'Input data must be in a dictionary but not a {0}' \
                                                ''.format(type(data_set_dict))

        # construct
        x_list = sorted(data_set_dict.keys())
        vec_x = data_set_dict[x_list[0]][0]
        vec_y = np.array(x_list)
        size_x = len(vec_x)

        # create matrix on mesh
        grid_shape = len(vec_y), len(vec_x)
        matrix_y = np.ndarray(grid_shape, dtype='float')
        matrix_index = 0
        for index in vec_y:
            # vector X
            vec_x_i = data_set_dict[index][0]
            if len(vec_x_i) != size_x:
                raise RuntimeError('Unable to form a contour plot because {0}-th vector has a different size {1} '
                                   'than first size {2}'.format(index, len(vec_x_i), size_x))

            # vector Y: each row will have the value of a pattern
            matrix_y[matrix_index:] = data_set_dict[index][1]  #
            matrix_index += 1
        # END-FOR

        # clear canvas and add contour plot
        if self.canvas.has_plot('image'):
            self.canvas.update_image(matrix_y)
        else:
            self.add_2d_plot(array2d=matrix_y, x_min=min(vec_x), x_max=max(vec_x),
                             y_min=0, y_max=10, plot_type='image')

        return

    def remove_indicator(self, indicator_key):
        """ Remove indicator line
        :param indicator_key:
        :return:
        """
        #
        plot_id = self._myIndicatorsManager.get_canvas_line_index(indicator_key)
        self._myCanvas.remove_plot_1d(plot_id)
        self._myIndicatorsManager.delete(indicator_key)

        return

    def remove_line(self, line_id):
        """ Remove a line
        :param line_id:
        :return:
        """
        # remove line
        self._myCanvas.remove_plot_1d(line_id)

        # remove the records
        if line_id in self._statDict:
            del self._statDict[line_id]
            del self._my1DPlotDict[line_id]
        else:
            del self._statRightPlotDict[line_id]

        return

    def set_title(self, title, color='black'):
        """
        set title to canvas
        :param title:
        :param color:
        :return:
        """
        self._myCanvas.set_title(title, color)

        return

    def setXYLimit(self, xmin=None, xmax=None, ymin=None, ymax=None):
        """ Set X-Y limit automatically
        """
        self._myCanvas.axes.set_xlim([xmin, xmax])
        self._myCanvas.axes.set_ylim([ymin, ymax])

        self._myCanvas.draw()

        return

    def update_2d_plot(self):
        """ update 2D plot
        @return:
        """
        raise RuntimeError('Base class of {}: virtual method update_2d_plot'.format(self.__class__.__name__))


class Qt4Mpl2DCanvas(FigureCanvas):
    """  A customized Qt widget for matplotlib figure.
    It can be used to replace GraphicsView of QtGui
    """
    def __init__(self, parent):
        """  Initialization
        """
        # Instantiating matplotlib Figure
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')

        # initialization
        super(Qt4Mpl2DCanvas, self).__init__(self.fig)

        # set up axis/subplot (111) only for 2D
        self.axes = self.fig.add_subplot(111)  # return: matplotlib.axes.AxesSubplot
        self.fig.subplots_adjust(bottom=0.15)
        self.axes2 = None

        # plot management
        self._scatterPlot = None
        self._imagePlot = None

        # Initialize parent class and set parent
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        # Set size policy to be able to expanding and resizable with frame
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # Variables to manage all lines/subplot
        self._lineDict = {}
        self._lineIndex = 0

        # legend and color bar
        self._colorBar = None
        self._isLegendOn = False
        self._legendFontSize = 8

        return

    def update_image(self, array2d):
        """

        @return:
        """

        self._imagePlot.set_data(array2d)

        self._flush()

        return

    def has_plot(self, plot_type):
        if plot_type == 'image' and self._imagePlot is not None:
            return True

        return False

    @property
    def is_legend_on(self):
        """
        check whether the legend is shown or hide
        Returns:
        boolean
        """
        return self._isLegendOn

    def add_arrow(self, start_x, start_y, stop_x, stop_y):
        """
        Example: (0, 0, 0.5, 0.5, head_width=0.05, head_length=0.1, fc='k', ec='k')
        @param start_x:
        @param start_y:
        @param stop_x:
        @param stop_y:
        @return:
        """
        head_width = 0.05
        head_length = 0.1
        fc = 'k'
        ec = 'k'

        arrow = self.axes.arrrow(start_x, start_y, stop_x, stop_y, head_width,
                                 head_length, fc, ec)

        return arrow

    def add_contour_plot(self, vec_x, vec_y, matrix_z, use_contour=True):
        """ add a contour plot
        Example: reduced data: vec_x: d-values, vec_y: run numbers, matrix_z, matrix for intensities
        :param vec_x: a list of a vector for X axis
        :param vec_y: a list of a vector for Y axis
        :param matrix_z:
        :param use_contour: Flag to plot with contourf. otherwise, plot with imshow() without interpolation
        :return:
        """
        # check input
        assert isinstance(vec_x, list) or isinstance(vec_x, np.ndarray), 'Vector of X {} must be either a list ' \
                                                                         'or a numpy.ndarray but not of type {}' \
                                                                         ''.format(vec_x, type(vec_x))
        assert isinstance(vec_y, list) or isinstance(vec_y, np.ndarray), 'Vector of Y {} must be either a list ' \
                                                                         'or a numpy.ndarray but not of type {}' \
                                                                         ''.format(vec_y, type(vec_y))
        assert isinstance(matrix_z, np.ndarray), 'Matrix Z {} must be a numpy.ndarray but not of type {}' \
                                                 ''.format(matrix_z, type(matrix_z))

        # create mesh grid
        grid_x, grid_y = np.meshgrid(vec_x, vec_y)
        #
        # print '[DB...BAT] Grid X and Grid Y size: ', grid_x.shape, grid_y.shape

        # check size
        if grid_x.shape != matrix_z.shape:
            raise RuntimeError('Size of X (%d) and Y (%d) must match size of Z (%s).'
                               '' % (len(vec_x), len(vec_y), matrix_z.shape))

        # Do plot: resolution on Z axis (color bar is set to 100)
        self.axes.clear()
        if use_contour:
            contour_plot = self.axes.contourf(grid_x, grid_y, matrix_z, 100)
        else:
            self._imagePlot = self.axes.imshow(matrix_z,
                                               extent=[grid_x.min(), grid_x.max(),
                                                       grid_y.min(), grid_y.max()],
                                               interpolation='none')
        # END-IF-ELSE: Try different plotting option

        labels = [item.get_text() for item in self.axes.get_yticklabels()]
        print '[DB...BAT] Number of Y labels = ', len(labels), ', Number of Y = ', len(vec_y)

        # TODO/ISSUE/NOW: how to make this part more flexible
        if len(labels) == 2*len(vec_y) - 1:
            new_labels = [''] * len(labels)
            for i in range(len(vec_y)):
                new_labels[i*2] = '%d' % int(vec_y[i])
            self.axes.set_yticklabels(new_labels)
        # END-IF

        # explicitly set aspect ratio of the image
        self.axes.set_aspect('auto')

        if False:  # contour
            # Set color bar.  plt.colorbar() does not work!
            if self._colorBar is None:
                # set color map type
                contour_plot.set_cmap('spectral')
                self._colorBar = self.fig.colorbar(contour_plot)
            else:
                self._colorBar.update_bruteforce(contour_plot)

        # Flush...
        self._flush()

    def add_image_plot(self, array2d, xmin, xmax, ymin, ymax, yticklabels=None):
        """

        @param array2d:
        @param xmin:
        @param xmax:
        @param ymin:
        @param ymax:
        @param holdprev:
        @param yticklabels: list of string for y ticks
        @return:
        """
        # check
        assert isinstance(array2d, np.ndarray), 'blabla'
        assert len(array2d.shape) == 2, 'blabla'

        # show image
        self._imagePlot = self.axes.imshow(array2d, extent=[xmin, xmax, ymin, ymax], interpolation='none')

        print (self._imagePlot, type(self._imagePlot))

        # set y ticks as an option:
        if yticklabels is not None:
            # it will always label the first N ticks even image is zoomed in
            print ("[FIXME]: The way to set up the Y-axis ticks is wrong!")
            self.axes.set_yticklabels(yticklabels)

        # explicitly set aspect ratio of the image
        self.axes.set_aspect('auto')

        # set up color bar
        # # Set color bar.  plt.colorbar() does not work!
        # if self._colorBar is None:
        #     # set color map type
        #     imgplot.set_cmap('spectral')
        #     self._colorBar = self.fig.colorbar(imgplot)
        # else:
        #     self._colorBar.update_bruteforce(imgplot)

        # Flush...
        self._flush()

        return

    def add_image_file(self, imagefilename):
        """ Add an image by file
        """
        #import matplotlib.image as mpimg

        # set aspect to auto mode
        self.axes.set_aspect('auto')

        img = matplotlib.image.imread(str(imagefilename))
        # lum_img = img[:,:,0]
        # FUTURE : refactor for image size, interpolation and origin
        imgplot = self.axes.imshow(img, extent=[0, 1000, 800, 0], interpolation='none', origin='lower')

        # Set color bar.  plt.colorbar() does not work!
        if self._colorBar is None:
            # set color map type
            imgplot.set_cmap('spectral')
            self._colorBar = self.fig.colorbar(imgplot)
        else:
            self._colorBar.update_bruteforce(imgplot)

        self._flush()

        return

    def add_scatter_plot(self, array2d):
        """
        add scatter plot
        @param array2d:
        @return:
        """
        # check!
        assert isinstance(array2d, np.ndarray), 'blabla'
        if array2d.shape[1] < 3:
            raise RuntimeError('blabla3')

        if False:
            array2d = np.ndarray(shape=(100, 3), dtype='float')
            array2d[0][0] = 0
            array2d[0][1] = 0
            array2d[0][2] = 1

            import random
            for index in range(1, 98):
                x = random.randint(1, 255)
                y = random.randint(1, 255)
                z = random.randint(1, 20000)
                array2d[index][0] = float(x)
                array2d[index][1] = float(y)
                array2d[index][2] = float(z)

            array2d[99][0] = 255
            array2d[99][1] = 255
            array2d[99][2] = 1

        self._scatterPlot = self.axes.scatter(array2d[:, 0], array2d[:, 1], s=80, c=array2d[:, 2],
                                              marker='s')

        return

    def clear_canvas(self):
        """ Clear data including lines and image from canvas
        """
        # clear the image for next operation
        # self.axes.hold(False)

        # clear image
        self.axes.cla()
        # Try to clear the color bar
        if len(self.fig.axes) > 1:
            self.fig.delaxes(self.fig.axes[1])
            self._colorBar = None
            # This clears the space claimed by color bar but destroys sub_plot too.
            self.fig.clear()
            # Re-create subplot
            self.axes = self.fig.add_subplot(111)
            self.fig.subplots_adjust(bottom=0.15)

        # flush/commit
        self._flush()

        return

    def decrease_legend_font_size(self):
        """
        reset the legend with the new font size
        Returns:

        """
        # minimum legend font size is 2! return if it already uses the smallest font size.
        if self._legendFontSize <= 2:
            return

        self._legendFontSize -= 1
        self._setup_legend(font_size=self._legendFontSize)

        self.draw()

        return

    def getLastPlotIndexKey(self):
        """ Get the index/key of the last added line
        """
        return self._lineIndex-1

    def getPlot(self):
        """ reture figure's axes to expose the matplotlib figure to PyQt client
        """
        return self.axes

    def getXLimit(self):
        """
        Get limit of Y-axis
        :return: list of 2 float as min X and max X
        """
        return self.axes.get_xlim()

    def getYLimit(self):
        """ Get limit of Y-axis
        """
        return self.axes.get_ylim()

    def hide_legend(self):
        """
        hide the legend if it is not None
        Returns:

        """
        if self.axes.legend() is not None:
            # set visible to be False and re-draw
            self.axes.legend().set_visible(False)
            self.draw()

        self._isLegendOn = False

        return

    def increase_legend_font_size(self):
        """
        reset the legend with the new font size
        Returns:

        """
        self._legendFontSize += 1

        self._setup_legend(font_size=self._legendFontSize)

        self.draw()

        return

    def setXYLimit(self, xmin, xmax, ymin, ymax):
        """
        """
        # for X
        xlims = self.axes.get_xlim()
        xlims = list(xlims)
        if xmin is not None:
            xlims[0] = xmin
        if xmax is not None:
            xlims[1] = xmax
        self.axes.set_xlim(xlims)

        # for Y
        ylims = self.axes.get_ylim()
        ylims = list(ylims)
        if ymin is not None:
            ylims[0] = ymin
        if ymax is not None:
            ylims[1] = ymax
        self.axes.set_ylim(ylims)

        # try draw
        self.draw()

        return

    def set_title(self, title, color):
        """
        set the tile to an axis
        :param title:
        :param color
        :return:
        """
        # check input
        assert isinstance(title, str), 'Title must be a string but not a {0}.'.format(type(title))
        assert isinstance(color, str), 'Color must be a string but not a {0}.'.format(type(color))

        print '[DB...BAT] Set {0} in color {1} as the figure\'s title.'.format(title, color)
        self.setWindowTitle(title)

        self.draw()

        return

    def remove_plot_1d(self, plot_key):
        """ Remove the line with its index as key
        :param plot_key:
        :return:
        """
        # Get all lines in list
        lines = self.axes.lines
        assert isinstance(lines, list), 'Lines must be list'

        if plot_key in self._lineDict:
            try:
                self.axes.lines.remove(self._lineDict[plot_key])
            except ValueError as r_error:
                error_message = 'Unable to remove to 1D line %s (ID=%d) due to %s.' % (str(self._lineDict[plot_key]),
                                                                                       plot_key, str(r_error))
                raise RuntimeError(error_message)
            # remove the plot key from dictionary
            del self._lineDict[plot_key]
        else:
            raise RuntimeError('Line with ID %s is not recorded.' % plot_key)

        self._setup_legend(location='best', font_size=self._legendFontSize)

        # Draw
        self.draw()

        return

    def show_legend(self):
        """
        show the legend if the legend is not None
        Returns:

        """
        if self.axes.legend() is not None:
            # set visible to be True and re-draw
            # self.axes.legend().set_visible(True)
            self._setup_legend(font_size=self._legendFontSize)
            self.draw()

            # set flag on
            self._isLegendOn = True

        return

    def get_data(self, line_id):
        """
        Get vecX and vecY from line object in matplotlib
        :param line_id:
        :return: 2-tuple as vector X and vector Y
        """
        # check
        if line_id not in self._lineDict:
            raise KeyError('Line ID %s does not exist.' % str(line_id))

        # get line
        line = self._lineDict[line_id]
        if line is None:
            raise RuntimeError('Line ID %s has been removed.' % line_id)

        return line.get_xdata(), line.get_ydata()

    def getLineStyleList(self):
        """
        """
        return MplLineStyles

    def getLineMarkerList(self):
        """
        """
        return MplLineMarkers

    def getLineBasicColorList(self):
        """
        """
        return MplBasicColors

    def getDefaultColorMarkerComboList(self):
        """ Get a list of line/marker color and marker style combination
        as default to add more and more line to plot
        """
        combo_list = list()
        num_markers = len(MplLineMarkers)
        num_colors = len(MplBasicColors)

        for i in xrange(num_markers):
            marker = MplLineMarkers[i]
            for j in xrange(num_colors):
                color = MplBasicColors[j]
                combo_list.append((marker, color))
            # ENDFOR (j)
        # ENDFOR(i)

        return combo_list

    def _flush(self):
        """ A dirty hack to flush the image
        """
        w, h = self.get_width_height()
        self.resize(w+1, h)
        self.resize(w, h)

        return

    def _setup_legend(self, location='best', font_size=10):
        """
        Set up legend
        self.axes.legend(): Handler is a Line2D object. Lable maps to the line object
        Args:
            location:
            font_size:

        Returns:

        """
        allowed_location_list = [
            "best",
            "upper right",
            "upper left",
            "lower left",
            "lower right",
            "right",
            "center left",
            "center right",
            "lower center",
            "upper center",
            "center"]

        # Check legend location valid or not
        if location not in allowed_location_list:
            location = 'best'

        handles, labels = self.axes.get_legend_handles_labels()
        self.axes.legend(handles, labels, loc=location, fontsize=font_size)

        self._isLegendOn = True

        return

# END-OF-CLASS (MplGraphicsView)


class MyNavigationToolbar(NavigationToolbar2):
    """ A customized navigation tool bar attached to canvas
    Note:
    * home, left, right: will not disable zoom/pan mode
    * zoom and pan: will turn on/off both's mode

    Other methods
    * drag_pan(self, event): event handling method for dragging canvas in pan-mode
    """
    NAVIGATION_MODE_NONE = 0
    NAVIGATION_MODE_PAN = 1
    NAVIGATION_MODE_ZOOM = 2

    # This defines a signal called 'home_button_pressed' that takes 1 boolean
    # argument for being in zoomed state or not
    home_button_pressed = pyqtSignal()
    # This defines a signal called 'canvas_zoom_released'
    canvas_zoom_released = pyqtSignal()
    # zoom is pressed
    zoom_pressed = pyqtSignal()
    # view is updated
    view_updated_signal = pyqtSignal(name='ViewUpdatedSignal')

    def __init__(self, parent, canvas):
        """ Initialization
        built-in methods
        - drag_zoom(self, event): triggered during holding the mouse and moving
        """
        NavigationToolbar2.__init__(self, canvas, canvas)

        # parent
        self._myParent = parent
        # tool bar mode
        self._myMode = MyNavigationToolbar.NAVIGATION_MODE_NONE

        # connect the events to parent
        self.home_button_pressed.connect(self._myParent.evt_toolbar_home)
        self.zoom_pressed.connect(self._myParent.evt_zoom_pressed)
        self.canvas_zoom_released.connect(self._myParent.evt_zoom_released)
        self.view_updated_signal.connect(self._myParent.evt_view_updated)

        return

    @property
    def is_zoom_mode(self):
        """
        check whether the tool bar is in zoom mode
        Returns
        -------

        """
        return self._myMode == MyNavigationToolbar.NAVIGATION_MODE_ZOOM

    def get_mode(self):
        """
        :return: integer as none/pan/zoom mode
        """
        return self._myMode

    # Overriding base's methods
    def draw(self):
        """
        Canvas is drawn called by pan(), zoom()
        :return:
        """
        # draw!
        super(MyNavigationToolbar, self).draw()
        # NavigationToolbar2.draw(self)

        # send a signal to notify window
        self.view_updated_signal.emit()

        #  self._myParent.evt_view_updated()

        return

    def home(self, *args):
        """ handle the event that is emitted as the home-button is pressed
        :param args:
        :return:
        """
        # call super's home() method
        super(MyNavigationToolbar, self).home(args)

        # send a signal to parent class for further operation
        self.home_button_pressed.emit()

        return

    def pan(self, *args):
        """

        :param args:
        :return:
        """
        NavigationToolbar2.pan(self, args)

        if self._myMode == MyNavigationToolbar.NAVIGATION_MODE_PAN:
            # out of pan mode
            self._myMode = MyNavigationToolbar.NAVIGATION_MODE_NONE
        else:
            # into pan mode
            self._myMode = MyNavigationToolbar.NAVIGATION_MODE_PAN

        return

    def press_zoom(self, event):
        """ event emit when mouse is pressed while the zoom button is pushed to on-mode
        :param event:
        :return:
        """
        super(MyNavigationToolbar, self).press_zoom(event)

        self.zoom_pressed.emit()

        return

    def release_zoom(self, event):
        """ override zoom released method
        :param event:
        :return:
        """
        try:
            super(MyNavigationToolbar, self).release_zoom(event)
        except ValueError as run_err:
            print ('[ERROR-Caught] Release Zoom: {}'.format(run_err))

        self.canvas_zoom_released.emit()

        return

    def _update_view(self):
        """
        view update called by home(), back() and forward()
        :return:
        """
        # NavigationToolbar2._update_view(self)
        # call base class to update view
        super(MyNavigationToolbar, self)._update_view()

        # send signal
        self.view_updated_signal.emit()
        # self._myParent.evt_view_updated()

        return

    def zoom(self, *args):
        """
        Turn on/off zoom (zoom button)
        :param args:
        :return:
        """
        NavigationToolbar2.zoom(self, args)

        if self._myMode == MyNavigationToolbar.NAVIGATION_MODE_ZOOM:
            # out of zoom mode
            self._myMode = MyNavigationToolbar.NAVIGATION_MODE_NONE
        else:
            # into zoom mode
            self._myMode = MyNavigationToolbar.NAVIGATION_MODE_ZOOM

        return
