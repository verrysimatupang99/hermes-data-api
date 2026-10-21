"""Hermes Data API — read-only untuk data Crypto & Forex.

Didesain sebagai lapisan baca-saja di atas modul yang sudah dipakai pipeline
live (mexc_feed, play_scan, fx_scan, dst). TIDAK menulis file, TIDAK eksekusi
order, TIDAK menyentuh state trading.
"""
__version__ = "1.0.0"
