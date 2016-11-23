#pylint: disable=invalid-name,too-many-public-methods,too-many-arguments,non-parent-init-called,R0902,too-many-branches,C0302
import os
import numpy as np

from PyQt4 import QtGui

import matplotlib
from matplotlib.figure import Figure
import matplotlib.image
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar2
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

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


class IndicatorManager(object):
    """ Manager for all indicator lines

    Indicator's Type =
    - 0: horizontal.  moving along Y-direction. [x_min, x_max], [y, y];
    - 1: vertical. moving along X-direction. [x, x], [y_min, y_max];
    - 2: 2-way. moving in any direction. [x_min, x_max], [y, y], [x, x], [y_min, y_max].
    """
    def __init__(self):
        """

        :return:
        """
        # Auto color index
        self._colorIndex = 0
        # Auto line ID
        self._autoLineID = 1

        self._lineManager = dict()
        self._canvasLineKeyDict = dict()
        self._indicatorTypeDict = dict()  # value: 0 (horizontal), 1 (vertical), 2 (2-way)

        return

    def delete(self, indicator_id):
        """
        Delete indicator
        """
        # TODO/NOW: NEW

        del self._lineManager[indicator_id]
        del self._canvasLineKeyDict[indicator_id]
        del self._indicatorTypeDict[indicator_id]

        return

    def add_2way_indicator(self, x, x_min, x_max, y, y_min, y_max, color):
        """

        :param x:
        :param x_min:
        :param x_max:
        :param y:
        :param y_min:
        :param y_max:
        :param color:
        :return:
        """
        # Set up indicator ID
        this_id = str(self._autoLineID)
        self._autoLineID += 1

        # Set up vectors
        vec_x_horizontal = np.array([x_min, x_max])
        vec_y_horizontal = np.array([y, y])

        vec_x_vertical = np.array([x, x])
        vec_y_vertical = np.array([y_min, y_max])

        #
        self._lineManager[this_id] = [vec_x_horizontal, vec_y_horizontal, vec_x_vertical, vec_y_vertical, color]
        self._indicatorTypeDict[this_id] = 2

        return this_id

    def add_horizontal_indicator(self, y, x_min, x_max, color):
        """
        Add a horizontal indicator moving vertically
        :param y:
        :param x_min:
        :param x_max:
        :param color:
        :return:
        """
        # Get ID
        this_id = str(self._autoLineID)
        self._autoLineID += 1

        #
        vec_x = np.array([x_min, x_max])
        vec_y = np.array([y, y])

        #
        self._lineManager[this_id] = [vec_x, vec_y, color]
        self._indicatorTypeDict[this_id] = 0

        return this_id

    def add_vertical_indicator(self, x, y_min, y_max, color):
        """
        Add a vertical indicator to data structure moving horizontally
        :return: indicator ID as an integer
        """
        # Get ID
        this_id = self._autoLineID
        self._autoLineID += 1

        # form vec x and vec y
        vec_x = np.array([x, x])
        vec_y = np.array([y_min, y_max])

        #
        self._lineManager[this_id] = [vec_x, vec_y, color]
        self._indicatorTypeDict[this_id] = 1

        return this_id

    def get_canvas_line_index(self, indicator_id):
        """
        Get a line's ID (on canvas) from an indicator ID
        :param indicator_id:
        :return:
        """
        assert isinstance(indicator_id, int)

        if indicator_id not in self._canvasLineKeyDict:
            raise RuntimeError('Indicator ID %s cannot be found. Current keys are %s.' % (
                indicator_id, str(sorted(self._canvasLineKeyDict.keys()))
            ))
        return self._canvasLineKeyDict[indicator_id]

    def get_line_type(self, my_id):
        """

        :param my_id:
        :return:
        """
        return self._indicatorTypeDict[my_id]

    def get_2way_data(self, line_id):
        """

        :param line_id:
        :return:
        """
        assert self._indicatorTypeDict.has_key(line_id)
        assert self._indicatorTypeDict[line_id] == 2

        vec_set = [self._lineManager[line_id][0:2], self._lineManager[line_id][2:4]]

        return vec_set

    def get_data(self, line_id):
        """
        Get line's vector x and vector y
        :param line_id:
        :return: 2-tuple of numpy arrays
        """
        return self._lineManager[line_id][0], self._lineManager[line_id][1]

    def get_indicator_key(self, x, y):
        """ Get indicator's key with position
        :return:
        """
        if x is None and y is None:
            raise RuntimeError('It is not allowed to have both X and Y are none to get indicator key.')

        ret_key = None

        for line_key in self._lineManager.keys():

            if x is not None and y is not None:
                # 2 way
                raise NotImplementedError('ASAP')
            elif x is not None and self._indicatorTypeDict[line_key] == 1:
                # vertical indicator moving along X
                if abs(self._lineManager[line_key][0][0] - x) < 1.0E-2:
                    return line_key
            elif y is not None and self._indicatorTypeDict[line_key] == 0:
                # horizontal indicator moving along Y
                if abs(self._lineManager[line_key][1][0] - y) < 1.0E-2:
                    return line_key
        # END-FOR

        return ret_key

    @staticmethod
    def get_line_style(line_id=None):
        """

        :param line_id:
        :return:
        """
        if line_id is not None:
            style = '--'
        else:
            style = '--'

        return style

    def get_live_indicator_ids(self):
        """

        :return:
        """
        return sorted(self._lineManager.keys())

    @staticmethod
    def get_marker():
        """
        Get the marker a line
        :return:
        """
        return '.'

    def get_next_color(self):
        """
        Get next color by auto color index
        :return: string as color
        """
        next_color = MplBasicColors[self._colorIndex]

        # Advance and possibly reset color scheme
        self._colorIndex += 1
        if self._colorIndex == len(MplBasicColors):
            self._colorIndex = 0

        return next_color

    def set_canvas_line_index(self, my_id, canvas_line_index):
        """

        :param my_id:
        :param canvas_line_index:
        :return:
        """
        self._canvasLineKeyDict[my_id] = canvas_line_index

        return

    def set_position(self, my_id, pos_x, pos_y):
        """ Set the indicator to a new position
        :param line_id:
        :param pos_x:
        :param pos_y:
        :return:
        """
        if self._indicatorTypeDict[my_id] == 0:
            # horizontal
            self._lineManager[my_id][1][0] = pos_y
            self._lineManager[my_id][1][1] = pos_y

        elif self._indicatorTypeDict[my_id] == 1:
            # vertical
            self._lineManager[my_id][0][0] = pos_x
            self._lineManager[my_id][0][1] = pos_x

        elif self._indicatorTypeDict[my_id] == 2:
            # 2-way
            self._lineManager[my_id][0] = pos_x
            self._lineManager[my_id][1] = pos_y

        else:
            raise RuntimeError('Unsupported indicator of type %d' % self._indicatorTypeDict[my_id])

        self._lineManager[my_id][2] = 'black'

        return

    def shift(self, my_id, dx, dy):
        """

        :param my_id:
        :param dx:
        :param dy:
        :return:
        """
        # print self._lineManager[my_id][0]

        if self._indicatorTypeDict[my_id] == 0:
            # horizontal
            self._lineManager[my_id][1] += dy

        elif self._indicatorTypeDict[my_id] == 1:
            # vertical
            self._lineManager[my_id][0] += dx

        elif self._indicatorTypeDict[my_id] == 2:
            # 2-way
            self._lineManager[my_id][2] += dx
            self._lineManager[my_id][1] += dy

        else:
            raise RuntimeError('Unsupported indicator of type %d' % self._indicatorTypeDict[my_id])

        return

    def update_indicators_range(self, x_range, y_range):
        """
        Update indicator's range
        :param x_range:
        :param y_range:
        :return:
        """
        for i_id in self._lineManager.keys():
            # NEXT - Need a new flag for direction of the indicating line, vertical or horizontal
            if True:
                self._lineManager[i_id][1][0] = y_range[0]
                self._lineManager[i_id][1][-1] = y_range[1]
            else:
                self._lineManager[i_id][0][0] = x_range[0]
                self._lineManager[i_id][0][-1] = x_range[1]

        return


class MplGraphicsView(QtGui.QWidget):
    """ A combined graphics view including matplotlib canvas and
    a navigation tool bar

    Note: Merged with HFIR_Powder_Reduction.MplFigureCAnvas
    """
    def __init__(self, parent):
        """ Initialization
        """
        # Initialize parent
        QtGui.QWidget.__init__(self, parent)

        # set up canvas
        self._myCanvas = Qt4MplCanvas(self)
        self._myToolBar = MyNavigationToolbar(self, self._myCanvas)

        # set up layout
        self._vBox = QtGui.QVBoxLayout(self)
        self._vBox.addWidget(self._myCanvas)
        self._vBox.addWidget(self._myToolBar)

        # auto line's maker+color list
        self._myLineMarkerColorList = []
        self._myLineMarkerColorIndex = 0
        self.setAutoLineMarkerColorCombo()

        # Declaration of class variables
        self._indicatorKey = None

        # Indicator manager
        self._myIndicatorsManager = IndicatorManager()

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

    def add_line_set(self, vec_set, color, marker, line_style, line_width):
        """ Add a set of line and manage together
        :param vec_set:
        :param color:
        :param marker:
        :param line_style:
        :param line_width:
        :return:
        """
        key_list = list()
        for vec_x, vec_y in vec_set:
            temp_key = self._myCanvas.add_plot_1d(vec_x, vec_y, color=color, marker=marker,
                                                  line_style=line_style, line_width=line_width)
            assert isinstance(temp_key, int)
            assert temp_key >= 0
            key_list.append(temp_key)

        return key_list

    def add_plot_1d(self, vec_x, vec_y, y_err=None, color=None, label='', x_label=None, y_label=None,
                    marker=None, line_style=None, line_width=1, show_legend=True):
        """
        Add a 1-D plot to canvas
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
        line_key = self._myCanvas.add_plot_1d(vec_x, vec_y, y_err, color, label, x_label, y_label, marker, line_style,
                                              line_width, show_legend)

        return line_key

    def add_plot_1d_right(self, vec_x, vec_y, color=None, label='', marker=None, line_style=None, line_width=1):
        """
        Add 1 line (1-d plot) to right axis
        :param vec_x:
        :param vec_y:
        :param color:
        :param label:
        :param marker:
        :param line_style:
        :param line_width:
        :return:
        """
        line_key = self._myCanvas.add_1d_plot_right(vec_x, vec_y, label=label,
                                                    color=color, marker=marker,
                                                    linestyle=line_style, linewidth=line_width)

        return line_key

    def add_2way_indicator(self, x=None, y=None, color=None, master_line=None):
        """ Add a 2-way indicator following an existing line?
        :param x:
        :param y:
        :param color:
        :return:
        """
        if master_line is not None:
            raise RuntimeError('Implement how to use master_line ASAP.')

        x_min, x_max = self._myCanvas.getXLimit()
        if x is None:
            x = (x_min + x_max) * 0.5
        else:
            assert isinstance(x, float)

        y_min, y_max = self._myCanvas.getYLimit()
        if y is None:
            y = (y_min + y_max) * 0.5
        else:
            assert isinstance(y, float)

        if color is None:
            color = self._myIndicatorsManager.get_next_color()
        else:
            assert isinstance(color, str)

        my_id = self._myIndicatorsManager.add_2way_indicator(x, x_min, x_max,
                                                             y, y_min, y_max,
                                                             color)
        vec_set = self._myIndicatorsManager.get_2way_data(my_id)

        canvas_line_index = self.add_line_set(vec_set, color=color,
                                              marker=self._myIndicatorsManager.get_marker(),
                                              line_style=self._myIndicatorsManager.get_line_style(),
                                              line_width=1)
        self._myIndicatorsManager.set_canvas_line_index(my_id, canvas_line_index)

        return my_id

    def add_horizontal_indicator(self, y=None, color=None):
        """ Add an indicator line
        """
        # Default
        if y is None:
            y_min, y_max = self._myCanvas.getYLimit()
            y = (y_min + y_max) * 0.5
        else:
            assert isinstance(y, float)

        x_min, x_max = self._myCanvas.getXLimit()

        # For color
        if color is None:
            color = self._myIndicatorsManager.get_next_color()
        else:
            assert isinstance(color, str)

        # Form
        my_id = self._myIndicatorsManager.add_horizontal_indicator(y, x_min, x_max, color)
        vec_x, vec_y = self._myIndicatorsManager.get_data(my_id)

        canvas_line_index = self._myCanvas.add_plot_1d(vec_x=vec_x, vec_y=vec_y,
                                                       color=color, marker=self._myIndicatorsManager.get_marker(),
                                                       line_style=self._myIndicatorsManager.get_line_style(),
                                                       line_width=1)

        self._myIndicatorsManager.set_canvas_line_index(my_id, canvas_line_index)

        return my_id

    def add_vertical_indicator(self, x=None, color=None, style=None, line_width=1):
        """
        Add a vertical indicator line
        Guarantees: an indicator is plot and its ID is returned
        :param x: None as the automatic mode using default from middle of canvas
        :param color: None as the automatic mode using default
        :param style:
        :return: indicator ID
        """
        # For indicator line's position
        if x is None:
            x_min, x_max = self._myCanvas.getXLimit()
            x = (x_min + x_max) * 0.5
        else:
            assert isinstance(x, float)

        y_min, y_max = self._myCanvas.getYLimit()

        # For color
        if color is None:
            color = self._myIndicatorsManager.get_next_color()
        else:
            assert isinstance(color, str)

        # style
        if style is None:
            style = self._myIndicatorsManager.get_line_style()

        # Form
        my_id = self._myIndicatorsManager.add_vertical_indicator(x, y_min, y_max, color)
        vec_x, vec_y = self._myIndicatorsManager.get_data(my_id)

        canvas_line_index = self._myCanvas.add_plot_1d(vec_x=vec_x, vec_y=vec_y,
                                                       color=color,
                                                       marker=self._myIndicatorsManager.get_marker(),
                                                       line_style=style,
                                                       line_width=line_width)

        self._myIndicatorsManager.set_canvas_line_index(my_id, canvas_line_index)

        return my_id

    def add_plot_2d(self, array2d, x_min, x_max, y_min, y_max, hold_prev_image=True, y_tick_label=None):
        """
        Add a 2D image to canvas
        :param array2d: numpy 2D array
        :param x_min:
        :param x_max:
        :param y_min:
        :param y_max:
        :param hold_prev_image:
        :param y_tick_label:
        :return:
        """
        self._myCanvas.addPlot2D(array2d, x_min, x_max, y_min, y_max, hold_prev_image, y_tick_label)

        return


    def addImage(self, imagefilename):
        """ Add an image by file
        """
        # check
        if os.path.exists(imagefilename) is False:
            raise NotImplementedError("Image file %s does not exist." % (imagefilename))

        self._myCanvas.addImage(imagefilename)

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

    def clear_canvas(self):
        """ Clear canvas
        """
        return self._myCanvas.clear_canvas()

    def draw(self):
        """ Draw to commit the change
        """
        return self._myCanvas.draw()

    def evt_view_updated(self):
        """ Event handling as canvas size updated
        :return:
        """
        # update the indicator
        new_x_range = self.getXLimit()
        new_y_range = self.getYLimit()

        self._myIndicatorsManager.update_indicators_range(new_x_range, new_y_range)
        for indicator_key in self._myIndicatorsManager.get_live_indicator_ids():
            canvas_line_id = self._myIndicatorsManager.get_canvas_line_index(indicator_key)
            data_x, data_y = self._myIndicatorsManager.get_data(indicator_key)
            self.updateLine(canvas_line_id, data_x, data_y)
        # END-FOR

        return

    def getPlot(self):
        """
        """
        return self._myCanvas.getPlot()

    def getLastPlotIndexKey(self):
        """ Get ...
        """
        return self._myCanvas.getLastPlotIndexKey()

    def getXLimit(self):
        """ Get limit of Y-axis
        :return: 2-tuple as xmin, xmax
        """
        return self._myCanvas.getXLimit()

    def getYLimit(self):
        """ Get limit of Y-axis
        """
        return self._myCanvas.getYLimit()

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
        self._myCanvas.remove_plot_1d(line_id)

    def set_indicator_position(self, line_id, pos_x, pos_y):
        """ Set the indicator to new position
        :param line_id:
        :param pos_x:
        :param pos_y:
        :return:
        """
        # Set value
        self._myIndicatorsManager.set_position(line_id, pos_x, pos_y)

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

    def removePlot(self, ikey):
        """
        """
        return self._myCanvas.remove_plot_1d(ikey)

    def updateLine(self, ikey, vecx, vecy, linestyle=None, linecolor=None, marker=None, markercolor=None):
        """
        """
        return self._myCanvas.updateLine(ikey, vecx, vecy, linestyle, linecolor, marker, markercolor)

    def update_indicator(self, i_key, color):
        """
        Update indicator with new color
        :param i_key:
        :param vec_x:
        :param vec_y:
        :param color:
        :return:
        """
        if self._myIndicatorsManager.get_line_type(i_key) < 2:
            # horizontal or vertical
            canvas_line_index = self._myIndicatorsManager.get_canvas_line_index(i_key)
            self._myCanvas.updateLine(ikey=canvas_line_index, vecx=None, vecy=None, linecolor=color)
        else:
            # 2-way
            canvas_line_index_h, canvas_line_index_v = self._myIndicatorsManager.get_canvas_line_index(i_key)
            h_vec_set, v_vec_set = self._myIndicatorsManager.get_2way_data(i_key)

            self._myCanvas.updateLine(ikey=canvas_line_index_h, vecx=None, vecy=None, linecolor=color)
            self._myCanvas.updateLine(ikey=canvas_line_index_v, vecx=None, vecy=None, linecolor=color)

        return

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

        return

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
        # print "[DB] Print line %d: marker = %s, color = %s" % (self._myLineMarkerColorIndex, marker, color)

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

        return

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
            marker = 'o'
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

        # set/update legend
        if show_legend:
            self._setupLegend()

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
            # print self.par1, type(self.par1)

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
        self._setupLegend()

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
                self._lineDict[ikey] = None
            else:
                # error bar
                plot[0].remove()
                for line in plot[1]:
                    line.remove()
                for line in plot[2]:
                    line.remove()
                self._lineDict[ikey] = None
            # ENDIF(plot)
        # ENDFOR

        self._setupLegend()

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

        :param title:
        :return:
        """
        # TODO/NOW - doc & etc

        self.axes.set_title(title, loc='center', color=color)

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
            except RuntimeError as r_error:
                error_message = 'Unable to remove to 1D line (ID=%d) due to %s.' % (plot_key, str(r_error))
                raise RuntimeError(error_message)
            self._lineDict[plot_key] = None
        else:
            raise RuntimeError('Line with ID %s is not recorded.' % plot_key)

        self.axes.legend()

        # Draw
        self.draw()

        return

    def updateLine(self, ikey, vecx, vecy, linestyle=None, linecolor=None, marker=None, markercolor=None):
        """
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

        self.axes.legend()

        # commit
        self.draw()

        return

    def get_data(self, line_id):
        """
        Get vecX and vecY
        :param line_id:
        :return: 2-tuple as vector X and vector Y
        """
        line = self._lineDict[line_id]
        if line is None:
            print '[ERROR] Line (key = %d) is None. Unable to update' % line_id
            return

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

    def _setupLegend(self, location='best'):
        """ Set up legend
        self.axes.legend()
        Handler is a Line2D object. Lable maps to the line object
        """
        loclist = [
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
        if location not in loclist:
            location = 'best'

        handles, labels = self.axes.get_legend_handles_labels()
        self.axes.legend(handles, labels, loc=location)
        #self.axes.legend(self._myLegendHandlers, self._myLegentLabels)

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

    def __init__(self, parent, canvas):
        """ Initialization
        """
        NavigationToolbar2.__init__(self, canvas, canvas)

        self._myParent = parent
        self._navigationMode = MyNavigationToolbar.NAVIGATION_MODE_NONE

        return

    def get_mode(self):
        """
        :return: integer as none/pan/zoom mode
        """
        return self._navigationMode

    # Overriding base's methods
    def draw(self):
        """
        Canvas is drawn called by pan(), zoom()
        :return:
        """
        NavigationToolbar2.draw(self)

        self._myParent.evt_view_updated()

        return

    def pan(self, *args):
        """

        :param args:
        :return:
        """
        NavigationToolbar2.pan(self, args)

        if self._navigationMode == MyNavigationToolbar.NAVIGATION_MODE_PAN:
            # out of pan mode
            self._navigationMode = MyNavigationToolbar.NAVIGATION_MODE_NONE
        else:
            # into pan mode
            self._navigationMode = MyNavigationToolbar.NAVIGATION_MODE_PAN

        return

    def zoom(self, *args):
        """
        Turn on/off zoom (zoom button)
        :param args:
        :return:
        """
        NavigationToolbar2.zoom(self, args)

        if self._navigationMode == MyNavigationToolbar.NAVIGATION_MODE_ZOOM:
            # out of zoom mode
            self._navigationMode = MyNavigationToolbar.NAVIGATION_MODE_NONE
        else:
            # into zoom mode
            self._navigationMode = MyNavigationToolbar.NAVIGATION_MODE_ZOOM

        return

    def _update_view(self):
        """
        view update called by home(), back() and forward()
        :return:
        """
        NavigationToolbar2._update_view(self)

        self._myParent.evt_view_updated()

        return

