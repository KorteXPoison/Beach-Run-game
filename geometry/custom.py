import numpy as np
from OpenGL.GL import *
from core.attribute import Attribute
from geometry.geometry import Geometry

class CustomGeometry(Geometry):
    def __init__(self, vertices, uvs):
        super().__init__()
        self.add_attribute("vec3", "vertexPosition", vertices)
        self.add_attribute("vec2", "vertexUV", uvs)
