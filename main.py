from view import Application
import tkinter as tk


def main():
    width, height = 1280, 720
    root = tk.Tk()
    root.configure(bg='white')
    root.title('Picture Tools')
    root.geometry("{0}x{1}".format(width, height))
    root.update()  # to get the correct dimensions when calling winfo_width and winfo_height
    Application(root)
    root.mainloop()


if __name__ == '__main__':
    main()
