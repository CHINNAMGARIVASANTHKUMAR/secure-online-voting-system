# Secure Online Voting System

<p align="center">
  <strong>A Secure Voting Prototype with OTP Authentication and Blockchain-Inspired Record Keeping</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Security-Application%20Prototype-0A66C2?style=for-the-badge" alt="Security prototype" />
</p>

## Overview

The Secure Online Voting System is an academic software project that explores digital voter authentication, voting workflows, administrative controls, and verifiable vote-record storage.

The prototype is designed to demonstrate how web application technologies and security concepts can be combined to support a structured voting process.

**Project status:** Academic / educational prototype. This project is not certified for conducting public or government elections.

## Problem Statement

Voting applications must address important concerns, including unauthorized access, duplicate voting, protection of voter information, integrity of stored records, and accountability for administrative actions.

This project explores these challenges through a web-based voting workflow and security-focused record management.

## Objectives

- Implement a structured voter registration and authentication workflow.
- Explore OTP-based verification.
- Provide an interface for eligible users to participate in a voting process.
- Support election and candidate management through administrative controls.
- Store voting records using the project's implemented database and record-storage mechanism.
- Explore blockchain-inspired techniques for detecting unauthorized record changes.
- Document security limitations and opportunities for improvement.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Flask | Web application framework |
| SQLite | Database storage |
| Twilio | OTP delivery, if configured |
| HTML, CSS, JavaScript | User interface, if included |
| Custom blockchain implementation | Vote-record integrity demonstration, if implemented |

Only retain the technologies that are actually present in the repository.

## Core Modules

### 1. Voter Registration and Authentication

Provides a registration and login workflow. OTP verification may be used to add an additional authentication step.

### 2. Voting Module

Provides the voting interface and processes a user's selection according to the implemented eligibility and duplicate-voting checks.

### 3. Election Administration

If implemented, administrators can manage election status, candidates, and voting-related records.

### 4. Vote Record Storage

Stores voting data in the configured database. If a custom blockchain is implemented, explain how blocks are linked, how hashes are calculated, and how integrity is verified.

### 5. Activity Logging

If implemented, records relevant application or administrative events to support debugging and auditing.

## System Workflow

1. A voter opens the application.
2. The voter completes registration or authentication.
3. The application verifies the required credentials and OTP, if enabled.
4. The voter accesses the available election.
5. The application checks the relevant voting rules.
6. The vote is recorded using the implemented storage mechanism.
7. Authorized administrators can manage or review election information according to their permissions.

## Project Structure

The following is a suggested structure. Adjust it to match the actual files in your repository.

```text
Election_Commication_Voting/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
├── static/
├── database/
├── blockchain/
├── tests/
└── screenshots/
```

## Installation and Setup

### Prerequisites

- Python 3.10 or a compatible version for your dependencies
- pip
- Git

### 1. Clone the repository

```bash
git clone https://github.com/CHINNAMGARIVASANTHKUMAR/Election_Commication_Voting.git
cd Election_Commication_Voting
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

If the repository contains `requirements.txt`:

```bash
pip install -r requirements.txt
```

If it does not, create the file based on the dependencies your code actually imports.

### 4. Configure environment variables

If your application uses Twilio or other external services, configure the required credentials through environment variables. Do not commit API keys, passwords, OTP secrets, or production credentials.

### 5. Run the application

If your Flask entry point is `app.py`:

```bash
python app.py
```

Follow the local URL printed by the application. The entry point and startup command may differ depending on the source code.

## Security Considerations

- Store secrets outside the source code.
- Use appropriate password hashing and server-side validation.
- Apply access controls to administrative functionality.
- Validate eligibility and prevent duplicate vote submissions on the server.
- Minimize collection and retention of personal information.
- Protect database files, logs, and backups.
- Use HTTPS in a properly configured deployment.
- Test authentication, authorization, and input validation.

A hash-linked data structure alone does not guarantee election security, voter anonymity, or protection against a compromised application or administrator.

## Testing

Document the tests that you have actually performed.

| Test area | Result |
|---|---|
| Registration and login | Add verified result |
| OTP verification | Add verified result |
| Duplicate-vote prevention | Add verified result |
| Administrative access control | Add verified result |
| Vote-record integrity | Add verified result |
| Invalid input handling | Add verified result |

## Screenshots and Demo

Add genuine screenshots of:

- Registration and login page
- OTP verification screen
- Voting interface
- Administrative dashboard
- Vote-record verification, if implemented

Remove personal information, credentials, OTPs, and sensitive database values before uploading screenshots.

## Limitations

This is an educational prototype and must not be treated as a production election platform without independent security review and extensive testing.

Real election systems require rigorous identity and eligibility controls, ballot secrecy, verifiable election procedures, resilience, independent audits, and compliance with applicable laws and standards.

## Future Enhancements

- Automated tests for critical voting workflows.
- Stronger authentication and role-based authorization.
- Security event logging and monitoring.
- Integrity verification tests for stored records.
- Improved accessibility and user interface.
- Documented deployment and security testing procedures.

## Author

**Chinnamgari Vasanthkumar**

Cybersecurity | Python | Network Security | Secure Application Development

- GitHub: [CHINNAMGARIVASANTHKUMAR](https://github.com/CHINNAMGARIVASANTHKUMAR)
- LinkedIn: [Connect with me](https://www.linkedin.com/in/vasanthkumar-chinnamgari-783b88426/)

---

*Developed for academic learning and cybersecurity education. Use test data and authorized environments only.*
