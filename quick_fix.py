#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris Quick Fix Script
----------------------------
แก้ไขทุกอย่างในคำสั่งเดียว
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run command safely"""
    try:
        print(f"🔧 {description or cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            return True
        else:
            print(f"❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def upgrade_python_packages():
    """อัพเกรด Python packages"""
    print("\n🚀 Upgrading Python packages...")
    
    commands = [
        f"{sys.executable} -m pip install --upgrade pip",
        f"{sys.executable} -m pip install --upgrade setuptools wheel",
    ]
    
    for cmd in commands:
        run_command(cmd, "Upgrading pip components")

def install_requirements():
    """ติดตั้ง requirements"""
    print("\n📦 Installing requirements...")
    
    packages = [
        "pygame>=2.5.0",
        "PyYAML>=6.0", 
        "numpy>=1.24.0",
        "SQLAlchemy>=2.0.0",
        "bcrypt>=4.0.0",
        "Pillow>=10.0.0"
    ]
    
    failed = []
    for package in packages:
        cmd = f"{sys.executable} -m pip install {package}"
        if not run_command(cmd, f"Installing {package}"):
            # Try without version
            package_name = package.split(">=")[0]
            cmd_fallback = f"{sys.executable} -m pip install {package_name}"
            if not run_command(cmd_fallback, f"Installing {package_name} (fallback)"):
                failed.append(package_name)
    
    if failed:
        print(f"⚠️  Failed packages: {', '.join(failed)}")
        # Try pygame-ce as fallback
        if "pygame" in failed:
            run_command(f"{sys.executable} -m pip install pygame-ce", "Installing pygame-ce (fallback)")
    
    return len(failed) == 0

def create_missing_files():
    """สร้างไฟล์ที่ขาดหายไป"""
    print("\n📁 Creating missing files...")
    
    files = {
        'graphics/particles.py': '# Empty - see effects.py\npass\n',
        'ui/components.py': '# Empty - see menu.py\npass\n', 
        'ui/hud.py': '# Empty - see game_ui.py\npass\n',
        'utils/helper.py': '# Empty - distributed functions\npass\n'
    }
    
    for file_path, content in files.items():
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n\n{content}')
            print(f"✅ Created: {file_path}")
        except Exception as e:
            print(f"❌ Failed: {file_path} - {e}")

def create_launcher_files():
    """สร้างไฟล์ launcher"""
    print("\n🎮 Creating launcher files...")
    
    # check.py
    check_content = '''#!/usr/bin/env python
import sys, os

def check():
    print("🔍 DENSO Tetris System Check")
    if sys.version_info >= (3, 7):
        print("✅ Python OK")
    else:
        print("❌ Need Python 3.7+")
        return False
        
    modules = ["pygame", "yaml", "numpy"]
    for mod in modules:
        try:
            __import__(mod)
            print(f"✅ {mod} OK")
        except:
            print(f"❌ {mod} missing")
            return False
    
    files = ["main.py", "core/game.py"]
    for file in files:
        if os.path.exists(file):
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            return False
    
    print("\\n🎉 Ready! Run: python main.py")
    return True

if __name__ == "__main__":
    check()
'''
    
    # launch.py
    launch_content = '''#!/usr/bin/env python
import sys, os

try:
    if not os.path.exists('main.py'):
        print("❌ main.py not found!")
        sys.exit(1)
    
    from main import main
    print("🎮 Starting DENSO Tetris...")
    main()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: python quick_fix.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Game error: {e}")
    sys.exit(1)
'''

    files = {
        'check.py': check_content,
        'launch.py': launch_content
    }
    
    for filename, content in files.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Failed: {filename} - {e}")

def fix_core_game_imports():
    """แก้ไข import ใน core/game.py"""
    print("\n🔧 Fixing core/game.py imports...")
    
    try:
        # อ่านไฟล์
        with open('core/game.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # เพิ่ม import ที่ขาดหายไป
        if 'import random' not in content:
            content = content.replace('import time', 'import random\nimport time')
        
        if 'import math' not in content:
            content = content.replace('import time', 'import time\nimport math')
        
        # เขียนไฟล์กลับ
        with open('core/game.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("✅ Fixed core/game.py imports")
        
    except FileNotFoundError:
        print("⚠️  core/game.py not found - using complete version")
    except Exception as e:
        print(f"❌ Error fixing imports: {e}")

def create_requirements_file():
    """สร้างไฟล์ requirements.txt"""
    print("\n📋 Creating requirements.txt...")
    
    requirements = """# DENSO Tetris Requirements
pygame>=2.5.0
PyYAML>=6.0
numpy>=1.24.0
SQLAlchemy>=2.0.0
bcrypt>=4.0.0
Pillow>=10.0.0
"""
    
    try:
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(requirements)
        print("✅ Created requirements.txt")
    except Exception as e:
        print(f"❌ Failed to create requirements.txt: {e}")

def test_imports():
    """ทดสอบ imports"""
    print("\n🧪 Testing imports...")
    
    modules = {
        'pygame': 'Game engine',
        'yaml': 'Configuration',
        'numpy': 'Math operations', 
        'sqlalchemy': 'Database',
        'bcrypt': 'Password hashing',
        'PIL': 'Image processing'
    }
    
    failed = []
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"✅ {module} ({description})")
        except ImportError:
            print(f"❌ {module} ({description}) - MISSING")
            failed.append(module)
    
    return len(failed) == 0

def verify_file_structure():
    """ตรวจสอบโครงสร้างไฟล์"""
    print("\n📂 Verifying file structure...")
    
    required_files = [
        'main.py',
        'core/game.py',
        'core/board.py', 
        'core/tetromino.py',
        'core/constants.py',
        'graphics/effects.py',
        'graphics/renderer.py',
        'ui/menu.py',
        'ui/game_ui.py',
        'audio/sound_manager.py',
        'utils/logger.py'
    ]
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing.append(file_path)
    
    return len(missing) == 0

def main():
    """Main fix process"""
    print("🎮 DENSO Tetris Quick Fix")
    print("=" * 50)
    
    print(f"Python version: {sys.version.split()[0]}")
    
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        print("Download from: https://www.python.org/downloads/")
        return False
    
    # Step 1: Upgrade packages
    upgrade_python_packages()
    
    # Step 2: Install requirements  
    install_success = install_requirements()
    
    # Step 3: Create missing files
    create_missing_files()
    
    # Step 4: Create launcher files
    create_launcher_files()
    
    # Step 5: Fix imports
    fix_core_game_imports()
    
    # Step 6: Create requirements.txt
    create_requirements_file()
    
    # Step 7: Test everything
    print("\n🧪 Final Tests")
    print("-" * 30)
    
    imports_ok = test_imports()
    files_ok = verify_file_structure()
    
    # Summary
    print("\n📋 Summary")
    print("-" * 20)
    print(f"✅ Packages: {'OK' if install_success else 'PARTIAL'}")
    print(f"✅ Imports: {'OK' if imports_ok else 'PARTIAL'}")
    print(f"✅ Files: {'OK' if files_ok else 'PARTIAL'}")
    
    if imports_ok and files_ok:
        print("\n🎉 All systems GO!")
        print("Next steps:")
        print("1. python setup.py     # Full setup (optional)")
        print("2. python check.py     # Quick check")
        print("3. python main.py      # Start game")
        print("4. python launch.py    # Safe start")
        return True
    else:
        print("\n⚠️  Some issues detected")
        print("Try running individual commands:")
        print("- python check.py")
        print("- pip install pygame PyYAML numpy")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)