import customtkinter as ctk
from tkinter import messagebox, filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# =====================================================================
# 🌍 СЛОВАРЬ ПЕРЕВОДОВ (ТОЛЬКО ДЛЯ ИНТЕРФЕЙСА)
# =====================================================================
TRANSLATION_DICT = {
    # --- Вкладки (Корневые теги) ---
    "ExplanatoryNoteNumber": "Шифр пояснительной записки",
    "ExplanatoryNoteYear": "Год составления",
    "GeneralInfo": "Общие сведения",
    "Developer": "Застройщик (Тех. заказчик)",
    "Object": "Объект строительства",
    "NonIndustrialObject": "Непроизводственный объект",
    "IndustrialObject": "Производственный объект",
    "LinearObject": "Линейный объект",
    "ProjectInitialDocuments": "Исходно-разрешительные документы",
    
    # --- Поля ---
    "DocumentName": "Наименование документа",
    "DocumentDate": "Дата документа",
    "DocumentNumber": "Номер документа",
    "OrganizationName": "Полное наименование организации",
    "INN": "ИНН",
    "OGRN": "ОГРН",
    "KPP": "КПП",
    "ObjectName": "Наименование объекта",
    "Address": "Почтовый адрес",
    "BuiltUpArea": "Площадь застройки (кв.м)",
    "TotalArea": "Общая площадь (кв.м)",
    "BuildingVolume": "Строительный объем (куб.м)",
    "Email": "Электронная почта"
    # Добавляй сюда новые переводы по мере необходимости!
}
# =====================================================================

class UniversalXMLGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("XML Генератор (с русским интерфейсом)")
        self.geometry("900x700")

        self.xml_tree = None
        self.xml_root = None
        self.entry_mappings = [] 
        
        self.tab_buttons = {} 
        self.tab_frames = {}  
        self.active_tab_id = None # Теперь используем ID вкладки, а не текст

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
        )
        self.save_btn.pack(side="right", padx=5)

        self.tab_bar_scroll = ctk.CTkScrollableFrame(self, orientation="horizontal", height=50, fg_color="transparent")
        self.tab_bar_scroll.pack(fill="x", padx=20, pady=(0, 10))

        self.main_content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def get_translation(self, tag):
        """Функция-помощник: ищет перевод в словаре. Если нет - возвращает сам тег."""
        return TRANSLATION_DICT.get(tag, tag)

    def load_xml_template(self):
        filepath = filedialog.askopenfilename(title="Выберите эталонный XML", filetypes=[("XML files", "*.xml")])
        if not filepath: return

        try:
            self.xml_tree = ET.parse(filepath)
            self.xml_root = self.xml_tree.getroot()
            self.rebuild_interface()
            self.save_btn.configure(state="normal")
            messagebox.showinfo("Успех", "Шаблон загружен, интерфейс переведен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать XML:\n{e}")

    def rebuild_interface(self):
        for widget in self.tab_bar_scroll.winfo_children(): widget.destroy()
        for widget in self.main_content_area.winfo_children(): widget.destroy()
        self.tab_buttons.clear()
        self.tab_frames.clear()
        self.entry_mappings.clear()
        self.active_tab_id = None

        first_tab_id = None

        for main_section in self.xml_root:
            raw_tag = main_section.tag
            translated_name = self.get_translation(raw_tag)
            
            # Уникальный ID для вкладки (на случай двух одинаковых тегов)
            tab_id = f"tab_{id(main_section)}"
            display_tab_name = translated_name

            # Если вкладка с таким именем уже есть, добавляем цифру для визуала (например, Застройщик 2)
            counter = 1
            while display_tab_name in [btn.cget("text") for btn in self.tab_buttons.values()]:
                display_tab_name = f"{translated_name} ({counter})"
                counter += 1

            if first_tab_id is None:
                first_tab_id = tab_id

            # Создаем кнопку вкладки (текст - русский, а логика привязана к tab_id)
            btn = ctk.CTkButton(
                self.tab_bar_scroll, 
                text=display_tab_name, 
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                border_width=2,
                border_color=("gray70", "gray30"),
                command=lambda t_id=tab_id: self.select_tab(t_id)
            )
            btn.pack(side="left", padx=5, pady=5)
            self.tab_buttons[tab_id] = btn

            content_frame = ctk.CTkScrollableFrame(self.main_content_area)
            self.tab_frames[tab_id] = content_frame

            self.extract_fields(main_section, content_frame, path_prefix="")

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
            
            # Формируем красивую подпись: "Русское название [<АнглийскийТег>]"
            display_name = f"{path_prefix}{translated_tag} [<{raw_tag}>]"
            
            ctk.CTkLabel(parent_ui, text=display_name, text_color=("gray20", "gray80"), font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 0), padx=10)
            entry = ctk.CTkEntry(parent_ui, width=500)
            entry.pack(anchor="w", pady=(0, 5), padx=10)

            if xml_element.text and xml_element.text.strip():
                entry.insert(0, xml_element.text.strip())

            # ВАЖНО: Привязываем поле к оригинальному XML-узлу
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
            # Записываем текст из интерфейса обратно в оригинальный XML узел
            mapping["xml_node"].text = mapping["ui_entry"].get()

        xml_string = ET.tostring(self.xml_root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="    ")
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(pretty_xml)
            messagebox.showinfo("Успех", "XML сохранен! В файле остались оригинальные английские теги.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

if __name__ == "__main__":
    app = UniversalXMLGeneratorApp()
    app.mainloop()