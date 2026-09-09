# RIMS Reset Guide

## Overview
The RIMS application includes automated reset scripts to quickly restart your application to a clean development or testing state. This is useful when you want to start fresh and have a clear testing ground.

---

## What Gets Reset

When you run the reset script, the following are cleared/recreated:

✓ **Database** - The SQLite database file is deleted and recreated from scratch  
✓ **Database Tables** - All tables are dropped and recreated based on your models  
✓ **Uploaded Files** - All files in the uploads folder are deleted  
✓ **Default Categories** - All 13 default product categories are seeded  
✓ **Admin User** (optional) - A default admin user is created with credentials provided below  

---

## Usage

### Option 1: Using the Shell Script (Recommended for Linux/Mac)

```bash
# Simple reset (development environment, with admin user)
./reset.sh

# Reset production environment
./reset.sh --prod

# Reset without creating admin user
./reset.sh --dev --no-admin

# View help
./reset.sh --help
```

### Option 2: Using Python Directly

```bash
# Simple reset (development environment, with admin user)
python3 reset.py

# Reset production environment
python3 reset.py --prod

# Reset without creating admin user
python3 reset.py --dev --no-admin

# View help
python3 reset.py --help
```

### Option 3: Using Windows Command Line (Windows only)

```cmd
python reset.py
python reset.py --prod
python reset.py --dev --no-admin
```

---

## Default Admin User

When you run the reset script with the `--create-admin` flag (which is the default), a default admin user is created:

- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@rims.local`
- **Role:** Administrator

⚠️ **IMPORTANT:** Change the password after your first login for security!

---

## Step-by-Step Process

When you run the reset script, it performs these steps:

1. **Remove Database** - Deletes the old SQLite database file
2. **Clear Uploads** - Removes all uploaded files from the uploads folder
3. **Recreate Schema** - Creates all database tables from scratch
4. **Seed Categories** - Populates 13 default product categories
5. **Create Admin User** - Creates the default admin account (if enabled)

Each step shows progress with checkmarks (✓) and completion status.

---

## Example Workflows

### Complete Fresh Start for Development

```bash
# Reset everything
./reset.sh

# Then start your app
python run.py
```

### Testing Different Scenarios

```bash
# Reset 1st time - test scenario A
./reset.sh

# Run tests
# ... do your testing ...

# Reset 2nd time - test scenario B with different data
./reset.sh

# Run more tests
```

### Production Reset (Use with Caution)

```bash
# Reset production environment
./reset.sh --prod
```

⚠️ Be very careful with this option - it will delete your production database!

---

## Troubleshooting

### Script returns "Permission Denied"

On Linux/Mac, make sure the script is executable:

```bash
chmod +x reset.sh
```

Then run it again:

```bash
./reset.sh
```

### Database File Still Exists After Reset

This can happen if the instance folder doesn't have write permissions. Check your file permissions:

```bash
ls -la instance/
```

### Script Fails During Execution

Check that:
1. Python 3 is installed: `python3 --version`
2. All dependencies are installed: `pip install -r requirements.txt`
3. You're running from the project root directory

---

## Files Included

- **reset.py** - Python script that performs the actual reset logic
- **reset.sh** - Shell script wrapper (Linux/Mac convenience wrapper)
- **RESET_GUIDE.md** - This guide

---

## Notes

- The reset script only affects your local development/test environment (unless you use `--prod`)
- Your source code is never modified
- Configuration files remain unchanged
- You can safely run the reset script multiple times
- The script creates backups of nothing - if you need to preserve data, back it up before resetting

---

## Next Steps After Reset

1. Run the reset script
2. Start your application: `python run.py`
3. Navigate to http://localhost:5000
4. Login with admin/admin123
5. Change the admin password immediately
6. Start testing/developing

---

For more information, see the main [QUICKSTART.md](QUICKSTART.md) or [README.md](README.md).
