import os
import time
import pytz
from dateutil.parser import parse
from datetime import datetime
from dateutil import tz

__author__ = 'wzz'


#
# static methods for general purpose
#

# Methods to process time
def convert_to_epoch1(date_time):
    """
    """
    print (type(date_time))
    # convert to time.struct_time
    converted = date_time.timetuple()
    print (converted)

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
    """

    :param epoch_time:
    :return: string
    """
    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
    # such as : '2015-08-01 00:00:00'

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
    utc_time = datetime.strptime(utc_time_formatted, '%Y-%m-%dT%H:%M:%S')

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
    year =  newsttime.tm_year
    month = newsttime.tm_mon
    day =   newsttime.tm_mday
    hour = newhour

    tformat = "%Y %m %d %H"
    newtime = time.strptime("%d %02d %02d %02d"%(year, month, day, hour), tformat)
    print newtime

    return


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


if __name__ == '__main__':
    time_str1 = '2016-04-27 09:19:50.094796666-EDT'
    time_1 = parse_time(time_str1)
    print time_1, type(time_1)

    time_str2 = '4/27/2016 12:29:25 PM'
    time_2 = parse_time(time_str2, local_est=True)
    print time_2, type(time_2)


#def getIptsRunFromFileName(nxsfilename):
#    """ Get IPTS number from a standard SNS nexus file name
#
#    Return :: tuple as 2 int, IPTS and run number
#    """
#    basename = os.path.basename(nxsfilename)
#
#    # Get IPTS
#    if basename == nxsfilename:
#        # not a full path
#        ipts = None
#    else:
#        # Format is /SNS/VULCAN/IPTS-????/0/NeXus/VULCAN_run...
#        try:
#            ipts = int(nxsfilename.split('IPTS-')[1].split('/')[0])
#        except IndexError:
#            ipts = None
#
#    # Get run number
#    try:
#        runnumber = int(basename.split('_')[1])
#    except IndexError:
#        runnumber = None
#    except ValueError:
#        runnumber = None
#
#    return ipts, runnumber