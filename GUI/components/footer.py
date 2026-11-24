'''
footer.py
Description: footer to home page
Author: Kobe Prior
Date Last Modified: Nov 24, 2026
'''
from nicegui import ui, background_tasks
def footer():
    with ui.footer().classes('bg-gray-100 text-gray-600 py-3 px-6 border-t border-gray-200 justify-center items-center gap-6'):
        ui.label('© 2026 Kobe Prior').classes('text-sm')
        ui.label('|').classes('text-gray-300')
        ui.link('Website', 'https://kobeprior.com', new_tab=True) \
            .classes('text-sm text-blue-600 hover:underline no-underline')
        ui.label('|').classes('text-gray-300')
        ui.link('LinkedIn', 'https://www.linkedin.com/in/kobeprior/', new_tab=True) \
            .classes('text-sm text-blue-600 hover:underline no-underline')

