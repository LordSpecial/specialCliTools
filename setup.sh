#!/bin/bash

# Import colors
source "$(dirname "$0")/scripts/utils/shell_colors.sh"

print_header() {
    echo -e "${BG}${FG}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "            Special CLI Tools Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

print_header

# Create and activate virtual environment
echo -e "${BLUE}[*] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo -e "${BLUE}[*] Installing requirements...${NC}"
total_packages=$(grep -c '^[^#]' requirements.txt)
current=0

while IFS= read -r package; do
    # Skip empty lines and comments
    [[ -z "$package" || "$package" =~ ^#.*$ ]] && continue
    
    ((current++))
    echo -ne "\r\033[K${CYAN}Installing ${package} (${current}/${total_packages})${NC}"
    pip install "$package" >/dev/null 2>&1
done < requirements.txt
echo -e "\n"

# Make tools executable
echo -e "${BLUE}[*] Setting up tools...${NC}"
chmod +x scripts/tools/*.py

# Create symlinks to tools in venv/bin
echo -e "${BLUE}[*] Creating tool symlinks...${NC}"
for tool in scripts/tools/*.py; do
    if [ -f "$tool" ]; then
        toolname=$(basename "$tool")
        ln -sf "../../$tool" "venv/bin/${toolname}"
    fi
done

# Add activation to shell rc files
activate_cmd="source ~/specialCliTools/venv/bin/activate"

for rc in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc" ]; then
        if ! grep -q "$activate_cmd" "$rc"; then
            echo -e "${BLUE}[*] Adding activation to ${rc}...${NC}"
            echo -e "\n# Activate specialCliTools environment\n$activate_cmd" >> "$rc"
        fi
    fi
done

echo -e "${GREEN}[✓] Setup complete!${NC}"
echo -e "${YELLOW}To activate the environment, run:${NC}"
echo -e "  source ~/specialCliTools/venv/bin/activate"
echo -e "${YELLOW}Your CLI tools will be available after activation${NC}"
