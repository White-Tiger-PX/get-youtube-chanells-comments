
import tkinter as tk


def show_message_box(title, message, text_button_true='Ок', text_button_false='Отмена'):
    """
    Показывает сообщение с кнопками "ОК" и "Отмена".
    Возвращает 1, если пользователь нажал "ОК", и 0 в остальных случаях.
    """
    show_message_box_result = 0

    def on_ok():
        nonlocal show_message_box_result
        show_message_box_result = 1
        root.destroy()

    def on_cancel():
        nonlocal show_message_box_result
        show_message_box_result = 0
        root.destroy()

    # Используем Toplevel, если уже существует Tk
    if tk._default_root is None:
        root = tk.Tk()
    else:
        root = tk.Toplevel()

    root.title(title)
    root.minsize(width=165, height=85)

    label = tk.Label(root, text=message)
    label.pack(pady=10)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    ok_button = tk.Button(button_frame, text=text_button_true, command=on_ok)
    cancel_button = tk.Button(button_frame, text=text_button_false, command=on_cancel)

    ok_button.pack(side=tk.LEFT, padx=5)
    cancel_button.pack(side=tk.LEFT, padx=5)

    # Ждать закрытия окна
    root.grab_set()  # Захват фокуса
    root.wait_window(root)  # Ожидание закрытия окна

    return show_message_box_result
