#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试依赖库是否可用"""

import sys
print('Python:', sys.version)

try:
    import requests
    print('requests: OK')
except ImportError:
    print('requests: MISSING')

try:
    from bs4 import BeautifulSoup
    print('bs4: OK')
except ImportError:
    print('bs4: MISSING')

try:
    import lxml
    print('lxml: OK')
except ImportError:
    print('lxml: MISSING')
