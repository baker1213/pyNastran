from pyNastran.gui.menus.modify_picker_properties import ModifyPickerPropertiesMenu

def on_set_picker_size_menu(self):
    #if not hasattr(self, 'case_keys'):
        #self.log_error('No model has been loaded.')
        #return

    #print('size =', self.element_picker_size)
    size = 10.
    size = self.get_element_picker_size()
    data = {
        'size' : size,
        'dim_max' : self.dim_max,
        #'clicked_ok' : False,
        #'clicked_cancel' : False,
        #'close' : False,
    }
    #print(data)
    if not self._picker_window_shown:
        self._picker_window = ModifyPickerPropertiesMenu(data, win_parent=self)
        self._picker_window.show()
        self._picker_window_shown = True
        self._picker_window.exec_()
    else:
        self._picker_window.activateWindow()

    if 'close' not in data:
        self._picker_window.activateWindow()
        return

    if data['close']:
        self._picker_window_shown = False
        del self._picker_window
    else:
        self._picker_window.activateWindow()
