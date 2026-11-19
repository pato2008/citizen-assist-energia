"""Atalho para rodar o assistente: python assistente_energia.py [--demo | --json ...]"""
import sys

from energia.assistente import main

if __name__ == "__main__":
    sys.exit(main())
