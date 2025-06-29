# Facebook Automation Tool - Project Overview

## Description

This project is a robust automation tool for managing multiple Facebook accounts and automating post interactions (like, comment) using Playwright.  
It is designed for non-interactive, configuration-driven automation with session recovery, logging, and human-like behavior simulation.

---

## Features

- Session state recovery (resume after interruption)
- Comprehensive logging and reporting (CSV and log files)
- Human-like behavior simulation (random delays, user agents)
- Rate limiting and retry mechanisms
- Separate login and post processing phases
- Easy configuration via JSON files

---

## Directory Structure

```
.
├── .gitignore
├── README.MD
├── PROJECT_OVERVIEW.md
├── requirements.txt
└── facebook_automation_tool/
    ├── __init__.py
    ├── account_management.py
    ├── configuration.py
    ├── exceptions.py
    ├── facebook_automation.py
    ├── logging_module.py
    ├── login_handler.py
    ├── main.py
    ├── post_interaction.py
    ├── post_url_management.py
    ├── session_management.py
    ├── utils.py
    ├── data/
    │   ├── accounts.json
    │   ├── automation_config.json
    │   ├── post_urls.json
    │   └── session_state.json
    └── logs/
        ├── activity_log.csv
        └── facebook_automation.log
```

---

## Setup

1. **Clone the repository**  
   ```sh
   https://github.com/MuhammadAizazA/FB_automation.git
   cd FB_automation
   ```

2. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   python -m playwright install
   ```

3. **Edit configuration files**  
   - Add Facebook account IDs and credentials in `accounts.json`
   - Add post URLs in `post_urls.json`
   - (Optional) Adjust settings in `automation_config.json`
## Configuration

- **accounts.json**: List of Facebook account IDs and credentials.
- **post_urls.json**: List of Facebook post URLs to interact with.
- **automation_config.json**: Automation settings (delays, timeouts, etc.).

Edit these files in `facebook_automation_tool/data/` before running the tool.

---

## Usage

1. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    python -m playwright install
    ```

2. **Configure accounts and posts**
    - Add accounts to `facebook_automation_tool/data/accounts.json`
    - Add post URLs to `facebook_automation_tool/data/post_urls.json`
    - Adjust settings in `facebook_automation_tool/data/automation_config.json` if needed

3. **Run the tool**
    ```sh
    cd facebook_automation_tool
    python -m main
    ```

---

## Output

- **Logs:** `facebook_automation_tool/logs/`
- **Session State:** `facebook_automation_tool/data/session_state.json`
- **Activity Log:** `facebook_automation_tool/logs/activity_log.csv`

---

## Notes

- Uses Playwright for browser automation (Chromium).
- Each account uses a separate browser profile for session isolation.
- Handles Facebook security challenges with user prompts.
- Designed for educational and research purposes.  

---
