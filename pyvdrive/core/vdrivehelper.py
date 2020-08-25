import os
import time
import pytz
from dateutil.parser import parse
import datetime
from dateutil import tz
from pyvdrive.core import datatypeutility
import mantid    # type: ignore
import stat
import numpy as np  # type: ignore
import pyvdrive.core.reduce_VULCAN as reduce_VULCAN

__author__ = 'wzz'

#
# static methods for general purpose for VDRIVE compatible
#


# Methods to process time
def convert_to_epoch1(date_time):
    """
    convert date time to epoch (version 1)
    :param date_time:
    :return:
    """
    # convert to time.struct_time
    converted = date_time.timetuple()
    epoch_time = time.mktime(converted)

    return epoch_time


def convert_to_epoch(m_date, m_time="00:00:00", date_pattern='%m/%d/%Y',
                     time_pattern='%H:%M:%S'):
    """ Convert a time in string format to epoch time
    Be aware that using module time, the resolution is second only
    :param m_date: input date (string)
    :param m_time: input time (string)
    :param date_pattern: format for date
    :param time_pattern: format for time
    :return: integer as total seconds from 1990.01.01
    """
    # check inputs
    assert isinstance(m_date, str)
    assert isinstance(m_time, str)

    # Form datetime and pattern
    date_time = '%s %s' % (m_date, m_time)

    # pattern for AM or PM
    pattern = '%s %s' % (date_pattern, time_pattern)
    if m_time.lower().endswith('m'):
        # ends with am or pm
        pattern += ' %p'

    # Convert to epoch
    try:
        epoch = int(time.mktime(time.strptime(date_time, pattern)))
    except ValueError as e:
        raise e

    return epoch


def convert_to_strtime_from_epoch(epoch_time):
    """ convert time in string in %Y-%m-%d %H:%M:%S format to epoch time
    :param epoch_time:
    :return: python datetime.datetime object
    """
    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))

    return date_time


def convert_to_utc(local_time):
    """
    convert local time to UTC time
    :param local_time:
    :return:
    """
    # check whether it is a local time, i.e., with time zone information
    # blabla

    # convert to UTC time
    utc_time = local_time.astimezone(pytz.utc)

    return utc_time


def convert_utc_to_local_time(utc_time):
    """
    convert UTC time to local time
    :param utc_time:
    :return:
    """
    # convert UTC time to a certain string in the format as 2017-11-29T13:51:42.787380666
    utc_time_formatted = str(utc_time).split('.')[0]
    utc_time = datetime.datetime.strptime(utc_time_formatted, '%Y-%m-%dT%H:%M:%S')

    # METHOD 1: Hardcode zones:
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')  # VULCAN will never been moved to other time zone!

    # METHOD 2: Auto-detect zones:
    # from_zone = tz.tzutc()
    # to_zone = tz.tzlocal()

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    utc_time = utc_time.replace(tzinfo=from_zone)

    # Convert time zone
    east_time = utc_time.astimezone(to_zone)

    return east_time


# TODO - TONIGHT - UNIT TEST :
def merge_2_logs(vec_times_x, vec_value_x, vec_times_y, vec_value_y):
    """
    Merge 2 time series sample logs along with the time
    For example:
    We have
    x: (t1, x1), (t3, x2), (t6, x3)
    y: (t2, y1), (t4, y2), (t5, y3)
    where t_i < t_(i+1)
    The output shall be
    (x1, y1) @ t2, (x2, y1) @ t3, (x2, y2) @ t4, (x2, y3) @ t5, (x3, y3) @ t6
    :param vec_times_x:
    :param vec_value_x:
    :param vec_times_y:
    :param vec_value_y:
    :return:
    """
    datatypeutility.check_numpy_arrays('X times and value vectors', [
                                       vec_times_x, vec_value_x], 1, True)
    datatypeutility.check_numpy_arrays('Y times and value vectors', [
                                       vec_times_y, vec_value_y], 1, True)

    list_x = list()
    list_y = list()

    # search for the start
    if vec_times_x[0] == vec_times_y[0]:
        index_x = 0
        index_y = 0
    elif vec_times_x[0] < vec_times_y[0]:
        # Y starts later
        index_x = np.searchsorted(vec_times_x, vec_times_y[0]) - 1
        index_y = 0
        assert index_x >= 0, 'As X starts first, starting searching index of X cannot be 0'
    else:
        # X starts later
        index_x = 0
        index_y = np.searchsorted(vec_times_y, vec_times_x[0]) - 1
        assert index_y >= 0, 'As Y starts first, starting searching index of Y cannot be 0'
    # END-IF-ELSE

    # add entries interveningly
    continue_add = True
    while continue_add:
        list_x.append(vec_value_x[index_x])
        list_y.append(vec_value_y[index_y])
        if vec_times_x[index_x] == vec_times_y[index_y]:
            # index X and Y are same: occur at tx = ty
            update_x = True
            update_y = True
        elif vec_value_x[index_x] < vec_times_y[index_y]:
            # time X is earlier: occur @ ty
            update_x = True
            update_y = False
        else:
            # time Y is earlier: occur @ tx
            update_x = False
            update_y = True

        # update index of X and Y
        if update_x:
            index_x += 1
        if update_y:
            index_y += 1

        # end loop signal
        if index_x == vec_times_x.shape[0] or index_y == vec_value_y.shape[0]:
            continue_add = False
    # END-WHILE

    # add entries from a single side
    if index_x < vec_times_x.shape[0]:  # X is not running out
        for index in range(index_x, vec_times_x.shape[0]):
            list_x.append(vec_value_x[index])
            list_y.append(vec_value_y[index_y-1])  # last entry of Y
    elif index_y < vec_times_y.shape[0]:  # Y is not running oout
        for index in range(index_y, vec_times_y.shape[0]):
            list_x.append(vec_value_x[index_x-1])  # last entry of X
            list_y.append(vec_value_y[index])

    # print (vec_times_x)
    # print (vec_times_y)
    # print (vec_value_x)
    # print (vec_value_y)
    # print (list_x)
    # print (list_y)

    return np.array(list_x), np.array(list_y)


def parse_time(date_time_str, local_est=True):
    """
    This is a smart way to guess time format
    example: 2016-04-27 09:19:50.094796666-EDT
    :param date_time_str:
    :param local_est: local time zone is EST
    :return: datetime.datetime instance
    """
    # check input
    assert isinstance(date_time_str, str), 'Input time %s must be a string but not a %s.' \
                                           '' % (str(date_time_str), type(date_time_str))

    # split time and date
    terms = date_time_str.strip().split()
    assert len(terms) > 1, 'Date time %s cannot be split.' % date_time_str

    # time string must have : inside
    if terms[0].count(':') == 0:
        # first part is time
        date_str = terms[0]
        time_str = date_time_str.split(date_str)[-1].strip()
    else:
        date_str = terms[-1]
        time_str = date_time_str.split(date_str)[0].strip()

    # time zone?
    if time_str.count('-') > 0:
        # case for -EDT or -EST
        time_terms = time_str.split('-')
        time_str = time_terms[0]
        tz_str = time_terms[1]
    else:
        tz_str = None

    # parse date time to naive time
    try:
        date_time_str = '%s %s' % (date_str, time_str)
        date_time = parse(date_time_str)
    except ValueError as val_err:
        raise RuntimeError('Unable to convert %s to datetime instance due to %s.' % str(val_err))

    # set time zone
    if tz_str is None and local_est:
        time_zone = pytz.timezone('US/Eastern')
    elif tz_str is not None:
        if tz_str == 'EDT' or tz_str == 'EST':
            time_zone = pytz.timezone('US/Eastern')
        else:
            raise RuntimeError('Time zone flag %s is not supported.' % tz_str)
    else:
        time_zone = pytz.utc

    # add time zone to the naive time to be aware
    date_time = time_zone.localize(date_time)

    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    print(date_time.strftime(fmt))

    return date_time


def setGPDateTime(epochtime):
    """ Reset epoch time to standard end time
    Link: http://www.tutorialspoint.com/python/time_strptime.htm
    """
    if isinstance(epochtime, float) is False:
        raise TypeError("Epoch time must be float.  Use getmtime() or getctime().")

    sttime = time.strptime(time.ctime(epochtime))
    rollbackdays = 0
    # set hour to 12 or 15
    if sttime.tm_hour < 9:
        rollbackdays = 1
        newhour = 15
    elif sttime.tm_hour >= 15:
        newhour = 15
    else:
        # only between 9 and 15 will be 12
        newhour = 12

    # roll back if needed
    epochtime -= rollbackdays*24*3600

    # get new wday
    sttime = time.strptime(time.ctime(epochtime))
    if sttime.tm_wday >= 5:
        rollbackdays = sttime.tm_wday-4
        # print "[DB] Rolls back for %d days" % (rollbackdays)
        epochtime -= rollbackdays*24*3600
        # if rolling back, the hour should be modified
        newhour = 15

    # set the new date by new hour
    newsttime = time.strptime(time.ctime(epochtime))
    year = newsttime.tm_year
    month = newsttime.tm_mon
    day = newsttime.tm_mday
    hour = newhour

    tformat = "%Y %m %d %H"
    newtime = time.strptime("%d %02d %02d %02d" % (year, month, day, hour), tformat)
    print(newtime)


# SNS related
def get_ipts_number_from_dir(ipts_dir):
    """ Get IPTS number from dir
    :param ipts_dir:
    :return: 2-tuple
    """
    assert(isinstance(ipts_dir, str))
    if ipts_dir.count('IPTS-') == 0:
        return False, 'No IPTS- involved.'

    # Simple way to figure out the file system
    terms = ipts_dir.split('IPTS-')
    if terms[0].endswith('/'):
        token = '/'
    else:
        token = '\\'

    ipts_number_str = terms[1].split(token)[0]
    try:
        ipts_number = int(ipts_number_str)
    except ValueError:
        return False, 'After IPTS-, %s is not an integer' % ipts_number_str

    return True, ipts_number


def export_experiment_log(ws_name, record_file_name, sample_name_list, sample_title_list, sample_operation_list,
                          patch_list):
    """ Export experiment logs
    Note: duplicate from reduce_VULCAN.ReduceVulcanData._export_experiment_log
    :param ws_name:
    :param record_file_name:
    :param sample_title_list:
    :param sample_operation_list:
    :param patch_list:
    :return:
    """
    # check inputs
    datatypeutility.check_file_name(record_file_name, check_exist=False, check_writable=True,
                                    is_dir=False, note='Standard material record file')
    datatypeutility.check_list('Sample log names', sample_name_list)
    datatypeutility.check_list('Sample log titles', sample_title_list)
    datatypeutility.check_list('Sample log operations', sample_operation_list)

    if len(sample_name_list) != len(sample_title_list) or len(sample_name_list) != len(sample_operation_list):
        raise RuntimeError('Sample name list ({0}), sample title list ({1}) and sample operation list ({2}) '
                           'must have the same size.'
                           ''.format(len(sample_name_list), len(sample_title_list), len(sample_operation_list)))

    # get file mode
    if os.path.exists(record_file_name):
        file_write_mode = 'append'
    else:
        file_write_mode = 'new'

    # write
    print('[DB...BAT] Export (TAG) experiment log record: {}'.format(record_file_name))
    try:
        mantid.simpleapi.ExportExperimentLog(InputWorkspace=ws_name,
                                             OutputFilename=record_file_name,
                                             FileMode=file_write_mode,
                                             SampleLogNames=sample_name_list,
                                             SampleLogTitles=sample_title_list,
                                             SampleLogOperation=sample_operation_list,
                                             TimeZone="America/New_York",
                                             OverrideLogValue=patch_list,
                                             OrderByTitle='RUN',
                                             RemoveDuplicateRecord=True)
    except RuntimeError as run_err:
        message = 'Failed to export experiment record to {} due to {}.' \
                  ''.format(record_file_name, run_err)
        return False, message
    except ValueError as value_err:
        message = 'Exporting experiment record to {0} failed due to {1}.' \
                  ''.format(record_file_name, value_err)
        return False, message

    # Set up the mode for global access
    file_access_mode = oct(os.stat(record_file_name)[stat.ST_MODE])
    file_access_mode = file_access_mode[-3:]
    if file_access_mode != '666' and file_access_mode != '676':
        try:
            os.chmod(record_file_name, 0o666)
        except OSError as os_err:
            return False, '[ERROR] Unable to set file {0} to mode 666 due to {1}' \
                          ''.format(record_file_name, os_err)
    # END-IF

    return True, ''


def export_normal_sample_log(ipts_number, run_number, ws_name, record_file_name):

    # convert record-tuple list to three list
    sample_title_list = [item[0] for item in reduce_VULCAN.RecordBase]
    sample_name_list = [item[1] for item in reduce_VULCAN.RecordBase]
    sample_operation_list = [item[2] for item in reduce_VULCAN.RecordBase]
    patch_list = reduce_VULCAN.generate_patch_log_list('VULCAN', ipts_number=ipts_number,
                                                       run_number=run_number)

    status, error_message = export_experiment_log(ws_name,
                                                  record_file_name=record_file_name,
                                                  sample_name_list=sample_name_list,
                                                  sample_title_list=sample_title_list,
                                                  sample_operation_list=sample_operation_list,
                                                  patch_list=patch_list)

    return status, error_message


def export_standard_sample_log(ipts_number, run_number, ws_name, standard_sample_tuple):
    import shutil

    # convert record-tuple list to three list
    sample_title_list = [item[0] for item in reduce_VULCAN.RecordBase]
    sample_name_list = [item[1] for item in reduce_VULCAN.RecordBase]
    sample_operation_list = [item[2] for item in reduce_VULCAN.RecordBase]
    material_name, tag_dir, standard_record_file = standard_sample_tuple
    patch_list = reduce_VULCAN.generate_patch_log_list('VULCAN', ipts_number=ipts_number,
                                                       run_number=run_number)
    status, error_message = export_experiment_log(ws_name,
                                                  record_file_name=os.path.join(
                                                      tag_dir, standard_record_file),
                                                  sample_name_list=sample_name_list,
                                                  sample_title_list=sample_title_list,
                                                  sample_operation_list=sample_operation_list,
                                                  patch_list=patch_list)
    # copy GSAS file
    # TODO - TONIGHT - Better code quality
    src_gda = '/SNS/VULCAN/IPTS-{}/shared/binned_data/{}.gda'.format(ipts_number, run_number)
    assert os.path.exists(src_gda), '{} does not exists'.format(src_gda)
    shutil.copy(src_gda, tag_dir)

    return status, error_message


def search_sorted_nearest(vector, values):  # NOTE: SAME as separate_log_cooling.search_sorted_nearest()
    """
    search a sorted numpy array to the nearest value
    :param vector:
    :param values:
    :return:
    """
    index_list = np.searchsorted(vector, values, side='left', sorter=None)
    for i, index_i in enumerate(index_list):
        if index_i == 0:
            pass  # already out of left boundary
        elif index_i == vector.shape[0]:
            pass  # already out of right boundary
        else:
            print('[DB...BAT...1] For {}: Selected vector (+/- 1): {}'
                  ''.format(values[i], vector[index_i-1:index_i+2]))
            if values[i] - vector[index_i-1] < vector[index_i] - values[i]:
                # v_i is closer to left value
                index_list[i] = index_i - 1
    # END-FOR

    return index_list


if __name__ == '__main__':
    time_str1 = '2016-04-27 09:19:50.094796666-EDT'
    time_1 = parse_time(time_str1)
    print(time_1, type(time_1))

    time_str2 = '4/27/2016 12:29:25 PM'
    time_2 = parse_time(time_str2, local_est=True)
    print(time_2, type(time_2))
