import customtkinter as ctk
from tkinter import messagebox, filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# =====================================================================
# 🌍 СЛОВАРЬ ПЕРЕВОДОВ (Для красивых названий полей)
# =====================================================================
TRANSLATION_DICT = {
    "ExplanatoryNoteNumber": "Номер ПЗ",
    "ExplanatoryNoteYear": "Год выпуска",
    "ExplanatoryNoteModifications": "Внесение изменений",
    "IssueAuthor": "Авторы проекта",
    "Signers": "Подписанты",
    "Developer": "Застройщик (Тех. заказчик)",
    "UsedNorms": "Используемые нормы",
    "ProjectDecisionDocuments": "Проектные решения",
    "ProjectInitialDocuments": "Исходно-разрешительные документы",
    "EngineeringSurveyDocuments": "Отчеты по инженерным изысканиям",
    "NonIndustrialObject": "Непроизводственный объект",
    "IndustrialObject": "Производственный объект",
    "LinearObject": "Линейный объект",
    "DesignerAssurance": "Заверения проектировщика",
    "DocumentName": "Наименование документа",
    "OrganizationName": "Полное наименование организации",
    "INN": "ИНН",
    "OGRN": "ОГРН"
}

# =====================================================================
# 🛠 ПРАВИЛА ОБЪЕДИНЕНИЯ ВКЛАДОК (Routing Rules)
# =====================================================================
CUSTOM_TAB_GROUPS = {
    # Эти сложные теги пойдут во вкладку "Общие данные" (вместе с простыми полями)
    "ExplanatoryNoteModifications": "📌 Общие данные",
    
    # Объединяем проектировщиков, авторов и подписантов
    "IssueAuthor": "👷 Генеральный проектировщик",
    "Signers": "👷 Генеральный проектировщик",
    "DesignerAssurance": "👷 Генеральный проектировщик",
    
    # Объединяем документацию
    "ProjectDecisionDocuments": "📑 Исходно-разрешительная документация",
    "ProjectInitialDocuments": "📑 Исходно-разрешительная документация",
}
# =====================================================================

class UniversalXMLGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("XML Генератор (с умным объединением вкладок)")
        self.geometry("900x750")

        self.xml_tree = None
        self.xml_root = None
        self.entry_mappings = [] 
        
        self.tab_buttons = {} 
        self.tab_frames = {}  
        self.active_tab_id = None 

        self.setup_ui()

    def setup_ui(self):
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            self.top_frame, text="📂 1. Загрузить XML Шаблон", 
            command=self.load_xml_template, fg_color="#d35400", hover_color="#e67e22"
        ).pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            self.top_frame, text="💾 2. Сохранить XML", 
            command=self.save_xml, fg_color="green", hover_color="darkgreen", state="disabled"
        ).pack(side="right", padx=5)

        self.tab_bar_scroll = ctk.CTkScrollableFrame(self, orientation="horizontal", height=50, fg_color="transparent")
        self.tab_bar_scroll.pack(fill="x", padx=20, pady=(0, 10))

        self.main_content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def get_translation(self, tag):
        return TRANSLATION_DICT.get(tag, tag)

    def load_xml_template(self):
        filepath = filedialog.askopenfilename(title="Выберите эталонный XML", filetypes=[("XML files", "*.xml")])
        if not filepath: return

        try:
            self.xml_tree = ET.parse(filepath)
            self.xml_root = self.xml_tree.getroot()
            self.rebuild_interface()
            # self.save_btn.configure(state="normal") # Кнопка пакуется сразу, так что её статус мы не меняем
            messagebox.showinfo("Успех", "Шаблон загружен, вкладки объединены по вашим правилам!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать XML:\n{e}")

    def create_tab(self, tab_id, display_name):
        btn = ctk.CTkButton(
            self.tab_bar_scroll, 
            text=display_name, 
            fg_color="transparent", 
            text_color=("gray10", "gray90"),
            border_width=2,
            border_color=("gray70", "gray30"),
            command=lambda t=tab_id: self.select_tab(t)
        )
        btn.pack(side="left", padx=5, pady=5)
        self.tab_buttons[tab_id] = btn

        content_frame = ctk.CTkScrollableFrame(self.main_content_area)
        self.tab_frames[tab_id] = content_frame
        return content_frame

    def rebuild_interface(self):
        for widget in self.tab_bar_scroll.winfo_children(): widget.destroy()
        for widget in self.main_content_area.winfo_children(): widget.destroy()
        self.tab_buttons.clear()
        self.tab_frames.clear()
        self.entry_mappings.clear()
        self.active_tab_id = None

        # --- 1. Сбор и распределение тегов по вкладкам ---
        tab_groups = {} # Словарь вида: {"Имя вкладки": [(тег, элемент), (тег, элемент)]}

        for child in self.xml_root:
            tag = child.tag
            
            # Определяем, в какую вкладку должен попасть этот тег
            if tag in CUSTOM_TAB_GROUPS:
                # Если тег есть в наших правилах объединения
                target_tab = CUSTOM_TAB_GROUPS[tag]
            elif len(child) == 0:
                # Простые теги (без вложений) всегда идут в Общие данные
                target_tab = "📌 Общие данные"
            else:
                # Все остальные сложные теги получают свою собственную вкладку
                translated_name = self.get_translation(tag)
                target_tab = f"📁 {translated_name}"

            if target_tab not in tab_groups:
                tab_groups[target_tab] = []
            tab_groups[target_tab].append((tag, child))

        # --- 2. Отрисовка интерфейса ---
        first_tab_id = None

        for tab_name, elements in tab_groups.items():
            # Генерируем уникальный ID для вкладки (хэшируем имя, чтобы избежать ошибок)
            tab_id = f"tab_{abs(hash(tab_name))}"
            if first_tab_id is None: first_tab_id = tab_id
            
            frame = self.create_tab(tab_id, tab_name)

            # Подсчитываем количество одинаковых тегов в этой вкладке (например, чтобы понять, сколько тут Авторов)
            tag_counts = {}
            for tag, _ in elements:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            current_tag_indices = {}

            # Размещаем поля
            for tag, elem in elements:
                translated_tag = self.get_translation(tag)
                
                # Если это сложный тег (в нем есть другие теги), рисуем красивый заголовок
                if len(elem) > 0:
                    current_tag_indices[tag] = current_tag_indices.get(tag, 0) + 1
                    
                    # Если таких тегов несколько (например, 3 автора), нумеруем их
                    if tag_counts[tag] > 1:
                        header_text = f"─── {translated_tag} {current_tag_indices[tag]} ───"
                    else:
                        header_text = f"─── {translated_tag} ───"
                        
                    header = ctk.CTkLabel(
                        frame, text=header_text, 
                        text_color="#3a7ebf", font=("Arial", 14, "bold")
                    )
                    header.pack(pady=(20, 5))

                # Рисуем сами поля ввода
                self.extract_fields(elem, frame, path_prefix="")

        # Активируем первую вкладку
        if first_tab_id:
            self.select_tab(first_tab_id)

    def select_tab(self, tab_id):
        if self.active_tab_id and self.active_tab_id in self.tab_frames:
            self.tab_frames[self.active_tab_id].pack_forget()
            self.tab_buttons[self.active_tab_id].configure(fg_color="transparent")

        self.tab_frames[tab_id].pack(fill="both", expand=True)
        self.tab_buttons[tab_id].configure(fg_color=["#3a7ebf", "#1f538d"])
        self.active_tab_id = tab_id

    def extract_fields(self, xml_element, parent_ui, path_prefix=""):
        if len(xml_element) == 0:
            raw_tag = xml_element.tag
            translated_tag = self.get_translation(raw_tag)
            
            display_name = f"{path_prefix}{translated_tag} [<{raw_tag}>]"
            
            ctk.CTkLabel(parent_ui, text=display_name, text_color=("gray20", "gray80"), font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
            entry = ctk.CTkEntry(parent_ui, width=500)
            entry.pack(anchor="w", pady=(0, 5), padx=10)

            if xml_element.text and xml_element.text.strip():
                entry.insert(0, xml_element.text.strip())

            self.entry_mappings.append({"xml_node": xml_element, "ui_entry": entry})
        else:
            for child in xml_element:
                translated_parent = self.get_translation(xml_element.tag)
                new_prefix = f"{path_prefix}{translated_parent} ➔ " if path_prefix else f"{translated_parent} ➔ "
                self.extract_fields(child, parent_ui, new_prefix)

    def save_xml(self):
        if not self.xml_tree: return

        filepath = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if not filepath: return

        for mapping in self.entry_mappings:
            mapping["xml_node"].text = mapping["ui_entry"].get()

        xml_string = ET.tostring(self.xml_root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="    ")
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(pretty_xml)
            messagebox.showinfo("Успех", "XML сохранен с сохранением оригинальной структуры!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

if __name__ == "__main__":
    app = UniversalXMLGeneratorApp()
    app.mainloop()