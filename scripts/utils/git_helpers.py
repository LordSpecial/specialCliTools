#!/usr/bin/env python3
import subprocess
from typing import Tuple, List
from .colors import Colors

def get_git_status() -> Tuple[List[str], List[str], List[str]]:
    """
    Get modified, untracked, and staged files in git repository
    Returns: Tuple of (modified_files, untracked_files, staged_files)
    """
    try:
        # Get modified files
        modified = subprocess.check_output(
            ['git', 'ls-files', '--modified'],
            text=True
        ).splitlines()

        # Get untracked files
        untracked = subprocess.check_output(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            text=True
        ).splitlines()

        # Get staged files
        staged = subprocess.check_output(
            ['git', 'diff', '--name-only', '--cached'],
            text=True
        ).splitlines()

        return modified, untracked, staged
    except subprocess.CalledProcessError:
        return [], [], []

def check_git_changes() -> bool:
    """
    Check for any local changes in git repository
    Returns: True if there are changes, False otherwise
    """
    modified, untracked, staged = get_git_status()
    return bool(modified or untracked or staged)

def print_git_status():
    """Print detailed git status with colors"""
    modified, untracked, staged = get_git_status()

    if not any([modified, untracked, staged]):
        print(Colors.success("No local modifications detected"))
        return False

    print(Colors.warning("\nLocal modifications detected:"))

    if modified:
        print(Colors.info("\nModified files:"))
        for file in modified:
            print(f"  {Colors.RED}M{Colors.RESET} {file}")

    if untracked:
        print(Colors.info("\nUntracked files:"))
        for file in untracked:
            print(f"  {Colors.RED}?{Colors.RESET} {file}")

    if staged:
        print(Colors.info("\nStaged files:"))
        for file in staged:
            print(f"  {Colors.GREEN}A{Colors.RESET} {file}")

    return True
