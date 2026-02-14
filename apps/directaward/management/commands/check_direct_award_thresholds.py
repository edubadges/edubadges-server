#!/usr/bin/env python
"""
Management command to check for suspicious direct award activity
"""

from directaward.threshold_monitor import Command

if __name__ == '__main__':
    command = Command()
    command.handle()
