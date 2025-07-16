import customtkinter
import random
import time
from threading import Thread
from database import MenuDB
import tkinter as tk
import datetime  # Add for current date
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator
from matplotlib.animation import FuncAnimation

# --- Matplotlib 한글/이모지 폰트 설정 ---
# Windows에서 이모지와 한글을 모두 지원하기 위해 폰트 리스트를 설정합니다.
# Matplotlib은 리스트의 첫 폰트부터 글자를 찾아 렌더링합니다.
font_families = ['Segoe UI Emoji', 'Malgun Gothic']
plt.rc('font', family=font_families)
plt.rcParams['axes.unicode_minus'] = False
# ---------------------------------

# Premium color scheme
COLOR_PRIMARY = "#4A90E2"
COLOR_SECONDARY = "#34495E"
COLOR_ACCENT = "#E74C3C"
COLOR_SUCCESS = "#2ECC71"
COLOR_SILVER = "#BDC3C7"  # Silver color for 2nd place
COLOR_BG = "#ECF0F1"
COLOR_BG_LIGHT = "#F8F9FA"  # Light background for frames
COLOR_CARD = "#FFFFFF"

# Set appearance
customtkinter.set_appearance_mode("Light")
customtkinter.set_default_color_theme("blue")


class LunchPickerApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Initialize database
        self.db = MenuDB()

        # Configure window
        self.title("점심 식당 선택")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(fg_color=COLOR_BG)

        # Get today's date
        today = datetime.datetime.now().strftime("%Y년 %m월 %d일")

        # Create header
        self.header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10), padx=20, fill="x")

        # Create title label with date
        self.title_label = customtkinter.CTkLabel(
            self,
            text=f"점심 식당 선택 ({today})",
            font=customtkinter.CTkFont(size=28, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.title_label.pack(pady=(30, 0))

        # Create subtitle label
        self.subtitle_label = customtkinter.CTkLabel(
            self.header_frame,
            text="오늘의 점심 식당을 추천해드립니다",
            font=customtkinter.CTkFont(size=16, family="Malgun Gothic"),
            text_color="#7F8C8D"
        )
        self.subtitle_label.pack()

        # Create main content frame
        self.content_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Create tab view with larger tabs
        self.tab_view = customtkinter.CTkTabview(
            self.content_frame,
            segmented_button_fg_color=COLOR_PRIMARY,
            segmented_button_selected_color=COLOR_SECONDARY,
            segmented_button_selected_hover_color=COLOR_SECONDARY,
            text_color="white",
            corner_radius=10,
            width=800,
            height=45
        )
        self.tab_view._segmented_button.configure(font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"))
        self.tab_view.configure(command=self._on_tab_change)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs with padding
        self.menu_tab = self.tab_view.add("  식당 관리  ")
        self.history_tab = self.tab_view.add("  선택 기록  ")
        self.stats_tab = self.tab_view.add("  통계  ")
        self.settings_tab = self.tab_view.add("  설정  ")

        # Setup all UI tabs
        self._setup_menu_tab()
        self._setup_history_tab()
        self._setup_stats_tab()
        self._setup_settings_tab()

        self.stats_animation = None # To hold the animation object

        # Load initial data from DB
        self.load_menu_items()
        self._apply_auto_exclusion()
        self.load_history()
        # self.update_stats_graph() # Now called on tab change

        self._load_company_name()

        # Set initial UI state using the new centralized method
        self._update_ui_for_state('idle')

    def _on_tab_change(self, tab_name=None):
        # Stop any running animation when changing tabs
        if self.stats_animation and self.stats_animation.event_source:
            self.stats_animation.event_source.stop()
            self.stats_animation = None

        current_tab = self.tab_view.get()
        if current_tab == "  통계  ":
            self.update_stats_graph()
        elif current_tab == "  선택 기록  ":
            self.load_history()
    def _setup_menu_tab(self):
        # Main content frame
        main_frame = customtkinter.CTkFrame(self.menu_tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Input section
        left_panel = customtkinter.CTkFrame(main_frame, fg_color=COLOR_CARD, corner_radius=12)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)
        left_panel.pack_propagate(False)
        left_panel.configure(width=400)
        
        # Input section title
        input_title = customtkinter.CTkLabel(
            left_panel,
            text="식당 추가",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        input_title.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Input field
        input_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent")
        input_frame.pack(pady=10, padx=20, fill="x")
        
        self.entry = customtkinter.CTkEntry(
            input_frame, 
            placeholder_text="새 식당 이름을 입력하세요",
            corner_radius=8,
            height=45,
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic")
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.add_button = customtkinter.CTkButton(
            input_frame, 
            text="추가",
            command=self.add_menu_item,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BCC",
            width=80,
            height=45,
            font=customtkinter.CTkFont(size=14, weight="bold", family="Malgun Gothic")
        )
        self.add_button.pack(side="right")
        
        # Divider
        customtkinter.CTkFrame(left_panel, height=2, fg_color="#EEEEEE").pack(pady=20, padx=20, fill="x")
        
        # Exclusion section title
        exclusion_title = customtkinter.CTkLabel(
            left_panel,
            text="식당 목록",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        exclusion_title.pack(pady=(0, 5), padx=20, anchor="w")

        exclusion_subtitle = customtkinter.CTkLabel(
            left_panel,
            text="(선택항목은 선택 대상에서 제외)",
            font=customtkinter.CTkFont(size=12, family="Malgun Gothic"),
            text_color="#7F8C8D"
        )
        exclusion_subtitle.pack(pady=(0, 10), padx=20, anchor="w")

        self.auto_exclude_label = customtkinter.CTkLabel(
            left_panel,
            text="",
            font=customtkinter.CTkFont(size=12, family="Malgun Gothic"),
            text_color="#7F8C8D",
            anchor="w"
        )
        self.auto_exclude_label.pack(pady=(0, 5), padx=20, fill="x")
        
        # Exclusion list
        self.exclusion_list_frame = customtkinter.CTkScrollableFrame(
            left_panel, 
            height=250,
            fg_color="#FAFAFA"
        )
        self.exclusion_list_frame.pack(padx=20, pady=5, fill="both", expand=True)
        
        # Menu items storage
        self.menu_widgets = {}
        
        # Right panel - Selection section
        right_panel = customtkinter.CTkFrame(main_frame, fg_color=COLOR_CARD, corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)
        
        # Selection title
        selection_title = customtkinter.CTkLabel(
            right_panel,
            text="점심 선택",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        selection_title.pack(pady=(20, 10), padx=20, anchor="w")

        # Countdown duration selector
        duration_frame = customtkinter.CTkFrame(right_panel, fg_color="transparent")
        duration_frame.pack(pady=10, padx=20, fill="x")

        duration_label = customtkinter.CTkLabel(
            duration_frame, 
            text="카운트다운 시간(초):", 
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic")
        )
        duration_label.pack(side="left")

        self.countdown_duration_var = customtkinter.StringVar(value="5")
        self.duration_menu = customtkinter.CTkOptionMenu(
            duration_frame,
            values=["3", "5", "10", "15"],
            variable=self.countdown_duration_var,
            width=100,
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic"),
            dropdown_font=customtkinter.CTkFont(size=14, family="Malgun Gothic"),
            fg_color=COLOR_PRIMARY,
            button_color=COLOR_SECONDARY
        )
        self.duration_menu.pack(side="right")
        
        # Start button
        button_frame = customtkinter.CTkFrame(right_panel, fg_color="transparent")
        button_frame.pack(pady=(0, 20), padx=20, fill="x")

        self.start_button = customtkinter.CTkButton(
            button_frame, 
            text="메뉴 추천 시작!", 
            command=self._run_countdown_logic,
            fg_color=COLOR_SUCCESS,
            hover_color="#27AE60",
            height=60,
            text_color="white",
            text_color_disabled="white",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic")
        )
        self.start_button.pack(fill="x")

        self.restart_button = customtkinter.CTkButton(
            button_frame, 
            text="추첨 재시작", 
            command=self.reset_selection,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BCC",
            height=60,
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic")
        )
        # The restart button is not packed initially
        
        # Result display
        self.result_frame = customtkinter.CTkFrame(
            right_panel, 
            fg_color=COLOR_BG_LIGHT, 
            corner_radius=15
        )
        self.result_frame.pack(pady=0, padx=20, fill="both", expand=True)
        self.result_frame.pack_propagate(False)
        
        self.countdown_label = customtkinter.CTkLabel(
            self.result_frame,
            text="",
            font=customtkinter.CTkFont(size=18, family="Malgun Gothic"),
            wraplength=300  # Enable text wrapping
        )
        self.countdown_label.pack(expand=True)

    def _setup_stats_tab(self):
        stats_frame = customtkinter.CTkFrame(self.stats_tab, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.stats_fig = plt.figure(figsize=(8, 6), dpi=100, facecolor=COLOR_BG_LIGHT)
        self.stats_ax = self.stats_fig.add_subplot(111, facecolor=COLOR_BG_LIGHT)
        
        self.stats_canvas = FigureCanvasTkAgg(self.stats_fig, master=stats_frame)
        self.stats_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_stats_graph(self):
        if self.stats_animation and self.stats_animation.event_source:
            self.stats_animation.event_source.stop()
            self.stats_animation = None

        stats = self.db.get_selection_stats()
        self.stats_ax.clear()

        if not stats:
            self.stats_ax.text(0.5, 0.5, "선택 기록이 없습니다.", ha='center', va='center', fontsize=18, color=COLOR_SECONDARY)
            self.stats_ax.set_xticks([]); self.stats_ax.set_yticks([])
            self.stats_ax.spines['right'].set_visible(False); self.stats_ax.spines['top'].set_visible(False)
            self.stats_ax.spines['left'].set_visible(False); self.stats_ax.spines['bottom'].set_visible(False)
        else:
            names = [item[0] for item in stats]
            all_counts = [item[1] for item in stats]
            names.reverse(); all_counts.reverse()

            self.stats_ax.set_xlim(0, max(all_counts) + 1.5)
            bars = self.stats_ax.barh(names, [0] * len(names), height=0.6, color=COLOR_SILVER)

            self.stats_ax.set_title('식당별 누적 선택 횟수', fontsize=16, weight='bold', color=COLOR_SECONDARY)
            self.stats_ax.set_xlabel('선택 횟수', fontsize=12, color=COLOR_SECONDARY)
            self.stats_ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.stats_ax.tick_params(axis='x', colors=COLOR_SECONDARY)
            self.stats_ax.tick_params(axis='y', colors=COLOR_SECONDARY, labelsize=11)
            self.stats_ax.spines['right'].set_visible(False); self.stats_ax.spines['top'].set_visible(False)
            self.stats_ax.spines['left'].set_color('#DDDDDD'); self.stats_ax.spines['bottom'].set_color('#DDDDDD')
            self.stats_ax.grid(axis='x', color='#EAEAEA', linestyle='--', linewidth=0.7)
            self.stats_ax.set_axisbelow(True)

            def animate(frame):
                for i, bar in enumerate(bars):
                    target_width = all_counts[i]
                    current_width = (target_width / frames) * (frame + 1)
                    bar.set_width(current_width)
                
                if frame == frames - 1:
                    unique_sorted_counts = sorted(list(set(all_counts)), reverse=True)

                    ranked_names = []
                    # Iterate in the original order of bars (which is reversed from stats)
                    for i, (name, count) in enumerate(zip(names, all_counts)):
                        # Determine rank
                        try:
                            rank = unique_sorted_counts.index(count) + 1
                        except ValueError:
                            rank = len(unique_sorted_counts) # Should not happen, fallback

                        # Determine prefix and color
                        rank_prefix = f"{rank}위. "
                        bar_color = COLOR_SILVER
                        
                        if rank == 1:
                            bar_color = COLOR_SUCCESS
                            rank_prefix += "👑 "
                        elif rank == 2:
                            bar_color = COLOR_PRIMARY
                            rank_prefix += "🥈 "
                        
                        bars[i].set_color(bar_color)
                        ranked_names.append(f"{rank_prefix}{name}")
                        
                        # Add value labels
                        self.stats_ax.text(count + 0.1, i, f'{int(count)}', va='center', ha='left', color=COLOR_SECONDARY, fontsize=10)

                    self.stats_ax.set_yticklabels(ranked_names)
                return bars

            frames = 30
            self.stats_animation = FuncAnimation(self.stats_fig, animate, frames=frames, interval=20, blit=False, repeat=False)

        self.stats_fig.tight_layout(pad=3.0)
        self.stats_canvas.draw()

    def _setup_settings_tab(self):
        settings_frame = customtkinter.CTkFrame(self.settings_tab, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        settings_card = customtkinter.CTkFrame(settings_frame, fg_color=COLOR_CARD, corner_radius=12)
        settings_card.pack(fill="x", pady=10)

        title = customtkinter.CTkLabel(
            settings_card,
            text="회사명 설정",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        title.pack(pady=(20, 10), padx=20, anchor="w")

        input_frame = customtkinter.CTkFrame(settings_card, fg_color="transparent")
        input_frame.pack(pady=10, padx=20, fill="x")

        self.company_name_entry = customtkinter.CTkEntry(
            input_frame,
            placeholder_text="회사명을 입력하세요",
            corner_radius=8,
            height=45,
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic")
        )
        self.company_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        save_button = customtkinter.CTkButton(
            input_frame,
            text="저장",
            command=self._save_company_name,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BCC",
            width=80,
            height=45,
            font=customtkinter.CTkFont(size=14, weight="bold", family="Malgun Gothic")
        )
        save_button.pack(side="right")

        self.save_status_label = customtkinter.CTkLabel(
            settings_card,
            text="",
            font=customtkinter.CTkFont(size=12, family="Malgun Gothic"),
            text_color=COLOR_SUCCESS
        )
        self.save_status_label.pack(pady=(0, 20), padx=20)

    def _load_company_name(self):
        company_name = self.db.get_setting('company_name')
        if company_name:
            today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
            self.title(f"{company_name} 점심 식당 선택")
            self.title_label.configure(text=f"{company_name} 점심 식당 선택 ({today})")
            if hasattr(self, 'company_name_entry'):
                self.company_name_entry.insert(0, company_name)

    def _save_company_name(self):
        company_name = self.company_name_entry.get().strip()
        if company_name:
            self.db.update_setting('company_name', company_name)
            today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
            self.title(f"{company_name} 점심 식당 선택")
            self.title_label.configure(text=f"{company_name} 점심 식당 선택 ({today})")
            self.save_status_label.configure(text="회사명이 저장되었습니다.")
            self.after(3000, lambda: self.save_status_label.configure(text=""))
        else:
            from tkinter import messagebox
            messagebox.showwarning("입력 오류", "회사명을 입력해주세요.")

    def _setup_history_tab(self):
        # History frame
        history_frame = customtkinter.CTkFrame(self.history_tab, fg_color="transparent")
        history_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # History card
        history_card = customtkinter.CTkFrame(history_frame, fg_color=COLOR_CARD, corner_radius=12)
        history_card.pack(fill="both", expand=True)
        
        # Title
        history_title = customtkinter.CTkLabel(
            history_card, 
            text="최근 선택 기록",
            font=customtkinter.CTkFont(size=22, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        history_title.pack(pady=(30, 20), padx=20, anchor="w")
        
        # History list
        self.history_list = customtkinter.CTkScrollableFrame(
            history_card, 
            height=400,
            fg_color="#FAFAFA"
        )
        self.history_list.pack(padx=20, pady=10, fill="both", expand=True)

    def load_menu_items(self):
        # Clear existing widgets
        for widget in self.exclusion_list_frame.winfo_children():
            widget.destroy()
        self.menu_widgets.clear()
        
        # Load from database
        items = self.db.get_menu_items()
        for item_id, name, is_excluded in items:
            item_frame = customtkinter.CTkFrame(self.exclusion_list_frame, fg_color="transparent", height=50)
            item_frame.pack(fill="x", padx=5, pady=6)
            
            var = customtkinter.BooleanVar(value=is_excluded)
            checkbox = customtkinter.CTkCheckBox(
                item_frame, 
                text="", 
                variable=var,
                command=lambda id=item_id, v=var: self.db.update_exclusion(id, v.get()),
                font=customtkinter.CTkFont(size=16, family="Malgun Gothic"),
                corner_radius=6,
                height=30,
                width=30,
                border_width=2
            )
            checkbox.pack(side="left", padx=(10, 15))
            
            # Add menu name as a separate label for better spacing
            menu_label = customtkinter.CTkLabel(
                item_frame,
                text=name,
                font=customtkinter.CTkFont(size=16, family="Malgun Gothic"),
                anchor="w"
            )
            menu_label.pack(side="left", fill="x", expand=True)
            
            self.menu_widgets[item_id] = (name, var, checkbox)

        self._apply_auto_exclusion()

        # Ensure the scrollable frame is scrolled to the top after loading
        self.exclusion_list_frame._parent_canvas.yview_moveto(0)

    def _apply_auto_exclusion(self):
        last_selected = self.db.get_last_selected_menu()
        if not last_selected:
            self.auto_excluded_label.configure(text="")
            return

        # Find the ID of the last selected menu to update its exclusion status in the DB
        all_items = self.db.get_menu_items()
        item_id_to_exclude = None
        for item_id, name, _ in all_items:
            if name == last_selected:
                item_id_to_exclude = item_id
                break

        if item_id_to_exclude:
            self.db.update_exclusion(item_id_to_exclude, True)
            self.auto_exclude_label.configure(text=f"최근 선택: {last_selected} (자동 제외)", text_color=COLOR_SECONDARY)
        else:
            self.auto_exclude_label.configure(text="")

    def load_history(self):
        # Clear existing history
        for widget in self.history_list.winfo_children():
            widget.destroy()
        
        # Load from database
        history = self.db.get_history()
        for i, (record_id, timestamp, name) in enumerate(history):
            frame = customtkinter.CTkFrame(self.history_list, fg_color=COLOR_CARD, corner_radius=8)
            frame.pack(fill="x", padx=10, pady=5)

            label_text = f"{timestamp}    {name}"
            label = customtkinter.CTkLabel(
                frame, 
                text=label_text, 
                font=customtkinter.CTkFont(size=14, family="Malgun Gothic"),
                anchor="w"
            )
            label.pack(side="left", padx=10, pady=10, expand=True, fill="x")

            delete_button = customtkinter.CTkButton(
                frame,
                text="삭제",
                width=60,
                height=30,
                fg_color="#E74C3C",
                hover_color="#C0392B",
                text_color="white",
                font=customtkinter.CTkFont(size=12, weight="bold", family="Malgun Gothic"),
                command=lambda r_id=record_id: self.delete_history_item(r_id)
            )
            delete_button.pack(side="right", padx=10, pady=5)

    def add_menu_item(self):
        item = self.entry.get().strip()
        if item:
            # Add to database
            item_id = self.db.add_menu_item(item)
            if item_id:
                self.entry.delete(0, "end")
                self.load_menu_items()

    def delete_history_item(self, record_id):
        self.db.delete_history(record_id)
        self.load_history()



    def _run_countdown_logic(self):
        self._update_ui_for_state('countdown')

        duration = int(self.countdown_duration_var.get())
        self._run_countdown(duration)

    def _run_countdown(self, remaining):
        if remaining > 0:
            # Game-like "slot machine" animation for each second
            self._animate_digit(10, remaining) # Animate 10 frames before showing the number
        else:
            self._select_menu()

    def _animate_digit(self, frame, final_digit):
        if frame > 0:
            # Display a random number with a flashy color
            random_digit = random.randint(0, 9)
            random_color = random.choice([COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS, COLOR_SECONDARY])
            self.countdown_label.configure(
                text=str(random_digit),
                font=customtkinter.CTkFont(size=100, weight="bold"),
                text_color=random_color
            )
            self.after(50, self._animate_digit, frame - 1, final_digit)
        else:
            # Show the actual remaining time
            self.countdown_label.configure(
                text=str(final_digit),
                font=customtkinter.CTkFont(size=120, weight="bold"),
                text_color=COLOR_PRIMARY
            )
            # Schedule the next second of the countdown
            self.after(700, self._run_countdown, final_digit - 1)

    def _select_menu(self):
        available_items = []
        all_items = self.db.get_menu_items()
        for item_id, name, is_excluded in all_items:
            if not is_excluded:
                available_items.append((item_id, name))

        if not available_items:
            self.countdown_label.configure(text="선택할 식당이 없습니다!", text_color=COLOR_ACCENT)
            self.reset_selection()
            return

        selected_item_id, selected_name = random.choice(available_items)

        # --- Data-centric update ---
        self.db.record_selection(selected_item_id)
        self.db.reset_all_exclusions()
        self.db.update_exclusion(selected_item_id, True)
        self.load_menu_items() # Reloads UI from DB

        # --- UI Finalization ---
        self.countdown_label.configure(
            text=f"오늘의 식당: {selected_name}",
            font=customtkinter.CTkFont(size=28, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SUCCESS
        )

        # Update history and stats first
        self.load_history()
        self.update_stats_graph()

        self._update_ui_for_state('result')

    def _toggle_exclusion(self, item_id, var):
        # This function is now the single source of truth for manual exclusion changes.
        is_excluded = var.get()
        self.db.update_exclusion(item_id, is_excluded)
        # After any manual change, we should re-evaluate the auto-exclusion label
        self._apply_auto_exclusion()

    def reset_selection(self):
        # --- DB-centric Reset Logic ---
        # 1. Clear all exclusions in the database
        self.db.reset_all_exclusions()
        # 2. Apply auto-exclusion for the last selected item (updates DB)
        self._apply_auto_exclusion()
        # 3. Reload the UI to reflect the new state
        self.load_menu_items()
        # ------------------------------

        # Clear result label
        self.countdown_label.configure(text="")

        self._update_ui_for_state('idle')

    def _update_ui_for_state(self, state: str):
        """Centralized UI state management."""
        if state == 'idle':
            # Show start, hide restart
            self.restart_button.pack_forget()
            self.start_button.pack(fill="x")
            
            # Enable all controls
            self.start_button.configure(state="normal")
            self.duration_menu.configure(state="normal")
            self.entry.configure(state="normal")
            self.add_button.configure(state="normal")
            for _, _, checkbox in self.menu_widgets.values():
                checkbox.configure(state="normal")

        elif state == 'countdown':
            # Disable all controls
            self.start_button.configure(state="disabled")
            self.duration_menu.configure(state="disabled")
            self.entry.configure(state="disabled")
            self.add_button.configure(state="disabled")
            for _, _, checkbox in self.menu_widgets.values():
                checkbox.configure(state="disabled")

        elif state == 'result':
            # Show restart, hide start
            self.start_button.pack_forget()
            self.restart_button.pack(fill="x")

            # Keep controls disabled
            self.duration_menu.configure(state="disabled")
            self.entry.configure(state="disabled")
            self.add_button.configure(state="disabled")
            # Checkboxes are already disabled from 'countdown' state

        self.update_idletasks()

    def on_closing(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = LunchPickerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
