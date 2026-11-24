'''
home.py
Description: home page to gui
Author: Kobe Prior
Date Last Modified: Nov 24, 2026
'''
from nicegui import APIRouter
from components.header import header
from components.nav_cards import nav_cards
from components.footer import footer

router = APIRouter()

@router.page('/')
def main_page():
    header()
    nav_cards()
    footer()
