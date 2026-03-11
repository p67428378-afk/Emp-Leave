from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import date, timedelta
import os

from shared.models import Base, Employee, LeaveRequest, LeaveType, FlexiHolidayList

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/leavedb')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create tables if they don't exist and add default leave types
@app.before_first_request
def initialize_database():
    Base.metadata.create_all(engine)
    session = Session()
    try:
        if not session.query(LeaveType).filter_by(name='Casual Leave').first():
            session.add(LeaveType(name='Casual Leave', auto_approve_flag=False))
        if not session.query(LeaveType).filter_by(name='Sick Leave').first():
            session.add(LeaveType(name='Sick Leave', auto_approve_flag=True))
        if not session.query(LeaveType).filter_by(name='Earned Leave').first():
            session.add(LeaveType(name='Earned Leave', auto_approve_flag=False))
        if not session.query(LeaveType).filter_by(name='Flexi Holiday').first():
            session.add(LeaveType(name='Flexi Holiday', auto_approve_flag=True, max_days_per_year=2))
        session.commit()
    except Exception as e:
        session.rollback()
        app.logger.error(f"Error initializing database: {e}")
    finally:
        session.close()

# Helper function to get leave type by name
def get_leave_type(session, name):
    return session.query(LeaveType).filter_by(name=name).first()

# Helper function to calculate working days (simple for now, can be expanded)
def calculate_working_days(start_date, end_date):
    delta = end_date - start_date
    days = 0
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        # Exclude weekends (Saturday=5, Sunday=6)
        if day.weekday() < 5: 
            days += 1
    return days

@app.route('/leave/apply', methods=['POST'])
def apply_for_leave():
    session = Session()
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        leave_type_name = data.get('leave_type')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        reason = data.get('reason')

        if not all([employee_id, leave_type_name, start_date_str, end_date_str, reason]):
            return jsonify({'error': 'Missing required fields'}), 400

        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        if start_date > end_date:
            return jsonify({'error': 'Start date cannot be after end date'}), 400

        employee = session.query(Employee).get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        leave_type = get_leave_type(session, leave_type_name)
        if not leave_type:
            return jsonify({'error': 'Invalid leave type'}), 400

        num_days = calculate_working_days(start_date, end_date)

        # Validate leave balances and rules
        if leave_type.name == 'Casual Leave':
            if employee.used_casual_leave + num_days > employee.total_casual_leave:
                return jsonify({'error': 'Insufficient Casual Leave balance'}), 400
        elif leave_type.name == 'Sick Leave':
            if employee.used_sick_leave + num_days > employee.total_sick_leave:
                return jsonify({'error': 'Insufficient Sick Leave balance'}), 400
        elif leave_type.name == 'Earned Leave':
            if employee.used_earned_leave + num_days > employee.total_earned_leave:
                return jsonify({'error': 'Insufficient Earned Leave balance'}), 400
        elif leave_type.name == 'Flexi Holiday':
            if num_days > leave_type.max_days_per_year:
                return jsonify({'error': f'Flexi Holiday cannot exceed {leave_type.max_days_per_year} days'}), 400
            if employee.used_flexi_holidays + num_days > leave_type.max_days_per_year:
                return jsonify({'error': 'Exceeded annual Flexi Holiday limit'}), 400
            # Check if flexi holidays are from predefined list (simplified for now)
            for i in range(num_days):
                current_date = start_date + timedelta(days=i)
                if not session.query(FlexiHolidayList).filter_by(holiday_date=current_date).first():
                    return jsonify({'error': f'Date {current_date} is not a valid Flexi Holiday'}), 400

        # Check for conflicting leaves (simplified: no overlapping dates for any leave type)
        conflicting_leaves = session.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(['Pending', 'Approved']),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date
        ).first()
        if conflicting_leaves:
            return jsonify({'error': 'Conflicting leave request already exists'}), 400

        # Determine initial status based on leave type
        status = 'Pending'
        if leave_type.auto_approve_flag:
            status = 'Approved'

        new_leave_request = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_type.leave_type_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=status,
            submission_date=date.today()
        )
        session.add(new_leave_request)

        # Update used leave balance if auto-approved
        if status == 'Approved':
            if leave_type.name == 'Casual Leave':
                employee.used_casual_leave += num_days
            elif leave_type.name == 'Sick Leave':
                employee.used_sick_leave += num_days
            elif leave_type.name == 'Earned Leave':
                employee.used_earned_leave += num_days
            elif leave_type.name == 'Flexi Holiday':
                employee.used_flexi_holidays += num_days
            new_leave_request.approval_date = date.today()

        session.commit()

        return jsonify({
            'message': 'Leave request submitted successfully',
            'request_id': new_leave_request.request_id,
            'status': new_leave_request.status
        }), 201

    except Exception as e:
        session.rollback()
        app.logger.error(f"Error applying for leave: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/leave/status/<int:employee_id>', methods=['GET'])
def get_leave_status(employee_id):
    session = Session()
    try:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        leave_requests = session.query(LeaveRequest).filter_by(employee_id=employee_id).all()
        results = []
        for req in leave_requests:
            results.append({
                'request_id': req.request_id,
                'leave_type': req.leave_type.name,
                'start_date': req.start_date.isoformat(),
                'end_date': req.end_date.isoformat(),
                'reason': req.reason,
                'status': req.status,
                'submission_date': req.submission_date.isoformat(),
                'approval_date': req.approval_date.isoformat() if req.approval_date else None,
                'comments': req.comments
            })
        return jsonify(results), 200
    except Exception as e:
        app.logger.error(f"Error getting leave status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/leave/balances/<int:employee_id>', methods=['GET'])
def get_leave_balances(employee_id):
    session = Session()
    try:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404

        balances = {
            'casual_leave': {
                'total': employee.total_casual_leave,
                'used': employee.used_casual_leave,
                'remaining': employee.total_casual_leave - employee.used_casual_leave
            },
            'sick_leave': {
                'total': employee.total_sick_leave,
                'used': employee.used_sick_leave,
                'remaining': employee.total_sick_leave - employee.used_sick_leave
            },
            'earned_leave': {
                'total': employee.total_earned_leave,
                'used': employee.used_earned_leave,
                'remaining': employee.total_earned_leave - employee.used_earned_leave
            },
            'flexi_holidays': {
                'total': employee.total_flexi_holidays, # This might be dynamic based on max_days_per_year
                'used': employee.used_flexi_holidays,
                'remaining': employee.total_flexi_holidays - employee.used_flexi_holidays
            }
        }
        return jsonify(balances), 200
    except Exception as e:
        app.logger.error(f"Error getting leave balances: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    # This block is for local development and testing. 
    # In a production container, Gunicorn or similar WSGI server would run the app.
    app.run(debug=True, host='0.0.0.0', port=5000)
