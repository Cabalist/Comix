# -*- coding: utf-8 -*-


import os
import sys
import tempfile
import gc
import shutil
import stat
import zipfile
import tarfile
import urllib
import locale
import gettext
import md5
import StringIO
import re
import time
import pwd
import cPickle

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject
import Image
import ImageEnhance
import ImageDraw
import ImageOps
import ImageStat
import ImageFont

import about
import constants


class Mainwindow:
    
    # =======================================================
    # All the preferences are stored here.
    # =======================================================
    prefs = {
        'fullscreen': 0,
        'default fullscreen': 0,
        'interp type': gtk.gdk.INTERP_TILES,
        'hide in fullscreen': 1,
        'double page': 0,
        'default double page': 0,
        'saturation': 1.0,
        'contrast': 1.0,
        'brightness': 1.0,
        'sharpness': 1.0,
        'save saturation and contrast': 0,
        'cache': 1,
        'manga': 0,
        'stretch': 0,
        'window width': gtk.gdk.screen_get_default().get_width() / 2,
        'window height': gtk.gdk.screen_get_default().get_height() * 3 / 4, 
        'window x': 0,
        'window y': 0,
        'save window pos': 1,
        'default open path': os.getenv('HOME'),
        'default zoom mode': 1,
        'zoom scale': 100,
        'zoom mode': 0,
        'red bg': 2100,
        'green bg': 2100,
        'blue bg': 2100,
        'hide scrollbar': 0,
        'go to next archive': 1,
        'hide cursor': 1,
        'show menubar': 1,
        'show toolbar': 1,
        'show statusbar': 1,
        'auto comments': 0,
        'comment extensions': 'txt nfo',
        'flip with wheel': 0,
        'scroll wheel horiz': 0,
        'smart double page scaling': 0,
        'toolbar style': gtk.TOOLBAR_ICONS,
        'smart space scroll': 0,
        'show thumbnails': 1,
        'hide thumbnail scrollbar': 0,
        'auto load last file': 0,
        'path to last file': '',
        'page of last file': 0,
        'open defaults to last browsed': 1,
        'path of last browsed': os.getenv('HOME'),
        'rotation': 0,
        'flip horiz': 0,
        'flip vert': 0,
        'keep transformation': 0,
        'show page numbers on thumbnails': 1,
        'autocontrast': 0,
        'emulate double page': 0,
        'thumbnail size': 80,
        'lens magnification': 2,
        'max lens update interval': 15,
        'use stored thumbnails': 1,
        'use stored archive thumbnails': 0,
        'hide all': 0,
        'stored hide all values': (0, 1, 1, 1, 1),
        'no double page for wide images': 0,
        'lib window width': gtk.gdk.screen_get_default().get_width() * 3 / 4,
        'lib window height':
            gtk.gdk.screen_get_default().get_height() * 3 / 4,
        'library filter on full path': 1,
        'library cover size': 128,
        'last convert type': '',
        'lens size from center': 90,
        'store recent file info': 1,
        'slideshow delay': 6.0,
        'space scroll length': 75,
        'space scroll type': 0
    }

    # =======================================================
    # Various shared variables used throughout the program.
    # =======================================================
    base_dir = ''
    path = ''
    archive_type = ''
    file = []
    file_number = 0
    old_file_number = -1
    comment = []
    comment_number = 0
    show_comments = 0
    bookmarks = []
    bookmark_numbers = []
    recent_files = []
    exit = 0
    file_exists = 0
    filetype_error = 0
    x_drag_position = -1
    y_drag_position = -1
    file_overwritten = 0
    mouse_moved_while_drag = 0
    change_scroll_adjustment = 0
    image1_width = 0
    image1_height = 0
    image2_width = 0
    image2_height = 0
    image1_scaled_width = 0
    image1_scaled_height = 0
    image2_scaled_width = 0
    image2_scaled_height = 0
    resize_event = 0
    scroll_events_up = 0
    scroll_events_down = 0
    number_of_thumbs_loaded = 0
    thumb_heights = []
    thumb_total_height = 0
    change_thumb_selection = 0
    thumb_loop_stop = 0
    stored_pixbuf = None
    stored_pixbuf2 = None
    cached_pixbuf = None
    cached_pixbuf2 = None
    stored_double = 0
    number_of_cached = 0
    main_layout_x_size = 0
    main_layout_y_size = 0
    menu_size = 0
    tool_size = 0
    status_size = 0
    thumb_size = 0
    thumb_vscroll_size = 0
    vscroll_size = 0
    hscroll_size = 0
    old_vadjust_value = 0
    old_hadjust_value = 0
    vadjust_upper = 0
    hadjust_upper = 0
    thumb_vadjust_upper = 0
    z_pressed = 0
    lens_timer = None
    drag_timer = None
    scroll_wheel_event_id = None
    stop_thumb_maintenance = 0
    stop_lib_maintenance = 0
    cursor_timer_id = None
    two_page_scan = None
    adding_to_library = 0
    lib_event_boxes = []
    lib_old_image = None
    lib_window_loaded = 0
    lib_window_is_open = 0
    lib_tables = []
    lib_select_timer = 0
    library_update_timer_id = None
    failed_to_open_file = 0
    info_box_timer_id = None
    slideshow_timer_id = None
    slideshow_started = False
    slideshow_stopped_by_mouse = False
    pil_font = ImageFont.load_default()
    lens_update_counter = 0
    window_width = 0
    window_height = 0
    colour_adjust_signal_kill = False
    colour_adjust_dialog_displayed = False
    
    def close_application(self, widget, event=None):
        
        ''' Catches termination events and closes the GTK main
        loop. Saves data to files. '''
        
        if self.file_exists:
            self.prefs['path to last file'] = self.path
        else:
            self.prefs['path to last file'] = ''
        self.prefs['page of last file'] = self.file_number
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        self.exit = True

        # =======================================================
        # Save preference data to ~/.comix/config with cPickle.
        # First it removes some data from self.prefs that should
        # not be saved depending on other prefs.
        # =======================================================
        
        # FIXME: The data that is never saved should not be a
        # part of self.prefs in the first place!
        del self.prefs['double page']
        del self.prefs['zoom scale']
        del self.prefs['zoom mode']
        del self.prefs['rotation']
        del self.prefs['flip horiz']
        del self.prefs['flip vert']
        del self.prefs['keep transformation']
        if not self.prefs['save saturation and contrast']:
            del self.prefs['saturation']
            del self.prefs['contrast']
            del self.prefs['brightness']
            del self.prefs['sharpness']
            del self.prefs['autocontrast']
        if not self.prefs['save window pos']:
            del self.prefs['window width']
            del self.prefs['window height']
            del self.prefs['window x']
            del self.prefs['window y']
            del self.prefs['fullscreen']
        if not os.path.exists(os.environ['HOME'] + '/.comix'):
            os.mkdir(os.environ['HOME'] + '/.comix')
        config = \
            open(os.path.join(os.environ['HOME'], '.comix/preferences_data'),
            'wb')
        os.chmod(os.path.join(os.environ['HOME'], '.comix/preferences_data'),
            0600)
        cPickle.dump(constants.version, config,
            protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(self.prefs, config, protocol=cPickle.HIGHEST_PROTOCOL)
        config.close()
        
        # =======================================================
        # Save bookmarks data to ~/.comix/bookmarks.
        # Each file path followed by a page number on the next row.
        # =======================================================
        bookmarks = \
            open(os.path.join(os.environ['HOME'], '.comix/bookmarks_data'),
            'wb')
        os.chmod(os.path.join(os.environ['HOME'], '.comix/bookmarks_data'),
            0600)
        cPickle.dump(self.bookmarks, bookmarks,
            protocol=cPickle.HIGHEST_PROTOCOL)
        cPickle.dump(self.bookmark_numbers, bookmarks,
            protocol=cPickle.HIGHEST_PROTOCOL)
        bookmarks.close()
        
        # =======================================================
        # Save recent files data to ~/.comix/recent_files.
        # =======================================================
        recent_files = \
            open(os.path.join(os.environ['HOME'], '.comix/recent_files_data'),
            'wb')
        os.chmod(os.path.join(os.environ['HOME'], '.comix/recent_files_data'),
            0600)
        cPickle.dump(self.recent_files, recent_files,
            protocol=cPickle.HIGHEST_PROTOCOL)
        recent_files.close()
        
        # =======================================================
        # We assure ourselves that there are no forgotten menu
        # thumbnails in the .comix/ directory. That might otherwise
        # happen if we have multiple Comix instances running with
        # different recent files/thumbnails data stored.
        # =======================================================
        if os.path.isdir(os.path.join(os.environ['HOME'],
            '.comix/menu_thumbnails')):
            hashes = []
            for stored in self.bookmarks + self.recent_files:
                uri = 'file://' + urllib.pathname2url(stored)
                hash = md5.new()
                hash.update(uri)
                hashes.append(hash.hexdigest())
            for thumb in os.listdir(os.path.join(os.environ['HOME'],
                '.comix/menu_thumbnails')):
                if thumb[:-4] not in hashes:
                    try:
                        os.remove(os.path.join(os.environ['HOME'],
                            '.comix/menu_thumbnails',  thumb))
                    except:
                        print 'Could not remove', thumb
            
        # =======================================================
        # Remove the temporary files directory, and if /tmp/comix
        # is empty (i.e. no other Comix instances are opened)
        # also remove /tmp/comix.
        # =======================================================
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        
        # =======================================================
        # Remove some legacy files in .comix/ that was used in
        # previous versions and that might still be present in
        # users home directories.
        # =======================================================
        if os.path.isdir(os.path.join(os.getenv('HOME'),
            '.comix/bookmark_thumbs')):
            shutil.rmtree(os.path.join(os.getenv('HOME'),
                '.comix/bookmark_thumbs'))
        if os.path.isfile(os.path.join(os.getenv('HOME'),
            '.comix/comixrc')):
            os.remove(os.path.join(os.getenv('HOME'),
                '.comix/comixrc'))
        if os.path.isfile(os.path.join(os.getenv('HOME'),
            '.comix/bookmarks')):
            os.remove(os.path.join(os.getenv('HOME'),
                '.comix/bookmarks'))
        if os.path.isfile(os.path.join(os.getenv('HOME'),
            '.comix/recent_files')):
            os.remove(os.path.join(os.getenv('HOME'),
                '.comix/recent_files'))
        if os.path.isfile(os.path.join(os.getenv('HOME'),
            '.comix/config')):
            os.remove(os.path.join(os.getenv('HOME'),
                '.comix/config'))

        if gtk.main_level():
            gtk.main_quit()
        else:
            sys.exit(0)
        return False
    
    def create_main_window(self):
        
        ''' Creates the main window and all its widgets. '''
        
        # =======================================================
        # Create main display area widgets.
        # =======================================================
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.realize()
        if self.prefs['save window pos']:
            self.window.move(self.prefs['window x'], self.prefs['window y'])
        self.window.set_size_request(300, 300)
        self.tooltips = gtk.Tooltips()
        self.image = gtk.Image()
        self.image2 = gtk.Image()

        self.comix_image = gtk.Image()
        if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(
            sys.argv[0])), 'images/logo/comix.svg')):
            icon_path = \
                os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])),
                'images/logo/comix.svg')
        else:
            for prefix in [os.path.dirname(os.path.dirname(sys.argv[0])),
                '/usr', '/usr/local', '/usr/X11R6']:
                icon_path = \
                    os.path.join(prefix,
                    'share/icons/hicolor/scalable/apps/comix.svg')
                if os.path.isfile(icon_path):
                    break
        try:
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file_at_size(icon_path, 300, 300)
            pixbuf_canvas = \
                gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 300, 300)
            pixbuf.composite(pixbuf_canvas, 0, 0, 300, 300, 0, 0, 1.0, 1.0,
                gtk.gdk.INTERP_NEAREST, 20)
            self.comix_image.set_from_pixbuf(pixbuf_canvas)
        except:
            pass

        self.image_box = gtk.HBox(False, 2)
        self.image_box.show()
        self.image_box.add(self.image)
        self.image_box.add(self.image2)
        self.comment_label = gtk.Label()
        label = gtk.Label()
        ebox = gtk.EventBox()
        self.slideshow_label_box = gtk.EventBox()
        ebox.set_border_width(4)
        self.slideshow_label_box.add(ebox)
        ebox.add(label)
        label.show()
        ebox.show()
        self.layout = gtk.Layout()
        self.layout.put(self.image_box, 0, 0)
        self.layout.put(self.comment_label, 0, 0)
        self.layout.put(self.slideshow_label_box, 0, 0)
        self.layout.put(self.comix_image, 0, 0)
        self.layout.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(
            gtk.gdk.Color(self.prefs['red bg'], self.prefs['green bg'],
            self.prefs['blue bg']), False, True))
        self.ui = -1
        self.actiongroup = gtk.ActionGroup('')
        self.recent_actiongroup = gtk.ActionGroup('')
        self.accelgroup = 0
        self.merge_id = -1
        self.toolbar = gtk.Toolbar()
        self.statusbar = gtk.Statusbar()
        
        # =======================================================
        # Create thumbnail sidebar widgets.
        # =======================================================
        self.thumb_liststore = gtk.ListStore(gtk.gdk.Pixbuf)
        self.thumb_tree_view = gtk.TreeView(self.thumb_liststore)
        self.thumb_column = gtk.TreeViewColumn(None)
        self.thumb_cell = gtk.CellRendererPixbuf()
        self.thumb_layout = gtk.Layout()
        self.thumb_layout.put(self.thumb_tree_view, 0, 0)
        self.thumb_tree_view.show()
        self.thumb_column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.thumb_column.set_fixed_width(self.prefs['thumbnail size'] + 7)
        self.thumb_tree_view.append_column(self.thumb_column)
        self.thumb_column.pack_start(self.thumb_cell, True)
        self.thumb_column.set_attributes(self.thumb_cell, pixbuf=0)
        self.thumb_layout.set_size_request(
            self.prefs['thumbnail size'] + 7, 0)
        self.thumb_tree_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.thumb_tree_view.set_headers_visible(False)
        self.thumb_vadjust = self.thumb_layout.get_vadjustment()
        self.thumb_vadjust.step_increment = 15
        self.thumb_vadjust.page_increment = 1
        self.thumb_vscroll = gtk.VScrollbar(None)
        self.thumb_vscroll.set_adjustment(self.thumb_vadjust)
        self.thumb_selection_handler = \
            self.thumb_tree_view.get_selection().connect(
            'changed', self.thumb_selection_event)
        
        # =======================================================
        # Create scrollbar widgets.
        # =======================================================
        self.vadjust = self.layout.get_vadjustment()
        self.hadjust = self.layout.get_hadjustment()
        self.vadjust.step_increment = 15
        self.vadjust.page_increment = 1
        self.hadjust.step_increment = 15
        self.hadjust.page_increment = 1
        self.hscroll = gtk.HScrollbar(None)
        self.hscroll.set_adjustment(self.hadjust)
        self.vscroll = gtk.VScrollbar(None)
        self.vscroll.set_adjustment(self.vadjust)
        
        # =======================================================
        # Create background tile used for transparent images.
        # =======================================================
        pil_image = Image.new('RGB', (16, 16), (99, 105, 99))
        draw = ImageDraw.Draw(pil_image)
        draw.rectangle([0, 0, 7, 7], fill=(148,154,148))
        draw.rectangle([8, 8, 16, 16], fill=(148,154,148))
        imagestr = pil_image.tostring()
        pixbuf_tiles = (gtk.gdk.pixbuf_new_from_data(imagestr,
            gtk.gdk.COLORSPACE_RGB, 0 , 8, 16, 16, 48))
        pixmap_tiles = gtk.gdk.Pixmap(self.window.window, 16, 16, -1)
        pixmap_tiles.draw_pixbuf(None, pixbuf_tiles, 0, 0, 0, 0, -1, -1,
            gtk.gdk.RGB_DITHER_MAX, 0, 0)
        self.gdk_gc = gtk.gdk.GC(pixmap_tiles, gtk.gdk.Color(0,0,0),
            gtk.gdk.Color(255,255,255), None, gtk.gdk.COPY,
            gtk.gdk.TILED, pixmap_tiles)
        
        # =======================================================
        # Create and add buttons to the toolbar.
        # =======================================================
        self.toolbutton_previous = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.toolbutton_next = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.toolbutton_first = gtk.ToolButton(gtk.STOCK_GOTO_FIRST)
        self.toolbutton_last = gtk.ToolButton(gtk.STOCK_GOTO_LAST)
        self.toolbutton_go = gtk.ToolButton(gtk.STOCK_JUMP_TO)
        
        self.toolbutton_fitscreen = \
            gtk.RadioToolButton(None, 'comix-fitscreen')
        self.toolbutton_fitscreen.set_label(_('Fit-to-screen mode'))
        self.toolbutton_fitwidth = \
            gtk.RadioToolButton(self.toolbutton_fitscreen, 'comix-fitwidth')
        self.toolbutton_fitwidth.set_label(_('Fit width mode'))
        self.toolbutton_fitheight = \
            gtk.RadioToolButton(self.toolbutton_fitwidth, 'comix-fitheight')
        self.toolbutton_fitheight.set_label(_('Fit height mode'))
        self.toolbutton_fitnone = \
            gtk.RadioToolButton(self.toolbutton_fitheight, 'comix-fitnone')
        self.toolbutton_fitnone.set_label(_('Manual zoom mode'))
        self.toolbutton_double_page = \
            gtk.ToggleToolButton('comix-double-page')
        self.toolbutton_double_page.set_label(_('Double page mode'))
        self.toolbutton_manga = gtk.ToggleToolButton('comix-manga')
        self.toolbutton_manga.set_label(_('Manga mode'))
        self.toolbutton_lens = gtk.ToggleToolButton('comix-lens')
        self.toolbutton_lens.set_label(_('Magnifying lens'))
        
        self.toolbutton_first.connect_object("clicked", self.first_page, None)
        self.toolbar.insert(self.toolbutton_first, -1)
        self.toolbutton_first.show()
        self.toolbutton_previous.connect_object("clicked", self.previous_page,
            None)
        self.toolbar.insert(self.toolbutton_previous, -1)
        self.toolbutton_previous.show()
        self.toolbutton_next.connect_object("clicked", self.next_page, None)
        self.toolbar.insert(self.toolbutton_next, -1)
        self.toolbutton_next.show()
        self.toolbutton_last.connect_object("clicked", self.last_page, None)
        self.toolbar.insert(self.toolbutton_last, -1)
        self.toolbutton_last.show()

        sep = gtk.SeparatorToolItem()
        self.toolbar.insert(sep, -1)
        sep.show()

        self.toolbutton_go.connect_object("clicked",
            self.go_to_page_dialog_open, None)
        self.toolbar.insert(self.toolbutton_go, -1)
        self.toolbutton_go.show()
        item = gtk.ToolItem()
        item.show()
        item.set_expand(True)
        self.toolbar.insert(item, -1)

        self.toolbutton_fitscreen.connect_object("clicked", 
            self.zoom_mode_switch_tool, 1)
        self.toolbar.insert(self.toolbutton_fitscreen, -1)
        self.toolbutton_fitscreen.show()
        self.toolbutton_fitwidth.connect_object("clicked", 
            self.zoom_mode_switch_tool, 2)
        self.toolbar.insert(self.toolbutton_fitwidth, -1)
        self.toolbutton_fitwidth.show()
        self.toolbutton_fitheight.connect_object("clicked", 
            self.zoom_mode_switch_tool, 3)
        self.toolbar.insert(self.toolbutton_fitheight, -1)
        self.toolbutton_fitheight.show()
        self.toolbutton_fitnone.connect_object("clicked", 
            self.zoom_mode_switch_tool, 0)
        self.toolbar.insert(self.toolbutton_fitnone, -1)
        self.toolbutton_fitnone.show()

        sep = gtk.SeparatorToolItem()
        self.toolbar.insert(sep, -1)
        sep.show()

        self.toolbutton_double_page.connect_object("clicked", 
            self.double_page_switch_tool, None)
        self.toolbar.insert(self.toolbutton_double_page, -1)
        self.toolbutton_double_page.show()
        self.toolbutton_manga.connect_object("clicked", 
            self.manga_mode_switch_tool, None)
        self.toolbar.insert(self.toolbutton_manga, -1)
        self.toolbutton_manga.show()

        sep = gtk.SeparatorToolItem()
        self.toolbar.insert(sep, -1)
        sep.show()

        self.toolbutton_lens.connect_object("clicked", 
            self.lens_switch_tool, None)
        self.toolbar.insert(self.toolbutton_lens, -1)
        self.toolbutton_lens.show()
                
        # Needed unless space key should activate buttons
        self.toolbar.set_focus_child(self.toolbutton_next)
        
        # =======================================================
        # Attach widgets to the main table.
        # =======================================================
        self.table = gtk.Table(2, 2, False)
        self.table.attach(self.thumb_layout, 0, 1, 2, 5, gtk.FILL,
            gtk.FILL|gtk.EXPAND, 0, 0)
        self.table.attach(self.thumb_vscroll, 1, 2, 2, 4, gtk.FILL|gtk.SHRINK,
            gtk.FILL|gtk.SHRINK, 0, 0)
        self.table.attach(self.layout, 2, 3, 2, 3, gtk.FILL|gtk.EXPAND,
            gtk.FILL|gtk.EXPAND, 0, 0)
        self.table.attach(self.vscroll, 3, 4, 2, 3, gtk.FILL|gtk.SHRINK,
            gtk.FILL|gtk.SHRINK, 0, 0)
        self.table.attach(self.hscroll, 2, 3, 4, 5, gtk.FILL|gtk.SHRINK,
            gtk.FILL|gtk.SHRINK, 0, 0)
        self.table.attach(self.toolbar, 0, 4, 1, 2, gtk.FILL|gtk.SHRINK,
            gtk.FILL|gtk.SHRINK, 0, 0)
        self.table.attach(self.statusbar, 0, 4, 5, 6, gtk.FILL|gtk.SHRINK,
            gtk.FILL|gtk.SHRINK, 0, 0)
        self.window.add(self.table)
        self.table.show()
        self.layout.show()
    
    def create_library_window(self):
        
        ''' Creates the library window and all its widgets. '''
        
        # =======================================================
        # Create widgets.
        # =======================================================
        self.lib_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.lib_window.set_title(_('Library'))
        self.window.realize()
        self.lib_cover_name = gtk.Label()
        self.lib_cover_name.set_alignment(0, 0.5)
        self.lib_cover_pages = gtk.Label()
        self.lib_cover_pages.set_alignment(0, 0.5)
        self.lib_cover_type = gtk.Label()
        self.lib_cover_type.set_alignment(0, 0.5)
        self.lib_cover_size = gtk.Label()
        self.lib_cover_size.set_alignment(0, 0.5)
        vbox = gtk.VBox(False, 4)
        vbox.set_border_width(6)
        vbox.pack_start(self.lib_cover_name, False, False, 2)
        vbox.pack_start(self.lib_cover_pages, False, False, 2)
        vbox.pack_start(self.lib_cover_type, False, False, 2)
        vbox.pack_start(self.lib_cover_size, False, False, 2)
        vbox.set_border_width(10)
        ebox = gtk.EventBox()
        ebox.set_border_width(1)
        cmap = ebox.get_colormap()
        ebox.modify_bg(gtk.STATE_NORMAL, cmap.alloc_color('#eadfc6'))
        ebox.add(vbox)
        ebox2 = gtk.EventBox()
        ebox2.modify_bg(gtk.STATE_NORMAL, cmap.alloc_color('#888888'))
        ebox2.add(ebox)
        
        self.lib_search_box = gtk.Entry()
        self.lib_search_box.connect(
            'activate', self.library_update)
        
        self.button_reg_expr = gtk.CheckButton(_("Apply filter on full path"))
        self.button_reg_expr.connect("toggled",
            self.reg_expr_full_path_switch)
        
        hbox = gtk.HBox(True, 0)
        button = gtk.Button(stock=gtk.STOCK_ADD)
        self.tooltips.set_tip(button, _("Add archives to library."))
        button.connect_object("clicked", self.library_add, None, None)
        hbox.pack_start(button, False, True, 0)
        self.lib_remove_button = gtk.Button(stock=gtk.STOCK_DELETE)
        self.tooltips.set_tip(self.lib_remove_button,
            _("Remove selected archive from library."))
        self.lib_remove_button.connect_object(
            "clicked", self.library_remove, None, None)
        hbox.pack_start(self.lib_remove_button, False, True, 0)
        button = gtk.Button(_("Clean up"), None)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,
            gtk.ICON_SIZE_SMALL_TOOLBAR))
        self.tooltips.set_tip(
            button, _("Remove orphaned or outdated library entries."))
        button.connect_object("clicked", self.library_clean_up, None, None)
        hbox.pack_start(button, False, True, 0)
        button = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.tooltips.set_tip(button, _("Close this window."))
        button.connect_object("clicked", self.library_close, None, None)
        hbox.pack_start(button, False, True, 0)
        self.lib_open_button = gtk.Button(stock=gtk.STOCK_OPEN)
        self.tooltips.set_tip(self.lib_open_button,
            _("Open selected archive."))
        self.lib_open_button.connect_object(
            "clicked", self.library_open, None, None)
        hbox.pack_start(self.lib_open_button, False, True, 0)
        
        self.lib_layout = gtk.Layout()
        self.lib_layout.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(gtk.gdk.Color(0, 0, 0),
            False, True))
        self.lib_window.resize(self.prefs['lib window width'],
            self.prefs['lib window height'])
        
        # =======================================================
        # Put everything together.
        # =======================================================
        self.lib_vadjust = self.lib_layout.get_vadjustment()
        self.lib_vadjust.step_increment = 15
        self.lib_vadjust.page_increment = 1
        self.lib_vscroll = gtk.VScrollbar(None)
        self.lib_vscroll.set_adjustment(self.lib_vadjust)
        
        self.lib_cover_table_s = gtk.Table(2, 2, False)
        self.lib_cover_table_s.attach(self.lib_layout, 0, 1, 0, 1,
            gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
        self.lib_cover_table_s.attach(self.lib_vscroll, 1, 2, 0, 1,
            gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK, 0, 0)
        
        info_box = gtk.VBox(False, 5)
        info_box.pack_start(self.lib_search_box, False, False, 4)
        info_box.pack_start(self.button_reg_expr, False, False, 2)
        info_box.pack_start(gtk.Label(), False, False, 0)
        info_box.pack_start(hbox, True, True, 4)
        
        self.lib_info_table = gtk.Table(2, 2, False)
        self.lib_info_table.set_homogeneous(False)
        self.lib_info_table.attach(ebox2, 0, 1, 0, 3, gtk.FILL|gtk.EXPAND,
            gtk.FILL|gtk.EXPAND, 10, 15)
        self.lib_info_table.attach(
            info_box, 1, 2, 0, 1, gtk.FILL, gtk.FILL, 5, 10)
        self.lib_info_table.set_row_spacing(2, 50)
        
        self.lib_table = gtk.Table(2, 2, False)
        self.lib_table.attach(self.lib_cover_table_s, 0, 1, 0, 1,
            gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
        self.lib_table.attach(self.lib_info_table, 0, 1, 1, 2,
            gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK, 0, 0)
        self.lib_table.show_all()
        self.lib_window.add(self.lib_table)
    
    def create_open_dialog(self):
        
        ''' Creates the dialog both for the standard "Open" function and
        for the add feature of the library. '''
        
        # =======================================================
        # Create the "Open" dialog.
        # =======================================================
        self.file_select = gtk.FileChooserDialog(title=_("Open"),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        self.file_select.set_default_response(gtk.RESPONSE_OK)
        self.file_select_preview_box = gtk.VBox(False, 2)
        self.file_select_preview_box.set_size_request(130, 0)
        self.file_select_preview_box.show()
        self.file_select.set_preview_widget(self.file_select_preview_box)
        self.file_select.set_use_preview_label(False)
        filter = gtk.FileFilter()
        filter.add_pattern('*')
        filter.set_name(_('All files'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/jpeg')
        filter.add_mime_type('image/png')
        filter.add_mime_type('image/gif')
        filter.add_mime_type('image/tiff')
        filter.add_mime_type('image/bmp')
        filter.add_mime_type('image/x-icon')
        filter.add_mime_type('image/x-xpixmap')
        filter.add_mime_type('image/x-xbitmap')
        filter.set_name(_('All images'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('application/x-zip')
        filter.add_mime_type('application/zip')
        filter.add_mime_type('application/x-rar')
        filter.add_mime_type('application/x-tar')
        filter.add_mime_type('application/x-gzip')
        filter.add_mime_type('application/x-bzip2')
        filter.add_mime_type('application/x-cbz')
        filter.add_mime_type('application/x-cbr')
        filter.add_mime_type('application/x-cbt')
        filter.set_name(_('All archives'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/jpeg')
        filter.set_name(_('JPEG image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/png')
        filter.set_name(_('PNG image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/gif')
        filter.set_name(_('GIF image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/tiff')
        filter.set_name(_('TIFF image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/bmp')
        filter.set_name(_('BMP image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/x-icon')
        filter.set_name(_('ICO image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/x-xpixmap')
        filter.set_name(_('XPM image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('image/x-xbitmap')
        filter.set_name(_('XBM image'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('application/x-zip')
        filter.add_mime_type('application/zip')
        filter.add_mime_type('application/x-cbz')
        filter.set_name(_('ZIP archive'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('application/x-rar')
        filter.add_mime_type('application/x-cbr')
        filter.set_name(_('RAR archive'))
        self.file_select.add_filter(filter)
        filter = gtk.FileFilter()
        filter.add_mime_type('application/x-tar')
        filter.add_mime_type('application/x-gzip')
        filter.add_mime_type('application/x-bzip2')
        filter.add_mime_type('application/x-cbt')
        filter.set_name(_('tar archive'))
        self.file_select.add_filter(filter)
        
        self.lib_add_recursive_toggle = \
            gtk.CheckButton(_('Add archives recursively'))
        self.file_select.set_extra_widget(self.lib_add_recursive_toggle)
        self.lib_add_recursive_toggle.connect('toggled',
            self.library_add_recursive_switch)

        self.file_select.set_transient_for(self.window)
    
    def create_preferences_dialog(self):
        
        ''' Creates the preferences dialog and all its widgets. '''
        
        # =======================================================
        # Create all publically available widgets.
        # =======================================================
        self.preferences_dialog = \
            gtk.Dialog(_("Preferences"), self.window, 0,())
        self.preferences_dialog.set_has_separator(False)
        self.preferences_dialog.set_resizable(False)
        self.preferences_dialog.action_area.set_size_request(0, 0)
        self.notebook = gtk.Notebook()
        self.select_default_folder_dialog = \
            gtk.FileChooserDialog(_("Select folder"), self.window,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.button_fullscreen = gtk.CheckButton(_("Fullscreen as default"))
        self.button_page = gtk.CheckButton(_("Double page mode as default"))
        self.button_stretch = \
            gtk.CheckButton(_("Stretch small images"))
        self.button_smart_scale = \
            gtk.CheckButton(_("Use smart scaling in double page mode"))
        self.button_comment = \
            gtk.CheckButton(_("Always view comments when opening a new file"))
        self.button_hide_bars = \
            gtk.CheckButton(
            _("Hide menubar, scrollbars etc. in fullscreen mode"))
        self.button_cache_next = \
            gtk.CheckButton(_("Cache pages for faster forward flipping"))
        self.button_scroll_horiz = \
            gtk.CheckButton(
            _("Scroll wheel scrolls horizontally at top and bottom of page"))
        self.button_scroll_flips = \
            gtk.CheckButton(
            _("Flip page when scrolling off the top or bottom of page"))
        self.button_thumb_scroll = \
            gtk.CheckButton(_("Hide thumbnail scrollbar"))
        self.button_smart_space = \
            gtk.CheckButton(_("Space key uses smart scrolling"))
        self.button_save_size = \
            gtk.CheckButton(
            _("Save window position and size for future sessions"))
        self.button_next_archive = \
            gtk.CheckButton(
            _("Go to the next archive in directory after last page"))
        self.button_hide_cursor = \
            gtk.CheckButton(_("Hide cursor in fullscreen mode"))
        self.button_open_last = \
            gtk.CheckButton(_("Open last viewed file on start"))
        self.button_show_pagenumber = \
            gtk.CheckButton(_("Show page numbers on thumbnails"))
        self.button_fake_double = \
            gtk.CheckButton(
            _("Always use smart scrolling as if in double page mode"))
        self.button_cache_thumbs = \
            gtk.CheckButton(
            _("Use stored thumbnails for images in directories"))
        self.button_cache_arch_thumbs = \
            gtk.CheckButton(_("Use stored thumbnails for images in archives"))
        self.button_two_page_scans = \
            gtk.CheckButton(
            _("Display only one page in double page mode if the image is wide"))
        self.button_store_recent = \
            gtk.CheckButton(
            _("Store recently opened files"))
        self.button_default_path = \
            gtk.RadioButton(None,
            _('Always go to this directory in the "Open" dialog:'))
        self.button_latest_path = \
            gtk.RadioButton(self.button_default_path,
            _('Always go to the latest directory in the "Open" dialog'))
        self.colorbutton = gtk.ColorButton(color=gtk.gdk.Color(0,0,0))
        self.button_lens_zoom = \
            gtk.SpinButton(gtk.Adjustment(2.0, 1.01, 5, 0.01, 0.01,
            page_size=0), climb_rate=0.0, digits=2)
        self.button_lens_size = \
            gtk.SpinButton(gtk.Adjustment(150, 20, 300, 1, 1, page_size=0),
            climb_rate=0.0, digits=0)
        self.button_lens_update = \
            gtk.SpinButton(gtk.Adjustment(30, 0, 150, 1, 1, page_size=0),
            climb_rate=0.0, digits=0)
        self.button_thumb_size = \
            gtk.SpinButton(gtk.Adjustment(1, 20, 128, 1, 1, page_size=0),
            climb_rate=0.0, digits=0)
        self.button_lib_thumb_size = \
            gtk.SpinButton(gtk.Adjustment(1, 20, 128, 1, 1, page_size=0),
            climb_rate=0.0, digits=0)
        self.button_slideshow_delay = \
            gtk.SpinButton(gtk.Adjustment(6.0, 1.0, 300.0, 0.1, 0.1,
            page_size=0), climb_rate=0.0, digits=1)
        self.spin_space_scroll = \
            gtk.SpinButton(gtk.Adjustment(100, 1, 100, 1, 1,
            page_size=0), climb_rate=1, digits=0)
        self.button_1 = \
            gtk.RadioButton(None, _('Nearest (quickest, worst quality)'))
        self.button_2 = gtk.RadioButton(self.button_1, _("Tiles"))
        self.button_3 = gtk.RadioButton(self.button_2, _("Bilinear"))
        self.button_4 = \
            gtk.RadioButton(self.button_3, _('Hyper (slowest, best quality)'))
        self.button_fit_manual_default = \
            gtk.RadioButton(None, _('Manual zoom mode as default'))
        self.button_fit_screen_default = \
            gtk.RadioButton(self.button_fit_manual_default,
            _('Fit-to-screen mode as default'))
        self.button_fit_width_default = \
            gtk.RadioButton(self.button_fit_screen_default,
            _('Fit width mode as default'))
        self.button_fit_height_default = \
            gtk.RadioButton(self.button_fit_width_default,
            _('Fit height mode as default'))
        self.comment_extensions_entry = gtk.Entry(max=100)
        self.button_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        self.filechooser_button = gtk.Button()
        self.combobox_tool = gtk.combo_box_new_text()
        self.combo_space_scroll = gtk.combo_box_new_text()
        box = gtk.VBox(False, 0)
        box.set_border_width(1)
        self.preferences_dialog.vbox.pack_start(box, False, False, 2)
        box.pack_start(self.notebook, False, False, 2)
        
        # =======================================================
        # Put the display tab together.
        # =======================================================
        vbox_display = gtk.VBox(False, 5)
        vbox_display.set_border_width(12)
        hbox = gtk.HBox(False, 0)
        vbox_display.pack_start(hbox, False, False, 0)
        label_box = gtk.VBox(False, 0)
        entry_box = gtk.VBox(False, 0)
        hbox.pack_start(label_box, True, True, 0)
        hbox.pack_start(entry_box, True, True, 0)
        
        label = gtk.Label(_("Background colour:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, False, 0)
        self.colorbutton.set_title(_("Background colour"))
        entry_box.pack_start(self.colorbutton, True, True, 2)
        label = gtk.Label(_("Toolbar button labels:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.combobox_tool, True, True, 2)
        self.combobox_tool.append_text(_('Icons only'))
        self.combobox_tool.append_text(_('Text only'))
        self.combobox_tool.append_text(_('Icons and text'))
        label = gtk.Label(_('Slideshow delay:'))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_slideshow_delay, True, True, 2)
        
        label = gtk.Label("")
        label.set_alignment(0, 0)
        vbox_display.pack_start(label, False, False, 0)
        
        self.button_hide_cursor.connect("toggled",
            self.preferences_dialog_change_settings, 15)
        vbox_display.pack_start(self.button_hide_cursor, False, False, 2)
        self.button_hide_bars.connect("toggled",
            self.preferences_dialog_change_settings, 12)
        vbox_display.pack_start(self.button_hide_bars, False, False, 2)
        
        self.notebook.insert_page(vbox_display, gtk.Label(_("Display")))
        
        # =======================================================
        # Put the behaviour tab together.
        # =======================================================
        vbox = gtk.VBox(False, 5)
        vbox.set_border_width(12)
        
        self.button_fullscreen.connect("toggled",
            self.preferences_dialog_change_settings, 0)
        vbox.pack_start(self.button_fullscreen, False, False, 2)
        self.button_page.connect("toggled",
            self.preferences_dialog_change_settings, 1)
        vbox.pack_start(self.button_page, False, False, 2)
        self.button_save_size.connect("toggled",
            self.preferences_dialog_change_settings, 10)
        vbox.pack_start(self.button_save_size, False, False, 2)
        self.button_open_last.connect("toggled",
            self.preferences_dialog_change_settings, 21)
        vbox.pack_start(self.button_open_last, False, False, 2)
        self.button_cache_next.connect("toggled",
            self.preferences_dialog_change_settings, 7)
        vbox.pack_start(self.button_cache_next, False, False, 2)
        self.button_two_page_scans.connect("toggled",
            self.preferences_dialog_change_settings, 30)
        vbox.pack_start(self.button_two_page_scans, False, False, 2)
        self.button_store_recent.connect("toggled",
            self.preferences_dialog_change_settings, 31)
        vbox.pack_start(self.button_store_recent, False, False, 2)
        
        label = gtk.Label('')
        label.set_alignment(0, 0)
        vbox.pack_start(label, False, False, 0)
        
        self.button_default_path.connect("toggled",
            self.preferences_dialog_change_settings, 22)
        vbox.pack_start(self.button_default_path, False, False, 2)
        
        hbox = gtk.HBox(False, 2)
        vbox.pack_start(hbox, False, False, 0)
        padding_box = gtk.VBox(False, 0)
        padding_box.set_border_width(10)
        hbox.pack_start(padding_box, False, False, 0)
        filechooser_box = gtk.VBox(False, 0)
        hbox.pack_start(filechooser_box, True, True, 0)
        
        self.filechooser_button.connect_object("clicked",
            self.default_folder_chooser_dialog_open, None)
        self.filechooser_button.set_use_underline(False)
        filechooser_box.pack_start(self.filechooser_button, False, True, 0)
        self.button_latest_path.connect("toggled",
            self.preferences_dialog_change_settings, 23)
        vbox.pack_start(self.button_latest_path, False, False, 2)
        
        self.notebook.insert_page(vbox, gtk.Label(_("Behaviour")))
        
        # =======================================================
        # Put the scaling tab together.
        # =======================================================
        vbox_scaling = gtk.VBox(False, 5)
        vbox_scaling.set_border_width(12)
        
        self.button_fit_manual_default.connect('toggled',
            self.preferences_dialog_change_settings, 32)
        vbox_scaling.pack_start(self.button_fit_manual_default, False,
            False, 2)
        self.button_fit_screen_default.connect('toggled',
            self.preferences_dialog_change_settings, 33)
        vbox_scaling.pack_start(self.button_fit_screen_default, False,
            False, 2)
        self.button_fit_width_default.connect('toggled',
            self.preferences_dialog_change_settings, 34)
        vbox_scaling.pack_start(self.button_fit_width_default, False,
            False, 2)
        self.button_fit_height_default.connect('toggled',
            self.preferences_dialog_change_settings, 35)
        vbox_scaling.pack_start(self.button_fit_height_default, False,
            False, 2)
            
        label = gtk.Label('')
        label.set_alignment(0, 0)
        vbox_scaling.pack_start(label, False, False, 0)
        
        self.button_stretch.connect("toggled",
            self.preferences_dialog_change_settings, 9)
        vbox_scaling.pack_start(self.button_stretch, False, False, 2)
        self.button_smart_scale.connect("toggled",
            self.preferences_dialog_change_settings, 19)
        vbox_scaling.pack_start(self.button_smart_scale, False, False, 2)
        
        label = gtk.Label()
        label.set_markup('\n<b>' + _('Scaling quality') + '</b>\n')
        label.set_alignment(0, 0)
        vbox_scaling.pack_start(label, False, False, 0)
        
        hbox = gtk.HBox(False, 2)
        vbox_scaling.pack_start(hbox, False, False, 0)
        padding_box = gtk.VBox(False, 0)
        padding_box.set_border_width(10)
        hbox.pack_start(padding_box, False, False, 0)
        button_box = gtk.VBox(True, 5)
        hbox.pack_start(button_box, True, True, 0)
        
        self.button_1.connect("toggled",
            self.preferences_dialog_change_settings, 2)
        button_box.pack_start(self.button_1, False, False, 2)
        self.button_2.connect("toggled",
            self.preferences_dialog_change_settings, 3)
        button_box.pack_start(self.button_2, False, False, 2)
        self.button_3.connect("toggled",
            self.preferences_dialog_change_settings, 4)
        button_box.pack_start(self.button_3, False, False, 2)
        self.button_4.connect("toggled",
            self.preferences_dialog_change_settings, 5)
        button_box.pack_start(self.button_4, False, False, 2)
        
        self.notebook.insert_page(vbox_scaling, gtk.Label(_("Scaling")))
        
        # =======================================================
        # Put the comments tab together.
        # =======================================================
        vbox_comments = gtk.VBox(False, 5)
        vbox_comments.set_border_width(12)
        
        self.button_comment.connect("toggled",
            self.preferences_dialog_change_settings, 16)
        vbox_comments.pack_start(self.button_comment, False, False, 2)
        
        label = \
            gtk.Label('\n' +
            _('Treat files with the following extensions as comments:'))
        label.set_alignment(0, 0)
        vbox_comments.pack_start(label, False, False, 0)
        vbox_comments.pack_start(self.comment_extensions_entry, False, False,
            0)
        
        self.notebook.insert_page(vbox_comments, gtk.Label(_("Comments")))
        
        # =======================================================
        # Put the scroll tab together.
        # =======================================================
        vbox_scroll = gtk.VBox(False, 5)
        vbox_scroll.set_border_width(12)
        
        self.button_next_archive.connect("toggled",
            self.preferences_dialog_change_settings, 14)
        vbox_scroll.pack_start(self.button_next_archive, False, False, 2)
        self.button_scroll_horiz.connect("toggled",
            self.preferences_dialog_change_settings, 17)
        vbox_scroll.pack_start(self.button_scroll_horiz, False, False, 2)
        self.button_scroll_flips.connect("toggled",
            self.preferences_dialog_change_settings, 18)
        vbox_scroll.pack_start(self.button_scroll_flips, False, False, 2)
        self.button_smart_space.connect("toggled",
            self.preferences_dialog_change_settings, 13)
        vbox_scroll.pack_start(self.button_smart_space, False, False, 2)
        self.button_fake_double.connect("toggled",
            self.preferences_dialog_change_settings, 27)
        vbox_scroll.pack_start(self.button_fake_double, False, False, 2)
        hbox = gtk.HBox(False, 2)
        vbox_scroll.pack_start(hbox, False, False, 2)
        label = gtk.Label(_('Space key scrolls'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, False, False, 2)
        hbox.pack_start(self.spin_space_scroll, False, False, 2)
        label = gtk.Label('% ' + _('of'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, False, False, 2)
        hbox.pack_start(self.combo_space_scroll, False, False, 2)
        self.combo_space_scroll.append_text(_('Window size'))
        self.combo_space_scroll.append_text(_('Page size'))

        self.notebook.insert_page(vbox_scroll, gtk.Label(_("Scroll")))
        
        # =======================================================
        # Put the lens tab together.
        # =======================================================
        vbox_lens = gtk.VBox(False, 5)
        vbox_lens.set_border_width(12)
        hbox = gtk.HBox(False, 0)
        vbox_lens.pack_start(hbox, False, False, 0)
        label_box = gtk.VBox(False, 0)
        entry_box = gtk.VBox(False, 0)
        hbox.pack_start(label_box, True, True, 0)
        hbox.pack_start(entry_box, True, True, 0)
        
        label = gtk.Label(_("Magnification factor:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_lens_zoom, True, True, 2)
        label = gtk.Label(_("Lens size (px):"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_lens_size, True, True, 2)
        label = gtk.Label(_("Update interval (milliseconds):"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_lens_update, True, True, 2)
        
        self.notebook.insert_page(vbox_lens, gtk.Label(_("Lens")))
        
        # =======================================================
        # Put the thumbnails tab together.
        # =======================================================
        vbox_thumbs = gtk.VBox(False, 5)
        vbox_thumbs.set_border_width(12)
        hbox = gtk.HBox(False, 0)
        vbox_thumbs.pack_start(hbox, False, False, 0)
        label_box = gtk.VBox(False, 0)
        entry_box = gtk.VBox(False, 0)
        hbox.pack_start(label_box, True, True, 0)
        hbox.pack_start(entry_box, True, True, 0)
        
        label = gtk.Label(_("Thumbnail sizes (px):"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_thumb_size, True, True, 2)
        
        label = gtk.Label(_("Library thumbnail sizes (px):"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(self.button_lib_thumb_size, True, True, 2)
        
        self.button_thumb_scroll.connect("toggled",
            self.preferences_dialog_change_settings, 20)
        vbox_thumbs.pack_start(self.button_thumb_scroll, False, False, 2)
        self.button_show_pagenumber.connect("toggled",
            self.preferences_dialog_change_settings, 25)
        vbox_thumbs.pack_start(self.button_show_pagenumber, False, False, 2)
        self.button_cache_thumbs.connect("toggled",
            self.preferences_dialog_change_settings, 28)
        vbox_thumbs.pack_start(self.button_cache_thumbs, False, False, 2)
        self.button_cache_arch_thumbs.connect("toggled",
            self.preferences_dialog_change_settings, 29)
        vbox_thumbs.pack_start(self.button_cache_arch_thumbs, False, False, 2)
        
        self.notebook.insert_page(vbox_thumbs, gtk.Label(_("Thumbnails")))
        
        # =======================================================
        # Add dialog buttons.
        # =======================================================
        hbox = gtk.HBox(True, 0)
        self.preferences_dialog.vbox.pack_start(hbox, False, False, 0)
        
        self.button_apply.connect_object("clicked",
            self.preferences_dialog_save_and_close, None)
        hbox.pack_start(self.button_apply, False, True, 0)
        alignment = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
        hbox.pack_start(alignment, True, True, 0)
        button = gtk.Button(stock=gtk.STOCK_CANCEL)
        button.connect_object("clicked", self.preferences_dialog_close,
            None, None)
        hbox.pack_start(button, False, True, 0)
        button = gtk.Button(stock=gtk.STOCK_OK)
        button.connect_object("clicked",
            self.preferences_dialog_save_and_close, 'close')
        hbox.pack_start(button, False, True, 0)
        
        self.preferences_dialog.vbox.show_all()
    
    def create_colour_adjust_dialog(self):
        
        ''' Creates the colour adjustment dialog and all its widgets. '''
        
        self.colour_adjust_dialog = \
            gtk.Dialog(_('Adjust colour'), self.window, False,)
        self.colour_adjust_dialog.add_buttons(
            _('Default'), gtk.RESPONSE_NO,
            gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.colour_adjust_dialog.set_resizable(False)
        self.colour_adjust_dialog.set_has_separator(False)
        
        vbox = gtk.VBox(False, 10)
        vbox.set_border_width(10)
        self.colour_adjust_dialog.vbox.add(vbox)
        
        self.colour_adjust_histogram = gtk.Image()
        vbox.pack_start(self.colour_adjust_histogram, True, True, 2)
        
        vbox.pack_start(gtk.HSeparator())

        hbox = gtk.HBox(False, 10)
        vbox.pack_start(hbox, False, False, 2)
        vbox_left = gtk.VBox(False, 10)
        vbox_right = gtk.VBox(False, 10)
        vbox_right.set_size_request(230, -1)
        hbox.pack_start(vbox_left, False, False, 2)
        hbox.pack_start(vbox_right, True, True, 2)

        label = gtk.Label(_('Brightness') + ':')
        label.set_alignment(1, 0.5)
        vbox_left.pack_start(label, True, False, 2)
        adj = gtk.Adjustment(1.0, 0, 2.0, 0.01, 0.1)
        self.brightness_scale = gtk.HScale(adj)
        self.brightness_scale.set_digits(2)
        self.brightness_scale.set_value_pos(gtk.POS_RIGHT)
        self.brightness_scale.connect('value-changed',
            self.colour_adjust_change_value, 'brightness')
        self.brightness_scale.set_update_policy(gtk.UPDATE_DELAYED)
        vbox_right.pack_start(self.brightness_scale, True, False, 2)

        label = gtk.Label(_('Contrast') + ':')
        label.set_alignment(1, 0.5)
        vbox_left.pack_start(label, True, False, 2)
        adj = gtk.Adjustment(1.0, 0, 2.0, 0.01, 0.1)
        self.contrast_scale = gtk.HScale(adj)
        self.contrast_scale.set_digits(2)
        self.contrast_scale.set_value_pos(gtk.POS_RIGHT)
        self.contrast_scale.connect('value-changed',
            self.colour_adjust_change_value, 'contrast')
        self.contrast_scale.set_update_policy(gtk.UPDATE_DELAYED)
        vbox_right.pack_start(self.contrast_scale, True, False, 2)

        label = gtk.Label(_('Saturation') + ':')
        label.set_alignment(1, 0.5)
        vbox_left.pack_start(label, True, False, 2)
        adj = gtk.Adjustment(1.0, 0, 2.0, 0.01, 0.1)
        self.saturation_scale = gtk.HScale(adj)
        self.saturation_scale.set_digits(2)
        self.saturation_scale.set_value_pos(gtk.POS_RIGHT)
        self.saturation_scale.connect('value-changed',
            self.colour_adjust_change_value, 'saturation')
        self.saturation_scale.set_update_policy(gtk.UPDATE_DELAYED)
        vbox_right.pack_start(self.saturation_scale, True, False, 2)

        label = gtk.Label(_('Sharpness') + ':')
        label.set_alignment(1, 0.5)
        vbox_left.pack_start(label, True, False, 2)
        adj = gtk.Adjustment(1.0, 0, 2.0, 0.01, 0.1)
        self.sharpness_scale = gtk.HScale(adj)
        self.sharpness_scale.set_digits(2)
        self.sharpness_scale.set_value_pos(gtk.POS_RIGHT)
        self.sharpness_scale.connect('value-changed',
            self.colour_adjust_change_value, 'sharpness')
        self.sharpness_scale.set_update_policy(gtk.UPDATE_DELAYED)
        vbox_right.pack_start(self.sharpness_scale, True, False, 2)
        
        vbox.pack_start(gtk.HSeparator())
        
        self.button_autocontrast = \
            gtk.CheckButton(_('Automatically adjust contrast'))
        vbox.pack_start(self.button_autocontrast, False, False, 2)
        self.button_autocontrast.connect("toggled",
            self.colour_adjust_change_value, 'autocontrast')

        self.button_save_satcon = \
            gtk.CheckButton(
            _('Save values for future sessions'))
        vbox.pack_start(self.button_save_satcon, False, False, 2)
        self.button_save_satcon.connect("toggled",
            self.colour_adjust_change_value, 'save')     

        self.colour_adjust_dialog.vbox.show_all()

    def create_properties_dialog(self):
        
        ''' Creates the properties dialog and all its widgets. '''
        
        self.properties_dialog = \
            (gtk.Dialog(_("Properties"), self.window, 0, (gtk.STOCK_CLOSE,
            gtk.RESPONSE_CLOSE)))
        self.properties_dialog.set_resizable(False)
        self.properties_label = gtk.Label()
        self.properties_label2 = gtk.Label()
        self.properties_notebook = gtk.Notebook()
        self.properties_dialog.vbox.pack_start(
            self.properties_notebook, False, False, 0)
        
        self.properties_dialog.set_has_separator(False)
        self.properties_label.set_justify(gtk.JUSTIFY_RIGHT)
        self.properties_dialog.vbox.show_all()
    
    def create_go_to_page_dialog(self):
        
        ''' Creates the go-to-page dialog and all its widgets. '''
        
        self.go_to_page_dialog = \
            gtk.Dialog(_("Go to page"), self.window, 0, (gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.go_to_page_dialog.set_resizable(False)
        self.go_to_page_dialog.set_default_response(gtk.RESPONSE_OK)
        self.button_page_spin = \
            gtk.SpinButton(gtk.Adjustment(1, 1, 1000, 1, 1, page_size=0),
            climb_rate=0.0, digits=0)
        self.button_page_spin.connect('activate',
            self.go_to_page_dialog_save_and_close, -5)
        self.go_to_page_label = gtk.Label()
        hbox = gtk.HBox(False, 0)
        hbox.set_border_width(5)
        self.go_to_page_dialog.vbox.pack_start(hbox, True, True, 10)
        self.go_to_page_dialog.set_has_separator(False)
        hbox.pack_start(self.button_page_spin, True, True, 0)
        self.go_to_page_label.set_alignment(0, 1)
        hbox.pack_start(self.go_to_page_label, False, False, 0)
        self.go_to_page_dialog.vbox.show_all()
    
    def create_bookmark_dialog(self):
        
        ''' Creates the bookmark dialog and all its widgets. '''
        
        self.bookmark_dialog = \
            gtk.Dialog(_("Edit bookmarks"), self.window, 0, (gtk.STOCK_ADD,
            gtk.RESPONSE_YES, gtk.STOCK_REMOVE, gtk.RESPONSE_NO,
            gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.liststore = gtk.ListStore(str, str, gtk.gdk.Pixbuf)
        self.bookmark_manager_tree_view = gtk.TreeView(self.liststore)
        self.bookmark_manager_tree_view.set_rules_hint(True)
        # FIXME: Rows should be reorderable, and the changes should be
        # mirrored everywhere.
        #self.bookmark_manager_tree_view.set_reorderable(True)
        self.bookmark_column = gtk.TreeViewColumn(_('Title'))
        self.bookmark_column2 = gtk.TreeViewColumn(_('Page'))
        self.cellpb = gtk.CellRendererPixbuf()
        self.cell = gtk.CellRendererText()
        self.cell2 = gtk.CellRendererText()
        self.bookmark_dialog.set_has_separator(False)
        box = gtk.VBox(False, 2)
        box.set_border_width(7)
        self.bookmark_dialog.vbox.pack_start(box, True, True, 2)
        box.pack_start(self.bookmark_manager_tree_view, True, True, 2)
        self.bookmark_column.set_expand(True)
        self.bookmark_column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.bookmark_column2.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.bookmark_manager_tree_view.append_column(self.bookmark_column)
        self.bookmark_manager_tree_view.append_column(self.bookmark_column2)
        self.bookmark_column.pack_start(self.cellpb, False)
        self.bookmark_column.pack_start(self.cell, True)
        self.bookmark_column2.pack_start(self.cell2, True)
        self.bookmark_column.set_attributes(self.cell, text=0)
        self.bookmark_column2.set_attributes(self.cell2, text=1)
        self.bookmark_column.set_attributes(self.cellpb, pixbuf=2)
        self.bookmark_dialog.vbox.show_all()
    
    def create_thumbnail_dialog(self):
        
        ''' Creates the thumbnail maintenance dialog and all its
        widgets. '''
        
        self.thumbnail_dialog = \
            gtk.Dialog(_("Manage thumbnails"), self.window, 0,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.thumbnail_dialog.set_has_separator(False)
        self.thumbnail_dialog.set_resizable(False)
        notebook = gtk.Notebook()
        self.thumbnail_dialog.vbox.pack_start(notebook, False, False, 5)
        
        # =======================================================
        # Directories tab.
        # =======================================================
        box = gtk.VBox(False, 0)
        box.set_border_width(12)
        
        self.dir_thumb_label = gtk.Label()
        self.dir_thumb_label2 = gtk.Label()
        vbox = gtk.VBox(False, 2)
        hbox = gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(self.dir_thumb_label, False, False, 0)
        hbox.pack_start(self.dir_thumb_label2, False, False, 0)
        box.pack_start(vbox, False, False, 2)
        self.dir_thumb_label.set_justify(gtk.JUSTIFY_RIGHT)
        
        hbox = gtk.HBox(False, 6)
        box.pack_start(hbox, False, False, 0)
        label_box = gtk.VBox(False, 0)
        entry_box = gtk.VBox(False, 0)
        hbox.pack_start(label_box, True, True, 0)
        hbox.pack_start(entry_box, True, True, 0)
        
        button = gtk.Button(stock=gtk.STOCK_DELETE)
        button.connect_object("clicked",
            self.thumbnail_maintenance_dialog_clean, 1)
        label = gtk.Label(_("Remove all stored thumbnails:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(button, True, True, 2)
        
        button = gtk.Button(_("Clean up"), None)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,
            gtk.ICON_SIZE_SMALL_TOOLBAR))
        button.connect_object("clicked",
            self.thumbnail_maintenance_dialog_clean, 2)
        label = gtk.Label(_("Remove orphaned thumbnails:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(button, True, True, 2)
        
        notebook.insert_page(box, gtk.Label(_("Directories")))
        
        # =======================================================
        # Archives tab.
        # =======================================================
        box = gtk.VBox(False, 0)
        box.set_border_width(12)
        
        self.arch_thumb_label = gtk.Label()
        self.arch_thumb_label2 = gtk.Label()
        vbox = gtk.VBox(False, 2)
        hbox = gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(self.arch_thumb_label, False, False, 0)
        hbox.pack_start(self.arch_thumb_label2, False, False, 0)
        box.pack_start(vbox, False, False, 2)
        self.arch_thumb_label.set_justify(gtk.JUSTIFY_RIGHT)
        
        hbox = gtk.HBox(False, 6)
        box.pack_start(hbox, False, False, 0)
        label_box = gtk.VBox(False, 0)
        entry_box = gtk.VBox(False, 0)
        hbox.pack_start(label_box, True, True, 0)
        hbox.pack_start(entry_box, True, True, 0)
        
        button = gtk.Button(stock=gtk.STOCK_DELETE)
        button.connect_object("clicked",
            self.thumbnail_maintenance_dialog_clean, 3)
        label = gtk.Label(_("Remove all stored thumbnails:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(button, True, True, 2)
        
        button = gtk.Button(_("Clean up"), None)
        button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR,
            gtk.ICON_SIZE_SMALL_TOOLBAR))
        button.connect_object("clicked",
            self.thumbnail_maintenance_dialog_clean, 4)
        label = gtk.Label(_("Remove orphaned thumbnails:"))
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, True, True, 0)
        entry_box.pack_start(button, True, True, 2)
        
        notebook.insert_page(box, gtk.Label(_("Archives")))
        
        self.thumbnail_dialog.vbox.show_all()
    
    def create_progress_dialog(self):
        
        ''' Creates the thumbnail maintenance progress dialog and all
        its widgets. '''
        
        self.progress_dialog = \
            gtk.Dialog(_("Removing thumbnails"), self.window, 0,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.progress_dialog.set_has_separator(False)
        self.progress_dialog.set_resizable(False)
        self.progress_dialog.set_size_request(300, 120)
        box = gtk.VBox(False, 10)
        box.set_border_width(12)
        self.progress_dialog.vbox.pack_start(box, True, True, 0)
        self.progress_bar = gtk.ProgressBar()
        box.pack_start(self.progress_bar, False, False, 0)
        self.progress_label = gtk.Label()
        self.progress_label.set_alignment(0, 0.5)
        box.pack_start(self.progress_label, False, False, 0)
        self.progress_dialog.vbox.show_all()
    
    def create_lib_progress_dialog(self):
        
        ''' Creates the library maintenance progress dialog and all
        its widgets. '''
        
        self.lib_progress_dialog = \
            gtk.Dialog('', self.lib_window, 0, (gtk.STOCK_CLOSE,
            gtk.RESPONSE_CLOSE))
        self.lib_progress_dialog.set_has_separator(False)
        self.lib_progress_dialog.set_resizable(False)
        self.lib_progress_dialog.set_size_request(300, 120)
        box = gtk.VBox(False, 10)
        box.set_border_width(12)
        self.lib_progress_dialog.vbox.pack_start(box, True, True, 0)
        self.lib_progress_bar = gtk.ProgressBar()
        box.pack_start(self.lib_progress_bar, False, False, 0)
        self.lib_progress_label = gtk.Label()
        self.lib_progress_label.set_alignment(0, 0.5)
        box.pack_start(self.lib_progress_label, False, False, 0)
        self.lib_progress_dialog.vbox.show_all()
    
    def create_convert_dialog(self):
        
        ''' Creates the convert dialog and all its widgets. '''        
        
        self.convert_dialog = gtk.FileChooserDialog(title=_("Convert"),
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        self.convert_dialog.set_default_response(gtk.RESPONSE_OK)
        
        self.convert_liststore = gtk.ListStore(str, str)
        self.convert_tree = gtk.TreeView(self.convert_liststore)
        self.convert_tree.set_rules_hint(True)
        self.convert_column = gtk.TreeViewColumn(_('File type'))
        self.convert_column2 = gtk.TreeViewColumn(_('Extension'))
        self.convert_cell = gtk.CellRendererText()
        self.convert_cell2 = gtk.CellRendererText()
        self.convert_column.set_expand(True)
        self.convert_column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.convert_column2.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.convert_tree.append_column(self.convert_column)
        self.convert_tree.append_column(self.convert_column2)
        self.convert_column.pack_start(self.convert_cell, True)
        self.convert_column2.pack_start(self.convert_cell2, True)
        self.convert_column.set_attributes(self.convert_cell, text=0)
        self.convert_column2.set_attributes(self.convert_cell2, text=1)
        self.convert_liststore.append([_('Zip archive'), 'cbz'])
        self.convert_liststore.append([_('Tar archive'), 'cbt'])
        self.convert_liststore.append([_('Gzip compressed tar archive'), 
            'cbt'])
        self.convert_liststore.append([_('Bzip2 compressed tar archive'), 
            'cbt'])
        tbox = gtk.VBox()
        tbox.pack_start(self.convert_tree, False, False, 0)
        tbox.set_border_width(1)
        bbox = gtk.EventBox()
        bbox.set_border_width(0)
        map = bbox.get_colormap()
        bbox.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#888888'))
        bbox.add(tbox)
        
        self.convert_toggle_delete_old = \
            gtk.CheckButton(_("Delete old archive/directory"))
        box = gtk.VBox()
        box.pack_start(bbox, True, True, 2)
        box.pack_start(self.convert_toggle_delete_old, False, False, 10)
        box.show_all()
        self.convert_dialog.set_extra_widget(box)
        self.convert_dialog.set_do_overwrite_confirmation(True)
    
    def create_extract_dialog(self):
        
        ''' Creates the extract image dialog and all its widgets. '''        
        
        self.extract_dialog = gtk.FileChooserDialog(
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE,gtk.RESPONSE_OK))
        self.extract_dialog.set_default_response(gtk.RESPONSE_OK)
        self.extract_dialog.set_do_overwrite_confirmation(True)
    
    def create_permission_dialog(self):
        
        ''' Creates the invalid permissions warning dialog and all
        its widgets. '''
        
        self.permission_dialog = \
            gtk.Dialog(_("Permission denied"), self.window, 0,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.permission_dialog.set_resizable(False)
        self.permission_label = gtk.Label()
        self.permission_dialog.set_has_separator(False)
        hbox = gtk.HBox(False, 10)
        hbox.set_border_width(5)
        self.permission_dialog.vbox.pack_start(hbox, True, True, 0)
        box = gtk.VBox(False, 0)
        hbox.pack_start(box, False, False, 2)
        stock = \
            gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR,
            gtk.ICON_SIZE_DIALOG)
        box.pack_start(stock, False, False, 2)
        alignment = gtk.Alignment(0.0, 0.0, 0.0, 1.0)
        box.pack_start(alignment, True, True, 0)
        hbox.pack_start(self.permission_label, True, True, 2)
        self.permission_dialog.vbox.show_all()

    def create_are_you_sure_dialog(self):
        
        ''' Creates the pestering "are you sure?" warning dialog and all
        its widgets. '''
        
        self.are_you_sure_dialog = \
            gtk.Dialog(_("Confirm operation"), self.window, gtk.DIALOG_MODAL,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.are_you_sure_dialog.set_default_response(gtk.RESPONSE_CANCEL)
        self.are_you_sure_dialog.set_resizable(False)
        self.are_you_sure_label = gtk.Label()
        self.are_you_sure_label.set_alignment(0, 0.05)
        self.are_you_sure_dialog.set_has_separator(False)
        hbox = gtk.HBox(False, 10)
        hbox.set_border_width(10)
        self.are_you_sure_dialog.vbox.pack_start(hbox, True, True, 0)
        box = gtk.VBox(False, 0)
        hbox.pack_start(box, False, False, 2)
        self.are_you_sure_image = gtk.Image()
        box.pack_start(self.are_you_sure_image, False, False, 2)
        alignment = gtk.Alignment(0.0, 0.0, 0.0, 1.0)
        box.pack_start(alignment, True, True, 0)
        hbox.pack_start(self.are_you_sure_label, True, True, 6)
        self.are_you_sure_dialog.vbox.show_all()
 
    def key_press_event(self, widget, event, data=None):
        
        ''' Catches key press events and takes the appropriate
        actions. '''
        
        if self.exit:
            return False
        
        #self.scroll_events_down = 0
        #self.scroll_events_up = 0
        self.update_sizes()
        if self.slideshow_started:
            self.stop_slideshow()
            self.window.emit_stop_by_name("key_press_event")
            return True
        
        # =======================================================
        # Delete key deletes an image (duh...)
        # =======================================================
        if event.keyval == gtk.keysyms.Delete:
            self.delete_file()
        
        # =======================================================
        # Numpad aligns the image depending on the key. 
        #
        # FIXME: Nobody knows about this, I don't even think about
        # it myself. Write that damn documentation some time!
        # =======================================================
        elif event.keyval == gtk.keysyms.KP_1:
            self.vadjust.set_value(self.vadjust_upper)
            self.hadjust.set_value(0)
        elif event.keyval == gtk.keysyms.KP_2:
            self.vadjust.set_value(self.vadjust_upper)
            self.hadjust.set_value(self.hadjust_upper / 2)
        elif event.keyval == gtk.keysyms.KP_3:
            self.vadjust.set_value(self.vadjust_upper)
            self.hadjust.set_value(self.hadjust_upper)
        elif event.keyval == gtk.keysyms.KP_4:
            self.vadjust.set_value(self.vadjust_upper / 2)
            self.hadjust.set_value(0)
        elif event.keyval == gtk.keysyms.KP_5:
            self.vadjust.set_value(self.vadjust_upper / 2)
            self.hadjust.set_value(self.hadjust_upper / 2)
        elif event.keyval == gtk.keysyms.KP_6:
            self.vadjust.set_value(self.vadjust_upper / 2)
            self.hadjust.set_value(self.hadjust_upper)
        elif event.keyval == gtk.keysyms.KP_7:
            self.vadjust.set_value(0)
            self.hadjust.set_value(0)
        elif event.keyval == gtk.keysyms.KP_8:
            self.vadjust.set_value(0)
            self.hadjust.set_value(self.hadjust_upper / 2)
        elif event.keyval == gtk.keysyms.KP_9:
            self.vadjust.set_value(0)
            self.hadjust.set_value(self.hadjust_upper)
        
        # =======================================================
        # Enter/exit fullscreen. 'f' is also a valid key,
        # defined as an accelerator elsewhere.
        # =======================================================
        elif event.keyval == gtk.keysyms.Escape:
            if self.prefs['fullscreen']:
                self.actiongroup.get_action('Fullscreen').set_active(False)
        elif event.keyval == gtk.keysyms.F11:
            if self.prefs['fullscreen']:
                self.actiongroup.get_action('Fullscreen').set_active(False)
            else:
                self.actiongroup.get_action('Fullscreen').set_active(True)

        # =======================================================
        # Zooming commands for manual zoom mode. These keys 
        # complement others (with the same action) defined as 
        # accelerators.
        # =======================================================
        elif event.keyval in [gtk.keysyms.plus, gtk.keysyms.equal]:
            self.zoom_in(None)
        elif event.keyval == gtk.keysyms.minus:
            self.zoom_out(None)
        elif (event.keyval in [gtk.keysyms._0, gtk.keysyms.KP_0] and 
            'GDK_CONTROL_MASK' in event.state.value_names):
            self.zoom_original(None)
        
        # =======================================================
        # Arrow keys scroll the image, except in
        # fit-to-screen mode where they flip pages.
        # =======================================================
        elif event.keyval == gtk.keysyms.Down:
            self.scroll_events_up = 0
            if not self.prefs['zoom mode'] == 1 or self.show_comments:
                height = self.layout.get_size()[1]
                if (self.vadjust.get_value() >= height - self.main_layout_y_size):
                     if self.prefs['flip with wheel']:
                         self.scroll_events_down += 1
                         if self.scroll_events_down > 2:
                             self.next_page(None)
                             self.scroll_events_down = 0
                elif (self.vadjust.get_value() + 20 > height -
                    self.main_layout_y_size):
                    self.vadjust.set_value(height - self.main_layout_y_size)
                else:
                    self.vadjust.set_value(self.vadjust.get_value() + 20)
            else:
                self.next_page(None)
        elif event.keyval == gtk.keysyms.Up:
            self.scroll_events_down = 0
            if not self.prefs['zoom mode'] == 1 or self.show_comments:
                if self.vadjust.get_value() <= 0:
                    if self.prefs['flip with wheel']:
                        self.scroll_events_up += 1
                        if self.scroll_events_up > 2:
                            self.previous_page(None)
                            self.scroll_events_up = 0
                elif self.vadjust.get_value() - 20 < 0:
                    self.vadjust.set_value(0)
                else:
                    self.vadjust.set_value(self.vadjust.get_value() - 20)
            else:
                self.previous_page(None)
        elif event.keyval == gtk.keysyms.Right:
            if not self.prefs['zoom mode'] == 1 or self.show_comments:
                if (self.hadjust.get_value() + 20 >
                    self.layout.get_size()[0] - self.main_layout_x_size):
                    self.hadjust.set_value(self.layout.get_size()[0] -
                        self.main_layout_x_size)
                else:
                    self.hadjust.set_value(self.hadjust.get_value() + 20)
            else:
                self.next_page(None)
        elif event.keyval == gtk.keysyms.Left:
            if not self.prefs['zoom mode'] == 1 or self.show_comments:
                if self.hadjust.get_value() - 20 < 0:
                    self.hadjust.set_value(0)
                else:
                    self.hadjust.set_value(self.hadjust.get_value() - 20)
            else:
                self.previous_page(None)
        
        # =======================================================
        # Space key scrolls down one "window height" at the time,
        # or a predefined percentage of the image height.
        # When at the bottom it flips to the next page. 
        # 
        # It also has a "smart scrolling mode", in which we also
        # scroll sideways.
        # See the tooltip for the preference for more info.
        #
        # FIXME: Can't this be made cleaner? And get rid of the
        # damn Indentations-From-Outer-Space (TM) as well.
        # =======================================================
        elif event.keyval == gtk.keysyms.space:
            if self.prefs['zoom mode'] == 1 and not self.show_comments:
                self.next_page(None)
            else:
                height = self.layout.get_size()[1]
                max_vadjust_value = height - self.main_layout_y_size
                if self.prefs['space scroll type']:
                    vscroll = \
                        self.prefs['space scroll length'] * 0.01 * height
                else:
                    vscroll = \
                        self.prefs['space scroll length'] * 0.01 * \
                        self.main_layout_y_size
                # =======================================================
                # No smart scrolling, simply go down or flip page.
                # =======================================================
                if not self.prefs['smart space scroll']:
                    if self.vadjust.get_value() >= max_vadjust_value:
                        self.next_page(None)
                    else:
                        if (self.vadjust.get_value() + vscroll >=
                           max_vadjust_value):
                           self.vadjust.set_value(max_vadjust_value)
                        else:
                            self.vadjust.set_value(
                                self.vadjust.get_value() + vscroll)
                else:
                    # =======================================================
                    # Smart scrolling, this is trickier. We now go 
                    # left to right before going down, and keeps double page
                    # mode in mind (which can be emulated).
                    # =======================================================
                    if (self.prefs['double page'] and self.file_number < 
                        len(self.file) - 1):
                        double_page = True
                        im1_width = self.image1_scaled_width
                        im2_width = self.image2_scaled_width
                    elif self.prefs['emulate double page']:
                        double_page = True
                        # When emulating double page mode we assume both
                        # pages are the same size.
                        im1_width = self.image1_scaled_width // 2
                        im2_width = im1_width
                    else:
                        double_page = False
                        im1_width = self.image1_scaled_width
                        im2_width = 0
                    width = im1_width + im2_width + 2
                    max_hadjust_value = width - self.main_layout_x_size
                    middle_hadjust_value = \
                        min(im1_width, max_hadjust_value)
                    if self.prefs['space scroll type']:
                        hscroll = \
                            self.prefs['space scroll length'] * 0.01 * width
                    else:
                        hscroll = \
                            self.prefs['space scroll length'] * 0.01 * \
                            self.main_layout_x_size
                    # =======================================================
                    # Single page mode.
                    # =======================================================
                    if not double_page:
                        # No manga mode.
                        if not self.prefs['manga']:
                            if self.hadjust.get_value() >= max_hadjust_value:
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.next_page(None)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(0)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(0)
                            else:
                                if (self.hadjust.get_value() + hscroll >=
                                    max_hadjust_value):
                                    self.hadjust.set_value(max_hadjust_value)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() + hscroll)
                        # Manga mode.
                        else:
                            if self.hadjust.get_value() <= 0:
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.next_page(None)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(max_hadjust_value)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(max_hadjust_value)
                            else:
                                if self.hadjust.get_value() - hscroll <= 0:
                                    self.hadjust.set_value(0)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() - hscroll)
                    # =======================================================
                    # Double page mode.
                    # =======================================================
                    else:
                        # No manga mode.
                        if not self.prefs['manga']:
                            # Move right on first page.
                            if (self.hadjust.get_value() <
                                middle_hadjust_value -
                                self.main_layout_x_size):
                                if (self.hadjust.get_value() + hscroll >=
                                    middle_hadjust_value - 
                                    self.main_layout_x_size):
                                    self.hadjust.set_value(
                                        middle_hadjust_value -
                                        self.main_layout_x_size)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() + hscroll)
                            # Move right on second page.
                            elif (self.hadjust.get_value() < 
                                max_hadjust_value and 
                                self.hadjust.get_value() >=
                                middle_hadjust_value):
                                if (self.hadjust.get_value() + hscroll >=
                                    max_hadjust_value):
                                    self.hadjust.set_value(
                                        max_hadjust_value)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() + hscroll)
                            # Move down on first page.
                            elif (middle_hadjust_value - 
                                self.main_layout_x_size <=
                                self.hadjust.get_value() < 
                                middle_hadjust_value):
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(0)
                                    self.hadjust.set_value(
                                        middle_hadjust_value)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(0)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(0)
                            # Move down on second page.
                            elif (self.hadjust.get_value() >= 
                                max_hadjust_value):
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.next_page(None)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(
                                        middle_hadjust_value)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(
                                        middle_hadjust_value)
                        # Manga mode.
                        else:
                            # Move left on first page.
                            if (self.hadjust.get_value() >
                                max(0, middle_hadjust_value)):
                                if (self.hadjust.get_value() - hscroll <=
                                    middle_hadjust_value):
                                    self.hadjust.set_value(
                                        middle_hadjust_value)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() - hscroll)
                            # Move left on second page.
                            elif (self.hadjust.get_value() <=  
                                middle_hadjust_value - 
                                self.main_layout_x_size and 
                                self.hadjust.get_value() > 0):
                                if self.hadjust.get_value() - hscroll <= 0:
                                    self.hadjust.set_value(0)
                                else:
                                    self.hadjust.set_value(
                                        self.hadjust.get_value() - hscroll)
                            # Move down on first page.
                            elif (middle_hadjust_value -
                                self.main_layout_x_size <
                                self.hadjust.get_value() <= 
                                middle_hadjust_value and 
                                self.hadjust.get_value() > 0):
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(0)
                                    self.hadjust.set_value(
                                        middle_hadjust_value - 
                                        self.main_layout_x_size)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(max_hadjust_value)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(max_hadjust_value)
                            # Move down on second page.
                            elif self.hadjust.get_value() <= 0:
                                if (self.vadjust.get_value() >=
                                    max_vadjust_value):
                                    self.next_page(None)
                                elif (self.vadjust.get_value() + vscroll >=
                                    max_vadjust_value):
                                    self.vadjust.set_value(max_vadjust_value)
                                    self.hadjust.set_value(
                                        middle_hadjust_value - 
                                        self.main_layout_x_size)
                                else:
                                    self.vadjust.set_value(
                                        self.vadjust.get_value() + vscroll)
                                    self.hadjust.set_value(
                                        middle_hadjust_value -
                                        self.main_layout_x_size)

        # =======================================================
        # We kill the signals here for the Up, Down, Space and 
        # Enter keys. Otherwise they will start moving
        # the thumbnail selector, we don't want that.
        # =======================================================
        if (event.keyval in [gtk.keysyms.Up, gtk.keysyms.Down,
            gtk.keysyms.space, gtk.keysyms.KP_Enter] or 
            (event.keyval == gtk.keysyms.Return and not
            'GDK_MOD1_MASK' in event.state.value_names)):
            self.window.emit_stop_by_name("key_press_event")
            return True
        else:
            return False
    
    def scroll_wheel_event(self, view, event, data=None):
        
        ''' Catches scroll wheel events and takes the appropriate
        actions. The scroll wheel flips pages in fit-to-screen mode
        and scrolls the scrollbars when not. With a preference set,
        three successive scrolls at the top or bottom of the page will
        flip pages when not in fit-to-screen mode as well. '''
        
        if self.exit:
            return False
            
        self.update_sizes()
        
        if event.direction == gtk.gdk.SCROLL_UP:
            self.scroll_events_down = 0
            if self.prefs['zoom mode'] == 1 and not self.show_comments:
                self.previous_page(None)
            else:
                if self.vadjust.get_value() <= 0:
                    if ((self.prefs['scroll wheel horiz'] or
                        self.prefs['zoom mode'] == 3) and 
                        self.hadjust.get_value() > 0 and
                        not self.prefs['manga']):
                        
                        if self.hadjust.get_value() - 60 <= 0:
                            self.hadjust.set_value(0)
                        else:
                            self.hadjust.set_value(
                                self.hadjust.get_value() - 60)
                    
                    elif ((self.prefs['scroll wheel horiz'] or
                        self.prefs['zoom mode'] == 3) and 
                        self.hadjust.get_value() <
                        self.layout.get_size()[0] -
                        self.main_layout_x_size and self.prefs['manga']):
                        
                        if (self.hadjust.get_value() + 60 >
                            self.layout.get_size()[0] -
                            self.main_layout_x_size):
                            self.hadjust.set_value(self.layout.get_size()[0] -
                                self.main_layout_x_size)
                        else:
                            self.hadjust.set_value(self.hadjust.get_value() +
                                60)
                    
                    elif self.prefs['flip with wheel']:
                        self.scroll_events_up += 1
                        if self.scroll_events_up > 2:
                            self.previous_page(None)
                            self.scroll_events_up = 0
                
                elif self.vadjust.get_value() - 60 < 0:
                    self.vadjust.set_value(0)
                else:
                    self.vadjust.set_value(self.vadjust.get_value() - 60)
        
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.scroll_events_up = 0
            if self.prefs['zoom mode'] == 1 and not self.show_comments:
                self.next_page(None)
            else:
                if (self.vadjust.get_value() >= self.layout.get_size()[1] -
                    self.main_layout_y_size):
                    
                    if ((self.prefs['scroll wheel horiz'] or
                        self.prefs['zoom mode'] == 3) and 
                        self.hadjust.get_value() > 0 and
                        self.prefs['manga']):
                        
                        if self.hadjust.get_value() - 60 <= 0:
                            self.hadjust.set_value(0)
                        else:
                            self.hadjust.set_value(self.hadjust.get_value() -
                                60)
                    
                    elif ((self.prefs['scroll wheel horiz'] or
                        self.prefs['zoom mode'] == 3) and
                        self.hadjust.get_value() <
                        self.layout.get_size()[0] -
                        self.main_layout_x_size and not self.prefs['manga']):
                        
                        if (self.hadjust.get_value() + 60 >
                            self.layout.get_size()[0] -
                            self.main_layout_x_size):
                            self.hadjust.set_value(self.layout.get_size()[0] -
                                self.main_layout_x_size)
                        else:
                            self.hadjust.set_value(self.hadjust.get_value() +
                                60)
                    
                    elif self.prefs['flip with wheel']:
                        
                        self.scroll_events_down += 1
                        
                        if self.scroll_events_down > 2:
                            self.next_page(None)
                            self.scroll_events_down = 0
                
                elif (self.vadjust.get_value() + 60 >
                    self.layout.get_size()[1] - self.main_layout_y_size):
                    self.vadjust.set_value(self.layout.get_size()[1] -
                        self.main_layout_y_size)
                else:
                    self.vadjust.set_value(self.vadjust.get_value() + 60)
        
        elif event.direction == gtk.gdk.SCROLL_LEFT:
            self.previous_page(None)
        
        elif event.direction == gtk.gdk.SCROLL_RIGHT:
            self.next_page(None)
    
    def lib_scroll_wheel_event(self, view, event, data=None):
        
        ''' Handles scroll wheel events in the library window. '''
        
        if self.exit:
            return False
        
        if event.direction == gtk.gdk.SCROLL_UP:
            if self.lib_vadjust.get_value() - 60 < 0:
                self.lib_vadjust.set_value(0)
            else:
                self.lib_vadjust.set_value(self.lib_vadjust.get_value() - 60)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            if (self.lib_vadjust.get_value() + 60 >
                self.lib_layout.get_size()[1] -
                self.lib_window.get_size()[1] +
                self.lib_info_table.size_request()[1]):
                self.lib_vadjust.set_value(self.lib_layout.get_size()[1] -
                    self.lib_window.get_size()[1] +
                    self.lib_info_table.size_request()[1])
            else:
                self.lib_vadjust.set_value(self.lib_vadjust.get_value() + 60)
    
    def thumb_scroll_wheel_event(self, view, event, data=None):
        
        ''' Handles scroll wheel events in the thumbnail sidebar. '''
        
        if self.exit:
            return False
        
        if event.direction == gtk.gdk.SCROLL_UP:
            if self.thumb_vadjust.get_value() > 0:
                if self.thumb_vadjust.get_value() - 60 < 0:
                    self.thumb_vadjust.set_value(0)
                else:
                    self.thumb_vadjust.set_value(
                        self.thumb_vadjust.get_value() - 60)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            if self.thumb_vadjust.get_value() < self.thumb_vadjust_upper:
                if (self.thumb_vadjust.get_value() + 60 >
                    self.thumb_vadjust_upper):
                    self.thumb_vadjust.set_value(self.thumb_vadjust_upper)
                else:
                    self.thumb_vadjust.set_value(
                        self.thumb_vadjust.get_value() + 60)
    
    def thumb_selection_event(self, data):
        
        ''' Handles selections of thumbnails in the thumbnail
        sidebar. '''
        
        if self.exit:
            return False

        self.show_comments = 0
        
        if (len(self.thumb_tree_view.get_selection().get_selected_rows()[1]) >
            0):
            if (self.thumb_tree_view.get_selection()
                .get_selected_rows()[1][0][0] != self.file_number):
                self.stop_slideshow()
                self.file_number = \
                    self.thumb_tree_view.get_selection() \
                    .get_selected_rows()[1][0][0]
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 2
                if not self.prefs['keep transformation']:
                    self.prefs['rotation'] = 0
                    self.prefs['flip horiz'] = 0
                    self.prefs['flip vert'] = 0
                self.refresh_image()
            
            # =======================================================
            # To keep two selected thumbs in double page mode
            # when already selected thumb is clicked.
            # =======================================================
            elif (self.prefs['double page'] and
                self.file_number != len(self.file) - 1 and
                len(self.thumb_tree_view.get_selection()
                .get_selected_rows()[1]) == 1 and
                self.number_of_thumbs_loaded > self.file_number + 1):
                
                self.thumb_tree_view.get_selection().unselect_all()
                self.thumb_tree_view.get_selection().select_range(
                    self.file_number, self.file_number + 1)
    
    def area_resize_event(self, widget, allocation):
        
        ''' Handles events from resizing and moving the main window. '''
        
        if self.exit:
            return False
        
        if not self.prefs['fullscreen']:
            self.prefs['window x'], self.prefs['window y'] = \
                self.window.get_position()
        if (allocation.width != self.window_width or
            allocation.height != self.window_height):
            if not self.prefs['fullscreen']:
                self.prefs['window width'] = allocation.width
                self.prefs['window height'] = allocation.height
            self.window_width = allocation.width
            self.window_height = allocation.height
            self.resize_event = 1
            self.refresh_image()
            self.resize_event = 0
    
    def mouse_button_press_event(self, view, event, data=None):
        
        ''' Handles mouse click events on the main window. '''
        
        if self.exit:
            return False
        
        self.scroll_events_down = 0
        self.scroll_events_up = 0
        self.set_cursor_type('normal')
        if self.slideshow_started:
            self.stop_slideshow()
            self.slideshow_stopped_by_mouse = True
            return
        
        if event.button == 3:
            self.ui.get_widget('/Pop').popup(None, None, None, event.button,
                event.time)
        elif event.button == 1:
            self.x_drag_position = event.x_root
            self.y_drag_position = event.y_root
            self.mouse_moved_while_drag = 0
            self.old_vadjust_value = self.vadjust.value
            self.old_hadjust_value = self.hadjust.value
        elif event.button == 2:
            if self.scroll_wheel_event_id != None:
                self.layout.disconnect(self.scroll_wheel_event_id)
                self.scroll_wheel_event_id = None
            self.zooming_lens(event.x, event.y, event.time)
    
    def mouse_button_release_event(self, widget, event):
        
        ''' Handles mouse button release events on the main window. '''
        
        if self.exit:
            return False
        if self.slideshow_stopped_by_mouse:
            self.slideshow_stopped_by_mouse = False
            self.set_cursor_type('normal')
            return
        
        self.set_cursor_type('normal')
        if self.mouse_moved_while_drag == 0 and event.button == 1:
            self.next_page(None)
        if event.button == 2 and self.z_pressed:
            self.actiongroup.get_action('Lens').set_active(False)
        if self.scroll_wheel_event_id == None:
            self.scroll_wheel_event_id = \
                self.layout.connect('scroll_event', self.scroll_wheel_event)
    
    def motion_event(self, widget, event):
        
        ''' Handles mouse pointer motion events in the main window.
        Calls the appropriate method depending on the circumstance. '''
        
        if self.exit:
            return False
        
        # Remove any existing timers.
        if self.cursor_timer_id != None:
            gobject.source_remove(self.cursor_timer_id)
        
        if 'GDK_BUTTON1_MASK' in event.state.value_names:
            self.drag_image(event)
        elif ((self.z_pressed or 'GDK_BUTTON2_MASK' in
            event.state.value_names)
            and not self.show_comments):
            self.zooming_lens(event.x, event.y, event.time)
        else:
            if self.prefs['fullscreen'] and self.prefs['hide cursor']:
                # Show pointer and set a timer to hide it after a while.
                for x in gtk.gdk.window_get_toplevels():
                    x.set_cursor(None)
                self.layout.window.set_cursor(None)
                self.cursor_timer_id = \
                    gobject.timeout_add(2000, self.set_cursor_type)
    
    def update_sizes(self):
        
        ''' Calculates the current relevant dimensions of all widgets in the
        main window that define the size of the main display area. '''
        
        if self.exit:
            return False
        
        if self.prefs['fullscreen']:
            self.menu_size = \
                (1 - self.prefs['hide in fullscreen']) * \
                self.prefs['show menubar'] * \
                self.ui.get_widget('/Menu').size_request()[1]
            self.tool_size = \
                (1 - self.prefs['hide in fullscreen']) * \
                self.prefs['show toolbar'] * \
                self.toolbar.size_request()[1]
            self.status_size = \
                (1 - self.prefs['hide in fullscreen']) * \
                self.prefs['show statusbar'] * \
                self.statusbar.size_request()[1]
            if self.prefs['show thumbnails']:
                self.thumb_size = \
                    (self.prefs['thumbnail size'] + 7) * \
                    (1 - self.prefs['hide in fullscreen'])
                self.thumb_vscroll_size = \
                    self.thumb_vscroll.size_request()[0] * \
                    (1 - self.prefs['hide thumbnail scrollbar']) * \
                    (1 - self.prefs['hide in fullscreen'])
            else:
                self.thumb_size = 0
                self.thumb_vscroll_size = 0
            if (self.prefs['hide in fullscreen'] or 
                self.prefs['hide scrollbar'] or 
                self.prefs['zoom mode'] == 1):
                self.vscroll_size = 0
                self.hscroll_size = 0
            else:
                self.vscroll_size = self.vscroll.size_request()[0]
                self.hscroll_size = self.hscroll.size_request()[1]
        else:
            self.menu_size = \
                self.prefs['show menubar'] * \
                self.ui.get_widget('/Menu').size_request()[1]
            self.tool_size = \
                self.prefs['show toolbar'] * self.toolbar.size_request()[1]
            self.status_size = \
                self.prefs['show statusbar'] * \
                self.statusbar.size_request()[1]
            if self.prefs['show thumbnails']:
                self.thumb_size = (self.prefs['thumbnail size'] + 7)
                self.thumb_vscroll_size = \
                    self.thumb_vscroll.size_request()[0] * \
                    (1 - self.prefs['hide thumbnail scrollbar'])
            else:
                self.thumb_size = 0
                self.thumb_vscroll_size = 0
            if self.prefs['hide scrollbar'] or self.prefs['zoom mode'] == 1:
                self.vscroll_size = 0
                self.hscroll_size = 0
            elif self.prefs['zoom mode'] == 2:
                self.vscroll_size = self.vscroll.size_request()[0]
                self.hscroll_size = 0
            elif self.prefs['zoom mode'] == 3:
                self.vscroll_size = 0
                self.hscroll_size = self.hscroll.size_request()[1]
            else:
                self.vscroll_size = self.vscroll.size_request()[0]
                self.hscroll_size = self.hscroll.size_request()[1]
        if self.show_comments:
            self.hscroll_size = self.hscroll.size_request()[1]
            self.vscroll_size = self.vscroll.size_request()[0]
        
        if self.prefs['fullscreen']:
            screen = self.window.get_screen()
            monitor = \
                screen.get_monitor_geometry(screen.get_monitor_at_point(
                *self.window.get_position()))
            self.main_layout_x_size = \
                monitor.width - \
                self.vscroll_size - self.thumb_vscroll_size - self.thumb_size
            self.main_layout_y_size = \
                monitor.height - \
                self.hscroll_size - self.menu_size - self.tool_size - \
                self.status_size
        else:
            self.main_layout_x_size = \
                self.window.get_size()[0] - self.vscroll_size - \
                self.thumb_vscroll_size - self.thumb_size
            self.main_layout_y_size = \
                self.window.get_size()[1] - self.hscroll_size - \
                self.menu_size - self.tool_size - self.status_size
    
    def zooming_lens(self, event_x, event_y, millisecs):
        
        ''' Changes the cursor to a square containing a magnification
        of the image data currently under the pointer's position. '''
        
        if self.exit:
            return False
        
        # =======================================================
        # Deal with negative times sometimes reported by certain 
        # versions of X.org (7.0?)
        # =======================================================
        if self.lens_timer == None:
            self.lens_timer = \
                millisecs - self.prefs['max lens update interval'] - 100
        
        # =======================================================
        # Never update more often than at a certain
        # interval, uses lots of resources.
        # =======================================================
        if not (millisecs > self.lens_timer + 
            self.prefs['max lens update interval'] and self.file_exists):
            return 1

        if (event_x - float(self.prefs['lens size from center']) / 
            self.prefs['lens magnification'] <=
            self.hadjust.get_value() or event_y - 
            float(self.prefs['lens size from center']) /
            self.prefs['lens magnification'] <= self.vadjust.get_value() or 
            event_x + self.prefs['lens size from center'] / 
            self.prefs['lens magnification'] >=
            self.hadjust.get_value() + self.main_layout_x_size or
            event_y + self.prefs['lens size from center'] / 
            self.prefs['lens magnification'] >=
            self.vadjust.get_value() + self.main_layout_y_size):
            return 1

        both_pages = False
        self.zooming_lens_manga_flip()
        
        # =======================================================
        # Calculate possible padding for the images.
        # =======================================================
        x_padding = \
            (self.main_layout_x_size - self.layout.get_size()[0]) / 2
        if x_padding < 0:
            x_padding = 0
        y_padding = \
            (self.main_layout_y_size - self.image1_scaled_height) / 2
        if y_padding < 0:
            y_padding = 0
        y_padding2 = \
            (self.main_layout_y_size - self.image2_scaled_height) / 2
        if y_padding2 < 0:
            y_padding2 = 0
        
        # =======================================================
        # Calculate magnification scales relative to the original
        # images based on the sizes of the displayed images.
        # =======================================================
        scale1 = \
            float(self.image1_scaled_width) / self.image1_width * \
            self.prefs['lens magnification']
        if (self.prefs['double page'] and 
            self.file_number != len(self.file) - 1):
            scale2 = \
                float(self.image2_scaled_width) / self.image2_width * \
                self.prefs['lens magnification']

        # =======================================================
        # Position of the pointer on the image(s). x and y are
        # distances from the top left corner on the first image in
        # the scale of the first original image. x2 and y2 are
        # distances from the top left corner of the second image
        # in the scale of the second original image (if in double
        # page mode.)
        # =======================================================
        if (not self.prefs['double page'] or
            self.file_number == len(self.file) - 1):
            x = \
                (event_x - x_padding) * self.image1_width / \
                self.image1_scaled_width
            y = \
                (event_y - y_padding) * self.image1_width / \
                self.image1_scaled_width
        else:
            x = \
                (event_x - x_padding) * self.image1_width / \
                self.image1_scaled_width
            y = \
                (event_y - y_padding) * self.image1_width / \
                self.image1_scaled_width
            x2 = \
                (event_x - x_padding - self.image1_scaled_width) * \
                self.image2_width / self.image2_scaled_width
            y2 = \
                (event_y - y_padding2) * self.image2_width / \
                self.image2_scaled_width
        
        # =======================================================
        # Calculate where the pointer maps on the original image
        # (self.stored_pixbuf) in single page mode.
        # =======================================================
        if (not self.prefs['double page'] or
            self.file_number == len(self.file) - 1):
            if self.prefs['rotation'] == 0:
                src_x = x - self.prefs['lens size from center'] / scale1
                src_y = y - self.prefs['lens size from center'] / scale1
            elif self.prefs['rotation'] == 1:
                src_x = y - self.prefs['lens size from center'] / scale1
                src_y = \
                    self.image1_width - x - \
                    self.prefs['lens size from center'] / scale1
            elif self.prefs['rotation'] == 2:
                src_x = \
                    self.image1_width - x - \
                    self.prefs['lens size from center'] / scale1
                src_y = \
                    self.image1_height - y - \
                    self.prefs['lens size from center'] / scale1
            elif self.prefs['rotation'] == 3:
                src_x = \
                    self.image1_height - y - \
                    self.prefs['lens size from center'] / scale1
                src_y = x - self.prefs['lens size from center'] / scale1
            
            if self.prefs['flip horiz']:
                if self.prefs['rotation'] in [1, 3]:
                    src_y = \
                        self.image1_width - src_y - \
                        (self.prefs['lens size from center'] * 2) / \
                        scale1
                else:
                    src_x = \
                        self.image1_width - src_x - \
                        (self.prefs['lens size from center'] * 2) / \
                        scale1
            if self.prefs['flip vert']:
                if self.prefs['rotation'] in [1, 3]:
                    src_x = \
                        self.image1_height - src_x - \
                        (self.prefs['lens size from center'] * 2) / scale1
                else:
                    src_y = \
                        self.image1_height - src_y - \
                        (self.prefs['lens size from center'] * 2) / scale1
            
            # =======================================================
            # More sanity checks. Yey!
            # =======================================================
            if (int(src_x) + int((self.prefs['lens size from center'] * 2) /
                scale1) > self.stored_pixbuf.get_width() or int(src_y) +
                int((self.prefs['lens size from center'] * 2) / scale1) >
                self.stored_pixbuf.get_height() or int(src_x) < 0 or
                int(src_y) < 0):
                
                self.set_cursor_type('normal')
                return 1
            
            # =======================================================
            # Copy area to a new pixbuf and scale it to the lens size.
            # =======================================================
            pixbuf = \
                self.stored_pixbuf.subpixbuf(int(src_x), int(src_y),
                int((self.prefs['lens size from center'] * 2) / scale1),
                int((self.prefs['lens size from center'] * 2) / scale1))
            pixbuf = \
                pixbuf.scale_simple((self.prefs['lens size from center'] * 2),
                (self.prefs['lens size from center'] * 2),
                gtk.gdk.INTERP_TILES)
        
        # =======================================================
        # Calculate where the pointer maps on the original images
        # in double page mode. The displayed images do not
        # necessarily have the same relative scaling, *sigh*.
        # =======================================================
        else:
            
            # =======================================================
            # Whole lens is on the first page, makes life a little
            # easier.
            # =======================================================
            if (x + self.prefs['lens size from center'] / scale1 <= 
                self.image1_width):
                if self.prefs['rotation'] == 0:
                    src_x = x - self.prefs['lens size from center'] / scale1
                    src_y = y - self.prefs['lens size from center'] / scale1
                elif self.prefs['rotation'] == 1:
                    src_x = y - self.prefs['lens size from center'] / scale1
                    src_y = \
                        self.image1_width - x - \
                        self.prefs['lens size from center'] / scale1
                elif self.prefs['rotation'] == 2:
                    src_x = \
                        self.image1_width - x - \
                        self.prefs['lens size from center'] / scale1
                    src_y = \
                        self.image1_height - y - \
                        self.prefs['lens size from center'] / scale1
                elif self.prefs['rotation'] == 3:
                    src_x = \
                        self.image1_height - y - \
                        self.prefs['lens size from center'] / scale1
                    src_y = x - self.prefs['lens size from center'] / scale1
                
                if self.prefs['flip horiz']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_y = \
                            self.image1_width - src_y - \
                            (self.prefs['lens size from center'] * 2) / scale1
                    else:
                        src_x = \
                            self.image1_width - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale1
                if self.prefs['flip vert']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_x = \
                            self.image1_height - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale1
                    else:
                        src_y = \
                            self.image1_height - src_y - \
                            (self.prefs['lens size from center'] * 2) / scale1
                
                # =======================================================
                # Sanity check.
                # =======================================================
                if (int(src_x) + int((self.prefs['lens size from center'] *
                    2) / scale1) > self.stored_pixbuf.get_width() or
                    int(src_y) + 
                    int((self.prefs['lens size from center'] * 2) / scale1) >
                    self.stored_pixbuf.get_height() or int(src_x) < 0 or
                    int(src_y) < 0):
                    
                    self.set_cursor_type('normal')
                    self.zooming_lens_manga_flip()
                    return 1
                
                # =======================================================
                # Copy area to a new pixbuf and scale it to the lens size.
                # =======================================================
                pixbuf = \
                    self.stored_pixbuf.subpixbuf(int(src_x), int(src_y),
                    int((self.prefs['lens size from center'] * 2) / scale1),
                    int((self.prefs['lens size from center'] * 2) / scale1))
                pixbuf = \
                    pixbuf.scale_simple((
                    self.prefs['lens size from center'] * 2),
                    (self.prefs['lens size from center'] * 2),
                    gtk.gdk.INTERP_TILES)
            
            # =======================================================
            # Whole lens is on the second page, also makes life a
            # little easier.
            # =======================================================
            elif (x - self.prefs['lens size from center'] /
                scale1 > self.image1_width):
                if self.prefs['rotation'] == 0:
                    src_x = x2 - self.prefs['lens size from center'] / scale2
                    src_y = y2 - self.prefs['lens size from center'] / scale2
                elif self.prefs['rotation'] == 1:
                    src_x = y2 - self.prefs['lens size from center'] / scale2
                    src_y = \
                        self.image2_width - x2 - \
                        self.prefs['lens size from center'] / scale2
                elif self.prefs['rotation'] == 2:
                    src_x = \
                        self.image2_width - x2 - \
                        self.prefs['lens size from center'] / scale2
                    src_y = \
                        self.image2_height - y2 - \
                        self.prefs['lens size from center'] / scale2
                elif self.prefs['rotation'] == 3:
                    src_x = \
                        self.image2_height - y2 - \
                        self.prefs['lens size from center'] / scale2
                    src_y = x2 - self.prefs['lens size from center'] / scale2
                
                if self.prefs['flip horiz']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_y = \
                            self.image2_width - src_y - \
                            (self.prefs['lens size from center'] * 2) / scale2
                    else:
                        src_x = \
                            self.image2_width - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale2
                if self.prefs['flip vert']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_x = \
                            self.image2_height - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale2
                    else:
                        src_y = \
                            self.image2_height - src_y - \
                            (self.prefs['lens size from center'] * 2) / scale2
                
                # =======================================================
                # Sanity check.
                # =======================================================
                if (int(src_x) + int((self.prefs['lens size from center'] *
                    2) / scale2) >
                    self.stored_pixbuf2.get_width() or int(src_y) +
                    int((self.prefs['lens size from center'] * 2) / scale2) >
                    self.stored_pixbuf2.get_height() or int(src_x) < 0 or
                    int(src_y) < 0):
                    
                    self.set_cursor_type('normal')
                    self.zooming_lens_manga_flip()
                    return 1
                
                # =======================================================
                # Copy area to a new pixbuf and scale it to the lens size.
                # =======================================================
                pixbuf = \
                    self.stored_pixbuf2.subpixbuf(int(src_x), int(src_y),
                    int((self.prefs['lens size from center'] * 2) / scale2),
                    int((self.prefs['lens size from center'] * 2) / scale2))
                pixbuf = \
                    pixbuf.scale_simple((
                    self.prefs['lens size from center'] * 2),
                    (self.prefs['lens size from center'] * 2),
                    gtk.gdk.INTERP_TILES)
            
            # =======================================================
            # Lens on both pages at the same time. We have to copy
            # parts of both images and merge them together.
            # =======================================================
            else:
                both_pages = True

                # =======================================================
                # Map pointer position to area on the first image.
                # =======================================================
                if self.prefs['rotation'] == 0:
                    src_x = x - self.prefs['lens size from center'] / scale1
                    src_y = y - self.prefs['lens size from center'] / scale1
                    width = \
                        self.image1_width - x + \
                        self.prefs['lens size from center'] / scale1 - 1
                    height = \
                        (self.prefs['lens size from center'] * 2) / scale1
                elif self.prefs['rotation'] == 1:
                    src_x = y - self.prefs['lens size from center'] / scale1
                    src_y = 0
                    width = (self.prefs['lens size from center'] * 2) / scale1
                    height = \
                        self.image1_width - x + \
                        self.prefs['lens size from center'] / scale1 - 1
                elif self.prefs['rotation'] == 2:
                    src_x = 0
                    src_y = \
                        self.image1_height - y - \
                        self.prefs['lens size from center'] / scale1
                    width = \
                        self.image1_width - x + \
                        self.prefs['lens size from center'] / scale1 - 1
                    height = \
                        (self.prefs['lens size from center'] * 2) / scale1
                elif self.prefs['rotation'] == 3:
                    src_x = \
                        self.image1_height - y - \
                        self.prefs['lens size from center'] / scale1
                    src_y = x - self.prefs['lens size from center'] / scale1
                    width = (self.prefs['lens size from center'] * 2) / scale1
                    height = \
                        self.image1_width - x + \
                        self.prefs['lens size from center'] / scale1 - 1
                
                if self.prefs['flip horiz']:
                    if self.prefs['rotation'] == 1:
                        src_y = self.image1_width - height
                    elif self.prefs['rotation'] == 3:
                        src_y = 0
                    else:
                        src_x = self.image1_width - src_x - width
                if self.prefs['flip vert']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_x = \
                            self.image1_height - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale1
                    else:
                        src_y = \
                        self.image1_height - src_y - \
                        (self.prefs['lens size from center'] * 2) / scale1
                
                # =======================================================
                # Sanity check.
                # =======================================================
                if (int(src_x) + int(width) >
                    self.stored_pixbuf.get_width() or int(src_y) +
                    int(height) > self.stored_pixbuf.get_height() or
                    int(src_x) < 0 or int(src_y) < 0 or int(width) <
                    1 or int(height) < 1):
                    
                    self.set_cursor_type('normal')
                    self.zooming_lens_manga_flip()
                    return 1
                
                # =======================================================
                # Copy area to a new pixbuf and scale it to the lens size.
                # =======================================================
                pixbuf = \
                    self.stored_pixbuf.subpixbuf(int(src_x), int(src_y),
                    int(width), int(height))

                if self.prefs['rotation'] in [1, 3]:
                    dst_width = (self.prefs['lens size from center'] * 2)
                    dst_height = int(height * scale1)
                else:
                    dst_width = int(width * scale1)
                    dst_height = (self.prefs['lens size from center'] * 2)
                if dst_width < 1:
                    dst_width = 1
                if dst_height < 1:
                    dst_height = 1
                pixbuf = \
                    pixbuf.scale_simple(dst_width, dst_height,
                    gtk.gdk.INTERP_TILES)
                
                # =======================================================
                # Map pointer position to area on the second image.
                # =======================================================
                if self.prefs['rotation'] == 0:
                    src_x = 0
                    src_y = y2 - self.prefs['lens size from center'] / scale2
                    width = \
                        x2 + self.prefs['lens size from center'] / scale2 - 1
                    height = \
                        (self.prefs['lens size from center'] * 2) / scale2
                elif self.prefs['rotation'] == 1:
                    src_x = y2 - self.prefs['lens size from center'] / scale2
                    src_y = \
                        self.image2_width - x2 - \
                        self.prefs['lens size from center'] / scale2
                    width = (self.prefs['lens size from center'] * 2) / scale2
                    height = \
                        x2 + self.prefs['lens size from center'] / scale2 - 1
                elif self.prefs['rotation'] == 2:
                    src_x = \
                        self.image2_width - x2 - \
                        self.prefs['lens size from center'] / scale2
                    src_y = \
                        self.image2_height - y2 - \
                        self.prefs['lens size from center'] / scale2
                    width = \
                        x2 + self.prefs['lens size from center'] / scale2 - 1
                    height = \
                        (self.prefs['lens size from center'] * 2) / scale2
                elif self.prefs['rotation'] == 3:
                    src_x = \
                        self.image2_height - y2 - \
                        self.prefs['lens size from center'] / scale2
                    src_y = 0
                    width = (self.prefs['lens size from center'] * 2) / scale2
                    height = \
                        x2 + self.prefs['lens size from center'] / scale2 - 1
                
                if self.prefs['flip horiz']:
                    if self.prefs['rotation'] == 1:
                        src_y = 0
                    elif self.prefs['rotation'] == 3:
                        src_y = \
                            self.image2_width - x2 - \
                            self.prefs['lens size from center'] / scale2
                    else:
                        src_x = self.image2_width - src_x - width
                if self.prefs['flip vert']:
                    if self.prefs['rotation'] in [1, 3]:
                        src_x = \
                            self.image2_height - src_x - \
                            (self.prefs['lens size from center'] * 2) / scale2
                    else:
                        src_y = \
                            self.image2_height - src_y - \
                            (self.prefs['lens size from center'] * 2) / scale2
                
                # =======================================================
                # Sanity check.
                # =======================================================
                if (int(src_x) + int(width) >
                    self.stored_pixbuf2.get_width() or int(src_y) +
                    int(height) > self.stored_pixbuf2.get_height() or
                    int(src_x) < 0 or int(src_y) < 0 or int(width) < 1 or
                    int(height) < 1):
                    
                    self.set_cursor_type('normal')
                    self.zooming_lens_manga_flip()
                    return 1
                
                # =======================================================
                # Copy area to a new pixbuf and scale it to the lens size.
                # =======================================================
                pixbuf2 = \
                    self.stored_pixbuf2.subpixbuf(int(src_x), int(src_y),
                    int(width), int(height))

                if self.prefs['rotation'] in [1, 3]:
                    dst_width = (self.prefs['lens size from center'] * 2)
                    dst_height = \
                        (self.prefs['lens size from center'] *2 - 2) - \
                        pixbuf.get_height()
                else:
                    dst_width = \
                        (self.prefs['lens size from center'] *2 - 2) - \
                        pixbuf.get_width()
                    dst_height = (self.prefs['lens size from center'] * 2)
                if dst_width < 1:
                    dst_width = 1
                if dst_height < 1:
                    dst_height = 1
                pixbuf2 = \
                    pixbuf2.scale_simple(dst_width, dst_height,
                    gtk.gdk.INTERP_TILES)
        
        # =======================================================
        # Now we have the image data for our cursor in one or two
        # pixbufs. We still have to add a border, possibly
        # rotate and/or flip the images and do some other things.
        # =======================================================
        stride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()
        mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
        pil_image = \
            Image.frombuffer(mode, (pixbuf.get_width(),
            pixbuf.get_height()), pixels, 'raw', mode, stride, 1)
        if self.prefs['rotation'] == 1:
            pil_image = pil_image.transpose(Image.ROTATE_270)
        elif self.prefs['rotation'] == 2:
            pil_image = pil_image.transpose(Image.ROTATE_180)
        elif self.prefs['rotation'] == 3:
            pil_image = pil_image.transpose(Image.ROTATE_90)
        if self.prefs['flip horiz']:
            pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
        if self.prefs['flip vert']:
            pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)

        # =======================================================
        # If we had two different pixbufs (i.e. data from both
        # pages) we have to transform the second one as well and
        # then add then merge them together.
        #
        # FIXME: Does newer version of PyGTK (2.10?) support rotating/
        # flipping of pixbufs? It should be faster to use those
        # methods directly and skip the PIL step. A conditional with
        # the pygtk version might do the trick.
        # =======================================================
        if both_pages:
            assert(pixbuf2.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
            stride2 = pixbuf2.get_rowstride()
            pixels2 = pixbuf2.get_pixels()
            mode2 = pixbuf2.get_has_alpha() and 'RGBA' or 'RGB'
            pil_image2 = \
                Image.frombuffer(mode2, (pixbuf2.get_width(),
                pixbuf2.get_height()), pixels2, 'raw', mode2, stride2, 1)
            if self.prefs['rotation'] == 1:
                pil_image2 = pil_image2.transpose(Image.ROTATE_270)
            elif self.prefs['rotation'] == 2:
                pil_image2 = pil_image2.transpose(Image.ROTATE_180)
            elif self.prefs['rotation'] == 3:
                pil_image2 = pil_image2.transpose(Image.ROTATE_90)
            if self.prefs['flip horiz']:
                pil_image2 = pil_image2.transpose(Image.FLIP_LEFT_RIGHT)
            if self.prefs['flip vert']:
                pil_image2 = pil_image2.transpose(Image.FLIP_TOP_BOTTOM)
            
            pil_image_canvas = \
                Image.new('RGBA', ((self.prefs['lens size from center'] * 2),
                (self.prefs['lens size from center'] * 2)), (0, 0, 0, 0))
            if not mode == 'RGBA':
                pil_image = pil_image.convert('RGBA')
            if not mode2 == 'RGBA':
                pil_image2 = pil_image2.convert('RGBA')
            pil_image_canvas.paste(pil_image, (0, 0))
            draw = ImageDraw.Draw(pil_image_canvas)
            draw.rectangle((pil_image.size[0], 0, pil_image.size[0] + 2,
                self.prefs['lens size from center'] * 2),
                fill=(self.prefs['red bg'] // 256,
                self.prefs['green bg'] // 256, self.prefs['blue bg'] // 256))
            pil_image_canvas.paste(pil_image2, (pil_image.size[0] + 2, 0))
            pil_image = pil_image_canvas

        # =======================================================
        # Add a nice border and convert back to pixbuf.
        # =======================================================
        pil_image = ImageOps.expand(pil_image, border=1, fill=(255, 255, 255))
        pil_image = ImageOps.expand(pil_image, border=1, fill=(0, 0, 0))
        imagestr = pil_image.tostring()
        pixbuf = \
            gtk.gdk.pixbuf_new_from_data(imagestr, gtk.gdk.COLORSPACE_RGB,
            (pixbuf.get_has_alpha() or both_pages), 8,
            (self.prefs['lens size from center'] *2 + 4),
            (self.prefs['lens size from center'] *2 + 4),
            (self.prefs['lens size from center'] *2 + 4) * 
            (3 + 1 * (pixbuf.get_has_alpha() or both_pages)))
        if not (pixbuf.get_has_alpha() or both_pages):
            pixbuf = pixbuf.add_alpha(False, 'W', 'T', 'F')

        # =======================================================
        # Set pixbuf as cursor. We have now "zoomed in" on the
        # image, and there was much rejoicing. :-)
        # =======================================================
        cursor = \
            gtk.gdk.Cursor(gtk.gdk.display_get_default(), pixbuf,
            (self.prefs['lens size from center'] + 2),
            (self.prefs['lens size from center'] + 2))
        self.layout.window.set_cursor(cursor)
        
        self.zooming_lens_manga_flip()
        
        # =======================================================
        # We need garbage cleanup here more often than the
        # Python GC will normally do. It is a quite costly operation
        # though, so we won't do it too often. This will introduce
        # a small periodic "hack" in the lens update flow, but it
        # will not be *that* annoying and is preferable to wasting 
        # many MBs of memory.
        #
        # FIXME: Is once every 30 times a good compromise?
        # =======================================================
        if self.lens_update_counter > 30:
            gc.collect()
            self.lens_update_counter = 0

        self.lens_timer = millisecs
        self.lens_update_counter += 1

    def zooming_lens_manga_flip(self):
        
        ''' Helper method to zooming_lens().
        Flips positions of the two images in the variables. Helps
        to keep zooming_lens() logic a little bit cleaner. '''
        
        if self.exit:
            return False
        
        if self.prefs['double page'] and self.prefs['manga']:
            temp = self.stored_pixbuf
            self.stored_pixbuf = self.stored_pixbuf2
            self.stored_pixbuf2 = temp
            temp = self.image1_width
            self.image1_width = self.image2_width
            self.image2_width = temp
            temp = self.image1_scaled_width
            self.image1_scaled_width = self.image2_scaled_width
            self.image2_scaled_width = temp
            temp = self.image1_height
            self.image1_height = self.image2_height
            self.image2_height = temp
            temp = self.image1_scaled_height
            self.image1_scaled_height = self.image2_scaled_height
            self.image2_scaled_height = temp
    
    def drag_image(self, event):
        
        ''' Handles dragging of the image with the mouse. '''

        # FIXME: This is relatively costly on CPU resources, can't it be
        # made more efficient?
        
        if self.exit:
            return False
        
        self.mouse_moved_while_drag = 1
        self.set_cursor_type('fleur')
        
        if not self.prefs['zoom mode'] == 1 or self.show_comments:
            if self.drag_timer == None:
                self.drag_timer = event.time - 100
            if event.time > self.drag_timer + 12:
                if (self.old_vadjust_value - event.y_root +
                    self.y_drag_position > self.vadjust_upper):
                    self.vadjust.set_value(self.vadjust_upper)
                    self.y_drag_position = event.y_root
                    self.old_vadjust_value = self.vadjust.value
                elif (self.old_vadjust_value - event.y_root +
                    self.y_drag_position < 0):
                    self.vadjust.set_value(0)
                    self.y_drag_position = event.y_root
                    self.old_vadjust_value = self.vadjust.value
                else:
                    self.vadjust.set_value(self.old_vadjust_value -
                        event.y_root + self.y_drag_position)
                if (self.old_hadjust_value - event.x_root +
                    self.x_drag_position > self.hadjust_upper):
                    self.hadjust.set_value(self.hadjust_upper)
                    self.x_drag_position = event.x_root
                    self.old_hadjust_value = self.hadjust.value
                elif (self.old_hadjust_value - event.x_root +
                    self.x_drag_position < 0):
                    self.hadjust.set_value(0)
                    self.x_drag_position = event.x_root
                    self.old_hadjust_value = self.hadjust.value
                else:
                    self.hadjust.set_value(self.old_hadjust_value -
                        event.x_root + self.x_drag_position)
                
                self.drag_timer = event.time
    
    def lens_switch(self, event):
        
        ''' Switch magnifying lens activation on/off (by the z-key,
        not by the middle mouse button.) '''
        
        self.set_cursor_type('normal')
        if not self.z_pressed:
            self.z_pressed = 1
            self.toolbutton_lens.set_active(True)
        else:
            self.z_pressed = 0
            self.toolbutton_lens.set_active(False)

    def lens_switch_tool(self, *args):
        
        if self.exit:
            return False

        if (self.z_pressed and self.toolbutton_lens.get_active() or
            not self.z_pressed and 
            not self.toolbutton_lens.get_active()):
            return

        if self.toolbutton_lens.get_active():
            self.actiongroup.get_action('Lens').set_active(True)
        else:
            self.actiongroup.get_action('Lens').set_active(False)
    
    def fullscreen_switch(self, event):
        
        ''' Switch fullscreen on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['fullscreen']:
            self.prefs['fullscreen'] = 0
            self.window.unfullscreen()
        else:
            self.prefs['fullscreen'] = 1
            self.window.fullscreen()

    def double_page_switch(self, event):
        
        ''' Switch double page mode on/off. '''
        
        if self.exit:
            return False
        
        if self.two_page_scan != None:
            self.two_page_scan = None
            self.number_of_cached = [-1]
            self.prefs['double page'] = 1
        if self.prefs['double page'] == 1:
            self.prefs['double page'] = 0
            self.cached_pixbuf = self.stored_pixbuf2
            try:
                self.number_of_cached.pop()
                self.number_of_cached.pop()
            except:
                pass
            self.number_of_cached.append(self.file_number + 1)
        else:
            self.prefs['double page'] = 1

        if self.prefs['double page']:
            self.actiongroup.get_action('Delete').set_sensitive(False)
            self.jpegtran_activate(False)
        elif self.archive_type == '':
            self.actiongroup.get_action('Delete').set_sensitive(True)
            self.jpegtran_activate(bool(self.jpegtran))

        if self.prefs['double page']:
            self.toolbutton_double_page.set_active(True)
        else:
            self.toolbutton_double_page.set_active(False)

        self.change_thumb_selection = 2
        self.refresh_image()

    def double_page_switch_tool(self, *args):
        
        if self.exit:
            return False

        if (self.prefs['double page'] and
            self.toolbutton_double_page.get_active() or
            not self.prefs['double page'] and 
            not self.toolbutton_double_page.get_active()):
            return

        if self.toolbutton_double_page.get_active():
            self.actiongroup.get_action('Double').set_active(True)
        else:
            self.actiongroup.get_action('Double').set_active(False)

    def zoom_mode_switch(self, event, data):
        
        self.prefs['zoom mode'] = data.get_current_value()

        if self.prefs['zoom mode'] == 0:
            toggle = True
        else:
            toggle = False

        self.actiongroup.get_action('Zin').set_sensitive(toggle)
        self.actiongroup.get_action('Zout').set_sensitive(toggle)
        self.actiongroup.get_action('Zoriginal').set_sensitive(toggle)
        self.actiongroup.get_action('Zwidth').set_sensitive(toggle)
        self.actiongroup.get_action('Zheight').set_sensitive(toggle)
        self.actiongroup.get_action('Zfit').set_sensitive(toggle)

        if self.prefs['zoom mode'] == 0:
            self.toolbutton_fitnone.set_active(True)
        elif self.prefs['zoom mode'] == 1:
            self.toolbutton_fitscreen.set_active(True)
        elif self.prefs['zoom mode'] == 2:
            self.toolbutton_fitwidth.set_active(True)
        else:
            self.toolbutton_fitheight.set_active(True)
        self.vadjust.set_value(0)
        if self.prefs['manga'] and not self.show_comments:
            self.hadjust.set_value(self.hadjust_upper)
        else:
            self.hadjust.set_value(0)
        self.refresh_image()

    def zoom_mode_switch_tool(self, type):
        
        if self.exit:
            return False
        
        if (self.prefs['zoom mode'] == type or not True in 
            [self.toolbutton_fitnone.get_active(),
             self.toolbutton_fitscreen.get_active(),
             self.toolbutton_fitwidth.get_active(),
             self.toolbutton_fitheight.get_active()]):
            return

        if type == 0:
            self.actiongroup.get_action('fit_manual_mode').set_active(True)
        elif type == 1:
            self.actiongroup.get_action('fit_screen_mode').set_active(True)
        elif type == 2:
            self.actiongroup.get_action('fit_width_mode').set_active(True)
        else:
            self.actiongroup.get_action('fit_height_mode').set_active(True)   
    
    def menubar_switch(self, event):
        
        ''' Switch menubar visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['show menubar']:
            self.prefs['show menubar'] = 0
        else:
            self.prefs['show menubar'] = 1
        self.refresh_image()
    
    def toolbar_switch(self, event):
        
        ''' Switch toolbar visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['show toolbar']:
            self.prefs['show toolbar'] = 0
        else:
            self.prefs['show toolbar'] = 1
        self.refresh_image()
    
    def statusbar_switch(self, event):
        
        ''' Switch statusbar visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['show statusbar']:
            self.prefs['show statusbar'] = 0
        else:
            self.prefs['show statusbar'] = 1
        self.refresh_image()
    
    def scrollbars_switch(self, event):
        
        ''' Switch scrollbar visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['hide scrollbar']:
            self.prefs['hide scrollbar'] = 0
        else:
            self.prefs['hide scrollbar'] = 1
        self.refresh_image()
    
    def comment_switch(self, event):
        
        ''' Switch comment visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.comment:
            if self.show_comments:
                self.show_comments = 0
                self.vadjust.set_value(0)
                if self.prefs['manga']:
                    self.hadjust.set_value(self.hadjust_upper)
                else:
                    self.hadjust.set_value(0)
            else:
                self.show_comments = 1
                self.comment_number = 0
            self.change_scroll_adjustment = 1
            self.refresh_image()
    
    def thumbnail_switch(self, event):
        
        ''' Switch thumbnail visibility on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['show thumbnails']:
            self.prefs['show thumbnails'] = 0
        else:
            self.prefs['show thumbnails'] = 1
        self.change_thumb_selection = 1
        self.refresh_image()
        self.load_thumbnails()
        self.refresh_image()
    
    def hide_all_switch(self, event):
        
        ''' Switch visibility of all on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['hide all']:
            self.prefs['hide all'] = 0
            self.prefs['hide scrollbar'], self.prefs['show menubar'], \
                self.prefs['show toolbar'], self.prefs['show statusbar'], \
                self.prefs['show thumbnails'] = \
                self.prefs['stored hide all values']
        else:
            self.prefs['hide all'] = 1
            self.prefs['stored hide all values'] = \
                self.prefs['hide scrollbar'], self.prefs['show menubar'], \
                self.prefs['show toolbar'], self.prefs['show statusbar'], \
                self.prefs['show thumbnails']
            self.prefs['hide scrollbar'], self.prefs['show menubar'], \
                self.prefs['show toolbar'], self.prefs['show statusbar'], \
                self.prefs['show thumbnails'] = 1, 0, 0, 0, 0
        self.change_thumb_selection = 1
        self.refresh_image()
        self.load_thumbnails()
        self.refresh_image()
    
    def manga_mode_switch(self, event):
        
        if self.exit:
            return False
            
        if self.prefs['manga']:
            self.prefs['manga'] = 0
            self.toolbutton_manga.set_active(False)
        else:
            self.prefs['manga'] = 1
            self.toolbutton_manga.set_active(True)
        if self.prefs['double page']:
            self.refresh_image()

    def manga_mode_switch_tool(self, *args):
        
        if self.exit:
            return False

        if (self.prefs['manga'] and self.toolbutton_manga.get_active() or
            not self.prefs['manga'] and not
            self.toolbutton_manga.get_active()):
            return

        if self.toolbutton_manga.get_active():
            self.actiongroup.get_action('manga_mode').set_active(True)
        else:
            self.actiongroup.get_action('manga_mode').set_active(False)
    
    def keep_transformation_switch(self, event):
        
        ''' Switch "keep transformation" on/off. '''
        
        if self.exit:
            return False
        
        if self.prefs['keep transformation']:
            self.prefs['keep transformation'] = 0
        else:
            self.prefs['keep transformation'] = 1
    
    def reg_expr_full_path_switch(self, event):
        
        ''' Switch full path on library regular expressions on/off. '''
        
        if self.exit:
            return False
        
        self.prefs['library filter on full path'] = \
            self.button_reg_expr.get_active()
    
    def rotate_90(self, data=None):
        
        ''' Rotates 90 degrees clockwise. '''
        
        if self.exit:
            return False
        
        self.prefs['rotation'] = (self.prefs['rotation'] + 1) % 4
        self.refresh_image()
    
    def rotate_180(self, data=None):
        
        ''' Rotates 180 degrees. '''
        
        if self.exit:
            return False
        
        self.prefs['rotation'] = (self.prefs['rotation'] + 2) % 4
        self.refresh_image()
    
    def rotate_270(self, data=None):
        
        ''' Rotates 270 degrees clockwise. '''
        
        if self.exit:
            return False
        
        self.prefs['rotation'] = (self.prefs['rotation'] + 3) % 4
        self.refresh_image()
    
    def flip_horizontally(self, data=None):
        
        ''' Flips image horizontally. '''
        
        if self.exit:
            return False
        
        if self.prefs['flip horiz'] == 0:
            self.prefs['flip horiz'] = 1
        else:
            self.prefs['flip horiz'] = 0
        self.refresh_image()
    
    def flip_vertically(self, data=None):
        
        ''' Flips image vertically. '''
        
        if self.exit:
            return False
        
        if self.prefs['flip vert'] == 0:
            self.prefs['flip vert'] = 1
        else:
            self.prefs['flip vert'] = 0
        self.refresh_image()
    
    def zoom_in(self, event):
        
        ''' Zooms in 15 %. '''
        
        if self.exit:
            return False
        
        if not self.prefs['zoom mode']:
            if self.prefs['zoom scale'] * 1.15 > 1000:
                self.prefs['zoom scale'] = 1000
            else:
                self.prefs['zoom scale'] = self.prefs['zoom scale'] * 1.15
            self.refresh_image()
    
    def zoom_out(self, event):
        
        ''' Zooms out 15 %. '''
        
        if self.exit:
            return False
        
        if not self.prefs['zoom mode']:
            if self.prefs['zoom scale'] * 0.85 < 10:
                scale = 10.0 / self.prefs['zoom scale']
                self.prefs['zoom scale'] = 10
            else:
                scale = 0.85
                self.prefs['zoom scale'] = self.prefs['zoom scale'] * 0.85
            self.refresh_image()
    
    def zoom_original(self, event):
        
        ''' Zooms to original size. '''
        
        if self.exit:
            return False
        
        if not self.prefs['zoom mode']:
            self.prefs['zoom scale'] = 100
            self.refresh_image()
    
    def zoom_width(self, event):
        
        ''' Zooms to fit width. '''
        
        if self.exit:
            return False
        
        self.update_sizes()
        if not self.prefs['zoom mode'] and self.file_exists:
            if not self.prefs['double page']:
                self.prefs['zoom scale'] = \
                    100.0 * self.main_layout_x_size / self.image1_width
            else:
                self.prefs['zoom scale'] = \
                    100.0 * self.main_layout_x_size / \
                    (self.image1_width + self.image2_width)
            if self.prefs['zoom scale'] > 1000:
                self.prefs['zoom scale'] = 1000.0
            self.refresh_image()
    
    def zoom_height(self, event):
        
        ''' Zooms to fit height. '''
        
        if self.exit:
            return False
        
        if not self.prefs['zoom mode'] and self.file_exists:
            self.update_sizes()
            if not self.prefs['double page']:
                self.prefs['zoom scale'] = \
                    100.0 * (self.main_layout_y_size) / self.image1_height
            else:
                if self.image1_height > self.image2_height:
                    height = self.image1_height
                else:
                    height = self.image2_height
                self.prefs['zoom scale'] = \
                    100.0 * (self.main_layout_y_size) / height
            if self.prefs['zoom scale'] > 1000:
                self.prefs['zoom scale'] = 1000.0
            self.refresh_image()
    
    def zoom_fit(self, event):
        
        ''' Zoom to best fit. '''
        
        if self.exit:
            return False
        
        if not self.prefs['zoom mode'] and self.file_exists:
            self.update_sizes()
            if self.prefs['double page']:
                width = self.image1_width + self.image2_width + 2
                height = max(self.image1_height, self.image2_height)
            else:
                width = self.image1_width
                height = self.image1_height
            if (float(width) / self.main_layout_x_size >
                float(height) / self.main_layout_y_size):
                self.zoom_width(None)
            else:
                self.zoom_height(None)
    
    def next_page(self, event):
        
        ''' Flips to the next page. '''
        
        if self.exit:
            return False
        
        # =======================================================
        # Flip comments.
        # =======================================================
        if self.show_comments:
            if self.comment_number < len(self.comment) - 1:
                self.comment_number = self.comment_number + 1
            else:
                self.vadjust.set_value(0)
                if self.prefs['manga']:
                    self.hadjust.set_value(self.hadjust_upper)
                else:
                    self.hadjust.set_value(0)
                self.show_comments = 0
            self.change_scroll_adjustment = 1
            self.change_thumb_selection = 1
            self.refresh_image()
        
        # =======================================================
        # Flip pages.
        # =======================================================
        else:
            flip_page = 0
            if not self.prefs['double page']:
                if self.file_number < len(self.file) - 1:
                    self.file_number = self.file_number + 1
                    flip_page = 1
            elif self.file_number < len(self.file) - 2:
                self.file_number = self.file_number + 2
                flip_page = 1
            if flip_page:
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 1
                if not self.prefs['keep transformation']:
                    self.prefs['rotation'] = 0
                    self.prefs['flip horiz'] = 0
                    self.prefs['flip vert'] = 0
                self.refresh_image()
            
            # =======================================================
            # Go to next archive.
            # =======================================================
            elif (self.archive_type != "" and 
                self.prefs['go to next archive'] and self.file_exists):
                self.set_cursor_type('watch')
                dir_list = os.listdir(os.path.dirname(self.path))
                dir_list.sort(locale.strcoll)
                for file in dir_list[dir_list.index(os.path.basename(
                    self.path)) + 1:]:
                    if (self.archive_mime_type(os.path.dirname(self.path) +
                        '/' + file)):
                        self.load_file(os.path.dirname(self.path) + '/' +
                            file, 0)
                        if self.file_exists:
                            self.refresh_image()
                        else:
                            self.close_file()
                        break
                self.set_cursor_type()
    
    def previous_page(self, event):
        
        ''' Flips to the previous page. '''
        
        if self.exit:
            return False
        
        # =======================================================
        # Flip comments.
        # =======================================================
        if self.show_comments:
            if self.comment_number > 0:
                self.comment_number = self.comment_number - 1
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 1
                self.refresh_image()
        
        # =======================================================
        # Flip pages.
        # =======================================================
        else:
            flip_page = 0
            if not self.prefs['double page'] or self.file_number == 1:
                if self.file_number > 0:
                    self.file_number = self.file_number - 1
                    flip_page = 1
            elif self.file_number > 1:
                self.file_number = self.file_number - 2
                flip_page = 1
            if flip_page:
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 1
                if not self.prefs['keep transformation']:
                    self.prefs['rotation'] = 0
                    self.prefs['flip horiz'] = 0
                    self.prefs['flip vert'] = 0
                self.refresh_image()
                self.vadjust.set_value(self.layout.get_size()[1] -
                    self.main_layout_y_size)
            
            # =======================================================
            # Go to previous archive.
            # =======================================================
            elif (self.archive_type != "" and 
                self.prefs['go to next archive'] and self.file_exists):
                self.set_cursor_type('watch')
                dir_list = os.listdir(os.path.dirname(self.path))
                dir_list.sort(locale.strcoll)
                for file in reversed(dir_list[:dir_list.index(
                    os.path.basename(self.path))]):
                    if (self.archive_mime_type(os.path.dirname(self.path) +
                        '/' + file)):
                        self.load_file(os.path.dirname(self.path) + '/' +
                            file, -1)
                        if self.file_exists:
                            self.refresh_image()
                            self.vadjust.set_value(self.layout.get_size()[1] -
                                self.main_layout_y_size)
                        else:
                            self.close_file()
                        break
                self.set_cursor_type()
    
    def first_page(self, event):
        
        ''' Flips to the first page. '''
        
        if self.exit:
            return False
        
        if self.show_comments:
            if self.comment_number != 0:
                self.comment_number = 0
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 1
                self.refresh_image()
        elif self.file_number != 0:
            self.file_number = 0
            self.change_scroll_adjustment = 1
            self.change_thumb_selection = 1
            if not self.prefs['keep transformation']:
                self.prefs['rotation'] = 0
                self.prefs['flip horiz'] = 0
                self.prefs['flip vert'] = 0
            self.refresh_image()
    
    def last_page(self, event):
        
        ''' Flips to the last page. '''
        
        if self.exit:
            return False
        
        if self.show_comments:
            if self.comment_number != len(self.comment) - 1:
                self.comment_number = len(self.comment) - 1
                self.change_scroll_adjustment = 1
                self.change_thumb_selection = 1
                self.refresh_image()
        elif self.file_number != len(self.file) - 1:
            self.file_number = len(self.file) - 1
            self.change_scroll_adjustment = 1
            self.change_thumb_selection = 1
            if not self.prefs['keep transformation']:
                self.prefs['rotation'] = 0
                self.prefs['flip horiz'] = 0
                self.prefs['flip vert'] = 0
            self.refresh_image()
    
    def go_to_page_dialog_open(self, event):
        
        ''' Opens the go-to-page dialog. '''
        
        if self.exit:
            return False
        
        self.button_page_spin.set_range(1, len(self.file))
        self.button_page_spin.set_value(self.file_number + 1)
        self.button_page_spin.grab_focus()
        self.go_to_page_label.set_text(
            ' ' + _('of') + ' ' + str(len(self.file)))
        self.go_to_page_dialog.show()
    
    def go_to_page_dialog_save_and_close(self, event, data):
        
        ''' Hides the go-to-page dialog and flips to the selected
        page. '''
        
        if self.exit:
            return False
        
        self.go_to_page_dialog.hide()
        if data == -5: # OK
            self.button_page_spin.update()
            if (int(self.button_page_spin.get_value()) > 0 and
                int(self.button_page_spin.get_value()) <= len(self.file)):
                if (int(self.button_page_spin.get_value()) - 1 !=
                    self.file_number):
                    self.show_comments = 0
                    self.file_number = \
                        int(self.button_page_spin.get_value()) - 1
                    self.change_scroll_adjustment = 1
                    self.change_thumb_selection = 1
                    if not self.prefs['keep transformation']:
                        self.prefs['rotation'] = 0
                        self.prefs['flip horiz'] = 0
                        self.prefs['flip vert'] = 0
                    self.refresh_image()
    
    def go_to_page_dialog_close(self, event, data=None):
        
        ''' Hides the go-to-page dialog. '''
        
        if self.exit:
            return False
        
        self.go_to_page_dialog.hide()
        return True
    
    def bookmark_dialog_open(self, event):
        
        ''' Opens the bookmarks dialog. '''
        
        if self.exit:
            return False
        
        self.bookmark_dialog.resize(50, 200)
        self.create_menus()
        
        if not self.bookmarks:
            self.bookmark_dialog.action_area.get_children()[1].set_sensitive(
                False)
        else:
            self.bookmark_dialog.action_area.get_children()[1].set_sensitive(
                True)
        if self.file_exists:
            self.bookmark_dialog.action_area.get_children()[2].set_sensitive(
                True)
        else:
            self.bookmark_dialog.action_area.get_children()[2].set_sensitive(
                False)
        
        self.bookmark_dialog.show()
    
    def bookmark_dialog_button_press(self, event, data):
        
        ''' Handles button presses in the bookmark dialog. '''
        
        if self.exit:
            return False
        
        if data == -7:
            self.bookmark_dialog.hide()
        elif data == -9:
            if len(self.bookmark_manager_tree_view.get_selection()
                .get_selected_rows()[1]) > 0:
                self.remove_bookmark(
                    self.bookmark_manager_tree_view.get_selection()
                    .get_selected_rows()[1][0][0])
        elif data == -8:
            self.add_menu_thumb(self.path)
    
    def bookmark_dialog_close(self, event, data=None):
        
        ''' Hides the bookmarks dialog. '''
        
        if self.exit:
            return False
        
        self.bookmark_dialog.hide()
        return True

    def are_you_sure_dialog_update(self, path, mode):
        
        ''' Opens the `Are you sure?` dialog. '''
        
        if self.exit:
            return False
        
        if mode == 'del':
            self.are_you_sure_label.set_text(
                _('Permanently remove %s?') % 
                ('"' + self.to_unicode(path) + '"'))
        elif mode == 'rot-flip':
            self.are_you_sure_label.set_text(
                _('Perform lossless JPEG operation on %s?') %
                ('"' + self.to_unicode(path) + '"') + '\n\n' +
                _('Some images might be trimmed a bit during the operation.'))
        elif mode == 'grayscale':
            self.are_you_sure_label.set_text(
                _('Permanently convert %s to greyscale?') %
                ('"' + self.to_unicode(path) + '"') + '\n\n' +
                _('Some images might be trimmed a bit during the operation.'))
        pixbuf_file = \
            gtk.gdk.pixbuf_new_from_file_at_size(
            self.file[self.file_number], 100, 100)   
        pixbuf = \
            gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
            pixbuf_file.get_width() + 2,
            pixbuf_file.get_height() + 2)
        pixbuf.fill(0x0)
        pixbuf_file.composite(pixbuf, 1, 1,
            pixbuf_file.get_width(), pixbuf_file.get_height(), 0,
            0, 1.0, 1.0, gtk.gdk.INTERP_NEAREST, 255)
        self.are_you_sure_image.set_from_pixbuf(pixbuf)
        del pixbuf_file
        gc.collect()
        
    def default_folder_chooser_dialog_open(self, data):
        
        ''' Opens the default folder chooser dialog. '''
        
        if self.exit:
            return False
        
        if os.path.isdir(self.temp_prefs['default open path']):
            self.select_default_folder_dialog.set_current_folder(
                self.temp_prefs['default open path'])
        else:
            self.select_default_folder_dialog.set_current_folder(
                os.getenv('HOME'))
        response = self.select_default_folder_dialog.run()
        # For some reason we need int()
        if int(response) == int(gtk.RESPONSE_OK):
            if (len(self.to_unicode(
                self.select_default_folder_dialog.get_filename())) > 50):
                self.filechooser_button.set_label('... ' + self.to_unicode(
                    self.select_default_folder_dialog.get_filename())[-47:])
            else:
                self.filechooser_button.set_label(self.to_unicode(
                    self.select_default_folder_dialog.get_filename()))
            self.temp_prefs['default open path'] = \
                self.select_default_folder_dialog.get_filename()
        self.select_default_folder_dialog.hide()
    
    def default_folder_chooser_dialog_close(self, event, data=None):
        
        ''' Hides the default folder chooser dialog. '''
        
        if self.exit:
            return False
        
        self.select_default_folder_dialog.hide()
        return True
    
    def convert_dialog_open(self, event):
        
        ''' Opens the convert archive dialog. '''
        
        if self.exit:
            return False
        
        if self.archive_type != '':
            self.convert_dialog.set_current_folder(os.path.dirname(self.path))
        else:
            self.convert_dialog.set_current_folder(os.path.dirname(
                os.path.dirname(self.path)))
        
        if self.prefs['last convert type'] == 'tar':
            self.convert_tree.get_selection().select_path(1)
        elif self.prefs['last convert type'] == 'gzip':
            self.convert_tree.get_selection().select_path(2)
        elif self.prefs['last convert type'] == 'bzip2':
            self.convert_tree.get_selection().select_path(3)
        else:
            self.convert_tree.get_selection().select_path(0)
        self.convert_dialog_change_type(None)
        self.convert_dialog.show()
        self.dir_removed = 0
    
    def convert_dialog_save_and_close(self, event, data):
        
        ''' Hides the convert archive dialog and converts the archive. '''
        
        if self.exit:
            return False
        
        self.convert_dialog.hide()
        old_path = self.path
        dst_path = self.convert_dialog.get_filename()
        
        if data == -5: # OK
            
            if os.path.exists(self.base_dir + 'convert'):
                shutil.rmtree(self.base_dir + 'convert')
                
            # =======================================================
            # Copy or extract files to self.base_dir + 'convert'
            # =======================================================
            if self.archive_type == '':
                shutil.copytree(os.path.dirname(self.path),
                    self.base_dir + 'convert/')
            else:
                os.mkdir(self.base_dir + 'convert')
                self.extract_archive(self.path,
                    self.base_dir + 'convert')
            
            # =======================================================
            # Now it's time to create the new archive.
            # =======================================================
            self.set_cursor_type('watch')
            
            # =======================================================
            # Create new Zip archive.
            # =======================================================
            if (self.convert_tree.get_selection().
                get_selected_rows()[1][0][0] == 0):
                try:
                    new_zip = \
                        zipfile.ZipFile(dst_path, 'w')
                except:
                    self.wrong_permissions_dialog_open(os.path.basename(
                        dst_path), 0)
                    return 0
                dir = os.getcwd()
                os.chdir(self.base_dir + 'convert')
                files = os.listdir('.')
                loop = 1
                while loop:
                    loop = 0
                    for i, file in enumerate(files):
                        if os.path.isdir(file):
                            files.pop(i)
                            temp_files = os.listdir(file)
                            for temp_file in temp_files:
                                temp_file = file + '/' + temp_file
                                files.append(temp_file)
                            loop = 1
                            break
                for i, file in enumerate(files):
                    file = self.to_unicode(file)
                    try:
                        name = file.encode('cp437')
                    except:
                        name = str(i) + '_unknown_encoding'
                    new_zip.write(file, name)
                new_zip.close()
                os.chdir(dir)
            
            # =======================================================
            # Create new tar archive.
            # =======================================================
            else:
                # Type of compression
                if (self.convert_tree.get_selection().
                    get_selected_rows()[1][0][0] == 1):
                    type = 'w'
                elif (self.convert_tree.get_selection().
                    get_selected_rows()[1][0][0] == 2):
                    type = 'w:gz'
                else:
                    type = 'w:bz2'
                try:
                    new_tar = \
                        tarfile.open(dst_path, type)
                except:
                    self.wrong_permissions_dialog_open(dst_path, 0)
                    return 0
                dir = os.getcwd()
                os.chdir(self.base_dir + 'convert')
                files = os.listdir('.')
                loop = 1
                while loop:
                    loop = 0
                    for i, file in enumerate(files):
                        if os.path.isdir(file):
                            files.pop(i)
                            temp_files = os.listdir(file)
                            for temp_file in temp_files:
                                temp_file = file + '/' + temp_file
                                files.append(temp_file)
                            loop = 1
                            break
                for file in files:
                    new_tar.add(file)
                new_tar.close()
                os.chdir(dir)
            
            # =======================================================
            # Remove temporary files.
            # =======================================================
            if os.path.exists(self.base_dir + 'convert'):
                shutil.rmtree(self.base_dir + 'convert')
            
            # =======================================================
            # Remove old archive/directory if the button was checked
            # unless it has already been overwritten with the new one.
            # =======================================================
            if self.convert_toggle_delete_old.get_active():
                if dst_path != self.path:
                    if self.archive_type == '':
                        try:
                            shutil.rmtree(os.path.dirname(self.path))
                        except:
                            self.wrong_permissions_dialog_open(
                                os.path.dirname(self.path), 1)
                    else:
                        try:
                            os.remove(self.path)
                        except:
                            self.wrong_permissions_dialog_open(self.path, 1)
            
            # =======================================================
            # Update some variables to fit the new file.
            # =======================================================
            if self.archive_type != '':
                if (self.convert_toggle_delete_old.get_active() or
                    dst_path == self.path):
                    if (self.convert_tree.get_selection()
                        .get_selected_rows()[1][0][0] == 0):
                        self.archive_type = _('Zip archive')
                    elif (self.convert_tree.get_selection()
                        .get_selected_rows()[1][0][0] == 1):
                        self.archive_type = _('Tar archive')
                    elif (self.convert_tree.get_selection()
                        .get_selected_rows()[1][0][0] == 2):
                        self.archive_type = \
                            _('Gzip compressed tar archive')
                    else:
                        self.archive_type = \
                            _('Bzip2 compressed tar archive')
                    self.path = dst_path
            else:
                if (self.convert_toggle_delete_old.get_active() or
                    dst_path == os.path.dirname(self.path)):
                    self.load_file(dst_path, self.file_number)
            self.refresh_image()
        
        # =======================================================
        # Update the library if the old file was in it and has
        # been replaced.
        # =======================================================
        if (old_path != self.path or
            self.convert_toggle_delete_old.get_active()):
            hash = md5.new()
            hash.update(old_path)
            hash = hash.hexdigest()
            hash_new = md5.new()
            hash_new.update(self.path)
            hash_new = hash_new.hexdigest()
            lib_dir = os.getenv('HOME') + '/.comix/library/'
            if os.path.isfile(lib_dir + hash):
                hash_file = open(lib_dir + hash)
                hash_info = hash_file.readlines()
                hash_file.close()
                hash_info[0] = self.path + '\n'
                if self.archive_type == _('Zip archive'):
                    hash_info[1] = 'zip\n'
                elif self.archive_type == _('Gzip compressed tar archive'):
                    hash_info[1] = 'gzip\n'
                elif self.archive_type == _('Bzip2 compressed tar archive'):
                    hash_info[1] = 'bzip2\n'
                elif self.archive_type == _('Tar archive'):
                    hash_info[1] = 'tar\n'
                else:
                    hash_info[1] = 'rar\n'
                hash_info[2] = str('%.1f' % (os.stat(self.path) \
                    [stat.ST_SIZE] / 1048576.0)) + '\n'
                hash_info[3] = str(os.stat(self.path)[stat.ST_MTIME]) + '\n'
                
                os.remove(lib_dir + hash)
                hash_file = open(lib_dir + hash_new, 'w')
                hash_file.write(hash_info[0] + hash_info[1] + hash_info[2] +
                    hash_info[3] + hash_info[4])
                hash_file.close()
            if hash + '.png' in os.listdir(lib_dir + 'covers'):
                os.rename(lib_dir + 'covers/' + hash + '.png', lib_dir +
                    'covers/' + hash_new + '.png')
            
            self.lib_window_loaded = 0
            if self.lib_window_is_open:
                self.library_load_files(None)
        
        self.set_cursor_type('normal')
        
        # =======================================================
        # Save the last used archive type.
        # =======================================================
        if (self.convert_tree.get_selection().
            get_selected_rows()[1][0][0] == 0):
            self.prefs['last convert type'] = 'zip'
        elif (self.convert_tree.get_selection().
            get_selected_rows()[1][0][0] == 1):
            self.prefs['last convert type'] = 'tar'
        elif (self.convert_tree.get_selection().
            get_selected_rows()[1][0][0] == 2):
            self.prefs['last convert type'] = 'gzip'
        else:
            self.prefs['last convert type'] = 'bzip2'
    
    def convert_dialog_close(self, event, data=None):
        
        ''' Hides the convert archive dialog. '''
        
        if self.exit:
            return False
        
        self.convert_dialog.hide()
        return True
    
    def convert_dialog_change_type(self, event):
        
        ''' Handles archive type selections in the convert archive dialog. '''
        
        if self.exit:
            return False
            
        if (self.convert_tree.get_selection().get_selected_rows()[1][0][0] ==
            0):
            ext = '.cbz'
        else:
            ext = '.cbt'
        
        if self.archive_type != '':
            self.convert_dialog.set_current_name(self.to_unicode(
                os.path.splitext(
                os.path.basename(self.path))[0] + ext))
        else:
            self.convert_dialog.set_current_name(self.to_unicode(
                os.path.splitext(
                os.path.basename(os.path.dirname(self.path)))[0] + ext))
        
    def preferences_dialog_open(self, event):
        
        ''' Opens the preferences dialog. '''
        
        if self.exit:
            return False
        
        self.notebook.set_current_page(0)
        
        # =======================================================
        # temp_prefs stores the values as we edit them in the
        # dialog. old_prefs stores the values we had when we
        # opened the dialog, so that we can revert back to them
        # if Cancel is pressed.
        # =======================================================
        self.temp_prefs = self.prefs.copy()
        self.old_prefs = self.prefs.copy()
        
        # =======================================================
        # Set the widgets in the dialog to represent the current
        # settings.
        # =======================================================
        self.button_fullscreen.set_active(self.prefs['default fullscreen'])
        self.button_page.set_active(self.prefs['default double page'])
        self.button_cache_next.set_active(self.prefs['cache'])
        self.button_stretch.set_active(self.prefs['stretch'])
        self.button_save_size.set_active(self.prefs['save window pos'])
        self.button_comment.set_active(self.prefs['auto comments'])
        self.button_next_archive.set_active(self.prefs['go to next archive'])
        self.button_hide_cursor.set_active(self.prefs['hide cursor'])
        self.button_hide_bars.set_active(self.prefs['hide in fullscreen'])
        self.button_scroll_flips.set_active(self.prefs['flip with wheel'])
        self.button_scroll_horiz.set_active(self.prefs['scroll wheel horiz'])
        self.button_smart_scale.set_active(
            self.prefs['smart double page scaling'])
        self.button_smart_space.set_active(self.prefs['smart space scroll'])
        self.button_thumb_scroll.set_active(
            self.prefs['hide thumbnail scrollbar'])
        self.button_open_last.set_active(self.prefs['auto load last file'])
        self.button_save_satcon.set_active(
            self.prefs['save saturation and contrast'])
        self.button_show_pagenumber.set_active(
            self.prefs['show page numbers on thumbnails'])
        self.button_autocontrast.set_active(self.prefs['autocontrast'])
        self.button_fake_double.set_active(self.prefs['emulate double page'])
        self.button_cache_thumbs.set_active(
            self.prefs['use stored thumbnails'])
        self.button_cache_arch_thumbs.set_active(
            self.prefs['use stored archive thumbnails'])
        self.button_two_page_scans.set_active(
            self.prefs['no double page for wide images'])
        self.button_store_recent.set_active(
            self.prefs['store recent file info'])
        if self.prefs['smart space scroll']:
            self.button_fake_double.set_sensitive(True)
        else:
            self.button_fake_double.set_sensitive(False)
        if self.prefs['open defaults to last browsed']:
            self.button_latest_path.set_active(True)
        else:
            self.button_default_path.set_active(True)
        if self.prefs['interp type'] == gtk.gdk.INTERP_NEAREST:
            self.button_1.set_active(True)
        elif self.prefs['interp type'] == gtk.gdk.INTERP_HYPER:
            self.button_4.set_active(True)
        elif self.prefs['interp type'] == gtk.gdk.INTERP_BILINEAR:
            self.button_3.set_active(True)
        else:
            self.button_2.set_active(True)
        if self.prefs['default zoom mode'] == 0:
            self.button_fit_manual_default.set_active(True)
        elif self.prefs['default zoom mode'] == 1:
            self.button_fit_screen_default.set_active(True)
        elif self.prefs['default zoom mode'] == 2:
            self.button_fit_width_default.set_active(True)
        else:
            self.button_fit_height_default.set_active(True)
        self.button_thumb_size.set_value(self.prefs['thumbnail size'])
        self.button_lib_thumb_size.set_value(self.prefs['library cover size'])
        self.button_lens_zoom.set_value(self.prefs['lens magnification'])
        self.button_lens_size.set_value(
            self.prefs['lens size from center'] * 2)
        self.button_lens_update.set_value(
            self.prefs['max lens update interval'])
        self.button_slideshow_delay.set_value(self.prefs['slideshow delay'])
        self.spin_space_scroll.set_value(self.prefs['space scroll length'])
        self.combo_space_scroll.set_active(self.prefs['space scroll type'])
        self.comment_extensions_entry.set_text(self.to_unicode(
            self.prefs['comment extensions']))
        self.colorbutton.set_color(gtk.gdk.colormap_get_system().alloc_color(
            gtk.gdk.Color(self.prefs['red bg'], self.prefs['green bg'],
            self.prefs['blue bg']), False, True))
        if len(self.to_unicode(self.prefs['default open path'])) > 50:
            self.filechooser_button.set_label('... ' +
                self.to_unicode(self.prefs['default open path'])[-47:])
        else:
            self.filechooser_button.set_label(self.to_unicode(
                self.prefs['default open path']))
        if self.prefs['toolbar style'] == gtk.TOOLBAR_TEXT:
            self.combobox_tool.set_active(1)
        elif self.prefs['toolbar style'] == gtk.TOOLBAR_BOTH:
            self.combobox_tool.set_active(2)
        else:
            self.combobox_tool.set_active(0)
        
        self.preferences_dialog.show()
    
    def preferences_dialog_save_and_close(self, data):
        
        ''' Updates the preferences from temp_prefs and hides the dialog
        if OK was pressed. '''
        
        if self.exit:
            return False
        
        if data == 'close':
            self.preferences_dialog.hide()
        
        # =======================================================
        # These settings should not be updated from temp_prefs
        # as they are not dependent on the preferences dialog and
        # might have been altered since the dialog was opened.
        # =======================================================
        fullscreen = self.prefs['fullscreen']
        manga = self.prefs['manga']
        x_res = self.prefs['window width']
        y_res = self.prefs['window height']
        fit_to_screen = self.prefs['zoom mode']
        double_page_mode = self.prefs['double page']
        scrollbar = self.prefs['hide scrollbar']
        menubar = self.prefs['show menubar']
        toolbar = self.prefs['show toolbar']
        statusbar = self.prefs['show statusbar']
        thumbs = self.prefs['show thumbnails']
        thumb_numbers = self.prefs['show page numbers on thumbnails']
        thumb_size = self.prefs['thumbnail size']
        rotation = self.prefs['rotation']
        two_page_scan = self.prefs['no double page for wide images']
        reg_expr = self.prefs['library filter on full path']
        lib_thumb_size = self.prefs['library cover size']
        store_recent = self.prefs['store recent file info']
        
        # =======================================================
        # Update prefs from with data from temp_prefs.
        # =======================================================
        if not os.path.exists(self.temp_prefs['default open path']):
            self.temp_prefs['default open path'] = \
                self.prefs['default open path']
        self.prefs.update(self.temp_prefs)
        
        # =======================================================
        # Put back the original data for these settings again
        # (see above.)
        # =======================================================
        self.prefs['fullscreen'] = fullscreen
        self.prefs['manga'] = manga
        self.prefs['window width'] = x_res
        self.prefs['window height'] = y_res
        self.prefs['zoom mode'] = fit_to_screen
        self.prefs['double page'] = double_page_mode
        self.prefs['hide scrollbar'] = scrollbar
        self.prefs['show menubar'] = menubar
        self.prefs['show toolbar'] = toolbar
        self.prefs['show statusbar'] = statusbar
        self.prefs['show thumbnails'] = thumbs
        self.prefs['rotation'] = rotation
        self.prefs['library filter on full path'] = reg_expr
        
        # =======================================================
        # Some settings that require extra attention.
        # =======================================================
        if self.prefs['no double page for wide images'] != two_page_scan:
            if self.two_page_scan != None:
                self.prefs['double page'] = 1
                self.two_page_scan = None
            self.change_thumb_selection = 1
        
        self.prefs['slideshow delay'] = \
            self.button_slideshow_delay.get_value()
        self.prefs['thumbnail size'] = \
            int(self.button_thumb_size.get_value())
        self.prefs['library cover size'] = \
            int(self.button_lib_thumb_size.get_value())
        self.prefs['lens magnification'] = self.button_lens_zoom.get_value()
        self.prefs['max lens update interval'] = \
            self.button_lens_update.get_value()
        self.prefs['lens size from center'] = \
            int(self.button_lens_size.get_value() / 2)
        self.prefs['space scroll length'] = self.spin_space_scroll.get_value()
        self.prefs['space scroll type'] = self.combo_space_scroll.get_active()
        self.prefs['red bg'] = self.colorbutton.get_color().red
        self.prefs['green bg'] = self.colorbutton.get_color().green
        self.prefs['blue bg'] = self.colorbutton.get_color().blue
        self.layout.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(gtk.gdk.Color(
            self.prefs['red bg'], self.prefs['green bg'], 
            self.prefs['blue bg']), False, True))
        if self.combobox_tool.get_active_text() == _('Text only'):
            self.prefs['toolbar style'] = gtk.TOOLBAR_TEXT
        elif self.combobox_tool.get_active_text() == _('Icons and text'):
            self.prefs['toolbar style'] = gtk.TOOLBAR_BOTH
        else:
            self.prefs['toolbar style'] = gtk.TOOLBAR_ICONS
        
        # =======================================================
        # If we just turned off the store recent files preference
        # we clear that list.
        # =======================================================
        if not self.prefs['store recent file info'] and store_recent:
            self.clear_recent_files()
        
        # =======================================================
        # Update comment files.
        # =======================================================
        if (self.prefs['comment extensions'] != 
            self.comment_extensions_entry.get_text()):
            self.prefs['comment extensions'] = \
                self.comment_extensions_entry.get_text()
            self.comment = []
            if self.file_exists:
                comment_extensions = \
                    map(lambda s: '.' + s,
                    self.prefs['comment extensions'].split())
                if self.archive_type != '':
                    comment_dir = self.base_dir
                else:
                    comment_dir = os.path.dirname(self.path) + '/'
                for infile in os.listdir(comment_dir):
                    infile = comment_dir + infile
                    if not os.path.isdir(infile):
                        if (os.path.splitext(infile)[1].lower() in
                            comment_extensions and 
                            gtk.gdk.pixbuf_get_file_info(infile) == None):
                            self.comment.append(infile)
                if self.comment_number > len(self.comment) - 1:
                    self.comment_number = 0
                if len(self.comment) > 0:
                    self.actiongroup.get_action(
                        'Comments').set_sensitive(True)
                else:
                    self.show_comments = 0
                    self.actiongroup.get_action(
                        'Comments').set_sensitive(False)
        
        self.refresh_image()
        
        # =======================================================
        # Update library or thumbnails if necessary.
        # =======================================================
        if self.prefs['library cover size'] != lib_thumb_size:
            self.lib_window_loaded = 0
            if self.lib_window_is_open:
                self.library_load_files(None)
        
        if (thumb_numbers != self.prefs['show page numbers on thumbnails'] or
            thumb_size != self.prefs['thumbnail size']):
            self.thumb_tree_view.get_selection().disconnect(
                self.thumb_selection_handler)
            self.thumb_column.set_fixed_width(
                self.prefs['thumbnail size'] + 7)
            self.thumb_layout.set_size_request(
                self.prefs['thumbnail size'] + 7, 0)
            self.change_thumb_selection = 1
            self.number_of_thumbs_loaded = 0
            self.thumb_vadjust.set_value(0)
            self.thumb_liststore.clear()
            self.thumb_heights = []
            self.thumb_total_height = 0
            self.thumb_loop_stop = 1
            self.thumb_selection_handler = \
                self.thumb_tree_view.get_selection().connect(
                'changed', self.thumb_selection_event)
            self.load_thumbnails()
            self.refresh_image()
    
    def preferences_dialog_close(self, event, data=None):
        
        ''' Hides the preferences dialog and reverts the preferences
        back to the ones we had when we opened the dialog. '''
        
        if self.exit:
            return False
        
        self.preferences_dialog.hide()
        
        fullscreen = self.prefs['fullscreen']
        manga = self.prefs['manga']
        x_res = self.prefs['window width']
        y_res = self.prefs['window height']
        fit_to_screen = self.prefs['zoom mode']
        double_page_mode = self.prefs['double page']
        scrollbar = self.prefs['hide scrollbar']
        menubar = self.prefs['show menubar']
        toolbar = self.prefs['show toolbar']
        statusbar = self.prefs['show statusbar']
        thumbs = self.prefs['show thumbnails']
        thumb_numbers = self.prefs['show page numbers on thumbnails']
        thumb_size = self.prefs['thumbnail size']
        rotation = self.prefs['rotation']
        reg_expr = self.prefs['library filter on full path']
        lib_thumb_size = self.prefs['library cover size']
        
        for key in self.old_prefs:
            self.prefs[key] = self.old_prefs[key]
        
        self.prefs['fullscreen'] = fullscreen
        self.prefs['manga'] = manga
        self.prefs['window width'] = x_res
        self.prefs['window height'] = y_res
        self.prefs['zoom mode'] = fit_to_screen
        self.prefs['double page'] = double_page_mode
        self.prefs['hide scrollbar'] = scrollbar
        self.prefs['show menubar'] = menubar
        self.prefs['show toolbar'] = toolbar
        self.prefs['show statusbar'] = statusbar
        self.prefs['show thumbnails'] = thumbs
        self.prefs['rotation'] = rotation
        self.prefs['library filter on full path'] = reg_expr
        
        self.layout.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(gtk.gdk.Color(
            self.prefs['red bg'], self.prefs['green bg'],
            self.prefs['blue bg']), False, True))
        
        self.refresh_image()
        
        if self.prefs['library cover size'] != lib_thumb_size:
            self.lib_window_loaded = 0
            if self.lib_window_is_open:
                self.library_load_files(None)
        
        if (thumb_numbers != self.prefs['show page numbers on thumbnails'] or
            thumb_size != self.prefs['thumbnail size']):
            self.thumb_column.set_fixed_width(
                self.prefs['thumbnail size'] + 7)
            self.thumb_layout.set_size_request(
                self.prefs['thumbnail size'] + 7, 0)
            self.change_thumb_selection = 1
            self.number_of_thumbs_loaded = 0
            self.thumb_vadjust.set_value(0)
            self.thumb_liststore.clear()
            self.thumb_heights = []
            self.thumb_total_height = 0
            self.thumb_loop_stop = 1
            self.load_thumbnails()
            self.refresh_image()
        
        return True
    
    def preferences_dialog_change_settings(self, widget, data):
        
        ''' Handles preference changes in the preferences dialog by
        updating temp_prefs as widgets report events. '''
        
        if self.exit:
            return False

        # FIXME: Rewrite this.
        
        if data == 0:
            if self.button_fullscreen.get_active():
                self.temp_prefs['default fullscreen'] = 1
            else:
                self.temp_prefs['default fullscreen'] = 0
        elif data == 1:
            if self.button_page.get_active():
                self.temp_prefs['default double page'] = 1
            else:
                self.temp_prefs['default double page'] = 0
        elif data == 7:
            if self.button_cache_next.get_active():
                self.temp_prefs['cache'] = 1
            else:
                self.temp_prefs['cache'] = 0
        #elif data == 8:
        # FREE!
        elif data == 9:
            if self.button_stretch.get_active():
                self.temp_prefs['stretch'] = 1
            else:
                self.temp_prefs['stretch'] = 0
        elif data == 10:
            if self.button_save_size.get_active():
                self.temp_prefs['save window pos'] = 1
            else:
                self.temp_prefs['save window pos'] = 0
        #elif data == 11:
        # FREE!
        elif data == 12:
            if self.button_hide_bars.get_active():
                self.temp_prefs['hide in fullscreen'] = 1
            else:
                self.temp_prefs['hide in fullscreen'] = 0
        elif data == 13:
            if self.button_smart_space.get_active():
                self.temp_prefs['smart space scroll'] = 1
                self.button_fake_double.set_sensitive(True)
            else:
                self.temp_prefs['smart space scroll'] = 0
                self.button_fake_double.set_sensitive(False)
        elif data == 14:
            if self.button_next_archive.get_active():
                self.temp_prefs['go to next archive'] = 1
            else:
                self.temp_prefs['go to next archive'] = 0
        elif data == 15:
            if self.button_hide_cursor.get_active():
                self.temp_prefs['hide cursor'] = 1
            else:
                self.temp_prefs['hide cursor'] = 0
        elif data == 16:
            if self.button_comment.get_active():
                self.temp_prefs['auto comments'] = 1
            else:
                self.temp_prefs['auto comments'] = 0
        elif data == 17:
            if self.button_scroll_horiz.get_active():
                self.temp_prefs['scroll wheel horiz'] = 1
            else:
                self.temp_prefs['scroll wheel horiz'] = 0
        elif data == 18:
            if self.button_scroll_flips.get_active():
                self.temp_prefs['flip with wheel'] = 1
            else:
                self.temp_prefs['flip with wheel'] = 0
        elif data == 19:
            if self.button_smart_scale.get_active():
                self.temp_prefs['smart double page scaling'] = 1
            else:
                self.temp_prefs['smart double page scaling'] = 0
        elif data == 20:
            if self.button_thumb_scroll.get_active():
                self.temp_prefs['hide thumbnail scrollbar'] = 1
            else:
                self.temp_prefs['hide thumbnail scrollbar'] = 0
        elif data == 21:
            if self.button_open_last.get_active():
                self.temp_prefs['auto load last file'] = 1
            else:
                self.temp_prefs['auto load last file'] = 0
        elif data == 22:
            self.temp_prefs['open defaults to last browsed'] = 0
        elif data == 23:
            self.temp_prefs['open defaults to last browsed'] = 1
        #elif data == 24:
        # FREE!
        elif data == 25:
            if self.button_show_pagenumber.get_active():
                self.temp_prefs['show page numbers on thumbnails'] = 1
            else:
                self.temp_prefs['show page numbers on thumbnails'] = 0
        #elif data == 26:
        # FREE!
        elif data == 27:
            if self.button_fake_double.get_active():
                self.temp_prefs['emulate double page'] = 1
            else:
                self.temp_prefs['emulate double page'] = 0
        elif data == 28:
            if self.button_cache_thumbs.get_active():
                self.temp_prefs['use stored thumbnails'] = 1
            else:
                self.temp_prefs['use stored thumbnails'] = 0
        elif data == 29:
            if self.button_cache_arch_thumbs.get_active():
                self.temp_prefs['use stored archive thumbnails'] = 1
            else:
                self.temp_prefs['use stored archive thumbnails'] = 0
        elif data == 30:
            if self.button_two_page_scans.get_active():
                self.temp_prefs['no double page for wide images'] = 1
            else:
                self.temp_prefs['no double page for wide images'] = 0
        elif data == 31:
            if self.button_store_recent.get_active():
                self.temp_prefs['store recent file info'] = 1
            else:
                self.temp_prefs['store recent file info'] = 0
        elif data == 32:
            self.temp_prefs['default zoom mode'] = 0
        elif data == 33:
            self.temp_prefs['default zoom mode'] = 1
        elif data == 34:
            self.temp_prefs['default zoom mode'] = 2
        elif data == 35:
            self.temp_prefs['default zoom mode'] = 3
        elif data == 2:
            self.temp_prefs['interp type'] = gtk.gdk.INTERP_NEAREST
        elif data == 3:
            self.temp_prefs['interp type'] = gtk.gdk.INTERP_TILES
        elif data == 4:
            self.temp_prefs['interp type'] = gtk.gdk.INTERP_BILINEAR
        elif data == 5:
            self.temp_prefs['interp type'] = gtk.gdk.INTERP_HYPER
    
    def about_dialog_open(self, data=None):
        
        ''' Opens the about dialog. '''
        
        if self.exit:
            return False
        
        self.about_dialog.action_area.get_children()[0].grab_focus()
        self.about_dialog.show()
    
    def about_dialog_close(self, event, data=None):
        
        ''' Hides the about dialog. '''
        
        if self.exit:
            return False
        
        self.about_dialog.hide()
        return True
    
    def thumbnail_maintenance_dialog_open(self, data=None):
        
        ''' Opens the thumbnail maintenance dialog. '''
        
        if self.exit:
            return False
        
        dir_path = os.getenv('HOME', '') + '/.thumbnails/normal/'
        arch_path = os.getenv('HOME', '') + '/.comix/archive_thumbnails/'
        
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, 0700)
        dir_size = 0
        for file in os.listdir(dir_path):
            dir_size += os.stat(dir_path + file)[stat.ST_SIZE] / 1048576.0
        self.dir_thumb_label.set_markup('<b>' + _('Location:') + '\n' +
            _('Quantity:') + '\n' + _('Total size:') + '\n</b>')
        self.dir_thumb_label2.set_text(self.to_unicode(dir_path) + '\n' +
            str(len(os.listdir(dir_path))) + '\n' + str('%.1f' % dir_size) +
            ' MiB\n')
        
        if not os.path.isdir(arch_path):
            os.makedirs(arch_path, 0700)
        arch_size = 0
        for file in os.listdir(arch_path):
            arch_size += os.stat(arch_path + file)[stat.ST_SIZE] / 1048576.0
        self.arch_thumb_label.set_markup('<b>' + _('Location:') + '\n' +
            _('Quantity:') + '\n' + _('Total size:') + '\n</b>')
        self.arch_thumb_label2.set_text(self.to_unicode(arch_path) + '\n' +
            str(len(os.listdir(arch_path))) + '\n' +
            str('%.1f' % arch_size) + ' MiB\n')
        
        self.thumbnail_dialog.show()
    
    def thumbnail_maintenance_dialog_close(self, event, data=None):
        
        ''' Hides the thumbnail maintenance dialog. '''
        
        if self.exit:
            return False
        
        self.thumbnail_dialog.hide()
        self.stop_thumb_maintenance = 1
        self.progress_dialog.hide()
        return True
    
    def thumbnail_maintenance_dialog_clean(self, data):
        
        ''' Clears or cleans up orphaned thumbnails. '''
        
        self.stop_thumb_maintenance = 0
        dir_path = os.getenv('HOME', '') + '/.thumbnails/normal/'
        arch_path = os.getenv('HOME', '') + '/.comix/archive_thumbnails/'
        
        # =======================================================
        # Clear all standard directory thumbnails.
        # =======================================================
        if data == 1:
            self.thumbnail_maintenance_dialog_progress_open()
            quantity = len(os.listdir(dir_path))
            counter = 0
            removed = 0
            self.progress_label.set_text(_('Removed:') + ' 0')
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
                os.chmod(dir_path, 0700)
            for file in os.listdir(dir_path):
                if self.stop_thumb_maintenance or self.exit:
                    return 0
                counter += 1
                os.remove(dir_path + file)
                removed += 1
                self.progress_label.set_text(
                    _('Removed:') + ' ' + str(removed))
                self.progress_bar.set_fraction(float(counter) / quantity)
                while gtk.events_pending():
                    gtk.main_iteration(False)
            self.progress_label.set_text(_('Removed:') + ' ' + str(removed) +
                '\n' + _('Done!'))
        
        # =======================================================
        # Clean up orphaned standard directory thumbnails.
        # =======================================================
        elif data == 2:
            self.thumbnail_maintenance_dialog_progress_open()
            quantity = len(os.listdir(dir_path))
            counter = 0
            removed = 0
            self.progress_label.set_text(_('Removed:') + ' 0')
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
                os.chmod(dir_path, 0700)
            for file in os.listdir(dir_path):
                counter += 1
                if self.stop_thumb_maintenance or self.exit:
                    return 0
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(dir_path + file)
                    mtime = pixbuf.get_option('tEXt::Thumb::MTime')
                    uri = pixbuf.get_option('tEXt::Thumb::URI')
                    uri = urllib.unquote(uri[7:])
                    if (not os.path.isfile(uri) or mtime !=
                        str(os.stat(uri)[stat.ST_MTIME])):
                        os.remove(os.getenv('HOME', '') +
                            '/.thumbnails/normal/' + file)
                        removed += 1
                        self.progress_label.set_text(
                            _('Removed:') + ' ' + str(removed))
                except:
                    os.remove(dir_path + file)
                    removed += 1
                    self.progress_label.set_text(
                        _('Removed:') + ' ' + str(removed))
                self.progress_bar.set_fraction(float(counter) / quantity)
                while gtk.events_pending():
                    gtk.main_iteration(False)
            self.progress_label.set_text(_('Removed:') + ' ' + str(removed) +
                '\n' + _('Done!'))
        
        # =======================================================
        # Clear all archive thumbnails.
        # =======================================================
        elif data == 3:
            self.thumbnail_maintenance_dialog_progress_open()
            quantity = len(os.listdir(arch_path))
            counter = 0
            removed = 0
            self.progress_label.set_text(_('Removed:') + ' 0')
            if not os.path.isdir(arch_path):
                os.makedirs(arch_path)
                os.chmod(arch_path, 0700)
            for file in os.listdir(arch_path):
                if self.stop_thumb_maintenance or self.exit:
                    return 0
                counter += 1
                os.remove(arch_path + file)
                removed += 1
                self.progress_label.set_text(
                    _('Removed:') + ' ' + str(removed))
                self.progress_bar.set_fraction(float(counter) / quantity)
                while gtk.events_pending():
                    gtk.main_iteration(False)
            self.progress_label.set_text(_('Removed:') + ' ' + str(removed) +
                '\n' + _('Done!'))
        
        # =======================================================
        # Clean up orphaned archive thumbnails.
        # =======================================================
        elif data == 4:
            self.thumbnail_maintenance_dialog_progress_open()
            quantity = len(os.listdir(arch_path))
            counter = 0
            removed = 0
            self.progress_label.set_text(_('Removed:') + ' 0')
            if not os.path.isdir(arch_path):
                os.makedirs(arch_path)
                os.chmod(arch_path, 0700)
            for file in os.listdir(arch_path):
                counter += 1
                if self.stop_thumb_maintenance or self.exit:
                    return 0
                try:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(arch_path + file)
                    mtime = pixbuf.get_option('tEXt::Thumb::MTime')
                    uri = pixbuf.get_option('tEXt::Thumb::URI')
                    uri = urllib.unquote(uri[7:])
                    if (not os.path.isfile(uri) or mtime !=
                        str(os.stat(uri)[stat.ST_MTIME])):
                        os.remove(arch_path + file)
                        removed += 1
                        self.progress_label.set_text(
                            _('Removed:') + ' ' + str(removed))
                except:
                    os.remove(arch_path + file)
                    removed += 1
                    self.progress_label.set_text(
                        _('Removed:') + ' ' + str(removed))
                self.progress_bar.set_fraction(float(counter) / quantity)
                while gtk.events_pending():
                    gtk.main_iteration(False)
            self.progress_label.set_text(_('Removed:') + ' ' + str(removed) +
                '\n' + _('Done!'))
        
        self.thumbnail_maintenance_dialog_open(None)
    
    def thumbnail_maintenance_dialog_progress_open(self):
        
        ''' Opens the thumbnail maintenance progress dialog. '''
        
        if self.exit:
            return False
        
        self.progress_dialog.show()
    
    def thumbnail_maintenance_dialog_progress_close(self, event, data=None):
        
        ''' Hides the thumbnail maintenance progress dialog. '''
        
        if self.exit:
            return False
        
        self.stop_thumb_maintenance = 1
        self.progress_dialog.hide()
        return True
    
    def properties_dialog_open(self, data=None):
        
        ''' Opens the properties dialog and updates it's information. '''
        
        if self.exit:
            return False
        
        # FIXME: This is ugly code.

        for child in self.properties_notebook.get_children():
            child.destroy()
        
        # =======================================================
        # Archive tab.
        # =======================================================
        if self.archive_type != '':
            main_box = gtk.VBox(False, 10)
            main_box.set_border_width(10)
            hbox = gtk.HBox(False, 10)
            main_box.pack_start(hbox, False, False, 0)
            try:
                cover_pixbuf = \
                    gtk.gdk.pixbuf_new_from_file_at_size(self.file[0],
                    200, 128)
                pixmap = \
                    gtk.gdk.Pixmap(self.window.window,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2, -1)
                pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2)
                pixmap.draw_pixbuf(None, cover_pixbuf, 0, 0, 1, 1, -1, -1,
                    gtk.gdk.RGB_DITHER_MAX, 0, 0)
                gc = pixmap.new_gc(gtk.gdk.Color(0, 0, 0))
                pixmap.draw_line(gc, 0, 0, cover_pixbuf.get_width() + 1, 0)
                pixmap.draw_line(gc, 0, 0, 0, cover_pixbuf.get_height() + 1)
                pixmap.draw_line(gc, cover_pixbuf.get_width() + 1, 0,
                    cover_pixbuf.get_width() + 1,
                    cover_pixbuf.get_height() + 1)
                pixmap.draw_line(gc, 0, cover_pixbuf.get_height() + 1,
                    cover_pixbuf.get_width() + 1,
                    cover_pixbuf.get_height() + 1)
                cover_pixbuf = \
                    gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2)
                cover_pixbuf.get_from_drawable(pixmap,
                    gtk.gdk.colormap_get_system(), 0, 0, 0, 0, -1, -1)
                cover_image = gtk.Image()
                cover_image.set_from_pixbuf(cover_pixbuf)
            except:
                cover_image = None
            if cover_image != None:
                hbox.pack_start(cover_image, False, False, 2)
            vbox = gtk.VBox(False, 2)
            vbox.set_border_width(6)
            ebox = gtk.EventBox()
            ebox.set_border_width(1)
            map = ebox.get_colormap()
            ebox.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#eadfc6'))
            ebox.add(vbox)
            ebox2 = gtk.EventBox()
            ebox2.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#888888'))
            ebox2.add(ebox)
            hbox.pack_start(ebox2, True, True, 2)
            filename = \
                ' ' + self.to_unicode(os.path.basename(self.path))
            if len(filename) > 35:
                filename = filename[:32] + '...'
            label = gtk.Label(filename)
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            vbox.pack_start(gtk.Alignment(0, 0, 0, 0), True, False, 0)
            label = gtk.Label(' ' + str(len(self.file)) + ' ' + _('pages'))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            if len(self.comment) == 1:
                label = gtk.Label(' ' + '1 ' + _('comment'))
            else:
                label = \
                    gtk.Label(' ' + str(len(self.comment)) + ' ' +
                    _('comments'))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = gtk.Label(' ' + self.archive_type)
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(' ' + str('%.1f' %
                (os.path.getsize(self.path) / 1048576.0)) + ' MiB')
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            vbox = gtk.VBox(False, 6)
            main_box.pack_start(vbox, False, False, 2)
            filename = ' ' + self.to_unicode(os.path.dirname(self.path))
            if len(filename) > 45:
                filename = filename[:42] + '...'
            label = \
                gtk.Label(_('Location') + ':  ' + filename)
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            hash = md5.new()
            hash.update(self.path)
            hash = hash.hexdigest()
            if os.path.isfile(os.getenv('HOME') + '/.comix/library/' + hash):
                label = \
                    gtk.Label(_('In library') + ':  ' + _('Yes'))
            else:
                label = \
                    gtk.Label(_('In library') + ':  ' + _('No'))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            if self.path in self.bookmarks:
                label = \
                    gtk.Label(_('Bookmarked') + ':  ' + _('Yes, page') + ' ' +
                    str(self.bookmark_numbers[self.bookmarks.index(
                    self.path)]))
            else:
                label = \
                    gtk.Label(_('Bookmarked') + ':  ' + _('No'))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Accessed') + ':  ' +
                    time.strftime('%Y-%m-%d   [%H:%M:%S]',
                    time.localtime(os.stat(self.path)[stat.ST_ATIME])))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Modified') + ':  ' +
                    time.strftime('%Y-%m-%d   [%H:%M:%S]',
                    time.localtime(os.stat(self.path)[stat.ST_MTIME])))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Permissions') + ':  ' +
                    str(oct(stat.S_IMODE(os.stat(self.path)[stat.ST_MODE]))))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Owner') + ':  ' +
                    pwd.getpwuid(os.stat(self.path)[stat.ST_UID])[0])
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            self.properties_notebook.insert_page(main_box,
                gtk.Label(_('Archive')))
        
        # =======================================================
        # Image (1) tab
        # =======================================================
        top_hbox = gtk.HBox(False, 5)
        main_box = gtk.VBox(False, 10)
        top_hbox.pack_start(main_box)
        top_hbox.set_border_width(10)
        hbox = gtk.HBox(False, 10)
        main_box.pack_start(hbox, False, False, 0)
        try:
            cover_pixbuf = \
                gtk.gdk.pixbuf_new_from_file_at_size(
                self.file[self.file_number], 200, 128)
            pixmap = \
                gtk.gdk.Pixmap(self.window.window,
                cover_pixbuf.get_width() + 2,
                cover_pixbuf.get_height() + 2, -1)
            pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                cover_pixbuf.get_width() + 2,
                cover_pixbuf.get_height() + 2)
            pixmap.draw_pixbuf(None, cover_pixbuf, 0, 0, 1, 1, -1, -1,
                gtk.gdk.RGB_DITHER_MAX, 0, 0)
            gc = pixmap.new_gc(gtk.gdk.Color(0, 0, 0))
            pixmap.draw_line(gc, 0, 0, cover_pixbuf.get_width() + 1, 0)
            pixmap.draw_line(gc, 0, 0, 0, cover_pixbuf.get_height() + 1)
            pixmap.draw_line(gc, cover_pixbuf.get_width() + 1, 0,
                cover_pixbuf.get_width() + 1, cover_pixbuf.get_height() + 1)
            pixmap.draw_line(gc, 0, cover_pixbuf.get_height() + 1,
                cover_pixbuf.get_width() + 1, cover_pixbuf.get_height() + 1)
            cover_pixbuf = \
                gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                cover_pixbuf.get_width() + 2, cover_pixbuf.get_height() + 2)
            cover_pixbuf.get_from_drawable(pixmap,
                gtk.gdk.colormap_get_system(), 0, 0, 0, 0, -1, -1)
            cover_image = gtk.Image()
            cover_image.set_from_pixbuf(cover_pixbuf)
        except:
            cover_image = None
        if cover_image != None:
            hbox.pack_start(cover_image, False, False, 2)
        vbox = gtk.VBox(False, 2)
        vbox.set_border_width(6)
        ebox = gtk.EventBox()
        ebox.set_border_width(1)
        map = ebox.get_colormap()
        ebox.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#eadfc6'))
        ebox.add(vbox)
        ebox2 = gtk.EventBox()
        ebox2.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#888888'))
        ebox2.add(ebox)
        hbox.pack_start(ebox2, True, True, 2)
        if self.archive_type != '':
            label = \
                gtk.Label(' ' + _('Page') + ' ' + str(self.file_number + 1))
        else:
            filename = \
                ' ' + self.to_unicode(os.path.basename(
                self.file[self.file_number]))
            if len(filename) > 35:
                filename = filename[:32] + '...'
            label = gtk.Label(filename)
        label.set_alignment(0, 0)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        vbox.pack_start(gtk.Alignment(0, 0, 0, 0), True, False, 0)
        label = \
            gtk.Label(' ' + str(self.image1_width) + 'x' +
            str(self.image1_height) + ' px')
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = \
            gtk.Label(' ' + str(self.image1_scaled_width) + 'x' +
            str(self.image1_scaled_height) + ' px (' +
            str('%.1f' % (100.0 * self.image1_scaled_width /
            self.image1_width)) + ' %)')
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = gtk.Label(' ' + gtk.gdk.pixbuf_get_file_info(self.file
            [self.file_number])[0]['mime_types'][0][6:].upper())
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = \
            gtk.Label(' ' + str('%.1f' %
            (os.path.getsize(self.file[self.file_number]) /
            1024.0)) + ' kiB')
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        
        vbox = gtk.VBox(False, 6)
        main_box.pack_start(vbox, True, True, 2)
        filename = \
            ' ' + self.to_unicode(os.path.dirname(
            self.file[self.file_number]))
        if len(filename) > 45:
            filename = filename[:42] + '...'
        label = gtk.Label(_('Location') + ':  ' + filename)
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        
        label = \
            gtk.Label(_('Accessed') + ':  ' +
                time.strftime('%Y-%m-%d   [%H:%M:%S]',
                time.localtime(os.stat(self.file[self.file_number])
                [stat.ST_ATIME])))
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = \
            gtk.Label(_('Modified') + ':  ' +
                time.strftime('%Y-%m-%d   [%H:%M:%S]',
                time.localtime(os.stat(self.file[self.file_number])
                [stat.ST_MTIME])))
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = \
            gtk.Label(_('Permissions') + ':  ' +
                str(oct(stat.S_IMODE(os.stat(self.file[self.file_number])
                [stat.ST_MODE]))))
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        label = \
            gtk.Label(_('Owner') + ':  ' +
                pwd.getpwuid(os.stat(self.file[self.file_number])
                [stat.ST_UID])[0])
        label.set_alignment(0, 0.5)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrlist)
        vbox.pack_start(label, False, False, 2)
        
        top_hbox.pack_start(gtk.VSeparator(), False, False, 5)
        expander = gtk.Expander()
        top_hbox.pack_start(expander, False, False, 0)
        hist_box = gtk.VBox(False, 2)
        hist_image, mean, median, stddev, pixels, sum, extrema, mode = \
            self.draw_histogram(self.stored_pixbuf, self.file_number)
        
        label = gtk.Label(_('Mode') + ':  ' + mode)
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        hist_box.pack_start(label, False, False, 2)
        label = gtk.Label(_('Pixel count') + ':  ' + str(pixels))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            label.get_text().index(':') + 1))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        hist_box.pack_start(label, False, False, 2)

        hist_box.pack_start(gtk.HSeparator(), False, False, 6)
        hbox = gtk.HBox(False, 30)
        hist_box.pack_start(hbox)

        label_box = gtk.VBox(False, 2)
        label = gtk.Label(_('Pixel sum'))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('R' + ':  ' + str(int(sum[0])))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('G' + ':  ' + str(int(sum[1])))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('B' + ':  ' + str(int(sum[2])))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        hbox.pack_start(label_box, False, False, 2)
        
        label_box = gtk.VBox(False, 2)
        label = gtk.Label(_('Extrema'))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('R' + ':  ' + str(extrema[0][0]) + '  -  ' +
            str(extrema[0][1]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('G' + ':  ' + str(extrema[1][0]) + '  -  ' +
            str(extrema[1][1]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = \
            gtk.Label('B' + ':  ' + str(extrema[2][0]) + '  -  ' +
            str(extrema[2][1]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        hbox.pack_start(label_box, False, False, 2)

        hist_image.set_alignment(0, 0.5)
        hist_box.pack_start(hist_image, False, False, 10)
        hbox = gtk.HBox(False, 20)
        hist_box.pack_start(hbox, False, False, 2)

        label_box = gtk.VBox(False, 2)
        label = gtk.Label(_('Mean'))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('R:  ' + '%3.1f' % mean[0])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('G:  ' + '%3.1f' % mean[1])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('B:  ' + '%3.1f' % mean[2])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        hbox.pack_start(label_box, False, False, 0)

        label_box = gtk.VBox(False, 2)
        label = gtk.Label(_('Median'))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('R:  ' + str(median[0]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('G:  ' + str(median[1]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('B:  ' + str(median[2]))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        hbox.pack_start(label_box, False, False, 0)

        label_box = gtk.VBox(False, 2)
        label = gtk.Label(_('Standard deviation'))
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(label.get_text())))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('R:  ' + '%3.1f' % stddev[0])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('G:  ' + '%3.1f' % stddev[1])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        label = gtk.Label('B:  ' + '%3.1f' % stddev[2])
        attrs = pango.AttrList()
        attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
        label.set_attributes(attrs)
        label.set_alignment(0, 0.5)
        label_box.pack_start(label, False, False, 2)
        hbox.pack_start(label_box, False, False, 0)
        
        expander.add(hist_box)

        if (not self.prefs['double page'] or
            self.file_number == len(self.file) - 1):
            self.properties_notebook.insert_page(top_hbox,
                gtk.Label(_('Image')))
        else:
            self.properties_notebook.insert_page(top_hbox,
                gtk.Label(_('Image 1')))
        
        # =======================================================
        # Image (2) tab
        # =======================================================
        if (self.prefs['double page'] and 
            self.file_number != len(self.file) - 1):
            top_hbox = gtk.HBox(False, 5)
            main_box = gtk.VBox(False, 10)
            top_hbox.pack_start(main_box)
            top_hbox.set_border_width(10)
            hbox = gtk.HBox(False, 10)
            main_box.pack_start(hbox, False, False, 0)
            try:
                cover_pixbuf = \
                    gtk.gdk.pixbuf_new_from_file_at_size(
                    self.file[self.file_number + 1], 200, 128)
                pixmap = \
                    gtk.gdk.Pixmap(self.window.window,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2, -1)
                pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2)
                pixmap.draw_pixbuf(None, cover_pixbuf, 0, 0, 1, 1, -1, -1,
                    gtk.gdk.RGB_DITHER_MAX, 0, 0)
                gc = pixmap.new_gc(gtk.gdk.Color(0, 0, 0))
                pixmap.draw_line(gc, 0, 0, cover_pixbuf.get_width() + 1, 0)
                pixmap.draw_line(gc, 0, 0, 0, cover_pixbuf.get_height() + 1)
                pixmap.draw_line(gc, cover_pixbuf.get_width() + 1, 0,
                    cover_pixbuf.get_width() + 1,
                    cover_pixbuf.get_height() + 1)
                pixmap.draw_line(gc, 0, cover_pixbuf.get_height() + 1,
                    cover_pixbuf.get_width() + 1,
                    cover_pixbuf.get_height() + 1)
                cover_pixbuf = \
                    gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                    cover_pixbuf.get_width() + 2,
                    cover_pixbuf.get_height() + 2)
                cover_pixbuf.get_from_drawable(pixmap,
                    gtk.gdk.colormap_get_system(), 0, 0, 0, 0, -1, -1)
                cover_image = gtk.Image()
                cover_image.set_from_pixbuf(cover_pixbuf)
            except:
                cover_image = None
            if cover_image != None:
                hbox.pack_start(cover_image, False, False, 2)
            vbox = gtk.VBox(False, 2)
            vbox.set_border_width(6)
            ebox = gtk.EventBox()
            ebox.set_border_width(1)
            map = ebox.get_colormap()
            ebox.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#eadfc6'))
            ebox.add(vbox)
            ebox2 = gtk.EventBox()
            ebox2.modify_bg(gtk.STATE_NORMAL, map.alloc_color('#888888'))
            ebox2.add(ebox)
            hbox.pack_start(ebox2, True, True, 2)
            if self.archive_type != '':
                label = \
                    gtk.Label(' ' + _('Page') + ' ' +
                    str(self.file_number + 2))
            else:
                filename = \
                    ' ' + self.to_unicode(os.path.basename(
                    self.file[self.file_number + 1]))
                if len(filename) > 35:
                    filename = filename[:32] + '...'
                label = gtk.Label(filename)
            label.set_alignment(0, 0)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            vbox.pack_start(gtk.Alignment(0, 0, 0, 0), True, False, 0)
            label = \
                gtk.Label(' ' + str(self.image2_width) + 'x' +
                str(self.image2_height) + ' px')
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(' ' + str(self.image2_scaled_width) + 'x' +
                str(self.image2_scaled_height) + ' px (' +
                str('%.1f' % (100.0 * self.image2_scaled_width /
                self.image2_width)) + ' %)')
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = gtk.Label(' ' + gtk.gdk.pixbuf_get_file_info(self.file
                [self.file_number + 1])[0]['mime_types'][0][6:].upper())
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(' ' + str('%.1f' %
                (os.path.getsize(self.file[self.file_number + 1]) /
                1024.0)) + ' kiB')
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            vbox = gtk.VBox(False, 6)
            main_box.pack_start(vbox, True, True, 2)
            filename = \
                ' ' + self.to_unicode(os.path.dirname(
                self.file[self.file_number + 1]))
            if len(filename) > 45:
                filename = filename[:42] + '...'
            label = gtk.Label(_('Location') + ':  ' + filename)
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            label = \
                gtk.Label(_('Accessed') + ':  ' +
                    time.strftime('%Y-%m-%d   [%H:%M:%S]',
                    time.localtime(os.stat(self.file[self.file_number + 1])
                    [stat.ST_ATIME])))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Modified') + ':  ' +
                    time.strftime('%Y-%m-%d   [%H:%M:%S]',
                    time.localtime(os.stat(self.file[self.file_number + 1])
                    [stat.ST_MTIME])))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Permissions') + ':  ' +
                str(oct(stat.S_IMODE(os.stat(
                self.file[self.file_number + 1])[stat.ST_MODE]))))
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            label = \
                gtk.Label(_('Owner') + ':  ' +
                    pwd.getpwuid(os.stat(self.file[self.file_number + 1])
                    [stat.ST_UID])[0])
            label.set_alignment(0, 0.5)
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrlist)
            vbox.pack_start(label, False, False, 2)
            
            top_hbox.pack_start(gtk.VSeparator(), False, False, 5)
            expander = gtk.Expander()
            top_hbox.pack_start(expander, False, False, 0)
            hist_box = gtk.VBox(False, 2)
            hist_image, mean, median, stddev, pixels, sum, extrema, mode = \
                self.draw_histogram(self.stored_pixbuf2, self.file_number + 1)
            
            label = gtk.Label(_('Mode') + ':  ' + mode)
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            hist_box.pack_start(label, False, False, 2)
            label = gtk.Label(_('Pixel count') + ':  ' + str(pixels))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                label.get_text().index(':') + 1))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            hist_box.pack_start(label, False, False, 2)

            hist_box.pack_start(gtk.HSeparator(), False, False, 6)
            hbox = gtk.HBox(False, 30)
            hist_box.pack_start(hbox)

            label_box = gtk.VBox(False, 2)
            label = gtk.Label(_('Pixel sum'))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('R' + ':  ' + str(int(sum[0])))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('G' + ':  ' + str(int(sum[1])))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('B' + ':  ' + str(int(sum[2])))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            hbox.pack_start(label_box, False, False, 2)
            
            label_box = gtk.VBox(False, 2)
            label = gtk.Label(_('Extrema'))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('R' + ':  ' + str(extrema[0][0]) + '  -  ' +
                str(extrema[0][1]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('G' + ':  ' + str(extrema[1][0]) + '  -  ' +
                str(extrema[1][1]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = \
                gtk.Label('B' + ':  ' + str(extrema[2][0]) + '  -  ' +
                str(extrema[2][1]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            hbox.pack_start(label_box, False, False, 2)

            hist_image.set_alignment(0, 0.5)
            hist_box.pack_start(hist_image, False, False, 10)
            hbox = gtk.HBox(False, 20)
            hist_box.pack_start(hbox, False, False, 2)

            label_box = gtk.VBox(False, 2)
            label = gtk.Label(_('Mean'))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('R:  ' + '%3.1f' % mean[0])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('G:  ' + '%3.1f' % mean[1])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('B:  ' + '%3.1f' % mean[2])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            hbox.pack_start(label_box, False, False, 0)

            label_box = gtk.VBox(False, 2)
            label = gtk.Label(_('Median'))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('R:  ' + str(median[0]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('G:  ' + str(median[1]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('B:  ' + str(median[2]))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            hbox.pack_start(label_box, False, False, 0)

            label_box = gtk.VBox(False, 2)
            label = gtk.Label(_('Standard deviation'))
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(label.get_text())))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('R:  ' + '%3.1f' % stddev[0])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('G:  ' + '%3.1f' % stddev[1])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            label = gtk.Label('B:  ' + '%3.1f' % stddev[2])
            attrs = pango.AttrList()
            attrs.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 2))
            label.set_attributes(attrs)
            label.set_alignment(0, 0.5)
            label_box.pack_start(label, False, False, 2)
            hbox.pack_start(label_box, False, False, 0)
            
            expander.add(hist_box)

            self.properties_notebook.insert_page(top_hbox,
                gtk.Label(_('Image 2')))
        
        self.properties_dialog.action_area.get_children()[0].grab_focus()
        self.properties_dialog.show_all()
    
    def properties_dialog_close(self, event, data=None):
        
        ''' Hides the properties dialog. '''
        
        if self.exit:
            return False
        
        self.properties_dialog.hide()
        return True
    
    def draw_histogram(self, pixbuf, file_number=None):
        
        ''' Draws a histogram from pixbuf and returns it as another
        pixbuf together with some statistics. '''

        dimensions = pixbuf.get_width(), pixbuf.get_height()
        stride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()
        mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
        pil_image = \
            Image.frombuffer(mode, dimensions, pixels, 'raw', mode, stride, 1)
        hist_data = pil_image.histogram()
        hist_rgb_im = Image.new('RGB', (256, 150), (50, 50, 50))
        maximum = \
            max(hist_data[:768] + [1])
        y_scale = float(150) / maximum
        for x in xrange(256):
            r = int(hist_data[x] * y_scale)
            g = int(hist_data[x + 256] * y_scale)
            b = int(hist_data[x + 512] * y_scale)
            for y, val in enumerate(reversed(xrange(150))):
                hist_rgb_im.putpixel((x, y), (255 * (r > val),
                    255 * (g > val), 255 * (b > val)))
        maxstr = 'max: ' + str(maximum)
        draw = ImageDraw.Draw(hist_rgb_im)
        draw.rectangle((0, 0, len(maxstr) * 6 + 2, 10), fill=(0, 0, 0))
        draw.text((2, 0), maxstr, fill=(255, 255, 255))
        hist_rgb_im = ImageOps.expand(hist_rgb_im, 2, (50, 50, 50))
        hist_rgb_im = ImageOps.expand(hist_rgb_im, 1, (0, 0, 0))
        imagestr = hist_rgb_im.tostring()
        IS_RGBA = hist_rgb_im.mode == 'RGBA'
        hist_rgb_pixbuf = \
            gtk.gdk.pixbuf_new_from_data(imagestr,
            gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8,
            hist_rgb_im.size[0], hist_rgb_im.size[1],
            (IS_RGBA and 4 or 3) * hist_rgb_im.size[0])
        hist_rgb_image = gtk.Image()
        hist_rgb_image.set_from_pixbuf(hist_rgb_pixbuf)
        stat = ImageStat.Stat(pil_image)
        # We load the image anew directly from PIL to get the real image mode
        # (e.g. RGB, CMYK, etc.). This is a lazy operation, and since we
        # don't do anything with the data it is very fast.
        try:
            im = Image.open(self.file[file_number])
            mode = im.mode
        except:
            mode = 'unknown'
        return (hist_rgb_image, stat.mean, stat.median, stat.stddev,
            stat.count[0], stat.sum, stat.extrema, mode)

    def wrong_permissions_dialog_open(self, path, remove):
        
        ''' Opens the wrong permissions warning dialog. '''
        
        if self.exit:
            return False
        
        self.set_cursor_type('normal')
        if remove:
            self.permission_label.set_markup('<b><big>' +
                _('Permission denied') + '</big></b>\n\n' +
                _('Could not delete') + ' "' + self.to_unicode(path) +
                '"\n' + _('Please check your permissions.'))
        else:
            self.permission_label.set_markup('<b><big>' +
                _('Permission denied') + '</big></b>\n\n' +
                _('Could not create') + ' "' + self.to_unicode(path) +
                '"\n' + _('Please check your permissions.'))
        self.permission_dialog.show()
    
    def wrong_permissions_dialog_close(self, event, data=None):
        
        ''' Hides the wrong permissions warning dialog. '''
        
        if self.exit:
            return False
        
        self.permission_dialog.hide()
        return True
    
    def library_open(self, event, data):
        
        ''' Opens an archive from the library. '''
        
        # =======================================================
        # Note: 
        # For the poor soul who reads this code, the whole 
        # library implementation is a big hack and should 
        # (someday) be rewritten more or less from scratch. 
        # Until then, this at least works.
        # =======================================================
        
        if self.exit:
            return False
        
        if self.lib_old_image != None:
            keys = self.cover_dict.keys()
            keys.sort(locale.strcoll)
            path = \
                keys[self.lib_old_image[1]].encode(
                sys.getfilesystemencoding())
            self.library_close(None, None)
            self.window.present()
            self.load_file(path, 0)
            self.refresh_image()
    
    def library_close(self, event, data=None):
        
        ''' Hides the library window. '''
        
        if self.exit:
            return False
        
        self.lib_window_is_open = 0
        self.lib_window.hide()
        return True
    
    def library_add_helper(self, event):
        
        ''' Calls library add with currently opened file as a parameter.
        Used because menu accelerators don't want to many parameters.
        Could probably be fixed in better way. '''
        
        self.library_add(None, [self.path])
    
    def library_add(self, event, data):
        
        ''' Adds archive(s) to the library. Some code blatantly copied
        from Christoph Wolk's comicthumb. '''
        
        if self.exit:
            return False
        
        # =======================================================
        # if data is a list of files to add we use it, otherwise
        # we open up a filechooser.
        # =======================================================
        if data != None:
            in_files = data
        else:
            self.adding_to_library = 1
            self.file_select.set_select_multiple(True)
            self.library_add_recursive_switch()
            in_files = self.file_chooser_open(None)
            self.file_select.set_select_multiple(False)
            self.adding_to_library = 0
        if in_files == None:
            return 0
        
        self.set_cursor_type('watch')
        
        # =======================================================
        # Recursive adding. All hail the os.walk method!
        # While in recursive mode we only add files with .cbr, 
        # .cbz or .cbt extension, to avoid adding too much other
        # files otherwise matching the magic numbers, such as
        # .jar etc.
        # =======================================================
        if self.lib_add_recursive_toggle.get_active():
            if os.path.isdir(in_files[0]):
                for tuple in os.walk(in_files[0]):
                    for file in tuple[2]:
                        file = os.path.join(tuple[0], file)
                        if (os.path.splitext(file)[1].lower() in
                            ['.cbr', '.cbz', '.cbt']):
                            in_files.append(file)
            in_files.pop(0)
        
        # =======================================================
        # We add all archives and show the progress with a
        # progress bar.
        # =======================================================
        self.stop_lib_maintenance = 0
        if self.lib_window_is_open:
            self.library_progress_dialog_open()
        quantity = len(in_files)
        counter = 0
        added = 0
        self.lib_progress_label.set_text(_('Added:') + ' 0')
        self.lib_progress_dialog.set_title(_('Adding library entries'))
        
        for path in in_files:
            if self.stop_lib_maintenance or self.exit:
                break
            type = self.archive_mime_type(path)
            if not os.path.isfile(path) or type == '':
                counter += 1
                self.lib_progress_label.set_text(
                    _('Added:') + ' ' + str(added))
                self.lib_progress_bar.set_fraction(float(counter) / quantity)
                while gtk.events_pending():
                    gtk.main_iteration(False)
                continue
            hash = md5.new()
            hash.update(path)
            hash = hash.hexdigest()
            lib_dir = os.getenv('HOME') + '/.comix/library/'
            if not os.path.exists(lib_dir):
                os.makedirs(lib_dir)
                os.chmod(lib_dir, 0700)
            thumb_dir = lib_dir + '/covers/'
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
                os.chmod(thumb_dir, 0700)
            size = str('%.1f' % (os.stat(path)[stat.ST_SIZE] / 1048576.0))
            mtime = str(os.stat(path)[stat.ST_MTIME])
            create_thumb = False
            if (os.path.isfile(thumb_dir + hash + '.png') and
                os.path.isfile(lib_dir + hash)):
                try:
                    hash_file = open(lib_dir + hash)
                    hash_info = hash_file.readlines()
                    hash_file.close()
                    if hash_info[3][:-1] != mtime:
                        create_thumb = True
                except:
                    create_thumb = True
            else:
                create_thumb = True
            if create_thumb:
                THUMB_SIZE = 128
                try:
                    if type == 'zip':
                        archive = zipfile.ZipFile(path, 'r')
                        files = archive.namelist()
                    elif type in ['tar', 'gzip', 'bzip2']:
                        archive = tarfile.open(path, 'r')
                        files = archive.getnames()
                    elif type == 'rar':
                        files = \
                            os.popen(self.rar + ' vb "' + path +
                                '"').readlines()
                        files = [file.rstrip('\n') for file in files]
                    cover = None
                    files.sort()
                    p = re.compile('cover|front', re.IGNORECASE)
                    exts = \
                        re.compile(
                        r'\.(jpg|png|jpeg|gif|bmp|tif|tiff|xpm|xbm|ico)\s*$',
                        re.IGNORECASE)
                    coverlist = filter(p.search, files)
                    coverlist = \
                        [s for s in coverlist if 'back' not in s.lower()]
                    for file in coverlist:
                        if exts.search(file):
                            cover = file
                            break
                    if cover == None:
                        for file in files:
                            if exts.search(file):
                                cover = file
                                break
                    if cover != None:
                        if type == 'rar':
                            os.popen(self.rar + ' p -inul -- "' + path + '" "' +
                                cover + '" > "' + thumb_dir +
                                '/temp" 2>/dev/null', "r").close()
                            image = Image.open(thumb_dir + '/temp')
                            os.remove(thumb_dir + '/temp')
                        elif type == 'zip':
                            image = \
                                Image.open(StringIO.StringIO(
                                archive.read(cover)))
                            archive.close()
                        elif type in ['tar', 'gzip', 'bzip2']:
                            image = \
                                Image.open(StringIO.StringIO(
                                archive.extractfile(cover).read()))
                            archive.close()
                    
                    if image.size[0] > image.size[1]:
                        x = THUMB_SIZE
                        y = THUMB_SIZE * image.size[1] / image.size[0]
                    else:
                        x = THUMB_SIZE * image.size[0] / image.size[1]
                        y = THUMB_SIZE
                    image = image.resize((x, y), Image.ANTIALIAS)
                    image = image.convert('RGB')
                    imagestr = image.tostring()
                    IS_RGBA = image.mode == 'RGBA'
                    pixbuf = \
                        gtk.gdk.pixbuf_new_from_data(imagestr,
                        gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8, image.size[0],
                        image.size[1],
                        (IS_RGBA and 4 or 3) * image.size[0])
                    pixbuf.save(thumb_dir + hash + '.pngcomix_' +
                        constants.version + '_temp', 'png', {
                        'tEXt::Thumb::URI':'file://' +
                        urllib.pathname2url(path),
                        'tEXt::Thumb::MTime':mtime,
                        'tEXt::Thumb::Size':size,
                        'tEXt::Software':'Comix ' + constants.version})
                    os.chmod(thumb_dir + hash + '.pngcomix_' +
                        constants.version + '_temp', 0600)
                    os.rename(thumb_dir + hash + '.pngcomix_' +
                        constants.version + '_temp',
                        thumb_dir + hash + '.png')
                    name = self.to_unicode(path)
                    pages = str(len(filter(exts.search, files)))
                    lib_file = open(lib_dir + hash, 'w')
                    lib_file.write(
                        name + '\n' + 
                        type + '\n' + 
                        size + '\n' + 
                        mtime + '\n' +
                        pages + '\n')
                    lib_file.close()
                    os.chmod(lib_dir + hash, 0600)
                    added += 1
                    del pixbuf
                    del image
                    gc.collect()
                except:
                    try:
                        os.remove(lib_dir + hash)
                    except:
                        pass
                    try:
                        os.remove(thumb_dir + hash + '.png')
                    except:
                        pass
            counter += 1
            self.lib_progress_label.set_text(_('Added:') + ' ' + str(added))
            self.lib_progress_bar.set_fraction(float(counter) / quantity)
            while gtk.events_pending():
                gtk.main_iteration(False)
        self.lib_progress_label.set_text(_('Added:') + ' ' + str(added) +
            '\n' + _('Done!'))
        
        self.lib_window_loaded = 0
        if self.lib_window_is_open:
            self.library_load_files(None)
        self.set_cursor_type('normal')
        
    def library_add_recursive_switch(self, *args):
        
        if self.lib_add_recursive_toggle.get_active():
            self.file_select.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        else:
            self.file_select.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    
    def library_remove(self, event, data):
        
        ''' Removes an archive from the library. '''
        
        if self.exit:
            return False
        
        if self.lib_old_image != None:
            keys = self.cover_dict.keys()
            keys.sort(locale.strcoll)
            path = \
                keys[self.lib_old_image[1]].encode(
                sys.getfilesystemencoding())
            hash = md5.new()
            hash.update(path)
            hash = hash.hexdigest()
            lib_dir = os.getenv('HOME') + '/.comix/library/'
            if os.path.exists(lib_dir + hash):
                os.remove(lib_dir + hash)
            if os.path.exists(lib_dir + 'covers/' + hash + '.png'):
                os.remove(lib_dir + 'covers/' + hash + '.png')
            self.lib_window_loaded = 0
            self.lib_old_image = None
            self.library_load_files(None)
    
    def library_clean_up(self, event, data):
        
        ''' Removes orphaned library entries. '''
        
        if self.exit:
            return False
        
        self.stop_lib_maintenance = 0
        lib_dir = os.getenv('HOME') + '/.comix/library/'
        self.library_progress_dialog_open()
        quantity = len(self.cover_dict.keys())
        counter = 0
        removed = 0
        self.lib_progress_label.set_text(_('Removed:') + ' 0')
        self.lib_progress_dialog.set_title(_('Removing library entries'))
        
        if not os.path.isdir(lib_dir):
            os.makedirs(lib_dir)
            os.chmod(lib_dir, 0700)
        
        for key in self.cover_dict.keys():
            if self.stop_lib_maintenance or self.exit:
                break
            try:
                path = key.encode(sys.getfilesystemencoding())
            except:
                # FIXME!
                counter += 1
                continue
            if (not os.path.isfile(path) or
                str(os.stat(path)[stat.ST_MTIME]) != self.cover_dict[key][2]):
                hash = md5.new()
                hash.update(path)
                hash = hash.hexdigest()
                if os.path.isfile(lib_dir + hash):
                    os.remove(lib_dir + hash)
                if os.path.isfile(lib_dir + 'covers/' + hash + '.png'):
                    os.remove(lib_dir + 'covers/' + hash + '.png')
                removed += 1
            counter += 1
            self.lib_progress_label.set_text(
                _('Removed:') + ' ' + str(removed))
            self.lib_progress_bar.set_fraction(float(counter) / quantity)
            
            while gtk.events_pending():
                gtk.main_iteration(False)
        
        self.lib_progress_label.set_text(_('Removed:') + ' ' + str(removed) +
            '\n' + _('Done!'))
        self.lib_old_image = None
        self.lib_window_loaded = 0
        self.library_load_files(None)
    
    def library_load_files(self, event):
        
        ''' Loads all the cover images and archive data from
        ~/.comix/library. '''
        
        if self.exit:
            return False
            
        self.set_cursor_type('watch')
        self.lib_window_is_open = 1
        
        if not self.lib_window_loaded:
            for c in self.lib_event_boxes:
                c.destroy()
            for c in self.lib_tables:
                c.destroy()
            for c in self.lib_layout.get_children():
                for cc in c:
                    for ccc in cc:
                        ccc.destroy()
                    cc.destroy()
                c.destroy()
            self.lib_old_image = None
            self.cover_dict = {}
            self.lib_tooltips = gtk.Tooltips()
            self.lib_cover_name.set_text('')
            self.lib_cover_pages.set_text('')
            self.lib_cover_type.set_text('')
            self.lib_cover_size.set_text('')
            self.button_reg_expr.set_active(
                self.prefs['library filter on full path'])
            lib_dir = os.getenv('HOME') + '/.comix/library/'
            if not os.path.exists(lib_dir):
                os.makedirs(lib_dir)
                os.chmod(lib_dir, 0700)
            thumb_dir = lib_dir + 'covers/'
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
                os.chmod(thumb_dir, 0700)
                
            for file in os.listdir(lib_dir):
                if os.path.isfile(lib_dir + file):
                    info_file = open(lib_dir + file)
                    info = info_file.readlines()
                    info_file.close()
                    try:
                        self.cover_dict[info[0][:-1]] = \
                            [info[1][:-1], info[2][:-1], info[3][:-1],
                            thumb_dir + file + '.png', info[4][:-1]]
                    except:
                        pass
                        
            keys = self.cover_dict.keys()
            keys.sort(locale.strcoll)
            self.lib_event_boxes = []
            
            for i, key in enumerate(keys):
                try:
                    pixbuf_file = \
                        gtk.gdk.pixbuf_new_from_file_at_size(
                        self.cover_dict[key][3],
                        self.prefs['library cover size'],
                        self.prefs['library cover size'])   
                    pixbuf = \
                        gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
                        pixbuf_file.get_width() + 4,
                        pixbuf_file.get_height() + 4)
                    pixbuf.fill(0xffffffff)
                    pixbuf_file.composite(pixbuf, 2, 2,
                        pixbuf_file.get_width(), pixbuf_file.get_height(), 0,
                        0, 1.0, 1.0, gtk.gdk.INTERP_NEAREST, 255)
                    image = gtk.Image()
                    image.set_from_pixbuf(pixbuf)
                    event_box = gtk.EventBox()
                    event_box.add(image)
                    # Increases speed for clicking library entries (???)
                    event_box.set_size_request(pixbuf.get_width(),
                        self.prefs['library cover size'] + 4)
                    event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(
                        0, 0, 0))
                    event_box.set_events(gtk.gdk.BUTTON_PRESS)
                    event_box.connect('button_press_event',
                        self.library_select_archive, i)
                    self.lib_event_boxes.append(event_box)
                    self.lib_tooltips.set_tip(event_box,
                        os.path.basename(key))
                except:
                   pass
            
            self.library_update()
            self.lib_window_loaded = 1

        self.set_cursor_type('normal')
        gc.collect()
        self.lib_window.show()
        self.lib_window.present()
        
    def library_area_resize_event(self, window, allocation):
        
        if self.library_update_timer_id != None:
            gobject.source_remove(self.library_update_timer_id)
        
        self.library_update_timer_id = \
            gobject.timeout_add(1000, self.library_update,
            None, (allocation.width, allocation.height))
    
    def library_update(self, bogus=None, area=None):
        
        ''' Draws the covers in the library screen. '''
        
        if (area == None or area[0] != self.prefs['lib window width'] or
            area[1] != self.prefs['lib window height']):
            for c in self.lib_layout.get_children():
                for cc in c.get_children():
                    c.remove(cc)
                self.lib_layout.remove(c)
            
            width = \
                self.lib_window.get_size()[0] - \
                self.lib_vscroll.get_size_request()[0] - 20
            col, row_width, row = 0, 10, 0
            self.lib_tables = []
            table = gtk.Table(2, 2, False)
            self.lib_tables.append(table)
            table.set_row_spacings(10)
            table.set_col_spacings(10)
            self.lib_layout.put(table, 10, 10)
            pattern = self.lib_search_box.get_text()
            keys = self.cover_dict.keys()
            keys.sort(locale.strcoll)
            displayed_archives = 0
            
            if pattern != '':
                pattern = re.compile(pattern, re.IGNORECASE)
            
            for i, box in enumerate(self.lib_event_boxes):
                if self.prefs['library filter on full path']:
                    filter_string = keys[i]
                else:
                    filter_string = os.path.basename(keys[i])
                if pattern == '' or pattern.search(filter_string):
                    row_width = row_width + box.get_size_request()[0] + 10
                    if row_width > width:
                        row_width = box.get_size_request()[0] + 20
                        col = 0
                        row += 1
                        table = gtk.Table(2, 2, False)
                        self.lib_tables.append(table)
                        table.set_row_spacings(10)
                        table.set_col_spacings(10)
                        self.lib_layout.put(table, 10,
                            (self.prefs['library cover size'] + 14) *
                            row + 10)
                    table.attach(box, col, col + 1, 0, 1, gtk.FILL|gtk.EXPAND,
                        gtk.FILL|gtk.EXPAND, 0, 0)
                    col += 1
                    displayed_archives += 1
            self.lib_layout.set_size(self.lib_window.get_size()[1] -
                self.lib_vscroll.get_size_request()[1] - 20,
                (self.prefs['library cover size'] + 14) * (row + 1) + 10)
            self.lib_layout.show_all()
            self.prefs['lib window width'], \
                self.prefs['lib window height'] = self.lib_window.get_size()
            if self.lib_old_image == None:
                self.lib_open_button.set_sensitive(False)
                self.lib_remove_button.set_sensitive(False)
            self.lib_window.set_title(_('Library') + ' --- [' +
                str(displayed_archives) + ' / ' +
                str(len(self.lib_event_boxes)) + ']')
    
    def library_select_archive(self, widget, event, number):
        
        ''' Handles selections of archives in the library. '''
        
        if event.button == 1:
            if (self.lib_select_timer > event.time - 200 and
                self.lib_old_image != None and
                number == self.lib_old_image[1]):
                self.layout.handler_block(self.button_release_event_id)
                self.library_open(None, None)
                if self.exit:
                    return False
                self.layout.handler_unblock(self.button_release_event_id)
                return
            self.lib_select_timer = event.time
        
        if self.lib_old_image != None:
            box = self.lib_event_boxes[self.lib_old_image[1]]
            box.get_children()[0].set_from_pixbuf(self.lib_old_image[0])
            table = box.get_parent()
            if self.lib_tables.count(table) > 0:
                pos = self.lib_tables.index(table)
                self.lib_layout.remove(table)
                self.lib_layout.put(table, 10,
                    (self.prefs['library cover size'] + 14) * pos + 10)
        pixbuf = self.lib_event_boxes[number].get_children()[0].get_pixbuf()
        self.lib_old_image = (pixbuf.copy(), number)
        assert(pixbuf.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
        dimensions = pixbuf.get_width(), pixbuf.get_height()
        stride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()
        mode = pixbuf.get_has_alpha() and "RGBA" or "RGB"
        pil_image = \
            Image.frombuffer(mode, dimensions, pixels, "raw", mode, stride, 1)
        draw = ImageDraw.Draw(pil_image)
        draw.rectangle(((0, 0),
            (pil_image.size[0] - 1, pil_image.size[1] - 1)),
            outline=(20, 118, 193))
        draw.rectangle(((1, 1),
            (pil_image.size[0] - 2, pil_image.size[1] - 2)),
            outline=(20, 118, 193))
        draw.rectangle(((2, 2),
            (pil_image.size[0] - 3, pil_image.size[1] - 3)),
            outline=(255, 255, 255))
        imagestr = pil_image.tostring()
        IS_RGBA = pil_image.mode == 'RGBA'
        pixbuf = \
            gtk.gdk.pixbuf_new_from_data(imagestr,
            gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8, pil_image.size[0],
            pil_image.size[1],
            (IS_RGBA and 4 or 3) * pil_image.size[0])        
        box = self.lib_event_boxes[number]
        box.get_children()[0].set_from_pixbuf(pixbuf)
        keys = self.cover_dict.keys()
        keys.sort(locale.strcoll)
        self.lib_cover_name.set_text(os.path.basename(keys[number]))
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
            len(self.lib_cover_name.get_text())))
        attrlist.insert(pango.AttrSize(10000, 0,
            len(self.lib_cover_name.get_text())))
        self.lib_cover_name.set_attributes(attrlist)
        self.lib_cover_pages.set_text(
            self.cover_dict[keys[number]][4] + ' ' + _('pages'))
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrSize(10000, 0,
            len(self.lib_cover_pages.get_text())))
        self.lib_cover_pages.set_attributes(attrlist)
        
        if self.cover_dict[keys[number]][0] == 'zip':
            type = _('Zip archive')
        elif self.cover_dict[keys[number]][0] == 'tar':
            type = _('Tar archive')
        elif self.cover_dict[keys[number]][0] == 'gzip':
            type = _('Gzip compressed tar archive')
        elif self.cover_dict[keys[number]][0] == 'bzip2':
            type = _('Bzip2 compressed tar archive')
        else:
            type = _('RAR archive')
        self.lib_cover_type.set_text(type)
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrSize(10000, 0,
            len(self.lib_cover_type.get_text())))
        self.lib_cover_type.set_attributes(attrlist)
        self.lib_cover_size.set_text(
            self.cover_dict[keys[number]][1] + ' MiB')
        attrlist = pango.AttrList()
        attrlist.insert(pango.AttrSize(10000, 0,
            len(self.lib_cover_size.get_text())))
        self.lib_cover_size.set_attributes(attrlist)
        
        self.lib_open_button.set_sensitive(True)
        self.lib_remove_button.set_sensitive(True)
    
    def library_progress_dialog_open(self):
        
        ''' Opens the library progress dialog. '''
        
        if self.exit:
            return False
        
        self.lib_progress_dialog.show()
    
    def library_progress_dialog_close(self, event, data=None):
        
        ''' Hides the library progress dialog. '''
        
        if self.exit:
            return False
        
        self.stop_lib_maintenance = 1
        self.lib_progress_dialog.hide()
        return True
    
    def file_chooser_open(self, event, data=None):
        
        ''' Opens the file chooser dialog. '''
        
        if self.exit:
            return False

        if len(self.prefs['default open path']) > 0:
            if self.prefs['default open path'][-1:] != '/':
                self.prefs['default open path'] += '/'
        else:
            self.prefs['default open path'] = '/'
        if len(self.prefs['path of last browsed']) > 0:
            if self.prefs['path of last browsed'][-1:] != '/':
                self.prefs['path of last browsed'] += '/'
        else:
            self.prefs['path of last browsed'] = '/'
        if (self.prefs['open defaults to last browsed'] and
            os.path.isdir(self.prefs['path of last browsed'])):
            self.file_select.set_current_folder(
                self.prefs['path of last browsed'])
        elif (not self.prefs['open defaults to last browsed'] and
            os.path.isdir(self.prefs['default open path'])):
            self.file_select.set_current_folder(
                self.prefs['default open path'])
        else:
            self.file_select.set_current_folder(os.environ["HOME"])
        if self.adding_to_library:
            self.lib_add_recursive_toggle.show()
        else:
            self.lib_add_recursive_toggle.hide()
            self.file_select.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.file_select.show()
        response = self.file_select.run()
        if int(response) == int(gtk.RESPONSE_OK):
            return self.file_chooser_ok(None)
        else:
            self.file_chooser_cancel(None)
    
    def file_chooser_ok(self, event, data=None):
        
        ''' Handles OK from the file chooser. '''
        
        if self.exit:
            return False
        
        self.file_select.hide()
        try:
            self.prefs['path of last browsed'] = \
                os.path.dirname(self.file_select.get_filename())
        except:
            pass
        if self.adding_to_library:
            return self.file_select.get_filenames()
        else:
            self.load_file(self.file_select.get_filename(), -2)
            self.refresh_image()
    
    def file_chooser_cancel(self, event, data=None):
        
        ''' Handles Cancel from the file chooser. '''
        
        if self.exit:
            return False
        
        try:
            self.prefs['path of last browsed'] = \
                os.path.dirname(self.file_select.get_filename())
        except:
            pass
        self.file_select.hide()
        return True
    
    def file_chooser_change_preview(self, event, data=None):
        
        ''' Changes the preview in the file chooser dialog when
        necessary. We try to load thumbnails when they exist,
        otherwise we create them. For archives we use the thumbs
        in arhive_thumbnails/ if they exist, otherwise we use a global
        one, if that does not exist either we ignore it. '''
        
        if self.exit:
            return False
        
        file = self.file_select.get_preview_filename()
        name_label = gtk.Label()
        size_label = gtk.Label()
        resolution_label = gtk.Label()
        type_label = gtk.Label()
        page_label = gtk.Label()
        preview_loaded = 0
        
        for widget in self.file_select_preview_box.get_children():
            self.file_select_preview_box.remove(widget)
        
        # =======================================================
        # Image file.
        # =======================================================
        if file != None and self.is_image_file(file):
            global_thumbs_path = \
                os.getenv('HOME', '') + '/.thumbnails/normal/'
            if not os.path.isdir(global_thumbs_path):
                os.makedirs(os.getenv('HOME', '') + '/.thumbnails/normal/')
                os.chmod(os.getenv('HOME', '') + '/.thumbnails/normal/', 0700)
            try:
                mtime = str(os.stat(file)[stat.ST_MTIME])
                uri = 'file://' + urllib.pathname2url(file)
                hash = md5.new()
                hash.update(uri)
                hash = hash.hexdigest() + '.png'
            except:
                hash = ''
            global_thumb_exists = 0
            
            # =======================================================
            # Thumbnail corresponding to the URI already exists.
            # =======================================================
            if os.path.isfile(global_thumbs_path + hash):
                try:
                    pixbuf = \
                        gtk.gdk.pixbuf_new_from_file(
                        global_thumbs_path + hash)
                    if mtime == pixbuf.get_option('tEXt::Thumb::MTime'):
                        global_thumb_exists = 1
                        name_label.set_text(self.to_unicode(
                            os.path.basename(file)))
                        if (pixbuf.get_option('tEXt::Thumb::Image::Width') !=
                            None and pixbuf.get_option(
                            'tEXt::Thumb::Image::Height') != None):
                            resolution_label.set_text(pixbuf.get_option(
                                'tEXt::Thumb::Image::Width') + 'x' +
                                pixbuf.get_option(
                                    'tEXt::Thumb::Image::Height'))
                        elif (pixbuf.get_option('tEXt::Thumb::Width') !=
                            None and pixbuf.get_option(
                            'tEXt::Thumb::Height') != None):
                            resolution_label.set_text(pixbuf.get_option(
                                'tEXt::Thumb::Width') + 'x' +
                                pixbuf.get_option('tEXt::Thumb::Height'))
                        if pixbuf.get_option('tEXt::Thumb::Size') != None:
                            size_label.set_text(str('%.1f' % (int(
                                pixbuf.get_option(
                                'tEXt::Thumb::Size')) / 1024.0)) + ' KiB')
                        else:
                            size_label.set_text(str('%.1f' % (
                                os.stat(file)[stat.ST_SIZE] / 1024.0)) +
                                ' KiB')
                        if pixbuf.get_option('tEXt::Thumb::Mimetype') != None:
                            type_label.set_text(pixbuf.get_option(
                                'tEXt::Thumb::Mimetype')[6:].upper())
                        else:
                            type_label.set_text(gtk.gdk.pixbuf_get_file_info(
                                file)[0]['mime_types'][0][6:].upper())
                except:
                    global_thumb_exists = 0
            
            # =======================================================
            # There exists no valid global thumbnail,
            # we check for local ones instead.
            # =======================================================
            if not global_thumb_exists:
                local_path = \
                    os.path.dirname(self.path) + '/.thumblocal/normal/'
                if os.path.isdir(local_path):
                    try:
                        uri_local = \
                            urllib.pathname2url(os.path.basename(file))
                        hash_local = md5.new()
                        hash_local.update(uri_local)
                        hash_local = hash_local.hexdigest() + '.png'
                        hash_local = ''
                        
                        # ====================================================
                        # Local thumbnail corresponding to the URI exists.
                        # ====================================================
                        if os.path.isfile(local_path + hash_local):
                            pixbuf = \
                                gtk.gdk.pixbuf_new_from_file(os.path.dirname(
                                    self.path) + '/.thumblocal/normal/' +
                                    hash_local)
                            if (mtime ==
                                pixbuf.get_option('tEXt::Thumb::MTime')):
                                global_thumb_exists = 1
                                name_label.set_text(self.to_unicode(
                                    os.path.basename(file)))
                                if (pixbuf.get_option(
                                    'tEXt::Thumb::Image::Width') != None and
                                    pixbuf.get_option(
                                    'tEXt::Thumb::Image::Height') != None):
                                    resolution_label.set_text(
                                        pixbuf.get_option(
                                        'tEXt::Thumb::Image::Width') + 'x' +
                                        pixbuf.get_option(
                                        'tEXt::Thumb::Image::Height'))
                                elif (pixbuf.get_option(
                                    'tEXt::Thumb::Width') != None and
                                    pixbuf.get_option(
                                    'tEXt::Thumb::Height') != None):
                                    resolution_label.set_text(
                                        pixbuf.get_option(
                                        'tEXt::Thumb::Width') + 'x' +
                                        pixbuf.get_option(
                                        'tEXt::Thumb::Height'))
                                if (pixbuf.get_option('tEXt::Thumb::Size') !=
                                    None):
                                    size_label.set_text(str('%.1f' % (int(
                                        pixbuf.get_option(
                                        'tEXt::Thumb::Size')) / 1024.0)) +
                                        ' KiB')
                                else:
                                    size_label.set_text(str('%.1f' % (os.stat(
                                        file)[stat.ST_SIZE] / 1024.0)) +
                                        ' KiB')
                                if (pixbuf.get_option(
                                    'tEXt::Thumb::Mimetype') != None):
                                    type_label.set_text(pixbuf.get_option(
                                        'tEXt::Thumb::Mimetype')[6:].upper())
                                else:
                                    type_label.set_text(
                                        gtk.gdk.pixbuf_get_file_info(file)[0]
                                        ['mime_types'][0][6:].upper())
                    except:
                        global_thumb_exists = 0
            
            # ====================================================
            # There exists no valid thumbnail. We create one,
            # either on the fly or by saving it to disk.
            # ====================================================
            try:
                if (not global_thumb_exists and 
                    self.prefs['use stored thumbnails']):
                    pixbuf, image_width, image_height = \
                        self.create_thumbnail(file, global_thumbs_path + hash,
                        128, {'tEXt::Thumb::URI':uri,
                        'tEXt::Thumb::MTime':mtime,
                        'tEXt::Thumb::Size':str(os.stat(file)[stat.ST_SIZE]),
                        'tEXt::Thumb::Mimetype':gtk.gdk.pixbuf_get_file_info(
                            file)[0]['mime_types'][0],
                        'tEXt::Software':'Comix ' + constants.version},
                        None, 128, True)
                    image_width = str(image_width)
                    image_height = str(image_height)
                    name_label.set_text(self.to_unicode(
                        os.path.basename(file)))
                    resolution_label.set_text(image_width + 'x' +
                        image_height)
                    size_label.set_text(str('%.1f' % (os.stat(file)
                        [stat.ST_SIZE] / 1024.0)) + ' KiB')
                    type_label.set_text(gtk.gdk.pixbuf_get_file_info(file)
                        [0]['mime_types'][0][6:].upper())
                    global_thumb_exists = 1
                elif (not global_thumb_exists and
                    not self.prefs['use stored thumbnails']):
                    pixbuf = \
                        gtk.gdk.pixbuf_new_from_file_at_size(file, 128, 128)
                    name_label.set_text(self.to_unicode(
                        os.path.basename(file)))
                    size_label.set_text(str('%.1f' % (os.stat(file)
                        [stat.ST_SIZE] / 1024.0)) + ' KiB')
                    type_label.set_text(gtk.gdk.pixbuf_get_file_info(file)
                        [0]['mime_types'][0][6:].upper())
                preview_loaded = 1
            except:
                preview_loaded = 0
        
        # ====================================================
        # Archive file.
        # ====================================================
        type = ''
        if file != None:
            type = self.archive_mime_type(file)
        if not preview_loaded and type != '':
            global_thumbs_path = \
                os.getenv('HOME', '') + '/.comix/archive_thumbnails/'
            if not os.path.isdir(global_thumbs_path):
                os.makedirs(global_thumbs_path)
                os.chmod(global_thumbs_path, 0700)
            try:
                mtime = str(os.stat(file)[stat.ST_MTIME])
                uri = 'file://' + urllib.pathname2url(file)
                hash = md5.new()
                hash.update(uri)
                hash = hash.hexdigest() + '1.png'
            except:
                hash = ''
            
            # ====================================================
            # Thumbnail corresponding to the URI exists in
            # ~/.comix/archive_thumbnails/.
            # ====================================================
            if os.path.isfile(global_thumbs_path + hash):
                try:
                    pixbuf = \
                        gtk.gdk.pixbuf_new_from_file(global_thumbs_path +
                        hash)
                    if mtime == pixbuf.get_option('tEXt::Thumb::MTime'):
                        name_label.set_text(self.to_unicode(
                            os.path.basename(file)))
                        size_label.set_text(str('%.1f' % (os.stat(file)
                            [stat.ST_SIZE] / 1048576.0)) + ' MiB')
                        if (pixbuf.get_option(
                            'tEXt::Thumb::Document::Pages') != None):
                            page_label.set_text(pixbuf.get_option(
                                'tEXt::Thumb::Document::Pages') + ' ' +
                                _('pages'))
                        if type == 'zip':
                            type_label.set_text(_("Zip archive"))
                        elif type == 'tar':
                            type_label.set_text(_("Tar archive"))
                        elif type == 'gzip':
                            type_label.set_text(
                                    _("Gzip compressed tar archive"))
                        elif type == 'bzip2':
                            type_label.set_text(
                                    _("Bzip2 compressed tar archive"))
                        else:
                            type_label.set_text(_("RAR archive"))
                        preview_loaded = 1
                except:
                    preview_loaded = 0
            
            # ====================================================
            # Thumbnail didn't exist, we look for it in
            # ~/.thumbnails/normal/ instead.
            # ====================================================
            if not preview_loaded:
                global_thumbs_path = \
                    os.getenv('HOME', '') + '/.thumbnails/normal/'
                if not os.path.isdir(global_thumbs_path):
                    os.makedirs(global_thumbs_path)
                    os.chmod(global_thumbs_path, 0700)
                try:
                    mtime = str(os.stat(file)[stat.ST_MTIME])
                    uri = 'file://' + urllib.pathname2url(file)
                    hash = md5.new()
                    hash.update(uri)
                    hash = hash.hexdigest() + '.png'
                except:
                    hash = ''
                global_thumb_exists = 0

                if os.path.isfile(global_thumbs_path + hash):
                    try:
                        pixbuf = \
                            gtk.gdk.pixbuf_new_from_file(global_thumbs_path +
                            hash)
                        if mtime == pixbuf.get_option('tEXt::Thumb::MTime'):
                            name_label.set_text(self.to_unicode(
                                os.path.basename(file)))
                            size_label.set_text(str('%.1f' % (os.stat(file)
                                [stat.ST_SIZE] / 1048576.0)) + ' MiB')
                            if (pixbuf.get_option(
                                'tEXt::Thumb::Document::Pages') != None):
                                page_label.set_text(pixbuf.get_option(
                                    'tEXt::Thumb::Document::Pages') + ' ' +
                                    _('pages'))
                            if type == 'zip':
                                type_label.set_text(_("Zip archive"))
                            elif type == 'tar':
                                type_label.set_text(_("Tar archive"))
                            elif type == 'gzip':
                                type_label.set_text(
                                        _("Gzip compressed tar archive"))
                            elif type == 'bzip2':
                                type_label.set_text(
                                        _("Bzip2 compressed tar archive"))
                            else:
                                type_label.set_text(_("RAR archive"))
                            preview_loaded = 1
                    except:
                        preview_loaded = 0
        
        # ====================================================
        # If we have loaded a pixbuf with the preview we
        # display it together with some info.
        # ====================================================
        if preview_loaded:
            assert(pixbuf.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
            dimensions = pixbuf.get_width(), pixbuf.get_height()
            stride = pixbuf.get_rowstride()
            pixels = pixbuf.get_pixels()
            mode = pixbuf.get_has_alpha() and "RGBA" or "RGB"
            pil_image = \
                Image.frombuffer(mode, dimensions, pixels, "raw", mode,
                stride, 1)
            pil_image = ImageOps.expand(pil_image, border = 1, fill=(0,0,0))
            imagestr = pil_image.tostring()
            IS_RGBA = pil_image.mode=='RGBA'
            pixbuf = \
                (gtk.gdk.pixbuf_new_from_data(imagestr,
                gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8, pil_image.size[0],
                pil_image.size[1], (IS_RGBA and 4 or 3) * pil_image.size[0]))
            pixmap = \
                gtk.gdk.Pixmap(self.window.window, pixbuf.get_width(),
                pixbuf.get_height(), -1)
            pixmap.draw_rectangle(self.gdk_gc, True, 0, 0, pixbuf.get_width(),
                pixbuf.get_height())
            pixmap.draw_pixbuf(None, pixbuf, 0, 0, 0, 0, -1, -1,
                gtk.gdk.RGB_DITHER_MAX, 0, 0)
            pixbuf.get_from_drawable(pixmap, gtk.gdk.colormap_get_system(),
                0, 0, 0, 0, -1, -1)
            image = gtk.Image()
            image.set_from_pixbuf(pixbuf)
            image.set_size_request(130, 130)
            image.show()
            self.file_select_preview_box.pack_start(image, False, False, 2)
            name_label.show()
            attrlist = pango.AttrList()
            attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                len(name_label.get_text())))
            attrlist.insert(pango.AttrSize(8000, 0,
                len(name_label.get_text())))
            name_label.set_attributes(attrlist)
            self.file_select_preview_box.pack_start(name_label, False, False,
                2)
            
            if resolution_label.get_text() != '':
                resolution_label.show()
                attrlist = pango.AttrList()
                attrlist.insert(pango.AttrSize(8000, 0,
                    len(resolution_label.get_text())))
                resolution_label.set_attributes(attrlist)
                self.file_select_preview_box.pack_start(resolution_label,
                    False, False, 2)
            if size_label.get_text() != '':
                size_label.show()
                attrlist = pango.AttrList()
                attrlist.insert(pango.AttrSize(8000, 0,
                    len(size_label.get_text())))
                size_label.set_attributes(attrlist)
                self.file_select_preview_box.pack_start(size_label,
                    False, False, 2)
            if page_label.get_text() != '':
                page_label.show()
                attrlist = pango.AttrList()
                attrlist.insert(pango.AttrSize(8000, 0,
                    len(page_label.get_text())))
                page_label.set_attributes(attrlist)
                self.file_select_preview_box.pack_start(page_label,
                    False, False, 2)
            if type_label.get_text() != '':
                type_label.show()
                attrlist = pango.AttrList()
                attrlist.insert(pango.AttrSize(8000, 0,
                    len(type_label.get_text())))
                type_label.set_attributes(attrlist)
                self.file_select_preview_box.pack_start(type_label,
                    False, False, 2)
        
        gc.collect()
    
    def extract_image_open(self, *args):
        
        ''' Opens the extract image dialog. '''
        
        if self.exit:
            return False
        
        self.extract_dialog.set_title(_('Extract page') + ' ' + str(
            self.file_number + 1))
        ext = os.path.splitext(self.file[self.file_number])[1]
        if self.archive_type == '':
            filename = \
                os.path.basename(os.path.dirname(
                self.file[self.file_number]))
        else:
            filename = os.path.splitext(os.path.basename(self.path))[0]
        filename += \
            ('_' + str(self.file_number + 1).zfill(len(str(len(
            self.file)))) + ext)
        filename = self.to_unicode(filename)
        self.extract_dialog.set_current_name(filename)
        self.extract_dialog.show()
        response = self.extract_dialog.run()
        if int(response) == int(gtk.RESPONSE_OK):
            self.extract_image_ok(self.extract_dialog.get_filename())
        else:
            self.extract_image_cancel(None)
    
    def extract_image_ok(self, path):
        
        ''' Closes the extract image dialog and extracts the current
        image to path. '''
        
        if self.exit:
            return False
        
        self.extract_dialog.hide()
        # FIXME: Should pop up a warning dialog instead of print to terminal.
        try:
            shutil.copy(self.file[self.file_number], path)
        except:
            print '*** Could not save ' + self.to_unicode(path)
    
    def extract_image_cancel(self, *args):
        
        ''' Closes the extract image dialog. '''
        
        if self.exit:
            return False
        
        self.extract_dialog.hide()
    
    def colour_adjust_open(self, *args):
        
        ''' Opens the colour adjust dialog. '''

        if self.exit:
            return False
        
        self.colour_adjust_signal_kill = True
        self.contrast_scale.set_value(self.prefs['contrast'])
        self.saturation_scale.set_value(self.prefs['saturation'])
        self.brightness_scale.set_value(self.prefs['brightness'])
        self.sharpness_scale.set_value(self.prefs['sharpness'])
        self.button_save_satcon.set_active(
            self.prefs['save saturation and contrast'])
        self.button_autocontrast.set_active(self.prefs['autocontrast'])
        self.colour_adjust_signal_kill = False
        self.colour_adjust_dialog_displayed = True
        if self.file_exists:
            # To get histogram. FIXME: Too costly.
            self.refresh_image()
        self.colour_adjust_dialog.show()

    def colour_adjust_close(self, *args):

        ''' Hides the colour adjust dialog. '''

        if self.exit:
            return False

        self.colour_adjust_dialog.hide()
        self.colour_adjust_dialog_displayed = False
        return True

    def colour_adjust_response(self, dialog, response):
        
        ''' Handles button presses (i.e. OK or Default) '''
        
        if self.exit:
            return False
        
        if response in [int(gtk.RESPONSE_OK), int(gtk.RESPONSE_DELETE_EVENT)]:
            self.colour_adjust_close()
        else:
            self.colour_adjust_signal_kill = True
            self.contrast_scale.set_value(1.0)
            self.saturation_scale.set_value(1.0)
            self.brightness_scale.set_value(1.0)
            self.sharpness_scale.set_value(1.0)
            self.button_save_satcon.set_active(False)
            self.button_autocontrast.set_active(False)
            self.colour_adjust_signal_kill = False
            self.refresh_image()

    def colour_adjust_change_value(self, scale, operation):
        
        if operation == 'save':
            self.prefs['save saturation and contrast'] = \
                self.button_save_satcon.get_active()
        elif operation == 'autocontrast':
            self.prefs['autocontrast'] = \
                self.button_autocontrast.get_active()
            self.contrast_scale.set_sensitive(not self.prefs['autocontrast'])
        else:
            self.prefs[operation] = scale.get_value()
        if not self.colour_adjust_signal_kill and not operation == 'save':
            self.refresh_image()

    def colour_adjust_draw_histogram(self, pixbuf):
        
        dimensions = pixbuf.get_width(), pixbuf.get_height()
        stride = pixbuf.get_rowstride()
        pixels = pixbuf.get_pixels()
        mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
        pil_image = \
            Image.frombuffer(mode, dimensions, pixels, 'raw', mode, stride, 1)
        hist_data = pil_image.histogram()
        hist_rgb_im = Image.new('RGB', (256, 150), (50, 50, 50))
        maximum = \
            max(hist_data[:768] + [1])
        y_scale = float(150) / maximum
        for x in xrange(256):
            r = int(hist_data[x] * y_scale)
            g = int(hist_data[x + 256] * y_scale)
            b = int(hist_data[x + 512] * y_scale)
            for y, val in enumerate(reversed(xrange(150))):
                hist_rgb_im.putpixel((x, y), (255 * (r > val),
                    255 * (g > val), 255 * (b > val)))
        maxstr = 'max: ' + str(maximum)
        hist_rgb_im = ImageOps.expand(hist_rgb_im, 2, (50, 50, 50))
        hist_rgb_im = ImageOps.expand(hist_rgb_im, 1, (0, 0, 0))
        imagestr = hist_rgb_im.tostring()
        IS_RGBA = hist_rgb_im.mode == 'RGBA'
        hist_rgb_pixbuf = \
            gtk.gdk.pixbuf_new_from_data(imagestr,
            gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8,
            hist_rgb_im.size[0], hist_rgb_im.size[1],
            (IS_RGBA and 4 or 3) * hist_rgb_im.size[0])
        self.colour_adjust_histogram.set_from_pixbuf(hist_rgb_pixbuf)
    
    def open_bookmark(self, event):
        
        ''' Opens a bookmark. '''
        
        if self.exit:
            return False
        
        if (self.path != self.bookmarks[int(event.get_name()[4:]) - 1] or
            self.file_number != self.bookmark_numbers[int(
            event.get_name()[4:]) - 1] - 1):
            self.load_file(self.bookmarks[int(event.get_name()[4:]) - 1],
                self.bookmark_numbers[int(event.get_name()[4:]) - 1] - 1)
            self.refresh_image()
    
    def remove_bookmark(self, bookmark):
        
        ''' Removes a bookmark. '''
        
        path = self.bookmarks[bookmark]
        self.bookmarks.pop(bookmark)
        self.bookmark_numbers.pop(bookmark)
        thumb_dir = os.path.join(os.getenv('HOME'), '.comix/menu_thumbnails')
        
        if not self.recent_files.count(path):
            try:
                uri = 'file://' + urllib.pathname2url(path)
                hash = md5.new()
                hash.update(uri)
                hash = hash.hexdigest() + '.png'
                os.remove(os.path.join(thumb_dir, hash))
            except:
                pass
        self.create_menus()
    
    def clear_bookmarks(self, event):
        
        ''' Clears bookmarks. '''
        
        if self.exit:
            return False
        
        thumb_dir = os.path.join(os.getenv('HOME'), '.comix/menu_thumbnails')
        
        for file in self.bookmarks:
            if not self.recent_files.count(file):
                try:
                    uri = 'file://' + urllib.pathname2url(file)
                    hash = md5.new()
                    hash.update(uri)
                    hash = hash.hexdigest() + '.png'
                    os.remove(os.path.join(thumb_dir, hash))
                except:
                    pass
        while self.bookmarks:
            self.bookmarks.pop()
        for i in range(len(self.bookmark_numbers)):
            self.bookmark_numbers.pop()
        self.create_menus()
    
    def add_menu_thumb(self, event, path=None, type='bookmark'):
        
        ''' Saves a recent file. '''
        
        if self.exit:
            return False
        
        if path == None:
            if self.archive_type != '':
                path = self.path
            else:
                path = self.file[self.file_number]
        
        thumb_dir = os.getenv('HOME', '') + '/.comix/menu_thumbnails/'
        if not os.path.isdir(thumb_dir):
            os.makedirs(thumb_dir)
            os.chmod(thumb_dir, 0700)
        
        if type == 'bookmark':
            if self.bookmarks.count(path) > 0:
                del self.bookmark_numbers[self.bookmarks.index(path)]
                self.bookmarks.remove(path)
            self.bookmarks.insert(0, path)
            self.bookmark_numbers.insert(0, self.file_number + 1)
        elif type == 'recent':
            if not self.prefs['store recent file info']:
                return
            try:
                recently_used_file = \
                    open(os.path.join(os.environ['HOME'], '.recently-used'))
                recently_used_data = recently_used_file.readlines()
                recently_used_file.close()
            except:
                recently_used_data = \
                    ['<?xml version="1.0"?>\n', '<RecentFiles>\n',
                    '</RecentFiles>\n']
            if recently_used_data.count('    <URI>file://' +
                urllib.pathname2url(path) + '</URI>\n'):
                position = \
                    recently_used_data.index('    <URI>file://' +
                    urllib.pathname2url(path) + '</URI>\n') + 2
                recently_used_data.pop(position)
                recently_used_data.insert(position, '    <Timestamp>' +
                    str(int(time.time())) + '</Timestamp>\n')
            else:
                recently_used_data.insert(2, '  </RecentItem>\n')
                recently_used_data.insert(2, '    </Groups>\n')
                recently_used_data.insert(2, '      <Group>comix</Group>\n')
                recently_used_data.insert(2, '    <Groups>\n')
                recently_used_data.insert(2, '    <Timestamp>' +
                    str(int(time.time())) + '</Timestamp>\n')
                mime_type = '    <Mime-Type>'
                if self.archive_type == _('Zip archive'):
                    mime_type += 'application/x-cbz'
                elif self.archive_type == _('RAR archive'):
                    mime_type += 'application/x-cbr'
                elif self.archive_type in [_('Tar archive'),
                    _('Gzip compressed tar archive'),
                    _('Bzip2 compressed tar archive')]:
                    mime_type += 'application/x-cbt'
                else:
                    mime_type += gtk.gdk.pixbuf_get_file_info(
                        path)[0]['mime_types'][0]
                mime_type += '</Mime-Type>'
                recently_used_data.insert(2, mime_type + '\n')
                recently_used_data.insert(2, '    <URI>file://' +
                    urllib.pathname2url(path) + '</URI>\n')
                recently_used_data.insert(2, '  <RecentItem>\n')
            recently_used_file = \
                open(os.path.join(os.environ['HOME'],
                '.recently-used-comix-temp'), 'w')
            counter = 0
            for l in recently_used_data:
                recently_used_file.write(l)
                if l.startswith('  </RecentItem>'):
                    counter += 1
                if counter >= 500:
                    recently_used_file.write('</RecentFiles>\n')
                    break
            recently_used_file.close()
            os.rename(os.path.join(os.environ['HOME'],
                '.recently-used-comix-temp'),
                os.path.join(os.environ['HOME'],
                '.recently-used'))
            os.chmod(os.path.join(os.environ['HOME'],
                '.recently-used'), 0600)
            
            if self.recent_files.count(path) > 0:
                self.recent_files.remove(path)
            self.recent_files.insert(0, path)
            if len(self.recent_files) > 10:
                if not self.bookmarks.count(self.recent_files[10]):
                    try:
                        uri = \
                            'file://' + urllib.pathname2url(
                            self.recent_files[10])
                        hash = md5.new()
                        hash.update(uri)
                        hash = hash.hexdigest() + '.png'
                        os.remove(thumb_dir + hash)
                    except:
                        pass
                self.recent_files.pop()
        else:
            print '*** This is programming error #1'
            return
            
        uri = 'file://' + urllib.pathname2url(path)
        hash = md5.new()
        hash.update(uri)
        hash = hash.hexdigest() + '.png'
        
        if not os.path.isfile(thumb_dir + hash):
            try:
                if self.archive_type != '':
                    image_file = self.file[0]
                else:
                    image_file = path
                # =======================================================
                # pixbuf_new_from_file_at_size() is faster than
                # pixbuf_new_from_file() + scale_simple(), but for some
                # reason it is very slow when scaling to a small
                # resolution (in this case 14x14 px). As a workaround we 
                # use pixbuf_new_from_file_at_size() to 50x50 px 
                # (which is fast) and then scale it to 14x14 with 
                # scale_simple() (which is also fast with small 
                # resolutions.)
                #
                # See http://bugzilla.gnome.org/show_bug.cgi?id=80925
                # for more information.
                # =======================================================
                pixbuf = \
                    gtk.gdk.pixbuf_new_from_file_at_size(image_file, 50, 50)
                if pixbuf.get_width() > pixbuf.get_height():
                    width = 14
                    height = 14 * pixbuf.get_height() / pixbuf.get_width()
                else:
                    width = 14 * pixbuf.get_width() / pixbuf.get_height()
                    height = 14
                pixbuf = \
                    pixbuf.scale_simple(width, height,
                    gtk.gdk.INTERP_BILINEAR)
                assert(pixbuf.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
                dimensions = pixbuf.get_width(), pixbuf.get_height()
                stride = pixbuf.get_rowstride()
                pixels = pixbuf.get_pixels()
                mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
                pil_image_top = \
                    Image.frombuffer(mode, dimensions, pixels, "raw", mode,
                    stride, 1)
                pil_image_top = \
                    ImageOps.expand(pil_image_top, border = 1, fill=(0, 0, 0))
                pil_image = Image.new('RGBA', (16, 16))
                pil_image.paste(pil_image_top,
                    ((16 - pil_image_top.size[0]) / 2,
                    (16 - pil_image_top.size[1]) / 2))
                if os.path.isdir(thumb_dir):
                    pil_image.save(thumb_dir + hash, 'PNG')
                    os.chmod(thumb_dir + hash, 0600)
            except:
                print '*** Error while saving menu thumbnail in ' + \
                self.to_unicode(thumb_dir) + \
                '. This is probably nothing to worry about.'
        self.create_menus()
    
    def open_recent_file(self, event):
        
        ''' Opens a recently viewed file. '''
        
        if self.exit:
            return False
        
        self.load_file(self.recent_files[int(event.get_name()[6:]) - 1], -2)
        self.refresh_image()
    
    def clear_recent_files(self, data=None):
        
        ''' Clears recent files. '''
        
        if self.exit:
            return False
        
        thumb_dir = os.path.join(os.getenv('HOME'), '.comix/menu_thumbnails')
        
        for file in self.recent_files:
            if not self.bookmarks.count(file):
                try:
                    uri = 'file://' + urllib.pathname2url(file)
                    hash = md5.new()
                    hash.update(uri)
                    hash = hash.hexdigest() + '.png'
                    os.remove(os.path.join(thumb_dir, hash))
                except:
                    pass
        for i in range(len(self.recent_files)):
            self.recent_files.pop()
        self.create_menus()
    
    def create_menus(self):
        
        ''' Creates the menus for the menubar and the right-click menu.
        This method is recalled every time a bookmark has been
        added/removed. '''
        
        if self.exit:
            return False
        
        # =======================================================
        # Adds bookmarks to the menus and to the bookmark
        # manager with possible thumbnails if found.
        # =======================================================
        thumb_dir = os.getenv('HOME', '') + '/.comix/menu_thumbnails/'
        self.liststore.clear()
        for i, bookmark in enumerate(self.bookmarks):
            uri = 'file://' + urllib.pathname2url(bookmark)
            hash = md5.new()
            hash.update(uri)
            hash = hash.hexdigest() + '.png'
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(thumb_dir + hash)
            except:
                pixbuf = \
                    self.bookmark_dialog.render_icon(gtk.STOCK_FILE,
                    gtk.ICON_SIZE_MENU)
            page = ', ' + _('page') + ' ' + str(self.bookmark_numbers[i])
            if self.is_image_file(bookmark):
                title = \
                    self.to_unicode(os.path.basename(os.path.dirname(
                    bookmark)))
            else:
                title = \
                    self.to_unicode(os.path.basename(bookmark))
            if len(title) > 25:
                title = title[:11] + '...' + title[-11:]
            
            # =======================================================
            # Create bookmark for the bookmarks manager.
            # =======================================================
            self.liststore.append([title, str(self.bookmark_numbers[i]),
                pixbuf])
            
            # We don't want underlines in the menus.
            title = title.replace('_', '__')
            
            # =======================================================
            # Create bookmark for the menus.
            # =======================================================
            factory = gtk.IconFactory()
            iconset = gtk.IconSet(pixbuf)
            factory.add(bookmark, iconset)
            factory.add_default()
            self.actiongroup.add_actions([('Book' + str(i + 1), bookmark,
                title + page, '', None, self.open_bookmark)])
        
        # =======================================================
        # Adds recent files to the menus with possible thumbnails
        # if found.
        # =======================================================
        for i, file in enumerate(self.recent_files):
            uri = 'file://' + urllib.pathname2url(file)
            hash = md5.new()
            hash.update(uri)
            hash = hash.hexdigest() + '.png'
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(thumb_dir + hash)
            except:
                pixbuf = \
                    self.bookmark_dialog.render_icon(gtk.STOCK_FILE,
                    gtk.ICON_SIZE_MENU)
            title = self.to_unicode(os.path.basename(file))
            if len(title) > 25:
                title = title[:11] + '...' + title[-11:]
            
            # We don't want underlines in the menus.
            title = title.replace('_', '__')
            
            # =======================================================
            # Create recent file for the menus.
            # =======================================================
            factory = gtk.IconFactory()
            iconset = gtk.IconSet(pixbuf)
            factory.add(file, iconset)
            factory.add_default()
            self.actiongroup.add_actions([('recent' + str(i + 1), file,
                title, None, None, self.open_recent_file)])
        
        # =======================================================
        # Create or recreate the menus.
        # =======================================================
        try:
            self.ui.get_widget('/Menu').hide()
        except:
            pass
        try:
            self.ui.remove_ui(self.merge_id)
        except:
            pass
        gc.collect()
        
        self.ui = gtk.UIManager()
        ui_description = """<ui>
            <popup name="Pop">
                <menu action="menu_go_popup">
                    <menuitem action="First" />
                    <menuitem action="Previous" />
                    <menuitem action="Next" />
                    <menuitem action="Last" />
                    <separator />
                    <menuitem action="Go" />
                </menu>
                <separator />
                <menu action="menu_view_popup">
                    <menuitem action="Fullscreen" />
                    <menuitem action="Double" />
                    <menuitem action="manga_mode" />
                    <separator />
                    <menuitem action="fit_screen_mode" />
                    <menuitem action="fit_width_mode" />
                    <menuitem action="fit_height_mode" />
                    <menuitem action="fit_manual_mode" />
                    <separator />
                    <menuitem action="Slideshow" />
                    <separator />
                    <menuitem action="colour_adjust" />
                    <separator />
                    <menuitem action="Lens" />
                    <separator />
                    <menu action="menu_toolbars">
                        <menuitem action="Menubar" />
                        <menuitem action="Toolbar" />
                        <menuitem action="Statusbar" />
                        <menuitem action="Scrollbars" />
                        <menuitem action="Thumbnails" />
                        <separator />
                        <menuitem action="Hide_all" />
                    </menu>
                </menu>
                <menu action="Transform">
                    <menuitem action="Rotate_90" />
                    <menuitem action="Rotate_270" />
                    <menuitem action="Rotate_180" />
                    <menuitem action="Flip_horiz" />
                    <menuitem action="Flip_vert" />
                    <separator />
                    <menuitem action="Keep_rotation" />
                </menu>
                <menu action="Zoom">
                    <menuitem action="Zin" />
                    <menuitem action="Zout" />
                    <menuitem action="Zoriginal" />
                    <menuitem action="Zwidth" />
                    <menuitem action="Zheight" />
                    <menuitem action="Zfit" />
                </menu>
                <menu action="menu_bookmarks_popup">
                    <menuitem action="Save_book" />
                    <menuitem action="Bookmark_manager" />
                    <separator />"""
        for i, bookmark in enumerate(self.bookmarks):
            ui_description = \
                ui_description + '\n<menuitem action="Book' + str(i+1) + \
                '" />'
        ui_description = ui_description + """
                    <separator />
                    <menuitem action="Clear_book" />
                </menu>
                <separator />
                <menuitem action="File" />
                <menuitem action="Comments" />
                <menuitem action="Options" />
                <menuitem action="Thumbnail_dialog" />
                <separator />
                <menuitem action="Add_to_library" />
                <menuitem action="Convert" />
                <menuitem action="Extract" />
                <menu action="menu_file_operations">
                    <menuitem action="file_rot_90" />
                    <menuitem action="file_rot_270" />
                    <menuitem action="file_flip_horiz" />
                    <menuitem action="file_flip_vert" />
                    <menuitem action="file_desaturate" />
                    <separator />
                    <menuitem action="Delete" />
                </menu>
                <separator />
                <menu action="Recent">"""
        for i, bookmark in enumerate(self.recent_files):
            ui_description = \
                ui_description + '\n<menuitem action="recent' + str(i + 1) + \
                '" />'
        ui_description = ui_description + """
                    <separator />
                    <menuitem action="Clear_recent" />
                </menu>
                <separator />
                <menuitem action="Open" />
                <menuitem action="Library" />
                <separator />
                <menuitem action="About" />
                <separator />
                <menuitem action="Close" />
                <menuitem action="Quit" />
            </popup>
            <menubar name="Menu">
                <menu action="menu_file">
                    <menuitem action="Open" />
                    <menuitem action="Library" />
                    <separator />
                    <menuitem action="Add_to_library" />
                    <menuitem action="Convert" />
                    <menuitem action="Extract" />
                    <menu action="menu_file_operations">
                        <menuitem action="file_rot_90" />
                        <menuitem action="file_rot_270" />
                        <menuitem action="file_flip_horiz" />
                        <menuitem action="file_flip_vert" />
                        <menuitem action="file_desaturate" />
                        <separator />
                        <menuitem action="Delete" />
                    </menu>

                    <separator />
                    <menu action="Recent">
                    """
        for i, bookmark in enumerate(self.recent_files):
            ui_description = \
                ui_description + '\n<menuitem action="recent' + str(i + 1) + \
                '" />'
        ui_description = ui_description + """
                        <separator />
                        <menuitem action="Clear_recent" />
                    </menu>
                    <separator />
                    <menuitem action="File" />
                    <menuitem action="Comments" />
                    <separator />
                    <menuitem action="Close" />
                    <menuitem action="Quit" />
                </menu>
                <menu action="menu_edit">
                    <menuitem action="Thumbnail_dialog" />
                    <menuitem action="Options" />
                </menu>
                <menu action="menu_view">
                    <menuitem action="Fullscreen" />
                    <menuitem action="Double" />
                    <menuitem action="manga_mode" />
                    <separator />
                    <menuitem action="fit_screen_mode" />
                    <menuitem action="fit_width_mode" />
                    <menuitem action="fit_height_mode" />
                    <menuitem action="fit_manual_mode" />
                    <separator />
                    <menuitem action="Slideshow" />
                    <separator />
                    <menuitem action="colour_adjust" />
                    <separator />
                    <menuitem action="Lens" />
                    <separator />
                    <menu action="Transform">
                        <menuitem action="Rotate_90" />
                        <menuitem action="Rotate_270" />
                        <menuitem action="Rotate_180" />
                        <menuitem action="Flip_horiz" />
                        <menuitem action="Flip_vert" />
                        <separator />
                        <menuitem action="Keep_rotation" />
                    </menu>
                    <menu action="Zoom">
                        <menuitem action="Zin" />
                        <menuitem action="Zout" />
                        <menuitem action="Zoriginal" />
                        <menuitem action="Zwidth" />
                        <menuitem action="Zheight" />
                        <menuitem action="Zfit" />
                    </menu>
                    <separator />
                    <menu action="menu_toolbars">
                        <menuitem action="Menubar" />
                        <menuitem action="Toolbar" />
                        <menuitem action="Statusbar" />
                        <menuitem action="Scrollbars" />
                        <menuitem action="Thumbnails" />
                        <separator />
                        <menuitem action="Hide_all" />
                    </menu>
                </menu>
                <menu action="menu_go">
                    <menuitem action="First" />
                    <menuitem action="Previous" />
                    <menuitem action="Next" />
                    <menuitem action="Last" />
                    <separator />
                    <menuitem action="Go" />
                </menu>
                <menu action="menu_bookmarks">
                    <menuitem action="Save_book" />
                    <menuitem action="Bookmark_manager" />
                    <separator />"""
        for i,bookmark in enumerate(self.bookmarks):
            ui_description = \
                ui_description + '\n<menuitem action="Book' + str(i+1) + \
                '" />'
        ui_description = ui_description + """
                    <separator />
                    <menuitem action="Clear_book" />
                </menu>
                <menu action="menu_help">
                    <menuitem action="About" />
                </menu>
            </menubar>
        </ui>"""
        
        self.merge_id = self.ui.add_ui_from_string(ui_description)
        self.ui.insert_action_group(self.actiongroup, 0)
        self.ui.insert_action_group(self.recent_actiongroup, 1)
        
        self.table.attach(self.ui.get_widget('/Menu'), 0, 4, 0, 1,
            gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK, 0, 0)
        
        if not self.bookmarks:
            self.actiongroup.get_action('Clear_book').set_sensitive(False)
            self.bookmark_dialog.action_area.get_children()[1].set_sensitive(
                False)
        else:
            self.actiongroup.get_action('Clear_book').set_sensitive(True)
            self.bookmark_dialog.action_area.get_children()[1].set_sensitive(
                True)
        if not self.recent_files:
            self.actiongroup.get_action('Clear_recent').set_sensitive(False)
        else:
            self.actiongroup.get_action('Clear_recent').set_sensitive(True)
        if (self.prefs['hide in fullscreen'] and
            self.prefs['fullscreen'] or not self.prefs['show menubar']):
            self.ui.get_widget('/Menu').hide()
        else:
            self.ui.get_widget('/Menu').show()
    
    def close_file(self, data=None):
        
        ''' Closes the currently loaded file. '''
        
        if self.exit:
            return False
        
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            os.makedirs(self.base_dir)
        for i in range(len(self.file)):
            self.file.pop()
        self.set_file_exists(False)
        self.refresh_image()
    
    def archive_mime_type(self, path):
        
        ''' Returns the archive type of path or the empty string for
        non-archives. '''
        
        if self.exit:
            return False
        
        try:
            if os.path.isfile(path):
                if zipfile.is_zipfile(path):
                    return 'zip'
                fd = open(path, 'rb')
                magic = fd.read(4)
                fd.close()
                if tarfile.is_tarfile(path) and os.path.getsize(path) > 0:
                    if magic[:3] == 'BZh':
                        return 'bzip2'
                    if magic[:2] == '\037\213':
                        return 'gzip'
                    return 'tar'
                if magic == 'Rar!':
                    return 'rar'
        except:
            pass
        return ''
    
    def drag_motion(self, wid, context, x, y, time):
        
        ''' Required for drag and drop. '''
        
        if self.exit:
            return False
        
        context.drag_status(gtk.gdk.ACTION_COPY, time)
        return True
    
    def drag_n_drop(self, widget, drag_context, x, y, selection, info, time):
        
        ''' Handles drag and drop  to the main window. '''
        
        if self.exit:
            return False
        
        # We don't want to open files from our selves.
        if selection.data.startswith('file:///tmp/comix/'):
            return
        
        uri = selection.data.strip()
        path = urllib.url2pathname(uri)
        paths = path.rsplit('\n')
        for i, path in enumerate(paths):
            paths[i] = path.rstrip('\r')
        path = paths[0] # Only open one file.
        if path.startswith('file://'): # Nautilus etc.
            path = path[7:]
        elif path.startswith('file:'): # Xffm etc.
            path = path[5:]
        self.load_file(path, -2)
        self.refresh_image()
    
    def lib_drag_n_drop(self, widget, drag_context, x, y, selection, info,
        time):
        
        ''' Handles drag and drop to the library window. '''
        
        if self.exit:
            return False
        
        uri = selection.data.strip()
        path = urllib.url2pathname(uri)
        paths = path.rsplit('\n')
        for i, path in enumerate(paths):
            if path.startswith('file://'): # Nautilus etc.
                path = path[7:]
            elif path.startswith('file:'): # Xffm etc.
                path = path[5:]
            paths[i] = path.rstrip('\r')
        self.library_add(None, paths)
    
    def load_thumbnails(self):
        
        ''' Load thumbnails for the thumbnail side bar. Comix can read
        and write thumbnails from the ~/.thumbnails directory 
        (or .thumblocal) as proposed by the freedesktop.org standard
        (http://jens.triq.net/thumbnail-spec). '''

        # FIXME: Rewrite this, it has some ridiculous indentations.
        
        if self.exit:
            return False
        
        self.update_sizes()
        self.thumb_loop_stop = 0
        
        if (not self.prefs['show thumbnails'] or
            self.number_of_thumbs_loaded == len(self.file)):
            self.thumb_loop_stop = 1
            return
        
        for i, file in enumerate(self.file):
            if (self.exit or not self.prefs['show thumbnails'] or
                self.thumb_loop_stop):
                return False
            elif i + 1 > self.number_of_thumbs_loaded:
                try:
                    # =======================================================
                    # Use standard thumbnail handling as proposed by
                    # freedesktop.org.
                    # =======================================================
                    if (not self.archive_type and 
                        self.prefs['use stored thumbnails']):
                        thumbs_path = \
                            os.getenv('HOME', '') + '/.thumbnails/normal/'
                        try:
                            # The modification time of the original file.
                            mtime = str(os.stat(file)[stat.ST_MTIME])
                            # URI of the original file.
                            uri = 'file://' + urllib.pathname2url(file)
                            # md5 hash of the URI to be used as the filename.
                            hash = md5.new()
                            hash.update(uri)
                            hash = hash.hexdigest() + '.png'
                        except:
                            hash = ''
                        thumb_exists = 0
                        
                        # Thumbnail corresponding to the URI already exists.
                        if os.path.exists(thumbs_path + hash):
                            try:
                                pixbuf = \
                                    gtk.gdk.pixbuf_new_from_file(thumbs_path +
                                    hash)
                                
                                # If the modification time for the file is the
                                # same as the one stored in the thumbnail.
                                if (mtime ==
                                    pixbuf.get_option('tEXt::Thumb::MTime')):
                                    thumb_exists = 1
                                    
                                    # We scale it down to our prefered size.
                                    if (pixbuf.get_width() > 
                                        pixbuf.get_height()):
                                        width = self.prefs['thumbnail size']
                                        height = \
                                            pixbuf.get_height() * \
                                            self.prefs['thumbnail size'] / \
                                            pixbuf.get_width()
                                    else:
                                        width = \
                                            pixbuf.get_width() * \
                                            self.prefs['thumbnail size'] / \
                                            pixbuf.get_height()
                                        height = self.prefs['thumbnail size']
                                    if width < 1:
                                        width = 1
                                    if height < 1:
                                        height = 1
                                    pixbuf = \
                                        pixbuf.scale_simple(width, height,
                                        gtk.gdk.INTERP_TILES)
                            except:
                                thumb_exists = 0
                        
                        # ====================================================
                        # There exists no valid global thumbnail, we check for
                        # local ones instead.
                        # ====================================================
                        if not thumb_exists:
                            local_thumbs_path = \
                                os.path.dirname(self.path) + \
                                '/.thumblocal/normal/'
                            if os.path.isdir(local_thumbs_path):
                                try:
                                    # URI of the original file (only basename)
                                    local_uri = \
                                        urllib.pathname2url(
                                        os.path.basename(file))
                                    local_hash = md5.new()
                                    local_hashupdate(local_uri)
                                    local_hash = \
                                        hash_local.hexdigest() + '.png'
                                except:
                                    local_hash = ''
                                if (os.path.exists(local_thumbs_path +
                                    local_hash)):
                                    try:
                                        pixbuf = \
                                            gtk.gdk.pixbuf_new_from_file(
                                            local_thumbs_path + local_hash)
                                        if (mtime ==
                                            pixbuf.get_option(
                                            'tEXt::Thumb::MTime')):
                                            thumb_exists = 1
                                            
                                            if (pixbuf.get_width() >
                                                pixbuf.get_height()):
                                                width = \
                                                    self.prefs[
                                                    'thumbnail size']
                                                height = \
                                                    pixbuf.get_height() * \
                                                    self.prefs[
                                                    'thumbnail size'] / \
                                                    pixbuf.get_width()
                                            else:
                                                width = \
                                                    pixbuf.get_width() * \
                                                    self.prefs[
                                                    'thumbnail size'] / \
                                                    pixbuf.get_height()
                                                height = \
                                                    self.prefs[
                                                    'thumbnail size']
                                            if width < 1:
                                                width = 1
                                            if height < 1:
                                                height = 1
                                            pixbuf = \
                                                pixbuf.scale_simple(width,
                                                height, gtk.gdk.INTERP_TILES)
                                    except:
                                        thumb_exists = 0
                        
                        # ====================================================
                        # There exists no valid thumbnail. We create one.
                        # ====================================================
                        if not thumb_exists:
                            pixbuf = \
                                self.create_thumbnail(file, thumbs_path +
                                hash, 128, {'tEXt::Thumb::URI':uri,
                                'tEXt::Thumb::MTime':mtime,
                                'tEXt::Thumb::Size':
                                str(os.stat(file)[stat.ST_SIZE]),
                                'tEXt::Thumb::Mimetype':
                                gtk.gdk.pixbuf_get_file_info(file)
                                [0]['mime_types'][0],
                                'tEXt::Software':'Comix ' + constants.version}
                                , pixbuf_size = self.prefs['thumbnail size'])
                    
                    # =======================================================
                    # For archives we have to use a Comix-specific folder and
                    # change the handling a bit due to restrictions in the
                    # freedesktop.org standard (only one thumbnail per file.)
                    # =======================================================
                    elif (self.archive_type and 
                        self.prefs['use stored archive thumbnails']):
                        
                        # ====================================================
                        # Load the thumbnail if it exists.
                        # ====================================================
                        thumbs_path = \
                            os.getenv('HOME', '') + \
                            '/.comix/archive_thumbnails/'
                        if not os.path.isdir(thumbs_path):
                            os.makedirs(thumbs_path)
                            os.chmod(thumbs_path, 0700)
                        try:
                            mtime = str(os.stat(self.path)[stat.ST_MTIME])
                            uri = 'file://' + urllib.pathname2url(self.path)
                            hash = md5.new()
                            hash.update(uri)
                            # Page number is inserted before '.png'.
                            hash = hash.hexdigest() + str(i + 1) + '.png'
                        except:
                            hash = ''
                        thumb_exists = 0
                        if os.path.exists(thumbs_path + hash):
                            try:
                                pixbuf = \
                                    gtk.gdk.pixbuf_new_from_file(
                                    thumbs_path + hash)
                                if (mtime ==
                                    pixbuf.get_option('tEXt::Thumb::MTime')):
                                    thumb_exists = 1
                                    if (pixbuf.get_width() > 
                                        pixbuf.get_height()):
                                        width = self.prefs['thumbnail size']
                                        height = \
                                            pixbuf.get_height() * \
                                            self.prefs['thumbnail size'] / \
                                            pixbuf.get_width()
                                    else:
                                        width = \
                                            pixbuf.get_width() * \
                                            self.prefs['thumbnail size'] / \
                                            pixbuf.get_height()
                                        height = self.prefs['thumbnail size']
                                    if width < 1:
                                        width = 1
                                    if height < 1:
                                        height = 1
                                    pixbuf = \
                                        pixbuf.scale_simple(width, height,
                                        gtk.gdk.INTERP_TILES)
                            except:
                                thumb_exists = 0
                        
                        # ====================================================
                        # There exists no valid thumbnail. We create one.
                        # ====================================================
                        if not thumb_exists:
                            pixbuf = \
                                self.create_thumbnail(file, thumbs_path +
                                hash, 128, {'tEXt::Thumb::URI':uri,
                                'tEXt::Thumb::MTime':mtime,
                                'tEXt::Thumb::Size':
                                str(os.stat(file)[stat.ST_SIZE]),
                                'tEXt::Thumb::Mimetype':
                                gtk.gdk.pixbuf_get_file_info(file)
                                [0]['mime_types'][0],
                                'tEXt::Thumb::Document::Pages':
                                str(len(self.file)),
                                'tEXt::Software':'Comix ' + constants.version}
                                , pixbuf_size = self.prefs['thumbnail size'])
                        
                    # =======================================================
                    # No usage of stored thumbnails, instead we create
                    # thumbnails on the fly. This is much faster than
                    # creating and saving thumbnails, but not as fast as
                    # loading precreated thumbnails.
                    # =======================================================
                    else:
                        pixbuf = \
                            gtk.gdk.pixbuf_new_from_file_at_size(file,
                            self.prefs['thumbnail size'],
                            self.prefs['thumbnail size'])
                except:
                    pixbuf = \
                        self.about_dialog.render_icon(
                        gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                    pixbuf = \
                        pixbuf.scale_simple(self.prefs['thumbnail size'],
                        pixbuf.get_height() * self.prefs['thumbnail size'] / 
                        pixbuf.get_width(), gtk.gdk.INTERP_TILES)
                
                # =======================================================
                # We make some formatting of the thumbnail, i.e. border,
                # page number etc.
                # =======================================================
                pixmap = \
                    gtk.gdk.Pixmap(self.window.window, pixbuf.get_width(),
                    pixbuf.get_height(), -1)
                pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                    pixbuf.get_width(), pixbuf.get_height())
                pixmap.draw_pixbuf(None, pixbuf, 0, 0, 0, 0, -1, -1,
                    gtk.gdk.RGB_DITHER_MAX, 0, 0)
                pixbuf.get_from_drawable(pixmap,
                    gtk.gdk.colormap_get_system(), 0, 0, 0, 0, -1, -1)
                
                assert(pixbuf.get_colorspace() == gtk.gdk.COLORSPACE_RGB)
                dimensions = pixbuf.get_width(), pixbuf.get_height()
                stride = pixbuf.get_rowstride()
                pixels = pixbuf.get_pixels()
                mode = pixbuf.get_has_alpha() and "RGBA" or "RGB"
                pil_image = \
                    Image.frombuffer(mode, dimensions, pixels, "raw", mode,
                    stride, 1)
                
                if self.prefs['show page numbers on thumbnails']:
                    draw = ImageDraw.Draw(pil_image)
                    text_size = self.pil_font.getsize(str(i + 1))
                    draw.rectangle([0, 0, text_size[0] + 1, text_size[1]],
                        fill=(0, 0, 0))
                    try:
                        draw.text((1, 0), str(i + 1), fill=(255, 255, 255),
                            font=self.pil_font)
                    except:
                        print ('*** Could not draw page numbers on '
                              'thumbnails.\nThis is probably due to a '
                              'buggy build of PIL, see\n'
                              'https://bugzilla.novell.com/show_bug.cgi?'
                              'id=167513\n'
                              'Please try a different build of PIL if you '
                              'want page numbers on the thumbnails.\n')
                
                pil_image = \
                    ImageOps.expand(pil_image, border=1, fill=(0, 0, 0))
                imagestr = pil_image.tostring()
                IS_RGBA = pil_image.mode=='RGBA'
                pixbuf = \
                    gtk.gdk.pixbuf_new_from_data(imagestr,
                    gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8, pil_image.size[0],
                    pil_image.size[1],
                    (IS_RGBA and 4 or 3) * pil_image.size[0])
                
                # Append it to the thumbnail liststore.
                self.thumb_liststore.append([pixbuf])
            
            # =======================================================
            # Check for other pending events.
            # =======================================================
            while gtk.events_pending():
                gtk.main_iteration(False)
            if self.exit:
                return False
            
            # =======================================================
            # Update some information for the GUI.
            # =======================================================
            elif i + 1 > self.number_of_thumbs_loaded:
                self.thumb_total_height = \
                    self.thumb_total_height + \
                    self.thumb_tree_view.get_background_area(i,
                    self.thumb_column).height
                self.thumb_layout.set_size((self.prefs['thumbnail size'] + 7),
                    self.thumb_total_height)
                self.thumb_heights.append(
                    self.thumb_tree_view.get_background_area(i,
                    self.thumb_column).height)
                self.thumb_vadjust_upper = \
                    self.thumb_vadjust.upper - self.window.get_size()[1] + \
                    self.status_size + self.tool_size + self.menu_size
                self.number_of_thumbs_loaded = \
                    self.number_of_thumbs_loaded + 1
            
            gc.collect()
        self.thumb_loop_stop = 1
    
    def create_thumbnail(self, src_path, dst_path, size, tEXt_dict={},
        overlay=None, pixbuf_size=0, return_sizes=False):
        
        ''' Creates a thumbnail, dst_path, in the PNG format, from src_path.
        The thumbnail can fit inside a square with width size.
        
        The data in tEXt_dict will be added to the thumbnail as PNG tEXt
        data. Image width and image height will be added automatically.
        
        If overlay is 'cbt', 'cbz' or 'cbr' a speech bubble with that text
        will be added to the saved thumbnail.
        
        If pixbuf_size is not zero a pixbuf with the thumbnail of size
        pixbuf_size will be returned. 
        
        If return_sizes is True the returned pixbuf will be in a tuple with
        the width and the height of the original image. '''
        
        try:
            
            # =======================================================
            # Load src_path and scale it down to size.
            # =======================================================
            pixbuf = gtk.gdk.pixbuf_new_from_file(src_path)
            image_width = str(pixbuf.get_width())
            image_height = str(pixbuf.get_height())
            
            if pixbuf.get_width() > 128 or pixbuf.get_height() > 128:
                tEXt_dict['tEXt::Thumb::Image::Width'] = image_width
                tEXt_dict['tEXt::Thumb::Image::Height'] = image_height
                if pixbuf.get_width() > pixbuf.get_height():
                    width = size
                    height = pixbuf.get_height() * size / pixbuf.get_width()
                else:
                    width = pixbuf.get_width() * size / pixbuf.get_height()
                    height = size
                if width < 1:
                    width = 1
                if height < 1:
                    height = 1
                pixbuf = \
                    pixbuf.scale_simple(width, height, gtk.gdk.INTERP_TILES)
                
                # =======================================================
                # Apply possible overlay.
                # =======================================================
                if overlay != None:
                    if os.path.exists('images/' + overlay + '.png'):
                        overlay_path = 'images/' + overlay + '.png'
                    elif os.path.exists('../share/pixmaps/comix/' + overlay +
                        '.png'):
                        overlay_path = \
                            '../share/pixmaps/comix/' + overlay + '.png'
                    elif os.path.exists('/usr/local/share/pixmaps/comix/' +
                        overlay + '.png'):
                        overlay_path = \
                            '/usr/local/share/pixmaps/comix/' + overlay + \
                            '.png'
                    elif os.path.exists('/usr/share/pixmaps/comix/' +
                        overlay + '.png'):
                        overlay_path = \
                            '/usr/share/pixmaps/comix/' + overlay + '.png'
                    pixbuf_overlay = \
                        gtk.gdk.pixbuf_new_from_file(overlay_path)
                    pixbuf_overlay.composite(pixbuf, pixbuf.get_width() - 35,
                        pixbuf.get_height() - 30, 30, 25,
                        pixbuf.get_width() - 35, pixbuf.get_height() - 30,
                        1.0, 1.0, gtk.gdk.INTERP_BILINEAR, 255)
                
                # =======================================================
                # Save the thumbnail to dst_path.
                # =======================================================
                if not os.path.isdir(os.path.dirname(dst_path)):
                    os.makedirs(os.path.dirname(dst_path))
                    os.chmod(os.path.dirname(dst_path), 0700)
                pixbuf.save(dst_path + 'comix_' + constants.version + '_temp',
                    'png', tEXt_dict)
                # To assure the users privacy we chmod it 600.
                os.chmod(dst_path + 'comix_' + constants.version + '_temp',
                    0600)
                # Then we rename it to the final name (atom operation.)
                os.rename(dst_path + 'comix_' + constants.version + '_temp',
                    dst_path)
                
            # =======================================================
            # We scale it down to pixbuf_size and return the pixbuf
            # (if a pixbuf size has been given.)
            # =======================================================
            if pixbuf_size != 0:
                if pixbuf.get_width() > pixbuf.get_height():
                    width = pixbuf_size
                    height = \
                        pixbuf.get_height() * pixbuf_size / pixbuf.get_width()
                else:
                    width = \
                        pixbuf.get_width() * pixbuf_size / pixbuf.get_height()
                    height = pixbuf_size
                if width < 1:
                    width = 1
                if height < 1:
                    height = 1
                pixbuf = \
                    pixbuf.scale_simple(width, height, gtk.gdk.INTERP_TILES)
                if return_sizes:
                    return (pixbuf, image_width, image_height)
                return pixbuf
            return False
        except:
            if pixbuf_size != 0:
                return self.about_dialog.render_icon(gtk.STOCK_MISSING_IMAGE,
                    gtk.ICON_SIZE_DIALOG)
            return False
    
    def set_cursor_type(self, mode='normal'):
        
        ''' Sets the cursor type depending on mode. '''

        if self.exit:
            return False
        
        if mode == 'normal':
            if self.prefs['hide cursor'] and self.prefs['fullscreen']:
                pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
                color = gtk.gdk.Color()
                cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
                for x in gtk.gdk.window_get_toplevels():
                    x.set_cursor(None)
                self.layout.window.set_cursor(cursor)
            else:
                for x in gtk.gdk.window_get_toplevels():
                    x.set_cursor(None)
                self.layout.window.set_cursor(None)
        elif mode == 'watch':
            for x in gtk.gdk.window_get_toplevels():
                x.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            self.layout.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        elif mode == 'fleur':
            for x in gtk.gdk.window_get_toplevels():
                x.set_cursor(None)
            self.layout.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
    
    def set_file_exists(self, exists):
        
        ''' Sets sensitivity on widgets and the like depending on whether a
        file is loaded or not. '''
        
        if exists:
            self.file_exists = 1
            self.filetype_error = 0
            self.actiongroup.get_action('File').set_sensitive(True)
            self.actiongroup.get_action('Save_book').set_sensitive(True)
            self.actiongroup.get_action('Convert').set_sensitive(True)
            self.actiongroup.get_action('Extract').set_sensitive(True)
            self.actiongroup.get_action('Close').set_sensitive(True)
            self.actiongroup.get_action('Go').set_sensitive(True)
            self.actiongroup.get_action('Next').set_sensitive(True)
            self.actiongroup.get_action('Previous').set_sensitive(True)
            self.actiongroup.get_action('First').set_sensitive(True)
            self.actiongroup.get_action('Last').set_sensitive(True)
            self.actiongroup.get_action('Rotate_90').set_sensitive(True)
            self.actiongroup.get_action('Rotate_180').set_sensitive(True)
            self.actiongroup.get_action('Rotate_270').set_sensitive(True)
            self.actiongroup.get_action('Flip_horiz').set_sensitive(True)
            self.actiongroup.get_action('Flip_vert').set_sensitive(True)
            self.actiongroup.get_action('Slideshow').set_sensitive(True)
            if self.archive_type == '' and not self.prefs['double page']:
                self.actiongroup.get_action('Delete').set_sensitive(True)
                self.jpegtran_activate(bool(self.jpegtran))
            else:
                self.actiongroup.get_action('Delete').set_sensitive(False)
                self.jpegtran_activate(False)
            if self.archive_type != '':
                self.actiongroup.get_action('Add_to_library').set_sensitive(
                    True)
            else:
                self.actiongroup.get_action('Add_to_library').set_sensitive(
                    False)
            self.toolbutton_previous.set_sensitive(True)
            self.toolbutton_next.set_sensitive(True)
            self.toolbutton_first.set_sensitive(True)
            self.toolbutton_last.set_sensitive(True)
            self.toolbutton_go.set_sensitive(True)
            self.bookmark_dialog.action_area.get_children()[2].set_sensitive(
                True)
            if len(self.comment) > 0:
                self.actiongroup.get_action('Comments').set_sensitive(True)
            else:
                self.actiongroup.get_action('Comments').set_sensitive(False)
            self.comix_image.hide()
        else:
            self.path = ''
            self.file_exists = 0
            self.file_number = 0
            self.number_of_thumbs_loaded = 0
            self.actiongroup.get_action('Comments').set_sensitive(False)
            self.actiongroup.get_action('File').set_sensitive(False)
            self.actiongroup.get_action('Save_book').set_sensitive(False)
            self.actiongroup.get_action('Convert').set_sensitive(False)
            self.actiongroup.get_action('Extract').set_sensitive(False)
            self.actiongroup.get_action('Close').set_sensitive(False)
            self.actiongroup.get_action('Go').set_sensitive(False)
            self.actiongroup.get_action('Next').set_sensitive(False)
            self.actiongroup.get_action('Previous').set_sensitive(False)
            self.actiongroup.get_action('First').set_sensitive(False)
            self.actiongroup.get_action('Last').set_sensitive(False)
            self.actiongroup.get_action('Rotate_90').set_sensitive(False)
            self.actiongroup.get_action('Rotate_180').set_sensitive(False)
            self.actiongroup.get_action('Rotate_270').set_sensitive(False)
            self.actiongroup.get_action('Flip_horiz').set_sensitive(False)
            self.actiongroup.get_action('Flip_vert').set_sensitive(False)
            self.actiongroup.get_action('Add_to_library').set_sensitive(False)
            self.actiongroup.get_action('Slideshow').set_sensitive(False)
            self.actiongroup.get_action('Delete').set_sensitive(False)
            self.toolbutton_previous.set_sensitive(False)
            self.toolbutton_next.set_sensitive(False)
            self.toolbutton_first.set_sensitive(False)
            self.toolbutton_last.set_sensitive(False)
            self.toolbutton_go.set_sensitive(False)
            self.bookmark_dialog.action_area.get_children()[2].set_sensitive(
                False)
            self.thumb_liststore.clear()
            self.thumb_vadjust.set_value(0)
            self.thumb_liststore.clear()
            self.thumb_heights = []
            self.stored_pixbuf = 0
            if self.thumb_total_height != 0:
                self.thumb_total_height = 0
                self.thumb_layout.set_size(
                    (self.prefs['thumbnail size'] + 7), 0)
            self.update_sizes()
            self.layout.move(self.comix_image, 
                max(0, self.main_layout_x_size // 2 - 150),
                max(0, self.main_layout_y_size // 2 - 150))
            self.colour_adjust_histogram.clear()
            self.comix_image.show()

    def is_image_file(self, path):
        
        ''' Returns True if path is an image file in a supported format. '''
        
        if os.path.isfile(path): 
            info = gtk.gdk.pixbuf_get_file_info(path)
            if (info != None and info[0]['mime_types'][0]
                in ['image/jpeg', 'image/bmp', 'image/gif',
                'image/png', 'image/tiff', 'image/x-icon',
                'image/x-xpixmap', 'image/x-xbitmap', 'image/svg+xml',
                'image/svg', 'image/svg-xml', 'image/vnd.adobe.svg+xml',
                'text/xml-svg', 'image/x-portable-anymap',
                'image/x-portable-bitmap', 'image/x-portable-graymap',
                'image/x-portable-pixmap', 'image/x-pcx',
                'image/x-cmu-raster', 'image/x-sun-raster', 
                'image/x-tga']):
                    return info[0]['mime_types'][0]
        return False
    
    def extract_archive(self, src_path, dst_path):
        
        ''' Extracts an archive to dst_path. Returns the archive type or an
        emtpy string if the extraction fails. '''
        
        if not dst_path.endswith('/'):
            dst_path += '/'
        archive_type = self.archive_mime_type(src_path)
        try:
            
            # =======================================================
            # Zip archive.
            # =======================================================
            if archive_type == 'zip':
                zipf = zipfile.ZipFile(src_path)
                zipfiles = zipf.namelist()
                for i, x in enumerate(zipfiles):
                    # Caught the directory descriptor. Skip it.
                    if x.endswith('/'):
                        continue
                    # FIXME: Other possible encodings?
                    dst = unicode(x, 'cp437')
                    found_encoding = False
                    for enc in (sys.getfilesystemencoding(),
                        sys.getdefaultencoding(), 'utf8', 'latin-1'):
                        try:
                            dst = dst.encode(enc)
                        except:
                            pass
                        else:
                            found_encoding = True
                            break
                    if not found_encoding:
                        dst = str(i) + '_unknown_encoding'
                    if zipf.getinfo(x).file_size > 0:
                        if not os.path.exists(
                            os.path.dirname(dst_path + dst)):
                            os.makedirs(os.path.dirname(dst_path + dst))
                        new = open(dst_path + dst, 'w')
                        new.write(zipf.read(x))
                        new.close()
                zipf.close()
                return _("Zip archive")
            
            # =======================================================
            # Tar archive.
            # =======================================================
            elif archive_type in ['tar', 'gzip', 'bzip2']:
                tar = tarfile.open(src_path, 'r')
                tarfiles = tar.getmembers()
                for x in tarfiles:
                    tar.extract(x, dst_path)
                tar.close()
                if archive_type == 'gzip':
                    return _("Gzip compressed tar archive")
                elif archive_type == 'bzip2':
                    return _("Bzip2 compressed tar archive")
                else:
                    return _("Tar archive")
            
            # =======================================================
            # RAR archive.
            # =======================================================
            elif archive_type == 'rar':
                if self.rar:
                    os.popen(
                        self.rar + ' x "' + src_path + '" "' + dst_path + '"')
                else:
                    self.statusbar.push(0,
                        _('Could not find the unrar executable. Please install it if you wish to open RAR archives.'))
                    self.failed_to_open_file = 1
                return _("RAR archive")
            return ''
        except:
            self.statusbar.push(0, _('Could not open') + ' ' +
                self.to_unicode(src_path))
            self.failed_to_open_file = 1
    
    def load_file(self, path, page):
        
        ''' Loads an archive or a directory of images from disk.
        Supported archive types are Zip, RAR (if rar/unrar is installed),
        tar, tar.gz and tar.bz2. Subarchives and subdirectories are
        loaded inside archives. '''
        
        if self.exit:
            return False
        
        self.set_cursor_type('watch')
        self.path = path
        self.file = []
        self.file_number = 0
        self.old_file_number = -1
        self.number_of_cached = [-1]
        self.comment = []
        self.comment_number = 0
        self.show_comments = 0
        self.archive_type = ''
        self.change_scroll_adjustment = 1
        self.change_thumb_selection = 1
        self.number_of_thumbs_loaded = 0
        self.thumb_vadjust.set_value(0)
        self.thumb_liststore.clear()
        self.thumb_heights = []
        self.thumb_total_height = 0
        self.thumb_loop_stop = 1
        self.stored_pixbuf = 0
        self.failed_to_open_file = 0
        if not self.prefs['keep transformation']:
            self.prefs['rotation'] = 0
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            os.makedirs(self.base_dir)
        
        # =======================================================
        # If the given path is invalid.
        # =======================================================
        if not os.path.isfile(path):
            if os.path.isdir(path):
                self.statusbar.push(0, '"' + self.to_unicode(
                os.path.basename(path)) + '" ' + _('is not a file.'))
            else:
                self.statusbar.push(0, '"' + self.to_unicode(
                os.path.basename(path)) + '" ' + _('does not exist.'))
            self.filetype_error = 1
            self.set_file_exists(False)
            self.set_cursor_type('normal')
            return 0
        
        else:
            
            # =======================================================
            # Parse the user-defined comment extensions data to a
            # list with the valid extensions.
            # =======================================================
            comment_extensions = \
                map(lambda s: '.' + s,
                self.prefs['comment extensions'].split())
            
            # =======================================================
            # If the file is an archive we extract it.
            # =======================================================
            self.archive_type = self.extract_archive(path, self.base_dir)
            
            # =======================================================
            # The file is an archive. We go through the unpacked data
            # and look for more archives and/or directories. In the
            # end all files will be directly in the /tmp/comix/<num>
            # base directory.
            # =======================================================
            if self.archive_type != '':
                dir = 1
                while (dir):
                    dir = 0
                    temp = os.listdir(self.base_dir)
                    for infile in temp:
                        infile = self.base_dir + infile
                        # Directories will be removed and their contents will
                        # be moved up one step in the directory structure.
                        if os.path.isdir(infile):
                            for x in os.listdir(infile):
                                src = infile + "/" + x
                                dst = \
                                    os.path.dirname(infile) + "/" + \
                                    os.path.basename(infile) + x
                                while (True):
                                    if os.path.exists(dst):
                                        dst = dst[:-len(x)] + "z" +  x
                                    else:
                                        break
                                shutil.move(src, dst)
                            shutil.rmtree(infile)
                            temp.remove(infile[len(self.base_dir):])
                            dir = 1
                            self.file = []
                            break
                        
                        # ====================================================
                        # Archives will be extracted in new directories and
                        # then removed.
                        # ====================================================
                        elif self.archive_mime_type(infile) != '':
                            i = 1
                            while(1):
                                temp_dir = infile + 'z' * i + '/'
                                if os.path.exists(temp_dir):
                                    i += 1
                                else:
                                    break
                            os.mkdir(temp_dir)
                            self.extract_archive(infile, temp_dir)
                            os.remove(infile)
                            dir = 1
                
                # =======================================================
                # When the temp data has been arranged we add image files
                # and comment files to their corresponding lists.
                # =======================================================
                for infile in temp:
                    infile = self.base_dir + infile
                    if self.is_image_file(infile):
                        self.file.append(infile)
                    elif (os.path.splitext(infile)[1].lower() in
                        comment_extensions):
                        self.comment.append(infile)
                
                # Sort the list after the standards set up by the LC_COLLATE
                # environmental variable
                self.file.sort(locale.strcoll)
            
            # =======================================================
            # The opened file is a plain file in a directory.
            # =======================================================
            else:
                self.archive_type = ''
                temp = os.listdir(os.path.dirname(path))
                
                # Add files to their corresponding lists.
                for infile in temp:
                    infile = os.path.dirname(path) + '/' + infile
                    if self.is_image_file(infile):
                        self.file.append(infile)
                    elif (os.path.isfile(infile) and
                        os.path.splitext(infile)[1].lower() in
                        comment_extensions):
                        self.comment.append(infile)
                
                # If the specific file opened is invalid
                if self.file.count(path) == 0:
                    for i in range(len(self.file)):
                        self.file.pop()
                    self.statusbar.push(0, _('Filetype of') + ' "' +
                        self.to_unicode(os.path.basename(path)) + '" ' +
                        _('not recognized.'))
                    self.filetype_error = 1
                
                # Sort by LC_COLLATE and set the filenumber to that
                # of the opened file
                else:
                    self.file.sort(locale.strcoll)
                    self.file_number = self.file.index(path)
        
        # =======================================================
        # If there are no viewable image files opened.
        # =======================================================
        if len(self.file) == 0:
            if self.archive_type != '':
                if not self.failed_to_open_file:
                    self.statusbar.push(0, _('No images in "%s"') % 
                    self.to_unicode(os.path.basename(path)))
                self.filetype_error = 1
            self.set_file_exists(False)
        
        # =======================================================
        # There are at least one valid image file.
        # =======================================================
        else:
            self.set_file_exists(True)
            if self.prefs['auto comments'] and len(self.comment) > 0:
                self.show_comments = 1
            
            # Set the correct page number.
            if page == -2:
                pass
            elif page == -1:
                if len(self.file) > 1 and self.prefs['double page']:
                    self.file_number = len(self.file) - 2
                else:
                    self.file_number = len(self.file) - 1
            else:
                if page < len(self.file) and page >= 0:
                    self.file_number = page
                else:
                    self.file_number = 0
            self.refresh_image()
            self.add_menu_thumb(None, path, 'recent')
            self.load_thumbnails()
            
            if self.exit:
                return False
        
        self.set_cursor_type('normal')
    
    def start_slideshow(self, *args):

        ''' Starts a slideshow. '''
        
        self.stop_slideshow()
        self.old_zoom_mode = self.prefs['zoom mode']
        self.old_hide_in_fullscreen = self.prefs['hide in fullscreen']
        self.old_fullscreen = self.prefs['fullscreen']
        self.prefs['zoom mode'] = 1
        self.prefs['hide in fullscreen'] = 1
        self.slideshow_label_even = True
        self.slideshow_label_timer_ids = []
        self.slideshow_timer_id = gobject.timeout_add(
            int(self.prefs['slideshow delay'] * 1000), self.new_slide)
        self.slideshow_started = True
        if not self.prefs['fullscreen']:
            self.fullscreen_switch(None)
        else:
            self.refresh_image()
        for n, t in enumerate(
            range(0, int(self.prefs['slideshow delay'] * 1000),
            int(self.prefs['slideshow delay'] * 1000) / 22)):
            self.slideshow_label_timer_ids.append(
                gobject.timeout_add(t, self.put_slideshow_label, n))
        self.slideshow_label_box.show()

    def stop_slideshow(self):

        ''' Stops the slideshow (if it is started). '''
            
        if self.slideshow_timer_id != None:
            gobject.source_remove(self.slideshow_timer_id)
            for tid in self.slideshow_label_timer_ids:
                gobject.source_remove(tid)
            self.slideshow_timer_id = None
            self.prefs['zoom mode'] = self.old_zoom_mode
            self.prefs['hide in fullscreen'] = self.old_hide_in_fullscreen
            self.slideshow_label_box.hide()
            if not self.old_fullscreen:
                self.fullscreen_switch(None)
            else:
                self.refresh_image()
            self.slideshow_started = False

    def new_slide(self):
        
        ''' Flips to the next slide. '''
         
        for tid in self.slideshow_label_timer_ids:
            gobject.source_remove(tid)
        if (self.file_number + self.prefs['double page'] >=
            len(self.file) - 1):
            self.stop_slideshow()
            return False
        if self.prefs['double page']:
            self.file_number += 2
        else:
            self.file_number += 1
        self.change_scroll_adjustment = 1
        self.change_thumb_selection = 1
        if not self.prefs['keep transformation']:
            self.prefs['rotation'] = 0
            self.prefs['flip horiz'] = 0
            self.prefs['flip vert'] = 0
        self.refresh_image()
        self.slideshow_label_even = not self.slideshow_label_even
        for n, t in enumerate(
            range(0, int(self.prefs['slideshow delay'] * 1000),
            int(self.prefs['slideshow delay'] * 1000) / 22)):
            self.slideshow_label_timer_ids.append(
                gobject.timeout_add(t, self.put_slideshow_label, n))
        return True

    def put_slideshow_label(self, timer=0):
        
        ''' Updates the slideshow label in the bottom right corner. '''
        
        if (not self.prefs['double page'] or len(self.file) ==
            self.file_number + 1):
            page_number = \
                str(self.file_number + 1) + ' / ' + str(len(self.file))
        else:
            page_number = \
                str(self.file_number + 1) + ',' + \
                str(self.file_number + 2) + ' / ' + str(len(self.file))
        label = self.slideshow_label_box.get_children()[0].get_children()[0]
        label.set_text(page_number + '   IIIIIIIIIIIIIIIIIIII')
        attrlist = pango.AttrList()
        if (self.prefs['red bg'] + self.prefs['green bg'] +
            self.prefs['blue bg'] < 80000):
            c1 = 65535
            c2 = 35000
        else:
            c1 = 0
            c2 = 35000
        if self.slideshow_label_even:
            attrlist.insert(pango.AttrForeground(c1, c1, c1, 0,
                len(page_number) + 3 + timer))
            attrlist.insert(pango.AttrForeground(c2, c2, c2, 
                len(page_number) + 3 + timer, len(label.get_text())))
        else:
            attrlist.insert(pango.AttrForeground(c1, c1, c1, 0,
                len(page_number)))
            attrlist.insert(pango.AttrForeground(c2, c2, c2, 
                len(page_number) + 3, len(page_number) + 3 + timer))
            attrlist.insert(pango.AttrForeground(c1, c1, c1, 
                len(page_number) + 3 + timer, len(label.get_text())))
        attrlist.insert(pango.AttrFamily('sans', 0, len(label.get_text())))
        label.set_attributes(attrlist)
        self.slideshow_label_box.modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(
            gtk.gdk.Color(self.prefs['red bg'], self.prefs['green bg'],
            self.prefs['blue bg']), False, True))
        self.slideshow_label_box.get_children()[0].modify_bg(gtk.STATE_NORMAL,
            gtk.gdk.colormap_get_system().alloc_color(
            gtk.gdk.Color(self.prefs['red bg'], self.prefs['green bg'],
            self.prefs['blue bg']), False, True))
        self.layout.move(self.slideshow_label_box,
            self.window.get_screen().get_width() -
            self.slideshow_label_box.size_request()[0],
            self.window.get_screen().get_height() - 
            self.slideshow_label_box.size_request()[1])

    def to_unicode(self, string):
        
        ''' Converts string to unicode. First tries the default filesystem
        encoding, and then falls back on some common encodings. If none
        of the convertions are successful it returns an error message. '''

        # FIXME: Should investigate more which encodings are possible to
        # test that results in unique failure/success depending on the bit
        # patterns, and which are the most common ones and thus best to test.
        
        if type(string) == unicode:
            return string
        for encoding in (sys.getfilesystemencoding(), 'utf-8', 'latin-1'):
            try:
                ustring = unicode(string, encoding)
                return ustring
            except (UnicodeError, LookupError):
                pass
        return '???'

    def delete_file(self, *args):
        
        if self.exit:
            return False

        if (self.prefs['double page'] or self.archive_type != '' or 
            not self.file_exists):
            return
        self.are_you_sure_dialog_update(os.path.basename(
            self.file[self.file_number]), 'del')
        response = self.are_you_sure_dialog.run()
        self.are_you_sure_dialog.hide()
        if response != -5:
            return

        try:
            os.remove(self.file[self.file_number])
        except:
            self.wrong_permissions_dialog_open(os.path.basename(
                self.file[self.file_number]), 1)
            return
        try:
            uri = 'file://' + urllib.pathname2url(self.file[self.file_number])
            thumb_path = md5.new()
            thumb_path.update(uri)
            thumb_path = \
                os.path.join(os.environ['HOME'], '.thumbnails', 'normal',
                thumb_path.hexdigest() + '.png')
            os.remove(thumb_path)
        except:
            pass
        self.file.pop(self.file_number)
        if self.file_number >= len(self.file):
            self.file_number -= 1
        self.number_of_cached = [None]
        self.stored_pixbuf = 0
        self.refresh_image()
        self.thumb_tree_view.get_selection().disconnect(
            self.thumb_selection_handler)
        self.thumb_column.set_fixed_width(self.prefs['thumbnail size'] + 7)
        self.thumb_layout.set_size_request(
            self.prefs['thumbnail size'] + 7, 0)
        self.change_thumb_selection = 1
        self.number_of_thumbs_loaded = 0
        self.thumb_vadjust.set_value(0)
        self.thumb_liststore.clear()
        self.thumb_heights = []
        self.thumb_total_height = 0
        self.thumb_loop_stop = 1
        self.thumb_selection_handler = \
            self.thumb_tree_view.get_selection().connect(
            'changed', self.thumb_selection_event)
        self.load_thumbnails()
        self.refresh_image()

    def jpegtran_activate(self, activate):

        ''' Activate image operations if jpegtran is installed'''

        self.actiongroup.get_action('file_rot_90').\
            set_sensitive(activate)
        self.actiongroup.get_action('file_rot_270').\
            set_sensitive(activate)
        self.actiongroup.get_action('file_flip_horiz').\
            set_sensitive(activate)
        self.actiongroup.get_action('file_flip_vert').\
            set_sensitive(activate)
        self.actiongroup.get_action('file_desaturate').\
            set_sensitive(activate)

    def jpegtran_operation(self, operation):

        ''' Performs the jpegtran <operation> on the current image. '''
        
        if self.exit:
            return False
        if (self.prefs['double page'] or self.archive_type != '' or 
            not self.jpegtran):
            return
        if operation.startswith('-rotate') or operation.startswith('-flip'):
            mode = 'rot-flip'
        elif operation == '-grayscale':
            mode = 'grayscale'
        self.are_you_sure_dialog_update(os.path.basename(
            self.file[self.file_number]), mode)
        response = self.are_you_sure_dialog.run()
        self.are_you_sure_dialog.hide()
        if response != -5:
            return
        os.popen(self.jpegtran + ' -copy all -trim ' + operation +
            ' -outfile "' + self.file[self.file_number] + '" "' +
            self.file[self.file_number] + '"')
        try:
            uri = 'file://' + urllib.pathname2url(self.file[self.file_number])
            thumb_path = md5.new()
            thumb_path.update(uri)
            thumb_path = \
                os.path.join(os.environ['HOME'], '.thumbnails', 'normal',
                thumb_path.hexdigest() + '.png')
            os.remove(thumb_path)
        except:
            pass
        self.number_of_cached = [None]
        self.stored_pixbuf = 0
        self.refresh_image()
        self.thumb_tree_view.get_selection().disconnect(
            self.thumb_selection_handler)
        self.thumb_column.set_fixed_width(self.prefs['thumbnail size'] + 7)
        self.thumb_layout.set_size_request(
            self.prefs['thumbnail size'] + 7, 0)
        self.change_thumb_selection = 1
        self.number_of_thumbs_loaded = 0
        self.thumb_vadjust.set_value(0)
        self.thumb_liststore.clear()
        self.thumb_heights = []
        self.thumb_total_height = 0
        self.thumb_loop_stop = 1
        self.thumb_selection_handler = \
            self.thumb_tree_view.get_selection().connect(
            'changed', self.thumb_selection_event)
        self.load_thumbnails()
        self.refresh_image()

    def rotate_file_90(self, *args):
        
        if self.exit:
            return False

        self.jpegtran_operation('-rotate 90')

    def rotate_file_270(self, *args):
        
        if self.exit:
            return False

        self.jpegtran_operation('-rotate 270')

    def flip_file_horizontal(self, *args):
        
        if self.exit:
            return False

        self.jpegtran_operation('-flip horizontal')

    def flip_file_vertical(self, *args):
        
        if self.exit:
            return False

        self.jpegtran_operation('-flip vertical')

    def desaturate_file(self, *args):
        
        if self.exit:
            return False

        self.jpegtran_operation('-grayscale')

    def refresh_image(self):

        ''' Loads image files, from memory or from disk, scales them and does
        other operations on them and then redraws the main part of the window
        completely. Also caches image files as in-memory pixbufs. '''
        
        if self.exit:
            return False
        if not self.refresh_activated:
            return

        # =======================================================
        # Check if the last viewed page was a two page scan (i.e.
        # two pages in one image file) and handle it accordingly.
        # =======================================================
        if self.two_page_scan != None:
            if self.two_page_scan != self.file_number:
                self.prefs['double page'] = 1
                self.two_page_scan = None
                if self.old_file_number == self.file_number + 1:
                    self.file_number -= 1
                    self.number_of_cached = [-1]
        
        # =======================================================
        # Reset the number of scroll events that has been caught.
        # Used in scroll_wheel_event() if the "Flip page when
        # scrolling of the top or bottom of the page" preference
        # is set.
        # =======================================================
        self.scroll_events_down = 0
        self.scroll_events_up = 0
        
        # =======================================================
        # Must be single plain jpeg if we want to rotate it.
        # =======================================================
        if (self.file_exists and not self.prefs['double page'] and
            self.archive_type == '' and
            self.is_image_file(self.file[self.file_number]) == 'image/jpeg'
            and self.jpegtran):
            self.jpegtran_activate(True)
        else:
            self.jpegtran_activate(False)

        # =======================================================
        # Hide/unhide toolbar, scrollbars etc. depending on the
        # set preferences and then update all the stored pixel
        # sizes for these widgets.
        # =======================================================
        
        # Hide everything if in fullscreen with the hide in fullscreen
        # option set.
        if (self.prefs['hide in fullscreen'] and
            self.prefs['fullscreen']) or self.prefs['hide all']:
            self.actiongroup.get_action('Menubar').set_sensitive(False)
            self.actiongroup.get_action('Toolbar').set_sensitive(False)
            self.actiongroup.get_action('Statusbar').set_sensitive(False)
            self.actiongroup.get_action('Scrollbars').set_sensitive(False)
            self.actiongroup.get_action('Thumbnails').set_sensitive(False)
            self.ui.get_widget('/Menu').hide()
            self.toolbar.hide()
            self.statusbar.hide()
            self.hscroll.hide()
            self.vscroll.hide()
            self.thumb_layout.hide()
            self.thumb_vscroll.hide()
        
        # Else hide/show according to each corresponding option.
        else:
            self.actiongroup.get_action('Menubar').set_sensitive(True)
            self.actiongroup.get_action('Toolbar').set_sensitive(True)
            self.actiongroup.get_action('Statusbar').set_sensitive(True)
            self.actiongroup.get_action('Scrollbars').set_sensitive(True)
            self.actiongroup.get_action('Thumbnails').set_sensitive(True)
            if self.prefs['show thumbnails']:
                self.thumb_layout.show()
                if self.prefs['hide thumbnail scrollbar']:
                    self.thumb_vscroll.hide()
                else:
                    self.thumb_vscroll.show()
            else:
                self.thumb_layout.hide()
                self.thumb_vscroll.hide()
            if self.prefs['hide scrollbar'] or self.prefs['zoom mode'] == 1:
                self.hscroll.hide()
                self.vscroll.hide()
            elif self.prefs['zoom mode'] == 2:
                self.hscroll.hide()
                self.vscroll.show()
            elif self.prefs['zoom mode'] == 3:
                self.vscroll.hide()
                self.hscroll.show()
            else:
                self.hscroll.show()
                self.vscroll.show()
            if not self.prefs['show menubar']:
                self.ui.get_widget('/Menu').hide()
            else:
                self.ui.get_widget('/Menu').show()
            if not self.prefs['show toolbar']:
                self.toolbar.hide()
            else:
                self.toolbar.show()
            if not self.prefs['show statusbar']:
                self.statusbar.hide()
            else:
                self.statusbar.show()
            
            # Always show scrollbars when viewing comments
            if self.show_comments:
                self.hscroll.show()
                self.vscroll.show()
        
        self.toolbar.set_style(self.prefs['toolbar style'])
        self.update_sizes()
        
        # =======================================================
        # Calculate the size of the image displaying area in the
        # main window and make sure the window is displayed.
        # =======================================================
        x = self.main_layout_x_size
        y = self.main_layout_y_size
        if not self.prefs['fullscreen']:
            self.window.resize(self.prefs['window width'],
                self.prefs['window height'])
        
        self.window.show()
        
        # =======================================================
        # Display a comment instead of images.
        # =======================================================
        if self.show_comments:
            self.image.hide()
            self.image2.hide()
            
            # Set the text colour to white if using a dark background and
            # to black if using light background.
            if (self.prefs['red bg'] + self.prefs['green bg'] +
                self.prefs['blue bg'] < 80000):
                self.comment_label.modify_fg(gtk.STATE_NORMAL,
                    gtk.gdk.colormap_get_system().alloc_color(
                    gtk.gdk.color_parse('#FFFFFF'), False, True))
            else:
                self.comment_label.modify_fg(gtk.STATE_NORMAL,
                    gtk.gdk.colormap_get_system().alloc_color(
                    gtk.gdk.color_parse('#000000'), False, True))
            
            # Try to open the comments file.
            try:
                comment_file = open(self.comment[self.comment_number], 'r')
                comment_header = \
                    '--- ' + _('Comment file') + ' ' + \
                    str(self.comment_number + 1) + ' ' + _('of') + ' ' + \
                    str(len(self.comment)) + ' - ' + self.to_unicode(
                    os.path.basename(self.comment[self.comment_number])) + \
                    ' ---'
                comment_body = '\n\n' + self.to_unicode(comment_file.read())
                comment_file.close()
                self.comment_label.set_text(comment_header + comment_body)
                attrlist = pango.AttrList()
                attrlist.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0,
                    len(comment_header)))
                attrlist.insert(pango.AttrFamily('mono', len(comment_header),
                    len(comment_body)))
                self.comment_label.set_attributes(attrlist)
            except:
                comment = \
                    _('Could not read') + self.to_unicode(' "' +
                    os.path.basename(self.comment[self.comment_number]) + '"')
                self.comment_label.set_text(comment)
            
            self.comment_label.show()
            self.comment_label.set_padding(10, 10)
            self.layout.set_size(
                self.comment_label.get_layout().get_pixel_size()[0] + 20,
                self.comment_label.get_layout().get_pixel_size()[1] + 20)
            
            # Set window title and statusbar message.
            if self.archive_type != '':
                self.window.set_title(self.to_unicode(os.path.basename(
                    self.path)) + ' --- ' + _('Comment') +
                    ' ' + str(self.comment_number + 1) + ' ' + _('of') + ' ' +
                    str(len(self.comment)) + '')
                self.statusbar.push(0, _('Comment') + ' ' +
                    str(self.comment_number + 1) + ' ' + _('of') + ' ' +
                    str(len(self.comment)) + '    ---    ' + self.to_unicode(
                    os.path.basename(self.path)))
            else:
                self.window.set_title(self.to_unicode(os.path.basename(
                    os.path.dirname(self.path))) + ' --- ' +
                    _('Comment') + ' ' + str(self.comment_number + 1) + ' ' +
                    _('of') + ' ' + str(len(self.comment)) + '')
                self.statusbar.push(0, _('Comment') + ' ' +
                    str(self.comment_number + 1) + ' ' + _('of') + ' ' +
                    str(len(self.comment)) + '    ---    ' + self.to_unicode(
                    os.path.basename(os.path.dirname(self.path))))
        
        else:
            self.comment_label.hide()
            if self.file_exists:
                backwards_caching = 0
                
                # =======================================================
                # Display an image in single page mode.
                # =======================================================
                if (not self.prefs['double page'] or len(self.file) ==
                    self.file_number + 1):
                    self.stored_double = 0
                    
                    # =======================================================
                    # Load the image data (from disk or from memory cache).
                    # =======================================================
                    
                    # Switching from double page mode to single page mode.
                    if (self.number_of_cached ==
                        [self.file_number, self.file_number + 1] and
                        self.prefs['cache']):
                        if self.stored_pixbuf != None:
                            pixbuf = self.stored_pixbuf.copy()
                        else:
                            pixbuf = None
                        self.cached_pixbuf = self.stored_pixbuf2
                        self.number_of_cached = [self.file_number + 1]
                        backwards_caching = 1
                    
                    # Refreshing the same image that is already being viewed.
                    elif (self.file_number == self.old_file_number and
                        self.stored_pixbuf != 0):
                        if self.stored_pixbuf != None:
                            pixbuf = self.stored_pixbuf.copy()
                        else:
                            pixbuf = None
                    
                    # Using normal single mode cache.
                    elif (self.file_number == self.number_of_cached[0] and
                        self.prefs['cache']):
                        if self.cached_pixbuf != None:
                            pixbuf = self.cached_pixbuf.copy()
                            self.stored_pixbuf = pixbuf.copy()
                        else:
                            pixbuf = None
                            self.stored_pixbuf = None
                    
                    # No valid cache is present or cache option turned off.
                    else:
                        
                        # When flipping backwards the previously viewed image
                        # is used as the new cache.
                        if (self.file_number == self.old_file_number - 1 and
                            self.prefs['cache']):
                            self.cached_pixbuf = self.stored_pixbuf
                            backwards_caching = 1
                            self.number_of_cached = [self.file_number + 1]
                        
                        # Load new image file from disk
                        try:
                            pixbuf = \
                                gtk.gdk.pixbuf_new_from_file(
                                self.file[self.file_number])
                            self.stored_pixbuf = pixbuf.copy()
                        except:
                            pixbuf = \
                                self.about_dialog.render_icon(
                                gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                            self.stored_pixbuf = pixbuf.copy()
                    
                    # =======================================================
                    # Make sure all data connected to image2 is removed.
                    # =======================================================
                    try:
                        del self.stored_pixbuf2
                    except:
                        pass
                    try:
                        del self.cached_pixbuf2
                    except:
                        pass
                    try:
                        del self.pixbuf2
                    except:
                        pass
                    gc.collect()
                    
                    # =======================================================
                    # Scale the image to fit the display area or to the
                    # current zoom level.
                    # =======================================================
                    temp_x = x
                    temp_y = y
                    
                    # Flip width and height if page is to be rotated 90
                    # or 270 degrees.
                    if self.prefs['rotation'] in [0, 2]:
                        self.image1_width = pixbuf.get_width()
                        self.image1_height = pixbuf.get_height()
                    else:
                        self.image1_height = pixbuf.get_width()
                        self.image1_width = pixbuf.get_height()
                        x = temp_y
                        y = temp_x
                    if ((pixbuf.get_width() > x or pixbuf.get_height() > y or
                        self.prefs['stretch']) and 
                        self.prefs['zoom mode'] == 1 or
                        (pixbuf.get_width() > x or
                        self.prefs['stretch']) and 
                        self.prefs['zoom mode'] == 2 or
                        (pixbuf.get_height() > y or
                        self.prefs['stretch']) and 
                        self.prefs['zoom mode'] == 3 or
                        (self.prefs['zoom scale'] != 100 and
                        not self.prefs['zoom mode'])):
                        if self.prefs['zoom mode'] == 1:
                            if (1.0 * pixbuf.get_width() / x >
                                1.0 * pixbuf.get_height() / y):
                                width = x
                                height = \
                                    pixbuf.get_height() * x / \
                                    pixbuf.get_width()
                            else:
                                width = \
                                    pixbuf.get_width() * y/ \
                                    pixbuf.get_height()
                                height = y
                        elif self.prefs['zoom mode'] == 2:
                            width = x
                            height = \
                                pixbuf.get_height() * x / \
                                pixbuf.get_width()
                        elif self.prefs['zoom mode'] == 3:
                            width = \
                                pixbuf.get_width() * y/ \
                                pixbuf.get_height()
                            height = y
                        else:
                            width = \
                                int(pixbuf.get_width() * \
                                self.prefs['zoom scale'] / 100)
                            height = \
                                int(pixbuf.get_height() * \
                                self.prefs['zoom scale'] / 100)
                        # At least one pixel big or things will get nasty.
                        if width < 1:
                            width = 1
                        if height < 1:
                            height = 1
                        pixbuf = \
                            pixbuf.scale_simple(width, height,
                            self.prefs['interp type'])
                    x = temp_x
                    y = temp_y
                    
                    # =======================================================
                    # Convert image data to a PIL object and perform
                    # transformations on it. Then we convert it back to a GTK
                    # pixbuf.
                    # =======================================================
                    if (self.prefs['rotation'] != 0 or
                        self.prefs['flip horiz'] or
                        self.prefs['flip vert'] or
                        self.prefs['contrast'] != 1.0 or
                        self.prefs['sharpness'] != 1.0 or 
                        self.prefs['saturation'] != 1.0 or
                        self.prefs['brightness'] != 1.0 or
                        self.prefs['autocontrast']):
                        assert(pixbuf.get_colorspace() ==
                            gtk.gdk.COLORSPACE_RGB)
                        dimensions = pixbuf.get_width(), pixbuf.get_height()
                        stride = pixbuf.get_rowstride()
                        pixels = pixbuf.get_pixels()
                        mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
                        pil_image = \
                            Image.frombuffer(mode, dimensions, pixels, 'raw',
                            mode, stride, 1)
                        if self.prefs['rotation'] == 1:
                            pil_image = pil_image.transpose(Image.ROTATE_270)
                        elif self.prefs['rotation'] == 2:
                            pil_image = pil_image.transpose(Image.ROTATE_180)
                        elif self.prefs['rotation'] == 3:
                            pil_image = pil_image.transpose(Image.ROTATE_90)
                        
                        if self.prefs['flip horiz']:
                            pil_image = \
                                pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                        if self.prefs['flip vert']:
                            pil_image = \
                                pil_image.transpose(Image.FLIP_TOP_BOTTOM)
                        
                        if self.prefs['autocontrast'] and mode == 'RGB':
                            pil_image = \
                                ImageOps.autocontrast(pil_image, cutoff=1)
                        elif self.prefs['contrast'] != 1.0:
                            pil_image = \
                                ImageEnhance.Contrast(pil_image).enhance(
                                self.prefs['contrast'])
                        if self.prefs['saturation'] != 1.0:
                            pil_image = \
                                ImageEnhance.Color(pil_image).enhance(
                                self.prefs['saturation'])
                        if self.prefs['brightness'] != 1.0:
                            pil_image = \
                                ImageEnhance.Brightness(pil_image).enhance(
                                self.prefs['brightness'])
                        if self.prefs['sharpness'] != 1.0:
                            pil_image = \
                                ImageEnhance.Sharpness(pil_image).enhance(
                                self.prefs['sharpness'])
                        imagestr = pil_image.tostring()
                        IS_RGBA = pil_image.mode == 'RGBA'
                        pixbuf = \
                            gtk.gdk.pixbuf_new_from_data(imagestr,
                            gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8,
                            pil_image.size[0], pil_image.size[1],
                            (IS_RGBA and 4 or 3) * pil_image.size[0])
                    
                    # =======================================================
                    # Store the width and height of the scaled image. Resize
                    # and move the display area accordingly to these images
                    # dimensions.
                    # =======================================================
                    self.image1_scaled_width = pixbuf.get_width()
                    self.image1_scaled_height = pixbuf.get_height()
                    
                    x_move = (x - pixbuf.get_width()) / 2
                    y_move = (y - pixbuf.get_height()) / 2
                    if x_move < 0:
                        x_move = 0
                    if y_move < 0:
                        y_move = 0
                    
                    self.layout.set_size(pixbuf.get_width(),
                        pixbuf.get_height())
                    self.layout.move(self.image_box, x_move, y_move)
                    
                    if self.colour_adjust_dialog_displayed:
                        self.colour_adjust_draw_histogram(pixbuf)

                    # =======================================================
                    # Create a pixmap, draw the pixbuf on it and then convert
                    # it back to a pixbuf. It is an *ugly* hack, but it gives
                    # us full depth dithering of the image. Then we display
                    # the resulting image.
                    # =======================================================
                    pixmap = \
                        gtk.gdk.Pixmap(self.window.window,
                        self.image1_scaled_width,
                        self.image1_scaled_height, -1)
                    if pixbuf.get_has_alpha():
                        pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                            self.image1_scaled_width,
                            self.image1_scaled_height)
                    pixmap.draw_pixbuf(None, pixbuf, 0, 0, 0, 0, -1, -1,
                        gtk.gdk.RGB_DITHER_MAX, 0, 0)

                    self.image.set_from_pixmap(pixmap, None)
                    self.image2.hide()
                    self.image.show()
                    
                    # =======================================================
                    # Set window title and statusbar message.
                    # =======================================================
                    if self.archive_type != "":
                        self.window.set_title(self.to_unicode(
                            os.path.basename(
                            self.path) + ' --- [' +
                            str(self.file_number + 1) + ' / ' +
                            str(len(self.file)) + ']'))
                        self.statusbar.push(0, self.to_unicode(('[' +
                            str(self.file_number + 1) + ' / ' +
                            str(len(self.file)) + ']    ---    ' +
                            os.path.basename(self.path) +
                            '    ---    ' + str(self.image1_width) + 'x' +
                            str(self.image1_height) + '    ---    ' +
                            str('%.1f' % (100.0 * self.image1_scaled_height /
                            self.image1_height)) + '%')))
                    else:
                        self.window.set_title(self.to_unicode(
                            os.path.basename(
                            os.path.dirname(self.path)) + ' --- [' +
                            str(self.file_number + 1) + ' / ' +
                            str(len(self.file)) + ']'))
                        self.statusbar.push(0, self.to_unicode(('[' +
                            str(self.file_number + 1) + ' / ' +
                            str(len(self.file)) + ']    ---    ' +
                            os.path.basename(os.path.dirname(self.path)) +
                            '/' + os.path.basename(
                            self.file[self.file_number]) + '    ---    ' +
                            str(self.image1_width) + 'x' +
                            str(self.image1_height) + '    ---    ' +
                            str('%.1f' % (100.0 * self.image1_scaled_height /
                            self.image1_height)) + '%')))
                
                # =======================================================
                # Display two images in double page mode.
                # =======================================================
                else:
                    
                    # =======================================================
                    # Load the image data (from disk or from memory cache).
                    # =======================================================
                    
                    # If refreshing the two images previously viewed.
                    if (self.file_number == self.old_file_number and
                        self.stored_double):
                        if self.stored_pixbuf != None:
                            pixbuf = self.stored_pixbuf.copy()
                        else:
                            pixbuf = None
                        if self.stored_pixbuf2 != None:
                            pixbuf2 = self.stored_pixbuf2.copy()
                        else:
                            pixbuf2 = None
                    
                    # Using normal double page mode cache.
                    elif (self.number_of_cached == [self.file_number,
                        self.file_number + 1] and self.prefs['cache']):
                        if self.cached_pixbuf != None:
                            pixbuf = self.cached_pixbuf.copy()
                            self.stored_pixbuf = pixbuf.copy()
                        else:
                            pixbuf = None
                            self.stored_pixbuf = None
                        if self.cached_pixbuf2 != None:
                            pixbuf2 = self.cached_pixbuf2.copy()
                            self.stored_pixbuf2 = pixbuf2.copy()
                        else:
                            pixbuf2 = None
                            self.stored_pixbuf2 = None
                    
                    # Flipping only one page ahead although in
                    # double page mode.
                    elif (self.number_of_cached == [self.file_number + 1,
                        self.file_number + 2] and self.prefs['cache']):
                        if self.stored_pixbuf2 != None:
                            pixbuf = self.stored_pixbuf2.copy()
                            self.stored_pixbuf = pixbuf.copy()
                        else:
                            pixbuf = None
                            self.stored_pixbuf = None
                        if self.cached_pixbuf != None:
                            pixbuf2 = self.cached_pixbuf.copy()
                            self.stored_pixbuf2 = pixbuf2.copy()
                        else:
                            pixbuf2 = None
                            self.stored_pixbuf2 = None
                    
                    # No valid caches present or the cache option turned off.
                    else:
                        
                        # If flipping backwards the previously viewed images
                        # is used as the new cache.
                        if (self.file_number == self.old_file_number - 2 and
                            self.stored_double and self.prefs['cache']):
                            self.cached_pixbuf = self.stored_pixbuf
                            self.cached_pixbuf2 = self.stored_pixbuf2
                            backwards_caching = 1
                            self.number_of_cached = \
                                [self.file_number + 2, self.file_number + 3]
                        
                        # Load new files from disk.
                        try:
                            pixbuf = \
                                gtk.gdk.pixbuf_new_from_file(
                                self.file[self.file_number])
                            self.stored_pixbuf = pixbuf.copy()
                        except:
                            pixbuf = \
                                self.about_dialog.render_icon(
                                gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                            self.stored_pixbuf = pixbuf.copy()
                        try:
                            pixbuf2 = \
                                gtk.gdk.pixbuf_new_from_file(
                                self.file[self.file_number + 1])
                            self.stored_pixbuf2 = pixbuf2.copy()
                        except:
                            pixbuf2 = \
                                self.about_dialog.render_icon(
                                gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                            self.stored_pixbuf2 = pixbuf2.copy()
                    
                    self.stored_double = 1
                    
                    # =======================================================
                    # If one or both of the images is a two page scan (i.e.
                    # it's width is greater than it's height) and the
                    # "Display only one page in double page mode if the image
                    # is wide" preference is set, we set the recurse but this
                    # time we choose single page mode.
                    # =======================================================
                    if (self.prefs['no double page for wide images'] and
                        (pixbuf.get_width() > pixbuf.get_height() or
                        pixbuf2.get_width() > pixbuf2.get_height())):
                        self.prefs['double page'] = 0
                        temp_file_number = self.old_file_number
                        self.old_file_number = self.file_number
                        if temp_file_number == self.file_number + 2:
                            self.file_number += 1
                        self.two_page_scan = self.file_number
                        self.refresh_image()
                        return 0
                    
                    # =======================================================
                    # Scale the images to fit the display area or to the
                    # current zoom level.
                    # =======================================================
                    temp_x = x
                    temp_y = y
                    
                    # Flip width and height if page is to be rotated
                    # 90 or 270 degrees.
                    if self.prefs['rotation'] in [0, 2]:
                        self.image1_width = pixbuf.get_width()
                        self.image1_height = pixbuf.get_height()
                        self.image2_width = pixbuf2.get_width()
                        self.image2_height = pixbuf2.get_height()
                        height = \
                            max(pixbuf.get_height(), pixbuf2.get_height())
                        width = pixbuf.get_width() + pixbuf2.get_width()
                    else:
                        self.image1_height = pixbuf.get_width()
                        self.image1_width = pixbuf.get_height()
                        self.image2_height = pixbuf2.get_width()
                        self.image2_width = pixbuf2.get_height()
                        x = temp_y
                        y = temp_x
                        width = max(pixbuf.get_width(), pixbuf2.get_width())
                        height = pixbuf.get_height() + pixbuf2.get_height()
                    width1 = pixbuf.get_width()
                    height1 = pixbuf.get_height()
                    width2 = pixbuf2.get_width()
                    height2 = pixbuf2.get_height()
                    
                    if ((width > x or height > y or self.prefs['stretch']) and
                        self.prefs['zoom mode'] == 1 or
                        (width > x or self.prefs['stretch']) and
                        self.prefs['zoom mode'] == 2 or
                        (height > y or self.prefs['stretch']) and
                        self.prefs['zoom mode'] == 3 or
                        (self.prefs['zoom scale'] != 100 and
                        not self.prefs['zoom mode'])):
                            
                        if self.prefs['zoom mode'] == 1:
                            # Smart scaling, rotated 0 or 180 degrees.
                            if (self.prefs['smart double page scaling'] and
                                1.0 * width / x < 1.0 * height / y and
                                self.prefs['rotation'] in [0, 2]):
                                if pixbuf.get_height() > pixbuf2.get_height():
                                    width1 = y * pixbuf.get_width() / height
                                    height1 = y
                                    if (pixbuf2.get_width() > x - width1 or
                                        pixbuf2.get_height() > y or
                                        self.prefs['stretch'] == 1):
                                        if (1.0 * pixbuf2.get_width() /
                                            (x - width1) >
                                            1.0 * pixbuf2.get_height() / y):
                                            width2 = x - width1
                                            height2 = \
                                                pixbuf2.get_height() * \
                                                (x - width1) / \
                                                pixbuf2.get_width()
                                        else:
                                            width2 = \
                                                pixbuf2.get_width() * y / \
                                                pixbuf2.get_height()
                                            height2 = y
                                else:
                                    width2 = y * pixbuf2.get_width() / height
                                    height2 = \
                                        y * pixbuf2.get_height() / height
                                    if (pixbuf.get_width() > x - width2 or
                                        pixbuf.get_height() > y or
                                        self.prefs['stretch'] == 1):
                                        if (1.0 * pixbuf.get_width() /
                                            (x - width2) >
                                            1.0 * pixbuf.get_height() / y):
                                            width1 = x - width2
                                            height1 = \
                                                pixbuf.get_height() * \
                                                (x - width2) / \
                                                pixbuf.get_width()
                                        else:
                                            width1 = \
                                                pixbuf.get_width() * y / \
                                                pixbuf.get_height()
                                            height1 = y
                            
                            # Smart scaling, rotated 90 or 270 degrees.
                            elif (self.prefs['smart double page scaling'] and
                                1.0 * width / x > 1.0 * height / y and
                                self.prefs['rotation'] in [1, 3]):
                                if pixbuf.get_width() > pixbuf2.get_width():
                                    width1 = x
                                    height1 = \
                                        self.image1_width * x / \
                                        self.image1_height
                                    if (self.image2_width > x - height1 or
                                        self.image2_height > y or
                                        self.prefs['stretch'] == 1):
                                        if (1.0 * self.image2_width /
                                            (y - height1) >
                                            1.0 * self.image2_height / x):
                                            width2 = \
                                                self.image2_height * \
                                                (y - height1) / \
                                                self.image2_width
                                            height2 = y - height1
                                        else:
                                            width2 = x
                                            height2 = \
                                                self.image2_width * x / \
                                                self.image2_height
                                else:
                                    width2 = x
                                    height2 = \
                                        self.image2_width * x / \
                                        self.image2_height
                                    if (self.image1_width > x - height2 or
                                        self.image1_height > y or
                                        self.prefs['stretch'] == 1):
                                        if (1.0 * self.image1_width /
                                            (y - height2) >
                                            1.0 * self.image1_height / x):
                                            width1 = \
                                                self.image1_height * \
                                                (y - height2) / \
                                                self.image1_width
                                            height1 = y - height2
                                        else:
                                            width1 = x
                                            height1 = \
                                            self.image1_width * x / \
                                            self.image1_height
                            
                            # Fit-to-screen mode, no smart scaling.
                            else:
                                if 1.0 * width / x > 1.0 * height / y:
                                    width1 = x * pixbuf.get_width() / width
                                    height1 = x * pixbuf.get_height() / width
                                    width2 = x * pixbuf2.get_width() / width
                                    height2 = x * pixbuf2.get_height() / width
                                else:
                                    width1 = y * pixbuf.get_width() / height
                                    height1 = y * pixbuf.get_height() / height
                                    width2 = y * pixbuf2.get_width() / height
                                    height2 = \
                                        y * pixbuf2.get_height() / height
                        
                        elif self.prefs['zoom mode'] == 2:
                            width1 = x * pixbuf.get_width() / width
                            height1 = x * pixbuf.get_height() / width
                            width2 = x * pixbuf2.get_width() / width
                            height2 = x * pixbuf2.get_height() / width
                            
                        elif self.prefs['zoom mode'] == 3:
                            width1 = y * pixbuf.get_width() / height
                            height1 = y * pixbuf.get_height() / height
                            width2 = y * pixbuf2.get_width() / height
                            height2 = \
                                y * pixbuf2.get_height() / height
                            
                        # Just scale to the current zoom level.
                        else:
                            width1 = \
                                int(pixbuf.get_width() * \
                                self.prefs['zoom scale'] / 100)
                            height1 = \
                                int(pixbuf.get_height() * \
                                self.prefs['zoom scale'] / 100)
                            width2 = \
                                int(pixbuf2.get_width() * \
                                self.prefs['zoom scale'] / 100)
                            height2 = \
                                int(pixbuf2.get_height() * \
                                self.prefs['zoom scale'] / 100)
                        
                        # At least one pixel big, please!
                        if width1 < 1:
                            width1 = 1
                        if height1 < 1:
                            height1 = 1
                        if width2 < 1:
                            width2 = 1
                        if height2 < 1:
                            height2 = 1
                        
                        pixbuf = \
                            pixbuf.scale_simple(width1, height1,
                            self.prefs['interp type'])
                        pixbuf2 = \
                            pixbuf2.scale_simple(width2, height2,
                            self.prefs['interp type'])
                    x = temp_x
                    y = temp_y
                    
                    # =======================================================
                    # Switch position of the images if in "manga mode".
                    # =======================================================
                    if self.prefs['manga'] == 1:
                        self.image_box.reorder_child(self.image, -1)
                    else:
                        self.image_box.reorder_child(self.image, 0)
                    
                    # =======================================================
                    # Convert image data to a PIL objects and perform
                    # transformations on them. Then we convert them back to
                    # GTK pixbufs.
                    # =======================================================
                    if (self.prefs['rotation'] != 0 or
                        self.prefs['flip horiz'] or
                        self.prefs['flip vert'] or
                        self.prefs['contrast'] != 1.0 or
                        self.prefs['sharpness'] != 1.0 or 
                        self.prefs['saturation'] != 1.0 or
                        self.prefs['brightness'] != 1.0 or
                        self.prefs['autocontrast']):
                        assert(pixbuf.get_colorspace() ==
                            gtk.gdk.COLORSPACE_RGB)
                        assert(pixbuf2.get_colorspace() ==
                            gtk.gdk.COLORSPACE_RGB)
                        dimensions = pixbuf.get_width(), pixbuf.get_height()
                        dimensions2 = \
                            pixbuf2.get_width(), pixbuf2.get_height()
                        stride = pixbuf.get_rowstride()
                        stride2 = pixbuf2.get_rowstride()
                        pixels = pixbuf.get_pixels()
                        pixels2 = pixbuf2.get_pixels()
                        mode = pixbuf.get_has_alpha() and 'RGBA' or 'RGB'
                        mode2 = pixbuf2.get_has_alpha() and 'RGBA' or 'RGB'
                        pil_image = \
                            Image.frombuffer(mode, dimensions, pixels, 'raw',
                            mode, stride, 1)
                        pil_image2 = \
                            Image.frombuffer(mode2, dimensions2, pixels2,
                            'raw', mode2, stride2, 1)
                        
                        if self.prefs['rotation'] == 1:
                            pil_image = pil_image.transpose(Image.ROTATE_270)
                            pil_image2 = \
                                pil_image2.transpose(Image.ROTATE_270)
                        elif self.prefs['rotation'] == 2:
                            pil_image = pil_image.transpose(Image.ROTATE_180)
                            pil_image2 = \
                                pil_image2.transpose(Image.ROTATE_180)
                        elif self.prefs['rotation'] == 3:
                            pil_image = pil_image.transpose(Image.ROTATE_90)
                            pil_image2 = \
                                pil_image2.transpose(Image.ROTATE_90)
                        
                        if self.prefs['flip horiz']:
                            pil_image = \
                                pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                            pil_image2 = \
                                pil_image2.transpose(Image.FLIP_LEFT_RIGHT)
                        if self.prefs['flip vert']:
                            pil_image = \
                                pil_image.transpose(Image.FLIP_TOP_BOTTOM)
                            pil_image2 = \
                                pil_image2.transpose(Image.FLIP_TOP_BOTTOM)
                        
                        if self.prefs['autocontrast'] and mode == 'RGB':
                            pil_image = \
                                ImageOps.autocontrast(pil_image, cutoff=1)
                        elif self.prefs['contrast'] != 1.0:
                            pil_image = \
                                ImageEnhance.Contrast(pil_image).enhance(
                                self.prefs['contrast'])
                        if self.prefs['autocontrast'] and mode2 == 'RGB':
                            pil_image2 = \
                                ImageOps.autocontrast(pil_image2, cutoff=1)
                        elif self.prefs['contrast'] != 1.0:
                            pil_image2 = \
                                ImageEnhance.Contrast(pil_image2).enhance(
                                self.prefs['contrast'])
                        if self.prefs['saturation'] != 1.0:
                            pil_image = \
                                ImageEnhance.Color(pil_image).enhance(
                                self.prefs['saturation'])
                            pil_image2 = \
                                ImageEnhance.Color(pil_image2).enhance(
                                self.prefs['saturation'])
                        if self.prefs['brightness'] != 1.0:
                            pil_image = \
                                ImageEnhance.Brightness(pil_image).enhance(
                                self.prefs['brightness'])
                            pil_image2 = \
                                ImageEnhance.Brightness(pil_image2).enhance(
                                self.prefs['brightness'])
                        if self.prefs['sharpness'] != 1.0:
                            pil_image = \
                                ImageEnhance.Sharpness(pil_image).enhance(
                                self.prefs['sharpness'])
                            pil_image2 = \
                                ImageEnhance.Sharpness(pil_image2).enhance(
                                self.prefs['sharpness']) 

                        imagestr = pil_image.tostring()
                        imagestr2 = pil_image2.tostring()
                        IS_RGBA = pil_image.mode == 'RGBA'
                        IS_RGBA2 = pil_image2.mode == 'RGBA'
                        pixbuf = \
                            gtk.gdk.pixbuf_new_from_data(imagestr,
                            gtk.gdk.COLORSPACE_RGB, IS_RGBA, 8,
                            pil_image.size[0], pil_image.size[1],
                            (IS_RGBA and 4 or 3) * pil_image.size[0])
                        pixbuf2 = \
                            gtk.gdk.pixbuf_new_from_data(imagestr2,
                            gtk.gdk.COLORSPACE_RGB, IS_RGBA2, 8,
                            pil_image2.size[0], pil_image2.size[1],
                            (IS_RGBA2 and 4 or 3) * pil_image2.size[0])
                    
                    self.image1_scaled_width = pixbuf.get_width()
                    self.image1_scaled_height = pixbuf.get_height()
                    self.image2_scaled_width = pixbuf2.get_width()
                    self.image2_scaled_height = pixbuf2.get_height()
                    
                    if pixbuf.get_height() > pixbuf2.get_height():
                        height = pixbuf.get_height()
                    else:
                        height = pixbuf2.get_height()
                    
                    # =======================================================
                    # Store the width and height of the scaled images. Resize
                    # and move the display area accordingly to these image
                    # dimensions.
                    # =======================================================
                    x_move = \
                        (x - (pixbuf.get_width() + pixbuf2.get_width())) / 2
                    y_move = (y - height) / 2
                    
                    if x_move < 0:
                        x_move = 0
                    if y_move < 0:
                        y_move = 0
                    
                    self.layout.move(self.image_box, x_move, y_move)
                    self.layout.set_size(pixbuf.get_width() +
                        pixbuf2.get_width(), height)
                    
                    if self.colour_adjust_dialog_displayed:
                        self.colour_adjust_draw_histogram(pixbuf)

                    # =======================================================
                    # Create pixmaps, draw the pixbufs on them and then
                    # convert them back to pixbufs. It is an *ugly* hack, but
                    # it gives us full depth dithering of the images. Then we
                    # display the resulting images.
                    # =======================================================
                    pixmap = \
                        gtk.gdk.Pixmap(self.window.window,
                        self.image1_scaled_width, self.image1_scaled_height,
                        -1)
                    if pixbuf.get_has_alpha():
                        pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                            self.image1_scaled_width,
                            self.image1_scaled_height)
                    pixmap.draw_pixbuf(None, pixbuf, 0, 0, 0, 0, -1, -1,
                        gtk.gdk.RGB_DITHER_MAX, 0, 0)
                    self.image.set_from_pixmap(pixmap, None)
                    
                    pixmap = \
                        gtk.gdk.Pixmap(self.window.window,
                        self.image2_scaled_width, self.image2_scaled_height,
                        -1)
                    if pixbuf2.get_has_alpha():
                        pixmap.draw_rectangle(self.gdk_gc, True, 0, 0,
                            self.image2_scaled_width,
                            self.image2_scaled_height)
                    pixmap.draw_pixbuf(None, pixbuf2, 0, 0, 0, 0, -1, -1,
                        gtk.gdk.RGB_DITHER_MAX, 0, 0)
                    self.image2.set_from_pixmap(pixmap, None)
                    
                    self.image.show()
                    self.image2.show()
                    
                    # =======================================================
                    # Set window title and statusbar message.
                    # =======================================================
                    if self.archive_type != '':
                        self.window.set_title(self.to_unicode(
                            os.path.basename(
                            self.path) + ' --- [' +
                            str(self.file_number + 1) + ',' +
                            str(self.file_number + 2) + ' / ' +
                            str(len(self.file)) + ']'))
                        self.statusbar.push(0, self.to_unicode(('[' +
                            str(self.file_number + 1) + ',' +
                            str(self.file_number + 2) + ' / ' +
                            str(len(self.file)) + ']    ---    ' +
                            os.path.basename(self.path) + '    ---    ' +
                            str(self.image1_width) + 'x' +
                            str(self.image1_height) + ' , ' +
                            str(self.image2_width) + 'x' +
                            str(self.image2_height) + '    ---    ' +
                            str('%.1f' % (100.0 * self.image1_scaled_height /
                            self.image1_height)) + '%' + ' , ' +
                            str('%.1f' % (100.0 * self.image2_scaled_height /
                            self.image2_height)) + '%')))
                    else:
                        self.window.set_title(self.to_unicode(
                            os.path.basename(
                            os.path.dirname(self.path)) + ' --- [' +
                            str(self.file_number + 1) + ',' +
                            str(self.file_number + 2) + ' / ' +
                            str(len(self.file)) + ']'))
                        self.statusbar.push(0, self.to_unicode(('[' +
                            str(self.file_number + 1) + ',' +
                            str(self.file_number + 2) + ' / ' +
                            str(len(self.file)) + ']    ---    ' +
                            os.path.basename(os.path.dirname(self.path) ) +
                            '    ---    ' + str(self.image1_width) + 'x' +
                            str(self.image1_height) + ' , ' +
                            str(self.image2_width) + 'x' +
                            str(self.image2_height) + '    ---    ' +
                            str('%.1f' % (100.0 * self.image1_scaled_height /
                            self.image1_height)) + '%' + ' , ' +
                            str('%.1f' % (100.0 * self.image2_scaled_height /
                            self.image2_height)) + '%')))
            
            # =======================================================
            # No file loaded, lets happily display "Comix" as the
            # window title and whistle a merry tune while we wait for
            # something better to do.
            # =======================================================
            else:
                self.window.set_title("Comix")
                self.image.hide()
                self.image2.hide()
                self.layout.move(self.comix_image, 
                    max(0, self.main_layout_x_size // 2 - 150),
                    max(0, self.main_layout_y_size // 2 - 150))
                
                # Unless there was an error opening a file we blank out
                # the statusbar.
                if not self.filetype_error:
                    self.statusbar.push(0, '')
        
        # =======================================================
        # Set some new values for the scrollbars.
        # =======================================================
        self.vadjust_upper = \
            self.vadjust.upper - self.window.get_size()[1] + \
            self.hscroll_size + self.status_size + self.tool_size + \
            self.menu_size
        self.hadjust_upper = \
            self.hadjust.upper - self.window.get_size()[0] + \
            self.vscroll_size + self.thumb_vscroll_size + \
            self.thumb_size
        self.thumb_vadjust_upper = \
            self.thumb_vadjust.upper - self.window.get_size()[1] + \
            self.status_size + self.tool_size + self.menu_size
        
        self.set_cursor_type('normal')
        
        # =======================================================
        # Update thumbnail selection(s).
        # =======================================================
        if (self.file_exists and self.number_of_thumbs_loaded ==
            len(self.file) and not self.show_comments and
            self.prefs['show thumbnails'] and self.change_thumb_selection):
            
            self.thumb_tree_view.get_selection().unselect_all()
            
            if (self.prefs['double page'] and
                self.file_number != len(self.file) - 1):
                self.thumb_tree_view.get_selection().select_range(
                    self.file_number, self.file_number + 1)
            else:
                self.thumb_tree_view.get_selection().select_path(
                    self.file_number)
            
            if self.change_thumb_selection:
                lower = 0
                upper = 0
                if (self.prefs['double page'] and self.file_number !=
                    len(self.file) - 1):
                    for i in range(self.file_number):
                        lower = lower + self.thumb_heights[i]
                    upper = \
                        lower + self.thumb_heights[self.file_number] + \
                        self.thumb_heights[self.file_number + 1]
                else:
                    for i in range(self.file_number):
                        lower = lower + self.thumb_heights[i]
                    upper = lower + self.thumb_heights[self.file_number]
                if (self.thumb_vadjust.get_value() > lower or
                    self.thumb_vadjust.get_value() <
                    upper - y + self.hscroll_size):
                    if (lower + (upper - lower - y + self.hscroll_size) / 2 >
                        self.thumb_vadjust_upper):
                        self.thumb_vadjust.set_value(self.thumb_vadjust_upper)
                    else:
                        self.thumb_vadjust.set_value(lower + (
                            upper - lower - y + self.hscroll_size) / 2)
            
            self.change_thumb_selection = 0
        
        old_file_number_cache_temp = self.old_file_number
        self.old_file_number = self.file_number
        
        # =======================================================
        # Set the scrollbars back to default unless we just
        # reloaded the same image.
        # =======================================================
        if self.change_scroll_adjustment:
            self.vadjust.set_value(0)
            if self.prefs['manga'] and not self.show_comments:
                self.hadjust.set_value(self.hadjust_upper)
            else:
                self.hadjust.set_value(0)
            self.change_scroll_adjustment = 0
        
        # =======================================================
        # Display some text when running a slideshow
        # =======================================================
        if self.slideshow_started:
            self.put_slideshow_label(20)

        # =======================================================
        # Update all GUI changes now except when resizing the
        # image (looks choppy then.)
        # =======================================================
        if not self.resize_event:
            while gtk.events_pending():
                gtk.main_iteration(False)
        
        # =======================================================
        # Cache page(s).
        # =======================================================
        if (self.file_exists and self.prefs['cache'] and
            not self.show_comments and not backwards_caching):
            
            # Cache in double page mode.
            if (self.file_number + 3 < len(self.file) and
                self.prefs['double page'] and (self.file_number !=
                old_file_number_cache_temp or
                len(self.number_of_cached) != 2)):
                try:
                    self.cached_pixbuf = \
                        gtk.gdk.pixbuf_new_from_file(
                        self.file[self.file_number + 2])
                except:
                    self.cached_pixbuf = \
                        self.about_dialog.render_icon(
                        gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                try:
                    self.cached_pixbuf2 = \
                        gtk.gdk.pixbuf_new_from_file(
                        self.file[self.file_number + 3])
                except:
                    self.cached_pixbuf2 = \
                        self.about_dialog.render_icon(
                        gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                self.number_of_cached = \
                    [self.file_number + 2, self.file_number + 3]
            
            # Cache for last page in double page mode.
            elif (self.file_number + 2 < len(self.file) and
                self.prefs['double page'] and (self.file_number !=
                old_file_number_cache_temp or
                len(self.number_of_cached) != 2)):
                try:
                    self.cached_pixbuf = \
                        gtk.gdk.pixbuf_new_from_file(
                        self.file[self.file_number + 2])
                except:
                    self.cached_pixbuf = \
                        self.about_dialog.render_icon(
                        gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                self.number_of_cached = [self.file_number + 2]
            
            # Cache for single page mode.
            elif (self.file_number + 1 < len(self.file) and
                not self.prefs['double page'] and self.file_number !=
                old_file_number_cache_temp):
                try:
                    self.cached_pixbuf = \
                        gtk.gdk.pixbuf_new_from_file(
                        self.file[self.file_number + 1])
                except:
                    self.cached_pixbuf = \
                        self.about_dialog.render_icon(
                        gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
                self.number_of_cached = [self.file_number + 1]
        
        # =======================================================
        # Delete some big stuff and let the garbage collector
        # remove it. We don't want to store multiple big pixbufs
        # on the garbage heap before the garbage collector
        # thinks it is fit to remove them.
        # =======================================================
        try:
            del pixbuf
        except:
            pass
        try:
            del pixbuf2
        except:
            pass
        
        if not self.prefs['cache']:
            self.number_of_cached = [-1]
            try:
                del self.cached_pixbuf
            except:
                pass
            try:
                del self.cached_pixbuf2
            except:
                pass
        
        gc.collect()
    
    def __init__(self):
        
        ''' Loads preference and bookmarks settings from disk, creates all
        windows and widgets and does some other startup tasks. '''
        
        # =======================================================
        # This effectively deactivates the refresh_image() method
        # during  most of __init__(). It would otherwise
        # be called repeatedly while setting up GUI elements.
        # This saves about 0.2 - 0.4 s in startup time on a
        # regular system.
        # =======================================================
        self.refresh_activated = False
        
        # =======================================================
        # Eliminate symbolic links so that we know where to look
        # for icons etc.
        # =======================================================
        sys.argv[0] = os.path.realpath(sys.argv[0])
        self.bin_dir = os.path.dirname(sys.argv[0])

        # =======================================================
        # Use gettext translations as found in the source dir,
        # otherwise based on the install path.
        # =======================================================
        if os.path.isdir(os.path.dirname(os.path.dirname(sys.argv[0])) +
            '/messages'):
            gettext.install('comix', os.path.dirname(os.path.dirname(
                sys.argv[0])) + '/messages', unicode=True)
        else:
            gettext.install('comix', os.path.dirname(os.path.dirname(
                sys.argv[0])) + '/share/locale', unicode=True)
        
        # =======================================================
        # Create the temporary directory used in this Comix session.
        # =======================================================
        self.base_dir = tempfile.mkdtemp(prefix="comix.", suffix="/")
            
        # =======================================================
        # Determine if rar/unrar exists.
        # =======================================================
        self.rar = ''
        for path in os.getenv('PATH').split(':') + ['./']:
            if os.path.isfile(os.path.join(path, 'unrar')):
                self.rar = 'unrar'
                break
            elif os.path.isfile(os.path.join(path, 'rar')):
                self.rar = 'rar'
                break
        if not self.rar:
            print 'Could not find the `rar` or `unrar` executables.'
            print 'RAR (.cbr) files will not be readable.'
            print

        # =======================================================
        # Determine if jpegtran exists.
        # =======================================================
        self.jpegtran = ''
        for path in os.getenv('PATH').split(':') + ['./']:
            if os.path.isfile(os.path.join(path, 'jpegtran')):
                self.jpegtran = 'jpegtran'
                break
        if not self.jpegtran:
            print 'Could not find the `jpegtran` executable.'
            print 'Lossless JPEG rotation will not be available.'
            print
        
        # =======================================================
        # Set the window icon, if an icon is found.
        # =======================================================
        if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(
            sys.argv[0])), 'images/logo/comix.png')):
            icon_path = \
                os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])),
                'images/logo/comix.png')
        else:
            for prefix in [os.path.dirname(os.path.dirname(sys.argv[0])),
                '/usr', '/usr/local', '/usr/X11R6']:
                icon_path = os.path.join(prefix, 'share/pixmaps/comix.png')
                if os.path.isfile(icon_path):
                    break
        try:
            icon = gtk.gdk.pixbuf_new_from_file(icon_path)
            gtk.window_set_default_icon(icon)
        except:
            pass
        
        # =======================================================
        # Set icons for the transform action, if found.
        # =======================================================
        if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(
            sys.argv[0])), 'images/lens.png')):
            icon_path = \
                os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])),
                'images')
        else:
            for prefix in [os.path.dirname(os.path.dirname(sys.argv[0])),
                '/usr', '/usr/local', '/usr/X11R6']:
                if os.path.isfile(os.path.join(prefix,
                    'share/pixmaps/comix/lens.png')): # Try one
                    icon_path = os.path.join(prefix, 'share/pixmaps/comix')
                    break
        try:
            factory = gtk.IconFactory()
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'flip-horizontal.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-flip-horiz', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'flip-vertical.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-flip-vert', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'rotate-180.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-rotate-180', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'rotate-270.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-rotate-270', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'rotate-90.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-rotate-90', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'rotate-90-jpeg.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-rotate-90-jpeg', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'rotate-270-jpeg.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-rotate-270-jpeg', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'flip-horizontal-jpeg.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-flip-horizontal-jpeg', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'flip-vertical-jpeg.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-flip-vertical-jpeg', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-library.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-library', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-library-add.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-library-add', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-slideshow.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-slideshow', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-bookmarks.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-bookmarks', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-desaturate.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-desaturate', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-file-operations.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-file-operations', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-thumbnails.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-thumbnails', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-view.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-view', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-zoom.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-zoom', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-transform.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-transform', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-recent-files.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-recent-files', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-edit-bookmarks.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-edit-bookmarks', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-toolbars.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-toolbars', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'silk-colour-adjust.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-colour-adjust', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'lens.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-lens', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'double-page.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-double-page', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'manga.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-manga', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'fitscreen.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-fitscreen', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'fitwidth.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-fitwidth', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'fitheight.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-fitheight', iconset)
            pixbuf = \
                gtk.gdk.pixbuf_new_from_file(
                os.path.join(icon_path, 'fitnone.png'))
            iconset = gtk.IconSet(pixbuf)
            factory.add('comix-fitnone', iconset)
            factory.add_default()
        except:
            print 'Could not load icons.'
            print
        
        # =======================================================
        # Parse preferences_data file.
        # =======================================================
        if os.path.isfile(os.path.join(os.environ['HOME'],
            '.comix/preferences_data')):
            try:
                config = \
                    open(os.path.join(os.environ['HOME'],
                    '.comix/preferences_data'))
                version = cPickle.load(config) # For future use.
                self.prefs.update(cPickle.load(config))
                config.close()
            except:
                pass
        
        # =======================================================
        # Parse bookmarks file.
        # =======================================================
        if os.path.isfile(os.path.join(os.environ['HOME'],
            '.comix/bookmarks_data')):
            try:
                bookmarks = \
                    open(os.path.join(os.environ['HOME'],
                    '.comix/bookmarks_data'))
                self.bookmarks = cPickle.load(bookmarks)
                self.bookmark_numbers = cPickle.load(bookmarks)
                bookmarks.close()
            except:
                self.bookmarks = []
                self.bookmark_numbers = []
        
        # =======================================================
        # Parse recent_files file.
        # =======================================================
        if os.path.exists(os.path.join(os.environ['HOME'],
            '.comix/recent_files_data')):
            try:
                recent_files = \
                    open(os.path.join(os.environ['HOME'],
                    '.comix/recent_files_data'))
                self.recent_files = cPickle.load(recent_files)
                recent_files.close()
            except:
                self.recent_files = []
        
        # =======================================================
        # Create windows and dialogs.
        # =======================================================
        self.create_main_window()
        self.create_library_window()
        self.create_open_dialog()
        self.create_preferences_dialog()
        self.create_properties_dialog()
        self.create_go_to_page_dialog()
        self.create_bookmark_dialog()
        #self.create_about_dialog()
        self.about_dialog = about.Aboutdialog(self.window)
        self.create_convert_dialog()
        self.create_permission_dialog()
        self.create_thumbnail_dialog()
        self.create_progress_dialog()
        self.create_lib_progress_dialog()
        self.create_extract_dialog()
        self.create_are_you_sure_dialog()
        self.create_colour_adjust_dialog()
        
        # =======================================================
        # Apply event masks and connect event handlers.
        # =======================================================
        self.layout.drag_dest_set(gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_DROP, [("text/uri-list", 0, 80)],
            gtk.gdk.ACTION_DEFAULT)
        self.lib_layout.drag_dest_set(gtk.DEST_DEFAULT_HIGHLIGHT |
            gtk.DEST_DEFAULT_DROP, [("text/uri-list", 0, 81)],
            gtk.gdk.ACTION_DEFAULT)
        self.layout.set_events(gtk.gdk.BUTTON1_MOTION_MASK |
            gtk.gdk.BUTTON2_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK)
        
        self.window.connect('delete_event', self.close_application)
        self.window.connect('key_press_event', self.key_press_event)
        self.window.connect('button_press_event',
            self.mouse_button_press_event)
        self.window.connect('configure_event', self.area_resize_event)
        self.lib_window.connect('delete_event', self.library_close)
        self.lib_window.connect('configure_event',
            self.library_area_resize_event)
        self.lib_layout.connect('scroll_event', self.lib_scroll_wheel_event)
        self.lib_layout.connect('drag_motion', self.drag_motion)
        self.lib_layout.connect('drag_data_received', self.lib_drag_n_drop)
        self.scroll_wheel_event_id = \
            self.layout.connect('scroll_event', self.scroll_wheel_event)
        self.thumb_layout.connect('scroll_event',
            self.thumb_scroll_wheel_event)
        self.preferences_dialog.connect('delete_event',
            self.preferences_dialog_close)
        self.file_select.connect('delete_event', self.file_chooser_cancel)
        self.file_select.connect('selection-changed',
            self.file_chooser_change_preview)
        self.permission_dialog.connect('response',
            self.wrong_permissions_dialog_close)
        self.permission_dialog.connect('delete_event',
            self.wrong_permissions_dialog_close)
        self.properties_dialog.connect('response',
            self.properties_dialog_close)
        self.properties_dialog.connect('delete_event',
            self.properties_dialog_close)
        self.about_dialog.connect('response', self.about_dialog_close)
        self.about_dialog.connect('delete_event', self.about_dialog_close)
        self.thumbnail_dialog.connect('response',
            self.thumbnail_maintenance_dialog_close)
        self.thumbnail_dialog.connect('delete_event',
            self.thumbnail_maintenance_dialog_close)
        self.progress_dialog.connect('response',
            self.thumbnail_maintenance_dialog_progress_close)
        self.progress_dialog.connect('delete_event',
            self.thumbnail_maintenance_dialog_progress_close)
        self.lib_progress_dialog.connect('response',
            self.library_progress_dialog_close)
        self.lib_progress_dialog.connect('delete_event',
            self.library_progress_dialog_close)
        self.go_to_page_dialog.connect('response',
            self.go_to_page_dialog_save_and_close)
        self.go_to_page_dialog.connect('delete_event',
            self.go_to_page_dialog_close)
        self.bookmark_dialog.connect('response',
            self.bookmark_dialog_button_press)
        self.bookmark_dialog.connect('delete_event',
            self.bookmark_dialog_close)
        self.select_default_folder_dialog.connect('delete_event',
            self.default_folder_chooser_dialog_close)
        self.convert_dialog.connect('response',
            self.convert_dialog_save_and_close)
        self.convert_dialog.connect('delete_event', self.convert_dialog_close)
        self.convert_tree.get_selection().connect('changed',
            self.convert_dialog_change_type)
        self.layout.connect('drag_motion', self.drag_motion)
        self.layout.connect('drag_data_received', self.drag_n_drop)
        self.layout.connect('motion_notify_event', self.motion_event)
        self.button_release_event_id = \
            self.layout.connect('button_release_event',
            self.mouse_button_release_event)
        self.colour_adjust_dialog.connect('response',
            self.colour_adjust_response)
        self.colour_adjust_dialog.connect('delete_event',
            self.colour_adjust_close)
        
        # =======================================================
        # Create actions for the menus.
        # =======================================================
        self.actiongroup.add_actions([
            ('Next', gtk.STOCK_GO_FORWARD, _('_Next page'), 'Page_Down',
                None, self.next_page),
            ('Previous', gtk.STOCK_GO_BACK, _('_Previous page'), 'Page_Up',
                None, self.previous_page),
            ('First', gtk.STOCK_GOTO_FIRST, _('_First page'), 'Home',
                None, self.first_page),
            ('Last',gtk.STOCK_GOTO_LAST, _('_Last page'), 'End',
                None, self.last_page),
            ('Go', gtk.STOCK_JUMP_TO, _('_Go to page...'), 'g',
                None, self.go_to_page_dialog_open),
            ('Zoom', 'comix-zoom', _('Manual _Zoom')),
            ('Zin', gtk.STOCK_ZOOM_IN, _('_Zoom in'), 'KP_Add',
                None, self.zoom_in),
            ('Zout', gtk.STOCK_ZOOM_OUT, _('Zoom _out'), 'KP_Subtract',
                None, self.zoom_out),
            ('Zoriginal', gtk.STOCK_ZOOM_100, _('_Normal size'), 'n',
                None, self.zoom_original),
            ('Zwidth', gtk.STOCK_ZOOM_FIT, _('Fit _width'), '<Control>w',
                None, self.zoom_width),
            ('Zheight', gtk.STOCK_ZOOM_FIT, _('Fit _height'), '<Control>h',
                None, self.zoom_height),
            ('Zfit', gtk.STOCK_ZOOM_FIT, _('_Best fit'), 'b',
                None, self.zoom_fit),
            ('Save_book', gtk.STOCK_ADD, _('_Add bookmark'), '<Control>d',
                None, self.add_menu_thumb),
            ('Clear_book', gtk.STOCK_CLEAR, _('Clear bookmarks'), '',
                None, self.clear_bookmarks),
            ('Bookmark_manager', 'comix-edit-bookmarks',
                _('_Edit bookmarks...'), '<Control>b', None,
                self.bookmark_dialog_open),
            ('Options', gtk.STOCK_PREFERENCES, _('Pr_eferences'), '',
                None, self.preferences_dialog_open),
            ('About', gtk.STOCK_ABOUT, _('_About'), '',
                None, self.about_dialog_open),
            ('Thumbnail_dialog', 'comix-thumbnails',
                _('_Manage thumbnails...'),
                '', None, self.thumbnail_maintenance_dialog_open),
            ('File', gtk.STOCK_PROPERTIES, _('Proper_ties'), '<Alt>Return',
                None, self.properties_dialog_open),
            ('Comments', gtk.STOCK_INFO, _('View _comments'), 'c',
                None, self.comment_switch),
            ('Open', gtk.STOCK_OPEN, _('_Open...'), '<Control>o',
                None, self.file_chooser_open),
            ('Recent', 'comix-recent-files', _('_Recent files')),
            ('Clear_recent', gtk.STOCK_CLEAR, _('Clear recent files'), '',
                None, self.clear_recent_files),
            ('Library', 'comix-library', _('Open _library...'), '<Control>l',
                None, self.library_load_files),
            ('Add_to_library', 'comix-library-add', _('_Add to library'), '',
                None, self.library_add_helper),
            ('Convert', gtk.STOCK_CONVERT, _('Con_vert...'), '',
                None, self.convert_dialog_open),
            ('Extract', gtk.STOCK_SAVE_AS, _('E_xtract image...'), '',
                None, self.extract_image_open),
            ('Close', gtk.STOCK_CLOSE, _('_Close'), '<Control>w',
                None, self.close_file),
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<Control>q',
                None, self.close_application),
            ('colour_adjust', 'comix-colour-adjust', _('_Adjust colour...'),
                'j', None, self.colour_adjust_open),
            ('Slideshow', 'comix-slideshow', _('Slideshow'), '<Control>S', 
                None, self.start_slideshow),
            ('Delete', gtk.STOCK_DELETE, _('Delete image...'), None,
                None, self.delete_file),
            ('file_rot_90', 'comix-rotate-90-jpeg',
                _('CW lossless JPEG rotation...'), '<Alt>r',
                None, self.rotate_file_90),
            ('file_rot_270', 'comix-rotate-270-jpeg',
                _('CCW lossless JPEG rotation...'),
                '<Alt><Shift>r', None, self.rotate_file_270),
            ('file_flip_horiz', 'comix-flip-horizontal-jpeg',
                _('Horizontal lossless JPEG flip...'),
                None, None, self.flip_file_horizontal),
            ('file_flip_vert', 'comix-flip-vertical-jpeg',
                _('Vertical lossless JPEG flip...'),
                None, None, self.flip_file_vertical),
            ('file_desaturate', 'comix-desaturate',
                _('Convert JPEG to greyscale...'),
                None, None, self.desaturate_file),
            ('menu_bookmarks', None, _('_Bookmarks')),
            ('menu_toolbars', 'comix-toolbars', _('_Toolbars')),
            ('menu_bookmarks_popup', 'comix-bookmarks', _('_Bookmarks')),
            ('menu_edit', None, _('_Edit')),
            ('menu_file_operations', 'comix-file-operations',
                _('File o_perations')),
            ('menu_file', None, _('_File')),
            ('menu_view', None, _('_View')),
            ('menu_view_popup', 'comix-view', _('_View')),
            ('menu_go', None, _('_Go')),
            ('menu_go_popup', gtk.STOCK_GO_FORWARD, _('_Go')),
            ('menu_help', None, _('_Help')),
            ('Transform', 'comix-transform', _('_Transform')),
            ('Rotate_90', 'comix-rotate-90', _('_Rotate 90 degrees CW'), 'r',
                None, self.rotate_90),
            ('Rotate_180','comix-rotate-180', _('Rotate 180 de_grees'), None,
                None, self.rotate_180),
            ('Rotate_270', 'comix-rotate-270', _('Rotat_e 90 degrees CCW'),
                '<Shift>r', None, self.rotate_270),
            ('Flip_horiz', 'comix-flip-horiz', _('Fli_p horizontally'), None,
                None, self.flip_horizontally),
            ('Flip_vert', 'comix-flip-vert', _('Flip _vertically'), None,
                None, self.flip_vertically)])
        self.actiongroup.add_toggle_actions([
            ('Fullscreen', None, _('_Fullscreen'), 'f',
                None, self.fullscreen_switch),
            ('Double', None, _('_Double page mode'), 'd',
                None, self.double_page_switch),
            ('Toolbar', None, _('_Toolbar'), None,
                None, self.toolbar_switch),
            ('Menubar', None, _('_Menubar'), None,
                None, self.menubar_switch),
            ('Statusbar', None, _('St_atusbar'), None,
                None, self.statusbar_switch),
            ('Scrollbars', None, _('S_crollbars'), None,
                None, self.scrollbars_switch),
            ('Thumbnails', None, _('Th_umbnails'), 'F9',
                None, self.thumbnail_switch),
            ('Hide_all', None, _('H_ide all'), 'i',
                None, self.hide_all_switch),
            ('manga_mode', None, _('_Manga mode'), 'm',
                None, self.manga_mode_switch),
            ('Keep_rotation', None, _('_Keep transformation'), 'k',
                None, self.keep_transformation_switch),
            ('Lens', None, _('Magnifying _lens'), 'z',
                None, self.lens_switch)])
        self.actiongroup.add_radio_actions([
            ('fit_manual_mode', None, _('Manual zoom mode'), 'a', None, 0),
            ('fit_screen_mode', None, _('Fit-to-_screen mode'), 's', None, 1),
            ('fit_width_mode', None, _('Fit _width mode'), 'w', None, 2),
            ('fit_height_mode', None, _('Fit _height mode'), 'h', None, 3)],
            0, self.zoom_mode_switch)
        
        # =======================================================
        # Create menus and initialize accelerators.
        # =======================================================
        self.create_menus()
        self.accelgroup = self.ui.get_accel_group()
        self.window.add_accel_group(self.accelgroup)
        
        # =======================================================
        # Set tooltips for some various widgets.
        # Yes, pygettext.py wants them all on single lines, really.
        # =======================================================
        self.tooltips.set_tip(self.button_fullscreen, _('Enter fullscreen mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_page, _('Enter double page mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_fit_manual_default, _('Enter manual zoom mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_fit_screen_default, _('Enter fit-to-screen mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_fit_width_default, _('Enter fit width mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_fit_height_default, _('Enter fit height mode automatically when Comix is started.'))
        self.tooltips.set_tip(self.button_stretch, _('Also scale images to a size that is larger than their original size in fit-to-screen mode, fit width mode and fit height mode.'))
        self.tooltips.set_tip(self.button_smart_scale, _('Scale the images independently when in double page mode and fit-to-screen mode. The smaller of the two images will scale up to fill any extra space that is given.'))
        self.tooltips.set_tip(self.button_comment, _('Automatically show any available comments when opening a new file.'))
        self.tooltips.set_tip(self.button_hide_bars, _('Automatically hide scrollbars, menubar, toolbar, statusbar and thumbnails when in fullscreen mode.'))
        self.tooltips.set_tip(self.button_cache_next, _('Cache the next page in the archive/directory to increase the perceived speed. This is generally recommended unless you are running low on RAM.'))
        self.tooltips.set_tip(self.button_scroll_horiz, _('Move the horizontal scrollbar instead of the vertical when using the scroll wheel at the top or the bottom of the page. The direction will be determined by whether you use manga mode or not.'))
        self.tooltips.set_tip(self.button_scroll_flips, _('Flip pages when scrolling "off the page" with the scroll wheel, as well as with the arrow keys, even when not in fit-to-screen mode. It takes three "steps" with the scroll wheel or arrow keys to trigger this behaviour.'))
        self.tooltips.set_tip(self.button_save_size, _('Save the position and the size of the window for the next time you start Comix.'))
        self.tooltips.set_tip(self.button_next_archive, _('Automatically open the next archive in the directory when scrolling past the last page of the current archive, and automatically open the previous archive in the directory when scrolling past the first page of the current archive.'))
        self.tooltips.set_tip(self.button_hide_cursor, _('Hide the cursor when in fullscreen mode.'))
        self.tooltips.set_tip(self.button_1, _('Set the image scaling method. The best choice is often "Tiles", it is quite quick and produces almost as good results as "Bilinear" or "Hyper".'))
        self.tooltips.set_tip(self.button_2, _('Set the image scaling method. The best choice is often "Tiles", it is quite quick and produces almost as good results as "Bilinear" or "Hyper".'))
        self.tooltips.set_tip(self.button_3, _('Set the image scaling method. The best choice is often "Tiles", it is quite quick and produces almost as good results as "Bilinear" or "Hyper".'))
        self.tooltips.set_tip(self.button_4, _('Set the image scaling method. The best choice is often "Tiles", it is quite quick and produces almost as good results as "Bilinear" or "Hyper".'))
        self.tooltips.set_tip(self.comment_extensions_entry, _('Treat files with the following extensions as comment files. Extensions should be separated by whitespaces. They are not case sensitive.'))
        self.tooltips.set_tip(self.button_smart_space, _('Use smart scrolling with the space key. Pressing the space key normally scrolls straight down one window height unless at the bottom of the page where it flips pages instead. When this option is set Comix automatically tries to follow the reading flow of the comic book. When pressing the space key it will not only scroll down but will also scroll horizontally to the edge of the page (left or right depending on whether you use manga mode). In double page mode it will go to the edge of the first page if it is in view, otherwise it will go to the edge of the second page. Also, in double page mode with this option, Comix will not flip pages unless at the bottom of the second page. At the bottom of the first page it will instead go to the top of the second page.'))
        self.tooltips.set_tip(self.button_thumb_scroll, _('Always hide the thumbnail scrollbar.'))
        self.tooltips.set_tip(self.button_open_last, _('Automatically open the last viewed page when Comix is started.'))
        self.tooltips.set_tip(self.button_latest_path, _('Automatically go to the same directory as last time when opening the "Open" dialog.'))
        self.tooltips.set_tip(self.button_default_path, _('Automatically go to this directory when opening the "Open" dialog.'))
        self.tooltips.set_tip(self.button_save_satcon, _('Automatically restore these values the next time Comix is started.'))
        self.tooltips.set_tip(self.button_show_pagenumber, _('Show the page number in the upper left corner of each thumbnail.'))
        self.tooltips.set_tip(self.button_autocontrast, _('Automatically adjust the contrast of the images so that the darkest pixel is completely black and the lightest pixel is completely white. This only works with images without an alpha channel.'))
        self.tooltips.set_tip(self.button_fake_double, _('The space key uses smart scrolling as if in double page mode even when in single page mode. This can be useful for comics with two scanned pages in each image. The pages are assumed to be of equal size'))
        self.tooltips.set_tip(self.button_lens_zoom, _('Adjust the lens magnification factor.'))
        self.tooltips.set_tip(self.button_lens_size, _('Set the lens width and height in pixels. A larger lens will use more CPU resources than a small one.'))
        self.tooltips.set_tip(self.button_lens_update, _('Set the maximum update frequency for the magnification lens in milliseconds. Setting the value too low can cause the lens to lag behind when moving the mouse quickly. Setting the value too high can cause the lens to appear choppy.'))
        self.tooltips.set_tip(self.button_cache_thumbs, _('Read and write thumbnails in the ~/.thumbnails directory as proposed by the freedesktop.org standard. With this preference set, Comix will use the thumbnails already stored there to speed up thumbnail loading. If there are no thumbnails, Comix will create them and save them there. This is a standard that many applications conform to, thumbnails created by other applications can be used by Comix and vice versa. If this preference is not set, Comix will create thumbnails on the fly every time a directory is opened.'))
        self.tooltips.set_tip(self.button_cache_arch_thumbs, _('Also use stored thumbnails for images in archives in a similiar way. Due to restrictions in the freedesktop.org standard, these thumbnails will be stored in ~/.comix and will only be used by Comix. If this preference is not set, Comix will create thumbnails on the fly every time an archive is opened.'))
        self.tooltips.set_tip(self.button_two_page_scans, _("Only display a single image in double page mode if the image consists of two pages. An image is assumed to consist of two pages if its width is greater than its height."))
        self.tooltips.set_tip(self.lib_search_box, _("Filter out archives with regular expressions."))
        self.tooltips.set_tip(self.button_reg_expr, _("Apply filters on full paths rather than filenames."))
        self.tooltips.set_tip(self.button_store_recent, _("Store a list of the 10 last opened files that can be accessed through the menus."))
        self.toolbutton_fitscreen.set_tooltip(self.tooltips, _("Fit-to-screen mode"))
        self.toolbutton_fitwidth.set_tooltip(self.tooltips, _("Fit width mode"))
        self.toolbutton_fitheight.set_tooltip(self.tooltips, _("Fit height mode"))
        self.toolbutton_fitnone.set_tooltip(self.tooltips, _("Manual zoom mode"))
        self.toolbutton_double_page.set_tooltip(self.tooltips, _("Double page mode"))
        self.toolbutton_lens.set_tooltip(self.tooltips, _("Magnifying lens"))
        self.toolbutton_manga.set_tooltip(self.tooltips, _("Manga mode"))
        self.toolbutton_first.set_tooltip(self.tooltips, _("First page"))
        self.toolbutton_previous.set_tooltip(self.tooltips, _("Previous page"))
        self.toolbutton_next.set_tooltip(self.tooltips, _("Next page"))
        self.toolbutton_last.set_tooltip(self.tooltips, _("Last page"))
        self.toolbutton_go.set_tooltip(self.tooltips, _("Go to page..."))
        
        # =======================================================
        # Do some tasks depending on the the information parsed
        # from the comixrc and bookmarks files.
        # =======================================================
        
        # Default double page mode.
        if self.prefs['default double page']:
            self.actiongroup.get_action('Double').set_active(True)
        
        # Manga mode
        if self.prefs['manga']:
            self.prefs['manga'] = 0
            self.actiongroup.get_action('manga_mode').set_active(True)
        
        # Default fit to screen/width/height/etc. mode.
        if self.prefs['default zoom mode'] != 0:
            self.actiongroup.get_action('Zin').set_sensitive(False)
            self.actiongroup.get_action('Zout').set_sensitive(False)
            self.actiongroup.get_action('Zoriginal').set_sensitive(False)
            self.actiongroup.get_action('Zwidth').set_sensitive(False)
            self.actiongroup.get_action('Zheight').set_sensitive(False)
            self.actiongroup.get_action('Zfit').set_sensitive(False)
            self.actiongroup.get_action('Scrollbars').set_sensitive(False)
            if self.prefs['default zoom mode'] == 1:
                self.actiongroup.get_action('fit_screen_mode').set_active(
                    True)
            elif self.prefs['default zoom mode'] == 2:
                self.actiongroup.get_action('fit_width_mode').set_active(
                    True)
            elif self.prefs['default zoom mode'] == 3:
                self.actiongroup.get_action('fit_height_mode').set_active(
                    True)
        
        # Set the bars visibility according to the preferences.
        if self.prefs['hide all']:
            self.prefs['hide scrollbar'], self.prefs['show menubar'], \
                self.prefs['show toolbar'], self.prefs['show statusbar'], \
                self.prefs['show thumbnails'] = \
                self.prefs['stored hide all values']
        if self.prefs['show menubar']:
            self.prefs['show menubar'] = 0
            self.actiongroup.get_action('Menubar').set_active(True)
        if self.prefs['show toolbar']:
            self.prefs['show toolbar'] = 0
            self.actiongroup.get_action('Toolbar').set_active(True)
        if self.prefs['show statusbar']:
            self.prefs['show statusbar'] = 0
            self.actiongroup.get_action('Statusbar').set_active(True)
        if not self.prefs['hide scrollbar']:
            self.prefs['hide scrollbar'] = 1
            self.actiongroup.get_action('Scrollbars').set_active(True)
        if self.prefs['show thumbnails']:
            self.prefs['show thumbnails'] = 0
            self.actiongroup.get_action('Thumbnails').set_active(True)
        if self.prefs['hide all']:
            self.prefs['hide all'] = 0
            self.actiongroup.get_action('Hide_all').set_active(True)

        # Default fullscreen.
        if self.prefs['default fullscreen'] or self.prefs['fullscreen']:
            self.window.resize(self.prefs['window width'],
                self.prefs['window height'])
            # Some window managers place the window (without decorations) 
            # at (0, 0) when starting in fullscreen. These lines ensure that
            # the decorations are not hidden when leaving fullscreen by
            # explicitly placing the window at (50, 50) instead.
            if not self.prefs['save window pos']:
                self.window.move(50, 50)
            self.window.show()
            if self.prefs['fullscreen']:
                self.prefs['fullscreen'] = 0
            self.actiongroup.get_action('Fullscreen').set_active(True)
        
        if len(self.bookmarks) == 0:
            self.actiongroup.get_action('Clear_book').set_sensitive(False)
        
        # =======================================================
        # Now, if a file has been given as a parameter or the
        # "Open last viewed file on start" preference is set, we
        # load the appropriate file. If the argument is a directory,
        # we recurse into it searching for the first image file.
        # =======================================================
        self.refresh_activated = True
        self.refresh_image()
        if len(sys.argv) == 2:
            path = os.path.abspath(sys.argv[1])
            if os.path.isdir(path):
                exts = \
                    re.compile(
                    r'\.(jpg|png|jpeg|gif|bmp|tif|tiff|xpm|xbm|ico|' + 
                    'cbz|cbt|cbr)\s*$', re.IGNORECASE)
                stop = False
                for root, dirs, files in os.walk(path):
                    files.sort(locale.strcoll)
                    for f in files:
                        if exts.search(f):
                            path = os.path.join(root, f)
                            stop = True
                            break
                    if stop:
                        break
                if not stop:
                    self.statusbar.push(0, _('No images in "%s"') %
                        self.to_unicode(os.path.basename(path)))
                    self.filetype_error = 1
                else:
                    self.load_file(path, -2)
            else:
                self.load_file(path, -2)
            self.refresh_image()
        elif (self.prefs['auto load last file'] and
            self.prefs['path to last file'] != ''):
            self.load_file(self.prefs['path to last file'],
                self.prefs['page of last file'])
            self.refresh_image()
        else:
            self.set_file_exists(False)



