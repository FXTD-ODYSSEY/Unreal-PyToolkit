# -*- coding: utf-8 -*-
"""
copy asset reference to clipboard 
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = 'timmyliang'
__email__ = '820472580@qq.com'
__date__ = '2021-04-09 09:27:23'

import unreal
from Qt import QtWidgets

util_lib = unreal.EditorUtilityLibrary
def main():

    path_list = [asset.get_path_name() for asset in util_lib.get_selected_assets()]
    path = "\n".join(path_list)
    
    cb = QtWidgets.QApplication.clipboard()
    cb.clear(mode=cb.Clipboard)
    cb.setText(path, mode=cb.Clipboard)

if __name__ == '__main__':
    main()
