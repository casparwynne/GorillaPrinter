import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


def generate_html_from_gorilla(folder_path, questionnaire_title):
    base_path = Path(folder_path)

    try:
        with open(base_path / "spec.json", encoding="utf-8") as f:
            spec = json.load(f)
        with open(base_path / "metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)
        with open(base_path / "manifest.json", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError as e:
        messagebox.showerror("Error", f"Missing file: {e.filename}")
        return

    assets = manifest.get("assets", []) or []
    asset_lookup = {a['filename']: a['url'] for a in assets}

    html = ["<html><head><meta charset='UTF-8'><style>",
            "body { font-family: sans-serif; }",
            ".question { margin-bottom: 2em; }",
            "table { border-collapse: collapse; margin-top: 1em; }",
            "th, td { border: 1px solid #000; padding: 5px; text-align: center; }",
            "td:first-child { max-width: 200px; word-wrap: break-word; white-space: normal; text-align: left; }",
            "</style></head><body>"]

    html.append(f"<h1>{questionnaire_title}</h1><hr>")

    for entity in spec["scenes"][0]["scene"][0]["children"]:
        comp = entity["components"][0]
        tag = comp["class"]
        question_text = comp.get("question_text", "Question")
        question_html = "<div class='question'>"

        if tag == "QuestionnaireMarkdown":
            question_html += f"<div>{comp['text'].replace(chr(10),'<br/>')}</div>"

        elif tag == "QuestionnaireImage":
            img_src = asset_lookup.get(comp["image"], "")
            question_html += f"<div><img src='{img_src}' alt='Image' style='max-width:100%;'/></div>"

        elif tag == "QuestionnaireAudio":
            audio_src = asset_lookup.get(comp["audioName"], "")
            question_html += f"<p><b>Audio Prompt:</b> <a href='{audio_src}' target='_blank'>{comp['audioName']}</a></p>"

        elif tag == "QuestionnaireCommentBoxEntry":
            rows = comp.get("rows", 5)
            question_html += f"<p>{question_text}</p>" + ("<br/><span style='display:block;border-bottom:1px solid #000;width:100%;'>&nbsp;</span>" * rows)

        elif tag == "QuestionnaireDropdown":
            question_html += f"<p>{question_text} (please tick one)</p><ul>"
            options = comp.get("question_keys", [{}])[0].get("options", [])
            for opt in options:
                question_html += f"<li>{opt['label']} ________</li>"
            question_html += "</ul>"

        elif tag == "QuestionnaireMultipleChoice":
            question_html += f"<p>{question_text}</p>"
            for opt in comp.get("options", []):
                question_html += f"<label><input type='radio'> {opt['label']}</label><br/>"

        elif tag == "QuestionnaireSlider":
            question_html += ("<div style='margin-top:1em;margin-bottom:1em;'>"
                              "<p>Please indicate your response by drawing a mark on the line below:</p>"
                              "<div style='width:50%;border-bottom:2px solid #000;height:1.5em;margin:auto;'></div>"
                              "<div style='width:50%;display:flex;justify-content:space-between;margin:auto;'>"
                              "<span>Min</span><span>Max</span></div></div>")

        elif tag == "QuestionnaireDateEntry":
            question_html += f"<p>{question_text} (DD/MM/YY)</p><span style='display:inline-block;border-bottom:1px solid #000;width:300px;'>&nbsp;</span>"

        elif tag == "QuestionnaireTimeEntry":
            question_html += f"<p>{question_text} (HH:MM)</p><span style='display:inline-block;border-bottom:1px solid #000;width:300px;'>&nbsp;</span>"

        elif tag == "QuestionnaireEmailEntry":
            question_html += f"<p>Email: <span style='display:inline-block;border-bottom:1px solid #000;width:300px;'>&nbsp;</span></p>"

        elif tag in ["QuestionnaireTextEntry", "QuestionnaireNumberEntry"]:
            question_html += f"<p>{question_text}</p><span style='display:inline-block;border-bottom:1px solid #000;width:300px;'>&nbsp;</span>"

        elif tag == "QuestionnaireHeightEntry":
            question_html += (f"<p>{question_text}</p>"
                              "<p>Metric (cm): <span style='border-bottom:1px solid #000;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>"
                              "<p>Imperial (ft/in): <span style='border-bottom:1px solid #000;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>")

        elif tag == "QuestionnaireWeightEntry":
            question_html += (f"<p>{question_text}</p>"
                              "<p>Metric (kg): <span style='border-bottom:1px solid #000;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>"
                              "<p>Imperial (st/lb): <span style='border-bottom:1px solid #000;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></p>")

        elif tag == "QuestionnaireMultipleChoiceGrid":
            rows = comp.get("rows", [])
            columns = comp.get("columns", [])
            question_html += f"<p>{question_text}</p><table>"
            question_html += "<tr><th></th>" + "".join(f"<th>{col['label']}</th>" for col in columns) + "</tr>"
            for row in rows:
                question_html += f"<tr><td>{row['label']}</td>" + "".join("<td>☐</td>" for _ in columns) + "</tr>"
            question_html += "</table>"

        elif tag == "QuestionnaireRatingScale":
            question_html += f"<p>{question_text}</p>" + " ".join(["⚪" for _ in comp.get("options", [])])

        else:
            question_html += f"<p><i>Unsupported question type: {tag}</i></p>"

        question_html += "</div>"
        html.append(question_html)

    html.append("</body></html>")
    output_html = base_path / f"printable_{questionnaire_title.replace(' ', '_')}.html"

    with open(output_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    messagebox.showinfo("Success", f"Saved to: {output_html}")


# ---- Improved Tkinter GUI ----
class QuestionnaireApp:
    def __init__(self, master):
        self.master = master
        master.title("Gorilla Questionnaire to Printable HTML")

        tk.Label(master, text="Step 1: Enter Questionnaire Title").pack(pady=(10, 0))
        self.title_entry = tk.Entry(master, width=50)
        self.title_entry.pack(pady=5)

        tk.Label(master, text="Step 2: Select Folder Containing Gorilla Export Files").pack(pady=(10, 0))
        self.select_button = tk.Button(master, text="Select Folder", command=self.select_folder)
        self.select_button.pack(pady=5)

        self.status_text = tk.StringVar()
        self.status_label = tk.Label(master, textvariable=self.status_text, fg="green")
        self.status_label.pack(pady=(10, 0))

        self.file_checks = {}
        for file in ["spec.json", "metadata.json", "manifest.json"]:
            self.file_checks[file] = tk.Label(master, text=f"{file}: ❌", anchor="w")
            self.file_checks[file].pack()

        self.generate_button = tk.Button(master, text="Generate Printable HTML", command=self.generate_html, state="disabled")
        self.generate_button.pack(pady=15)

        self.folder_path = None

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            return

        all_found = True
        for file, label in self.file_checks.items():
            path = Path(self.folder_path) / file
            if path.exists():
                label.config(text=f"{file}: ✅", fg="green")
            else:
                label.config(text=f"{file}: ❌", fg="red")
                all_found = False

        if all_found:
            self.status_text.set("All required files found.")
            self.generate_button.config(state="normal")
        else:
            self.status_text.set("Missing one or more required files.")
            self.generate_button.config(state="disabled")

    def generate_html(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Input Required", "Please enter a title for the questionnaire.")
            return
        generate_html_from_gorilla(self.folder_path, title)


if __name__ == "__main__":
    root = tk.Tk()
    app = QuestionnaireApp(root)
    root.mainloop()