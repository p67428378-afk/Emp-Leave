from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import date
import os

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'

    employee_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    manager_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=True)
    total_casual_leave = Column(Integer, default=0)
    used_casual_leave = Column(Integer, default=0)
    total_sick_leave = Column(Integer, default=0)
    used_sick_leave = Column(Integer, default=0)
    total_earned_leave = Column(Integer, default=0)
    used_earned_leave = Column(Integer, default=0)
    total_flexi_holidays = Column(Integer, default=0)
    used_flexi_holidays = Column(Integer, default=0)

    manager = relationship('Employee', remote_side=[employee_id], backref='direct_reports')
    leave_requests = relationship('LeaveRequest', back_populates='employee')

    def __repr__(self):
        return f"<Employee(id={self.employee_id}, name='{self.first_name} {self.last_name}')>"

class LeaveType(Base):
    __tablename__ = 'leave_types'

    leave_type_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    auto_approve_flag = Column(Boolean, default=False)
    max_days_per_year = Column(Integer, nullable=True) # For Flexi Holiday

    leave_requests = relationship('LeaveRequest', back_populates='leave_type')

    def __repr__(self):
        return f"<LeaveType(id={self.leave_type_id}, name='{self.name}')>"

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    request_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=False)
    leave_type_id = Column(Integer, ForeignKey('leave_types.leave_type_id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default='Pending') # e.g., 'Pending', 'Approved', 'Rejected'
    approver_id = Column(Integer, ForeignKey('employees.employee_id'), nullable=True)
    submission_date = Column(Date, default=date.today)
    approval_date = Column(Date, nullable=True)
    comments = Column(String, nullable=True)

    employee = relationship('Employee', foreign_keys=[employee_id], back_populates='leave_requests')
    approver = relationship('Employee', foreign_keys=[approver_id])
    leave_type = relationship('LeaveType', back_populates='leave_requests')

    def __repr__(self):
        return f"<LeaveRequest(id={self.request_id}, employee_id={self.employee_id}, status='{self.status}')>"

class FlexiHolidayList(Base):
    __tablename__ = 'flexi_holiday_list'

    holiday_date = Column(Date, primary_key=True)
    description = Column(String, nullable=False)

    def __repr__(self):
        return f"<FlexiHoliday(date={self.holiday_date}, description='{self.description}')>"

# Database setup (example, will be configured via environment variables)
def init_db(database_url=None):
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/leavedb')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

# Example usage (for local testing/initialization)
if __name__ == '__main__':
    print("Initializing database schema...")
    Session = init_db()
    session = Session()

    # Add initial leave types if not present
    if not session.query(LeaveType).filter_by(name='Casual Leave').first():
        session.add(LeaveType(name='Casual Leave', auto_approve_flag=False))
    if not session.query(LeaveType).filter_by(name='Sick Leave').first():
        session.add(LeaveType(name='Sick Leave', auto_approve_flag=True))
    if not session.query(LeaveType).filter_by(name='Earned Leave').first():
        session.add(LeaveType(name='Earned Leave', auto_approve_flag=False))
    if not session.query(LeaveType).filter_by(name='Flexi Holiday').first():
        session.add(LeaveType(name='Flexi Holiday', auto_approve_flag=True, max_days_per_year=2))
    session.commit()
    session.close()
    print("Database schema initialized and default leave types added.")
