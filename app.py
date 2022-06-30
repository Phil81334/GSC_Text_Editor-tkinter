import sys
from os import remove, walk
from os.path import isfile, exists, join, dirname, realpath
from progress.spinner import Spinner
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
import os
from stat import S_IREAD
import time
import re
from pathlib import Path
import threading
from threading import Thread
from app_lists import list_of_words, list_of_keywords, list_of_engine_functions, list_of_utility_functions
import json
import customtkinter
from PIL import ImageTk, Image
import webbrowser

# use this line for testing
root_dir = dirname(realpath(__file__))
#print("root_dir:" + root_dir)
# use this line when packing into an exe
#root_dir = "./"

# everytime this app gets executed this line of code will make the below file read only.
# this can then be altered by user in say vscode but as soon as this app is run again, it'll be set back to read only.
# this is to ensure its integirty.
os.chmod(join(dirname(realpath(__file__)), "raw_gsc_code.txt"), S_IREAD)
os.chmod(join(dirname(realpath(__file__)), "raw_script_ref_functions.txt"), S_IREAD)
os.chmod(join(dirname(realpath(__file__)), "app_lists.py"), S_IREAD)

""" GLOBAL VARS """
global is_file_open
is_file_open = False

global current_open_filename
current_open_filename = "New Document..."

global all_editors_saved
all_editors_saved = True

def update_root_window_title():
    global current_open_filename
    global is_file_open

    dir = join(dirname(realpath(__file__)), current_open_filename)
    #print(f"dir: {dir}")

    if is_file_open == False:
        root.title("New Document... - GSC Text Editor")
    else:
        root.title(f"{dir} - GSC Text Editor")

def new():
    #print("new")
    F2_text_editor.delete("1.0","end")
    global current_open_filename
    current_open_filename = "New Document..."
    global is_file_open
    is_file_open = False
    update_line_numbers()
    update_root_window_title()

def open_file():
    #print("open_file")
    global is_file_open
    is_file_open = True

    filepath = askopenfilename( filetypes=[("GSC Script", "*.gsc"), ("All Files", "*.*")] )
    if not filepath:
        return
    F2_text_editor.delete("1.0", "end")
    with open(filepath, "r") as input_file:
        text = input_file.read()
        F2_text_editor.insert("end-1c", text)

    file_name = Path(filepath)
    global current_open_filename
    current_open_filename = file_name.name
    update_root_window_title()
    F2_control_panel.tab(F2_control_panel.index('current'), text=current_open_filename)
    update_line_numbers()

    # so. i need to get all the text. then scan text line by line and group shit up and append to list for highlighting to be done.
    text_to_highlight = []
    # get lines count
    line_count = F2_text_editor.index('end-1c').split('.')[0]
    print(f"line_count: {line_count}")

    for a in range(len(list_of_keywords)):
        list_of_keywords[a] = list_of_keywords[a].lower()
    for b in range(len(list_of_engine_functions)):
        list_of_engine_functions[b] = list_of_engine_functions[b].lower()
    for c in range(len(list_of_utility_functions)):
        list_of_utility_functions[c] = list_of_utility_functions[c].lower()

    # start a loop to scan/iterate through each line
    i = 1
    current_line = "1.0"
    scan_complete = False
    while scan_complete == False:
        #print(f"current_line: {current_line}")
        #print(f"i: {i}")
        #time.sleep(0.5)

        s_idx = F2_text_editor.index(f"{current_line} linestart")
        e_idx = F2_text_editor.index(f"{current_line} lineend")
        line = F2_text_editor.get(s_idx, e_idx)
        #print(f"line: {line}")
        line = line.strip() # remove left and right whitespace
        line = line.lower()
        # check if line is even worth parsing. if not, skip to next line
        if (len(line) > 0):
            #print(f"whole line: {line}")
            fc = line[:1]
            f2c = line[:2]
            lc = line[-1]
            l2c = line[-2:]

            # potentially an 'include', 'using_animtree'
            if (fc == "#"):
                # 'include'
                if (f2c == "#i"):
                    # get the '#include' part
                    first_part = line[:8] # '#include'
                    # check if first part is correct
                    if (first_part.lower() == "#include"):
                        text_to_highlight.append(first_part)
                # 'using_animtree'
                elif (f2c == "#u"):
                    # get the '#using_animtree' part
                    first_part = line[:15] # '#using_animtree'
                    # check if first part is correct
                    if (first_part.lower() == "#using_animtree"):
                        text_to_highlight.append(first_part)

                    matches = re.findall(r'"(.*?)"', line)
                    if len(matches) == 1: # means it found 2 quotation marks
                        within_double_quotes = re.findall('"([^"]*)"', line)
                        a = '"' + str(within_double_quotes)[2:-2] + '"'
                        text_to_highlight.append(a)

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

            # potentially a 'line comment, block comment'
            elif (fc == "/"):
                if line.startswith("//"):
                    #print(f"line: {line}")
                    text_to_highlight.append(line)

                elif line.startswith("/*"):
                    if line.endswith("*/"):
                        text_to_highlight.append(line)
                    else:
                        if int(line_count) > 1:
                            var = ""
                            var = var + line

                            break_from_loop = False
                            while break_from_loop == False:
                                #print(f"current_line: {current_line}")

                                f = float(current_line)
                                next_line = float(f) + float(1)
                                current_line = next_line

                                # get text from the line that the cursor is on. the cusor position on said line does not affect what it grabs.
                                s_idx = F2_text_editor.index(f"{current_line} linestart")
                                e_idx = F2_text_editor.index(f"{current_line} lineend")
                                line = F2_text_editor.get(s_idx, e_idx)
                                #print(f"line: {line}")
                                # check if line is even worth parsing. if not, skip to next line
                                if len(line) > 0:
                                    var = var + line
                                    #if line.endswith("*/"): # <-- advanced parsing. coz bad syntax could follow this but id have to then parse that too.
                                    if "*/" in line: # <-- basic parsing. this means the line starts with /* and somewhere in that line */ is included. it'll do for now.
                                        break_from_loop = True

                                # if end of line has been reached. kill loop
                                if (i == int(line_count) and scan_complete == False):
                                    break_from_loop = True
                                    scan_complete = True

                                i = i +1
                            text_to_highlight.append(var)
                        else:
                            text_to_highlight.append(line)

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

            # potentially a 'function'
            elif fc.isalpha() and l2c.endswith('()'):
                text_to_highlight.append(line)

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

            elif len(re.findall(r'"(.*?)"', line)) >= 1:
                #print(f"len(matches): {len(matches)}")
                within_double_quotes = re.findall('"([^"]*)"', line)
                a = '"' + str(within_double_quotes)[2:-2] + '"'
                text_to_highlight.append(a)
                #print(f"a: {a}")

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

            else:
                for a in range(len(list_of_keywords)):
                    if list_of_keywords[a] in line:
                        text_to_highlight.append(list_of_keywords[a].lower())
                for b in range(len(list_of_engine_functions)):
                    if list_of_engine_functions[b] in line:
                        text_to_highlight.append(list_of_engine_functions[b].lower())
                for c in range(len(list_of_utility_functions)):
                    if list_of_utility_functions[c] in line:
                        text_to_highlight.append(list_of_utility_functions[c].lower())

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

        # nothing to scan on current line so moving on
        else:
            f = float(current_line)
            next_line = float(f) + float(1)
            current_line = next_line

        # if end of line has been reached. kill loop
        if (i == int(line_count) and scan_complete == False):
            scan_complete = True

        i = i +1
    """ HIGHLIGHTING END """

    #split = string.split()
    #print(f"split: {split}")
    #print(f"len(split): {len(split)}")
    highlight_complete = False
    j = 0
    #a_size = len(split)
    a_size = len(text_to_highlight)
    size = a_size -1
    #size = len(text_to_highlight)

    while highlight_complete == False:
        # word = split[j]
        word = text_to_highlight[j]
        word = word.lower()
        print(word)
        #print(f"len(word): {len(word)}")
        # word length use as offset to get end position for tag
        offset = '+%dc' % len(word)
        #print(f"offset {offset}") # +4c (5 chars)

        # search word from first char ("1.0") to the end of text ("end")
        pos_start = F2_text_editor.search(word, '1.0', "end-1c")
        # create tag style
        if word.startswith('//') or word.startswith('/*'):
            #print(f"word: {word}")
            tag = "green_tag"
            F2_text_editor.tag_config(tag, foreground="#60BF13", underline=0)
        elif word.startswith('#'):
            tag = "brown_tag"
            F2_text_editor.tag_config(tag, foreground="brown", underline=0)
        elif '"' in word: # if string
            matches = re.findall(r'"(.*?)"', word)
            if len(matches) == 1: # means it found 2 quotation marks
                tag = "lightblue_tag"
                F2_text_editor.tag_config(tag, foreground="#4FE7FF", underline=0)
        elif word in list_of_keywords:
            tag = "blue_tag"
            F2_text_editor.tag_config(tag, foreground="#0094FF", underline=0)
        elif word in list_of_engine_functions:
            tag = "orange_tag"
            F2_text_editor.tag_config(tag, foreground="#FF7E2D", underline=0)
        elif word in list_of_utility_functions:
            tag = "purple_tag"
            F2_text_editor.tag_config(tag, foreground="#B27CFF", underline=0)
        elif word[:1].isalpha() and word[-2:].endswith('()'):
            tag = "yellow_tag"
            F2_text_editor.tag_config(tag, foreground="yellow", underline=0)
        else:
            tag = None

        if tag != None:
            # check if found the word
            while pos_start:
                pos_end = pos_start + offset
                F2_text_editor.tag_add(tag, pos_start, pos_end)
                # search again from pos_end to the end of text ("end")
                pos_start = F2_text_editor.search(word, pos_end, "end-1c")

        if j == size:
            highlight_complete = True

        j = j +1

def save_file(which):
    #print("save_file")
    global current_open_filename
    global is_file_open
    global all_editors_saved
    all_editors_saved = True

    if (which == "menu_save" or which == "keyboard_save"):
        #print(which)
        if (is_file_open == True):
            print("file is open")
            #print("you have a file open. so ill just override its contents with whats in the textbox")
            # grab everything in textbox
            # open up filename and overwrite its content with content in texbox
            #print(current_open_filename)
            text_on_text_box = F2_text_editor.get("1.0", "end")
            dir = join(dirname(realpath(__file__)), current_open_filename)
            try:
                with open(dir, "w") as current_file:
                    current_file.write(text_on_text_box)

                current_file.close()
            except:
                pass
        else:
            filepath = asksaveasfilename(defaultextension = ".gsc", filetypes=[("GSC Script", "*.gsc"), ("All Files", "*.*")])
            if not filepath:
                return
            with open(filepath, "w") as output_file:
                text = F2_text_editor.get("1.0", "end")
                output_file.write(text)
                output_file.close()
                file_name = Path(filepath)
                current_open_filename = file_name.name
                is_file_open = True
                update_root_window_title()
                F2_control_panel.tab(F2_control_panel.index('current'), text=current_open_filename)
    elif (which == "menu_save_as"):
        #print(which)
        filepath = asksaveasfilename(defaultextension = ".gsc", filetypes=[("GSC Script", "*.gsc"), ("All Files", "*.*")])
        if not filepath:
            return
        with open(filepath, "w") as output_file:
            text = F2_text_editor.get("1.0", "end")
            output_file.write(text)
            output_file.close()
            file_name = Path(filepath)
            current_open_filename = file_name.name
            is_file_open = False
            update_root_window_title()
            F2_control_panel.tab(F2_control_panel.index('current'), text=current_open_filename)

def display_raw_gsc_code(start, end): # this is for the buttons
    f = open(join(dirname(realpath(__file__)), "raw_gsc_code.txt"), 'rt')
    with f as file:
        copy = False
        for line in file:
            if line.strip() == start:
                copy = True
                continue
            elif line.strip() == end:
                break
            elif copy:
                F2_text_editor.insert("insert", line) #"end"
    f.close()
    update_line_numbers()

def autoindent():
    st = F2_text_editor.index(f"{tk.INSERT} linestart")
    e = F2_text_editor.index(f"{tk.INSERT} lineend")
    s = F2_text_editor.get(st, e)
    #print(f"s[1] {s}")
    try:
        if (' ' in s or '\n' in s): # if theres spaces before the last entered input
            last_char = s.split()[-1] # grabs everything after the last space
            s = last_char
            #print(f"s[2] {s}")
    except:
        pass

    try:
        if (s == "{" or s == "(" or s == "["):
            # get current line
            line = F2_text_editor.get("insert linestart", "insert lineend")
            # compute the indentation of the current line
            match = re.match(r'^(\s+)', line)
            current_indent = len(match.group(0)) if match else 0
            # compute the new indentation
            new_indent = current_indent + 4
            # insert the character that triggered the event,
            # a newline, and then new indentation
            global char_end
            if (s == "{"):
                char_end = "}"
            elif (s == "["):
                char_end = "]"
            elif (s == "("):
                char_end = ")"
            """
            if (event.char == "{"):
                char_start = "{"
                char_end = "}"
            elif (event.char == "["):
                char_start = "["
                char_end = "]"
            elif (event.char == "("):
                char_start = "("
                char_end = ")"
            """
            #F2_text_editor.insert("insert", char_start + "\n" + " "*new_indent)
            F2_text_editor.insert("current", "\n" + " "*new_indent)
            current_cursor_pos = F2_text_editor.index("current")
            #print(f"current_cursor_pos {current_cursor_pos}")
            F2_text_editor.insert("insert", "\n" + char_end)
            # now bring cursor back to 'current_cursor_pos' origin
            F2_text_editor.mark_set("insert", current_cursor_pos)
            # return 'break' to prevent the default behavior
            return "break"
    except:
        pass

def indent_highlighted_text_via_tab_key(event):
    try:
        start_line = int(F2_text_editor.index("sel.first")[0])
        last_line = int(F2_text_editor.index("sel.last")[0])
        for x in range(start_line, last_line+1):
            F2_text_editor.insert(f"{x}.0", "\t")
        return 'break'
    except:
        pass

def track_mouse_cursor_motion(event): # not in use
    x, y = event.x, event.y
    #print('{}, {}'.format(x, y))

def fill_word_via_mouse(event):
    try:
        F2_text_editor.insert("end", F2_listbox.get(F2_listbox.curselection()))
    except:
        pass

def remove_tab_from_frame_2_editor(F2_control_panel):
    #print("remove tab")
    active_tabs_name = F2_control_panel.tab(F2_control_panel.select(), "text")
    if active_tabs_name == 'Main':
        messagebox.showinfo("Error", "Can't remove the Main tab.")
    else:
        #F2_control_panel.forget(F2_control_panel.select()) # this only hides the tab. not deletes it.
        for item in F2_control_panel.winfo_children():
            if str(item) == (F2_control_panel.select()):
                tabs_open.pop(F2_control_panel.index('current'))
                item.destroy()
                return

"""                   """
""" FRAME 1 FUNCTIONS """
"""                   """

def show_widget():
   frame_3.pack(side=tk.RIGHT,fill=tk.Y,expand=False,padx=XOFFSET,pady=YOFFSET)
   hide_show_frame_3.configure(text="Maximise Main Editor", command=hide_widget)
def hide_widget():
   frame_3.pack_forget()
   hide_show_frame_3.configure(text="Minimise Main Editor", command=show_widget)

"""                   """
""" FRAME 2 FUNCTIONS """
"""                   """

word = ""
data = ""
def check_input_against_list_of_words(event):
    
    #F2_listbox.pack(side=tk.RIGHT,fill=tk.Y,expand=False,padx=XOFFSET,pady=YOFFSET)
    
    #print("check_input_against_list_of_words")
    widget = event.widget
    global word
    global data
    #start_of_current_line_pos = widget.index("insert")
    #pos_end_of_current_line = widget.index("current")
    try:
        s = widget.index("{0} linestart".format(tk.INSERT))
        e = widget.index("{0} lineend".format(tk.INSERT))

        #print(f"s: {s}")
        #print(f"e: {e}")

        text_on_current_line = widget.get(s, e)
        #print(f"text_on_current_line: {text_on_current_line}")

        #print(f"typed: {typed}")
        #print(f"typed[-1]: {typed[-1]}")

        typed = text_on_current_line

        if (typed == "" or ' ' in typed[-1] or '\n' in typed[-1]):
            data = list
            word = data
        else:
            last_char = typed.split()[-1]
            typed = last_char
            data = []
            word = data
            length_of_typed = len(typed)
            for item in list:
                #if typed.lower() in item.lower(): # this updates the list to show all items that have a matching letter regardless of order.
                if typed.lower() in item.lower()[0:length_of_typed]: # this updates the list to show items that are spelt exactly as you're typing them.
                    data.append(item)
    except:
        pass
    update(data)

def update(list):
    global F2_listbox
    F2_listbox.delete(0, "end")
    for items in list:
        F2_listbox.insert("end", items)

def fill_word_via_keyboard(event):
    
    #F2_listbox.pack_forget()
    
    #print("fill_word_via_keyboard")
    widget = event.widget
    s = widget.index("{0} linestart".format(tk.INSERT))
    e = widget.index("{0} lineend".format(tk.INSERT))
    text_on_current_line = widget.get(s, e)
    #print(f"whats_in_text_box: {whats_in_text_box}") # prints everything including spaces and new-lines
    try:
        if (' ' in text_on_current_line): # if theres spaces
            #print("textbox msg has spaces")
            last_char = text_on_current_line.split()[-1] # grabs everything after the last space
            #print(f"last_char {last_char}") # from 'hi my name is' this'll print out 'is' for example
            #last_char_length = len(last_char)
            #print(f"last_char_length {last_char_length}") 'is', so '2'
            mod_word = word[0][len(last_char):] # slice string to remove first X characters from string
            #print(f"mod_word {mod_word}") # if word == 'issue', this'll print 'sue'
        else: # theres no spaces
            #print("textbox msg has NO spaces")
            mod_word = word[0][len(text_on_current_line):]
            #if (mod_word == word[0]):
        #F2_text_editor.delete("end-1c")
        #if (mod_word in text_on_current_line):
        if (text_on_current_line != ""):
            #print(f"word[0]: {word[0]}")
            if word[0] in list_of_keywords:
                widget.insert("insert", mod_word + ' ')
            else:
                widget.insert("insert", mod_word + '() ')
        #print(f"u pressed shift-r {word[0]}")
    except:
        pass

def change_colour_of_specific_last_word_entered(event):
    #print("change_colour_of_specific_last_word_entered")
    widget = event.widget
    st = widget.index(f"{tk.INSERT} linestart")
    #print(st)
    e = widget.index(f"{tk.INSERT} lineend")
    #print(e)
    a = widget.get(st, e)
    #s = a.lower()
    s = a
    try:
        if (' ' in s or '\n' in s): # if theres spaces
            last_char = s.split()[-1] # grabs everything after the last space
            s = last_char
    except:
        pass

    # this changes every word thats in the list_of_words_to red.
    # o i just simply create a list for diff categories and then apply a specific colour to each list
    #a = s + ' '
    #print(f"s: {s}")
    global tag
    global tag_colour
    tag = ""
    tag_colour = ""
    if (s in list_of_keywords):
        tag = "found_keyword"
        tag_colour = "#A55B92"
    elif (s in list_of_engine_functions):
        tag = "found_engine_function"
        tag_colour = "#FF8000"
    elif (s in list_of_utility_functions):
        tag = "found_utility_function"
        tag_colour = "#903AFF"
    elif ('()' in s): # custom function
        tag = "found_function"
        tag_colour = "#9CDCDB"
    elif ('//' in s): # line comment
        tag = "found_line_comment"
        tag_colour = "#6A7A2B"
    elif ('/*' in s): # block comment
        tag = "found_block_comment"
        tag_colour = "#AD491E"
    elif ('#' in s): # #include
        tag = "found_include"
        tag_colour = "#800000"
    else:
        #print("else")
        return
    """
    #elif ('"0"' in s or '"1"' in s or '"2"' in s or '"3"' in s or '"4"' in s or '"5"' in s or '"6"' in s or '"7"' in s or '"8"' in s or '"9"' in s):# string
    #elif ('{0}'.format(" ") in s):
    elif ('"' in s):
        tag = "found_string"
        tag_colour = "#90EBFF"
    elif ('0' in s or '1' in s or '2' in s or '3' in s or '4' in s or '5' in s or '6' in s or '7' in s or '8' in s or '9' in s): # int
        tag = "found_integer"
        tag_colour = "#008000"

    else:
        return
    """

    idx = '1.0'
    while 1:
        #searches for desired string from index 1
        idx = F2_text_editor.search(s, idx, nocase=1, stopindex="end")
        if not idx: break
        #last index sum of current index and
        #length of text
        lastidx = '%s+%dc' % (idx, len(s))
        #overwrite 'Found' at idx
        F2_text_editor.tag_add(tag, idx, lastidx)
        idx = lastidx

    F2_text_editor.tag_config(tag, foreground=tag_colour)

def remove_colour_of_specific_last_word_entered(event):
    #print("remove_colour_of_specific_last_word_entered")
    widget = event.widget
    s = widget.index(f"{tk.INSERT} linestart")
    e = widget.index(f"{tk.INSERT} lineend")
    a = widget.get(s, e)
    s = a.lower()
    try:
        if (' ' in s or '\n' in s): # if theres spaces
            last_char = s.split()[-1] # grabs everything after the last space
            s = last_char
    except:
        pass

    if (s in list):
        idx = '1.0'
        while 1:
            #searches for desired string from index 1
            idx = widget.search(s, idx, nocase=1, stopindex="end")
            if not idx: break
            #last index sum of current index and
            #length of text
            lastidx = '%s+%dc' % (idx, len(s))
            #overwrite 'Found' at idx
            if (s in list_of_keywords):
                widget.tag_remove('found_keyword', idx, lastidx)
            elif (s in list_of_engine_functions):
                widget.tag_remove('found_engine_function', idx, lastidx)
            elif (s in list_of_utility_functions):
                widget.tag_remove('found_utility_function', idx, lastidx)
            idx = lastidx

# WITH THREADING
def thread_update_line_numbers():
    #print("thread_on_key_release")
    final_index = str(F2_text_editor.index("end-1c"))
    #print(f"final_index: {final_index}")

    num_of_lines = final_index.split('.')[0]
    #print(f"num_of_lines: {num_of_lines}")

    line_numbers_string = "\n".join(str(no + 1) for no in range(int(num_of_lines)))
    #print(f"line_numbers_string: {line_numbers_string}")

    width = len(str(num_of_lines))
    #print(f"width: {width}")

    F2_line_numbers.configure(state='normal', width=width)
    F2_line_numbers.delete("1.0", "end")
    F2_line_numbers.insert("1.0", line_numbers_string)
    F2_line_numbers.configure(state='disabled')
    F2_line_numbers.see("end")

def update_line_numbers():
    #print("update_line_numbers")
    new_thread = Thread(target=thread_update_line_numbers)
    new_thread.start()

def update_editors_saved_status():
    global all_editors_saved
    all_editors_saved = False

def _print(msg):
    print(msg)
    
    #F2_control_panel.select()
    #active_tabs_name = F2_control_panel.tab(F2_control_panel.select(), "text")
    #print(active_tabs_name)
    #if active_tabs_name == 'Main':

tabs_open = []
def create_another_text_editor_window(F2_control_panel):
    #print("create tab")
    if len(tabs_open) <= 19:
        tab = tk.Frame(F2_control_panel,relief=RELIEF)
        if len(tabs_open) < 1:
            F2_control_panel.add(tab, text='Main')
        else:
            F2_control_panel.add(tab, text=f'Tab {len(tabs_open) +1}')
        tabs_open.append(tab)

        global F2_text_editor
        F2_text_editor = scrolledtext.ScrolledText(tab,relief=RELIEF,bd=2,undo=True,wrap="none",width=40,height=10,bg='#1E1E1E',insertbackground='white')
        F2_text_editor.pack(side=tk.TOP,fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
        F2_text_editor.config(font=("Courier New",FONT_SIZE), fg="white")
        F2_text_editor.bind("<KeyRelease>", lambda e: update_editors_saved_status())
        F2_text_editor.bind("<KeyRelease>", check_input_against_list_of_words, add="+")
        F2_text_editor.bind("<Button-1>", check_input_against_list_of_words)
        F2_text_editor.bind("<KeyPress-Shift_R>", fill_word_via_keyboard)
        F2_text_editor.bind("<Control-n>", lambda e: new())
        F2_text_editor.bind("<Control-o>", lambda e: open_file())
        F2_text_editor.bind("<Control-s>", lambda e: save_file("keyboard_save"))
        F2_text_editor.bind("<KeyRelease>", change_colour_of_specific_last_word_entered, add="+")
        F2_text_editor.bind("<BackSpace>", remove_colour_of_specific_last_word_entered)
        F2_text_editor.bind('<Return>', lambda e: update_line_numbers())
        F2_text_editor.bind('<Return>', lambda e: autoindent(), add="+")
        F2_text_editor.bind("<BackSpace>", lambda e: update_line_numbers(), add="+")
        #F2_text_editor.bind("<Enter>", lambda e: _print("enter"))
        #F2_text_editor.bind("<Leave>", lambda e: _print("leave"))

        F2_text_editor_Horizontal_scrollbar = tk.Scrollbar(F2_text_editor, orient="horizontal", command=F2_text_editor.xview)
        F2_text_editor['xscrollcommand'] = F2_text_editor_Horizontal_scrollbar.set
        F2_text_editor_Horizontal_scrollbar.pack(side=tk.BOTTOM,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)

        F2_control_panel.select(tab)
        F2_text_editor.focus()
    else:
        messagebox.showinfo("Error", "Max number of tabs already in use.")

"""                   """
""" FRAME 3 FUNCTIONS """
"""                   """
def compare_files(f1_dir, f2_dir, output_box):
    # C:\Users\Phil-\python_main\gsc script building app\f1_loadout.gsc
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    try:
        f1 = open(f1_dir.get(), 'rt')
        f2 = open(f2_dir.get(), 'rt')
        #f1 = open(join(dirname(realpath(__file__)), "), 'rt')
        #f2 = open(join(dirname(realpath(__file__)), "f2_loadout.gsc"), 'rt')
        i = 0
        for line1 in f1:
            i += 1
            for line2 in f2:
                # matching line1 from both files
                if line1 == line2:
                    # print IDENTICAL if similar
                    # print("Line ", i, ": IDENTICAL")
                    output_box.insert("end", f"Line {i} : IDENTICAL\n")
                else:
                    #print("Line ", i, ":")
                    output_box.insert("end", f"Line {i}:\n")
                    # else print that line from both files
                    #print("\tFile 1:", line1, end='')
                    a = end=''
                    output_box.insert("end", f"\tFile 1: {line1} {a}")
                    #print("\tFile 2:", line2, end='')
                    output_box.insert("end", f"\tFile 2: {line2} {a}")
                break
        # closing files
        f1.close()
        f2.close()
    except:
        messagebox.showinfo("Error", "Enter full directory path! (this includes the filename)\n\nExample:\nE:\SteamLibrary\steamapps\common\Call of Duty Black Ops\raw\maps\_loadout.gsc")
        pass
    output_box.configure(state="disabled")

def stringify_function(data):
    res =  (
        "Summary:\n"
        + data["summary"] + "\n\n"
        + "Arguments:\n"
    )

    res += "Variable        Data type        Valid values        Additional information\n"

    for arg in data["args"]:
        res += f"{arg[0]}        {arg[1]}        {arg[2]}        {arg[3]}"

    return res

def display_raw_script_ref_code():
    global SR_function_entry
    global SR_ouput_textbox
    SR_ouput_textbox.configure(state="normal")
    SR_ouput_textbox.delete("1.0", "end")
    a = SR_function_entry.get()
    a = a.strip()

    a = a.lower()

    start = a + "_START"
    end = a + "_END"
    start = start.lower()
    end = end.lower()

    #print(f"a: {a}")
    #print(f"start: {start}")
    #print(f"end: {end}")
    f = open(join(dirname(realpath(__file__)), "raw_script_ref_functions.txt"), 'rt')
    with f as file:
        copy = False
        for line in file:
            #line = line.lower()
            #print(f"line.lower(): {line.lower()}")
            c = line
            #print(f"c.line: {c}")
            c = c.lower()
            #print(f"c.lower: {c}")
            c = c.strip()
            #print(f"c.strip: {c}")
            if c == start:
            #if line.strip() == start:
                #print(f"line.strip(): {line.strip()}")
                copy = True
                continue
            #elif line.strip() == end:
            elif c == end:
                break
            elif copy:
                SR_ouput_textbox.insert("insert", line)
        f.close()

    """
    data = json.loads(open(join(dirname(realpath(__file__)), "raw_script_ref_functions.json"), 'r').read())
    ref = stringify_function(data["utility"]["AI"]["deletable_magic_bullet_shield"])
    SR_ouput_textbox.insert("insert", ref)
    """

    SR_ouput_textbox.insert("insert", line)
    SR_ouput_textbox.configure(state="disabled")

def advanced_dir_search():
    global files_searched
    global FKS_output_textbox
    files_searched = 0
    FKS_output_textbox.configure(state="normal")
    if(initiate_extension_input() == False): # was a correct file extension entered?
        FKS_output_textbox.delete("1.0", "end")
        FKS_output_textbox.insert("end", 'no extention was added to search')
    elif(initiate_keyword_input() == False): # was a keyword entered?
        FKS_output_textbox.delete("1.0", "end")
        FKS_output_textbox.insert("end", 'no keyword was added to search')
    else:
        execute_search_based_on_input()
        if(len(file_names_with_path) != 0):
            add_to_file() # add "matched keyword" files to array
            FKS_output_textbox.insert("end", f"\n\nFiles searched: {files_searched}")
        else:
            FKS_output_textbox.delete("1.0", "end")
            FKS_output_textbox.insert("end", 'no keyword match located')
    FKS_output_textbox.configure(state="disabled")

def initiate_extension_input():
    global file_names_with_path
    file_names_with_path = []
    global gsc
    global csc
    global csv
    global txt
    gsc = gsc_var.get()
    csc = csc_var.get()
    csv = csv_var.get()
    txt = txt_var.get()
    if(gsc == 1 or csc == 1 or csv == 1 or txt == 1 ):
        return True
    return False

def initiate_keyword_input():
    global FKS_keyword
    global FKS_keyword_entry
    FKS_keyword = FKS_keyword_entry.get()
    if(FKS_keyword == ""):
        return False
    return True

def execute_search_based_on_input():
    if(exists(join(root_dir, "_advanced_dir_search.txt"))):
        remove(join(root_dir, "_advanced_dir_search.txt"))
    if(gsc == 1):
        search(".gsc")
    if(csc == 1):
        search(".csc")
    if(csv == 1):
        search(".csv")
    if(txt == 1):
        search(".txt")

def search(extension):
    global FKS_keyword
    spinner = Spinner('Loading ')
    while spinner != 'FINISHED':
        for path, subdirs, files in walk(root_dir):
            for name in files:
                content = join(path, name)
                #print("content:" + content)
                if(isfile(content) and content.endswith(extension)):
                    try: # does it require 'admin permission'?
                        curr_open_file = open(content, "r", encoding="ISO-8859-1")
                        global files_searched
                        files_searched += 1
                        # print("Searching:", content)
                        spinner.next()
                        if(FKS_keyword in curr_open_file.read()):
                            file_names_with_path.append(content) # found a match
                        curr_open_file.close()
                    except Exception: pass
        spinner = "FINISHED"

# scan complete. now create a file in the same directory as the exe to store the search log.
def add_to_file():
    global FKS_output_textbox
    global FKS_keyword
    if(len(file_names_with_path) != 0):
        f = open(join(root_dir, "_advanced_dir_search.txt"), "x")
        f.write(FKS_keyword)
        f.write("\n")
        f.write("\n")
        f.write("\n")
        for index in file_names_with_path:
            f.write(index)
            f.write("\n")
        f.close()
        FKS_output_textbox.insert("end", '\n')
        FKS_output_textbox.delete("1.0", "end")
        FKS_output_textbox.insert("end", f"{FKS_keyword} was located in {len(file_names_with_path)}, file(s)")
        FKS_output_textbox.insert("end", "\n\nview the results in '_advanced_dir_search.txt'")
    else:
        FKS_output_textbox.insert("end", '\n')
        FKS_output_textbox.insert("end", f"could not locate: {FKS_keyword}")

def script_parser():
    global SP_input_textbox
    global SP_output_textbox
    SP_output_textbox.configure(state="normal")

    # clear output box as a new search has begun
    if (len(SP_output_textbox.get("1.0", "end")) > 0):
        SP_output_textbox.delete("1.0", "end")

    # get lines count
    line_count = SP_input_textbox.index('end-1c').split('.')[0]
    #print(f"line_count: {line_count}")

    # start a loop to scan/iterate through each line
    i = 1
    current_line = "1.0"
    parse_complete = False
    while parse_complete == False:
        print(f"line_count: {line_count}")
        print(f"current_line: {current_line}")
        #print(f"i: {i}")
        #time.sleep(0.5)

        # get text from the line that the cursor is on. the cusor position on said line does not affect what it grabs.
        s_idx = SP_input_textbox.index(f"{current_line} linestart")
        e_idx = SP_input_textbox.index(f"{current_line} lineend")
        line = SP_input_textbox.get(s_idx, e_idx)
        print(f"line: {line}")
        line = line.strip() # remove left and right whitespace
        # check if line is even worth parsing. if not, skip to next line
        if (len(line) > 0):
            #print(f"whole line: {line}")

            # get the first character
            fc = line[:1]
            #print(f"first char {fc}")
            # get the first two characters
            f2c = line[:2]
            #print(f"first two chars {f2c}")
            # get the last character
            lc = line[-1]
            #print(f"last char {lc}")
            # get the last two characters
            l2c = line[-2:]
            #print(f"last 2 chars {l2c}")

            # things to check:
                # nothing other than the following can be outside of a function
                    # include, using_animtree
                    # line & block comments

                    # if all is well, continue to scan functions
                        # functions
                            # line & block comments
                            # variables
                            # keywords (self etc)
                            # and ofc () & {}

            # potentially an 'include', 'using_animtree' or bad syntax
            # #include could be followed by 'maps\' or 'common_scripts\'
            if (fc == "#"):
                # end of line looks good
                if (lc == ";"):
                    # CHANGED APPROACH, game doesnt care if there whitespace between '#include' & 'dir'

                    # 'include'
                    if (f2c == "#i"):
                        # get the '#include' part
                        first_part = line[:8] # '#include'
                        # check if first part is correct
                        if (first_part.lower() != "#include"):
                            SP_output_textbox.insert("1.0", f"[1]Bad syntax on line {i}")
                            parse_complete = True
                        # check if theres a '\' in string. there should be
                        if ('\\' not in line): # its only actually checking to see if there 1 \, not 2. python is weird with the '\\' due to dir stuff.
                            SP_output_textbox.insert("1.0", f"[2]Bad syntax on line {i}")
                            parse_complete = True
                    # 'using_animtree'
                    elif (f2c == "#u"):
                        # get the '#using_animtree' part
                        first_part = line[:15] # '#using_animtree'
                        # check if first part is correct
                        if (first_part.lower() != "#using_animtree"):
                            SP_output_textbox.insert("1.0", f"[3]Bad syntax on line {i}")
                            parse_complete = True
                        # check if theres a single '(' & ')' in string. there should be 1 of each minimum.
                        if ('(' not in line or ')' not in line):
                            SP_output_textbox.insert("1.0", f"B[4]ad syntax on line {i}")
                            parse_complete = True
                        # check if theres two quotation marks in string. there should be at least 2.
                            # where theyre placed is important but ill leave that for the Alpha version. for now just ensuring that theres 2 is enough.
                        matches = re.findall(r'"(.*?)"', line)
                        if len(matches) == 0:
                            SP_output_textbox.insert("1.0", f"[5]Bad syntax on line {i}")
                            parse_complete = True
                    else:
                        SP_output_textbox.insert("1.0", f"[6]Bad syntax on line {i}")
                        parse_complete = True
                else:
                    SP_output_textbox.insert("1.0", f"[7]Bad syntax on line {i}")
                    parse_complete = True

                f = float(current_line)
                next_line = float(f) + float(1)
                current_line = next_line

            # potentially a 'line comment, block comment' or bad syntax
            elif (fc == "/"):
                print("1")
                if not line.startswith("//") or not line.startswith("/*"):
                    print("2")
                    if line.startswith("/*"):
                        print("3")
                        if not line.endswith("*/"):
                            print("4")
                            if int(line_count) > 1:
                                f = float(current_line)
                                next_line = float(f) + float(1)
                                current_line = next_line
                                break_from_loop = False
                                while break_from_loop == False:
                                    print(f"current_line: {current_line}")

                                    # get text from the line that the cursor is on. the cusor position on said line does not affect what it grabs.
                                    s_idx = SP_input_textbox.index(f"{current_line} linestart")
                                    e_idx = SP_input_textbox.index(f"{current_line} lineend")
                                    line = SP_input_textbox.get(s_idx, e_idx)
                                    print(f"line: {line}")
                                    line = line.strip() # remove left and right whitespace
                                    # check if line is even worth parsing. if not, skip to next line
                                    if len(line) > 0:
                                        #if line.endswith("*/"): # <-- advanced parsing. coz bad syntax could follow this but id have to then parse that too.
                                        if "*/" in line: # <-- basic parsing. this means the line starts with /* and somewhere in that line */ is included. it'll do for now.
                                            break_from_loop = True

                                    f = float(current_line)
                                    next_line = float(f) + float(1)
                                    current_line = next_line

                                    # if end of line has been reached. kill loop
                                    if (i == int(line_count) and parse_complete == False):
                                        SP_output_textbox.insert("1.0", f"[8]Bad syntax on line {i}")
                                        break_from_loop = True
                                        parse_complete = True

                                    i = i +1
                            else:
                                SP_output_textbox.insert("1.0", f"[9]Bad syntax on line {i}")
                                parse_complete = True
                    elif not line.startswith("//"):
                        SP_output_textbox.insert("1.0", f"[10]Bad syntax on line {i}")
                        parse_complete = True
                else:
                    SP_output_textbox.insert("1.0", f"[10]Bad syntax on line {i}")
                    parse_complete = True
                """
                # potentially a 'function' or bad syntax
                elif fc.isalpha():
                    print(f"fc: {fc}")
                """

            else:
                SP_output_textbox.insert("1.0", f"[11]Bad syntax on line {i}")
                parse_complete = True

        # nothing to scan on current line so moving on
        else:
            f = float(current_line)
            next_line = float(f) + float(1)
            current_line = next_line

        # if end of line has been reached. kill loop
        if (i == int(line_count) and parse_complete == False):
            #messagebox.showinfo("SUCCESS", "No bad syntax")
            SP_output_textbox.insert("1.0", "SUCCESS: No bad syntax")
            parse_complete = True

        i = i +1

    print("print end")
    SP_output_textbox.configure(state="disabled")

"""                      """
"""     TKINTER MAIN     """
"""                      """

def slider_event(value):
    #print("slider_event")
    #print(value)
    F2_text_editor.config(font=("Courier New",int(value)))

"""            """
""" FRAME 1 TK """
"""            """
def populate_frame_1():
    F1_label = customtkinter.CTkLabel(frame_1,text='Main Editor Control',background='black',foreground='white',relief=RELIEF)
    F1_label.grid(column=0,row=0,sticky='ew',columnspan=3)
    F1_label.config(font=(FONT,FONT_SIZE),fg="white")

    global hide_show_frame_3
    hide_show_frame_3 = customtkinter.CTkButton(frame_1,fg_color='#00A500',hover_color='#006B00',relief=RELIEF,text="Maximise Main Editor",command=hide_widget)
    hide_show_frame_3.grid(column=0,row=1,sticky="ew",padx=XOFFSET,pady=YOFFSET)

    F1_label = customtkinter.CTkLabel(frame_1,text='Font Size',bg_color=None,fg_color=None,relief=RELIEF)
    F1_label.grid(column=0,row=2,sticky='ew',columnspan=3)
    F1_label.config(font=(FONT,FONT_SIZE),fg="white")

    F2_text_editor_font_size_slider = customtkinter.CTkSlider(master=frame_1,from_=5,to=20,command=slider_event,number_of_steps=15,button_color='#00A500',button_hover_color='#006B00')
    F2_text_editor_font_size_slider.grid(column=0,row=3,sticky="ew",padx=XOFFSET,pady=YOFFSET)#.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    F1_label = customtkinter.CTkLabel(frame_1,text='Code Shortcuts',background='black',foreground='white',relief=RELIEF)
    F1_label.grid(column=0,row=4,sticky='ew',columnspan=3)
    F1_label.config(font=(FONT,FONT_SIZE),fg="white")

    for i in range(0, 1): # col
        for x in range(4, 18): # row (start, end=end-1)
            if x == 5:
                F1_btn_1 = customtkinter.CTkButton(frame_1,text="#include maps",command=lambda: display_raw_gsc_code("INCLUDE_M_START","INCLUDE_M_END"))
                F1_btn_1.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 6:
                F1_btn_2 = customtkinter.CTkButton(frame_1,text="#include common_scripts",command=lambda: display_raw_gsc_code("INCLUDE_C_START","INCLUDE_C_END"))
                F1_btn_2.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 7:
                F1_btn_3 = customtkinter.CTkButton(frame_1,text="#using_animtree",command=lambda: display_raw_gsc_code("USING_START","USING_END"))
                F1_btn_3.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 8:
                F1_btn_4 = customtkinter.CTkButton(frame_1,text="init ()",command=lambda: display_raw_gsc_code("INIT_FUNCTION_START","INIT_FUNCTION_END"))
                F1_btn_4.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 9:
                F1_btn_5 = customtkinter.CTkButton(frame_1,text="main ()",command=lambda: display_raw_gsc_code("MAIN_FUNCTION_START","MAIN_FUNCTION_END"))
                F1_btn_5.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 10:
                F1_btn_6 = customtkinter.CTkButton(frame_1,text="custom ()",command=lambda: display_raw_gsc_code("CUSTOM_FUNCTION_START","CUSTOM_FUNCTION_END"))
                F1_btn_6.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 11:
                F1_btn_7 = customtkinter.CTkButton(frame_1,text="level.var",command=lambda: display_raw_gsc_code("GLOBAL_VARIABLE_START","GLOBAL_VARIABLE_END"))
                F1_btn_7.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 12:
                F1_btn_8 = customtkinter.CTkButton(frame_1,text="if () stmt",command=lambda: display_raw_gsc_code("IF_START","IF_END"))
                F1_btn_8.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 13:
                F1_btn_9 = customtkinter.CTkButton(frame_1,text="else if () stmt",command=lambda: display_raw_gsc_code("ELIF_START","ELIF_END"))
                F1_btn_9.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 14:
                F1_btn_10 = customtkinter.CTkButton(frame_1,text="else stmt",command=lambda: display_raw_gsc_code("ELSE_START","ELSE_END"))
                F1_btn_10.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 15:
                F1_btn_11 = customtkinter.CTkButton(frame_1,text="while loop",command=lambda: display_raw_gsc_code("WHILE_LOOP_START","WHILE_LOOP_END"))
                F1_btn_11.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 16:
                F1_btn_12 = customtkinter.CTkButton(frame_1,text="for loop",command=lambda: display_raw_gsc_code("FOR_LOOP_START","FOR_LOOP_END"))
                F1_btn_12.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)
            elif x == 17:
                F1_btn_13 = customtkinter.CTkButton(frame_1,text="switch stmt",command=lambda: display_raw_gsc_code("SWITCH_START","SWITCH_END"))
                F1_btn_13.grid(column=i,row=x,sticky="ew",padx=XOFFSET,pady=YOFFSET)

    frame_1.columnconfigure(0,weight=1)
    frame_1.columnconfigure(1,weight=1)
    frame_1.columnconfigure(2,weight=1)

"""            """
""" FRAME 2 TK """
"""            """
def populate_frame_2():
    F2_label = tk.Label(frame_2,text='Main Editor',background='black',foreground='white',relief=RELIEF)
    F2_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    F2_label.config(font=(FONT,FONT_SIZE),fg="white")

    global F2_line_numbers
    F2_line_numbers = tk.Text(frame_2,relief=RELIEF,bd=2,width=1,background='#D3D3D3',insertbackground='#1E1E1E')
    F2_line_numbers.pack(side=tk.LEFT,fill=tk.Y,expand=False,padx=XOFFSET,pady=YOFFSET)
    F2_line_numbers.config(font=(FONT,9),fg="black")
    F2_line_numbers.insert("1.0", '1')
    F2_line_numbers.configure(state='disabled')

    global F2_control_panel
    F2_control_panel = ttk.Notebook(frame_2)
    F2_control_panel.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
    F2_label.bind("<Double-Button-1>", lambda e: create_another_text_editor_window(F2_control_panel))

    global F2_listbox
    F2_listbox = tk.Listbox(frame_2,bg='#D3D3D3',relief=RELIEF)
    F2_listbox.pack(side=tk.RIGHT,fill=tk.Y,expand=False,padx=XOFFSET,pady=YOFFSET)
    F2_listbox.config(font=(FONT,8),fg="black")

    create_another_text_editor_window(F2_control_panel)

"""              """
""" FRAME 3 - TK """
"""              """
def populate_frame_3():
    F3_label = tk.Label(frame_3,text='Info Panel',background='black',foreground='white',relief=RELIEF)
    F3_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    F3_label.config(font=(FONT,FONT_SIZE),fg="white")

    control_panel = ttk.Notebook(frame_3)
    control_panel.pack(fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)

    tab1 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')
    tab2 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')
    tab3 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')
    tab4 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')
    tab5 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')
    tab6 = tk.Frame(control_panel,relief=RELIEF,bg='#D3D3D3')

    control_panel.add(tab1,text='Generic Editor')
    control_panel.add(tab2,text='Compare Files')
    control_panel.add(tab3,text='Script Reference')
    control_panel.add(tab4,text='File Keyword Search')
    control_panel.add(tab5,text='Script Parser')
    control_panel.add(tab6,text='Useful Links')

    """ TAB 1 [GENERIC EDITOR] """
    Dev_note_label = customtkinter.CTkLabel(tab1,text='Current Version: 1.0\nNOTE: No "if saved" checks are done in this editor',
                              bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")
    GE_input_textbox = scrolledtext.ScrolledText(tab1,relief=RELIEF,bd=2,undo=True,width=40,height=10,background='#1E1E1E',insertbackground='white',wrap='none')
    GE_input_textbox.pack(fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
    GE_input_textbox.config(font=(FONT,FONT_SIZE), fg='white')

    # TAB 2 [COMPARE FILES]
    # To Do: Replace directory input with "open dialog window" where you can select the file to compare.
    Dev_note_label = customtkinter.CTkLabel(tab2,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")
    CF_f1_entry = customtkinter.CTkEntry(tab2)
    CF_f1_entry.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    CF_f1_entry.insert(0, 'Enter full directory of file one: ')
    CF_f2_entry = customtkinter.CTkEntry(tab2)
    CF_f2_entry.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    CF_f2_entry.insert(0, 'Enter full directory of file two: ')
    CF_f2_entry.bind("<Return>", lambda e: compare_files(CF_f1_entry, CF_f2_entry, CF_output_textbox))
    CF_search_btn = customtkinter.CTkButton(tab2,text="Compare Files",relief=RELIEF,command=lambda: compare_files(CF_f1_entry, CF_f2_entry, CF_output_textbox))
    CF_search_btn.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    CF_output_textbox = tk.Text(tab2,relief=RELIEF, bd=2, undo=True, wrap="none", background='#1E1E1E', insertbackground='white')
    CF_output_textbox.config(font=(FONT,8), fg="white", width=40, height=10)
    CF_output_textbox.pack(side=tk.TOP,fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)

    # TAB 3 [SCRIPT REF]
    Dev_note_label = customtkinter.CTkLabel(tab3,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")
    global SR_function_entry
    global SR_ouput_textbox
    SR_function_entry = customtkinter.CTkEntry(tab3)
    SR_function_entry.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SR_function_entry.insert(0, 'Enter function name: ')
    SR_function_entry.bind("<Return>", lambda e: display_raw_script_ref_code())
    SR_search_btn = customtkinter.CTkButton(tab3, text="Search",relief=RELIEF, command=display_raw_script_ref_code)
    SR_search_btn.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SR_ouput_textbox = tk.Text(tab3,relief=RELIEF,bd=2,undo=True,wrap='word',background='#1E1E1E',insertbackground='white')
    SR_ouput_textbox.config(font=(FONT,8), fg="white", width=40, height=10)
    SR_ouput_textbox.pack(side=tk.TOP,fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)

    # TAB 4 [FILE KEYWORD SEARCH]
    Dev_note_label = customtkinter.CTkLabel(tab4,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")
    global gsc_var
    global csc_var
    global csv_var
    global txt_var
    global FKS_keyword_entry
    global FKS_output_textbox
    gsc_var = tk.IntVar()
    csc_var = tk.IntVar()
    csv_var = tk.IntVar()
    txt_var = tk.IntVar()
    FKS_gsc_button = customtkinter.CTkCheckBox(tab4,text="include .gsc extention file types?",variable=gsc_var,onvalue=1,offvalue=0)
    FKS_gsc_button.pack(expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_gsc_button.configure(bg_color=None,fg_color='green',text_color='black')

    FKS_csc_button = customtkinter.CTkCheckBox(tab4,text="include .csc extention file types?",variable=csc_var,onvalue=1,offvalue=0)
    FKS_csc_button.pack(expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_csc_button.configure(bg_color=None,fg_color='green',text_color='black')

    FKS_csv_button = customtkinter.CTkCheckBox(tab4,text="include .csv extention file types?",variable=csv_var,onvalue=1,offvalue=0)
    FKS_csv_button.pack(expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_csv_button.configure(bg_color=None,fg_color='green',text_color='black')

    FKS_txt_button = customtkinter.CTkCheckBox(tab4,text="include .txt extention file types?  ",variable=txt_var,onvalue=1,offvalue=0)
    FKS_txt_button.pack(expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_txt_button.configure(bg_color=None,fg_color='green',text_color='black')

    FKS_keyword_entry = customtkinter.CTkEntry(tab4)
    FKS_keyword_entry.insert(0, 'Enter keyword: ')
    FKS_keyword_entry.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_keyword_entry.bind("<Return>", lambda e: advanced_dir_search())
    FKS_search_btn = customtkinter.CTkButton(tab4,text="Start Search...",relief=RELIEF,command=advanced_dir_search)
    FKS_search_btn.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    FKS_output_textbox = tk.Text(tab4,relief=RELIEF, bd=2, undo=True, wrap="none", background='#1E1E1E', insertbackground='white')
    FKS_output_textbox.config(font=(FONT,FONT_SIZE), fg="white", width=90, height=10)
    FKS_output_textbox.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)

    # TAB 5 [SCRIPT PARSER]
    Dev_note_label = customtkinter.CTkLabel(tab5,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")
    global SP_input_textbox
    global SP_output_textbox
    SP_input_label = customtkinter.CTkLabel(tab5,text='Input',bg_color=None,fg_color='grey',relief=RELIEF)
    SP_input_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SP_debug_btn = customtkinter.CTkButton(tab5,text="Parse Script",relief=RELIEF, command=script_parser)
    SP_debug_btn.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SP_input_textbox = tk.Text(tab5,relief=RELIEF, bd=2, undo=True, wrap="none", background='#1E1E1E', insertbackground='white')
    SP_input_textbox.config(font=(FONT,8), fg="white")#, width=90, height=10) # this has expanded it more.
    SP_input_textbox.pack(fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
    #SP_input_textbox.bind("<Return>", lambda e: script_parser()) # works fine i just need to edit code during testing
    SP_output_label = customtkinter.CTkLabel(tab5,text='Ouput',bg_color=None,fg_color='grey',relief=RELIEF)
    SP_output_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SP_output_textbox = tk.Text(tab5,relief=RELIEF, bd=2, undo=True, wrap="none", background='#1E1E1E', insertbackground='white')
    SP_output_textbox.config(font=(FONT,8), fg="white", width=90, height=10)
    SP_output_textbox.pack(side=tk.BOTTOM,fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)

    # TAB 6 [USEFUL LINKS]
    #img = ImageTk.PhotoImage(Image.open(join(dirname(realpath(__file__)), "zombies_hd_bg.gif")).resize((1920,1080)))
    #bg = customtkinter.CTkLabel(master=tab6,bg_color=None,fg_color='grey',)#image=img)
    #bg.pack(fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
    
    Dev_note_label = customtkinter.CTkLabel(tab6,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    Dev_note_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    Dev_note_label.config(font=(FONT,FONT_SIZE),fg="white")

    ugx_mods = customtkinter.CTkLabel(tab6,text='UGX MODS',bg_color=None,fg_color='black',relief=RELIEF)
    ugx_mods.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    ugx_mods.config(font=(FONT,FONT_SIZE),fg="white")

    ugx_mods_btn = customtkinter.CTkButton(master=tab6,height=25,text="UGX Mods",border_width=3,fg_color=None,text_color='black',command=lambda:hyperlink("https://www.ugx-mods.com/"))
    ugx_mods_btn.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    
    ugx_mods_script_ref_btn = customtkinter.CTkButton(master=tab6,height=25,text="UGX Mods Script Reference",border_width=3,fg_color=None,text_color='black',command=lambda:hyperlink("https://www.ugx-mods.com/script/"))
    ugx_mods_script_ref_btn.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)

    ugx_mods_discord = customtkinter.CTkButton(master=tab6,height=25,text="UGX Mods Discord",border_width=3,fg_color=None,text_color='black',command=lambda:hyperlink("https://discord.gg/Dr5P9Bkj"))
    ugx_mods_discord.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)

    """
    bo1_linkermod = customtkinter.CTkLabel(tab6,text='BO1 LinkerMod',bg_color=None,fg_color='#1C1CCE',relief=RELIEF)
    bo1_linkermod.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    bo1_linkermod.config(font=(FONT,FONT_SIZE),fg="white")
    
    bo1_linkermod_btn = customtkinter.CTkButton(master=tab6,height=25,text="BO1 Discord",border_width=3,fg_color='#1C94CF',text_color='black',command=lambda:hyperlink("https://discord.gg/QrTmJBzK"))
    bo1_linkermod_btn.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    """

def hyperlink(url):
    try:
        webbrowser.open_new(url)
    except:
        messagebox.showinfo("Failed", "Could be that you have no internet connection?")
        pass

"""                """
""" TEMP FUNCTIONS """
"""                """
def place_holder_button():
    messagebox.showinfo("Message", "place_holder_button")

def lock_screen():
    screen_lock_bg.pack()
    main_frame.forget()
    frame_1.forget()
    frame_2.forget()
    frame_3.forget()

    """
    SS_label = customtkinter.CTkLabel(screen_lock_bg,text='Current Version: 1.0',bg_color=None,fg_color='black',relief=RELIEF)
    SS_label.pack(side=tk.TOP,fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SS_label.config(font=(FONT,FONT_SIZE),fg="white")

    SS_entry = customtkinter.CTkEntry(screen_lock_bg)
    SS_entry.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    SS_entry.insert(0, 'Enter Password: ')

    SS_btn = customtkinter.CTkButton(screen_lock_bg,text="Continue",relief=RELIEF,command=None)
    SS_btn.pack(fill=tk.X,expand=False,padx=XOFFSET,pady=YOFFSET)
    """

""" Actual application window """
if __name__ == "__main__":
    #root = tk.Tk()
    #root.iconbitmap('skull_icon_c.ico')
    #root.state('zoomed')
    #root.configure(background='#8585ad')
    #update_root_window_title()

    customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
    customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
    root = customtkinter.CTk()  # create CTk window like you do with the Tk window
    root.geometry("1366x720")
    #root = tk.Tk()
    root.iconbitmap('skull_icon_c.ico')
    root.state('zoomed')
    root.configure(background = '#000000') #'#8585ad')
    update_root_window_title()
    #root.bind('<Control-l>', lambda e: lock_screen())

XOFFSET = 5
YOFFSET = 5
RELIEF = "ridge"
BORDERWIDTH = 5
FONT = 'Consolas bold'
FONT_SIZE = 10

MAIN_FRAME_BACKGROUND_COLOUR = '#000000' #'#8585ad'
FRAME_1_BACKGROUND_COLOUR = '#000000'
FRAME_2_BACKGROUND_COLOUR = '#000000'
FRAME_3_BACKGROUND_COLOUR = '#000000'

def populate_root_menu_1():
    global menu_bar
    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar,tearoff=False,background='#A0A0A0',fg='black')
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New",command=lambda: new())
    file_menu.add_command(label="Open",command=lambda: open_file())
    file_menu.add_command(label="Save",command=lambda: save_file("menu_save"))
    file_menu.add_command(label="Save As...",command=lambda: save_file("menu_save_as"))
    file_menu.add_separator()
    file_menu.add_command(label="Exit",command=lambda: on_closing())

def populate_root_menu_2():
    main_editor = tk.Menu(menu_bar, tearoff=False,background='#A0A0A0',fg='black')
    menu_bar.add_cascade(label="Main Editor",menu=main_editor)
    #main_editor.add_command(label="Undo", command=F2_text_editor.edit_undo, accelerator="(Ctrl+Z)")
    #main_editor.add_command(label="Redo", command=F2_text_editor.edit_redo, accelerator="(Ctrl+Y)")
    main_editor.add_command(label="Remove active tab",command=lambda: remove_tab_from_frame_2_editor(F2_control_panel))

def populate_root_menu_3():
    help_menu = tk.Menu(menu_bar,tearoff=False,background='#A0A0A0',fg='black')
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About...", command=place_holder_button)

main_frame = tk.Frame(root,borderwidth=BORDERWIDTH,background=MAIN_FRAME_BACKGROUND_COLOUR,relief='sunken')
frame_1 = tk.Frame(main_frame,borderwidth=1,background=FRAME_1_BACKGROUND_COLOUR,relief='sunken')
frame_2 = tk.Frame(main_frame,borderwidth=1,background=FRAME_2_BACKGROUND_COLOUR,relief='sunken')
frame_3 = tk.Frame(main_frame,borderwidth=1,background=FRAME_3_BACKGROUND_COLOUR,relief='sunken')

main_frame.pack(fill=tk.BOTH,expand=True,padx=XOFFSET,pady=YOFFSET)
frame_1.pack(side=tk.LEFT,fill=tk.BOTH,padx=XOFFSET,pady=YOFFSET)
frame_2.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,pady=YOFFSET)
frame_3.pack(side=tk.RIGHT,fill=tk.Y,expand=False,padx=XOFFSET,pady=YOFFSET)

populate_frame_1()
populate_frame_2()
populate_frame_3()

populate_root_menu_1()
populate_root_menu_2()
populate_root_menu_3()

img = ImageTk.PhotoImage(Image.open(join(dirname(realpath(__file__)), "zombies_bg.jpg")).resize((1920,1080)))
screen_lock_bg = customtkinter.CTkLabel(root,image=img)

tab_font = ttk.Style()
tab_font.configure('.', font=(FONT,9,'bold') )

all_lists = []
for i in list_of_keywords: all_lists.append(i)
for i in list_of_engine_functions: all_lists.append(i)
for i in list_of_utility_functions: all_lists.append(i)
list = all_lists
update(list)

def on_closing():
    global all_editors_saved
    if all_editors_saved == False:
        if messagebox.askokcancel("WARNING", "You have unsaved content. Are you sure you want to quit?"):
            root.destroy()
    else:
        root.destroy()

root.config(menu=menu_bar)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
""" "end" OF FILE """