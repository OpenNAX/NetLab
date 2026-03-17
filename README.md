## OpenNAX (by NAX Entertainment) | ![Version](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FOpenNAX%2FAPI%2Fmain%2FOpenNAX-NetLab.txt&query=%24.version&label=version&color=blue) NetLab is a Termux-based utility for testing, diagnosing, and logging mobile network connections.

*Termux only*

First, you need to install Termux:API from an appstore like F-Droid

And run the following commands to continue

### One time:
```bash
pkg update && pkg install git -y
git clone https://github.com/OpenNAX/NetLab.git
cd NetLab
```

### One time:
```bash
chmod +x installer.sh
chmod +x run.sh
./installer.sh
```

### Normal run:
```bash
./run.sh
```