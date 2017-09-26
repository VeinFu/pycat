#! /usr/bin/python

"""
Status module for pycat. Supply method to access sqlite DB.
"""

import datetime
import sqlite3
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
try:
    from sqlalchemy import Binary
except ImportError, err:
    from sqlalchemy import LargeBinary as Binary

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

import xlwt

from pycat import log
from pycat import config

DB = None
Base = declarative_base()

def set_db(db):
    global DB
    DB = db

def get_db():
    global DB
    return DB

def get_session():
    db = get_db()
    engine = create_engine(db)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

class StatusType(Base):
    __tablename__ = 'status_type'
    name = Column(String(16), primary_key=True)
    description = Column(String(128), nullable=False)

def set_default_status_type():
    status_list = {'running': 'This test is running.',
                   'succeed': 'This test succeeded.',
                   'fail': 'This test failed.'}
    session = get_session()
    for name in status_list:
        status_type = StatusType(name=name, description=status_list[name])
        session.add(status_type)
    session.commit()

class ErrorType(Base):
    __tablename__ = 'error_type'
    name = Column(String(16), primary_key=True)
    key_word = Column(String(64), nullable=False)
    description = Column(String(128))

class Testcase(Base):
    __tablename__ = 'testcase'
    id = Column(Integer, primary_key=True)
    name = Column(String(16))
    process_type = Column(String(16))
    cycle_total = Column(Integer)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)

class Cycle(Base):
    __tablename__ = 'cycle'
    name = Column(String(32), primary_key=True)
    item_total = Column(Integer, nullable=False)
    case_id = Column(Integer, ForeignKey('testcase.id'))
    testcase = relationship(Testcase)

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    description = Column(String(64), nullable=False)
    cycle_name = Column(String(32), ForeignKey('cycle.name'))
    status = Column(String(16), ForeignKey('status_type.name'))
    cycle = relationship(Cycle)
    status_type = relationship(StatusType)

class ErrorCounter(Base):
    __tablename__ = 'error_counter'
    id = Column(Integer, primary_key=True)
    error_type_name = Column(String(16), ForeignKey('error_type.name'))
    item_id = Column(Integer, ForeignKey('item.id'))
    mesg = Column(Binary)
    error_type = relationship(ErrorType)
    item = relationship(Item)

class Monitor(Base):
    __tablename__ = 'monitor'
    name = Column(String(32), primary_key=True)
    value_type = Column(String(32))
    units = Column(String(16))

class MonitorData(Base):
    __tablename__ = 'monitor_data'
    id = Column(Integer, primary_key=True)
    monitor = Column(String(32), ForeignKey('monitor.name'))
    time = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(String(64))

def is_test_finished():
    pass

def config(db_path):
    db = "sqlite:///%s" % (db_path)
    set_db(db)
    engine = create_engine(db)
    Base.metadata.create_all(engine)
    set_default_status_type()

class Summary(object):
    def __init__(self):
        self.desc = None
        self.children = list()

    def __str__(self):
        ret = "%s\n" % self.desc
        for child in self.children:
            ret += "%s" % (child)
        return ret

def make_summary(db_path = None):
    if db_path != None:
        db = "sqlite:///%s" % (db_path)
        engine = create_engine(db)
        set_db(db)
    session = get_session()
    summary = Summary()
    summary.desc = "Test Case"
    for testcase in session.query(Testcase).all():
        testcase_sum = Summary()
        summary.children.append(testcase_sum)
        cycle_all = session.query(Cycle).filter(Cycle.case_id == testcase.id).all()
        cycle_succ = 0
        cycle_fail = 0
        for cycle in cycle_all:
            cycle_sum = Summary()
            testcase_sum.children.append(cycle_sum)
            item_all = session.query(Item).filter(Item.cycle_name == cycle.name)
            item_succ = 0
            item_fail = 0
            item_summary = None
            for item in item_all:
                item_sum = Summary()
                cycle_sum.children.append(item_sum)
                if item.status == "succeed":
                    item_sum.desc = "Test Item '%s' succeed" % (item.description)
                    item_succ += 1
                else:
                    item_sum.desc = "Test Item '%s' fail" % (item.description)
                    item_fail += 1

            if item_fail == 0:
                cycle_succ += 1
            else:
                cycle_fail += 1
            cycle_sum.desc = "Cycle %s: Item Total: %d, Succeed: %d, Fail: %d" %  (cycle.name, cycle.item_total, item_succ, item_fail)
        testcase_sum.desc =  "Start: %s, End: %s\nCycle Total: %d, Succeed: %d, Fail: %d" % (testcase.start_time, testcase.end_time, testcase.cycle_total, cycle_succ, cycle_fail)
    return summary

def export_monitor_to_excel(db_path, dist):
    db = "sqlite:///%s" % (db_path)
    engine = create_engine(db)
    set_db(db)
    session = get_session()
    wb = xlwt.Workbook()
    for monitor in session.query(Monitor).all():
        sheet = wb.add_sheet(monitor.name)
        sheet.write(0, 0, "Date")
        sheet.write(0, 1, monitor.units)
        row = 1
        sheet.col(0).width = 30 * 256
        for monitor_data in session.query(MonitorData).filter(MonitorData.monitor == monitor.name).all():
            sheet.write(row, 0, str(monitor_data.time))
            sheet.write(row, 1, monitor_data.data)
            row += 1
    wb.save(dist)


