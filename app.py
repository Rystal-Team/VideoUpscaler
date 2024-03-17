import os, customtkinter, queue, shutil, yaml
from src.upscale import upscale
from threading import Thread, RLock
from PIL import Image
from customtkinter import StringVar

with open("lang.yaml", "r", encoding="utf8") as stream:
    langs = yaml.safe_load(stream)

if not os.path.exists(f"./input"):
    os.mkdir(f"./input")
if not os.path.exists(f"./output"):
    os.mkdir(f"./output")
if not os.path.exists(f"./weights"):
    os.mkdir(f"./weights")

if os.path.exists(f"./temp"):
    shutil.rmtree(f"./temp")
os.mkdir(f"./temp")

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")

app_title = "ビデオアップスケーラー v1.0.2"


class ScrollableCheckBoxFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, item_list, command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.command = command
        self.checkbox_list = []

    def add_item(self, item):
        checkbox = customtkinter.CTkCheckBox(self, text=item)

        if self.command is not None:
            checkbox.configure(command=self.command)

        checkbox.grid(row=len(self.checkbox_list), column=0, pady=(0, 10), sticky="w")
        self.checkbox_list.append(checkbox)

    def remove_item(self, item):
        for checkbox in self.checkbox_list:
            if item == checkbox.cget("text"):
                checkbox.destroy()
                self.checkbox_list.remove(checkbox)
                return

    def get_checked_items(self):
        return [
            checkbox.cget("text") for checkbox in self.checkbox_list if checkbox == 1
        ]


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.rlock = RLock()

        # window
        self.title(app_title)
        self.iconbitmap("./app.ico")
        self.geometry(f"{800}x{600}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.lang = "en"
        self.lang_texts = {}

        for i in langs[self.lang]:
            self.lang_texts[i] = StringVar()

        for i in langs[self.lang]:
            self.lang_texts[i].set(langs[self.lang][i])

        print(self.lang_texts)

        # sidebar
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=2)

        self.logo_image = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="",
            image=customtkinter.CTkImage(Image.open("./icon.png"), size=(96, 96)),
        )
        self.logo_image.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="n")

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            textvariable=self.lang_texts["app_title"],
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=20, pady=(20, 10), sticky="n")

        self.select_all_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["select_all"],
            command=self.select_all_event,
        )
        self.select_all_button.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="n")

        self.deselect_all_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["deselect_all"],
            command=self.deselect_all_event,
        )
        self.deselect_all_button.grid(
            row=3, column=0, padx=20, pady=(0, 10), sticky="n"
        )

        self.upscale_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["start_upscale"],
            command=self.upscale_button_event,
        )
        self.upscale_button.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="n")

        self.refresh_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["refresh_input"],
            command=self.refresh_button_event,
        )
        self.refresh_button.grid(row=20, column=0, padx=20, pady=(0, 10), sticky="s")

        self.show_input_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["show_input"],
            command=self.open_input_folder,
        )
        self.show_input_button.grid(row=21, column=0, padx=50, pady=(0, 10), sticky="s")

        self.show_output_button = customtkinter.CTkButton(
            self.sidebar_frame,
            textvariable=self.lang_texts["show_output"],
            command=self.open_output_folder,
        )
        self.show_output_button.grid(
            row=22, column=0, padx=20, pady=(0, 10), sticky="s"
        )

        # model
        self.model_label = customtkinter.CTkLabel(
            self.sidebar_frame, textvariable=self.lang_texts["model_scale"], anchor="w"
        )
        self.model_label.grid(row=23, column=0, padx=20, pady=(10, 0))
        self.model_menu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=[
                "2x",
                "4x",
                "8x",
            ],
            command=self.change_model_event,
        )
        self.model_menu.grid(row=24, column=0, padx=20, pady=(10, 0))

        # appearance
        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            textvariable=self.lang_texts["appearance_mode"],
            anchor="w",
        )

        self.appearance_mode_label.grid(row=30, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "Default"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=31, column=0, padx=20, pady=(10, 0))

        self.langauge_selection = customtkinter.CTkLabel(
            self.sidebar_frame,
            textvariable=self.lang_texts["langauge_selection"],
            anchor="w",
        )
        self.langauge_selection.grid(row=32, column=0, padx=20, pady=(10, 0))

        self.langauge_selection_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["日本語", "English"],
            command=self.change_language,
        )
        self.langauge_selection_optionemenu.grid(
            row=33, column=0, padx=20, pady=(10, 20)
        )

        # scroll check box
        self.checkbox = ScrollableCheckBoxFrame(
            master=self,
            label_text=self.lang_texts["select_input"].get(),
            width=100,
            command=self.select_video,
            item_list=[],
            height=10000000,
        )
        self.checkbox.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # default
        self.appearance_mode_optionemenu.set("Dark")
        self.model_menu.set("2x")
        self.model = "2x"

        # call default
        self.refresh_button_event()
        self.select_all_event()

    def open_input_folder(self):
        os.startfile(os.path.realpath("./input"))

    def open_output_folder(self):
        os.startfile(os.path.realpath("./output"))

    def change_language(self, new_langauge: str):
        if new_langauge == "English":
            self.lang = "en"
        elif new_langauge == "日本語":
            self.lang = "ja"
        else:
            self.lang = "en"

        for i in langs[self.lang]:
            self.lang_texts[i].set(langs[self.lang][i])

        self.title(label_text=self.lang_texts["app_title"].get())
        self.checkbox.configure(label_text=self.lang_texts["select_input"].get())

    def change_model_event(self, new_model):
        self.model = new_model

    def select_video(self):
        if len(self.checkbox.get_checked_items()) == 0:
            self.upscale_button.configure(
                state=customtkinter.DISABLED,
                textvariable=self.lang_texts["no_video_selected"],
            )
        else:
            self.upscale_button.configure(
                state=customtkinter.NORMAL,
                textvariable=self.lang_texts["start_upscale"],
            )

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def select_all_event(self):
        for checkbox in self.checkbox.checkbox_list:
            checkbox.select()

        self.select_video()

    def deselect_all_event(self):
        for checkbox in self.checkbox.checkbox_list:
            checkbox.deselect()

        self.select_video()

    def refresh_button_event(self):
        self.checkbox.checkbox_list = []
        for filename in os.listdir("./input"):
            filepath = os.path.join("./input/", filename)

            if filename.endswith(".mkv") or filename.endswith(".mp4"):
                print(f"Discovered [{filename}]")
                self.checkbox.add_item(filepath)
            else:
                continue

    def upscale_button_event(self):
        def hc(filepath, filename):
            with self.rlock:
                filename = filename.replace(".mkv", "") and filename.replace(".mp4", "")
                upscale(filepath, filename, self.model)

        for filename in os.listdir("./input"):
            filepath = os.path.join("./input/", filename)

            if filename.endswith(".mkv") or filename.endswith(".mp4"):
                if filepath in self.checkbox.get_checked_items():

                    cc = Thread(target=hc, args=(filepath, filename))
                    self.queue.put(cc)
                    cc.start()

                else:
                    print(f"Ignored [{filename}].")
            else:
                continue


if __name__ == "__main__":
    app = App()
    app.mainloop()
