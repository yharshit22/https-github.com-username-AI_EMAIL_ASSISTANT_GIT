# VS Code Setup Guide for AI Email Assistant

This guide provides step-by-step instructions for setting up and running the AI Email Assistant project in Visual Studio Code.

## 📋 Prerequisites

Before starting, ensure you have:
- Visual Studio Code installed
- Python 3.9 or higher installed
- Git installed
- Basic familiarity with terminal/command prompt

## 🛠 Step-by-Step VS Code Setup

### Step 1: Create Project Folder

1. **Open VS Code**
   - Launch Visual Studio Code
   - If you see a welcome screen, click "Open Folder"

2. **Create New Folder**
   ```bash
   # Windows (in PowerShell or Command Prompt)
   mkdir C:\Users\YourUsername\Documents\ai_email_assistant
   
   # Linux/Mac (in Terminal)
   mkdir ~/ai_email_assistant
   ```

3. **Open Folder in VS Code**
   - Go to `File` → `Open Folder`
   - Navigate to the folder you just created
   - Click "Select Folder"

### Step 2: Create Virtual Environment

1. **Open Terminal in VS Code**
   - Use shortcut `` Ctrl+` `` (backtick) or
   - Go to `Terminal` → `New Terminal`

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   
   # Linux/Mac
   python3 -m venv venv
   ```

3. **Activate Virtual Environment**
   ```bash
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   
   # Windows (Command Prompt)
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

   💡 **Note**: If you get an execution policy error on Windows PowerShell, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Step 3: Create Project Files

1. **Create Project Structure**
   - Right-click in Explorer panel
   - Create folders: `app`, `migrations`, `logs`
   - Inside `app`, create: `auth`, `main`, `api`, `static`, `templates`
   - Inside `static`, create: `css`, `js`, `img`
   - Inside `templates`, create: `auth`, `main`, `partials`

2. **Create Files**
   - Right-click and create new files
   - Copy the content from the generated files above
   - Save each file with proper naming

### Step 4: Install Dependencies

1. **Create requirements.txt**
   - Create new file `requirements.txt`
   - Copy the dependencies list from above

2. **Install Python Packages**
   ```bash
   # Ensure virtual environment is activated
   pip install -r requirements.txt
   ```

   💡 **Tip**: If you get SSL errors, try:
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt
   ```

### Step 5: Environment Configuration

1. **Create .env File**
   - Create new file `.env` in project root
   - Copy content from `.env.example` above
   - Customize with your settings

2. **Important Configuration**
   ```env
   # Minimum required for basic operation
   SECRET_KEY=your-development-secret-key
   IMAP_USERNAME=your-email@gmail.com
   IMAP_PASSWORD=your-app-password
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

### Step 6: Database Setup

1. **Initialize Database**
   ```bash
   # Initialize migration repository
   flask db init
   
   # Create first migration
   flask db migrate -m "Initial migration"
   
   # Apply migration
   flask db upgrade
   ```

2. **Verify Database Creation**
   - Check that `email_assistant.db` file is created
   - No errors should appear in terminal

### Step 7: VS Code Configuration

1. **Install Recommended Extensions**
   - Python (Microsoft)
   - Flask Snippets (cstrap)
   - HTML CSS Support (ecmel)
   - Bootstrap 5 & Font Awesome (Hrishikesh Kale)
   - SQLite Viewer (alexcvzz)

2. **Configure Python Interpreter**
   - Press `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose the virtual environment interpreter
   - Path should be like: `./venv/Scripts/python.exe` (Windows) or `./venv/bin/python` (Linux/Mac)

3. **Create VS Code Settings**
   - Create `.vscode/settings.json`:
   ```json
   {
       "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
       "python.linting.enabled": true,
       "python.linting.pylintEnabled": true,
       "python.formatting.provider": "black",
       "files.associations": {
           "*.html": "html"
       },
       "emmet.includeLanguages": {
           "jinja-html": "html"
       }
   }
   ```

### Step 8: Run the Application

1. **Start Development Server**
   ```bash
   python run.py
   ```

2. **Expected Output**
   ```
   ============================================================
   AI Email Assistant - Development Server
   ============================================================
   Environment: development
   Debug Mode: True
   Database: sqlite:///email_assistant.db
   ============================================================
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```

3. **Open in Browser**
   - Click the link in terminal or
   - Press `Ctrl+Click` on the URL

## 🎯 VS Code Tips and Tricks

### Useful Shortcuts
- `` Ctrl+` `` - Toggle terminal
- `Ctrl+P` - Quick file open
- `Ctrl+Shift+P` - Command palette
- `F5` - Start debugging
- `Ctrl+F5` - Run without debugging

### Debugging Setup

1. **Create Debug Configuration**
   - Go to Run and Debug panel (Ctrl+Shift+D)
   - Click "create a launch.json file"
   - Choose "Flask"

2. **Configure launch.json**
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Python: Flask",
               "type": "python",
               "request": "launch",
               "module": "flask",
               "env": {
                   "FLASK_APP": "run.py",
                   "FLASK_ENV": "development"
               },
               "args": ["run", "--debug", "--port", "5000"],
               "jinja": true
           }
       ]
   }
   ```

### Code Navigation
- `F12` - Go to definition
- `Ctrl+Click` - Go to definition
- `Ctrl+Shift+O` - Go to symbol
- `Ctrl+P` - Search files by name

### Python-Specific Features
- **Auto-completion**: IntelliSense for Python
- **Linting**: Real-time error checking
- **Formatting**: Auto-format with Black
- **Virtual Environment**: Automatic activation

## 🔧 Troubleshooting Common Issues

### Issue 1: "Python not found"
**Solution**: 
- Install Python from python.org
- Restart VS Code
- Check Python path in settings

### Issue 2: "venv not activating"
**Solution**:
- Open new terminal after creating venv
- Check PowerShell execution policy on Windows
- Try manual activation command

### Issue 3: "Module not found" errors
**Solution**:
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python interpreter setting

### Issue 4: "Port 5000 already in use"
**Solution**:
- Change port: `python run.py --port 5001`
- Kill existing process:
  ```bash
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  
  # Linux/Mac
  lsof -ti:5000 | xargs kill -9
  ```

### Issue 5: Database errors
**Solution**:
- Delete `email_assistant.db` and recreate
- Run migrations again: `flask db upgrade`
- Check database permissions

## 📁 Recommended VS Code Extensions

### Essential Extensions
1. **Python** - Microsoft
   - Python language support
   - Debugging, linting, formatting

2. **Flask Snippets** - cstrap
   - Flask code snippets
   - Jinja2 template support

3. **HTML CSS Support** - ecmel
   - CSS class completion
   - HTML tag support

4. **Bootstrap 5** - Hrishikesh Kale
   - Bootstrap code snippets
   - Icon support

5. **SQLite Viewer** - alexcvzz
   - View database files
   - Run SQL queries

### Optional Extensions
- **GitLens** - Eric Amodio
- **Docker** - Microsoft
- **Live Server** - Ritwick Dey
- **Bracket Pair Colorizer** - CoenraadS

## 🚀 Advanced Configuration

### Custom Keybindings
Add to `keybindings.json`:
```json
[
    {
        "key": "ctrl+shift+r",
        "command": "workbench.action.terminal.sendSequence",
        "args": {"text": "python run.py\u000D"}
    }
]
```

### Snippets
Create custom snippets in `.vscode/python.json`:
```json
{
    "Flask Route": {
        "prefix": "froute",
        "body": [
            "@app.route('${1:/path}')",
            "def ${2:function_name}():",
            "    ${3:pass}",
            ""
        ]
    }
}
```

### Workspace Settings
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "files.associations": {
        "*.html": "html"
    },
    "emmet.includeLanguages": {
        "jinja-html": "html"
    },
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "python.linting.pylintArgs": [
        "--load-plugins",
        "pylint_flask"
    ]
}
```

## 📝 Development Workflow

### 1. Code Changes
- Edit files in VS Code
- Use auto-completion and linting
- Format code with Black (Shift+Alt+F)

### 2. Testing Changes
- Save files (auto-reload in debug mode)
- Check browser for changes
- Review terminal for errors

### 3. Debugging
- Set breakpoints (F9)
- Start debugging (F5)
- Use debug console
- Step through code (F10/F11)

### 4. Version Control
- Use Source Control panel
- Stage changes
- Commit with messages
- Push to repository

## 🎨 Customization

### Theme
- Use dark theme for better Python development
- Install custom icon themes
- Configure color scheme

### Layout
- Customize sidebar panels
- Arrange terminal and editor
- Use split views for multiple files

### Productivity
- Use multiple cursors (Alt+Click)
- Leverage find and replace
- Use code folding

## 📚 Additional Resources

### Documentation
- [VS Code Python Guide](https://code.visualstudio.com/docs/python/python-tutorial)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)

### Tutorials
- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)
- [Flask Tutorial](https://flask.palletsprojects.com/en/2.3.x/tutorial/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

### Community
- [VS Code Python Extension](https://github.com/microsoft/vscode-python)
- [Flask Community](https://flask.palletsprojects.com/community/)

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the terminal** for error messages
2. **Review this guide** for common solutions
3. **Search online** for specific error messages
4. **Create an issue** in the repository

Happy coding! 🎉