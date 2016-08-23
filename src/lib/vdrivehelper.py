__author__ = 'wzz'

import os
import time

#
# static methods for general purpose
#

# Methods to process time


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


def parse_time(date_time_str):
    """
    This is a smart way to guess time format
    example: 2016-04-27 09:19:50.094796666-EDT
    :param date_time_str:
    :return:
    """
    # check input
    assert isinstance(date_time_str, str), 'Input time %s must be a string but not a %s.' \
                                           '' % (str(date_time_str), type(date_time_str))

    # split time and date
    terms = date_time_str.strip().split()
    assert len(terms) > 1, 'Date time %s cannot be split.' % date_time_str

    if terms[0].count(':') == 0:
        # first part is time
        date_str = terms[0]
        time_str = date_time_str.split(date_str)[-1].strip()
    else:
        date_str = terms[-1]
        time_str = date_time_str.split(date_str)[0].strip()

    # auto parse date
    # try to parse date
    if date_str.count('-') > 0:
        sep = '-'
    elif date_str.count('/') > 0:
        sep = '/'

    try:
        blabla
    except ValueError:
        blabla

    return

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
