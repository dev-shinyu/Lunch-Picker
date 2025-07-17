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

# Localization texts
TEXTS = {
    'ko': {
        'title': '{meal} 선택',
        'subtitle': '오늘의 {meal}을 추천해드립니다',
        'tab_menu': '{meal} 관리',
        'tab_history': '선택 기록',
        'tab_stats': '통계',
        'tab_settings': '설정',
        'add_label': '{meal} 추가',
        'entry_placeholder': '새 {meal} 이름을 입력하세요',
        'add_button': '추가',
        'menu_list': '{meal} 목록',
        'menu_list_subtitle': '(선택항목은 선택 대상에서 제외)',
        'selection_title': '{meal} 선택',
        'duration_label': '카운트다운 시간(초):',
        'start_button': '메뉴 추천 시작!',
        'restart_button': '추첨 재시작',
        'idle_label': '오늘 {meal}은 무엇을 먹을까요?',
        'result_title': '오늘의 선택은',
        'history_title': '최근 선택 기록',
        'history_empty': '선택 기록이 없습니다.',
        'delete_history': '삭제',
        'no_items': '추천할 메뉴가 없습니다.',
        'recent_selection': '최근 선택: {name} (자동 제외)',
        'stats_title': '누적 선택 회수',
        'stats_xlabel': '누적 선택 횟수',
        'stats_error': '선택 기록이 없습니다.',
        'settings_title': '이름/사명',
        'settings_placeholder': '이름/사명을 입력하세요',
        'save_button': '저장',
        'save_success': '이름/사명이 저장되었습니다.',
        'settings_warning_title': '입력 오류',
        'settings_warning_msg': '이름/사명을 입력해주세요.'
    },
    'en': {
        'title': '{meal} Picker',
        'subtitle': 'Recommend today’s {meal}',
        'tab_menu': 'Manage {meal}s',
        'tab_history': 'Selection History',
        'tab_stats': 'Statistics',
        'tab_settings': 'Settings',
        'add_label': 'Add {meal}',
        'entry_placeholder': 'Enter {meal} name',
        'add_button': 'Add',
        'menu_list': '{meal} List',
        'menu_list_subtitle': '(Selected items will be excluded)',
        'selection_title': '{meal} Selection',
        'duration_label': 'Countdown Time (sec):',
        'start_button': 'Start Recommendation!',
        'restart_button': 'Restart Selection',
        'idle_label': 'What shall we eat for {meal} today?',
        'result_title': 'Today’s Selection',
        'history_title': 'Recent Selections',
        'history_empty': 'No selection records.',
        'delete_history': 'Delete',
        'no_items': 'No menu to recommend.',
        'recent_selection': 'Recent Selection: {name} (Auto excluded)',
        'stats_title': 'Cumulative Selection Count',
        'stats_xlabel': 'Cumulative Selection Count',
        'stats_error': 'No selection records.',
        'settings_title': 'Name/Company',
        'settings_placeholder': 'Enter name/company',
        'save_button': 'Save',
        'save_success': 'Name/Company saved.',
        'settings_warning_title': 'Input Error',
        'settings_warning_msg': 'Please enter name/company.'
    }
}

# Premium color scheme

MEAL_LABELS = {
    'ko': {'breakfast': '아침', 'lunch': '점심', 'dinner': '저녁'},
    'en': {'breakfast': 'Breakfast', 'lunch': 'Lunch', 'dinner': 'Dinner'}
}

COLOR_PRIMARY = "#4A90E2"
COLOR_SECONDARY = "#34495E"
COLOR_ACCENT = "#E74C3C"
COLOR_SUCCESS = "#2ECC71"
COLOR_SILVER = "#BDC3C7"  # Silver color for 2nd place
COLOR_BG = "#ECF0F1"
COLOR_BG_LIGHT = "#F8F9FA"  # Light background for frames
COLOR_CARD = "#FFFFFF"

# Pastel colors for meal tabs and badges
PASTEL_COLORS = {
    'breakfast': {'unselected': '#FFFDE7', 'selected': '#FFF9C4'},
    'lunch': {'unselected': '#C8E6C9', 'selected': '#A5D6A7'},
    'dinner': {'unselected': '#BBDEFB', 'selected': '#90CAF9'},
}  

# Pastel text colors for meal tabs and badges
PASTEL_TEXT_COLORS = {
    'breakfast': '#333333',  # Dark text for contrast
    'lunch': 'white',
    'dinner': 'white',
}

# Set appearance
customtkinter.set_appearance_mode("Light")
customtkinter.set_default_color_theme("blue")


class LunchPickerApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # Default language
        self.lang = 'ko'
        # Default meal
        self.meal = 'lunch'

        # Initialize database
        self.db = MenuDB()
        # Track the last selected menu name for UI updates
        self.last_selected_name: str | None = None

        # Configure window
        self.title(TEXTS[self.lang]['title'])
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(fg_color=COLOR_BG)

        # Get today's date
        self.today = datetime.datetime.now().strftime("%Y년 %m월 %d일")

        # Create header
        self.header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10), padx=20, fill="x")

        # Create title label with date
        self.title_label = customtkinter.CTkLabel(
            self,
            text=f"{TEXTS[self.lang]['title']} ({self.today})",
            font=customtkinter.CTkFont(size=28, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.title_label.pack(pady=(30, 0))

        # Create subtitle label
        self.subtitle_label = customtkinter.CTkLabel(
            self.header_frame,
            text=TEXTS[self.lang]['subtitle'],
            font=customtkinter.CTkFont(size=16, family="Malgun Gothic"),
            text_color="#7F8C8D"
        )
        self.subtitle_label.pack()
        # Language toggle
        self.lang_var = tk.StringVar(value='한글')
        self.lang_toggle = customtkinter.CTkSegmentedButton(self.header_frame, values=['한글','ENG'], variable=self.lang_var, command=self._on_language_change)
        self.lang_toggle.pack(side='right', padx=(0,20))
        # Meal selector
        self.meal_var = tk.StringVar(value=MEAL_LABELS[self.lang]['lunch'])
        self.meal_toggle = customtkinter.CTkSegmentedButton(
            self.header_frame,
            values=[MEAL_LABELS[self.lang][m] for m in ['breakfast','lunch','dinner']],
            variable=self.meal_var,
            command=self._on_meal_change
        )
        self.meal_toggle.pack(side='right', padx=(0,20))

        # Create main content frame
        self.content_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Create tab view with larger tabs
        self.tab_view = customtkinter.CTkTabview(
            self.content_frame,
            segmented_button_fg_color=PASTEL_COLORS[self.meal]['unselected'],
            segmented_button_selected_color=PASTEL_COLORS[self.meal]['selected'],
            segmented_button_selected_hover_color=PASTEL_COLORS[self.meal]['selected'],
            text_color=PASTEL_TEXT_COLORS[self.meal],
            corner_radius=10,
            width=800,
            height=45
        )
        self.tab_view._segmented_button.configure(font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"))
        self.tab_view.configure(command=self._on_tab_change)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs with padding
        self.menu_tab = self.tab_view.add(f"  {TEXTS[self.lang]['tab_menu'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ")
        self.history_tab = self.tab_view.add(f"  {TEXTS[self.lang]['tab_history'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ")
        self.stats_tab = self.tab_view.add(f"  {TEXTS[self.lang]['tab_stats'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ")
        self.settings_tab = self.tab_view.add(f"  {TEXTS[self.lang]['tab_settings'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ")

        # --- Initialization Order --- 
        # 1. Setup all UI tabs to create the widgets
        self._setup_menu_tab()
        self._setup_history_tab()
        self._setup_stats_tab()
        self._setup_settings_tab()

        self.stats_animation = None # To hold the animation object

        # 2. Load data and configure the widgets
        self._load_company_name()
        self.load_menu_items()  # This calls _apply_auto_exclusion internally
        self.load_history()
        
        # 3. Set the final initial UI state
        self._update_ui_for_state('idle')
        # Refresh UI texts based on language
        self._refresh_ui_texts()

    def _on_tab_change(self, tab_name=None):
        # This method is called when the tab is changed.
        current_tab = self.tab_view.get()

        # Stop any running animation when changing tabs to prevent resource leaks
        if self.stats_animation and self.stats_animation.event_source:
            self.stats_animation.event_source.stop()
            self.stats_animation = None

        # Localized tab change handling
        label = current_tab.strip()
        if label == TEXTS[self.lang]['tab_stats']:
            self.update_stats_graph()
        elif label == TEXTS[self.lang]['tab_history']:
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
        self.input_title = customtkinter.CTkLabel(
            left_panel,
            text=TEXTS[self.lang]['add_label'].format(meal=MEAL_LABELS[self.lang][self.meal]),
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.input_title.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Input field
        input_frame = customtkinter.CTkFrame(left_panel, fg_color="transparent")
        input_frame.pack(pady=10, padx=20, fill="x")
        
        self.entry = customtkinter.CTkEntry(
            input_frame, 
            placeholder_text=TEXTS[self.lang]['entry_placeholder'].format(meal=MEAL_LABELS[self.lang][self.meal]),
            corner_radius=8,
            height=45,
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic")
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.add_button = customtkinter.CTkButton(
            input_frame, 
            text=TEXTS[self.lang]['add_button'],
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
        self.exclusion_title = customtkinter.CTkLabel(
            left_panel,
            text=TEXTS[self.lang]['menu_list'].format(meal=MEAL_LABELS[self.lang][self.meal]),
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.exclusion_title.pack(pady=(0, 5), padx=20, anchor="w")

        self.exclusion_subtitle = customtkinter.CTkLabel(
            left_panel,
            text=TEXTS[self.lang]['menu_list_subtitle'],
            font=customtkinter.CTkFont(size=12, family="Malgun Gothic"),
            text_color="#7F8C8D"
        )
        self.exclusion_subtitle.pack(pady=(0, 10), padx=20, anchor="w")

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
        self.selection_title = customtkinter.CTkLabel(
            right_panel,
            text=TEXTS[self.lang]['selection_title'].format(meal=MEAL_LABELS[self.lang][self.meal]),
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.selection_title.pack(pady=(20, 10), padx=20, anchor="w")

        # Countdown duration selector
        duration_frame = customtkinter.CTkFrame(right_panel, fg_color="transparent")
        duration_frame.pack(pady=10, padx=20, fill="x")

        self.duration_label = customtkinter.CTkLabel(
            duration_frame, 
            text=TEXTS[self.lang]['duration_label'], 
            font=customtkinter.CTkFont(size=14, family="Malgun Gothic")
        )
        self.duration_label.pack(side="left")

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
            text=TEXTS[self.lang]['start_button'], 
            command=self._run_countdown_logic,
            fg_color=COLOR_SUCCESS,
            hover_color="#27AE60",
            height=60,
            text_color=PASTEL_TEXT_COLORS[self.meal],
            text_color_disabled="white",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic")
        )
        self.start_button.pack(fill="x")

        self.restart_button = customtkinter.CTkButton(
            button_frame, 
            text=TEXTS[self.lang]['restart_button'], 
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
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(1, weight=1)

        self.countdown_label = customtkinter.CTkLabel(
            self.result_frame,
            text="",
            font=customtkinter.CTkFont(size=18, family="Malgun Gothic"),
            wraplength=300
        )
        self.countdown_label.pack(expand=True)

        # Labels for the final result (initially hidden)
        self.result_title_label = customtkinter.CTkLabel(
            self.result_frame,
            text=TEXTS[self.lang]['result_title'],
            font=customtkinter.CTkFont(size=16, family="Malgun Gothic"),
            text_color="#95a5a6"
        )
        # Hidden until result state

        self.result_label = customtkinter.CTkLabel(
            self.result_frame,
            text="",
            font=customtkinter.CTkFont(size=36, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SUCCESS
        )
        # Hidden until result state

    def _setup_stats_tab(self):
        stats_frame = customtkinter.CTkFrame(self.stats_tab, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Initialize statistics canvas
        self.stats_fig = plt.figure(figsize=(8, 6), dpi=100, facecolor=COLOR_BG_LIGHT)
        self.stats_ax = self.stats_fig.add_subplot(111, facecolor=COLOR_BG_LIGHT)
        self.stats_canvas = FigureCanvasTkAgg(self.stats_fig, master=stats_frame)
        self.stats_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_stats_graph(self):
        # Stop any existing animation to prevent conflicts
        if hasattr(self, 'stats_animation') and self.stats_animation and self.stats_animation.event_source:
            self.stats_animation.event_source.stop()

        self.stats_ax.clear()
        stats = self.db.get_selection_stats()

        if not stats:
            # Reset axes to full canvas for proper centering when empty
            self.stats_ax.set_position([0, 0, 1, 1])
            self.stats_ax.text(0.5, 0.5, TEXTS[self.lang]['stats_error'], ha='center', va='center', fontsize=18, color=COLOR_SECONDARY, transform=self.stats_ax.transAxes)
            self.stats_ax.set_xticks([]); self.stats_ax.set_yticks([])
            self.stats_ax.spines['right'].set_visible(False); self.stats_ax.spines['top'].set_visible(False)
            self.stats_ax.spines['left'].set_visible(False); self.stats_ax.spines['bottom'].set_visible(False)
            self.stats_canvas.draw()
            return

        # 데이터 정렬 및 순위, 색상, 이름 준비
        stats.sort(key=lambda x: x[1])
        names = [item[0] for item in stats]
        all_counts = [item[1] for item in stats]
        y_pos = range(len(names))

        unique_sorted_counts = sorted(list(set(all_counts)), reverse=True)
        colors = []
        ranked_names = []
        for name, count in zip(names, all_counts):
            rank = unique_sorted_counts.index(count) + 1
            emoji, color = "", COLOR_SILVER
            if rank == 1:
                color, emoji = COLOR_SUCCESS, "👑 "
            elif rank == 2:
                color, emoji = COLOR_PRIMARY, "🥈 "
            colors.append(color)
            # Localize rank suffix
            if self.lang == 'ko':
                label_rank = f'{rank}위'
            else:
                # English ordinal suffix logic
                if rank % 100 in (11, 12, 13):
                    suffix = 'th'
                elif rank % 10 == 1:
                    suffix = 'st'
                elif rank % 10 == 2:
                    suffix = 'nd'
                elif rank % 10 == 3:
                    suffix = 'rd'
                else:
                    suffix = 'th'
                label_rank = f'{rank}{suffix}'
            ranked_names.append(f'{emoji}{label_rank}. {name}')

        # 그래프 기본 틀과 스타일 설정
        self.stats_ax.set_title(TEXTS[self.lang]['stats_title'], fontsize=16, weight='bold', color=COLOR_SECONDARY)
        self.stats_ax.set_xlabel(TEXTS[self.lang]['stats_xlabel'], fontsize=12, color=COLOR_SECONDARY)
        self.stats_ax.set_xlim(0, max(all_counts) + 1.5)
        self.stats_ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.stats_ax.tick_params(axis='x', colors=COLOR_SECONDARY)
        self.stats_ax.tick_params(axis='y', colors=COLOR_SECONDARY, labelsize=11)
        self.stats_ax.spines['right'].set_visible(False)
        self.stats_ax.spines['top'].set_visible(False)
        self.stats_ax.spines['left'].set_color('#DDDDDD')
        self.stats_ax.spines['bottom'].set_color('#DDDDDD')
        self.stats_ax.grid(axis='x', color='#EAEAEA', linestyle='--', linewidth=0.7)
        self.stats_ax.set_axisbelow(True)
        self.stats_fig.subplots_adjust(left=0.3, right=0.95, top=0.9, bottom=0.15)

        # y축 레이블 설정 (폰트 처리 포함)
        self.stats_ax.set_yticks(y_pos)
        original_font_family = plt.rcParams['font.family']
        try:
            plt.rcParams['font.family'] = ['Malgun Gothic', 'Segoe UI Emoji']
            self.stats_ax.set_yticklabels(ranked_names)
        finally:
            plt.rcParams['font.family'] = original_font_family

        # 애니메이션을 위한 막대그래프 초기화 (너비 0)
        bars = self.stats_ax.barh(y_pos, [0] * len(all_counts), height=0.6, align='center', color=colors)

        # 애니메이션 함수 정의
        def animate(frame):
            # 각 프레임마다 막대의 너비를 점진적으로 증가
            for i, bar in enumerate(bars):
                target_width = all_counts[i]
                current_width = target_width * (frame / 100.0) # 100 프레임에 걸쳐 증가
                bar.set_width(current_width)
            return bars

        # 애니메이션 실행
        self.stats_animation = FuncAnimation(
            self.stats_fig, 
            animate, 
            frames=101, # 0부터 100까지
            interval=15, # 15ms 간격
            blit=True, # 블리팅으로 성능 최적화
            repeat=False # 반복 안 함
        )

        # 애니메이션이 끝난 후, 막대 옆에 최종 횟수 표시
        def on_animation_end():
            # 애니메이션이 끝난 후 최종 값을 막대 옆에 텍스트로 표시
            for i, count in enumerate(all_counts):
                if self.stats_ax.get_xlim()[1] > count + 0.1: # 그래프 범위 내에 있을 때만 표시
                    self.stats_ax.text(count + 0.1, i, f'{int(count)}', va='center', ha='left', color=COLOR_SECONDARY, fontsize=10)
            self.stats_canvas.draw_idle() # 최종 상태를 다시 그림
        
        # 애니메이션 총 시간 이후에 콜백 실행 (약간의 지연 추가)
        self.after(int(101 * 15 + 50), on_animation_end)
        
        self.stats_canvas.draw()

    def _setup_settings_tab(self):
        settings_frame = customtkinter.CTkFrame(self.settings_tab, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        settings_card = customtkinter.CTkFrame(settings_frame, fg_color=COLOR_CARD, corner_radius=12)
        settings_card.pack(fill="x", pady=10)

        self.settings_title = customtkinter.CTkLabel(
            settings_card,
            text="회사명 설정",
            font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.settings_title.pack(pady=(20, 10), padx=20, anchor="w")

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

        self.save_button = customtkinter.CTkButton(
            input_frame,
            text="저장",
            command=self._save_company_name,
            fg_color=COLOR_PRIMARY,
            hover_color="#3A7BCC",
            width=80,
            height=45,
            font=customtkinter.CTkFont(size=14, weight="bold", family="Malgun Gothic")
        )
        self.save_button.pack(side="right")

        self.save_status_label = customtkinter.CTkLabel(
            settings_card,
            text="",
            font=customtkinter.CTkFont(size=12, family="Malgun Gothic"),
            text_color=COLOR_SUCCESS
        )
        self.save_status_label.pack(pady=(0, 20), padx=20)

    def _load_company_name(self):
        # Load and display company name with dynamic meal
        company_name = self.db.get_setting('company_name')
        if company_name:
            today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
            self.title(f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])}")
            self.title_label.configure(text=f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])} ({today})")
            if hasattr(self, 'company_name_entry'):
                self.company_name_entry.insert(0, company_name)

    def _save_company_name(self):
        # Save and display company name with dynamic meal
        company_name = self.company_name_entry.get().strip()
        if company_name:
            self.db.update_setting('company_name', company_name)
            today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
            self.title(f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])}")
            self.title_label.configure(text=f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])} ({today})")
            self.save_status_label.configure(text=TEXTS[self.lang]['save_success'])
            self.after(3000, lambda: self.save_status_label.configure(text=""))
        else:
            from tkinter import messagebox
            messagebox.showwarning(TEXTS[self.lang]['settings_warning_title'], TEXTS[self.lang]['settings_warning_msg'])

    def _setup_history_tab(self):
        # History frame
        history_frame = customtkinter.CTkFrame(self.history_tab, fg_color="transparent")
        history_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # History card
        history_card = customtkinter.CTkFrame(history_frame, fg_color=COLOR_CARD, corner_radius=12)
        history_card.pack(fill="both", expand=True)
        
        # Title
        self.history_title = customtkinter.CTkLabel(
            history_card, 
            text="최근 선택 기록",
            font=customtkinter.CTkFont(size=22, weight="bold", family="Malgun Gothic"),
            text_color=COLOR_SECONDARY
        )
        self.history_title.pack(pady=(30, 20), padx=20, anchor="w")
        
        # History list
        self.history_list = customtkinter.CTkScrollableFrame(
            history_card, 
            height=400,
            fg_color="#FAFAFA"
        )
        self.history_list.pack(padx=20, pady=10, fill="both", expand=True)

    def load_menu_items(self, last_selected_name: str | None = None):
        # Clear existing widgets
        for widget in self.exclusion_list_frame.winfo_children():
            widget.destroy()
        self.menu_widgets.clear()
        
        # Load from database
        items = self.db.get_menu_items()
        if not items:
            no_items_label = customtkinter.CTkLabel(
                self.exclusion_list_frame,
                text="등록된 식당이 없습니다. 설정 탭에서 추가해주세요.",
                font=customtkinter.CTkFont(size=14, family="Malgun Gothic"),
                text_color="#95a5a6"
            )
            no_items_label.pack(pady=20)
            self.auto_exclude_label.pack_forget() # Ensure label is hidden
            return

        for item_id, name, is_excluded in items:
            item_frame = customtkinter.CTkFrame(self.exclusion_list_frame, fg_color="transparent", height=50)
            item_frame.pack(fill="x", padx=5, pady=6)

            var = customtkinter.BooleanVar(value=is_excluded)
            checkbox = customtkinter.CTkCheckBox(
                item_frame,
                text="",
                variable=var,
                command=lambda id=item_id, v=var: self._toggle_exclusion(id, v),
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

        # --- Update Auto-Exclusion Label --- 
        # Prioritize the name passed directly after selection, otherwise query DB.
        # Determine the name to display: prefer parameter, then stored attribute, then DB
        if last_selected_name is not None:
            name_to_display = last_selected_name
        elif self.last_selected_name is not None:
            name_to_display = self.last_selected_name
        else:
            name_to_display = self.db.get_last_selected_menu()
        # Persist the last selected name for future UI refreshes
        self.last_selected_name = name_to_display

        if name_to_display:
            self.auto_exclude_label.configure(text=TEXTS[self.lang]['recent_selection'].format(name=name_to_display))
            # Show label above list
            self.auto_exclude_label.pack(pady=(0, 5), padx=20, fill="x")
            # Re-pack the list frame to ensure it stays below the label
            self.exclusion_list_frame.pack_forget()
            self.exclusion_list_frame.pack(padx=20, pady=5, fill="both", expand=True)
        else:
            self.auto_exclude_label.pack_forget()

        # Ensure the scrollable frame is scrolled to the top after loading
        self.exclusion_list_frame._parent_canvas.yview_moveto(0)

    def _apply_auto_exclusion(self):
        """Automatically exclude the last selected menu item in the database."""
        last_name = self.db.get_last_selected_menu()
        if last_name:
            for item_id, name, _ in self.db.get_menu_items():
                if name == last_name:
                    self.db.update_exclusion(item_id, True)
                    break



    def load_history(self):
        # Clear existing history
        for widget in self.history_list.winfo_children():
            widget.destroy()
        
        # Load from database
        history = self.db.get_history()
        if not history:
            no_history_label = customtkinter.CTkLabel(
                self.history_list,
                text=TEXTS[self.lang]['history_empty'],
                font=customtkinter.CTkFont(size=14, family="Malgun Gothic"),
                text_color="#95a5a6"
            )
            no_history_label.pack(pady=20)
            return
        for i, (record_id, timestamp, meal_type, name) in enumerate(history):
            frame = customtkinter.CTkFrame(self.history_list, fg_color=COLOR_CARD, corner_radius=8)
            frame.pack(fill="x", padx=10, pady=5)
            # Meal badge 표시
            badge = customtkinter.CTkLabel(
                master=frame,
                text=MEAL_LABELS[self.lang][meal_type],

                fg_color=PASTEL_COLORS[meal_type]['selected'],
                text_color=PASTEL_TEXT_COLORS[meal_type],
                corner_radius=6,
                font=customtkinter.CTkFont(size=12, weight="bold", family="Malgun Gothic")
            )
            badge.pack(side="left", padx=(10, 5), pady=10)

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
                text=TEXTS[self.lang]['delete_history'],
                width=60,
                height=30,
                fg_color="#E74C3C",
                hover_color="#C0392B",
                text_color=PASTEL_TEXT_COLORS[self.meal],
                font=customtkinter.CTkFont(size=12, weight="bold", family="Malgun Gothic"),
                command=lambda r_id=record_id: self.delete_history_item(r_id)
            )
            delete_button.pack(side="right", padx=10, pady=5)

    def add_menu_item(self):
        item = self.entry.get().strip()
        if item:
            # Add to database
            self.db.add_menu_item(item)

            # Clear the entry field and reload menu items, preserving the last selection
            self.entry.delete(0, "end")
            current_last_selected = self.last_selected_name
            self.load_menu_items(last_selected_name=current_last_selected)

    def delete_menu_item(self, item_id):
        self.db.delete_menu_item(item_id)
        # Preserve the last selection state when reloading the list
        current_last_selected = self.last_selected_name
        self.load_menu_items(last_selected_name=current_last_selected)

    def delete_history_item(self, record_id):
        self.db.delete_history(record_id)
        self.load_history()

# ... (rest of the code remains the same)


    def _run_countdown_logic(self):
        self._update_ui_for_state('countdown')

        duration = int(self.countdown_duration_var.get())
        self._run_countdown(duration)

    def _run_countdown(self, remaining):
        if remaining > 0:
            # Game-like "slot machine" animation for each second
            self._animate_digit(10, remaining) # Animate 10 frames before showing the number
        else:
            self.after(500, self._select_menu)

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
                text_color=COLOR_SECONDARY
            )
            # Proceed to the next second in the countdown
            self.after(1000, self._run_countdown, final_digit - 1)

    def _select_menu(self):
        all_items = self.db.get_menu_items()
        available_items = [(id, name) for id, name, excluded in all_items if not excluded]

        if not available_items:
            self.countdown_label.configure(
                text=TEXTS[self.lang]['no_items'],
                font=customtkinter.CTkFont(size=24, weight="bold", family="Malgun Gothic"),
                text_color=COLOR_WARNING
            )
            self._update_ui_for_state('idle')
            return

        selected_item_id, selected_name = random.choice(available_items)

        # --- Step 1: Update Database ---
        self.db.record_selection(selected_item_id, self.meal)
        self.db.reset_all_exclusions()
        self.db.update_exclusion(selected_item_id, True)

        # --- Step 2: Critical UI Update (with forced rendering) ---
        # Pass the result directly to avoid DB race conditions on first selection.
        self.load_menu_items(last_selected_name=selected_name)
        self.update_idletasks()

        # --- Step 3: Update other UI components ---
        self.load_history()
        if self.tab_view.get() == "통계":
            self.update_stats_graph()

        # --- Step 4: Display the final result ---
        self.countdown_label.pack_forget()
        self.result_title_label.pack(pady=(35,2))
        self.result_label.configure(text=selected_name)
        self.result_label.pack(pady=(0,20))

        # --- Step 5: Set final app state ---
        self._update_ui_for_state('result')

    def _toggle_exclusion(self, item_id, var):
        # This function is now the single source of truth for manual exclusion changes.
        is_excluded = var.get()
        self.db.update_exclusion(item_id, is_excluded)
        # Preserve the last selection state when reloading the list
        current_last_selected = self.last_selected_name
        self.load_menu_items(last_selected_name=current_last_selected)
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

        # Hide result labels and show the idle label
        self.result_title_label.pack_forget()
        self.result_label.pack_forget()
        self.countdown_label.pack(expand=True)

        self._update_ui_for_state('idle')

    def _update_ui_for_state(self, state: str):
        """Centralized UI state management."""
        if state == 'idle':
            # Hide result labels
            self.result_title_label.pack_forget()
            self.result_label.pack_forget()
            # Show start, hide restart
            self.restart_button.pack_forget()
            self.start_button.pack(fill="x")
            
            self.countdown_label.configure(
                text=TEXTS[self.lang]['idle_label'].format(meal=MEAL_LABELS[self.lang][self.meal]),
                font=customtkinter.CTkFont(size=22, weight="bold", family="Malgun Gothic"),
                text_color=COLOR_SECONDARY
            )
            
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


    def _on_language_change(self, choice):
        """Handle language toggle: hide content, rebuild UI, refresh texts smoothly."""
        # Hide the entire content area
        self.content_frame.pack_forget()
        self.lang = 'ko' if choice == '한글' else 'en'
        self._rebuild_tabview()
        self._refresh_ui_texts()
        # Show updated content
        self.content_frame.pack(padx=20, pady=10, fill="both", expand=True)

    def _on_meal_change(self, choice):
        """Handle meal toggle: hide content, rebuild UI, refresh texts smoothly."""
        # Hide the entire content area
        self.content_frame.pack_forget()
        for key, label in MEAL_LABELS[self.lang].items():
            if label == choice:
                self.meal = key
                break
        self._rebuild_tabview()
        self._refresh_ui_texts()
        # Show updated content
        self.content_frame.pack(padx=20, pady=10, fill="both", expand=True)



    def _rebuild_tabview(self):
        # Rebuild tabview with the new language labels
        old_tab = self.tab_view.get()
        old_values = self.tab_view._segmented_button.cget("values")
        # Remove old tabview
        self.tab_view.destroy()
        # Create new tabview
        self.tab_view = customtkinter.CTkTabview(
            self.content_frame,
            segmented_button_fg_color=PASTEL_COLORS[self.meal]['unselected'],
            segmented_button_selected_color=PASTEL_COLORS[self.meal]['selected'],
            segmented_button_selected_hover_color=PASTEL_COLORS[self.meal]['selected'],
            text_color=PASTEL_TEXT_COLORS[self.meal],
            corner_radius=10,
            width=800,
            height=45
        )
        self.tab_view._segmented_button.configure(font=customtkinter.CTkFont(size=18, weight="bold", family="Malgun Gothic"))
        self.tab_view.configure(command=self._on_tab_change)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)
        # Add tabs
        labels = [
            f"  {TEXTS[self.lang]['tab_menu'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ",
            f"  {TEXTS[self.lang]['tab_history'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ",
            f"  {TEXTS[self.lang]['tab_stats'].format(meal=MEAL_LABELS[self.lang][self.meal])}  ",
            f"  {TEXTS[self.lang]['tab_settings'].format(meal=MEAL_LABELS[self.lang][self.meal])}  "
        ]
        self.menu_tab = self.tab_view.add(labels[0])
        self.history_tab = self.tab_view.add(labels[1])
        self.stats_tab = self.tab_view.add(labels[2])
        self.settings_tab = self.tab_view.add(labels[3])
        # Setup tabs content
        self._setup_menu_tab()
        self._setup_history_tab()
        self._setup_stats_tab()
        self._setup_settings_tab()
        # Reload data
        self.load_menu_items()
        self.load_history()
        # Restore tab selection
        idx = list(old_values).index(old_tab) if old_tab in old_values else 0
        self.tab_view.set(labels[idx])

    def _refresh_ui_texts(self):
        # Update header texts
        self.title_label.configure(text=f"{TEXTS[self.lang]['title']} ({self.today})")
        self.subtitle_label.configure(text=TEXTS[self.lang]['subtitle'])


    def _refresh_ui_texts(self):
        # Determine date string by language
        now = datetime.datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일") if self.lang == 'ko' else now.strftime("%Y-%m-%d")
        # Determine date string by language
        now = datetime.datetime.now()
        date_str = now.strftime("%Y년 %m월 %d일") if self.lang == 'ko' else now.strftime("%Y-%m-%d")
        # Refresh window title and header label
        company_name = self.db.get_setting('company_name')
        if company_name:
            # include company name
            self.title(f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])}")
            self.title_label.configure(text=f"{company_name} {TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])} ({date_str})")
        else:
            self.title(TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal]))
            self.title_label.configure(text=f"{TEXTS[self.lang]['title'].format(meal=MEAL_LABELS[self.lang][self.meal])} ({date_str})")
        # Update subtitle label
        self.subtitle_label.configure(text=TEXTS[self.lang]['subtitle'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        # Update meal toggle values
        meal_values = [MEAL_LABELS[self.lang][m] for m in ['breakfast','lunch','dinner']]
        self.meal_toggle.configure(values=meal_values)
        self.meal_var.set(MEAL_LABELS[self.lang][self.meal])
        # Update tab labels and maintain frames
        sec_btn = self.tab_view._segmented_button
        keys = ['tab_menu', 'tab_history', 'tab_stats', 'tab_settings']
        # preserve current tab
        old_current = self.tab_view.get()
        # retrieve current tab labels
        old_values = sec_btn.cget("values")
        # compute new tab labels
        new_labels = [f"  {TEXTS[self.lang][k].format(meal=MEAL_LABELS[self.lang][self.meal])}  " for k in keys]
        # update segmented button values
        sec_btn.configure(values=new_labels)
        # preserve current tab selection
        current = self.tab_view.get()
        if current in old_values:
            idx = old_values.index(current)
            self.tab_view.set(new_labels[idx])
        # Update input section
        self.input_title.configure(text=TEXTS[self.lang]['add_label'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        self.entry.configure(placeholder_text=TEXTS[self.lang]['entry_placeholder'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        self.add_button.configure(text=TEXTS[self.lang]['add_button'])
        # Update menu list section
        self.exclusion_title.configure(text=TEXTS[self.lang]['menu_list'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        self.exclusion_subtitle.configure(text=TEXTS[self.lang]['menu_list_subtitle'])
        # Update selection section
        self.selection_title.configure(text=TEXTS[self.lang]['selection_title'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        self.duration_label.configure(text=TEXTS[self.lang]['duration_label'])
        self.start_button.configure(text=TEXTS[self.lang]['start_button'])
        self.restart_button.configure(text=TEXTS[self.lang]['restart_button'])
        self.countdown_label.configure(text=TEXTS[self.lang]['idle_label'].format(meal=MEAL_LABELS[self.lang][self.meal]))
        self.result_title_label.configure(text=TEXTS[self.lang]['result_title'])
        # Update history section
        self.history_title.configure(text=TEXTS[self.lang]['history_title'])
        # Update settings section
        self.settings_title.configure(text=TEXTS[self.lang]['settings_title'])
        self.company_name_entry.configure(placeholder_text=TEXTS[self.lang]['settings_placeholder'])
        self.save_button.configure(text=TEXTS[self.lang]['save_button'])

if __name__ == "__main__":

    app = LunchPickerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
