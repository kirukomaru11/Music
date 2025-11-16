#!/usr/bin/python3
from sys import argv

from AppUtils import *

css = """
small,
fullscreen { background: black; color: white; }
small controls,
fullscreen revealer > widget { background: linear-gradient(to top, color-mix(in srgb, black 50%, transparent), transparent); }
normal, small controls, fullscreen controls { padding: 10px; }
normal > clamp > clamp > widget > picture { border-radius: 10px; }
normal { border-spacing: 10px; box-shadow: 0px 0px 20px var(--card-shade-color); }
controls > box > box { border-spacing: 6px; }
controls > box > box:nth-child(2) > :nth-child(odd) { transform: scale(1.2); }
controls > box > box:nth-child(2) > :nth-child(2) { transform: scale(1.6); margin: 0px 14px 0px 14px; }
controls > scale { padding: 20px 0px 4px 0px; }

flowbox { padding: 4px; }
flowbox flowboxchild { border-radius: 100px; }

artist .no-cover,
masonrybox .no-cover { -gtk-icon-transform: scale(0.8); }
fullscreen .no-cover { -gtk-icon-transform: scale(0.5); }
small .no-cover { -gtk-icon-transform: scale(0.35); }

artist avatar { margin: 10px; }
artist label { font-weight: bold; margin: 14px 10px 10px 10px; }
artist picture { border-radius: 13px; }
artist picture { margin: 10px; }

sidebar preferencesgroup:nth-child(2) row:nth-child(2) box:first-child > image,
sidebar list row:nth-child(5) > box:first-child > image:first-child { transform: scale(1.25); }
sidebar preferencesgroup:nth-child(3) row box:first-child > image,
sidebar list row:nth-child(n+7) > box:first-child > image:first-child { transform: scale(1.3); }

listview row { padding: 0px; margin-bottom: 6px; }
listview box { border-radius: 8px; padding: 14px 6px 14px 0px; }
listview row label:first-child { min-width: 38px; padding: 0px 8px 0px 10px; }
listview row label:first-child { opacity: var(--dim-opacity); }
listview row:selected label:last-child { font-weight: bold; }
.colored listview row:selected { background-color: color-mix(in srgb, var(--color-2) 45%, transparent); }
listview:drop(active) .highlight {  border-color: var(--accent-bg-color); box-shadow: inset 0 0 0 1px var(--accent-bg-color); caret-color: var(--accent-bg-color); }

listview row:selected label:first-child { font-size: 0; background-repeat: no-repeat; background-position: 50%; opacity: 1;}

sheet,
normal,
navigation-split-view,
.sidebar-pane {
  transition-property: background;
  transition-duration: 250ms;
  transition-timing-function: ease;
}
.colored {
  --scrollbar-outline-color: rgb(0 0 0 / 25%);
  --accent-color: var(--color-2);
  --accent-bg-color: var(--color-2);
  --popover-bg-color: color-mix(in srgb, var(--color-2), var(--window-bg-color) 60%);
  --card-bg-color: rgb(255 255 255 / 4%);
}
.colored sheet,
.colored navigation-split-view {
  background: linear-gradient(to bottom right, color-mix(in srgb, var(--color-1) 45%, transparent), transparent),
    linear-gradient(to bottom left, color-mix(in srgb, var(--color-2) 45%, transparent), transparent),
    linear-gradient(to top, color-mix(in srgb, var(--color-3) 45%, transparent), transparent),
    var(--window-bg-color);
}
.colored normal { background: color-mix(in srgb, var(--color-3) 60%, transparent); box-shadow: none; }
.colored .sidebar-pane { background: color-mix(in srgb, var(--sidebar-bg-color) 15%, transparent); box-shadow: none; }
"""

def activate(a):
    if a.get_active_window(): return a.get_active_window().present()
    if a.data["General"]["music"] and os.path.exists(a.data["General"]["music"]):
        GLib.idle_add(parse_dir, a.data["General"]["music"])
        a.window.set_application(a)
        a.window.present()
    else:
        change_dir = Adw.ToolbarView(extend_content_to_top_edge=True, content=Gtk.WindowHandle(child=Adw.StatusPage(title="No Folder Selected", icon_name=f"{a.get_application_id()}-symbolic", child=Button(action_name="app.change-dir", label="Select Folder", css_classes=["pill", "suggested-action"], halign=Gtk.Align.CENTER))))
        change_dir.add_top_bar(Adw.HeaderBar(show_title=False))
        Adw.ApplicationWindow(application=a, title=a.name, content=change_dir).present()

def open_file(a, files, n, h):
    app.activate()
    sidebar.set_selected(3)
    change_view()
    for n, i in enumerate(files):
        exists = tuple(it for it in playlist.get_model().get_model().get_model().get_model() if it.equal(i))
        if exists:
            files[n] = exists[0]
        else:
            i.parent = i.get_parent()
            playlist.get_model().get_model().get_model().get_model().append(i)
    its = tuple(playlist.get_model().get_item(n) for n in range(playlist.get_model().get_n_items()))
    GLib.idle_add(playlist.scroll_to, *(its.index(files[0]), Gtk.ListScrollFlags.SELECT))

app = App(shortcuts={"General": (("Fullscreen", "app.fullscreen"), ("Open Current File", "app.open-file"), ("Open Library Folder", "app.open-library"), ("Keyboard Shortcuts", "app.shortcuts")), "Player": (("Seek Backwards", "a Left h"), ("Seek Forwards", "d Right l"), ("Play/Pause", "space"), ("Volume Up", "w Up k"), ("Volume Down", "s Down j"))},
          args=argv,
          activate=activate,
          application_id="io.github.kirukomaru11.Music",
          style=css,
          flags=Gio.ApplicationFlags.HANDLES_OPEN,
          file_open=open_file,
          data={
            "Window": { "default-height": 600, "default-width": 600, "maximized": False, "hide-on-close": False },
            "General": { "colors": True, "music": "" },
            "Played": {}
          })

a = Action("colors", callback=lambda *_: GLib.idle_add(set_colors, *(cover.p if hasattr(cover, "p") else None, True)), stateful=app.data["General"]["colors"])
a.path = "General"
app.persist.append(a)

default_paintable = Gtk.Svg.new_from_resource("/org/gtk/libgtk/icons/folder-music-symbolic.svg")
app.svg, app.l, app.folder, app.modifying = "", [], None, False

def select_dir(d, r):
    app.data["General"]["music"] = d.select_folder_finish(r).get_path()
    if app.get_active_window() != app.window:
        app.get_active_window().close()
        app.activate()
    else: GLib.idle_add(parse_dir, app.data["General"]["music"])
Action("change-dir", lambda *_: Gtk.FileDialog().select_folder(app.get_active_window(), None, select_dir))
Action("open-library", lambda *_: launch(app.music), "<primary><shift>o")
Action("open-file", lambda *_: launch(player.get_file()), "<primary>o")

track_factory = Gtk.SignalListItemFactory.new()
def Drag(w):
    drag_source = Gtk.DragSource(actions=Gdk.DragAction.COPY)
    drag_source.connect("prepare", lambda e, x, y: Gdk.ContentProvider.new_for_value(Gdk.FileList.new_from_list((e.get_widget().file,))))
    drag_source.connect("drag-begin", lambda e, d: Gtk.DragIcon.get_for_drag(d).set_child(Gtk.Label(margin_top=10, margin_start=10, label=e.get_widget().file.get_basename(), css_classes=("title-4",))))
    w.add_controller(drag_source)
def setup_track(f, l):
    l.set_child(Gtk.Box())
    for i in (Gtk.Label(), Gtk.Label(ellipsize=Pango.EllipsizeMode.END)): l.get_child().append(i)
    l.b1 = l.bind_property("position", l.get_child().get_first_child(), "label", GObject.BindingFlags.DEFAULT, bind_track_n)
    l.b2 = l.bind_property("item", l.get_child().get_last_child(), "label", GObject.BindingFlags.DEFAULT, bind_track_name)
track_factory.connect("setup", setup_track)
track_factory.connect("teardown", lambda f, l: (l.b1.unbind(), l.b2.unbind(), l.set_child(None)))
def track_name(v):
    if not v: return ""
    e = v.get_basename().rsplit(".", 1)[0]
    if e.split(" - ")[0].isdigit():
        e = e.split(" - ", 1)[-1]
    if e.split(". ", 1)[0].isdigit():
        e = e.split(". ", 1)[-1]
    return e
bind_track_n = lambda b, v: str(v + 1)
bind_track_name = lambda b, v: track_name(v)
def play_button(*_):
    if not app.window.get_visible(): return
    color = "ffffff" if app.get_style_manager().get_dark() else "222226"
    if player.get_playing():
        svg = f"""<g fill="#{color}"><path d="m 3 1 h 3 c 0.550781 0 1 0.449219 1 1 v 12 c 0 0.550781 -0.449219 1 -1 1 h -3 c -0.550781 0 -1 -0.449219 -1 -1 v -12 c 0 -0.550781 0.449219 -1 1 -1 z m 0 0"/><path d="m 10 1 h 3 c 0.550781 0 1 0.449219 1 1 v 12 c 0 0.550781 -0.449219 1 -1 1 h -3 c -0.550781 0 -1 -0.449219 -1 -1 v -12 c 0 -0.550781 0.449219 -1 1 -1 z m 0 0"/></g>"""
    else:
        svg = f"""<path d="m 2 2.5 v 11 c 0 1.5 1.269531 1.492188 1.269531 1.492188 h 0.128907 c 0.246093 0.003906 0.488281 -0.050782 0.699218 -0.171876 l 9.796875 -5.597656 c 0.433594 -0.242187 0.65625 -0.734375 0.65625 -1.226562 c 0 -0.492188 -0.222656 -0.984375 -0.65625 -1.222656 l -9.796875 -5.597657 c -0.210937 -0.121093 -0.453125 -0.175781 -0.699218 -0.175781 h -0.128907 s -1.269531 0 -1.269531 1.5 z m 0 0" fill="#{color}"/>"""
    if app.svg == svg: return
    app.svg = svg
    css = """listview row:selected label:first-child { background-image: url('data:image/svg+xml,<svg height="20px" viewBox="0 0 16 16" width="20px">""" + app.svg + "</svg>'); }"
    _css = Gtk.CssProvider.new()
    _css.load_from_string(css)
    GLib.idle_add(Gtk.StyleContext.add_provider_for_display, *(Gdk.Display.get_default(), _css, Gtk.STYLE_PROVIDER_PRIORITY_USER))
player = Gtk.MediaFile.new()
player.connect("notify::playing", play_button)
app.get_style_manager().connect("notify::dark", play_button)
def filter_playlist(*_):
    e = lambda i: (sidebar.get_selected() == 3) or (sidebar.get_selected() == 0 and app.folder == artist_page.file and i.has_parent(app.folder)) or (app.folder != artist_page.file and i.has_prefix(app.folder))
    if sidebar.get_selected() in (4, 5):
        e = lambda i: app.data["Played"].get(app.music.get_relative_path(i), 0) > 1
    if sidebar.get_selected() > 5:
        e = lambda i: app.music.get_relative_path(i) in sidebar.get_selected_item().content if hasattr(sidebar.get_selected_item(), "content") else False
    playlist.get_model().get_model().get_model().get_filter()[1].set_expression(Gtk.ClosureExpression.new(bool, e))
    playlist.get_model().get_model().get_model().get_filter()[1].set_invert(sidebar.get_selected() == 5)
search = Gtk.SearchEntry(hexpand=True, placeholder_text="Search")
def sort_playlist(*_):
    e = lambda i: 1
    if end_buttons[0].get_active():
        e = random_sort
    elif sidebar.get_selected() == 4:
        e = lambda i: app.data["Played"].get(app.music.get_relative_path(i), 0)
    elif sidebar.get_selected() > 5:
        e = lambda i: app.l.index(sidebar.get_selected_item().file.parent.get_relative_path(i)) if hasattr(sidebar.get_selected_item(), "parent") else 1
    playlist.get_model().get_model().get_sorter().set_properties(sort_order= 1 if sidebar.get_selected() == 4 else 0, expression=Gtk.ClosureExpression.new(int, e))
no_results = lambda: status.set_properties(icon_name="edit-find-symbolic", title="No Results", visible=True)

def search_changed(*_):
    status.set_visible(False)
    if playlist.get_mapped():
        playlist.get_model().get_model().get_model().get_filter()[0].set_search(search.get_text())
        if playlist.get_model().get_n_items() == 0: no_results()
    else:
        for c in catalog_pages:
            if c.get_child().get_mapped():
                children = tuple(i for i in c.get_child()) if isinstance(c.get_child(), Gtk.FlowBox) else c.get_child().get_children()
                for i in children:
                    ch = i.get_child() if isinstance(i, Gtk.FlowBoxChild) else i
                    i.set_visible(search.get_text().lower() in ch.get_tooltip_text().lower())
                if not children:
                    status.set_properties(icon_name=sidebar.get_selected_item().get_icon_name(), title=f"No {sidebar.get_selected_item().get_title()}", visible=True)
                if children and not any(i.get_visible() for i in children): no_results()

search.connect("search-changed", search_changed)
reset_search = lambda: GLib.idle_add(search.set_text, "") if search.get_text() else search_changed()
search_clamp = Adw.Clamp(maximum_size=350, child=search)
view = Adw.NavigationView(animate_transitions=False)
overlay = Gtk.Overlay(child=view)
status = Adw.StatusPage(visible=False)
overlay.add_overlay(status)
playlist = Gtk.ListView(vscroll_policy=Gtk.ScrollablePolicy.NATURAL, css_classes=("navigation-sidebar",), factory=track_factory, valign=1, model=Gtk.SingleSelection(autoselect=False, can_unselect=False, model=Gtk.SortListModel(model=Gtk.FilterListModel(model=Gio.ListStore.new(Gio.File)))))
e = Gtk.GestureLongPress()
def get_playlist_item(x, y):
    child = playlist.pick(x, y, Gtk.PickFlags.DEFAULT)
    if child == playlist: return
    while child.get_parent().get_parent() != playlist:
        child = child.get_parent()
    child.file = playlist.get_model().get_item(int(child.get_first_child().get_label()) - 1)
    return child
def long_click(e, x, y):
    child = get_playlist_item(x, y)
    if child: launch(child.file, folder=True)
    return
e.connect("pressed", long_click)
playlist.add_controller(e)
def track_drop(d, v, x, y):
    its = tuple(playlist.get_model().get_item(n) for n in range(playlist.get_model().get_n_items()))
    remove_button.set_reveal_child(False)
    if not v[0] in its or not playlist.highlight: return False
    for n, i in enumerate(its): setattr(i, "n", n)
    playlist.highlight.file.n, v[0].n = v[0].n, playlist.highlight.file.n
    playlist.get_model().get_model().get_sorter().set_sort_order(0)
    playlist.get_model().get_model().get_sorter().set_expression(Gtk.ClosureExpression.new(int, lambda i: i.n))
    if sidebar.get_selected() > 5 and not end_buttons[0].get_active():
        sidebar.get_selected_item().content = "\n".join(tuple(sidebar.get_selected_item().file.parent.get_relative_path(playlist.get_model().get_item(n)) for n in range(playlist.get_model().get_n_items())))
        sidebar.get_selected_item().file.replace_contents(sidebar.get_selected_item().content.encode("utf-8"), None, False, Gio.FileCreateFlags.NONE)
    return True
def highlight(e, x, y):
    if hasattr(playlist, "highlight") and playlist.highlight: playlist.highlight.remove_css_class("highlight")
    playlist.highlight = get_playlist_item(x, y)
    if playlist.highlight:
        playlist.highlight.add_css_class("highlight")
        return Gdk.DragAction.COPY
    return Gdk.DragAction.NONE
d = Gtk.DropTarget(preload=True, actions=Gdk.DragAction.COPY, formats=Gdk.ContentFormats.parse("GdkFileList"))
d.connect("drop", track_drop)
d.connect("motion", highlight)
playlist.add_controller(d)

drag_source = Gtk.DragSource(actions=Gdk.DragAction.COPY)
def d_prepare(e, x, y):
    child = get_playlist_item(x, y)
    if not child: return None
    e.file = child.file
    if hasattr(sidebar.get_selected_item(), "file"): remove_button.set_reveal_child(True)
    return Gdk.ContentProvider.new_for_value(Gdk.FileList.new_from_list((e.file,)))
drag_source.connect("prepare", d_prepare)
drag_source.connect("drag-cancel", lambda *_: (remove_button.set_reveal_child(False), True)[-1])
drag_source.connect("drag-begin", lambda e, d: Gtk.DragIcon.get_for_drag(d).set_child(Gtk.Label(margin_top=10, margin_start=10, label=e.file.get_basename(), css_classes=("title-4",))))
playlist.add_controller(drag_source)

playlist.get_model().get_model().set_sorter(Gtk.NumericSorter.new())
playlist.get_model().get_model().get_model().set_filter(Gtk.EveryFilter())
for i in (Gtk.StringFilter(expression=Gtk.ClosureExpression.new(str, lambda i: i.peek_path())), Gtk.BoolFilter()): playlist.get_model().get_model().get_model().get_filter().append(i)
playlist.get_model().connect("notify::selected-item", lambda s, p: set_play(s.get_selected_item()) if s.get_selected_item() and s.get_selected_item() != player.get_file() else None)
queue_page, artist_page, artist_title = Adw.NavigationPage(title="Queue", child=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=playlist)), Adw.NavigationPage(title="Artist", child=Gtk.Box(css_name="artist", orientation=Gtk.Orientation.VERTICAL)), Adw.WindowTitle()
artist_page.file = None
def playlist_changed():
    if player.get_file():
        its = tuple(playlist.get_model().get_item(n) for n in range(playlist.get_model().get_n_items()))
        if player.get_file() in its: GLib.idle_add(playlist.scroll_to, *(its.index(player.get_file()), Gtk.ListScrollFlags.SELECT))
    update()
    return False
playlist.get_model().get_model().get_model().connect("notify::n-items", lambda *_: GLib.idle_add(playlist_changed))

a_page_artist = Adw.Avatar(size=200, show_initials=True, halign=Gtk.Align.CENTER)
a_page_artist.bind_property("text", a_page_artist, "tooltip-text", GObject.BindingFlags.DEFAULT)
artist_page.get_child().append(a_page_artist)
a_page_albums, a_page_singles = ((b := Gtk.Box(orientation=Gtk.Orientation.VERTICAL), b.append(Gtk.Label(label=i)), b.append(Adw.Clamp(child=Adw.Carousel(), orientation=Gtk.Orientation.VERTICAL, maximum_size=300)), artist_page.get_child().append(b), b)[-1] for i in ("Albums", "Singles"))

toolbar, header = Adw.ToolbarView(content=Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, child=Gtk.Viewport(vscroll_policy=Gtk.ScrollablePolicy.NATURAL, child=overlay))), Adw.HeaderBar(show_back_button=False)
view.connect("notify::visible-page", lambda *_: toolbar.get_content().get_vadjustment().set_value(0))
view.bind_property("visible-page", header, "title-widget", GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE, lambda b, v: artist_title if v == artist_page else search_clamp)
toolbar.add_top_bar(header)
back_button = Button(callback=lambda b: view.pop() if view.get_navigation_stack().get_n_items() > 1 else split.set_show_content(False), tooltip_text="Back", icon_name="go-previous")
d = Gtk.DropTarget(actions=Gdk.DragAction.COPY, formats=Gdk.ContentFormats.parse("GdkFileList"))
d.connect("motion", lambda *_: (back_button.emit("clicked"), Gdk.DragAction.NONE)[-1])
back_button.add_controller(d)
header.pack_start(back_button)
sidebar = Adw.Sidebar(drop_preload=True, vexpand=True)
d = Gtk.DropTarget(preload=True, actions=Gdk.DragAction.COPY, formats=Gdk.ContentFormats.parse("GdkFileList"))
def drop(s, n, v, a):
    v = n if isinstance(n, Gdk.FileList) else v
    n = None if isinstance(n, Gdk.FileList) else n
    if n and 5 > n: return False
    if n:
        p = sidebar.get_item(n)
    else:
        f, n = app.music.get_child(f"{track_name(v[0])}.m3u8"), 0
        while os.path.exists(f.peek_path()):
            n += 1
            f = app.music.get_child(f"{track_name(v[0])} {n}.m3u8")
        f.replace_contents("".encode("utf-8"), None, False, Gio.FileCreateFlags.NONE)
        f.parent = f.get_parent()
        p = add_playlist(f)
    for it in v:
        for i in playlist.get_model().get_model().get_model().get_model():
            if (i.equal(it) or i.has_prefix(it)) and not f"{p.file.parent.get_relative_path(i)}\n" in p.content:
                p.content += f"\n{p.file.parent.get_relative_path(i)}\n"
                Toast(f"{i.get_basename()} added to {p.get_title()}", timeout=1)
    p.file.replace_contents(p.content.encode("utf-8"), None, False, Gio.FileCreateFlags.NONE)
    remove_button.set_reveal_child(False)
    return True
sidebar.setup_drop_target(Gdk.DragAction.COPY, (Gdk.FileList,))
sidebar.connect("drop", drop)
d.connect("drop", drop)
def drop_value_loaded(s, i, v):
    if i > 5 and tuple(it for it in v if it.has_prefix(app.music)): return Gdk.DragAction.COPY
    return Gdk.DragAction.NONE
sidebar.connect("drop-value-loaded", drop_value_loaded)
sections = tuple(Adw.SidebarSection() for _ in range(3))
for i in sections: sidebar.append(i)
for t, i in (("Artists", "folder-user"), ("Albums", "media-optical-cd"), ("Singles", "media-tape")): sections[0].append(Adw.SidebarItem(title=t, icon_name=f"{i}-symbolic", drag_motion_activate=False))
for t, i in (("All Songs", "library-music"), ("Most Played", "fire2"), ("Recently Added", "folder-recent")): sections[1].append(Adw.SidebarItem(title=t, icon_name=f"{i}-symbolic", drag_motion_activate=False))
main_page = Adw.NavigationPage(child=toolbar, title="Main Page")
sidebar_header = Adw.HeaderBar()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
split = Adw.NavigationSplitView(sidebar=Adw.NavigationPage(title="Music", child=(t := Adw.ToolbarView(content=box), t.add_controller(d), t.add_top_bar(sidebar_header), t)[-1]), content=main_page)
remove_button = Gtk.Revealer(child=Adw.ButtonRow(hexpand=True, title="Remove From Playlist"), transition_type=Gtk.RevealerTransitionType.SLIDE_UP, valign=Gtk.Align.END)
remove_button.get_child().add_css_class("destructive-action")
remove_d = Gtk.DropTarget(preload=True, actions=Gdk.DragAction.COPY, formats=Gdk.ContentFormats.parse("GdkFileList"))
def remove_drop(s, v, x, y):
    p = sidebar.get_selected_item()
    for it in v:
        for i in playlist.get_model().get_model().get_model().get_model():
            if (i.equal(it) or i.has_prefix(it)) and f"{p.file.parent.get_relative_path(i)}\n" in p.content:
                p.content = p.content.replace(f"{p.file.parent.get_relative_path(i)}\n", "").strip() + "\n"
                Toast(f"{i.get_basename()} removed from {p.get_title()}", timeout=1, use_markup=False)
    p.file.replace_contents(p.content.encode("utf-8"), None, False, Gio.FileCreateFlags.NONE)
    remove_button.set_reveal_child(False)
    return True
remove_d.connect("drop", remove_drop)
remove_button.add_controller(remove_d)
for i in (sidebar, remove_button): box.append(i)
def change_view(*_):
    if not sidebar.get_selected_item(): return
    if len(catalog_pages) > sidebar.get_selected():
        c = catalog_pages[sidebar.get_selected()].get_child()
        view.replace((catalog_pages[sidebar.get_selected()], ))
    else:
        if sidebar.get_selected() > 5:
            app.l = sidebar.get_selected_item().content.strip().split("\n")
        sort_playlist()
        filter_playlist()
        view.replace((queue_page,))
    reset_search()
sidebar.connect("notify::selected", change_view)
sidebar.connect("activated", lambda *_: (None if split.get_show_content() else GLib.idle_add(search_changed), split.set_show_content(True)))
def catalog_activate(m, c, b):
    app.folder = c.file
    sort_playlist()
    filter_playlist()
    view.push(queue_page)
    reset_search()
catalog_pages = tuple(Adw.NavigationPage(title=i.get_title(), child=Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, valign=Gtk.Align.START, min_children_per_line=2, max_children_per_line=8, row_spacing=16) if i.get_title() == "Artists" else MasonryBox(activate=catalog_activate)) for i in sections[0].get_items())
_breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.new_length(Adw.BreakpointConditionLengthType.MAX_WIDTH, 700, Adw.LengthUnit.PX))
app.window.add_breakpoint(_breakpoint)
_breakpoint.add_setter(catalog_pages[0].get_child(), "row-spacing", 6)
def artist_activate(f, ch):
    c = ch.get_child()
    a_page_artist.set_text(c.file.get_basename())
    artist_title.set_title(c.file.get_basename())
    artist_page.file = c.file
    a_page_artist.set_custom_image(c.get_custom_image())
    for i in (a_page_albums, a_page_singles):
        for it in tuple(it for it in i.get_last_child().get_child()): i.get_last_child().get_child().remove(it)
    for b in (catalog_pages[1].get_child(), catalog_pages[2].get_child()):
        ca = a_page_albums if b == catalog_pages[1].get_child() else a_page_singles
        ca = ca.get_last_child().get_child()
        for i in b.get_children():
            if not i.file.has_prefix(c.file): continue
            p = Gtk.Picture(halign=Gtk.Align.CENTER, css_classes=i.get_css_classes(), tooltip_text=i.get_tooltip_text(), paintable=i.get_paintable())
            (e := Gtk.GestureClick(), e.connect("released", lambda ev, *_: catalog_activate(None, ev.get_widget(), 0), p.add_controller(e)))
            Drag(p)
            p.file = i.file
            ca.append(p)
    n = sum(i.get_last_child().get_child().get_n_pages() for i in (a_page_albums, a_page_singles))
    if n == 0:
        app.folder = c.file
        sort_playlist()
        filter_playlist()
        view.push(queue_page)
        return reset_search()
    for i in playlist.get_model().get_model().get_model().get_model():
        if i.has_parent(c.file):
            p = Gtk.Picture(halign=Gtk.Align.CENTER, css_classes=("no-cover",), tooltip_text="Random Singles", paintable=default_paintable)
            (e := Gtk.GestureClick(), e.connect("released", lambda ev, *_: catalog_activate(None, ev.get_widget(), 0), p.add_controller(e)))
            Drag(p)
            p.file = c.file
            ca.append(p)
            break
    for i in (a_page_albums, a_page_singles):
        i.set_visible(i.get_last_child().get_child().get_n_pages() >= 1)
    header.set_title_widget(artist_title)
    view.push(artist_page)
    reset_search()
catalog_pages[0].get_child().connect("child-activated", artist_activate)
_breakpoint.add_setter(split, "collapsed", True)
_breakpoint.add_setter(sidebar, "mode", Adw.SidebarMode.PAGE)
back_update = lambda *_: back_button.set_visible(view.get_navigation_stack().get_n_items() > 1 or split.get_show_content() and split.get_collapsed())
for i in ("replaced", "pushed", "popped"): view.connect(i, back_update)
for i in ("collapsed", "show-content"): split.connect(f"notify::{i}", back_update)

loops = (("consecutive", "None"), ("repeat-song", "Track"), ("repeat", "Playlist"))

media_controls = Gtk.MediaControls(media_stream=player)
media_widgets = tuple(media_controls.get_template_child(Gtk.MediaControls, i) for i in ("play_button", "seek_scale", "volume_button"))
media_widgets[0].add_css_class("circular")
for i in media_widgets: i.unparent()
p_view = Adw.MultiLayoutView(focusable=True)
add_grab_focus(p_view)
controller = Gtk.ShortcutController()
p_view.add_controller(controller)
p_view.controls = media_controls
controller.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("space"), Gtk.CallbackAction.new(lambda *_: player.set_playing(not player.get_playing()))))
controller.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("Escape"), Gtk.CallbackAction.new(lambda *_: p_view.set_layout_name("small" if 700 > app.window.get_width() else "normal"))))
controller.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("f"), Gtk.CallbackAction.new(lambda *_: app.lookup_action("fullscreen").activate())))
add_move_shortcuts(controller, False)
cover, artist = Gtk.Picture(css_classes=("no-cover",)), Adw.Avatar(size=40, show_initials=True)
artist.bind_property("text", artist, "tooltip-text", GObject.BindingFlags.DEFAULT)
p_view.bind_property("layout-name", cover, "content-fit", GObject.BindingFlags.DEFAULT, lambda b, v: Gtk.ContentFit.FILL if v == "normal" else Gtk.ContentFit.CONTAIN if v == "fullscreen" else Gtk.ContentFit.COVER)
normal, small, fullscreen, controls_box = Gtk.Box(css_name="normal"), Adw.Clamp(css_name="small",  maximum_size=180, orientation=Gtk.Orientation.VERTICAL, unit=Adw.LengthUnit.PX, child=Gtk.Overlay(child=Adw.LayoutSlot.new("cover"))), Gtk.Overlay(css_name="fullscreen", child=Adw.LayoutSlot.new("cover")), Gtk.Box(css_name="controls", orientation=Gtk.Orientation.VERTICAL)
for i in (Adw.Clamp(maximum_size=90, orientation=Gtk.Orientation.VERTICAL, unit=Adw.LengthUnit.PX, child=Adw.Clamp(maximum_size=300, unit=Adw.LengthUnit.PX, child=Adw.LayoutSlot.new("cover"))), Adw.LayoutSlot.new("controls_box")): normal.append(i)
small.bind_property("tooltip-text", normal.get_first_child(), "tooltip-text", GObject.BindingFlags.DEFAULT)
small.get_child().add_overlay(Adw.Bin(child=Adw.LayoutSlot.new("controls_box"), valign=Gtk.Align.END))
fullscreen.add_overlay(Gtk.Revealer(child=Adw.LayoutSlot.new("controls_box"), valign=Gtk.Align.END, transition_type=Gtk.RevealerTransitionType.CROSSFADE))
menubutton = Button(t=Gtk.MenuButton, tooltip_text="Menu", css_classes=("flat",), valign=Gtk.Align.CENTER, icon_name="open-menu", menu_model=Menu((("Open Library Folder", "open-library"), ("Change Library Folder", "change-dir"), ("Clear Most Played", "clear"),), (("Cover Color Theming", "colors"), ("Run in Background", "hide-on-close")), app.default_menu))
fullscreen.get_last_child().add_controller((e := Gtk.EventControllerMotion(), e.bind_property("contains-pointer", fullscreen.get_last_child(), "reveal-child", GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE, lambda b,v: True if media_widgets[-1].get_active() or menubutton.get_active() else v), e)[-1])
start, center, end = tuple(Gtk.Box(valign=Gtk.Align.END) for _ in range(3))
for i in (start, end): _breakpoint.add_setter(i, "orientation", Gtk.Orientation.VERTICAL)
def Next(*_):
    if buttons[2].get_sensitive():
        if end_buttons[1].get_tooltip_text() == "Track":
            add_count()
            return player.seek(0)
        if playlist.get_model().get_n_items() > playlist.get_model().get_selected() + 1:
            playlist.get_model().set_selected(playlist.get_model().get_selected() + 1)
        else:
            if end_buttons[1].get_tooltip_text() == "Playlist":
                if playlist.get_model().get_selected() == 0:
                    add_count()
                    return player.seek(0)
                playlist.get_model().set_selected(0)
player.connect("notify::ended", lambda *_: Next() if player.get_file() and player.get_ended() else None)
def Previous(*_):
    if buttons[0].get_sensitive():
        if end_buttons[1].get_tooltip_text() == "Track":
            add_count()
            return player.seek(0)
        if playlist.get_model().get_selected() != 0:
            playlist.get_model().set_selected(playlist.get_model().get_selected() - 1)
        else:
            if end_buttons[1].get_tooltip_text() == "Playlist":
                playlist.get_model().set_selected(playlist.get_model().get_n_items() - 1)
                return
            if playlist.get_model().get_selected() == 0:
                add_count()
                return player.seek(0)
            playlist.get_model().set_selected(0)
for i in (artist, media_widgets[2], menubutton): start.append(i)
buttons = [Button(callback=c, icon_name=f"media-skip-{i}", tooltip_text=t, css_classes=["flat"], valign=Gtk.Align.CENTER, sensitive=False) for i, t, c in (("backward", "Previous", Previous), ("forward", "Next", Next))]
buttons.insert(1, media_widgets[0])
for i in buttons: center.append(i)
end_buttons = (Button(t=Gtk.ToggleButton, icon_name="media-playlist-shuffle", tooltip_text="Shuffle", callback=sort_playlist),
               Button(callback=lambda b: b.set_tooltip_text(next((loops[(i + 1) % len(loops)][1] for i, (_, s) in enumerate(loops) if s == b.get_tooltip_text()), None)), tooltip_text=loops[0][1], bindings=((None, "tooltip-text", None, "icon-name", None, lambda b, v: "media-playlist-" + next((f for f, s in loops if s == v), "")), (None, "tooltip-text", player, "loop", None, lambda b, v: v == "Track"))),
               Button(action_name="app.fullscreen", bindings=((p_view, "layout-name", None, "icon-name", None, lambda b, v: "view-restore-symbolic" if v == "fullscreen" else "view-fullscreen-symbolic"), (p_view, "layout-name", None, "tooltip-text", None, lambda b, v: "Restore" if v == "fullscreen" else "Fullscreen"))))
for i in end_buttons: i.add_css_class("flat"); i.set_valign(Gtk.Align.CENTER); end.append(i)
controls_box.append(Gtk.CenterBox(vexpand=True, hexpand=True, start_widget=start, center_widget=center, end_widget=end))
controls_box.append(media_widgets[1])

for n, i in (("cover", cover), ("controls_box", controls_box)): p_view.set_child(n, i) 
for a, b in (("normal", normal), ("small", small), ("fullscreen", fullscreen)): p_view.add_layout(Adw.Layout(name=a, content=b))
_breakpoint.connect("apply", lambda b: p_view.set_layout_name("small") if p_view.get_layout_name() != "fullscreen" else None)
_breakpoint.connect("unapply", lambda b: p_view.set_layout_name("normal") if p_view.get_layout_name() != "fullscreen" else None)
def fullscreen(*_):
    if p_view.get_layout_name() == "fullscreen": p_view.set_layout_name("small" if 700 > app.window.get_width() else "normal")
    else: p_view.set_layout_name("fullscreen")
Action("fullscreen", fullscreen, "F11")
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
app.window.get_content().set_child(box)
for i in (Gtk.Revealer(child=split, reveal_child=True), Gtk.WindowHandle(child=p_view)): box.append(i)
p_view.bind_property("layout-name", box.get_first_child(), "vexpand", GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE, lambda b, v: v != "fullscreen")
p_view.bind_property("layout-name", box.get_last_child(), "vexpand", GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE, lambda b, v: v == "fullscreen")
p_view.bind_property("layout-name", box.get_first_child(), "reveal-child", GObject.BindingFlags.DEFAULT | GObject.BindingFlags.SYNC_CREATE, lambda b, v: v != "fullscreen")

def rename(r):
    i = app.current
    nw, n = i.file.parent.get_child(f"{r.get_text()}.m3u8"), 0
    while os.path.exists(nw.peek_path()):
        n += 1
        nw = i.file.parent.get_child(f"{r.get_text()} {n}.m3u8")
    nw.parent = i.file.parent
    i.file.move(nw, Gio.FileCopyFlags.NONE)
    i.file = nw
    i.set_title(nw.get_basename().replace(".m3u8", "").replace(".m3u", ""))
    r.set_show_apply_button(False)
    p_edit.set_title(i.get_title())
    r.set_show_apply_button(True)
p_edit = Adw.PreferencesDialog(follows_content_size=True)
p_edit.add(Adw.PreferencesPage())
r = Adw.EntryRow(title="Name", show_apply_button=True)
p_edit.bind_property("title", r, "text", GObject.BindingFlags.DEFAULT)
for r, s, c in ((r, "apply", rename), (Adw.ButtonRow(title="Delete"), "activated", lambda *_: (are_you_sure.set_heading(f'Delete Playlist "{app.current.get_title()}"?'), are_you_sure.present(app.window)))):
    group = Adw.PreferencesGroup()
    p_edit.get_visible_page().add(group)
    r.connect(s, c)
    group.add(r)
r.add_css_class("destructive-action")
def add_press(w):
    b = w.get_ancestor(Gtk.ListBoxRow).get_child()
    if hasattr(b, "press") or not w.get_mapped(): return
    e = Gtk.GestureLongPress()
    e.i = w.i
    e.connect("pressed", lambda ev, *_: (setattr(app, "current", ev.i), p_edit.set_title(ev.i.get_title()), p_edit.present(app.window)))
    GLib.idle_add(b.add_controller, e)
def add_playlist(f):
    i = Adw.SidebarItem(title=f.get_basename().replace(".m3u8", "").replace(".m3u", ""), icon_name=f"playlist2-symbolic", drag_motion_activate=False, suffix=Adw.Bin())
    i.get_suffix().connect("map", add_press)
    i.get_suffix().i = i
    i.file = f
    n = len(sections[2].get_items())
    i.content = f.load_contents()[1].decode("utf-8").strip() + "\n"
    sections[2].append(i)
    return i
cover.set_paintable(default_paintable)

def add_count():
    app.data["Played"].setdefault(app.music.get_relative_path(player.get_file()), 0)
    app.data["Played"][app.music.get_relative_path(player.get_file())] += 1
def set_play(file=None):
    p = None
    if file:
        for b in (catalog_pages[1].get_child(), catalog_pages[2].get_child()):
            for i in b.get_children():
                if file.has_parent(i.file):
                    p = i.get_paintable()
                    break
        for a in catalog_pages[0].get_child():
            if file.has_prefix(a.get_child().file):
                artist.set_properties(text=a.get_child().get_text(), custom_image=a.get_child().get_custom_image())
                break
        p = artist.get_custom_image() if not p or p == default_paintable else p
        p = default_paintable if not p else p
        cover.set_paintable(p)
    else:
        p = default_paintable
        cover.set_paintable(p)
        artist.set_properties(text="", custom_image=None)
    if p == default_paintable: cover.add_css_class("no-cover")
    else: cover.remove_css_class("no-cover")
    cover.p = p
    set_colors(p, True)
    if player.is_prepared():
        player.stream_unprepared()
        player.clear()
    player.set_file(file)
    if file:
        add_count()
        player.set_playing(True)
        small.set_tooltip_text(track_name(file))
    else:
        small.set_tooltip_text("")
player.connect("notify::has-video", lambda p, pa: (cover.remove_css_class("no-cover"), cover.set_paintable(p)) if p.has_video() and app.window.get_visible() else None)
for i in (True, False, True): media_widgets[0].set_sensitive(i)

def ays_response(d, r):
    if r != "yes": return
    if are_you_sure.get_heading() == "Clear Most Played?": app.data["Played"].clear()
    else:
        sections[2].remove(app.current)
        app.current.file.delete()
        p_edit.close()
    sidebar.set_selected(0)
Action("clear", lambda *_: (are_you_sure.set_heading("Clear Most Played?"), are_you_sure.present(app.window)))
are_you_sure = Adw.AlertDialog(heading="Are You Sure", default_response="no")
are_you_sure.connect("response", ays_response)
for i in ("no", "yes"): are_you_sure.add_response(i, i.title())
are_you_sure.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)

def get_all(i):
    sv = {}
    for it in interfaces[i]["properties"]:
        sv[it] = GLib.Variant(interfaces[i]["properties"][it][0], interfaces[i]["properties"][it][2]())
    return sv
def update(*_):
    buttons[0].set_sensitive(False)
    buttons[2].set_sensitive(False)
    if player.get_file():
        buttons[0].set_sensitive(True)
        buttons[2].set_sensitive(True)
        if end_buttons[1].get_tooltip_text() == "None":
            buttons[0].set_sensitive(bool(playlist.get_model().get_selected_item()) and playlist.get_model().get_selected() != 0)
            buttons[2].set_sensitive(playlist.get_model().get_n_items() > playlist.get_model().get_selected() + 1)
    for i in interfaces: app.get_dbus_connection().emit_signal(None, "/" + mpris_interface.replace(".", "/"), f"{fd_interface}.Properties", "PropertiesChanged", GLib.Variant.new_tuple(*[GLib.Variant(sig,{"interface_name":i, "changed_properties": get_all(i), "invalidated_properties":()}[name]) for name, sig in {"interface_name": "s", "changed_properties": "a{sv}", "invalidated_properties": "as"}.items()]))

for w, prop in ((player, "duration"), (player, "playing"), (end_buttons[1], "tooltip-text"), (end_buttons[0], "active")): w.connect(f"notify::{prop}", update)
mpris_interface, fd_interface = "org.mpris.MediaPlayer2", "org.freedesktop.DBus"
interfaces = {
            f"{fd_interface}.Introspectable": {
                "methods": {
                  "Introspect": ((("data", "out", "s"),), lambda: mpris_xml),
                },
                "signals": (),
                "properties": {}
             },
            f"{fd_interface}.Properties": {
                "methods": {
                  "Set": ((("interface_name", "in", "s"), ("property_name", "in", "s"), ("value", "in", "v")),),
                  "Get": ((("interface", "in", "s"), ("property", "in", "s"), ("value", "out", "v")),),
                  "GetAll": ((("interface", "in", "s"), ("properties", "out", "a{sv}")),),
                },
                "signals": (("PropertiesChanged", (("interface_name", "s"), ("changed_properties", "a{sv}"), ("invalidated_properties", "as"))),),
                "properties": {}
             },
             f"{mpris_interface}": {
                "methods": {
                "Raise": ((), lambda: app.activate()),
                "Quit": ((), lambda: app.quit()),
                },
                "signals": (),
                "properties": {"CanQuit": ("b", "read", lambda: True), "Fullscreen": ("b", "readwrite", lambda: p_view.get_layout_name() == "fullscreen"), "CanSetFullscreen": ("b", "read", lambda: app.window.get_visible()), "CanRaise": ("b", "read", lambda: True), "HasTrackList": ("b", "read", lambda: False), "Identity": ("s", "read", lambda: app.about.get_application_name()), "DesktopEntry": ("s", "read", lambda: app.get_application_id()), "SupportedUriSchemes": ("as", "read", lambda: ["file"]), "SupportedMimeTypes": ("as", "read", lambda: ["application/ogg", "audio/x-vorbis+ogg", "audio/x-flac", "audio/mpeg"])}
             },
             f"{mpris_interface}.Player": {
                "methods": {
                  "Next": ((), Next), "Previous": ((), Previous), "Pause": ((), player.pause), "Play": ((), player.play), "PlayPause": ((), lambda: player.set_playing(not player.get_playing())), "Stop": ((), set_play),
                  "SetPosition": ((("TrackId", "in", "o"), ("Position", "in", "x")), lambda i, p: player.seek(p)), "Seek": ((("Offset", "in", "x"),), lambda o: player.seek(player.get_timestamp() + o))
                },
                "signals": (),
                "properties": {
                    "PlaybackStatus": ("s", "read", lambda: "Stopped" if not player.get_file() else "Playing" if player.get_playing() else "Paused"),
                    "CanGoNext": ("b", "read", lambda: buttons[2].get_sensitive()),
                    "CanGoPrevious": ("b", "read", lambda: buttons[0].get_sensitive()),
                    "CanPlay": ("b", "read", lambda: bool(player.get_file())),
                    "CanPause": ("b", "read", lambda: bool(player.get_file())),
                    "CanControl": ("b", "read", lambda: True),
                    "Rate": ("d", "readwrite", lambda: 1.0), "MinimumRate": ("d", "read", lambda: 1.0), "MaximumRate": ("d", "read", lambda: 1.0),
                    "CanSeek": ("b", "read", lambda: not player.is_seeking() and player.is_seekable()),
                    "LoopStatus": ("s", "readwrite", lambda: end_buttons[1].get_tooltip_text()),
                    "Shuffle": ("b", "readwrite", lambda: end_buttons[0].get_active()),
                    "Volume": ("d", "readwrite", lambda: media_widgets[2].get_value()),
                    "Position": ("x", "read", lambda: player.get_timestamp()),
                    "Metadata": ("a{sv}", "read", lambda: {"xesam:title": GLib.Variant("s", track_name(player.get_file())),
            "xesam:artist": GLib.Variant("as", (str(artist.get_tooltip_text()),)),
            "xesam:album": GLib.Variant("s", track_name(player.get_file().parent) if player.get_file() else ""),
            "xesam:useCount": GLib.Variant("i", app.data["Played"].get(app.music.get_relative_path(player.get_file()), 0) if player.get_file() else 0),
            "mpris:artUrl": GLib.Variant("s", GLib.Uri.unescape_string(cover.get_paintable().file.get_uri()) if hasattr(cover.get_paintable(), "file") else GLib.Uri.unescape_string(artist.get_custom_image().file.get_uri()) if hasattr(artist.get_custom_image(), "file") else ""),
            "mpris:length": GLib.Variant("x", player.get_duration()),}),
                }
             }}
mpris_xml = "<!DOCTYPE node PUBLIC '-//freedesktop//DTD D-BUS Object Introspection 1.0//EN' 'http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd'><node>"
for i in interfaces:
    mpris_xml += f"<interface name='{i}'>"
    for method in interfaces[i]["methods"]:
        mpris_xml += f"<method name='{method}'>"
        for arg in interfaces[i]["methods"][method][0]:
            mpris_xml += f"<arg name='{arg[0]}' direction='{arg[1]}' type='{arg[2]}'/>"
        mpris_xml += "</method>"
    for prop in interfaces[i]["properties"]:
        mpris_xml += f"<property name='{prop}' type='{interfaces[i]['properties'][prop][0]}' access='{interfaces[i]['properties'][prop][1]}'/>"
    for signal in interfaces[i]["signals"]:
        mpris_xml += f"<signal name='{signal[0]}'>"
        for arg in signal[1]:
            mpris_xml += f"<arg name='{arg[0]}' type='{arg[1]}'/>"
        mpris_xml += "</signal>"
    mpris_xml += "</interface>"
mpris_xml += "</node>"
def call(c, s, o_path, i, m, p, inv):
    if m == "Get": return inv.return_value(GLib.Variant("(v)", (GLib.Variant(interfaces[p[0]]["properties"][p[1]][0], interfaces[p[0]]["properties"][p[1]][2]()),)))
    elif m == "GetAll": return inv.return_value(GLib.Variant("(a{sv})", (get_all(p[0]), )))
    elif m == "Set":
        if p[1] == "Fullscreen": end_buttons[-1].activate()
        if p[1] == "LoopStatus": end_buttons[1].set_tooltip_text(p[2])
        if p[1] == "Volume": media_widgets[2].set_value(p[2])
        if p[1] == "Shuffle": end_buttons[0].set_active(p[2])
    elif m in interfaces[i]["methods"]: interfaces[i]["methods"][m][1](*p)
    inv.return_value(None)

Gio.bus_own_name_on_connection(app.get_dbus_connection(), f"{mpris_interface}.{app.get_application_id()}", Gio.BusNameOwnerFlags.NONE)
for i in Gio.DBusNodeInfo.new_for_xml(mpris_xml).interfaces: app.get_dbus_connection().register_object_with_closures2("/" + mpris_interface.replace(".", "/"), i, call)

def finish_func(picture, paintable):
    GLib.idle_add(picture.remove_css_class, "no-cover")
    paintable.colors = palette(paintable, distance=1.2, black_white=1.8)
    file = picture.file
    paintable.file = file.c
    for p in (catalog_pages[1], catalog_pages[2]):
        for i in p.get_child().get_children():
            if not i.file.c and i.get_paintable() is default_paintable and i.file.has_prefix(file):
                GLib.idle_add(i.set_paintable, paintable)
                GLib.idle_add(i.remove_css_class, "no-cover")
    for i in catalog_pages[0].get_child():
        if not i.get_child().file.c and (file.has_parent(i.get_child().file) or file.has_prefix(i.get_child().file)) and not i.get_child().get_custom_image():
            GLib.idle_add(i.get_child().set_custom_image, paintable)

def parse_dir(root):
    app.music = Gio.File.new_for_path(root)
    sections[2].remove_all()
    playlist.get_model().get_model().get_model().get_model().remove_all()
    for i in (catalog_pages): i.get_child().remove_all()
    artists, albums, singles = [], [], []
    for r, d, f in os.walk(root):
        d.sort(key=alphabetical_sort)
        file = Gio.File.new_for_path(r)
        file.f, file.c = sorted(f, key=alphabetical_sort), None
        for i in file.f:
            t = Gio.content_type_guess(i)[0]
            fi = file.get_child(i)
            fi.parent = file
            if i.endswith((".m3u", ".m3u8")): add_playlist(fi)
            elif t.startswith(("video", "audio")): playlist.get_model().get_model().get_model().get_model().append(fi)
            elif not file.c and t.startswith("image"):
                file.c = fi
        if r == root: continue
        if file.has_parent(app.music): artists.append(file)
        else: albums.append(file) if len(d) + len(f) >= 7 else singles.append(file)
    for i in artists:
        a = Media(i.c, parent_type=Adw.Avatar, finish_func=finish_func, media=True, p__halign=Gtk.Align.CENTER, p__show_initials=True, p__tooltip_text=i.get_basename(), p__text=i.get_basename(), p__size=200)
        Drag(a)
        a.file = i
        catalog_pages[0].get_child().append(a)
        a.get_parent().set_halign(Gtk.Align.CENTER)
        _breakpoint.add_setter(a, "size", 168)
    for n, l in enumerate((albums, singles)):
        for i in l:
            media = Media(i.c, finish_func=finish_func, parent_type=Gtk.Picture, p__css_classes=("no-cover",), p__tooltip_text=i.get_basename(), media=True, p__paintable=default_paintable)
            media.file = i
            Drag(media)
            catalog_pages[n + 1].get_child().add(media)
    change_view()
    return False
app.run(argv)
