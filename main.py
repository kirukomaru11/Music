#!/usr/bin/python3
import gi, os, sys, marshal
for a, b in (("Gtk", "4.0"), ("Adw", "1"), ("Gly", "2"), ("GlyGtk4", "2"), ("AppStream", "1.0")): gi.require_version(a, b)
from gi.repository import AppStream, Gio, GLib, Gtk, Adw, Gdk, Gly, GlyGtk4
from MasonryBox import MasonryBox
from PaintableColorThief import palette
com = (m := AppStream.Metadata(), m.parse_file(Gio.File.new_for_path(os.path.join(GLib.get_system_data_dirs()[0], "metainfo", "io.github.kirukomaru11.Music.metainfo.xml")), 1), m.get_component())[-1]
Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(os.path.join(GLib.get_system_data_dirs()[0], com.props.id))
(s := Gtk.CssProvider.new(), s.load_from_path(os.path.join(GLib.get_system_data_dirs()[0], com.props.id, "style.css")), Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), s, 800))
app = Adw.Application(application_id=com.props.id, flags=4)
app.register()
(app.run(sys.argv), exit()) if app.props.is_remote else None
app.modifying, app.l, app.folder = False, [], None
file_launcher= Gtk.FileLauncher.new()
Action = lambda n, s, c: (a := Gio.SimpleAction.new(n, None), app.add_action(a), app.set_accels_for_action(f"app.{n}", s), a.connect("activate", c))
shortcuts, about = Adw.ShortcutsDialog(), Adw.AboutDialog(application_icon=f"{com.props.id}-symbolic", application_name=com.props.name, developer_name=com.get_developer().get_name(), issue_url=tuple(com.props.urls.values())[0], website=tuple(com.props.urls.values())[-1], license_type=7, version=com.get_releases_plain().get_entries()[0].get_version(), release_notes=com.get_releases_plain().get_entries()[0].get_description())
Action("about", (), lambda *_: about.present(app.props.active_window))
Action("shortcuts", ("<primary>question",), lambda *_: shortcuts.present(app.props.active_window))
section = Adw.ShortcutsSection(title="General")
for t, a in ( ("Open Current File", "<primary>o"), ("Open Library Folder", "<primary><shift>o"), ("Keyboard Shortcuts", "<primary>question"), ("Fullscreen", "F11")): section.add(Adw.ShortcutsItem(title=t, accelerator=a))
shortcuts.add(section)
def Button(t="button", callback=None, icon_name="", bindings=(), **kargs):
    bt = Gtk.MenuButton if t == "menu" else Gtk.ToggleButton if t == "toggle" else Gtk.Button
    bt = bt(icon_name=icon_name + "-symbolic" if icon_name else "", **kargs)
    if callback: bt.connect("clicked" if t == "button" else "notify::active", callback)
    for b in bindings:
        source = b[0] if b[0] else bt
        source.bind_property(b[1], b[2] if b[2] else bt, b[3], b[4] if len(b) >= 5 and b[4] else 0 | 2, b[5] if len(b) >= 6 else None)
    return bt
default_menu, default_items, menu_playlists = tuple(Gio.Menu.new() for _ in range(3))
for t, a in (("New Playlist", "new-playlist"), ("Show in Files", "show-in-files")): default_items.append(t, "app." + a)
def new_playlist(*_):
    f, n = app.music.get_child(f"{track_name(file_launcher.props.file)}.m3u8"), 0
    while os.path.exists(f.peek_path()):
        n += 1
        f = app.music.get_child(f"{track_name(file_launcher.props.file)} {n}.m3u8")
    f.replace_contents(f"{app.music.get_relative_path(file_launcher.props.file)}\n".encode("utf-8"), None, False, 0)
    add_playlist(f)
Action("new-playlist", [], new_playlist)
Action("show-in-files", [], lambda *_: file_launcher.open_containing_folder())
for i in (default_items, menu_playlists): default_menu.append_section(None, i)
for i in (default_menu, default_items): i.freeze()
track_factory = Gtk.SignalListItemFactory.new()
def setup_menu(b, p):
    if not b.props.active: return
    file_launcher.props.file = b.props.parent.props.parent.file
    app.mo = True
    menu_playlists.remove_all()
    for n, i in enumerate(sections[2].props.items):
        menu_playlists.append(i.props.title, f"app.playlist-{n}")
        app.lookup_action(f"playlist-{n}").change_state(GLib.Variant("b", i.file.parent.get_relative_path(file_launcher.props.file) in i.content))
    app.mo = False
def Drag(w):
    drag_source = Gtk.DragSource(actions=Gdk.DragAction.COPY)
    drag_source.connect("prepare", lambda e, x, y: Gdk.ContentProvider.new_for_value(Gdk.FileList.new_from_list((e.props.widget.file,))))
    drag_source.connect("drag-begin", lambda e, d: Gtk.DragIcon.get_for_drag(d).set_child(Gtk.Label(margin_top=10, margin_start=10, label=e.props.widget.file.get_basename(), css_classes=["title-4"])))
    w.add_controller(drag_source)
def track_drop(d, v, x, y):
    its = tuple(playlist.props.model.get_item(n) for n in range(playlist.props.model.props.n_items))
    if not v[0] in its: return False
    for n, i in enumerate(its):
        i.n = n
    d.props.widget.file.n, v[0].n = v[0].n, d.props.widget.file.n
    playlist.props.model.props.model.props.sorter.props.sort_order = 0
    playlist.props.model.props.model.props.sorter.set_expression(Gtk.ClosureExpression.new(int, lambda i: i.n))
    if sidebar.props.selected > 5 and not end_buttons[0].props.active:
        sidebar.props.selected_item.content = "\n".join(tuple(sidebar.props.selected_item.file.parent.get_relative_path(playlist.props.model.get_item(n)) for n in range(playlist.props.model.props.n_items)))
        sidebar.props.selected_item.file.replace_contents(sidebar.props.selected_item.content.encode("utf-8"), None, False, 0)
    return True
def setup_track(f, l):
    l.bindings = []
    box = Gtk.Box()
    Drag(box)
    n, play, label = Gtk.Label(css_classes=["dimmed"]), Gtk.Image(), Gtk.Label(ellipsize=3)
    revealer = Gtk.Revealer(child=Button(t="menu", css_classes=["flat"], halign=2, hexpand=True, icon_name="view-more", menu_model=default_menu, callback=setup_menu), transition_type=1)
    for i in (n, play, label, revealer): box.append(i)
    e = Gtk.EventControllerMotion()
    l.bindings = (l.bind_property("position", n, "label", 0 | 2, lambda b, v: str(v + 1)), l.bind_property("selected", n, "visible", 0 | 2 | 4), n.bind_property("visible", play, "visible", 0 | 2 | 4), e.bind_property("contains-pointer", revealer, "reveal-child", 0 | 2, lambda b, v: True if b.props.target.props.child.props.active else v), media_widgets[0].bind_property("icon-name", play, "icon-name", 0 | 2), l.bind_property("item", label, "label", 0 | 2, lambda b, v: track_name(v)))
    box.add_controller(e)
    d = Gtk.DropTarget(preload=True, actions=1, formats=Gdk.ContentFormats.parse("GdkFileList"))
    d.connect("drop", track_drop)
    box.add_controller(d)
    l.set_child(box)
track_factory.connect("bind", lambda f, l: setattr(l.props.child, "file", l.props.item))
track_factory.connect("unbind", lambda f, l: setattr(l.props.child, "file", None))
def teardown_track(f, l):
    for i in l.bindings: i.unbind()
    if l.props.child:
        while l.props.child.get_first_child(): l.props.child.get_first_child().unparent()
    l.set_child(None)
track_factory.connect("setup", setup_track)
track_factory.connect("teardown", teardown_track)
def track_name(v):
    if not v: return ""
    e = v.get_basename().rsplit(".", 1)[0]
    if e.split(" - ")[0].isdigit():
        e = e.split(" - ", 1)[-1]
    if e.split(". ", 1)[0].isdigit():
        e = e.split(". ", 1)[-1]
    return e
player = Gtk.MediaFile.new()
def filter_playlist(*_):
    e = lambda i: (sidebar.props.selected == 3) or (sidebar.props.selected == 0 and app.folder == artist_page.file and i.has_parent(app.folder)) or (app.folder != artist_page.file and i.has_prefix(app.folder))
    if sidebar.props.selected in (4, 5):
        e = lambda i: app.data[0].get(app.music.get_relative_path(i), 0) > 1
    if sidebar.props.selected > 5:
        e = lambda i: app.music.get_relative_path(i) in sidebar.props.selected_item.content if hasattr(sidebar.props.selected_item, "content") else False
    playlist.props.model.props.model.props.model.props.filter[1].set_expression(Gtk.ClosureExpression.new(bool, e))
    playlist.props.model.props.model.props.model.props.filter[1].set_invert(sidebar.props.selected == 5)
search = Gtk.SearchEntry(hexpand=True, placeholder_text="Search", search_delay=250)
def sort_playlist(*_):
    e = lambda i: 1
    if end_buttons[0].props.active:
        e = lambda i: GLib.random_int_range(1, 100)
    elif sidebar.props.selected == 4:
        e = lambda i: app.data[0].get(app.music.get_relative_path(i), 0)
    elif sidebar.props.selected > 5:
        e = lambda i: app.l.index(sidebar.props.selected_item.file.parent.get_relative_path(i)) if hasattr(sidebar.props.selected_item, "parent") else 1
    playlist.props.model.props.model.props.sorter.set_expression(Gtk.ClosureExpression.new(int, e))
    playlist.props.model.props.model.props.sorter.props.sort_order = 1 if sidebar.props.selected == 4 else 0
def search_changed(*_):
    if app.modifying: return
    if playlist.get_mapped(): playlist.props.model.props.model.props.model.props.filter[0].set_search(search.props.text)
    else:
        for c in catalog_pages:
            if c.props.child.get_mapped():
                for i in c.props.child if isinstance(c.props.child, Gtk.FlowBox) else c.props.child.get_children():
                    ch = i.props.child if isinstance(i, Gtk.FlowBoxChild) else i
                    i.props.visible = search.props.text.lower() in ch.props.tooltip_text.lower()
search.connect("search-changed", search_changed)
search_clamp = Adw.Clamp(maximum_size=350, child=search)
view = Adw.NavigationView()
playlist = Gtk.ListView(vscroll_policy=1, css_classes=["navigation-sidebar"], factory=track_factory, valign=1, model=Gtk.SingleSelection(autoselect=False, can_unselect=False, model=Gtk.SortListModel(model=Gtk.FilterListModel(model=Gio.ListStore.new(Gio.File)))))
playlist.props.model.props.model.props.sorter = Gtk.NumericSorter.new()
playlist.props.model.props.model.props.model.props.filter = Gtk.EveryFilter()
for i in (Gtk.StringFilter(expression=Gtk.ClosureExpression.new(str, lambda i: i.peek_path())), Gtk.BoolFilter()): playlist.props.model.props.model.props.model.props.filter.append(i)
playlist.props.model.connect("notify::selected-item", lambda s, p: set_play(s.props.selected_item) if s.props.selected_item and s.props.selected_item != player.props.file else None)
empty_page, queue_page, artist_page, artist_title = Adw.NavigationPage(title="Empty", child=Adw.StatusPage()), Adw.NavigationPage(title="Queue", child=Gtk.Overlay(child=Gtk.ScrolledWindow(hscrollbar_policy=2, child=playlist))), Adw.NavigationPage(title="Artist", child=Gtk.Box(css_name="artist", orientation=1)), Adw.WindowTitle()
artist_page.file = None
reset_search = lambda *_: (setattr(app, "modifying", True), search.set_text(""),  setattr(app, "modifying", False))
search.connect("map", reset_search)
queue_page.props.child.add_overlay(Adw.StatusPage(icon_name="edit-find-symbolic", title="No Results"))
def playlist_changed(p, pa):
    queue_page.props.child.get_last_child().set_visible(playlist.props.model.props.n_items == 0)
    if player.props.file:
        its = tuple(playlist.props.model.get_item(n) for n in range(playlist.props.model.props.n_items))
        if player.props.file in its:
            playlist.props.model.set_selected(its.index(player.props.file))
            update()
playlist.props.model.props.model.props.model.connect("notify::n-items", playlist_changed)

a_page_artist = Adw.Avatar(size=200, show_initials=True, halign=3)
a_page_artist.bind_property("text", a_page_artist, "tooltip-text", 0)
artist_page.props.child.append(a_page_artist)
a_page_albums, a_page_singles = ((b := Gtk.Box(orientation=1), b.append(Gtk.Label(label=i)), b.append(Adw.Clamp(child=Adw.Carousel(), orientation=1, maximum_size=300)), artist_page.props.child.append(b), b)[-1] for i in ("Albums", "Singles"))
toolbar, header = Adw.ToolbarView(content=Gtk.ScrolledWindow(hscrollbar_policy=2, child=Gtk.Viewport(vscroll_policy=1, child=view))), Adw.HeaderBar()
view.connect("notify::visible-page", lambda *_: toolbar.props.content.props.vadjustment.set_value(0))
view.bind_property("visible-page", header, "title-widget", 0 | 2, lambda b, v: artist_title if v == artist_page else search_clamp)
view.bind_property("visible-page", header, "show-title", 0 | 2, lambda b, v: v != empty_page)
toolbar.add_top_bar(header)
back_button = Button(callback=lambda b: view.pop(), tooltip_text="Back", icon_name="go-previous", bindings=((None, "visible", header, "show-back-button", 0 | 4),))
header.pack_start(back_button)
for i in ("replaced", "pushed", "popped"): view.connect(i, lambda *_: back_button.set_visible(view.props.navigation_stack.get_n_items() > 1))
sidebar = Adw.Sidebar(drop_preload=True)
def drop(s, n, v, a):
    if 5 > n: return False
    p = sidebar.get_item(n)
    for it in v:
        for i in playlist.props.model.props.model.props.model.props.model:
            if (i.equal(it) or i.has_prefix(it)) and not f"{p.file.parent.get_relative_path(i)}\n" in p.content:
                p.content += f"\n{p.file.parent.get_relative_path(i)}\n"
                toast_overlay.add_toast(Adw.Toast(title=f"{i.get_basename()} added to {p.props.title}", use_markup=False))
    p.file.replace_contents(p.content.encode("utf-8"), None, False, 0)
    return True
sidebar.setup_drop_target(Gdk.DragAction.COPY, (Gdk.FileList,))
sidebar.connect("drop", drop)
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
menus = tuple(Gio.Menu.new() for _ in range(4))
for n, i in enumerate(((("Open Library Folder", "open-dir"), ("Change Library Folder", "change-dir"), ("Manage Playlists", "edit"), ("Clear Most Played", "clear"),),
                    (("Cover Color Theming", "colors"), ("Run in Background", "hide-on-close")),
                    (("Keyboard Shortcuts", "shortcuts"), (f"About {about.props.application_name}", "about")))):
    for t, a in i: menus[n].append(t, "app." + a)
for i in menus[:3]: (i.freeze(), menus[3].append_section(None, i))
menus[3].freeze()
sidebar_header.pack_end(Button(t="menu", tooltip_text="Menu", icon_name="open-menu", menu_model=menus[3]))
split = Adw.NavigationSplitView(sidebar=Adw.NavigationPage(title="Music", child=(t := Adw.ToolbarView(content=sidebar), t.add_top_bar(sidebar_header), t)[-1]), content=main_page)
Action("open-dir", ["<primary><shift>o"], lambda *_: (file_launcher.set_file(app.music), file_launcher.launch()))
Action("open-current", ["<primary>o"], lambda *_: (file_launcher.set_file(player.props.file), file_launcher.open_containing_folder()))
def change_view(*_):
    reset_search()
    if len(catalog_pages) > sidebar.props.selected:
        c = catalog_pages[sidebar.props.selected].props.child
        if not ((hasattr(c, "get_children") and c.get_children()) or (isinstance(c, Gtk.FlowBox) and c.get_first_child())):
            page = empty_page
            empty_page.props.child.props.icon_name = sidebar.props.selected_item.props.icon_name
            empty_page.props.child.props.title = f"No {sidebar.props.selected_item.props.title}"
        else:
            page = catalog_pages[sidebar.props.selected]
        view.replace((page, ))
    else:
        if sidebar.props.selected > 5:
            app.l = sidebar.props.selected_item.content.strip().split("\n")
        sort_playlist()
        filter_playlist()
        view.replace((queue_page,))
    split.set_show_content(True)
sidebar.connect("activated", change_view)
def catalog_activate(m, c, b):
    app.folder = c.file
    sort_playlist()
    filter_playlist()
    view.push(queue_page)
catalog_pages = tuple(Adw.NavigationPage(title=i.props.title, child=Gtk.FlowBox(selection_mode=0, valign=1, min_children_per_line=2, max_children_per_line=8, row_spacing=16) if i.props.title == "Artists" else MasonryBox(activate=catalog_activate)) for i in sections[0].props.items)
def artist_activate(f, ch):
    c = ch.props.child
    artist_title.props.title = a_page_artist.props.text = c.file.get_basename()
    artist_page.file = c.file
    a_page_artist.props.custom_image = c.props.custom_image
    for i in (a_page_albums, a_page_singles):
        for it in tuple(it for it in i.get_last_child().props.child): i.get_last_child().props.child.remove(it)
    for b in (catalog_pages[1].props.child, catalog_pages[2].props.child):
        ca = a_page_albums if b == catalog_pages[1].props.child else a_page_singles
        ca = ca.get_last_child().props.child
        for i in b.get_children():
            if not i.file.has_prefix(c.file): continue
            p = Gtk.Picture(halign=3, css_classes=i.props.css_classes, tooltip_text=i.props.tooltip_text, paintable=i.props.paintable)
            (e := Gtk.GestureClick(), e.connect("released", lambda ev, *_: catalog_activate(None, ev.props.widget, 0), p.add_controller(e)))
            Drag(p)
            p.file = i.file
            ca.append(p)
    n = sum(i.get_last_child().props.child.props.n_pages for i in (a_page_albums, a_page_singles))
    if n == 0:
        app.folder = c.file
        sort_playlist()
        filter_playlist()
        return view.push(queue_page)
    for i in playlist.props.model.props.model.props.model.props.model:
        if i.has_parent(c.file):
            p = Gtk.Picture(halign=3, css_classes=["no-cover"], tooltip_text="Random Singles", paintable=default_paintable)
            (e := Gtk.GestureClick(), e.connect("released", lambda ev, *_: catalog_activate(None, ev.props.widget, 0), p.add_controller(e)))
            Drag(p)
            p.file = c.file
            ca.append(p)
            break
    for i in (a_page_albums, a_page_singles):
        i.props.visible = i.get_last_child().props.child.props.n_pages >= 1
    header.props.title_widget = artist_title
    view.push(artist_page)
catalog_pages[0].props.child.connect("child-activated", artist_activate)
_breakpoint = Adw.Breakpoint.new(Adw.BreakpointCondition.new_length(1, 700, 0))
_breakpoint.add_setter(split, "collapsed", True)
_breakpoint.add_setter(sidebar, "mode", 1)

loops = (("consecutive", "None"), ("repeat-song", "Track"), ("repeat", "Playlist"))

media_controls = Gtk.MediaControls(media_stream=player)
media_widgets = tuple(media_controls.get_template_child(Gtk.MediaControls, i) for i in ("play_button", "seek_scale", "volume_button"))
media_widgets[0].props.css_classes = ["circular"]
for i in media_widgets: i.unparent()
p_view = Adw.MultiLayoutView()
cover, artist = Gtk.Picture(content_fit=3), Adw.Avatar(size=40, show_initials=True)
artist.bind_property("text", artist, "tooltip-text", 0)
p_view.bind_property("layout-name", cover, "content-fit", 0, lambda b, v: 3 if v == "normal" else 1 if v == "fullscreen" else 2)
normal, small, fullscreen, controls_box = Gtk.Box(css_name="normal"), Adw.Clamp(css_name="small",  maximum_size=160, orientation=1, unit=0, child=Gtk.Overlay(child=Adw.LayoutSlot.new("cover"))), Gtk.Overlay(css_name="fullscreen", child=Adw.LayoutSlot.new("cover")), Gtk.Box(css_name="controls", orientation=1)
for i in (Adw.Clamp(maximum_size=90, orientation=1, unit=0, child=Adw.Clamp(maximum_size=300, unit=0, child=Adw.LayoutSlot.new("cover"))), Adw.LayoutSlot.new("controls_box")): normal.append(i)
small.bind_property("tooltip-text", normal.get_first_child(), "tooltip-text", 0)
small.props.child.add_overlay(Adw.Bin(child=Adw.LayoutSlot.new("controls_box"), valign=2))
fullscreen.add_overlay(Gtk.Revealer(child=Adw.LayoutSlot.new("controls_box"), valign=2, transition_type=1))
fullscreen.get_last_child().add_controller((e := Gtk.EventControllerMotion(), e.bind_property("contains-pointer", fullscreen.get_last_child(), "reveal-child", 0 | 2, lambda b,v: True if media_widgets[-1].props.active else v), e)[-1])
start, center, end = tuple(Gtk.Box(valign=2) for _ in range(3))
for i in (start, end): _breakpoint.add_setter(i, "orientation", 1)
def Next(*_):
    if buttons[2].props.sensitive:
        if end_buttons[1].props.tooltip_text == "Track":
            add_count()
            return player.seek(0)
        if playlist.props.model.props.n_items > playlist.props.model.props.selected + 1:
            playlist.props.model.props.selected += 1
        else:
            if end_buttons[1].props.tooltip_text == "Playlist":
                if playlist.props.model.props.selected == 0:
                    add_count()
                    return player.seek(0)
                playlist.props.model.props.selected = 0
player.connect("notify::ended", lambda *_: Next() if player.props.file and player.props.ended else None)
def Previous(*_):
    if buttons[0].props.sensitive:
        if end_buttons[1].props.tooltip_text == "Track":
            add_count()
            return player.seek(0)
        if playlist.props.model.props.selected != 0:
            playlist.props.model.props.selected -= 1
        else:
            if end_buttons[1].props.tooltip_text == "Playlist":
                playlist.props.model.props.selected = playlist.props.model.props.n_items - 1
                return
            if playlist.props.model.props.selected == 0:
                add_count()
                return player.seek(0)
            playlist.props.model.props.selected = 0
for i in (artist, media_widgets[2]): start.append(i)
buttons = [Button(callback=c, icon_name=f"media-skip-{i}", tooltip_text=t, css_classes=["flat"], valign=3, sensitive=False) for i, t, c in (("backward", "Previous", Previous), ("forward", "Next", Next))]
buttons.insert(1, media_widgets[0])
for i in buttons: center.append(i)
end_buttons = (Button(t="toggle", icon_name="media-playlist-shuffle", tooltip_text="Shuffle", callback=sort_playlist),
               Button(callback=lambda b: b.set_tooltip_text(next((loops[(i + 1) % len(loops)][1] for i, (_, s) in enumerate(loops) if s == b.props.tooltip_text), None)), tooltip_text=loops[0][1], bindings=((None, "tooltip-text", None, "icon-name", None, lambda b, v: "media-playlist-" + next((f for f, s in loops if s == v), "")), (None, "tooltip-text", player, "loop", None, lambda b, v: v == "Track"))),
               Button(action_name="app.fullscreen", bindings=((p_view, "layout-name", None, "icon-name", None, lambda b, v: "view-restore-symbolic" if v == "fullscreen" else "view-fullscreen-symbolic"), (p_view, "layout-name", None, "tooltip-text", None, lambda b, v: "Restore" if v == "fullscreen" else "Fullscreen"))))
for i in end_buttons: i.add_css_class("flat"); i.set_valign(3); end.append(i)
controls_box.append(Gtk.CenterBox(start_widget=start, center_widget=center, end_widget=end))
controls_box.append(media_widgets[1])

for n, i in (("cover", cover), ("controls_box", controls_box)): p_view.set_child(n, i) 
for a, b in (("normal", normal), ("small", small), ("fullscreen", fullscreen)): p_view.add_layout(Adw.Layout(name=a, content=b))
_breakpoint.connect("apply", lambda b: p_view.set_layout_name("small") if p_view.props.layout_name != "fullscreen" else None)
_breakpoint.connect("unapply", lambda b: p_view.set_layout_name("normal") if p_view.props.layout_name != "fullscreen" else None)
def fullscreen(*_):
    if p_view.props.layout_name == "fullscreen":
        p_view.props.layout_name = "small" if 700 > app.props.active_window.get_width() else "normal"
    else:
        p_view.props.layout_name = "fullscreen"
Action("fullscreen", ["F11"], fullscreen)
toast_overlay = Adw.ToastOverlay()
toast_overlay.props.child = box = Gtk.Box(orientation=1)
for i in (Gtk.Revealer(child=split, reveal_child=True), Gtk.WindowHandle(child=p_view)): box.append(i)
p_view.bind_property("layout-name", box.get_first_child(), "vexpand", 0 | 2, lambda b, v: v != "fullscreen")
p_view.bind_property("layout-name", box.get_last_child(), "vexpand", 0 | 2, lambda b, v: v == "fullscreen")
p_view.bind_property("layout-name", box.get_first_child(), "reveal-child", 0 | 2, lambda b, v: v != "fullscreen")

def change_playlist(a, p):
    if app.mo: return
    p = sections[2].get_item(int(a.props.name.split("-")[-1]))
    if p.file.parent.get_relative_path(file_launcher.props.file) in p.content:
        p.content = p.content.replace(f"{p.file.parent.get_relative_path(file_launcher.props.file)}\n", "")
    else:
        p.content += f"{p.file.parent.get_relative_path(file_launcher.props.file)}\n"
    p.file.replace_contents(p.content.encode("utf-8"), None, False, 0)
def rename(d, r):
    if r != "confirm": return
    i = sections[2].get_item(d.n)
    nw, n = i.file.parent.get_child(f"{d.props.extra_child.props.text}.m3u8"), 0
    while os.path.exists(nw.peek_path()):
        n += 1
        nw = i.file.parent.get_child(f"{d.props.extra_child.props.text} {n}.m3u8")
    i.file.move(nw, 0)
    i.file = nw
    i.props.title = nw.get_basename().replace(".m3u8", "").replace(".m3u", "")
rename_dialog = Adw.AlertDialog(css_classes=["alert", "floating", "rename-dialog"], extra_child=Gtk.Entry(), default_response="cancel")
key = Gtk.EventControllerKey()
key.connect("key-pressed", lambda e, kv, *_: (e.props.widget.get_ancestor(Adw.Dialog).close(), True)[-1] if kv == 65307 else False)
rename_dialog.props.extra_child.add_controller(key)
rename_dialog.props.extra_child.connect("activate", lambda e: e.get_ancestor(Adw.Dialog).do_response("confirm"))
rename_dialog.connect("response", rename)
for i in ("cancel", "confirm"): rename_dialog.add_response(i, i.title())
rename_dialog.set_response_appearance("confirm", 1)
app.add_action(Gio.SimpleAction.new_stateful("edit", None, GLib.Variant("b", False)))
def playlist_ops(b):
    d = rename_dialog if "Rename" in b.props.tooltip_text else are_you_sure
    d.n = b.props.parent.n
    rename_dialog.props.extra_child.props.text = sections[2].get_item(b.props.parent.n).file.get_basename().replace(".m3u8", "").replace(".m3u", "")
    d.props.heading = f'{b.props.tooltip_text} Playlist "{sections[2].get_item(b.props.parent.n).props.title}"?'
    d.present(app.props.active_window)
def add_playlist(f):
    box = Gtk.Box()
    for i, t in (("document-edit", "Rename"), ("user-trash", "Delete")): box.append(Button(icon_name=i, tooltip_text=t, valign=3, callback=playlist_ops))
    i = Adw.SidebarItem(title=f.get_basename().replace(".m3u8", "").replace(".m3u", ""), icon_name=f"playlist2-symbolic", suffix=Gtk.Revealer(child=box, transition_type=3), drag_motion_activate=False)
    app.lookup_action("edit").bind_property("state", i.props.suffix, "reveal-child", 0 | 2, lambda b, v: v.get_boolean())
    i.file = f
    box.n = len(sections[2].props.items)
    i.content = f.load_contents()[1].decode("utf-8")
    if not app.lookup_action(f"playlist-{len(sections[2].props.items)}"):
        app.add_action(Gio.SimpleAction.new_stateful(f"playlist-{len(sections[2].props.items)}", None, GLib.Variant("b", False)))
        app.lookup_action(f"playlist-{len(sections[2].props.items)}").connect("notify::state", change_playlist)
    sections[2].append(i)

cover.props.paintable = default_paintable = Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).lookup_icon("folder-music-symbolic", None, 500, 1, 0, 0)

def add_count():
    app.data[0].setdefault(app.music.get_relative_path(player.props.file), 0)
    app.data[0][app.music.get_relative_path(player.props.file)] += 1
def set_play(file=None):
    p = None
    if file:
        for b in (catalog_pages[1].props.child, catalog_pages[2].props.child):
            for i in b.get_children():
                if file.has_parent(i.file):
                    p = i.props.paintable
                    break
        for a in catalog_pages[0].props.child:
            if file.has_prefix(a.props.child.file):
                artist.props.text, artist.props.custom_image = a.props.child.props.text, a.props.child.props.custom_image
                break
        p = artist.props.custom_image if not p or p == default_paintable else p
        p = default_paintable if not p else p
        cover.props.paintable = p
    else:
        cover.props.paintable = p = default_paintable
        artist.props.text, artist.props.custom_image = "", None
    if p == default_paintable: cover.add_css_class("no-cover")
    else: cover.remove_css_class("no-cover")
    if hasattr(p, "colors") and app.lookup_action("colors").props.state:
        style = Gtk.CssProvider()
        GLib.idle_add(style.load_from_string, ":root {" + "".join(tuple(f"--color-{i + 1}: rgb{color};" for i, color in enumerate(p.colors))) + "}")
        GLib.idle_add(Gtk.StyleContext.add_provider_for_display, *(app.props.active_window.props.display, style, 700))
        GLib.idle_add(app.props.active_window.add_css_class, "colored")
    else:
        GLib.idle_add(app.props.active_window.remove_css_class, "colored")
    if player.props.prepared:
        player.stream_unprepared()
        player.clear()
    player.set_file(file)
    if file:
        add_count()
        player.props.playing = True
        small.props.tooltip_text = track_name(file)
    else:
        small.props.tooltip_text = ""
player.connect("notify::has-video", lambda p, pa: (cover.remove_css_class("no-cover"), cover.set_paintable(p)) if p.props.has_video and app.props.active_window.props.visible else None)
for i in (True, False, True): media_widgets[0].set_sensitive(i)

def get_all(i):
    sv = {}
    for it in interfaces[i]["properties"]:
        sv[it] = GLib.Variant(interfaces[i]["properties"][it][0], interfaces[i]["properties"][it][2]())
    return sv
def update(*_):
    buttons[2].props.sensitive = buttons[0].props.sensitive = False
    if player.props.file:
        buttons[2].props.sensitive = buttons[0].props.sensitive = True
        if end_buttons[1].props.tooltip_text == "None":
            buttons[0].props.sensitive = bool(playlist.props.model.props.selected_item) and playlist.props.model.props.selected != 0
            buttons[2].props.sensitive = playlist.props.model.props.n_items > playlist.props.model.props.selected + 1
    for i in interfaces:
        app.get_dbus_connection().emit_signal(None, "/" + mpris_interface.replace(".", "/"), f"{fd_interface}.Properties", "PropertiesChanged", GLib.Variant.new_tuple(*[GLib.Variant(sig,{"interface_name":i, "changed_properties": get_all(i), "invalidated_properties":()}[name]) for name, sig in {"interface_name": "s", "changed_properties": "a{sv}", "invalidated_properties": "as"}.items()]))

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
                "properties": {"CanQuit": ("b", "read", lambda: True), "Fullscreen": ("b", "readwrite", lambda: p_view.props.layout_name == "fullscreen"), "CanSetFullscreen": ("b", "read", lambda: app.props.active_window.props.visible), "CanRaise": ("b", "read", lambda: True), "HasTrackList": ("b", "read", lambda: False), "Identity": ("s", "read", lambda: about.props.application_name), "DesktopEntry": ("s", "read", lambda: com.props.id), "SupportedUriSchemes": ("as", "read", lambda: ["file"]), "SupportedMimeTypes": ("as", "read", lambda: ["application/ogg", "audio/x-vorbis+ogg", "audio/x-flac", "audio/mpeg"])}
             },
             f"{mpris_interface}.Player": {
                "methods": {
                  "Next": ((), Next), "Previous": ((), Previous), "Pause": ((), player.pause), "Play": ((), player.play), "PlayPause": ((), lambda: player.set_playing(not player.props.playing)), "Stop": ((), set_play),
                  "SetPosition": ((("TrackId", "in", "o"), ("Position", "in", "x")), lambda i, p: player.seek(p)), "Seek": ((("Offset", "in", "x"),), lambda o: player.seek(player.props.timestamp + o))
                },
                "signals": (),
                "properties": {
                    "PlaybackStatus": ("s", "read", lambda: "Stopped" if not player.props.file else "Playing" if player.props.playing else "Paused"),
                    "CanGoNext": ("b", "read", lambda: buttons[2].props.sensitive),
                    "CanGoPrevious": ("b", "read", lambda: buttons[0].props.sensitive),
                    "CanPlay": ("b", "read", lambda: bool(player.props.file)),
                    "CanPause": ("b", "read", lambda: bool(player.props.file)),
                    "CanControl": ("b", "read", lambda: True),
                    "Rate": ("d", "readwrite", lambda: 1.0), "MinimumRate": ("d", "read", lambda: 1.0),                     "MaximumRate": ("d", "read", lambda: 1.0),
                    "CanSeek": ("b", "read", lambda: not player.props.seeking and player.props.seekable),
                    "LoopStatus": ("s", "readwrite", lambda: end_buttons[1].props.tooltip_text),
                    "Shuffle": ("b", "readwrite", lambda: end_buttons[0].props.active),
                    "Volume": ("d", "readwrite", lambda: media_widgets[2].props.value),
                    "Position": ("x", "read", lambda: player.props.timestamp),
                    "Metadata": ("a{sv}", "read", lambda: {"xesam:title": GLib.Variant("s", track_name(player.props.file)),
            "xesam:artist": GLib.Variant("as", (str(artist.props.tooltip_text),)),
            "xesam:album": GLib.Variant("s", track_name(player.props.file.parent) if player.props.file else ""),
            "xesam:useCount": GLib.Variant("i", app.data[0].get(app.music.get_relative_path(player.props.file), 0) if player.props.file else 0),
            "mpris:artUrl": GLib.Variant("s", GLib.Uri.unescape_string(cover.props.paintable.file.get_uri()) if hasattr(cover.props.paintable, "file") else GLib.Uri.unescape_string(artist.props.custom_image.file.get_uri()) if artist.props.custom_image else ""),
            "mpris:length": GLib.Variant("x", player.props.duration),}),
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
        if p[1] == "LoopStatus":
            end_buttons[1].props.tooltip_text = p[2]
        if p[1] == "Volume":
            media_widgets[2].props.value = p[2]
        if p[1] == "Shuffle":
            end_buttons[0].props.active = p[2]
    elif m in interfaces[i]["methods"]: interfaces[i]["methods"][m][1](*p)
    inv.return_value(None)

def ays_response(d, r):
    if r != "yes": return
    if are_you_sure.props.heading == "Clear Most Played?": app.data[0].clear()
    else:
        i = sections[2].get_item(d.n)
        sections[2].remove(i)
        i.file.delete()
        for n, i in enumerate(sections[2].props.items):
            i.props.suffix.props.child.n = n
Action("clear", [], lambda *_: (are_you_sure.set_heading("Clear Most Played?"), are_you_sure.present(app.props.active_window)))
are_you_sure = Adw.AlertDialog(heading="Are You Sure", default_response="no")
are_you_sure.connect("response", ays_response)
for i in ("no", "yes"): are_you_sure.add_response(i, i.title())
are_you_sure.set_response_appearance("yes", 1)

app.covers = Gio.ListStore.new(Gio.File)
def parse_dir(root):
    app.music = Gio.File.new_for_path(root)
    app.covers.remove_all()
    sections[2].remove_all()
    playlist.props.model.props.model.props.model.props.model.remove_all()
    for i in (catalog_pages): i.props.child.remove_all()
    for r, d, f in os.walk(root):
        d.sort(key=lambda i: GLib.utf8_collate_key_for_filename(i, -1))
        file = Gio.File.new_for_path(r)
        file.f, c = sorted(f, key=lambda i: GLib.utf8_collate_key_for_filename(i, -1)), None
        for i in file.f:
            t = Gio.content_type_guess(i)[0]
            fi = file.get_child(i)
            fi.parent = file
            if i.endswith((".m3u", ".m3u8")): add_playlist(fi)
            elif t.startswith(("video", "audio")): playlist.props.model.props.model.props.model.props.model.append(fi)
            elif not c and t.startswith("image"):
                c = fi
                app.covers.append(fi)
        if r == root: continue
        if file.has_parent(app.music):
            a = Adw.Avatar(halign=3, show_initials=True, tooltip_text=file.get_basename(), text=file.get_basename(), size=200)
            Drag(a)
            a.file = file
            catalog_pages[0].props.child.append(a)
            catalog_pages[0].props.child.get_last_child().props.halign = 3
            _breakpoint.add_setter(a, "size", 160)
        else:
            box = catalog_pages[1].props.child if len(d) + len(f) >= 7 else catalog_pages[2].props.child
            p = Gtk.Picture(css_classes=["no-cover"], tooltip_text=file.get_basename(), paintable=default_paintable)
            Drag(p)
            p.file = file
            box.add(p)
    for i in app.covers: Gio.Task.new(i).run_in_thread(load_cover)
    change_view()

app_data = Gio.File.new_for_path(os.path.join(GLib.get_user_data_dir(), about.props.application_name.lower()))
if not os.path.exists(app_data.peek_path()): app_data.make_directory()
data_file = app_data.get_child(about.props.application_name)
app.data = marshal.loads(data_file.load_contents()[1]) if os.path.exists(data_file.peek_path()) else ({}, {})
for n, v in (("default-width", 600), ("default-height", 600), ("maximized", False), ("music", ""), ("hide-on-close", False), ("colors", True)): app.data[-1].setdefault(n, v)
for i in tuple(app.data[-1])[4:]: app.add_action(Gio.SimpleAction.new_stateful(i, None, GLib.Variant("b", app.data[-1][i])))
def load_cover(task, file, d, c):
    image = Gly.Loader.new(file).load()
    frame = image.next_frame()
    t = GlyGtk4.frame_get_texture(frame)
    t.colors = palette(t)
    if frame.get_delay() > 0:
        t = Gtk.MediaFile.new_for_file(file)
        t.bind_property("playing", t, "muted", 0 | 2 | 3)
        t.props.loop = t.props.playing = True
    t.file = file
    for b in (catalog_pages[1].props.child, catalog_pages[2].props.child):
        for i in b.get_children():
            if file.has_parent(i.file):
                i.height = image.get_height() / image.get_width()
                GLib.idle_add(i.set_paintable, t)
                i.remove_css_class("no-cover")
    for i in catalog_pages[0].props.child:
        if file.has_parent(i.props.child.file) or file.has_prefix(i.props.child.file) and not i.props.child.props.custom_image and not tuple(it for it in app.covers if it.has_parent(i.props.child.file)):
            GLib.idle_add(i.props.child.set_custom_image, t)
            break

def select_dir(d, r):
    app.data[-1]["music"] = d.select_folder_finish(r).get_path()
    if app.props.active_window.props.content != toast_overlay:
        app.props.active_window.close()
        app.activate()
    else: parse_dir(app.data[-1]["music"])
Action("change-dir", [], lambda *_: Gtk.FileDialog().select_folder(app.props.active_window, None, select_dir))

def activate(a):
    if a.props.active_window: return a.props.active_window.present()
    if app.data[-1]["music"] and os.path.exists(app.data[-1]["music"]):
        parse_dir(app.data[-1]["music"])
        w = Adw.ApplicationWindow(application=a, title=about.props.application_name, content=toast_overlay, default_width=app.data[-1]["default-width"], default_height=app.data[-1]["default-height"], maximized=app.data[-1]["maximized"])
        app.lookup_action("hide-on-close").bind_property("state", w, "hide-on-close", 0 | 2, lambda b, v: v.get_boolean())
        w.add_breakpoint(_breakpoint)
        w.present()
        Gio.bus_own_name_on_connection(app.get_dbus_connection(), f"{mpris_interface}.{com.props.id}", 0)
        for i in Gio.DBusNodeInfo.new_for_xml(mpris_xml).interfaces: app.get_dbus_connection().register_object_with_closures2("/" + mpris_interface.replace(".", "/"), i, call)
    else:
        change_dir = Adw.ToolbarView(extend_content_to_top_edge=True, content=Gtk.WindowHandle(child=Adw.StatusPage(title="No Folder Selected", icon_name=f"{com.props.id}-symbolic", child=Button(action_name="app.change-dir", label="Select Folder", css_classes=["pill", "suggested-action"], halign=3))))
        change_dir.add_top_bar(Adw.HeaderBar(show_title=False))
        Adw.ApplicationWindow(application=a, title=about.props.application_name, content=change_dir).present()
        
app.connect("activate", activate)
app.connect("window-removed", lambda a, w: tuple(app.data[-1].update({i: getattr(w.props, i)}) for i in app.data[-1] if hasattr(w.props, i)) if w.props.content == toast_overlay else None)
def shutdown(*_):
    for i in app.data[-1]:
        if app.lookup_action(i):
            app.data[-1][i] = app.lookup_action(i).props.state.get_boolean()
    data_file.replace_contents(marshal.dumps(app.data), None, True, 0)
app.connect("shutdown", shutdown)
def open_file(a, files, n, h):
    app.activate()
    sidebar.props.selected = 3
    change_view()
    for n, i in enumerate(files):
        exists = tuple(it for it in playlist.props.model.props.model.props.model.props.model if it.equal(i))
        if exists:
            files[n] = exists[0]
        else:
            i.parent = i.get_parent()
            playlist.props.model.props.model.props.model.props.model.append(i)
    its = tuple(playlist.props.model.get_item(n) for n in range(playlist.props.model.props.n_items))
    GLib.idle_add(playlist.scroll_to, *(its.index(files[0]), Gtk.ListScrollFlags.SELECT))
app.connect("open", open_file)
app.run(sys.argv)
