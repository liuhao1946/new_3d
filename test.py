import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtCore import Qt
from OpenGL.GL import *
from PIL import Image
import numpy as np


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skybox_textures = None
        self.lastMouseX = 0
        self.lastMouseY = 0
        self.rotateX = 0
        self.rotateY = 0
        self.skybox_angle = 0
        self.setMouseTracking(True)  # Enable mouse tracking
        self.cube_angle = 0

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        self.load_skybox()

    def mousePressEvent(self, event):
        self.lastMouseX = event.x()
        self.lastMouseY = event.y()

    def mouseMoveEvent(self, event):
        deltaX = event.x() - self.lastMouseX
        deltaY = event.y() - self.lastMouseY
        self.rotateX += deltaY
        self.rotateY += deltaX
        self.lastMouseX = event.x()
        self.lastMouseY = event.y()
        self.update()

    def draw_cube(self):
        # 立方体的大小
        size = 1.0

        # 定义立方体的6个面的顶点
        vertices = [
            [size, size, size], [size, size, -size], [size, -size, -size], [size, -size, size],  # 右侧面
            [-size, size, -size], [-size, size, size], [-size, -size, size], [-size, -size, -size],  # 左侧面
            [size, size, size], [size, size, -size], [-size, size, -size], [-size, size, size],  # 顶部面
            [size, -size, -size], [size, -size, size], [-size, -size, size], [-size, -size, -size],  # 底部面
            [size, size, size], [size, -size, size], [-size, -size, size], [-size, size, size],  # 前侧面
            [size, -size, -size], [size, size, -size], [-size, size, -size], [-size, -size, -size]  # 后侧面
        ]

        # 定义每个面的法线方向，用于光照计算
        normals = [
            [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]
        ]

        glBegin(GL_QUADS)
        for i in range(6):  # 遍历6个面
            glNormal3fv(normals[i])  # 设置法线方向
            for j in range(4):  # 遍历每个面的4个顶点
                glVertex3fv(vertices[i * 4 + j])
        glEnd()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glRotatef(self.rotateX, 1, 0, 0)  # Rotate around X-axis for Skybox
        glRotatef(self.rotateY, 0, 1, 0)  # Rotate around Y-axis for Skybox
        # glRotatef(self.skybox_angle, 0, 1, 0)  # Rotate the skybox around Y-axis
        self.draw_skybox()

        # Draw rotating cube
        glPushMatrix()
        glTranslatef(0, 0, -5)  # Move the cube slightly into the scene
        # glRotatef(self.cube_angle, 0, 1, 0)  # Rotate the cube around Y-axis
        self.draw_cube()
        glPopMatrix()

        self.cube_angle += 1  # Increment the cube's rotation angle
        # self.skybox_angle += 1
        self.update()

    def load_skybox(self):
        try:
            textures = [
                "skybox/right.bmp", "skybox/left.bmp", "skybox/top.bmp", "skybox/bottom.bmp", "skybox/front.bmp",
                "skybox/back.bmp"
            ]
            self.skybox_textures = glGenTextures(6)
            for i, texture_path in enumerate(textures):
                glBindTexture(GL_TEXTURE_2D, self.skybox_textures[i])
                img = Image.open(texture_path).convert('RGBA')
                img_data = img.tobytes()
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
                error = glGetError()
                if error != GL_NO_ERROR:
                    print(f"OpenGL error: {error}")
        except Exception as e:
            print(e)

    def draw_skybox(self):
        skybox_size = 90

        glPushMatrix()
        glDepthFunc(GL_LEQUAL)  # 修改深度函数，使Skybox在其他物体后面渲染
        glEnable(GL_TEXTURE_2D)

        faces = [
            # Right face
            (self.skybox_textures[0],
             [(skybox_size, -skybox_size, -skybox_size), (skybox_size, -skybox_size, skybox_size),
              (skybox_size, skybox_size, skybox_size), (skybox_size, skybox_size, -skybox_size)],
             [(1, 0), (0, 0), (0, 1), (1, 1)]),
            # Left face
            (self.skybox_textures[1],
             [(-skybox_size, -skybox_size, skybox_size), (-skybox_size, -skybox_size, -skybox_size),
              (-skybox_size, skybox_size, -skybox_size), (-skybox_size, skybox_size, skybox_size)],
             [(1, 0), (0, 0), (0, 1), (1, 1)]),
            # Top face
            (self.skybox_textures[2],
             [(-skybox_size, skybox_size, -skybox_size), (-skybox_size, skybox_size, skybox_size),
              (skybox_size, skybox_size, skybox_size), (skybox_size, skybox_size, -skybox_size)],
             [(0, 0), (0, 1), (1, 1), (1, 0)]),
            # Bottom face
            (self.skybox_textures[3],
             [(-skybox_size, -skybox_size, skybox_size), (-skybox_size, -skybox_size, -skybox_size),
              (skybox_size, -skybox_size, -skybox_size), (skybox_size, -skybox_size, skybox_size)],
             [(1, 1), (1, 0), (0, 0), (0, 1)]),
            # Front face
            (self.skybox_textures[4],
             [(-skybox_size, -skybox_size, skybox_size), (skybox_size, -skybox_size, skybox_size),
              (skybox_size, skybox_size, skybox_size), (-skybox_size, skybox_size, skybox_size)],
             [(0, 0), (1, 0), (1, 1), (0, 1)]),
            # Back face
            (self.skybox_textures[5],
             [(skybox_size, -skybox_size, -skybox_size), (-skybox_size, -skybox_size, -skybox_size),
              (-skybox_size, skybox_size, -skybox_size), (skybox_size, skybox_size, -skybox_size)],
             [(0, 0), (1, 0), (1, 1), (0, 1)])
        ]

        for face, vertices, tex_coords in faces:
            glBindTexture(GL_TEXTURE_2D, face)
            glBegin(GL_QUADS)
            for i, vertex in enumerate(vertices):
                glTexCoord2fv(tex_coords[i])
                glVertex3f(*vertex)
            glEnd()

        glPopMatrix()
        glDepthFunc(GL_LESS)  # 恢复默认深度函数

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self.perspective_glu(45.0, w / h, 1, 100.0)  # 使用自定义方法替换 gluPerspective
        glMatrixMode(GL_MODELVIEW)

    def perspective_glu(self, fov_y, aspect, z_near, z_far):
        f = 1.0 / np.tan(np.radians(fov_y) / 2.0)
        perspective_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (z_far + z_near) / (z_near - z_far), 2 * z_far * z_near / (z_near - z_far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        glLoadMatrixf(perspective_matrix.T)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('3D Skybox Example')
        self.opengl_widget = OpenGLWidget(self)
        self.setCentralWidget(self.opengl_widget)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
