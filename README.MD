# Facebook Automation Tool

A robust automation tool for managing multiple Facebook accounts and automating post interactions (like, comment) using Playwright.  
**Note:** This tool is **not interactive** at runtime; you configure accounts and posts by editing JSON files before running the tool.

---

## Features

- **Secure credential management** (supports `.env` or prompt)
- **Session state recovery** (resume after interruption)
- **Comprehensive logging and reporting** (CSV and log files)
- **Human-like behavior simulation** (random delays, user agents)
- **Rate limiting and retry mechanisms**
- **Separate login and post processing phases**
- **Easy configuration via JSON files**

---

## How It Works

You manage your automation by **editing configuration files**:

- **accounts.json**: List your Facebook account IDs and credentials here.
- **post_urls.json**: Add the URLs of Facebook posts you want to interact with.
- **automation_config.json**: Adjust automation settings (delays, timeouts, etc.) as needed.

The tool reads these files at startup and processes the accounts and posts as specified. Logs and session state are saved automatically for review and recovery.

---

## Project Structure

```
.
├── .env
├── .gitignore
├── requirements.txt
├── logs/
│   ├── activity_log.csv
│   └── facebook_automation.log
└── facebook_automation_tool/
    ├── account_management.py
    ├── configuration.py
    ├── facebook_automation.py
    ├── logging_module.py
    ├── main.py
    ├── post_url_management.py
    ├── session_management.py
    ├── accounts.json
    ├── automation_config.json
    ├── post_urls.json
    ├── session_state.json
    └── utils.py
```

---

## Setup

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   python -m playwright install
   ```

3. **Configure Facebook Password**  
   - Set your password in `.env` as `FB_PASSWORD="yourpassword"`  
   - Or, you will be prompted at runtime.

4. **Edit configuration files**  
   - Add Facebook account IDs and credentials in `accounts.json`
   - Add post URLs in `post_urls.json`
   - (Optional) Adjust settings in `automation_config.json`

---

## Usage

Run the main script:

```sh
cd facebook_automation_tool
python -m main
```

- The tool will process the accounts and posts as specified in your configuration files.
- Logs and session state are saved in the `logs/` directory and `session_state.json`.

---

## Logs & Output

- **Activity Log:** `logs/activity_log.csv` (CSV of all actions)
- **Main Log:** `logs/facebook_automation.log` (detailed logs)
- **Session State:** `session_state.json` (for recovery/resume)
- **Accounts:** `accounts.json`
- **Post URLs:** `post_urls.json`

---

## Notes

- Uses Playwright for browser automation (Chromium).
- Each account uses a separate browser profile for session isolation.
- Handles Facebook security challenges with user prompts.
- Designed for educational and research purposes.  
  **Do not use for spamming or violating Facebook's terms of service.**

---

## License

MIT License

---

**Author:**  
[Your Name