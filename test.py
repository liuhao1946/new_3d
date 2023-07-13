from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QOpenGLWidget
from PyQt5.QtGui import QOpenGLContext, QOpenGLShader, QOpenGLShaderProgram
from PyQt5.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import math
from PyQt5.QtGui import QSurfaceFormat

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setSamples(4)  # Set the number of samples used for multisampling
        QSurfaceFormat.setDefaultFormat(fmt)  # Apply the format to the widget

        super(OpenGLWidget, self).__init__(parent)
        self.angle = 0
        self.x = 0
        self.y = 0
        self.z = 1

    def initializeGL(self):
        glEnable(GL_MULTISAMPLE)  # Enable multisampling
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10)
        glRotatef(self.angle, self.x, self.y, self.z)
        self.drawCube(3, 3, 0.3)
        self.update()  # Force window to repaint

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def update_rotation(self, w, x, y, z):
        self.angle, self.x, self.y, self.z = self.quaternion_to_angle_axis(w, x, y, z)

    def quaternion_to_angle_axis(self, w, x, y, z):
        angle = 2 * math.acos(w) * 180.0 / math.pi
        norm = math.sqrt(x * x + y * y + z * z)
        if norm == 0:
            return 0, 1, 0, 0
        return angle, x / norm, y / norm, z / norm

    def drawCube(self, length, width, height):
        half_length = length / 2
        half_width = width / 2
        half_height = height / 2

        glBegin(GL_QUADS)
        glColor3f(1, 0, 0)  # Red
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, -half_width)

        glColor3f(0, 1, 0)  # Green
        glVertex3f(half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)

        glColor3f(0, 0, 1)  # Blue
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)

        glColor3f(1, 1, 0)  # Yellow
        glVertex3f(half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, -half_width)

        glColor3f(1, 0, 1)  # Magenta
        glVertex3f(-half_length, half_height, half_width)
        glVertex3f(-half_length, half_height, -half_width)
        glVertex3f(-half_length, -half_height, -half_width)
        glVertex3f(-half_length, -half_height, half_width)

        glColor3f(0, 1, 1)  # Cyan
        glVertex3f(half_length, half_height, -half_width)
        glVertex3f(half_length, half_height, half_width)
        glVertex3f(half_length, -half_height, half_width)
        glVertex3f(half_length, -half_height, -half_width)
        glEnd()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.opengl = OpenGLWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.opengl)
        self.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_rotation)
        self.timer.start(1000)

        # Set default window size
        self.resize(800, 600)

    def update_rotation(self):
        import random
        w = random.random()
        x = random.random()
        y = random.random()
        z = random.random()
        self.opengl.update_rotation(w, x, y, z)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
