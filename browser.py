import gi
import os
import subprocess

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")

from gi.repository import Gtk, WebKit2, GLib

DOWNLOAD_DIR = "/home/joni/Downloads"

class Browser(Gtk.Window):
    def __init__(self):
        super().__init__(title="Generic Internet Browser")
        self.set_default_size(1024, 768)
        self.set_border_width(10)

        # Conectar la señal "download-started" en el WebContext predeterminado
        ctx = WebKit2.WebContext.get_default()
        ctx.connect("download-started", self.on_download_started)

        # Contenedor principal
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Barra de herramientas
        toolbar = Gtk.Box(spacing=6)
        vbox.pack_start(toolbar, False, False, 0)

        # Botón Atrás
        self.back_button = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.MENU)
        self.back_button.connect("clicked", self.go_back)
        toolbar.pack_start(self.back_button, False, False, 0)

        # Botón Adelante
        self.forward_button = Gtk.Button.new_from_icon_name("go-next", Gtk.IconSize.MENU)
        self.forward_button.connect("clicked", self.go_forward)
        toolbar.pack_start(self.forward_button, False, False, 0)

        # Barra de URL
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter URL...")
        self.url_entry.connect("activate", self.load_url)
        toolbar.pack_start(self.url_entry, True, True, 0)

        # Botón Recargar
        self.reload_button = Gtk.Button.new_from_icon_name("view-refresh", Gtk.IconSize.MENU)
        self.reload_button.connect("clicked", self.reload_page)
        toolbar.pack_start(self.reload_button, False, False, 0)

        # Botón Nueva Pestaña
        new_tab_button = Gtk.Button.new_from_icon_name("tab-new", Gtk.IconSize.MENU)
        new_tab_button.connect("clicked", self.new_tab)
        toolbar.pack_start(new_tab_button, False, False, 0)

        # Notebook para pestañas
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        vbox.pack_start(self.notebook, True, True, 0)

        # Barra de progreso
        self.progress_bar = Gtk.ProgressBar()
        vbox.pack_start(self.progress_bar, False, False, 0)

        # Crear la primera pestaña
        self.new_tab()
        self.connect("destroy", Gtk.main_quit)
        self.show_all()

    def new_tab(self, widget=None, url="https://www.duckduckgo.com"):
        # Crear el WebView y cargar la URL
        webview = WebKit2.WebView()
        webview.load_uri(url)
        webview.connect("load-changed", self.on_load_changed)
        webview.connect("load-failed", self.on_load_failed)
        webview.connect("notify::estimated-load-progress", self.on_load_progress)
        # No se conecta señal de descarga en el WebView, se hace a nivel de contexto

        # Crear un ScrolledWindow para el WebView
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(webview)
        scrolled_window.webview = webview

        # Etiqueta de la pestaña con botón de cerrar
        tab_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        label = Gtk.Label(label=f"Tab {self.notebook.get_n_pages() + 1}")
        close_button = Gtk.Button.new_from_icon_name("window-close", Gtk.IconSize.MENU)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.connect("clicked", self.close_tab)
        close_button.tab = scrolled_window

        tab_label_box.pack_start(label, True, True, 0)
        tab_label_box.pack_start(close_button, False, False, 0)
        tab_label_box.show_all()

        self.notebook.append_page(scrolled_window, tab_label_box)
        self.notebook.set_tab_reorderable(scrolled_window, True)
        self.notebook.set_current_page(self.notebook.get_n_pages() - 1)
        scrolled_window.show_all()
        self.url_entry.set_text(url)

    def load_url(self, widget):
        url = self.url_entry.get_text()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        current_page = self.notebook.get_nth_page(self.notebook.get_current_page())
        if current_page and hasattr(current_page, "webview"):
            current_page.webview.load_uri(url)

    def go_back(self, widget):
        current_page = self.notebook.get_nth_page(self.notebook.get_current_page())
        if current_page and hasattr(current_page, "webview"):
            current_page.webview.go_back()

    def go_forward(self, widget):
        current_page = self.notebook.get_nth_page(self.notebook.get_current_page())
        if current_page and hasattr(current_page, "webview"):
            current_page.webview.go_forward()

    def reload_page(self, widget):
        current_page = self.notebook.get_nth_page(self.notebook.get_current_page())
        if current_page and hasattr(current_page, "webview"):
            current_page.webview.reload()

    def close_tab(self, button):
        tab = button.tab
        if tab:
            page_num = self.notebook.page_num(tab)
            if page_num != -1:
                self.notebook.remove_page(page_num)

    def on_load_changed(self, webview, load_event):
        if load_event == WebKit2.LoadEvent.COMMITTED:
            self.url_entry.set_text(webview.get_uri())
            self.update_navigation_buttons(webview)

    def on_load_failed(self, webview, load_event, failing_uri, error):
        print(f"Error loading {failing_uri}: {error.message}")
        return True

    def on_load_progress(self, webview, progress):
        self.progress_bar.set_fraction(webview.get_estimated_load_progress())
        if webview.get_estimated_load_progress() == 1.0:
            self.progress_bar.set_fraction(0.0)

    def on_download_started(self, context, download):
        # Se invoca cuando se inicia una descarga a nivel de WebContext.
        url = download.get_request().get_uri()
        print("Iniciando descarga con wget:", url)
        # Cancelar la descarga interna de WebKit
        download.cancel()
        # Asegurarse de que exista el directorio de descargas
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
        # Invocar wget para manejar la descarga
        subprocess.Popen(["wget", url, "-P", DOWNLOAD_DIR])
        print("wget lanzado para descargar", url)

    def update_navigation_buttons(self, webview):
        self.back_button.set_sensitive(webview.can_go_back())
        self.forward_button.set_sensitive(webview.can_go_forward())

if __name__ == "__main__":
    app = Browser()
    Gtk.main()
