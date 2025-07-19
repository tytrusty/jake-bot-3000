#!/usr/bin/env python3
"""
Buy Iron Bot Example

This example demonstrates how to use the BuyIronBot to automate
buying iron ore from a vendor and depositing it in a bank.
"""

import sys
import os
from jake.buy_iron_script import BuyIronBot

def main():
    """Run the buy iron bot example"""
    
    # Configuration file path
    config_file = "buy_iron_config.json"
    
    print("Buy Iron Bot Example")
    print("=" * 50)
    print("This bot will:")
    print("1. Click on ladder to climb down")
    print("2. Wait for specified time")
    print("3. Move towards vendor (500px below center with random left/right)")
    print("4. Click on vendor (target color)")
    print("5. Buy iron ore (click in buy box)")
    print("6. Deposit in bank (target color)")
    print("7. Repeat from step 1")
    print("=" * 50)
    print()
    
    try:
        # Initialize the bot
        bot = BuyIronBot(config_file)
        
        # Run the bot (you can specify max_cycles to limit the number of cycles)
        # For example: bot.run(max_cycles=5) to run only 5 cycles
        bot.run()
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. The configuration file 'buy_iron_config.json' exists")
        print("2. RuneScape/RuneLite is running")
        print("3. The window title contains 'RuneLite'")
        print("4. You have the required permissions to capture screenshots")

if __name__ == "__main__":
    main() 