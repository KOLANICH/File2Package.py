import typing
from pathlib import Path
import re
from collections import defaultdict

import sqlite3
import datrie
from MempipedPath import *
import threading

from .interfaces import *
from .database import File2Package
