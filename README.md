# Employee Leave Application System

This repository contains the microservices for the Employee Leave Application system, enabling employees to apply for various leave types, track their statuses, and view their balances. The system incorporates automated and manager-based approval workflows and is designed for scalability and security.

## Project Overview

The Employee Leave Application system aims to modernize and streamline the current manual or disparate leave request processes. It provides a centralized, user-friendly, and efficient platform to improve employee experience, reduce administrative overhead, and ensure consistent application of leave policies.

**Key Features:**
- **Leave Type Selection:** Support for Casual Leave, Sick Leave, Earned Leave, and Flexi Holidays, with specific rules for Flexi Holidays (max 2 days/year).
- **Leave Request Submission:** Employees can submit requests with specified dates and reasons.
- **Automated Approval:** Instant approval for Sick Leave and Flexi Holidays.
- **Manager Approval Workflow:** Routing of Casual and Earned Leave requests to the direct manager for approval.
- **Leave Status Tracking:** Employees can view the real-time status (Pending, Approved, Rejected) of their requests.
- **Leave Balance Display:** Accurate display of remaining leave balances for each leave type.
- **Data Security:** Protection of sensitive employee and leave data through encryption and access controls.

## Architecture

The system adopts a **Microservices Architecture** with the following main components:

-   **Frontend Layer:**
    -   **Employee Portal (Web UI):** A responsive web application (e.g., React, Angular, Vue.js - *implementation not part of this repository*).
-   **Backend Layer:**
    -   **API Gateway:** Single entry point for external traffic.
    -   **Leave Management Service:** Manages the lifecycle of leave requests, validates, calculates balances, and interacts with other services.
    -   **Approval Workflow Service:** Orchestrates the approval process based on leave type.
    -   **User Service (IAM Integration):** Manages employee profiles, manager hierarchy, integrates with corporate IAM for authentication and authorization, and syncs with HR Master Data.
-   **Data Layer:**
    -   **Relational Database (PostgreSQL):** Primary data store for all application data.
-   **External Systems:**
    -   **Corporate IAM (SSO):** For employee authentication and authorization.
    -   **HR Master Data:** Source for employee and manager information.

## Services in this Repository

This repository will primarily focus on the backend microservices:

### 1. Leave Management Service

-   **Purpose:** Manages the core logic for leave requests, including creation, validation, and balance updates.
-   **Responsibilities:**
    -   Create, update, and cancel leave requests.
    -   Validate requests against balances and policies (e.g., Flexi Holiday limits).
    -   Calculate and update leave balances.
    -   Initiate approval processes via the Approval Workflow Service.

### 2. Approval Workflow Service

-   **Purpose:** Orchestrates the approval flow for different leave types.
-   **Responsibilities:**
    -   Automatically approve Sick Leave and Flexi Holiday requests.
    -   Route Casual and Earned Leave requests to the appropriate manager.
    -   Update leave request statuses.

### 3. User Service (IAM Integration) - *Placeholder/Integration Point*

-   **Purpose:** Provides employee and manager data, and handles authentication/authorization.
-   **Note:** While critical, the full implementation of this service, especially the corporate IAM integration and HR Master Data sync, is considered an integration point. This repository will include basic models and interfaces for interaction.

## Data Model

The system utilizes a PostgreSQL relational database with the following key entities:

-   **Employee:** Stores employee details, manager relationships, and current leave entitlements/balances.
    -   `employee_id` (PK), `first_name`, `last_name`, `email`, `manager_id` (FK), `total_casual_leave`, `used_casual_leave`, etc.
-   **LeaveRequest:** Records each leave application.
    -   `request_id` (PK), `employee_id` (FK), `leave_type_id` (FK), `start_date`, `end_date`, `reason`, `status`, `approver_id` (FK), `submission_date`, `approval_date`, `comments`.
-   **LeaveType:** Defines available leave types and their properties.
    -   `leave_type_id` (PK), `name` (e.g., 'Casual Leave'), `auto_approve_flag`, `max_days_per_year`.
-   **FlexiHolidayList:** A list of predefined flexi-holidays.
    -   `holiday_date` (PK), `description`.

## Deployment Strategy (Google Cloud Platform - GCP)

The system is designed for deployment on GCP, leveraging its managed services for scalability, reliability, and security.

-   **Compute:** Cloud Run for stateless microservices (containerized with Docker).
-   **Database:** Cloud SQL for PostgreSQL.
-   **Serverless:** Cloud Functions for event-driven tasks (e.g., notifications, scheduled accruals).
-   **CI/CD:** Cloud Build for automated build, test, and deployment pipelines.
-   **Security:** VPC, Cloud Load Balancing, Cloud Armor, Cloud KMS, Cloud Identity & IAM.

## Setup and Local Development

*(Detailed instructions for setting up the development environment, installing dependencies, configuring environment variables, and running the services locally will be provided here as the services are implemented.)*

## API Endpoints

*(Documentation for the API endpoints exposed by each service will be provided here.)*

## Contributing

*(Guidelines for contributing to the project.)*

## License

*(License information.)*
