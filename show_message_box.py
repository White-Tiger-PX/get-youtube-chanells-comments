import tkinter as tk


def show_message_box(title, message, text_button_true='Ок', text_button_false='Отмена'):
    """
    Показывает всплывающее окно с сообщением и двумя кнопками: одну для подтверждения и другую для отмены.

    Если пользователь нажимает кнопку для подтверждения, функция возвращает `1`.
    Если нажимает кнопку для отмены или закрывает окно, возвращается `0`.

    Параметры для кнопок по умолчанию — "Ок" для подтверждения и "Отмена" для отмены,
    но они могут быть изменены.

    Args:
        title (str): Заголовок окна.
        message (str): Текст сообщения.
        text_button_true (str, optional): Текст кнопки подтверждения. По умолчанию 'Ок'.
        text_button_false (str, optional): Текст кнопки отмены. По умолчанию 'Отмена'.

    Returns:
        int: `1`, если была нажата кнопка для подтверждения (например, "Ок"),
        `0` в остальных случаях (например, при нажатии "Отмена" или закрытии окна).
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

    # Используем Toplevel, если уже существует корневое окно Tk
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

    # Захват фокуса и ожидание закрытия окна
    root.grab_set()
    root.wait_window(root)

    return show_message_box_result
