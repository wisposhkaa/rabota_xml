import customtkinter as ctk
from tkinter import messagebox, filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import shutil
import zlib  # Библиотека для вычисления CRC32

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# =====================================================================
# 🌍 СЛОВАРЬ ПЕРЕВОДОВ 
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
    "OGRN": "ОГРН",
    "FileName": "Прикрепленный файл",
    "FileFormat": "Формат файла",
    "FileChecksum": "Хэш-сумма (CRC32)" # ИСПРАВЛЕНО: FileChecksum
}

# =====================================================================
# 🛠 ПРАВИЛА ОБЪЕДИНЕНИЯ ВКЛАДОК
# =====================================================================
CUSTOM_TAB_GROUPS = {
    "ExplanatoryNoteModifications": "📌 Общие данные",
    "IssueAuthor": "👷 Генеральный проектировщик",
    "Signers": "👷 Генеральный проектировщик",
    "DesignerAssurance": "👷 Генеральный проектировщик",
    "ProjectDecisionDocuments": "📑 Исходно-разрешительная документация",
    "ProjectInitialDocuments": "📑 Исходно-разрешительная документация",
}
# =====================================================================

class UniversalXMLGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("XML Генератор (CRC32 Автоматизация)")
        self.geometry("900x750")

        self.xml_tree = None
        self.xml_root = None
        self.entry_mappings = [] 
        
        self.tab_buttons = {} 
        self.tab_frames = {}  
        self.active_tab_id = None 

        self.parent_map = {}

        self.setup_ui()

    def setup_ui(self):
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            self.top_frame, text="📂 1. Загрузить XML Шаблон", 
            command=self.load_xml_template, fg_color="#d35400", hover_color="#e67e22"
        ).pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(
            self.top_frame, text="💾 2. Сохранить XML и Файлы", 
            command=self.save_xml, fg_color="green", hover_color="darkgreen", state="disabled"
        )
        self.save_btn.pack(side="right", padx=5)

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
            
            # Строим карту родителей
            self.parent_map = {c: p for p in self.xml_tree.iter() for c in p}
            
            self.rebuild_interface()
            self.save_btn.configure(state="normal")
            messagebox.showinfo("Успех", "Шаблон загружен! CRC32 готов к работе.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать XML:\n{e}")

    def create_tab(self, tab_id, display_name):
        btn = ctk.CTkButton(
            self.tab_bar_scroll, text=display_name, fg_color="transparent", 
            text_color=("gray10", "gray90"), border_width=2, border_color=("gray70", "gray30"),
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

        tab_groups = {}
        for child in self.xml_root:
            tag = child.tag
            if tag in CUSTOM_TAB_GROUPS:
                target_tab = CUSTOM_TAB_GROUPS[tag]
            elif len(child) == 0:
                target_tab = "📌 Общие данные"
            else:
                translated_name = self.get_translation(tag)
                target_tab = f"📁 {translated_name}"

            if target_tab not in tab_groups: tab_groups[target_tab] = []
            tab_groups[target_tab].append((tag, child))

        first_tab_id = None
        for tab_name, elements in tab_groups.items():
            tab_id = f"tab_{abs(hash(tab_name))}"
            if first_tab_id is None: first_tab_id = tab_id
            
            frame = self.create_tab(tab_id, tab_name)

            tag_counts = {}
            for tag, _ in elements: tag_counts[tag] = tag_counts.get(tag, 0) + 1
            current_tag_indices = {}

            for tag, elem in elements:
                translated_tag = self.get_translation(tag)
                if len(elem) > 0:
                    current_tag_indices[tag] = current_tag_indices.get(tag, 0) + 1
                    header_text = f"─── {translated_tag} {current_tag_indices[tag]} ───" if tag_counts[tag] > 1 else f"─── {translated_tag} ───"
                    ctk.CTkLabel(frame, text=header_text, text_color="#3a7ebf", font=("Arial", 14, "bold")).pack(pady=(20, 5))

                self.extract_fields(elem, frame, path_prefix="")

        if first_tab_id: self.select_tab(first_tab_id)

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

            # --- УМНАЯ ЛОГИКА ДЛЯ ПОЛЯ FileName И СОСЕДНИХ ПОЛЕЙ ---
            if raw_tag == "FileName":
                file_frame = ctk.CTkFrame(parent_ui, fg_color="transparent")
                file_frame.pack(anchor="w", pady=(0, 5), padx=10, fill="x")

                entry = ctk.CTkEntry(file_frame, width=350)
                entry.pack(side="left", padx=(0, 10))

                mapping_dict = {"xml_node": xml_element, "ui_entry": entry, "source_filepath": None}

                def browse_file(m=mapping_dict):
                    filepath = filedialog.askopenfilename(title="Выберите файл для прикрепления")
                    if filepath:
                        filename = os.path.basename(filepath)
                        m["ui_entry"].delete(0, 'end')
                        m["ui_entry"].insert(0, filename)
                        m["source_filepath"] = filepath

                        file_ext = os.path.splitext(filename)[1][1:].lower() 
                        
                        # Вычисление CRC32 по кусочкам
                        crc_value = 0
                        try:
                            with open(filepath, "rb") as f:
                                for chunk in iter(lambda: f.read(4096), b""):
                                    crc_value = zlib.crc32(chunk, crc_value)
                            # Форматируем результат в 8-символьную 16-ричную строку (например, "e412a832")
                            file_hash = f"{crc_value & 0xFFFFFFFF:08x}"
                        except Exception as e:
                            print(f"Ошибка чтения файла для хэша: {e}")
                            file_hash = ""

                        # ИЩЕМ СОСЕДНИЕ ПОЛЯ (FileFormat и FileChecksum)
                        parent_node = self.parent_map.get(m["xml_node"])
                        if parent_node is not None:
                            format_node = parent_node.find("FileFormat")
                            checksum_node = parent_node.find("FileChecksum") # ИСПРАВЛЕНО НА FileChecksum

                            for sibling_mapping in self.entry_mappings:
                                if sibling_mapping["xml_node"] == format_node:
                                    sibling_mapping["ui_entry"].delete(0, 'end')
                                    sibling_mapping["ui_entry"].insert(0, file_ext)
                                elif sibling_mapping["xml_node"] == checksum_node:
                                    sibling_mapping["ui_entry"].delete(0, 'end')
                                    sibling_mapping["ui_entry"].insert(0, file_hash)

                btn = ctk.CTkButton(file_frame, text="📎 Выбрать", width=100, command=browse_file)
                btn.pack(side="left")

                if xml_element.text and xml_element.text.strip():
                    entry.insert(0, xml_element.text.strip())
                
                self.entry_mappings.append(mapping_dict)

            # --- СТАНДАРТНАЯ ЛОГИКА ДЛЯ ОСТАЛЬНЫХ ПОЛЕЙ ---
            else:
                entry = ctk.CTkEntry(parent_ui, width=500)
                
                # ИСПРАВЛЕНО: делаем поле для FileChecksum шире, если нужно
                if raw_tag == "FileChecksum":
                    entry.configure(width=600)

                entry.pack(anchor="w", pady=(0, 5), padx=10)

                if xml_element.text and xml_element.text.strip():
                    entry.insert(0, xml_element.text.strip())

                self.entry_mappings.append({"xml_node": xml_element, "ui_entry": entry, "source_filepath": None})
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
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить XML файл:\n{e}")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__)) 
        files_dir = os.path.join(script_dir, "files")
        
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)

        copied_files_count = 0
        
        for mapping in self.entry_mappings:
            source_path = mapping.get("source_filepath")
            current_filename = mapping["ui_entry"].get()
            
            if source_path and os.path.exists(source_path):
                if current_filename == os.path.basename(source_path):
                    try:
                        shutil.copy2(source_path, files_dir)
                        copied_files_count += 1
                    except Exception as e:
                        print(f"Ошибка при копировании {source_path}: {e}")

        messagebox.showinfo(
            "Успех", 
            f"Файл XML успешно сохранен!\n\n"
            f"Скопировано файлов в папку 'files': {copied_files_count} шт."
        )

if __name__ == "__main__":
    app = UniversalXMLGeneratorApp()
    app.mainloop()