# QeMLflow Renaming Implementation Plan

## 🎯 **Safe Renaming Strategy for ChemML → QeMLflow**

### **Current Analysis**
- **94 Python files** in src/ directory need renaming
- **226 markdown files** with potential references
- **134+ text references** to "chemml" across the codebase
- **51+ import statements** with chemml references
- **Critical files**: setup.py, pyproject.toml, __init__.py files

---

## 🚧 **Phase 1: Pre-Rename Preparation & Safety**

### **Step 1.1: Create Comprehensive Backup**
```bash
# Full repository backup
cd /Users/sanjeev/Downloads/Repos/
cp -r ChemML ChemML_BACKUP_BEFORE_QEMLFLOW_RENAME_$(date +%Y%m%d_%H%M%S)

# Git safety checkpoint
cd ChemML
git add . && git commit -m "CHECKPOINT: Before QeMLflow renaming - safe restore point"
git tag pre-qemlflow-rename
```

### **Step 1.2: Verify Clean Git State**
```bash
git status  # Should be clean
git log --oneline -3  # Verify recent commits
```

### **Step 1.3: Create Renaming Scripts (Safe & Reversible)**
We'll create automated scripts that can be reversed if needed.

---

## 🔧 **Phase 2: Core Infrastructure Renaming**

### **Step 2.1: Package Structure Transformation**
```bash
# 1. Rename main source directory
cd src/
mv chemml qemlflow

# 2. Update all internal __init__.py files
find qemlflow/ -name "__init__.py" -exec sed -i '' 's/chemml/qemlflow/g' {} \;
```

### **Step 2.2: Configuration Files Update**
```python
# setup.py changes
name="ChemML" → name="QeMLflow"
packages=find_packages(where="src") # Will auto-detect qemlflow/

# pyproject.toml changes  
name = "chemml" → name = "qemlflow"
description = "Quantum-Enhanced Molecular Machine Learning Framework"
keywords = ["quantum-computing", "machine-learning", "drug-discovery", "molecular-modeling"]
```

### **Step 2.3: Import Statement Updates**
```bash
# Safe pattern replacement for import statements
find . -name "*.py" -exec sed -i '' 's/import chemml/import qemlflow/g' {} \;
find . -name "*.py" -exec sed -i '' 's/from chemml/from qemlflow/g' {} \;
find . -name "*.py" -exec sed -i '' 's/chemml\./qemlflow\./g' {} \;
```

---

## 🧪 **Phase 3: Validation & Testing**

### **Step 3.1: Import Validation**
```python
# Test script: test_qemlflow_imports.py
try:
    import qemlflow
    print("✅ Main import successful")
    
    from qemlflow.core import models, data_processing
    print("✅ Core modules import successful")
    
    from qemlflow.research import drug_discovery
    print("✅ Research modules import successful")
    
    from qemlflow.integrations import core
    print("✅ Integration modules import successful")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

### **Step 3.2: Functionality Testing**
```bash
# Run existing test suite with new name
python -m pytest tests/ -v
python tools/testing/functional_validation.py
```

---

## 📝 **Phase 4: Documentation & Content Updates**

### **Step 4.1: Markdown Files Update**
```bash
# Update documentation references
find . -name "*.md" -exec sed -i '' 's/ChemML/QeMLflow/g' {} \;
find . -name "*.md" -exec sed -i '' 's/chemml/qemlflow/g' {} \;

# Update specific content patterns
find . -name "*.md" -exec sed -i '' 's/Machine Learning for Chemistry/Quantum-Enhanced Machine Learning Workflows/g' {} \;
```

### **Step 4.2: README and Key Documents**
```markdown
# README.md
# QeMLflow: Quantum-Enhanced Machine Learning Workflows

QeMLflow is a production-ready framework that combines quantum computing, 
machine learning, and chemical workflow processing for molecular modeling 
and drug discovery.

## Quick Start
```python
import qemlflow
from qemlflow.core import models, data_processing
from qemlflow.quantum import QuantumProcessor
```

### **Step 4.3: Comments and Docstrings**
```bash
# Update code comments and docstrings
find src/ -name "*.py" -exec sed -i '' 's/ChemML/QeMLflow/g' {} \;
find src/ -name "*.py" -exec sed -i '' 's/Chemical ML/Quantum-Enhanced ML/g' {} \;
```

---

## 🏗️ **Phase 5: Repository & Infrastructure**

### **Step 5.1: GitHub Repository Renaming**
```bash
# This will be done through GitHub web interface:
# 1. Go to repository Settings
# 2. Repository name: ChemML → QeMLflow  
# 3. Update repository URL references
```

### **Step 5.2: Development Environment Updates**
```bash
# Update virtual environment
cd ..
mv chemml_env qemlflow_env

# Update IDE settings and configurations
# Update Docker configurations if any
# Update CI/CD pipeline references
```

---

## 🔒 **Phase 6: Safety Validation & Rollback Plan**

### **Step 6.1: Comprehensive Testing**
```bash
# Full validation suite
python tools/testing/comprehensive_functionality_tests.py
python tools/testing/performance_tests.py
python tools/testing/final_integration_tests.py

# Import verification
python -c "import qemlflow; print('✅ QeMLflow import successful')"
```

### **Step 6.2: Rollback Plan (If Needed)**
```bash
# Emergency rollback procedure
git reset --hard pre-qemlflow-rename
# OR restore from backup
rm -rf /Users/sanjeev/Downloads/Repos/ChemML
mv /Users/sanjeev/Downloads/Repos/ChemML_BACKUP_* /Users/sanjeev/Downloads/Repos/ChemML
```

---

## 🚀 **Phase 7: Final Publication**

### **Step 7.1: Git Commit & Push**
```bash
git add .
git commit -m "MAJOR: Rename ChemML to QeMLflow - Quantum-Enhanced ML Framework

Complete framework rebranding from ChemML to QeMLflow:
- Renamed src/chemml/ to src/qemlflow/
- Updated all import statements and module references
- Updated package configuration (setup.py, pyproject.toml)
- Updated documentation and README files
- Maintained full backward compatibility in functionality
- Added quantum-enhanced branding and positioning
- All tests passing with new naming structure

Breaking changes:
- Import statements: 'import chemml' → 'import qemlflow'
- Package name: 'chemml' → 'qemlflow'
- Repository name: ChemML → QeMLflow

Framework functionality remains identical - only naming changed."

git push origin main
```

### **Step 7.2: PyPI Package Publication**
```bash
# Build new package
python -m build
python -m twine upload dist/qemlflow-*
```

---

## 📋 **Automated Renaming Script**

### **Complete Automation Script: `rename_to_qemlflow.py`**

```python
#!/usr/bin/env python3
"""
Safe automated renaming script: ChemML → QeMLflow
"""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def create_backup():
    """Create comprehensive backup before renaming."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"ChemML_BACKUP_BEFORE_QEMLFLOW_{timestamp}"
    parent_dir = Path.cwd().parent
    backup_path = parent_dir / backup_name
    
    print(f"🔄 Creating backup: {backup_path}")
    shutil.copytree(".", backup_path)
    print("✅ Backup created successfully")
    return backup_path

def git_checkpoint():
    """Create git checkpoint for safety."""
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "CHECKPOINT: Before QeMLflow renaming"])
    subprocess.run(["git", "tag", "pre-qemlflow-rename"])
    print("✅ Git checkpoint created")

def rename_directories():
    """Rename main directories."""
    if Path("src/chemml").exists():
        Path("src/chemml").rename("src/qemlflow")
        print("✅ Renamed src/chemml/ → src/qemlflow/")

def update_files():
    """Update all file contents."""
    replacements = [
        ("chemml", "qemlflow"),
        ("ChemML", "QeMLflow"),
        ("Machine Learning for Chemistry", "Quantum-Enhanced Machine Learning Workflows"),
    ]
    
    file_patterns = ["*.py", "*.md", "*.txt", "*.yml", "*.yaml", "*.toml"]
    
    for pattern in file_patterns:
        for file_path in Path(".").rglob(pattern):
            if file_path.is_file() and ".git" not in str(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    modified = False
                    
                    for old, new in replacements:
                        if old in content:
                            content = content.replace(old, new)
                            modified = True
                    
                    if modified:
                        file_path.write_text(content, encoding='utf-8')
                        print(f"✅ Updated: {file_path}")
                        
                except Exception as e:
                    print(f"⚠️ Warning: Could not update {file_path}: {e}")

def validate_imports():
    """Validate that imports work after renaming."""
    try:
        import sys
        sys.path.insert(0, "src")
        import qemlflow
        print("✅ QeMLflow import validation successful")
        return True
    except ImportError as e:
        print(f"❌ Import validation failed: {e}")
        return False

def main():
    """Execute complete renaming process."""
    print("🚀 Starting ChemML → QeMLflow renaming process")
    
    # Safety first
    backup_path = create_backup()
    git_checkpoint()
    
    try:
        # Core renaming
        rename_directories()
        update_files()
        
        # Validation
        if validate_imports():
            print("🎉 Renaming completed successfully!")
            print("🔍 Please run comprehensive tests to verify everything works")
        else:
            print("❌ Validation failed - consider rollback")
            
    except Exception as e:
        print(f"❌ Error during renaming: {e}")
        print(f"💡 Backup available at: {backup_path}")
        print("💡 Git rollback: git reset --hard pre-qemlflow-rename")

if __name__ == "__main__":
    main()
```

---

## ⚡ **Quick Execution Summary**

### **One-Command Execution:**
```bash
# Create and run the automated script
python3 scripts/rename_to_qemlflow.py

# Or manual step-by-step (safer):
# 1. Create backup
# 2. Git checkpoint  
# 3. Rename directories
# 4. Update file contents
# 5. Test imports
# 6. Run test suite
# 7. Commit and push
```

### **Estimated Timeline:**
- **Phase 1-2 (Prep + Core)**: 30 minutes
- **Phase 3-4 (Testing + Docs)**: 45 minutes  
- **Phase 5-7 (Infrastructure + Publish)**: 30 minutes
- **Total**: ~2 hours for complete safe renaming

### **Risk Mitigation:**
- ✅ **Full backup before starting**
- ✅ **Git checkpoint with rollback tag**
- ✅ **Automated validation at each step**
- ✅ **Comprehensive test suite verification**
- ✅ **Reversible process at every stage**

This plan ensures a **safe, systematic, and reversible** transition from ChemML to QeMLflow while maintaining all functionality and providing multiple rollback options if needed.
