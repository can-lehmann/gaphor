import logging
import os.path

from gi.repository import Gtk

if Gtk.get_major_version() == 4:
    from gi.repository import Adw

from pathlib import Path

from gaphor.abc import ActionProvider, Service
from gaphor.core import action, gettext
from gaphor.ui.filedialog import open_file_dialog

log = logging.getLogger(__name__)


FILTERS = [
    (gettext("All Gaphor Models"), "*.gaphor", "application/x-gaphor"),
]


class AppFileManager(Service, ActionProvider):
    """Handle application level file loading."""

    def __init__(self, application):
        self.application = application
        self.last_dir = None

    def shutdown(self):
        pass

    @property
    def parent_window(self):
        return (
            self.application.active_session.get_service("main_window").window
            if self.application.active_session
            else None
        )

    @action(name="app.file-open")
    def action_open(self):
        """This menu action opens the standard model open dialog."""

        def open_files(filenames):
            for filename in filenames:
                if self.application.has_session(filename):
                    name = Path(filename).name
                    title = gettext("Switch to {name}?").format(name=name)
                    body = gettext(
                        "{name} is already opened. Do you want to switch to the opened window instead?"
                    ).format(name=name)
                    if Gtk.get_major_version() == 3:
                        dialog = Gtk.MessageDialog(
                            message_type=Gtk.MessageType.QUESTION,
                            buttons=Gtk.ButtonsType.YES_NO,
                            text=title,
                            secondary_text=body,
                        )
                        dialog.set_transient_for(self.parent_window)

                        dialog.set_modal(True)
                    else:
                        dialog = Adw.MessageDialog.new(
                            self.parent_window,
                            title,
                        )
                        dialog.set_body(body)
                        dialog.add_response("open", gettext("Open Again"))
                        dialog.add_response("switch", gettext("Switch"))
                        dialog.set_response_appearance(
                            "switch", Adw.ResponseAppearance.SUGGESTED
                        )
                        dialog.set_default_response("switch")
                        dialog.set_close_response("open")

                    def response(dialog, answer):
                        # Gtk.ResponseType.NO is for GTK3, open is for GTK4
                        force_new_session = answer in [Gtk.ResponseType.NO, "open"]
                        dialog.destroy()
                        self.application.new_session(
                            filename=filename, force=force_new_session
                        )

                    dialog.connect("response", response)
                    dialog.show()
                else:
                    self.application.new_session(filename=filename)

                self.last_dir = os.path.dirname(filename)

        open_file_dialog(
            gettext("Open a Model"),
            open_files,
            parent=self.parent_window,
            dirname=self.last_dir,
            filters=FILTERS,
        )
