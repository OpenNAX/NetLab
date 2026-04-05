clear
echo "[*] OpenNAX NetLab · v3.0.0"
echo "Starting download of required packages..."

echo "[+] Installing Termux-API..."
pkg install termux-api -y > /dev/null 2>&1

echo "[+] Installing Termux-API Battery and Telephone Status..."
pkg install termux-telephony-deviceinfo -y > /dev/null 2>&1
pkg install termux-battery-status -y > /dev/null 2>&1

echo "[+] Installing Python3..."
pkg install python3 -y > /dev/null 2>&1

echo "[+] Installing Curl..."
pkg install curl -y > /dev/null 2>&1

echo "-----------------------------------------------------"
echo "Installation complete!"
echo "From now, you can now run it by using the run.sh script."
echo "-----------------------------------------------------"
