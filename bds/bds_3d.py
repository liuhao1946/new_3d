from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QSurfaceFormat, QColor, QFont, QPainter
import pygame

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

        # Initialize the base and current quaternions as unit quaternions
        self.base_quaternion = [1, 0, 0, 0]
        self.current_quaternion = [1, 0, 0, 0]

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)  # 启用混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合函数

        pygame.init()  # 初始化pygame
        self.font = pygame.font.Font(None, 64)  # 创建字体对象
        self.axis_labels = {}  # 用于存储坐标轴标签的纹理
        for label in 'XYZ':
            # 渲染标签并创建纹理
            text_surface = self.font.render(label, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, 'RGBA', True)  # 修改为 'RGBA'
            width, height = text_surface.get_size()
            self.axis_labels[label] = self.create_texture(text_data, width, height)

    def create_texture(self, data, width, height):
        # 创建一个新的OpenGL纹理
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)  # 修改为 GL_RGBA
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return texture

    def draw_text(self, x, y, text, font_size=13):
        # Save the current OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        # Then draw your text over the 3D scene
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont('Arial', font_size))
        painter.drawText(x, y, text)
        painter.end()
        # Restore the saved OpenGL state
        glPopAttrib()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10)
        glRotatef(-90, 1, 0, 0)
        glRotatef(self.angle, self.x, self.y, self.z)
        self.drawAxes(3, 3)  # 在这里调用刚才添加的函数以绘制坐标轴
        self.drawCube(3, 0.5, 3)
        # self.draw_text(10, 20, 'MF02')

        self.update()  # Force window to repaint

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

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

    def normalize_rgb(self, red, green, blue):
        """
        Normalize RGB colors to a [0, 1] scale for OpenGL.

        :param red: Red component of the color (0-255).
        :param green: Green component of the color (0-255).
        :param blue: Blue component of the color (0-255).
        :return: Tuple of (red, green, blue) normalized to [0, 1].
        """

        return red / 255.0, green / 255.0, blue / 255.0

    def rotate_point(self, x, y, z, a, b, c, theta):
        """
        Rotate a point counterclockwise by a given angle around a given origin.

        The angle should be given in degrees.
        """
        theta = math.radians(theta)  # convert theta from degrees to radians
        cost = math.cos(theta)
        sint = math.sin(theta)

        # rotation matrix
        xr = (a * a * (1 - cost) + cost) * x + (a * b * (1 - cost) - c * sint) * y + (a * c * (1 - cost) + b * sint) * z
        yr = (a * b * (1 - cost) + c * sint) * x + (b * b * (1 - cost) + cost) * y + (b * c * (1 - cost) - a * sint) * z
        zr = (a * c * (1 - cost) - b * sint) * x + (b * c * (1 - cost) + a * sint) * y + (c * c * (1 - cost) + cost) * z

        return xr, yr, zr

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

        # Draw the Y axis in green
        glColor3f(0, 1, 0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axisLength, 0)
        glEnd()
        self.drawArrowHead(0, axisLength, 0, arrowSize, 0, 1, 0)

        # Draw the Z axis in blue
        glColor3f(0, 0, 1)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axisLength)
        glEnd()
        self.drawArrowHead(0, 0, axisLength, arrowSize, 0, 0, 1)
        glDisable(GL_LINE_SMOOTH)

        try:
            glEnable(GL_TEXTURE_2D)
            glColor3f(1, 1, 1)  # 使用白色绘制标签
            for label, position, rotation_axis in zip('XYZ', [(axisLength + 0.2, 0, 0), (0, axisLength + 0.2, 0),
                                                              (0, 0, axisLength + 0.2)],
                                                      [(1, 0, 0), (0, 1, 0), (0, 0, 1)]):
                glBindTexture(GL_TEXTURE_2D, self.axis_labels[label])
                glBegin(GL_QUADS)
                for dx, dy in [(-0.1, 0), (0.1, 0), (0.1, 0.2), (-0.1, 0.2)]:
                    if label == 'X':  # Rotate X axis
                        x, y, z = self.rotate_point(position[0] + dx, position[1] + dy, position[2], *rotation_axis, 90)
                    elif label == 'Z':  # Rotate Z axis
                        x, y, z = position[0] + dx, position[1] + dy, position[2] + dx
                        x, y, z = x - position[0], y - position[1], z - position[2]
                        x, y, z = self.rotate_point(x, y, z, *rotation_axis, 90)
                        x, y, z = self.rotate_point(x, y, z, 0, 1, 0, -90)
                        x, y, z = self.rotate_point(x, y, z, 0, 0, 1, 45)  # Added a little more rotation around the Z-axis
                        x, y, z = x + position[0], y + position[1], z + position[2]
                    else:  # Do not rotate Y axis
                        x, y, z = position[0] + dx, position[1] + dy, position[2]
                    glTexCoord2f((dx + 0.1) / 0.2, dy / 0.2)  # Adjust texture coordinates
                    glVertex3f(x, y, z)
                glEnd()
            glDisable(GL_TEXTURE_2D)
        except Exception as e:
            print(e)

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
            glVertex3f(x-size, y, z + size)
            glVertex3f(x, y, z)
            glVertex3f(x-size, y, z - size)
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

    def quaternion_to_euler(self, w, x, y, z):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)

        return roll_x, pitch_y, yaw_z  # in radians

    def radians_to_degrees(self, radians):
        """
        Convert radians to degrees.
        """
        return radians * 180 / math.pi

    def store_current_pose(self):
        """
        Store the current pose as the base quaternion.
        """
        self.base_quaternion = self.quaternion_inverse(self.current_quaternion)

    def rotate_relative_to_base(self, w, x, y, z):
        """
        Rotate the object relative to the stored base pose.
        The input parameters w, x, y, z represent a quaternion.
        """

        # Compute the new rotation as the product of the inverse of the base quaternion and the input quaternion
        new_rotation = self.quaternion_multiply(self.base_quaternion, [w, x, y, z])
        # Update the current quaternion and the rotation parameters for the object
        self.current_quaternion = [w, x, y, z]
        self.angle, self.x, self.y, self.z = self.quaternion_to_angle_axis(*new_rotation)

    def quaternion_inverse(self, q):
        """
        Compute the inverse of a quaternion.
        """
        w, x, y, z = q
        norm = w**2 + x**2 + y**2 + z**2
        return [w/norm, -x/norm, -y/norm, -z/norm]

    def quaternion_multiply(self, q1, q2):
        """
        Compute the product of two quaternions.
        """
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

        # normalize the quaternion
        norm = (w ** 2 + x ** 2 + y ** 2 + z ** 2) ** 0.5
        return [w / norm, x / norm, y / norm, z / norm]
