#!/usr/bin/env python3
"""Test immediate unbuffered output"""
import sys
import time

print("Starting test...", flush=True)
time.sleep(2)
print("After 2 seconds - you should see this immediately", flush=True)
time.sleep(2) 
print("After 4 seconds - if this appears all at once, output is buffered", flush=True)
