---
trigger: always_on
---

# Agent Permissions & Restrictions
- **Strict Restriction:** You are strictly forbidden from performing `read_file` or `write_file` on the `.env` file. Do not attempt to access or modify it.
- **Allowed Exception:** You have full permission to `read_file` and `write_file` the `example.env` file. Use this as your reference for environment variables.
- **Auto-Apply:** You are authorized to apply changes to `example.env` and all other project files (except `.env` and `.venv/`) without asking for manual approval.
- **Venv Protection:** Do not read or write any files inside the `.venv/` directory.