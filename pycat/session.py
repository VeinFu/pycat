#! /usr/bin/python

"""
Test session module for pycat.
This moudle will be refered to 'cat-session'. 'cat-session' is a CLI.

The responsibility of a session is to execute a test case. A session has at
least one process running background and some status files stored in cache
directory. Each session has a session ID. If the cache directory is
'/tmp/pycat' and the session ID is '2', the status files of this session is
stored in '/tmp/pycat/session/2'. 
The default status files are following:
    * log.txt    A text file recorded logs.
    * status.db  A sqlite database.
    * pid        A text file recorded PID of a session. If the session is
                 completed, this file will be removed.
    * case.xml   A test case file written in XML. 'cat-session' copies user's
                 test case file and make a hardlink named 'case.xml'.
"""

import sys
import getopt
import os
import shutil
from pkg_resources import iter_entry_points
import signal

from pycat import log
from pycat import config
from pycat import testcase
from pycat import status

#--------------------------------------------------------------------------
#    Session
#--------------------------------------------------------------------------
# Default session files
SESSION_LOG = "log.txt"
SESSION_STATUS = "status.db"
SESSION_PID = "pid"
SESSION_CASE = "case.xml"

class SessionObserver(object):
    """
    A SessionObserver instance provides methods to access status files of a
    session.
    """
    def __init__(self, session_id=None):
        """
        Create a new SessionObserver instance. If the 'session_id hasn't set,
        distribute a new session ID and create the cache directory. If the
        'session_id' has set, find the cache directory and load the status
        files.
        """
        if session_id == None:
            self.sid, self.sdir = self._create_session()
        else:
            self.sid = session_id
            cache = config.Cache()
            rootdir = cache.get_cache("session")
            self.sdir = os.path.join(rootdir, session_id)
            if not os.path.exists(self.sdir):
                raise ValueError("Session %s doesn't exist." % session_id)

    def __str__(self):
        ret = "%s: %s %s" % (self.sid, self.session_pid(), self.sdir)
        return ret

    def _create_session(self):
        """
        Create a new session ID and cache directory. The session ID start
        from 1.
        """
        sid = 1
        sdir = None
        cache = config.Cache()
        rootdir = cache.get_cache("session")
        # Create a new session
        for dirname, subdirs, files in os.walk(rootdir):
            if dirname == rootdir:
                if len(subdirs) == 0:
                    break
                else:
                    while str(sid) in subdirs:
                        sid += 1
        sdir = os.path.join(rootdir, str(sid))
        os.makedirs(sdir)
        return sid, sdir

    def session_id(self):
        """
        Get session ID.
        """
        return self.sid

    def session_dir(self):
        """
        Get session directory.
        """
        return self.sdir

    def session_pid(self):
        """
        Get PID of a session.
        """
        pid_file = os.path.join(self.sdir, SESSION_PID)
        pid = None
        if os.path.exists(pid_file):
            pid_fp = file(pid_file, 'r')
            pid = int(pid_fp.read())
        return pid

    def status_db(self):
        """
        Get the path of 'status.db'
        """
        filepath = os.path.join(self.sdir, SESSION_STATUS)
        if os.path.exists(filepath):
            return filepath
        else:
            return None

    def log(self):
        """
        Get the path of 'log.txt'
        """
        filepath = os.path.join(self.sdir, SESSION_LOG)
        if os.path.exists(filepath):
            return filepath
        else:
            return None

    def case(self):
        """
        Get the path of 'case.xml'
        """
        filepath = os.path.join(self.sdir, SESSION_CASE)
        if os.path.exists(filepath):
            return filepath
        else:
            return None

class Session(object):
    """
    A Session instance executes a test case.
    """
    def __init__(self, case):
        """
        Create a new session including cache directory and status files.
        """
        assert isinstance(case, str)
        self.observer = SessionObserver()
        sdir = self.observer.session_dir()
        # Initialize 'log'
        log_file = os.path.join(sdir, SESSION_LOG)
        log.config(filename=log_file)
        # Copy 'test case'
        case_file = os.path.join(sdir, os.path.basename(case))
        shutil.copyfile(case, case_file)
        os.link(case_file, os.path.join(sdir, SESSION_CASE))
        # Initialize 'status.db'
        status_db = os.path.join(sdir, SESSION_STATUS)
        status.config(status_db)

    def _init_pid(self):
        """
        Write PID into the 'pid' file.
        """
        sdir = self.observer.session_dir()
        pid = os.path.join(sdir, SESSION_PID)
        pid_file = file(pid, 'w+')
        pid_file.write(str(os.getpid()))

    def _remove_pid(self):
        """
        Remove PID file.
        """
        sdir = self.observer.session_dir()
        pid = os.path.join(sdir, SESSION_PID)
        if os.path.exists(pid):
            os.remove(pid)

    def _sigterm_handle(self, signum, frame):
        """
        The callback function for signal SGITERM.
        """
        self._remove_pid()
        sys.exit()

    def _exit(self):
        """
        The callback function for system exit.
        """
        self._remove_pid()

    def __call__(self):
        """
        Execute a test case.
        """
        self._init_pid()
        sys.exitfunc = self._exit
        signal.signal(signal.SIGTERM, self._sigterm_handle)
        print self.observer
        self.start()

    def load_testcase(self):
        """
        Find the plugin and load it.
        """
        sdir = self.observer.session_dir()
        case = os.path.join(sdir, SESSION_CASE)
        conf = testcase.TestCaseConfig(case)
        plugin = conf.get_plugin()
        casetype = conf.get_type()
        mod = None
        pointes = iter_entry_points(group="pycat.plugin", name=None)
        for point in pointes:
            if point.name == plugin:
                mod = point.load()
        if mod:
            caseclass = mod.find_testcase(casetype)
            case = caseclass(conf)
        else:
            raise ValueError("Unknown plugin %s", plugin)
        return case

    def start(self):
        """
        Children of Session sould replace this method.
        """
        raise NotImplementedError

class PerformProcessSession(Session):
    """
    A PerformProcessSession instance executes a test case.
    """
    def __init__(self, case):
        Session.__init__(self, case)

    def start(self):
        """
        Execute a test case.
        """
        case = self.load_testcase()
        case.perform_process()

class PrecheckSession(Session):
    """
    A PrecheckSession instance only check the arguments of a test case.
    """
    def __init__(self, case):
        Session.__init__(self, case)

    def start(self):
        """
        Precheck a test case.
        """
        case = self.load_testcase()
        case.precheck()

def observer_sessions():
    """
    Find all sessions.
    """
    cache = config.Cache()
    rootdir = cache.get_cache("session")
    observers = list()
    list_dirs = os.walk(rootdir)
    for root, dirs, files in list_dirs:
        for subdir in dirs:
            observer = SessionObserver(subdir)
            observers.append(observer)
    observers.sort(key=lambda x: int(x.sid))
    return observers

#--------------------------------------------------------------------------
#    Daemon Lancher
#--------------------------------------------------------------------------
class Daemon(object):
    """
    A Daemon instance executes a Session instance as daemon.
    """
    def __init__(self, execobj):
        self.execobj = execobj

    def start(self):
        """
        Start a daemon.
        """
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, err:
            print >> sys.stderr, "Fork failed: %d (%s)" % (err.errno,
                     err.strerror)
            sys.exit(1)
        os.chdir("/")
        os.setsid()
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, err:
            print >> sys.stderr, "Fork failed: %d (%s)" % (err.errno,
                     err.strerror)
            sys.exit(1)
        self.execobj()

#--------------------------------------------------------------------------
#    CLI Options
#--------------------------------------------------------------------------
def scan_sessions():
    """
    Scan all sessions.
    """
    observers = observer_sessions()
    for obse in observers:
        print obse
    return 0

def precheck_case(case):
    """
    Precheck a test case.
    """
    if case == None:
        print >> sys.stderr, "Please set '--case CASE'."
        return 1
    session = PrecheckSession(case)
    daemon = Daemon(session)
    daemon.start()
    return 0

def start_session(case):
    """
    Start a new session.
    """
    if case == None:
        print >> sys.stderr, "Please set '--case CASE'."
        return 1
    session = PerformProcessSession(case)
    daemon = Daemon(session)
    daemon.start()
    return 0

def print_session_status(session):
    """
    Print the status of a session.
    """
    if session == None:
        print >> sys.stderr, "Please set '--session ID.'"
        return 1
    observer = SessionObserver(session)
    dbfile = observer.status_db()
    summary = status.make_summary(dbfile)
    print summary
    return 0

def stop_session(session):
    """
    Stop a session.
    """
    if session == None:
        print >> sys.stderr, "Please set '--session ID.'"
        return 1
    observer = SessionObserver(session)
    pid = observer.session_pid()
    if pid != None:
        os.kill(pid, signal.SIGTERM)
        print "Stop session %s, PID: %d" % (session, pid)
        return 0
    else:
        print "Session %s doesn't exist." % (session)
        return 1

def export_report(session, distdir):
    """
    Export the report of a session.
    """
    observer = SessionObserver(session)
    if observer.session_pid() != None:
        print >> sys.stderr, "Session hasn't finished."
        return 1
    sdir = observer.session_dir()
    shutil.copytree(sdir, distdir)
    # Modify format of log.txt
    log_file = os.path.join(distdir, "log.txt")
    os.system("unix2dos %s" % (log_file))
    # Make status summary.
    #print "%s" % (os.path.join(distdir, "summary.txt"))
    dbfile = observer.status_db()
    summary = status.make_summary(dbfile)
    summary_fp = file(os.path.join(distdir, "summary.txt"), 'w')
    summary_fp.write(str(summary))
    # Export monitor data to excel.
    excel_file = os.path.join(distdir, "monitor.xls")
    status.export_monitor_to_excel(dbfile, excel_file)
    return 0

def remove_session(session):
    """
    Remove a session.
    """
    observer = SessionObserver(session)
    if observer.session_pid() != None:
        print >> sys.stderr, "Session hasn't finished."
        return 1
    sdir = observer.session_dir()
    shutil.rmtree(sdir, ignore_errors=True)
    return 0

def remove_all_sessions():
    """
    Remove all sessions.
    """
    observers = observer_sessions()
    for observer in observers:
        if observer.session_pid() != None:
            print >> sys.stderr, "%s is running." % (observer)
        else:
            sdir = observer.session_dir()
            shutil.rmtree(sdir, ignore_errors=True)
    return 0

def usage():
    """
    Usage of command line interface.
    """
    mesg = """
Usage: cat-session --scan
                   --precheck --case CASE
                   --start --case CASE 
                   --status --session ID
                   --stop --session ID
                   --export --session ID --dist DIR
                   --remove --session ID
                   --remove-all
Options:
    --scan Scan all sessions.
    --precheck Precheck a testcase.
    --start Start a new session.
    --stop Stop a session.
    --status Print the status.
    --export Export reports of a session.
    --remove Remove a session.
    --remove-all Remove all sessions.
    --case=CASE Set test case file.
    --session=ID Choose a session.
    --dist=DIR Set a dist directory.
    --help Print this help.
"""
    print >> sys.stderr, mesg

def main():
    """
    The main function for command line interface.
    """
    scan_flag = False
    precheck_flag = False
    start_flag = False
    status_flag = False
    stop_flag = False
    export_flag = False
    remove_flag = False
    remove_all_flag = False
    case = None
    session_id = None
    distdir = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "h",
                                   ["help",
                                    "scan", "precheck", "start", "status",
                                    "stop", "export", "remove", "remove-all",
                                    "case=", "session=", "distdir="])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit(1)
            elif opt in ("--scan"):
                scan_flag = True
            elif opt in ("--precheck"):
                precheck_flag = True
            elif opt in ("--start"):
                start_flag = True
            elif opt in ("--status"):
                status_flag = True
            elif opt in ("--stop"):
                stop_flag = True
            elif opt in ("--export"):
                export_flag = True
            elif opt in ("--remove"):
                remove_flag = True
            elif opt in ("--remove-all"):
                remove_all_flag = True
            elif opt in ("--case"):
                case = arg
            elif opt in ("--session"):
                session_id = arg
            elif opt in ("--distdir"):
                distdir = arg
            else:
                print >> sys.stderr, "Unknown option '%s'" % (opt)
                usage()
                sys.exit(1)
    except getopt.GetoptError, err:
        print >> sys.stderr, "getopt error: %s" % (err)
        usage()
        sys.exit(1)

    result = 0
    if scan_flag == True:
        result = scan_sessions()
    elif precheck_flag == True:
        result = precheck_case(case)
    elif start_flag == True:
        result = start_session(case)
    elif status_flag == True:
        result = print_session_status(session_id)
    elif stop_flag == True:
        result = stop_session(session_id)
    elif export_flag == True:
        result = export_report(session_id, distdir)
    elif remove_flag == True:
        result = remove_session(session_id)
    elif remove_all_flag == True:
        result = remove_all_sessions()
    else:
        usage()

    sys.exit(result)

if __name__ == "__main__":
    main()
