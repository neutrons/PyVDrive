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
    def __init__(self, parent, row_size=None, col_size=None, tool_bar=True):
        """Initialization
        :param parent:
        :param row_size: number of figures per column, i.e., number of rows
        :param col_size: number of figures per row, i.e., number of columns
        """
        # Initialize parent
        super(MplGraphicsView1D, self).__init__(parent)

        # set up other variables
        # key = line ID, value = row, col, bool (is main axes???)
        self._lineSubplotMap = dict()

        # records for all the lines that are plot on the canvas
        # key = [row, col][line key], value = label, x-min, x-max, y-min and y-max
        self._myMainPlotDict = dict()
        self._myMainPlotDict[0, 0] = dict()  # init

        # for right plot
        self._myRightPlotDict = dict()
        self._myRightPlotDict[0, 0] = dict()

        self._statMainPlotDict = dict()
        self._statRightPlotDict = dict()

        # auto line's maker+color list
        self._myLineMarkerColorList = []
        self._myLineMarkerColorIndex = 0
        self.setAutoLineMarkerColorCombo()

        # set up canvas
        self._myCanvas = Qt4MplCanvasMultiFigure(self, row_size, col_size)
        if row_size is not None and col_size is not None:
            self.set_subplots(row_size, col_size)

        if tool_bar:
            self._myToolBar = MyNavigationToolbar(self, self._myCanvas)
        else:
            self._myToolBar = None

        # state of operation
        self._isZoomed = False
        # X and Y limit with home button
        self._homeXYLimit = None

        # set up layout
        self._vBox = QtGui.QVBoxLayout(self)
        self._vBox.addWidget(self._myCanvas)
        self._vBox.addWidget(self._myToolBar)

        return

    def _get_plot_y_range(self, row_index, col_index, line_id, is_main):
        """
        get the Y range (index 3 and 4) of a recorded plot
        :param row_index:
        :param col_index:
        :param line_id:
        :param is_main:
        :return:
        """
        if is_main:
            # from main plot
            if (row_index, col_index) not in self._myMainPlotDict:
                raise RuntimeError('Main plot does not have subplot ({0}, {1})'.format(row_index, col_index))
            y_min = self._myMainPlotDict[row_index, col_index][line_id][3]
            y_max = self._myMainPlotDict[row_index, col_index][line_id][4]
        else:
            # from right plot
            if (row_index, col_index) not in self._myRightPlotDict:
                raise RuntimeError('Right plot does not have subplot ({0}, {1})'.format(row_index, col_index))
            y_min = self._myRightPlotDict[row_index, col_index][line_id][3]
            y_max = self._myRightPlotDict[row_index, col_index][line_id][4]

        return y_min, y_max

    # TEST TODO - Just expanded to right axes
    def _update_plot_line_information(self, row_index, col_index, line_id, is_main, remove_line, vec_x=None,
                                      vec_y=None, label=None):
        """update the plot line information
        :param row_index:
        :param col_index:
        :param line_id:
        :param is_main: flag whether this is for main axes. Other wise it is for right axes
        :param remove_line:
        :param vec_x:
        :param vec_y:
        :param label:
        :return:
        """
        # get the row-index and column-index if not given
        if row_index is None or col_index is None:
            if not (line_id in self._lineSubplotMap):
                raise RuntimeError('Line ID {0} is not recorded in line-subplot map'.format(line_id))
            row_index, col_index, is_main = self._lineSubplotMap[line_id]

        # check inputs and others
        assert isinstance(line_id, int), 'Line ID {0} must be an integer but not a {1}.' \
                                         ''.format(line_id, type(line_id))
        assert isinstance(row_index, int), 'Row index {0} must be an integer but not a {1}.' \
                                           ''.format(row_index, type(row_index))
        assert isinstance(col_index, int), 'Column index {0} must be an integer but not a {1}.' \
                                           ''.format(col_index, type(col_index))

        # get the mai or right
        if is_main:
            plot_dict = self._myMainPlotDict
        else:
            plot_dict = self._myRightPlotDict

        # check
        if (row_index, col_index) not in plot_dict:
            raise RuntimeError('Subplot ({0}, {1}) does not exist in main ({2}?). Existing subplots are {3}.'
                               ''.format(row_index, col_index, is_main, plot_dict.keys()))

        # update
        if remove_line:
            # remove a line from record
            if line_id in plot_dict:
                del plot_dict[line_id]
            else:
                raise RuntimeError('Line ID does {0} is not registered.'.format(line_id))
        else:
            # add a NEW line or update an existing line
            if line_id not in plot_dict:
                assert isinstance(label, str), 'For adding a line (remove_line={0}), label {1} must be a string.' \
                                               ''.format(remove_line, label)
            elif label is None:
                # for update version, using current label if no new label is given
                label = plot_dict[line_id][0]

            # get range of x and y
            min_x = max_x = min_y = max_y = None
            if vec_x is not None:
                min_x = np.min(vec_x)
                max_x = np.max(vec_x)
            if vec_y is not None:
                min_y = np.max(vec_y)
                max_y = np.max(vec_y)

            plot_dict[line_id] = [label, min_x, max_x, min_y, max_y]
        # END-IF

        return

    def add_arrow(self, start_x, start_y, stop_x, stop_y):
        """

        :param start_x:
        :param start_y:
        :param stop_x:
        :param stop_y:
        :return:
        """
        # FIXME - BROKEN! TODO/LATER
        self._myCanvas.add_arrow(start_x, start_y, stop_x, stop_y)

        return

    def add_plot(self, vec_x, vec_y, y_err=None, row_index=0, col_index=0, is_right=False, color=None, label='',
                 x_label=None, y_label=None, marker=None, line_style=None, line_width=1, show_legend=True):
        """Add a plot in 1D
        :param row_index:
        :param col_index:
        :param is_right: flag to show whether the line is added to the right axis
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
            # plot to the right axis
            line_key = self._myCanvas.add_right_plot(row_index=row_index, col_index=col_index,
                                                     x=vec_x, y=vec_y, y_label=y_label,
                                                     color=color, label=label,  marker=marker,
                                                     line_style=line_style, linewidth=line_width)
            self._statRightPlotDict[line_key] = min(vec_x), max(vec_x), min(vec_y), max(vec_y)

        else:
            # plot at the main axis
            line_key = self._myCanvas.add_main_plot(row_index, col_index, vec_x, vec_y, y_err, color, label, x_label,
                                                    y_label, marker, line_style,
                                                    line_width, show_legend)
            # record min/max
            self._statMainPlotDict[line_key] = min(vec_x), max(vec_x), min(vec_y), max(vec_y)
        # END-IF

        # update line information
        self._update_plot_line_information(row_index, col_index, line_key, is_main=not is_right,
                                           remove_line=False, label=label, vec_x=vec_x, vec_y=vec_y)

        # add line to dictionary
        self._lineSubplotMap[line_key] = row_index, col_index, not is_right

        return line_key

    def auto_rescale(self, row_index=None, col_index=None, percent_room=0.05,
                     lower_y_boundary=None, upper_y_boundary=None):
        """
        auto scale along the Y axis
        :param row_index: if None, then all the subplots
        :param col_index:
        :param percent_room:
        :param lower_y_boundary:
        :param upper_y_boundary:
        :return:
        """
        if row_index is not None and col_index is not None:
            # check
            assert isinstance(row_index, int), 'row index {0} must be an integer but not a {1}' \
                                               ''.format(row_index, type(row_index))
            assert isinstance(col_index, int), 'column index {0}  must be an integer but not a {1}' \
                                               ''.format(col_index, type(col_index))
            # set
            index_tup_list = [row_index, col_index]
        else:
            index_tup_list = self.get_subplots_indexes()

        # re-set limits
        assert isinstance(percent_room, float), 'Blank room percentage {0} must be a float but not a {1}' \
                                                ''.format(percent_room, type(percent_room))

        for row_index, col_index in index_tup_list:
            # collect all min and max of Y
            min_y_list = list()
            max_y_list = list()

            # get line IDs
            subplot_line_indexes = self._myCanvas.get_line_keys(row_index, col_index)

            for line_key in subplot_line_indexes:
                min_i, max_i = self._get_plot_y_range(row_index, col_index, line_key, is_main=True)
                min_y_list.append(min_i)
                max_y_list.append(max_i)
            # END-FOR

            # get real min and max
            min_y = np.min(np.array(min_y_list))
            max_y = np.max(np.array(max_y_list))

            delta_y = max_y - min_y

            upper_y = max_y + delta_y * percent_room
            lower_y = min_y - delta_y * percent_room

            if lower_y_boundary is not None and lower_y_boundary < lower_y:
                lower_y = lower_y_boundary
            if upper_y_boundary is not None and upper_y_boundary > upper_y:
                upper_y = upper_y_boundary

            # set limit
            self._myCanvas.set_y_limits(row_index, col_index, lower_y, upper_y, apply_change=True)
        # END-FOR

        return

    def canvas(self):
        """ Get the canvas
        :return:
        """
        return self._myCanvas

    def clear_all_lines(self):
        """
        clear all lines on the canvas
        :return:
        """
        for row_index, col_index in self._myCanvas.subplot_indexes:
            self._myCanvas.clear_subplot_lines(row_index, col_index)

        # TODO/CHECK/NOW - Only clear the 2-level entries.. (row, col) shall be kept
        self._statRightPlotDict.clear()
        self._statMainPlotDict.clear()
        for row_index, col_index in self._myMainPlotDict.keys():
            self._myMainPlotDict[row_index, col_index].clear()

        # about zoom
        self._isZoomed = False
        self._homeXYLimit = None

        return

    def clear_canvas(self):
        """ Clear canvas
        """
        #  clear all the lines
        self.clear_all_lines()

        return self._myCanvas.clear_canvas()

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

    def remove_line(self, row_index, col_index, line_id):
        """ Remove a line
        :param line_id:
        :return:
        """
        # remove line
        self._myCanvas.remove_plot_1d(row_index, col_index, line_id, apply_change=True)

        # remove the records
        self._update_plot_line_information(row_index, col_index, line_id=line_id, remove_line=True)

        if line_id in self._statMainPlotDict:
            del self._statMainPlotDict[line_id]
        else:
            del self._statRightPlotDict[line_id]

        return

    def get_canvas(self):
        """
        get canvas
        Returns:

        """
        return self._myCanvas

    def get_subplots_indexes(self):
        """
        get the indexes of all the subplots
        :return: a list of 2-tuples as (row-index, column-index)
        """
        return self._myCanvas.subplot_indexes

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

    def set_subplots(self, row_size, col_size):
        """
        re-set up the subplots.  This is the only  method that allows users to change the subplots
        :param row_size:
        :param col_size:
        :return:
        """
        # delete all the lines on canvas now
        self.clear_all_lines()

        # set the subplots
        self._myCanvas.set_subplots(row_size, col_size)

        # reset PlotDict
        subplot_indexes = self._myCanvas.subplot_indexes
        for index in subplot_indexes:
            self._myMainPlotDict[index] = dict()

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

        # get the row and column index
        if ikey in self._lineSubplotMap:
            row_index, col_index, is_main = self._lineSubplotMap[ikey]
        else:
            raise RuntimeError('Line with ID {0} is not recorded as a plot on canvas.'.format(ikey))

        # update information
        self._update_plot_line_information(row_index=row_index, col_index=col_index, is_main=is_main,
                                           line_id=ikey, remove_line=False,
                                           vec_y=vec_y)

        return self._myCanvas.updateLine(ikey, vec_x, vec_y, line_style, line_color, marker, marker_color)


# TODO/TODO/FIXME/ASAP - Check all _lineDict to [row, col][line_key]
class Qt4MplCanvasMultiFigure(FigureCanvas):
    """  A customized Qt widget for matplotlib figure.
    It can be used to replace GraphicsView of QtGui
    """
    def __init__(self, parent, row_size=None, col_size=None):
        """Initialization
        :param parent:
        :param row_size:
        :param col_size:
        """
        # Instantiating matplotlib Figure. It is a requirement to initialize a figure canvas
        self.fig = Figure()
        self.fig.patch.set_facecolor('white')

        # Initialize parent class and set parent
        super(Qt4MplCanvasMultiFigure, self).__init__(self.fig)
        self.setParent(parent)

        # Variables to manage all lines/subplot
        # default to 1 subplot at (0, 0)
        self._lineDict = dict()
        self._lineDict[0, 0] = dict()

        # right axes
        self._lineRightLine = dict()
        self._lineRightLine[0, 0] = dict()

        # line index
        self._lineIndex = 0
        self._lineRightIndex = 0

        # legend and color bar
        self._legendStatusDict = dict()
        self._legendFontSize = 8

        # data structure for sub plots
        self._numSubPlots = 0
        self.axes_main = dict()  # keys are 2-tuple, starting from (0, 0)
        self.axes_right = dict()

        # the subplots are not set up in the initialization
        if row_size is not None and col_size is not None:
            self.set_subplots(row_size, col_size)

        # Set size policy to be able to expanding and resizable with frame
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        return

    @property
    def subplot_indexes(self):
        """

        :return:  a list of 2 - tuples as (row - index, column - index)
        """
        return sorted(self.axes_main.keys())

    def set_subplots(self, row_size, col_size):
        """
        set subplots
        :param row_size:
        :param col_size:
        :return:
        """
        # check input
        assert isinstance(row_size, int), 'Row size {0} must be an integer but not a {1}.' \
                                          ''.format(row_size, type(row_size))
        assert isinstance(col_size, int), 'Column size {0} must be an integer but not a {1}.' \
                                          ''.format(col_size, type(col_size))

        if row_size < 1:
            raise RuntimeError('Row size {0} must be larger than 0.'.format(row_size))
        if col_size < 1:
            raise RuntimeError('Column size {0} must be larger than 0.'.format(row_size))

        for row_index in range(row_size):
            for col_index in range(col_size):
                sub_plot_index = row_index * col_size + col_index + 1
                subplot_ref = self.fig.add_subplot(row_size, col_size, sub_plot_index)
                self.axes_main[row_index, col_index] = subplot_ref
                self._lineDict[row_index, col_index] = dict()
                self._legendStatusDict[row_index, col_index] = False
            # END-FOR
        # END-FOR

    @property
    def is_legend_on(self):
        """
        check whether the legend is shown or hide
        Returns:
        boolean
        """
        return self._legendStatusDict

    def add_arrow(self, row_index, col_index, start_x, start_y, stop_x, stop_y):
        """
        0, 0, 0.5, 0.5, head_width=0.05, head_length=0.1, fc='k', ec='k')
        :return:
        """
        head_width = 0.05
        head_length = 0.1
        fc = 'k'
        ec = 'k'

        # check
        self._check_subplot_index(row_index, col_index)

        # do it
        self.axes_main[row_index, col_index].arrrow(start_x, start_y, stop_x, stop_y, head_width, head_length, fc, ec)
        #
        # self.axes.arrrow(start_x, start_y, stop_x, stop_y, head_width,
        #                  head_length, fc, ec)

        return

    def add_main_plot(self, row_index, col_index, vec_x, vec_y, y_err=None, color=None, label='',
                      x_label=None, y_label=None,
                      marker=None, line_style=None, line_width=1, show_legend=True):
        """Add 1D plot on the main side (left)
        :param row_index: numpy array X
        :param col_index: numpy array Y
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
        :return: line ID (i.e., new key)
        """
        # Check input
        self._check_subplot_index(row_index, col_index)

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
        # self.axes.hold(True)
        self.axes_main[row_index, col_index].hold(True)

        # set x-axis and y-axis label
        if x_label is not None:
            self.axes_main[row_index, col_index].set_xlabel(x_label, fontsize=16)  # or 20?
        if y_label is not None:
            self.axes_main[row_index, col_index].set_ylabel(y_label, fontsize=10)

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
            r = self.axes_main[row_index, col_index].plot(vec_x, vec_y, color=color, marker=marker, markersize=4,
                                                          linestyle=line_style, label=label, linewidth=line_width)
        else:
            r = self.self.axes_main[row_index, col_index].errorbar(vec_x, vec_y, yerr=y_err, color=color, marker=marker,
                                                                   linestyle=line_style, label=label,
                                                                   linewidth=line_width)

        # set aspect ratio
        self.axes_main[row_index, col_index].set_aspect('auto')

        # set/update legend
        if show_legend:
            self._setup_legend(row_index, col_index)

        # Register
        line_key = self._lineIndex
        if len(r) == 1:
            self._lineDict[row_index, col_index][line_key] = r[0]
            self._lineIndex += 1
        else:
            msg = 'Return from plot is a %d-tuple: %s.. \n' % (len(r), r)
            for i_r in range(len(r)):
                msg += 'r[%d] = %s\n' % (i_r, str(r[i_r]))
            raise NotImplementedError(msg)

        # Flush/commit
        self.draw()

        return line_key

    def add_right_plot(self, row_index, col_index, x, y, color=None, label="", x_label=None, y_label=None,
                       marker=None, line_style=None, linewidth=1):
        """
        add a 1-D line at the right axis
        :param row_index:
        :param col_index:
        :param x:
        :param y:
        :param color:
        :param label:
        :param x_label:
        :param y_label:
        :param marker:
        :param line_style:
        :param linewidth:
        :return:
        """
        # check
        self._check_subplot_index(row_index, col_index)

        # initialize twinx
        if (row_index, col_index) not in self.axes_right or self.axes_right[row_index, col_index] is None:
            self.axes_right[row_index, col_index] = self.axes_main[row_index, col_index].twinx()   # self.axes.twinx()

        # Hold previous data
        self.axes_right[row_index, col_index].hold(True)

        # turn on the right side ticks
        self.axes_right[row_index, col_index].yaxis.tick_right()

        # Default for line's color, marker and line style
        if color is None:
            # color must be RGBA (4-tuple)
            color = (0, 1, 0, 1)
        if marker is None:
            marker = 'o'
        if line_style is None:
            line_style = '-'

        # Special default
        if len(label) == 0:
            label = 'right'
            color = 'red'

        # return: list of matplotlib.lines.Line2D object
        plot_info = self.axes_right[row_index, col_index].plot(x, y, color=color, marker=marker, linestyle=line_style,
                                                               label=label, linewidth=linewidth)
        #

        self.axes_right[row_index, col_index].set_aspect('auto')

        # set x-axis and y-axis label
        if x_label is not None:
            raise NotImplementedError('ASAP! Use upper X-axis???')
            # self.axes2.set_xlabel(x_label, fontsize=20)

        if y_label is not None:
            self.axes_right[row_index, col_index].set_ylabel(y_label, fontsize=10)

        # set/update legend
        self._setup_legend(row_index, col_index)

        # Register
        line_id = self._lineIndex  # share the line ID counter with main axis
        if len(plot_info) == 1:
            self._lineRightLine[row_index, col_index][line_id] = plot_info[0]
            self._lineIndex += 1
        else:
            msg = 'Return from plot is a %d-tuple: %s.. \n' % (len(plot_info), plot_info)
            for i_r in range(len(plot_info)):
                msg += 'r[%d] = %s\n' % (i_r, str(r[i_r]))
            raise NotImplementedError(msg)

        # Flush/commit
        self.draw()

        return line_id

    # TODO/TEST - Remove line from left and right axes
    def clear_subplot_lines(self, row_index, col_index):
        """
        Remove all lines from a subplot
        :param row_index:
        :param col_index:
        :return:
        """
        # check
        self._check_subplot_index(row_index, col_index)

        # remove line and its record
        for line_key in self._lineDict[row_index, col_index].keys():
            mpl_line = self._lineDict[row_index, col_index][line_key]
            if mpl_line is None:
                # removed
                continue
            elif isinstance(mpl_line, tuple):
                # with error bar and etc
                mpl_line[0].remove()
                for line in mpl_line[1]:
                    line.remove()
                for line in mpl_line[2]:
                    line.remove()
            else:
                # with single line
                try:
                    self.axes_main[row_index, col_index].lines.remove(mpl_line)
                except ValueError as e:
                    print "[Error] Plot %s is not in axes.lines which has %d lines. Error mesage: %s" % (
                        str(line_key), len(self.axes_main[row_index, col_index].lines), str(e))
            # END-IF-ELSE

            # remove record
            del self._lineDict[row_index, col_index][line_key]
        # END-FOR

        self._setup_legend(row_index, col_index)

        self.draw()

        return

    def clear_canvas(self):
        """ Clear data including lines and image from canvas
        """
        # clear the image for next operation
        for subplot in self.axes_main.values():
            subplot.hold(False)
        for subplot in self.axes_right.values():
            if subplot is not None:
                subplot.hold(False)

        # clear all lines
        for row_index, col_index in self.axes_main.keys():
            self.clear_subplot_lines(row_index, col_index)
            self.axes_main[row_index, col_index].cla()


        # self.axes.hold(False)
        #
        # # Clear all lines
        # self.clear_all_1d_plots()
        #
        # # clear image
        # self.axes.cla()
        # Try to clear the color bar
        # if len(self.fig.axes) > 1:
        #     self.fig.delaxes(self.fig.axes[1])
        #     self._colorBar = None
        #     # This clears the space claimed by color bar but destroys sub_plot too.
        #     self.fig.clear()
        #     # Re-create subplot
        #     self.axes = self.fig.add_subplot(111)
        #     self.fig.subplots_adjust(bottom=0.15)

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

        self._legendStatusDict = False

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

    def set_x_limits(self, row_index, col_index, xmin, xmax, apply_change=True):
        """set limit on X-axis
        :param row_index:
        :param col_index:
        :param xmin:
        :param xmax:
        :param apply_change:
        :return:
        """
        # check
        self._check_subplot_index(row_index, col_index)

        # for X
        x_limits = list(self.axes_main[row_index, col_index].get_xlim())
        if xmin is not None:
            x_limits[0] = xmin
        if xmax is not None:
            x_limits[1] = xmax
        self.axes_main[row_index, col_index].set_xlim(x_limits)

        # try draw
        if apply_change:
            self.draw()

        return

    def set_y_limits(self, row_index, col_index, ymin, ymax, apply_change=True):
        """set limit on y-axis
        :param row_index:
        :param col_index:
        :param ymin:
        :param ymax:
        :param apply_change:
        :return:
        """
        # check
        self._check_subplot_index(row_index, col_index)

        # for Y
        y_limits = list(self.axes_main[row_index, col_index].get_ylim())
        if ymin is not None:
            y_limits[0] = ymin
        if ymax is not None:
            y_limits[1] = ymax
        self.axes_main[row_index, col_index].set_ylim(y_limits)

        # try draw
        if apply_change:
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

    def remove_plot_1d(self, row_index, col_index, plot_key, apply_change=True):
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
        if apply_change:
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
            self._legendStatusDict = True

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

    def _setup_legend(self, row_index, col_index, location='best', font_size=10):
        """Set up legend
        self.axes.legend(): Handler is a Line2D object. Lable maps to the line object
        :param row_index:
        :param col_index:
        :param location:
        :param font_size:
        :return:
        """
        # check input
        self._check_subplot_index(row_index, col_index)

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

        handles, labels = self.axes_main[row_index, col_index].get_legend_handles_labels()
        self.axes_main[row_index, col_index].legend(handles, labels, loc=location, fontsize=font_size)

        self._legendStatusDict[row_index, col_index] = True

        return

    def _check_subplot_index(self, row_index, col_index):
        """check whether the subplot indexes are valid
        :param row_index:
        :param col_index:
        :return:
        """
        # check type
        assert isinstance(row_index, int), 'Subplot row index {0} must be an integer but not a {1}' \
                                           ''.format(row_index, type(row_index))
        assert isinstance(col_index, int), 'Subplot column index {0} must be an integer but not a {1}' \
                                           ''.format(col_index, type(col_index))

        if (row_index, col_index) not in self.axes_main:
            raise RuntimeError('Subplot index {0}, {1} does not exist. Keys are {2}'
                               ''.format(row_index, col_index, self.axes_main.keys()))

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
