import dearpygui.dearpygui as dpg

from utils.resource_path import get_current_directory
from utils.font_loader import get_font, load_font_dpg


font = get_font(get_current_directory(), 'roboto', italic=False)
load_font_dpg(font)




with dpg.window(label="Data Table Window", no_background=True, tag="fullscreen"):
    with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                    borders_innerH=True, borders_outerH=True, borders_innerV=True,
                    borders_outerV=True, row_background=True, no_host_extendX=True,
                    hideable=True, reorderable=True, sortable=True):
        # Columns and rows will be added here

        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()

        for i in range(5):  # Example: 5 rows
            with dpg.table_row():
                dpg.add_text(f"Строка {i} Данные 1 !@##$$%%^")
                dpg.add_text(f"Строка {i} Данные 2")
                dpg.add_text(f"Строка {i} Данные 3")

dpg.create_viewport(title='DearPyGui Transparent Window', width=800, height=600, decorated=False)
dpg.set_primary_window("fullscreen", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()