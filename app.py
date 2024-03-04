import os, customtkinter, queue
from src.upscale import upscale
from threading import Thread, RLock


if not os.path.exists(f"./input"):
    os.mkdir(f"./input")
if not os.path.exists(f"./output"):
    os.mkdir(f"./output")
if not os.path.exists(f"./temp"):
    os.mkdir(f"./temp")
if not os.path.exists(f"./weights"):
    os.mkdir(f"./weights")

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")

app_title = "VideoUpscaler v1.0.1"


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
            checkbox.cget("text")
            for checkbox in self.checkbox_list
            if checkbox.get() == 1
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

        # sidebar
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=app_title,
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.select_all_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Select All", command=self.select_all_event
        )
        self.select_all_button.grid(row=1, column=0, padx=20, pady=10, sticky="n")

        self.select_all_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Deselect All", command=self.deselect_all_event
        )
        self.select_all_button.grid(row=2, column=0, padx=20, pady=10, sticky="n")

        self.refresh_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Refresh Inputs", command=self.refresh_button_event
        )
        self.refresh_button.grid(row=3, column=0, padx=20, pady=10, sticky="n")

        self.upscale_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Start Upscale", command=self.upscale_button_event
        )
        self.upscale_button.grid(row=4, column=0, padx=20, pady=10, sticky="n")

        self.show_input_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Show Input", command=self.open_input_folder
        )
        self.show_input_button.grid(row=5, column=0, padx=50, pady=10, sticky="n")

        self.show_output_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Show Output", command=self.open_output_folder
        )
        self.show_output_button.grid(row=6, column=0, padx=20, pady=10, sticky="n")

        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )

        # model
        self.model_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Model (Scale):", anchor="w"
        )
        self.model_label.grid(row=22, column=0, padx=20, pady=(10, 0))
        self.model_menu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=[
                "2x",
                "4x",
                "8x",
            ],
            command=self.change_model_event,
        )
        self.model_menu.grid(row=23, column=0, padx=20, pady=(10, 0))

        # appearance
        self.appearance_mode_label.grid(row=30, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=31, column=0, padx=20, pady=(10, 20))

        # scroll check box
        self.checkbox = ScrollableCheckBoxFrame(
            master=self,
            width=230,
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

    def change_model_event(self, new_model):
        self.model = new_model

    def select_video(self):
        if len(self.checkbox.get_checked_items()) == 0:
            self.upscale_button.configure(state="disabled", text="No Video Selected")
        else:
            self.upscale_button.configure(state="enabled", text="Start Upscale")

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
                    print(f"Processing [{filename}]...")

                    cc = Thread(target=hc, args=(filepath, filename))
                    self.queue.put(cc)
                    cc.start()

                    print(f"Completed [{filename}]")
                else:
                    print(f"Ignored [{filename}].")
            else:
                continue


if __name__ == "__main__":
    app = App()
    app.mainloop()
