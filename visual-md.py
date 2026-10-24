#!/usr/bin/env python3
"""visual-md — visor/editor de texto flotante y translúcido (GTK3).

Ventana GTK3 translúcida, movible y siempre por encima de las demás. Permite
abrir, editar, guardar y copiar texto plano o Markdown.

Requiere GTK3 + PyGObject y un compositor (GNOME/Mutter, picom, etc.).
"""

import os
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


APP_ID = "com.upstage.visualmd"
APP_VERSION = "0.1.0"
OPACITY_MIN = 0.25
OPACITY_MAX = 0.98
OPACITY_STEP = 0.05


class VisualMD(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.window = None
        self.view = None
        self.filename = None
        self.opacity = 0.72

    def do_activate(self):
        if self.window is None:
            self._build_window()

        # Un fichero pasado por línea de comandos (solo en el primer arranque).
        if self.filename is None:
            for arg in sys.argv[1:]:
                if not arg.startswith("-"):
                    self._load_file(os.path.abspath(os.path.expanduser(arg)))
                    break

        self.window.show_all()
        self.window.set_keep_above(True)
        self._apply_opacity()
        self.window.present()

        screen = self.window.get_screen()
        if not screen.is_composited():
            print(
                "Aviso: no hay compositor activo; la transparencia no se verá. "
                "Activa Mutter/GNOME o ejecuta picom.",
                file=sys.stderr,
            )

    # ------------------------------------------------------------------ UI
    def _build_window(self):
        self.window = Gtk.ApplicationWindow(
            application=self,
            title="visual-md",
            default_width=900,
            default_height=650,
        )
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("key-press-event", self._on_key_press)
        self.window.connect("delete-event", self._on_delete)
        self.window.connect("destroy", self._on_destroy)

        accel = Gtk.AccelGroup()
        self.window.add_accel_group(accel)
        self._add_accel(accel, Gdk.KEY_o, Gdk.ModifierType.CONTROL_MASK, self._on_open)
        self._add_accel(accel, Gdk.KEY_s, Gdk.ModifierType.CONTROL_MASK, self._on_save)
        self._add_accel(
            accel,
            Gdk.KEY_s,
            Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            self._on_save_as,
        )
        self._add_accel(accel, Gdk.KEY_r, Gdk.ModifierType.CONTROL_MASK, self._reload)
        self._add_accel(accel, Gdk.KEY_q, Gdk.ModifierType.CONTROL_MASK, self._on_quit)
        for key in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self._add_accel(
                accel,
                key,
                Gdk.ModifierType.CONTROL_MASK,
                lambda: self._change_opacity(OPACITY_STEP),
            )
        for key in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self._add_accel(
                accel,
                key,
                Gdk.ModifierType.CONTROL_MASK,
                lambda: self._change_opacity(-OPACITY_STEP),
            )

        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "visual-md"
        self.window.set_titlebar(header)

        open_btn = self._button("document-open", "Abrir (Ctrl+O)", self._on_open)
        save_btn = self._button("document-save", "Guardar (Ctrl+S)", self._on_save)
        copy_btn = self._button("edit-copy", "Copiar todo", self._copy_all)
        reload_btn = self._button("view-refresh", "Recargar (Ctrl+R)", self._reload)
        header.pack_start(open_btn)
        header.pack_start(save_btn)
        header.pack_start(copy_btn)
        header.pack_end(reload_btn)

        self.view = Gtk.TextView()
        self.view.set_editable(True)
        self.view.set_cursor_visible(True)
        self.view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.view.set_monospace(True)
        self.view.set_left_margin(14)
        self.view.set_right_margin(14)
        self.view.set_top_margin(10)
        self.view.set_bottom_margin(10)
        self.view.connect("key-press-event", self._on_key_press)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.view)
        self.window.add(scrolled)

        css = b"""
        window {
            background-color: rgba(0, 0, 0, 0.42);
            background-image: none;
        }
        headerbar, .titlebar {
            background-color: rgba(22, 22, 22, 0.72);
            background-image: none;
            border: none;
            box-shadow: none;
            color: #f7f7f7;
        }
        headerbar button {
            background-color: transparent;
            background-image: none;
            border: none;
            box-shadow: none;
            color: #f7f7f7;
        }
        headerbar button:hover {
            background-color: rgba(255, 255, 255, 0.14);
        }
        textview {
            background-color: rgba(0, 0, 0, 0.18);
            background-image: none;
            color: #f7f7f7;
            font-family: monospace;
            font-size: 16pt;
        }
        textview text {
            background-color: transparent;
            color: #f7f7f7;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.view.get_buffer().set_text(
            "Abre un fichero con Ctrl+O o arrastra uno aquí.\n", -1
        )
        self.view.get_buffer().set_modified(False)

    @staticmethod
    def _button(icon_name, tooltip, callback):
        btn = Gtk.Button.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", callback)
        return btn

    @staticmethod
    def _add_accel(group, key, mask, callback):
        def handler(*_args):
            callback()
            return True

        group.connect(key, mask, Gtk.AccelFlags.VISIBLE, handler)

    def _set_title(self):
        if self.filename:
            self.window.set_title(f"visual-md — {os.path.basename(self.filename)}")
        else:
            self.window.set_title("visual-md — sin título")

    def _base_dir(self):
        return os.path.dirname(self.filename) if self.filename else os.path.expanduser("~")

    # -------------------------------------------------------------- files
    def _load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            self._error("No se pudo abrir el fichero", str(exc))
            return False

        buffer = self.view.get_buffer()
        buffer.set_text(content, -1)
        buffer.set_modified(False)
        buffer.place_cursor(buffer.get_start_iter())
        self.filename = path
        self._set_title()
        return True

    def _save_file(self):
        if not self.filename:
            return self._save_as()
        text = self.view.get_buffer().get_text(
            self.view.get_buffer().get_start_iter(),
            self.view.get_buffer().get_end_iter(),
            False,
        )
        try:
            with open(self.filename, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            self._error("No se pudo guardar el fichero", str(exc))
            return False
        self.view.get_buffer().set_modified(False)
        self._set_title()
        return True

    def _save_as(self):
        dialog = Gtk.FileChooserDialog(
            title="Guardar como",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(
            os.path.basename(self.filename) if self.filename else "documento.md"
        )
        dialog.set_current_folder(self._base_dir())
        response = dialog.run()
        path = dialog.get_filename()
        dialog.destroy()
        if response != Gtk.ResponseType.OK or not path:
            return False
        self.filename = path
        return self._save_file()

    def _on_open(self, _widget=None):
        if not self._confirm_discard():
            return
        dialog = Gtk.FileChooserDialog(
            title="Abrir fichero",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Texto y Markdown (*.md, *.txt)")
        file_filter.add_pattern("*.md")
        file_filter.add_pattern("*.txt")
        file_filter.add_pattern("*.markdown")
        dialog.add_filter(file_filter)
        all_filter = Gtk.FileFilter()
        all_filter.set_name("Todos los ficheros")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        dialog.set_current_folder(self._base_dir())
        response = dialog.run()
        path = dialog.get_filename()
        dialog.destroy()
        if response == Gtk.ResponseType.OK and path:
            self._load_file(path)

    def _on_save(self, _widget=None):
        return self._save_file()

    def _on_save_as(self, _widget=None):
        return self._save_as()

    def _reload(self, _widget=None):
        if not self.filename:
            return
        if self._confirm_discard():
            self._load_file(self.filename)

    def _copy_all(self, _widget=None):
        buffer = self.view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()

    # ---------------------------------------------------------- lifecycle
    def _confirm_discard(self):
        if not self.view.get_buffer().get_modified():
            return True

        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO_CANCEL,
            text="¿Guardar los cambios?",
        )
        dialog.format_secondary_text(
            "Hay cambios sin guardar. ¿Quieres guardarlos antes de continuar?"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            return self._save_file()
        if response == Gtk.ResponseType.NO:
            return True
        return False

    def _on_delete(self, _widget=None, _event=None):
        return not self._confirm_discard()

    def _on_quit(self, _widget=None):
        if self._confirm_discard():
            self.window.destroy()

    def _error(self, title, detail):
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()

    # ------------------------------------------------------------ keyboard
    def _on_key_press(self, _widget, event):
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        if ctrl:
            if event.keyval == Gdk.KEY_o:
                self._on_open()
                return True
            if event.keyval == Gdk.KEY_s and shift:
                self._on_save_as()
                return True
            if event.keyval == Gdk.KEY_s:
                self._on_save()
                return True
            if event.keyval == Gdk.KEY_r:
                self._reload()
                return True
            if event.keyval == Gdk.KEY_q:
                self._on_quit()
                return True
            if event.keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                self._change_opacity(OPACITY_STEP)
                return True
            if event.keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
                self._change_opacity(-OPACITY_STEP)
                return True

        # Las teclas normales, Ctrl+C/V, etc. siguen llegando al TextView.
        return False

    def _apply_opacity(self):
        """Aplica la opacidad a la ventana X11 nativa.

        Gtk.Window.set_opacity() está deprecado en GTK3; Gdk.Window.set_opacity()
        escribe directamente _NET_WM_WINDOW_OPACITY y funciona con Mutter/picom.
        """
        gdk_window = self.window.get_window()
        if gdk_window is not None:
            gdk_window.set_opacity(self.opacity)
        else:
            self.window.set_opacity(self.opacity)

    def _change_opacity(self, delta):
        self.opacity = min(OPACITY_MAX, max(OPACITY_MIN, self.opacity + delta))
        self._apply_opacity()

    def _on_destroy(self, _widget=None):
        self.quit()


def main(argv):
    args = argv[1:]
    if "--version" in args:
        print(f"visual-md {APP_VERSION}")
        return 0
    if "--help" in args or "-h" in args:
        print(
            "Uso: visual-md [fichero]\n\n"
            "Visor/editor de texto flotante y translúcido.\n\n"
            "Atajos: Ctrl+O abrir, Ctrl+S guardar, Ctrl+Shift+S guardar como,\n"
            "        Ctrl+R recargar, Ctrl+Q salir, Ctrl++/Ctrl+- opacidad."
        )
        return 0

    app = VisualMD()
    # Gtk.Application no debe interpretar el nombre del fichero como una
    # petición de apertura: lo cargamos nosotros en do_activate().
    return app.run([argv[0]])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
