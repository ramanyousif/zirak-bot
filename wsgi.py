# -*- coding: utf-8 -*-
"""
WSGI configuration for PythonAnywhere
ئەم فایلە لە PythonAnywhere بەکار دەبرێت بۆ بەڕێکردنی Flask App
"""

import sys
import os

# پەیوەندی لەگەڵ فۆڵدەری بووتەکە
project_home = '/home/ramanyousif2002/zirak-bot'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# PythonAnywhere proxy
os.environ["HTTP_PROXY"] = "http://proxy.server:3128"
os.environ["HTTPS_PROXY"] = "http://proxy.server:3128"
os.environ["http_proxy"] = "http://proxy.server:3128"
os.environ["https_proxy"] = "http://proxy.server:3128"

from flask_app import app as application
