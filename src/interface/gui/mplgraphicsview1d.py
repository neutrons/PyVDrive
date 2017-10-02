#pylint: disable=invalid-name,too-many-public-methods,too-many-arguments,non-parent-init-called,R0902,too-many-branches,C0302
"""
Graphics class with matplotlib backend specific for advanced 1D plot
"""
import os
import numpy as np

from PyQt4 import QtGui, QtCore
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


class MplGraphicsView1D(QtGui.QWidget):
    """ A combined graphics view including matplotlib canvas and a navigation tool bar
    1. specific for 1-D data
    2.
    """
    def __init__(self, parent, row_size, col_size):
        """Initialization
        :param parent:
        :param row_size: number of figures per column, i.e., number of rows
        :param col_size: number of figures per row, i.e., number of columns
        """
        # Initialize parent
        QtGui.QWidget.__init__(self, parent)

        # set up canvas
        self._myCanvas = Qt4MplCanvas(self)
        self._myToolBar = MyNavigationToolbar(self, self._myCanvas)

        # state of operation
        self._isZoomed = False
        # X and Y limit with home button
        self._homeXYLimit = None

        # set up layout
        self._vBox = QtGui.QVBoxLayout(self)
        self._vBox.addWidget(self._myCanvas)
        self._vBox.addWidget(self._myToolBar)

        # auto line's maker+color list
        self._myLineMarkerColorList = []
        self._myLineMarkerColorIndex = 0
        self.setAutoLineMarkerColorCombo()

        # records for all the lines that are plot on the canvas
        self._my1DPlotDict = dict()

        # some statistic recorder for convenient operation
        self._statDict = dict()
        self._statRightPlotDict = dict()

        return

    def add_arrow(self, start_x, start_y, stop_x, stop_y):
        """

        :param start_x:
        :param start_y:
        :param stop_x:
        :param stop_y:
        :return:
        """
        self._myCanvas.add_arrow(start_x, start_y, stop_x, stop_y)

        return

    def add_plot(self, vec_x, vec_y, y_err=None, row_index=0, col_index=0, is_right=False, color=None, label='',
                 x_label=None, y_label=None, marker=None, line_style=None, line_width=1, show_legend=True):
        """Add a plot in 1D
        :param row_index:
        :param col_index:
        :param is_right:
        :param vec_x:
        :param vec_y:
        :param y_err:
        :param color:
        :param label:
        :param x_label:
        :param y_label:
        :param marker:
        :param line_style:
        :param line_width:
        :param show_legend:
        :return:
        """
        # check whether the input is empty
        if len(vec_y) == 0:
            print '[WARNING] Input is an empty vector set'
            return False

        if is_right:
            line_key = self._myCanvas.add_1d_plot_right(vec_x, vec_y, label=label,
                                                        color=color, marker=marker,
                                                        linestyle=line_style, linewidth=line_width)

            self._statRightPlotDict[line_key] = (min(vec_x), max(vec_x), min(vec_y), max(vec_y))
        else:
            line_key = self._myCanvas.add_plot_1d(vec_x, vec_y, y_err, color, label, x_label, y_label, marker, line_style,
                                              line_width, show_legend)

        # record min/max
        self._statDict[line_key] = min(vec_x), max(vec_x), min(vec_y), max(vec_y)
        self._my1DPlotDict[line_key] = label

        # update minimum and maximum
        self._update_plot_line_information(remove_line=False, self._statDict[line_key])

        return line_key

    def auto_rescale(self, vec_y=None):
        """
        rescale the canvas in an automatic way
        :return:
        """
        # TODO/ISSUE/62/GENERAL - How about the definition of _maxX, _maxY,..., ...
        # get right_x_bound and upper_y_bound
        delta_x = self._maxX
        delta_y = self._maxY

        right_x_bound = self._maxX + 0.05 * delta_x
        upper_y_bound = self._maxY + 0.05 * delta_y

        # set optionally xmin
        curr_x_min, curr_x_max = self.getXLimit()
        if curr_x_min > right_x_bound:
            left_x_bound = 0.
        else:
            left_x_bound = None

        # FIXME - This is not good!
        if vec_y is None:
            curr_y_min, curr_y_max = self.get_y_limit()
            if curr_y_min > upper_y_bound:
                lower_y_bound = 0.
            else:
                lower_y_bound = None
        else:
            min_y = min(vec_y)
            max_y = max(vec_y)
            dy = max_y - min_y
            lower_y_bound = min(0, min_y - dy * 0.05)
            upper_y_bound = max_y + dy * 0.05
        # END-IF-ELSE

        self.setXYLimit(xmin=left_x_bound, xmax=right_x_bound, ymin=lower_y_bound, ymax=upper_y_bound)

        return

    def canvas(self):
        """ Get the canvas
        :return:
        """
        return self._myCanvas

    def clear_all_lines(self):
        """
        """
        self._myCanvas.clear_all_1d_plots()

        self._statRightPlotDict.clear()
        self._statDict.clear()
        self._my1DPlotDict.clear()

        # about zoom
        self._isZoomed = False
        self._homeXYLimit = None

        return

    def clear_canvas(self):
        """ Clear canvas
        """
        # clear all the records
        self._statDict.clear()
        self._my1DPlotDict.clear()

        # about zoom
        self._isZoomed = False
        self._homeXYLimit = None

        return self._myCanvas.clear_canvas()

    def clear_line(self, row_index, col_index):
        """clear one specific line
        :param row_index:
        :param col_index:
        :return:
        """



    def draw(self):
        """ Draw to commit the change
        """
        return self._myCanvas.draw()

    def evt_toolbar_home(self):
        """

        Parameters
        ----------

        Returns
        -------

        """
        # turn off zoom mode
        self._isZoomed = False

        return

    def evt_view_updated(self):
        """ Event handling as canvas size updated
        :return:
        """
        # update the indicator
        new_x_range = self.getXLimit()
        new_y_range = self.get_y_limit()

        self._myIndicatorsManager.update_indicators_range(new_x_range, new_y_range)
        for indicator_key in self._myIndicatorsManager.get_live_indicator_ids():
            canvas_line_id = self._myIndicatorsManager.get_canvas_line_index(indicator_key)
            data_x, data_y = self._myIndicatorsManager.get_data(indicator_key)
            self.update_line(canvas_line_id, data_x, data_y)
        # END-FOR

        return

    def evt_zoom_released(self):
        """
        event for zoom is release
        Returns
        -------

        """
        # record home XY limit if it is never zoomed
        if self._isZoomed is False:
            self._homeXYLimit = list(self.getXLimit())
            self._homeXYLimit.extend(list(self.get_y_limit()))
        # END-IF

        # set the state of being zoomed
        self._isZoomed = True

        return

    def getPlot(self):
        """
        """
        return self._myCanvas.getPlot()

    def getLastPlotIndexKey(self):
        """ Get ...
        """
        return self._myCanvas.getLastPlotIndexKey()

    def get_y_limit(self):
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

    def get_canvas(self):
        """
        get canvas
        Returns:

        """
        return self._myCanvas

    def get_current_plots(self):
        """
        Get the current plots on canvas
        Returns
        -------
        list of 2-tuple: integer (plot ID) and string (label)
        """
        tuple_list = list()
        line_id_list = sorted(self._my1DPlotDict.keys())
        for line_id in line_id_list:
            tuple_list.append((line_id, self._my1DPlotDict[line_id]))

        return tuple_list

    def get_indicator_key(self, x, y):
        """ Get the key of the indicator with given position
        :param picker_pos:
        :return:
        """
        return self._myIndicatorsManager.get_indicator_key(x, y)

    def get_indicator_position(self, indicator_key):
        """ Get position (x or y) of the indicator
        :param indicator_key
        :return: a tuple.  (0) horizontal (x, x); (1) vertical (y, y); (2) 2-way (x, y)
        """
        # Get indicator's type
        indicator_type = self._myIndicatorsManager.get_line_type(indicator_key)
        if indicator_type < 2:
            # horizontal or vertical indicator
            x, y = self._myIndicatorsManager.get_data(indicator_key)

            if indicator_type == 0:
                # horizontal
                return y[0], y[0]

            elif indicator_type == 1:
                # vertical
                return x[0], x[0]

        else:
            # 2-way
            raise RuntimeError('Implement 2-way as soon as possible!')

        return 1.E100, 1.E100

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
        return self._myCanvas.getDefaultColorMarkerComboList()

    def getNextLineMarkerColorCombo(self):
        """ As auto line's marker and color combo list is used,
        get the NEXT marker/color combo
        """
        # get from list
        marker, color = self._myLineMarkerColorList[self._myLineMarkerColorIndex]
        # process marker if it has information
        if marker.count(' (') > 0:
            marker = marker.split(' (')[0]

        # update the index
        self._myLineMarkerColorIndex += 1
        if self._myLineMarkerColorIndex == len(self._myLineMarkerColorList):
            self._myLineMarkerColorIndex = 0

        return marker, color

    def reset_line_color_marker_index(self):
        """ Reset the auto index for line's color and style
        """
        self._myLineMarkerColorIndex = 0
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

    def setAutoLineMarkerColorCombo(self):
        """ Set the default/auto line marker/color combination list
        """
        self._myLineMarkerColorList = list()
        for marker in MplLineMarkers:
            for color in MplBasicColors:
                self._myLineMarkerColorList.append((marker, color))

        return

    def setLineMarkerColorIndex(self, newindex):
        """
        """
        self._myLineMarkerColorIndex = newindex

        return

    def update_line(self, ikey, vec_x=None, vec_y=None, line_style=None, line_color=None,
                    marker=None, marker_color=None):
        """
        Update a line, including value, line style, color, marker and etc.
        The line is indicated by its key
        :param ikey:
        :param vec_x:
        :param vec_y:
        :param line_style:
        :param line_color:
        :param marker:
        :param marker_color: color of the marker
        :return:
        """
        # check
        assert isinstance(ikey, int), 'Line key {0} must be an integer but not a {1}.'.format(ikey, type(ikey))
        if ikey not in self._my1DPlotDict:
            raise RuntimeError('Line with ID {0} is not recorded as a plot on canvas.'.format(ikey))

        return self._myCanvas.updateLine(ikey, vec_x, vec_y, line_style, line_color, marker, marker_color)


class Qt4MplCanvas(FigureCanvas):
    """  A customized Qt widget for matplotlib figure.
    It can be used to replace GraphicsView of QtGui
    """
    def __init__(self, parent):
        """  Initialization
        """
        # from mpl_toolkits.axes_grid1 import host_subplot
        # import mpl_toolkits.axisartist as AA
        # import matplotlib.pyplot as plt

        # Instantiating matplotlib Figure
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')

        if True:
            self.axes = self.fig.add_subplot(111)  # return: matplotlib.axes.AxesSubplot
            self.fig.subplots_adjust(bottom=0.15)
            self.axes2 = None
        else:
            self.axes = self.fig.add_host_subplot(111)

        # Initialize parent class and set parent
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        # Set size policy to be able to expanding and resizable with frame
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        # Variables to manage all lines/subplot
        self._lineDict = {}
        self._lineIndex = 0

        # legend and color bar
        self._colorBar = None
        self._isLegendOn = False
        self._legendFontSize = 8

        return

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
        0, 0, 0.5, 0.5, head_width=0.05, head_length=0.1, fc='k', ec='k')
        :return:
        """
        head_width = 0.05
        head_length = 0.1
        fc = 'k'
        ec = 'k'

        self.axes.arrrow(start_x, start_y, stop_x, stop_y, head_width,
                         head_length, fc, ec)

        return

    def add_plot_1d(self, vec_x, vec_y, y_err=None, color=None, label="", x_label=None, y_label=None,
                    marker=None, line_style=None, line_width=1, show_legend=True):
        """

        :param vec_x: numpy array X
        :param vec_y: numpy array Y
        :param y_err:
        :param color:
        :param label:
        :param x_label:
        :param y_label:
        :param marker:
        :param line_style:
        :param line_width:
        :param show_legend:
        :return: new key
        """
        # Check input
        if isinstance(vec_x, np.ndarray) is False or isinstance(vec_y, np.ndarray) is False:
            raise NotImplementedError('Input vec_x or vec_y for addPlot() must be numpy.array.')
        plot_error = y_err is not None
        if plot_error is True:
            if isinstance(y_err, np.ndarray) is False:
                raise NotImplementedError('Input y_err must be either None or numpy.array.')

        if len(vec_x) != len(vec_y):
            raise NotImplementedError('Input vec_x and vec_y must have same size.')
        if plot_error is True and len(y_err) != len(vec_x):
            raise NotImplementedError('Input vec_x, vec_y and y_error must have same size.')

        # Hold previous data
        self.axes.hold(True)

        # set x-axis and y-axis label
        if x_label is not None:
            self.axes.set_xlabel(x_label, fontsize=16)
        if y_label is not None:
            self.axes.set_ylabel(y_label, fontsize=16)

        # process inputs and defaults
        if color is None:
            color = (0, 1, 0, 1)
        if marker is None:
            marker = 'None'
        if line_style is None:
            line_style = '-'

        # color must be RGBA (4-tuple)
        if plot_error is False:
            # return: list of matplotlib.lines.Line2D object
            r = self.axes.plot(vec_x, vec_y, color=color, marker=marker, markersize=1, linestyle=line_style,
                               label=label, linewidth=line_width)
        else:
            r = self.axes.errorbar(vec_x, vec_y, yerr=y_err, color=color, marker=marker, linestyle=line_style,
                                   label=label, linewidth=line_width)

        self.axes.set_aspect('auto')

        # set x-axis and y-axis label
        if x_label is not None:
            self.axes.set_xlabel(x_label, fontsize=20)
        if y_label is not None:
            self.axes.set_ylabel(y_label, fontsize=20)

        # set/update legend
        if show_legend:
            self._setup_legend()

        # Register
        line_key = self._lineIndex
        if len(r) == 1:
            self._lineDict[line_key] = r[0]
            self._lineIndex += 1
        else:
            msg = 'Return from plot is a %d-tuple: %s.. \n' % (len(r), r)
            for i_r in range(len(r)):
                msg += 'r[%d] = %s\n' % (i_r, str(r[i_r]))
            raise NotImplementedError(msg)

        # Flush/commit
        self.draw()

        return line_key

    def add_1d_plot_right(self, x, y, color=None, label="", x_label=None, ylabel=None, marker=None, linestyle=None,
                          linewidth=1):
        """ Add a line (1-d plot) at right axis
        """
        if self.axes2 is None:
            self.axes2 = self.axes.twinx()

        # Hold previous data
        self.axes2.hold(True)

        # Default
        if color is None:
            color = (0, 1, 0, 1)
        if marker is None:
            marker = 'o'
        if linestyle is None:
            linestyle = '-'

        # Special default
        if len(label) == 0:
            label = 'right'
            color = 'red'

        # color must be RGBA (4-tuple)
        r = self.axes2.plot(x, y, color=color, marker=marker, linestyle=linestyle,
                            label=label, linewidth=linewidth)
        # return: list of matplotlib.lines.Line2D object

        self.axes2.set_aspect('auto')

        # set x-axis and y-axis label
        if x_label is not None:
            self.axes2.set_xlabel(x_label, fontsize=20)
        if ylabel is not None:
            self.axes2.set_ylabel(ylabel, fontsize=20)

        # set/update legend
        self._setup_legend()

        # Register
        line_key = -1
        if len(r) == 1:
            line_key = self._lineIndex
            self._lineDict[line_key] = r[0]
            self._lineIndex += 1
        else:
            print "Impoooooooooooooooosible!"

        # Flush/commit
        self.draw()

        return line_key

    def addPlot2D(self, array2d, xmin, xmax, ymin, ymax, holdprev, yticklabels=None):
        """ Add a 2D plot

        Arguments:
         - yticklabels :: list of string for y ticks
        """
        # Release the current image
        self.axes.hold(holdprev)

        # Do plot
        # y ticks will be shown on line 1, 4, 23, 24 and 30
        # yticks = [1, 4, 23, 24, 30]
        # self.axes.set_yticks(yticks)

        # show image
        imgplot = self.axes.imshow(array2d, extent=[xmin, xmax, ymin, ymax], interpolation='none')
        # set y ticks as an option:
        if yticklabels is not None:
            # it will always label the first N ticks even image is zoomed in
            print "--------> [FixMe]: The way to set up the Y-axis ticks is wrong!"
            #self.axes.set_yticklabels(yticklabels)

        # explicitly set aspect ratio of the image
        self.axes.set_aspect('auto')

        # Set color bar.  plt.colorbar() does not work!
        if self._colorBar is None:
            # set color map type
            imgplot.set_cmap('spectral')
            self._colorBar = self.fig.colorbar(imgplot)
        else:
            self._colorBar.update_bruteforce(imgplot)

        # Flush...
        self._flush()

        return

    def add_contour_plot(self, vec_x, vec_y, matrix_z):
        """

        :param vec_x:
        :param vec_y:
        :param matrix_z:
        :return:
        """
        # create mesh grid
        grid_x, grid_y = np.meshgrid(vec_x, vec_y)

        # check size
        assert grid_x.shape == matrix_z.shape, 'Size of X (%d) and Y (%d) must match size of Z (%s).' \
                                               '' % (len(vec_x), len(vec_y), matrix_z.shape)

        # Release the current image
        self.axes.hold(False)

        # Do plot
        contour_plot = self.axes.contourf(grid_x, grid_y, matrix_z, 100)

        labels = [item.get_text() for item in self.axes.get_yticklabels()]
        print '[DB...BAT] Number of Y labels = ', len(labels), ', Number of Y = ', len(vec_y)

        # TODO/ISSUE/55: how to make this part more powerful
        if len(labels) == 2*len(vec_y) - 1:
            new_labels = [''] * len(labels)
            for i in range(len(vec_y)):
                new_labels[i*2] = '%d' % int(vec_y[i])
            self.axes.set_yticklabels(new_labels)

        # explicitly set aspect ratio of the image
        self.axes.set_aspect('auto')

        # Set color bar.  plt.colorbar() does not work!
        if self._colorBar is None:
            # set color map type
            contour_plot.set_cmap('spectral')
            self._colorBar = self.fig.colorbar(contour_plot)
        else:
            self._colorBar.update_bruteforce(contour_plot)

        # Flush...
        self._flush()

    def addImage(self, imagefilename):
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

    def clear_all_1d_plots(self):
        """ Remove all lines from the canvas
        """
        for ikey in self._lineDict.keys():
            plot = self._lineDict[ikey]
            if plot is None:
                continue
            if isinstance(plot, tuple) is False:
                try:
                    self.axes.lines.remove(plot)
                except ValueError as e:
                    print "[Error] Plot %s is not in axes.lines which has %d lines. Error mesage: %s" % (
                        str(plot), len(self.axes.lines), str(e))
                del self._lineDict[ikey]
            else:
                # error bar
                plot[0].remove()
                for line in plot[1]:
                    line.remove()
                for line in plot[2]:
                    line.remove()
                del self._lineDict[ikey]
            # ENDIF(plot)
        # ENDFOR

        self._setup_legend()

        self.draw()

        return

    def clear_canvas(self):
        """ Clear data including lines and image from canvas
        """
        # clear the image for next operation
        self.axes.hold(False)

        # Clear all lines
        self.clear_all_1d_plots()

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
        """ Get limit of Y-axis
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

    def updateLine(self, ikey, vecx=None, vecy=None, linestyle=None, linecolor=None, marker=None, markercolor=None):
        """
        Update a plot line or a series plot line
        Args:
            ikey:
            vecx:
            vecy:
            linestyle:
            linecolor:
            marker:
            markercolor:

        Returns:

        """
        line = self._lineDict[ikey]
        if line is None:
            print '[ERROR] Line (key = %d) is None. Unable to update' % ikey
            return

        if vecx is not None and vecy is not None:
            line.set_xdata(vecx)
            line.set_ydata(vecy)

        if linecolor is not None:
            line.set_color(linecolor)

        if linestyle is not None:
            line.set_linestyle(linestyle)

        if marker is not None:
            line.set_marker(marker)

        if markercolor is not None:
            line.set_markerfacecolor(markercolor)

        oldlabel = line.get_label()
        line.set_label(oldlabel)

        self._setup_legend()

        # commit
        self.draw()

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
        self.canvas_zoom_released.connect(self._myParent.evt_zoom_released)

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
        NavigationToolbar2.draw(self)

        self._myParent.evt_view_updated()

        return

    def home(self, *args):
        """

        Parameters
        ----------
        args

        Returns
        -------

        """
        # call super's home() method
        NavigationToolbar2.home(self, args)

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

        print 'PANNED'

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

    def release_zoom(self, event):
        """
        override zoom released method
        Parameters
        ----------
        event

        Returns
        -------

        """
        self.canvas_zoom_released.emit()

        NavigationToolbar2.release_zoom(self, event)

        return

    def _update_view(self):
        """
        view update called by home(), back() and forward()
        :return:
        """
        NavigationToolbar2._update_view(self)

        self._myParent.evt_view_updated()

        return
