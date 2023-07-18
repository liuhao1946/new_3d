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
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -12)
        glRotatef(self.angle, self.x, self.y, self.z)

        self.drawCube(3, 3, 0.5)
        self.drawAxes(3, 2)
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

    def normalize_rgb(self, red, green, blue):
        """
        Normalize RGB colors to a [0, 1] scale for OpenGL.

        :param red: Red component of the color (0-255).
        :param green: Green component of the color (0-255).
        :param blue: Blue component of the color (0-255).
        :return: Tuple of (red, green, blue) normalized to [0, 1].
        """

        return red / 255.0, green / 255.0, blue / 255.0

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

        r, g, b = self.normalize_rgb(0xee, 0x63, 0x63)
        glColor3f(r, g, b)  # Blue
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

    def drawAxes(self, axisLength, lineWidth):
        '''
        Draw 3D axes
        axisLength - length of the axes
        arrowSize - size of the arrow heads
        lineWidth - width of the axes lines
        '''
        arrowSize = 0.3

        # 开启线条抗锯齿
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # Set the line width
        glLineWidth(lineWidth)

        # Draw the X axis in red
        glColor3f(1, 0, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(axisLength, 0, 0)
        glEnd()
        self.drawArrowHead(axisLength, 0, 0, arrowSize, 1, 0, 0)
        self.renderText3D(axisLength + 0.2, 0, 0, "X")  # 添加这一行

        # Draw the Y axis in green
        glColor3f(0, 1, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axisLength, 0)
        glEnd()
        self.drawArrowHead(0, axisLength, 0, arrowSize, 0, 1, 0)
        self.renderText3D(0, axisLength + 0.2, 0, "Y")  # 添加这一行

        # Draw the Z axis in blue
        glColor3f(0, 0, 1)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axisLength)
        glEnd()
        self.drawArrowHead(0, 0, axisLength, arrowSize, 0, 0, 1)
        self.renderText3D(0, 0, axisLength + 0.2, "Z")  # 添加这一行

        glDisable(GL_LINE_SMOOTH)

    def drawArrowHead(self, x, y, z, size, dx, dy, dz):
        '''
        Draw an arrow head
        x, y, z - position of the arrow head
        size - size of the arrow head
        dx, dy, dz - direction of the arrow
        '''

        # The arrow head is a set of lines that extend from the end of the axis
        glBegin(GL_LINES)

        if dx:
            # For X-axis, arrow head is in YZ plane
            glVertex3f(x-size, y + size, z)
            glVertex3f(x, y, z)
            glVertex3f(x-size, y - size, z)
            glVertex3f(x, y, z)
        elif dy:
            # For Y-axis, arrow head is in XZ plane
            glVertex3f(x + size, y - size, z)
            glVertex3f(x, y, z)
            glVertex3f(x - size, y - size, z)
            glVertex3f(x, y, z)
        elif dz:
            # For Z-axis, arrow head is in XY plane
            glVertex3f(x + size, y, z - size)
            glVertex3f(x, y, z)
            glVertex3f(x - size, y, z - size)
            glVertex3f(x, y, z)

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
