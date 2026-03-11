from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import date
import os

# Assuming models.py is accessible, e.g., via a shared library or copied
# For this example, we'll assume it's in a common location or copied for simplicity
# In a real microservices setup, models might be in a shared package or each service manages its own schema
from shared.models import Base, Employee, LeaveRequest, LeaveType

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/leavedb')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# This service primarily handles approval actions, so it doesn't need to initialize all leave types
# However, it needs to ensure the tables exist if it's the first service to connect
@app.before_first_request
def initialize_database():
    Base.metadata.create_all(engine)

@app.route('/approve/<int:request_id>', methods=['POST'])
def approve_leave_request(request_id):
    session = Session()
    try:
        data = request.get_json()
        approver_id = data.get('approver_id') # Manager's ID
        comments = data.get('comments')

        if not approver_id:
            return jsonify({'error': 'Approver ID is required'}), 400

        leave_request = session.query(LeaveRequest).get(request_id)
        if not leave_request:
            return jsonify({'error': 'Leave request not found'}), 404

        if leave_request.status != 'Pending':
            return jsonify({'error': f'Leave request is already {leave_request.status}'}), 400

        # Fetch leave type to check auto-approval flag (though auto-approved requests shouldn't reach here for manager approval)
        leave_type = session.query(LeaveType).get(leave_request.leave_type_id)

        # For Casual and Earned Leave, verify approver is the employee's manager
        if leave_type.name in ['Casual Leave', 'Earned Leave']:
            employee = session.query(Employee).get(leave_request.employee_id)
            if not employee or employee.manager_id != approver_id:
                return jsonify({'error': 'Only the direct manager can approve this leave type'}), 403

        leave_request.status = 'Approved'
        leave_request.approver_id = approver_id
        leave_request.approval_date = date.today()
        leave_request.comments = comments

        # Update employee's used leave balance
        employee = session.query(Employee).get(leave_request.employee_id)
        num_days = (leave_request.end_date - leave_request.start_date).days + 1 # Simplified for now
        
        if leave_type.name == 'Casual Leave':
            employee.used_casual_leave += num_days
        elif leave_type.name == 'Earned Leave':
            employee.used_earned_leave += num_days
        # Sick Leave and Flexi Holiday are auto-approved and balances updated by Leave Management Service

        session.commit()
        return jsonify({'message': 'Leave request approved successfully', 'request_id': request_id}), 200

    except Exception as e:
        session.rollback()
        app.logger.error(f"Error approving leave request: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/reject/<int:request_id>', methods=['POST'])
def reject_leave_request(request_id):
    session = Session()
    try:
        data = request.get_json()
        approver_id = data.get('approver_id') # Manager's ID
        comments = data.get('comments')

        if not approver_id:
            return jsonify({'error': 'Approver ID is required'}), 400

        leave_request = session.query(LeaveRequest).get(request_id)
        if not leave_request:
            return jsonify({'error': 'Leave request not found'}), 404

        if leave_request.status != 'Pending':
            return jsonify({'error': f'Leave request is already {leave_request.status}'}), 400

        leave_type = session.query(LeaveType).get(leave_request.leave_type_id)

        # For Casual and Earned Leave, verify approver is the employee's manager
        if leave_type.name in ['Casual Leave', 'Earned Leave']:
            employee = session.query(Employee).get(leave_request.employee_id)
            if not employee or employee.manager_id != approver_id:
                return jsonify({'error': 'Only the direct manager can reject this leave type'}), 403

        leave_request.status = 'Rejected'
        leave_request.approver_id = approver_id
        leave_request.approval_date = date.today()
        leave_request.comments = comments

        session.commit()
        return jsonify({'message': 'Leave request rejected successfully', 'request_id': request_id}), 200

    except Exception as e:
        session.rollback()
        app.logger.error(f"Error rejecting leave request: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
