#!/bin/bash

# Import colors and git helpers
source scripts/utils/colors.py
source scripts/utils/git_helpers.py

print_header() {
    echo -e "${BG}${FG}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "            Special CLI Tools Cleanup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

# Ensure we're in the right directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

print_header

# Check for local modifications
if python3 -c "from scripts.utils.git_helpers import print_git_status; has_changes = print_git_status()"; then
    echo -e "${RED}[!] Local modifications detected${NC}"
    echo -e "${YELLOW}Options:${NC}"
    echo "1. Save changes (git add & commit)"
    echo "2. Discard changes (git reset --hard)"
    echo "3. Cancel cleanup"
    
    read -p "Choose an option (1-3): " choice
    
    case $choice in
        1)
            echo -e "${BLUE}[*] Saving changes...${NC}"
            read -p "Enter commit message: " message
            git add .
            git commit -m "$message"
            ;;
        2)
            echo -e "${RED}[!] This will permanently delete all local changes!${NC}"
            read -p "Are you sure? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                git reset --hard
                git clean -fd
            else
                echo -e "${BLUE}Cleanup cancelled${NC}"
                exit 0
            fi
            ;;
        3)
            echo -e "${BLUE}Cleanup cancelled${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Cleanup cancelled${NC}"
            exit 1
            ;;
    esac
fi

# Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${BLUE}[*] Deactivating virtual environment...${NC}"
    deactivate
fi

# Remove venv directory
if [ -d "venv" ]; then
    echo -e "${BLUE}[*] Removing virtual environment...${NC}"
    rm -rf venv
fi

# Remove activation from shell rc files
activate_cmd="source ~/specialCliTools/venv/bin/activate"
for rc in ~/.bashrc ~/.zshrc; do
    if [ -f "$rc" ]; then
        echo -e "${BLUE}[*] Removing activation from ${rc}...${NC}"
        sed -i "\:${activate_cmd}:d" "$rc"
    fi
done

echo -e "${GREEN}[✓] Cleanup complete${NC}"
echo -e "${BLUE}To completely remove the tools, you can now delete the repository:${NC}"
echo "  rm -rf ~/specialCliTools"
