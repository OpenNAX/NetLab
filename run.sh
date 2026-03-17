clear

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment (venv) not found."
    echo "Please run the install script first."
    exit 1
fi

echo "Starting OpenNAX NetLab | v2.0.0"

source venv/bin/activate

python3 netlab.py

deactivate