
import tkinter as tk
from menu import MenuTallerApp


def main():
    ventana = tk.Tk()
    menu = MenuTallerApp(ventana)

    ventana.protocol("WM_DELETE_WINDOW", menu.salir)
    ventana.mainloop()


if __name__ == "__main__":
    main()
