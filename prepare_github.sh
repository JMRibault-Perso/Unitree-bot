#!/bin/bash

# GitHub Repository Setup Script
# Prepares the Unitree-bot project for GitHub upload

echo "🤖 Preparing Unitree-bot project for GitHub..."

# Create clean project directory
GITHUB_DIR="/root/G1/unitree-bot-github"
mkdir -p "$GITHUB_DIR"

echo "📁 Creating clean project structure..."

# Core application files
echo "📋 Copying core application..."
cp -r g1_app "$GITHUB_DIR/"

# Essential configuration files
echo "⚙️ Copying configuration files..."
cp cyclonedx.xml "$GITHUB_DIR/"
cp CMakeLists.txt "$GITHUB_DIR/"

# Documentation
echo "📚 Copying documentation..."
cp README_GITHUB.md "$GITHUB_DIR/README.md"
cp BOOT_SEQUENCE_ANALYSIS.md "$GITHUB_DIR/"
cp DISCOVERY_SUMMARY.md "$GITHUB_DIR/"
cp FSM_STATES_REFERENCE.md "$GITHUB_DIR/"
cp G1_AIR_CONTROL_GUIDE.md "$GITHUB_DIR/"
cp QUICK_START.md "$GITHUB_DIR/"

# Essential libraries and headers (without build artifacts)
echo "🏗️ Copying SDK components..."
cp -r include "$GITHUB_DIR/"
cp -r thirdparty "$GITHUB_DIR/"

# Select useful scripts (not test/debug ones)
echo "🛠️ Copying essential scripts..."
cp diagnose_dds.sh "$GITHUB_DIR/"
cp quick_test.sh "$GITHUB_DIR/"
cp run_web_ui.sh "$GITHUB_DIR/"

# Select example files
echo "💡 Copying examples..."
mkdir -p "$GITHUB_DIR/examples"
cp g1_quick_control.py "$GITHUB_DIR/examples/"
cp quick_connect.py "$GITHUB_DIR/examples/"
cp discover_robot.py "$GITHUB_DIR/examples/"

# Copy cmake files
echo "🔧 Copying build configuration..."
cp -r cmake "$GITHUB_DIR/"

# Git configuration
echo "🔄 Setting up Git configuration..."
cp .gitignore_github "$GITHUB_DIR/.gitignore"
cp LICENSE "$GITHUB_DIR/" 2>/dev/null || echo "# License" > "$GITHUB_DIR/LICENSE"

# Create additional helpful files
echo "📖 Creating additional documentation..."

# Create a quick setup guide
cat > "$GITHUB_DIR/SETUP.md" << 'EOF'
# Quick Setup Guide

## Prerequisites
- Ubuntu/Linux environment (WSL2 supported)
- Python 3.8+
- Root privileges for network operations

## Installation Steps

1. **Install Python dependencies**
   ```bash
   pip3 install fastapi uvicorn websockets zeroconf
   ```

2. **Set environment variables**
   ```bash
   export CYCLONEDX_URI=file://$(pwd)/cyclonedx.xml
   export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
   ```

3. **Start the web interface**
   ```bash
   ./run_web_ui.sh
   ```

4. **Access the interface**
   - Open http://localhost:8000 in your browser
   - Wait for robot discovery
   - Connect to your robot

## Quick Commands
- `./quick_test.sh` - Test robot connection
- `./diagnose_dds.sh` - Network diagnostics  
- `python3 examples/discover_robot.py` - Manual discovery

For detailed documentation, see README.md
EOF

# Create requirements.txt
cat > "$GITHUB_DIR/requirements.txt" << 'EOF'
fastapi>=0.68.0
uvicorn>=0.15.0
websockets>=10.0
zeroconf>=0.39.0
python-multipart>=0.0.5
aiofiles>=0.7.0
EOF

# Create development setup script
cat > "$GITHUB_DIR/setup.sh" << 'EOF'
#!/bin/bash

echo "🤖 Setting up Unitree G1 Control System..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Set up environment
echo "⚙️ Setting up environment variables..."
echo 'export CYCLONEDX_URI=file://$(pwd)/cyclonedx.xml' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH' >> ~/.bashrc

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x *.sh
chmod +x examples/*.py

echo "✅ Setup complete!"
echo "Run './run_web_ui.sh' to start the web interface"
EOF

chmod +x "$GITHUB_DIR/setup.sh"
chmod +x "$GITHUB_DIR"/*.sh

echo "✅ Project prepared in: $GITHUB_DIR"
echo ""
echo "📋 Next steps to create GitHub repository:"
echo "1. Go to https://github.com/JMRibault-Perso"
echo "2. Click 'New repository'"
echo "3. Name: 'Unitree-bot'"
echo "4. Description: 'Web-based control system for Unitree G1 robots'"
echo "5. Choose Public/Private"
echo "6. Don't initialize with README (we have one)"
echo "7. Create repository"
echo ""
echo "📤 Upload commands:"
echo "cd $GITHUB_DIR"
echo "git init"
echo "git add ."
echo "git commit -m 'Initial commit: Unitree G1 Robot Control System'"
echo "git branch -M main"
echo "git remote add origin https://github.com/JMRibault-Perso/Unitree-bot.git"
echo "git push -u origin main"
echo ""
echo "🎉 Your project is ready for GitHub!"