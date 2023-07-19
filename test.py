import webbrowser
import PySimpleGUI as sg

links = {
    "Google":"https://developers.google.com/edu/python/",
    "Udemy":"http://bit.ly/2D5vvnV",
    "CodeCademy":"https://bit.ly/learnpython3codecademy",
    "Educative":"https://www.educative.io/courses/learn-python-from-scratch?affiliate_id=5073518643380224",
    "Coursera":"https://coursera.pxf.io/c/3294490/1164545/14726?u=https%3A%2F%2Fwww.coursera.org%2Fspecializations%2Fpython",
    "Microsoft [edX]":"https://www.awin1.com/cread.php?awinmid=6798&awinaffid=631878&clickref=&p=%5B%5Bhttps%3A%2F%2Fwww.edx.org%2Fcourse%2Fintroduction-to-python-absolute-beginner-4%5D%5D",
    "FreeCodeCamp [Youtube]":"https://youtu.be/rfscVS0vtbw",
    "Lean Python in 1 hour (Javarevisited Youtube channel)":"https://youtu.be/7RDu6aoLQz4",
    "Python for Data Science and AI [Coursera]":"https://coursera.pxf.io/c/3294490/1164545/14726?u=https%3A%2F%2Fwww.coursera.org%2Flearn%2Fpython-for-applied-data-science-ai",
    "Introduction to Scripting in Python [Free Coursera Course]":"https://coursera.pxf.io/c/3294490/1164545/14726?u=https%3A%2F%2Fwww.coursera.org%2Fspecializations%2Fintroduction-scripting-in-python",
}

font1 = ("Arial", 16)
font2 = ("Times New", 16, "underline")
sg.theme('DarkBlue4')
sg.set_options(font=font1)

layout = [
    [sg.Text("Top 10 Websites to Learn Python Programming", justification='center', expand_x=True)]] + [
    [sg.Text(f'{i+1:0>2d}.'), sg.Text(f'{key}', enable_events=True, key=key)]
        for i, key in enumerate(links)]
window = sg.Window("Hyperlinks", layout, margins=(0, 0), finalize=True)
for key in links:
    window[key].bind('<Enter>', '<Enter>')
    window[key].bind('<Leave>', '<Leave>')
    window[key].set_cursor('hand2')

while True:

    event, values = window.read()

    if event == sg.WINDOW_CLOSED:
        break
    elif event.endswith('<Enter>'):
        element = window[event.split('<')[0]]
        element.update(font=font2)
    elif event.endswith('<Leave>'):
        element = window[event.split('<')[0]]
        element.update(font=font1)
    elif event in links:
        webbrowser.open(links[event])

window.close()