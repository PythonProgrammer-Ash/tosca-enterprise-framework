Tosca Framework Setup Guide
📋 Table of Contents
Prerequisites
Environment Setup
Tosca Workspace Configuration
CI/CD Integration
Test Management Integration
Troubleshooting
Prerequisites
Software Requirements
Required:
├── Tricentis Tosca 16.0 or higher
├── Tosca DEX Server (for parallel execution)
├── Python 3.9+
├── PowerShell 7.0+
├── Git 2.30+
└── Visual Studio Code (recommended IDE)

Optional but Recommended:
├── Jenkins 2.400+ or Azure DevOps
├── qTest Manager account
├── JIRA + Xray plugin
└── Slack/Teams for notifications
License Requirements
Tosca Commander license
Tosca DEX licenses (minimum 3 for optimal parallel execution)
API testing license (if performing API validation)
Mobile testing license (if testing mobile applications)
Hardware Requirements
Tosca Commander Workstation:
├── CPU: Intel i7 or higher (8+ cores recommended)
├── RAM: 16GB minimum, 32GB recommended
├── Disk: 500GB SSD
└── Network: Stable connection to test environments

DEX Execution Agents:
├── CPU: Intel i5 or higher (4+ cores)
├── RAM: 8GB minimum per agent
├── Disk: 250GB SSD
└── OS: Windows 10/11 or Windows Server 2019+
Environment Setup
Step 1: Install Tosca
powershell

# Run Tosca installer with admin privileges

# Choose Custom Installation

Installation Options:
☑ Tosca Commander
☑ Tosca ToscaCI Client
☑ Tosca DEX Server (on DEX server machine)
☑ API Engine
☐ Mobile Engine (if needed)
☑ Database Connector

# Recommended Installation Path

C:\Program Files (x86)\TRICENTIS\Tosca Testsuite
Step 2: Configure DEX Server
powershell

# On DEX Server machine

cd "C:\Program Files (x86)\TRICENTIS\Tosca Testsuite\ToscaDex\Server"

# Edit DexServer.exe.config

# Set your workspace connection string

<configuration>
  <connectionStrings>
    <add name="WorkspaceConnection" 
         connectionString="Server=YOUR_SERVER;Database=Tosca_Banking;Integrated Security=True" />
  </connectionStrings>
</configuration>

# Start DEX Server

.\DexServer.exe install
Start-Service "Tosca DEX Server"
Step 3: Configure DEX Agents
powershell

# On each agent machine

cd "C:\Program Files (x86)\TRICENTIS\Tosca Testsuite\ToscaDex\Agent"

# Edit DexAgent.exe.config

<configuration>
  <appSettings>
    <add key="DexServerUrl" value="http://dex-server:8731" />
    <add key="AgentName" value="DEX_Agent_1" />
    <add key="MaxConcurrentExecutions" value="3" />
  </appSettings>
</configuration>

# Register and start agent

.\DexAgent.exe install
Start-Service "Tosca DEX Agent"

# Verify agent registration

# Check DEX Server admin console: http://dex-server:8731/admin

Step 4: Setup Python Environment
bash

# Create virtual environment

python -m venv tosca-env

# Activate virtual environment

# Windows

tosca-env\Scripts\activate

# Install dependencies

pip install -r requirements.txt
requirements.txt:

requests==2.31.0
jira==3.5.0
pytest==7.4.0
lxml==4.9.3
pandas==2.0.3
openpyxl==3.1.2
python-dotenv==1.0.0
slack-sdk==3.21.3
Tosca Workspace Configuration
Step 1: Create Workspace Structure
Banking_App.tws
├── 📁 Modules/
│ ├── 📁 01_Login/
│ ├── 📁 02_Navigation/
│ ├── 📁 03_Transactions/
│ ├── 📁 04_Reports/
│ └── 📁 05_Admin/
│
├── 📁 TestCases/
│ ├── 📁 Smoke_Tests/
│ ├── 📁 Regression_Tests/
│ ├── 📁 API_Tests/
│ └── 📁 End_to_End/
│
├── 📁 TestStepBlocks/
│ ├── 📁 Authentication/
│ ├── 📁 Navigation/
│ ├── 📁 Transactions/
│ └── 📁 Utilities/
│
├── 📁 TestCaseDesign/
│ ├── 📁 Customer_Data/
│ ├── 📁 Transaction_Data/
│ └── 📁 Configuration/
│
├── 📁 ExecutionLists/
│ ├── Banking_Smoke_Suite
│ ├── Banking_Regression_Suite
│ └── Banking_FullSuite
│
└── 📁 Requirements/
└── Banking_Requirements.xlsx (imported from JIRA)
Step 2: Configure Steering
Best Practice Steering Configuration:

Priority Order:

1. ID (highest priority, most stable)
2. Name (good for static elements)
3. CSS Selector (for modern web apps)
4. XPath (last resort, use anchors)

Example Module Configuration:
┌─────────────────────────────────────────────────┐
│ Control: txt_Username │
├─────────────────────────────────────────────────┤
│ Technology: HTML │
│ Control Type: TextBox │
│ │
│ Steering Parameters: │
│ ☑ ID: username Priority: 1 │
│ ☑ Name: user-email Priority: 2 │
│ ☑ CSS: input[type='email'] Priority: 3 │
│ ☐ XPath: //input[@id='username'] Priority: 4 │
│ │
│ Dynamic Recognition: │
│ ☑ Enable adaptive identification │
│ ☑ Use anchors for XPath │
└─────────────────────────────────────────────────┘
Step 3: Setup Execution Configuration
Execution Configuration:

1. Create DEX Configuration:

   - Name: Parallel_3_Agents
   - Agents: DEX_Agent_1, DEX_Agent_2, DEX_Agent_3
   - Distribution: Load Balanced
   - Screenshot on: Failure + Verification
   - Logging Level: Information

2. Create Browser Profiles:

   - Chrome_Latest
   - Firefox_Latest
   - Edge_Chromium

3. Configure Recovery Scenarios:
   - Session Timeout Handler
   - Unexpected Popup Handler
   - Browser Crash Recovery
     CI/CD Integration
     Jenkins Setup
     Step 1: Install Jenkins Plugins
     Required Plugins:
     ☑ Pipeline
     ☑ Git
     ☑ HTML Publisher
     ☑ Email Extension
     ☑ Slack Notification
     ☑ Python
     ☑ PowerShell
     Step 2: Configure Jenkins Credentials
     Manage Jenkins → Credentials → Global credentials

Add:

1. qtest-api-token (Secret text)
2. jira-credentials (Username with password)
3. slack-webhook-url (Secret text)
4. git-credentials (Username with password)
   Step 3: Create Jenkins Pipeline Job
   New Item → Pipeline

General:
☑ Discard old builds (Keep last 30 builds)
☑ This project is parameterized

Build Triggers:
☑ Poll SCM: H/15 \* \* \* _ (every 15 minutes)
☑ Build periodically: H 2 _ \* \* (nightly at 2 AM)

Pipeline:
Definition: Pipeline script from SCM
SCM: Git
Repository URL: https://github.com/yourcompany/tosca-framework
Branch: \*/main
Script Path: ci-cd/Jenkinsfile
Azure DevOps Setup
Step 1: Create Build Pipeline
yaml

# azure-pipelines.yml already provided in repository

Steps:

1. Navigate to Pipelines → New Pipeline
2. Select: Azure Repos Git (or GitHub)
3. Choose repository
4. Select: Existing Azure Pipelines YAML file
5. Path: /ci-cd/azure-pipelines.yml
6. Save and Run
   Step 2: Configure Variable Groups
   Pipelines → Library → Variable Groups

Create:

1. qTest-Credentials

   - qtest-api-url
   - qtest-api-token (mark as secret)
   - qtest-project-id

2. JIRA-Credentials

   - jira-url
   - jira-username
   - jira-password (mark as secret)

3. Tosca-Configuration
   - workspace-path
   - dex-server-url
     Step 3: Configure Service Connections
     Project Settings → Service connections

Add:

1. Generic Connection for qTest

   - Server URL: https://yourcompany.qtestnet.com
   - Token: <API Token>

2. JIRA Connection
   - Server URL: https://yourcompany.atlassian.net
   - Username/Password or API Token
     Test Management Integration
     qTest Integration
     Step 1: Configure qTest Project
3. Create Project: Banking_Automation
4. Create Test Cycles:

   - Daily_Smoke
   - Weekly_Regression
   - Release_Validation

5. Map Tosca Tests to qTest:
   - Export test cases from Tosca
   - Import into qTest
   - Note qTest test case IDs
   - Map IDs in Tosca TestCase properties
     Step 2: Configure API Integration
     python

# .env file

QTEST_API_URL=https://yourcompany.qtestnet.com/api/v3
QTEST_API_TOKEN=your_token_here
QTEST_PROJECT_ID=12345
JIRA/Xray Integration
Step 1: Install Xray Plugin
JIRA → Apps → Find new apps
Search: Xray Test Management
Install and configure
Step 2: Create Test Project

1. Create Project: BANK
2. Issue Types:
   ☑ Test
   ☑ Test Set
   ☑ Test Execution
   ☑ Test Plan

3. Create Custom Fields:
   - Tosca_TestCase_ID
   - Automation_Status
   - Last_Execution_Date
     Step 3: Map Tosca to Xray
     In Tosca TestCase Properties:

- Custom Field: JIRA_Test_Key
- Value: BANK-T-123

This enables bi-directional sync
Troubleshooting
Common Issues
Issue 1: DEX Agent Not Connecting
Symptoms:

- Agent shows as offline in DEX Server
- Tests don't distribute to agents

Solutions:

1. Check network connectivity:
   Test-NetConnection -ComputerName dex-server -Port 8731

2. Verify service is running:
   Get-Service "Tosca DEX Agent"

3. Check firewall rules:

   - Allow inbound: Port 8731 (TCP)
   - Allow outbound: Port 8731 (TCP)

4. Review agent logs:
   C:\ProgramData\TRICENTIS\ToscaDex\Agent\Logs\
   Issue 2: Module Steering Failures
   Symptoms:

- "Control not found" errors
- Tests fail on element identification

Solutions:

1. Use Tosca's "Scan" tool to re-scan the control
2. Add multiple steering parameters (ID, CSS, XPath)
3. Implement WaitOn conditions:

   - WaitOn: Element.Exists
   - Timeout: 30 seconds

4. Enable dynamic identification:
   Module Properties → Enable adaptive identification
   Issue 3: ToscaCI Execution Fails
   Symptoms:

- Pipeline fails at execution step
- Exit code 1 or 2 from ToscaCI.exe

Solutions:

1. Check workspace path is correct
2. Verify execution list exists
3. Ensure proper permissions on results directory

Debug command:
ToscaCI.exe -workspace "path" -executionlist "name" -verbose true
Issue 4: Results Not Publishing to qTest
Symptoms:

- Script runs but no updates in qTest
- API authentication errors

Solutions:

1. Verify API token is valid:
   curl -H "Authorization: Bearer YOUR_TOKEN" \
    https://yourcompany.qtestnet.com/api/v3/projects

2. Check test case ID mapping exists
3. Review integration script logs
4. Validate JSON structure matches expected format
   Support & Resources
   Official Documentation
   Tosca Documentation
   Tosca Best Practices
   DEX Configuration Guide
   Community
   Tricentis Community
   Stack Overflow - Tosca Tag
   Training
   Tricentis University (official certification)
   LinkedIn Learning - Tosca Courses
   Udemy - Tosca Automation Courses
   Next Steps
   After completing setup:

✅ Run smoke test suite to validate configuration
✅ Execute single test case with each DEX agent
✅ Test CI/CD pipeline with sample execution
✅ Verify qTest/JIRA integration
✅ Configure monitoring and alerting
✅ Train team on framework usage
Setup complete! You're now ready to build scalable test automation with Tosca.

For questions or issues, refer to the main README.md or create an issue in the repository.
