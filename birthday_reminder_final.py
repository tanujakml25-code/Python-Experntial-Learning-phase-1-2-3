
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import json
import csv
import os
import uuid

DATA_FILE = "birthdays.json"

# Colour theme
BG = "#F5F2FF"
PURPLE = "#6750D8"
DARK = "#33265F"
PINK = "#FCE7F3"
GREEN = "#DDF7E9"
GOLD = "#FFF0C2"
WHITE = "#FFFFFF"
TEXT = "#30294A"

records = []
filter_mode = "all"


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [
            r for r in data
            if isinstance(r, dict)
            and r.get("name")
            and valid_date(r.get("birthday", ""))
        ]
    except (OSError, json.JSONDecodeError):
        messagebox.showerror("File Error", "Could not load birthdays.json.")
        return []


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        messagebox.showerror("Save Error", str(e))
        return False


def parse_date(value):
    try:
        return datetime.strptime(value.strip(), "%d-%m-%Y").date()
    except (ValueError, AttributeError):
        return None


def valid_date(value):
    return parse_date(value) is not None


def next_birthday(value):
    b = parse_date(value)
    if not b:
        return None
    today = date.today()
    try:
        upcoming = b.replace(year=today.year)
    except ValueError:
        upcoming = date(today.year, 2, 28)
    if upcoming < today:
        try:
            upcoming = b.replace(year=today.year + 1)
        except ValueError:
            upcoming = date(today.year + 1, 2, 28)
    return upcoming


def days_left(value):
    upcoming = next_birthday(value)
    return (upcoming - date.today()).days if upcoming else 99999


def is_today(value):
    b = parse_date(value)
    today = date.today()
    return bool(b and b.day == today.day and b.month == today.month)


def make_button(parent, text, command, color=PURPLE, fg=WHITE):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg, activebackground=color,
        activeforeground=fg, relief="flat", bd=0,
        cursor="hand2", font=("Segoe UI", 9, "bold"),
        padx=10, pady=8
    )


def update_dashboard():
    total.set(str(len(records)))
    today_count.set(str(sum(is_today(r["birthday"]) for r in records)))
    week_count.set(str(sum(0 <= days_left(r["birthday"]) <= 7 for r in records)))
    month_count.set(str(sum(
        parse_date(r["birthday"]).month == date.today().month
        for r in records
    )))


def refresh_table(items=None):
    for item in tree.get_children():
        tree.delete(item)

    shown = list(records if items is None else items)
    shown.sort(key=lambda r: (days_left(r["birthday"]), r["name"].casefold()))

    for r in shown:
        days = days_left(r["birthday"])
        upcoming = next_birthday(r["birthday"])

        if days == 0:
            status, tag = "Birthday Today!", "today"
        elif days == 1:
            status, tag = "Tomorrow", "soon"
        elif days <= 7:
            status, tag = "Coming Soon", "soon"
        else:
            status, tag = "Upcoming", "normal"

        tree.insert(
            "", "end", iid=r["id"],
            values=(
                r["name"], r["birthday"],
                upcoming.strftime("%d-%m-%Y"),
                days, status
            ),
            tags=(tag,)
        )

    empty_label.place(
        relx=0.5, rely=0.5, anchor="center"
    ) if not shown else empty_label.place_forget()

    update_dashboard()
    status_text.set(f"{len(shown)} birthday record(s) displayed")


def add_birthday():
    open_form()


def open_form(record=None):
    editing = record is not None

    win = tk.Toplevel(root)
    win.title("Update Birthday" if editing else "Add Birthday")
    win.geometry("420x330")
    win.resizable(False, False)
    win.configure(bg=BG)
    win.transient(root)
    win.grab_set()

    tk.Label(
        win,
        text="✎ Update Birthday" if editing else "🎂 Add a Birthday",
        font=("Segoe UI", 17, "bold"),
        bg=DARK, fg=WHITE, pady=15
    ).pack(fill="x")

    form = tk.Frame(win, bg=BG, padx=25, pady=18)
    form.pack(fill="both", expand=True)

    tk.Label(form, text="Full Name", bg=BG, fg=TEXT,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")

    name_var = tk.StringVar(value=record["name"] if editing else "")
    name_entry = tk.Entry(form, textvariable=name_var, font=("Segoe UI", 11))
    name_entry.pack(fill="x", ipady=6, pady=(5, 12))

    tk.Label(form, text="Birthday (DD-MM-YYYY)", bg=BG, fg=TEXT,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")

    date_var = tk.StringVar(value=record["birthday"] if editing else "")
    date_entry = tk.Entry(form, textvariable=date_var, font=("Segoe UI", 11))
    date_entry.pack(fill="x", ipady=6, pady=(5, 5))

    tk.Label(
        form, text="Example: 25-09-2005",
        bg=BG, fg="#82799D", font=("Segoe UI", 9)
    ).pack(anchor="w")

    def submit():
        name = name_var.get().strip()
        bday = parse_date(date_var.get())

        if not name:
            messagebox.showwarning("Missing Name", "Enter a name.", parent=win)
            return

        if not bday:
            messagebox.showwarning(
                "Invalid Date", "Use a valid DD-MM-YYYY date.",
                parent=win
            )
            return

        duplicate = any(
            r["name"].casefold() == name.casefold()
            and (not editing or r["id"] != record["id"])
            for r in records
        )

        if duplicate:
            messagebox.showwarning(
                "Duplicate Name",
                "This name already exists. Select it to update.",
                parent=win
            )
            return

        if editing:
            record["name"] = name
            record["birthday"] = bday.strftime("%d-%m-%Y")
        else:
            records.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "birthday": bday.strftime("%d-%m-%Y")
            })

        if save_data():
            win.destroy()
            show_all()
            messagebox.showinfo(
                "Success",
                "Birthday updated successfully!" if editing
                else "Birthday added successfully! 🎉"
            )

    row = tk.Frame(form, bg=BG)
    row.pack(anchor="w", pady=12)

    make_button(
        row, "Save Birthday" if not editing else "Update Birthday",
        submit
    ).pack(side="left", padx=(0, 8))

    make_button(
        row, "Cancel", win.destroy, "#E8E2FF", DARK
    ).pack(side="left")

    name_entry.focus_set()


def selected_record():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning(
            "Select Record", "Please select a birthday from the table."
        )
        return None
    rid = selected[0]
    return next((r for r in records if r["id"] == rid), None)


def update_selected():
    record = selected_record()
    if record:
        open_form(record)


def delete_selected():
    record = selected_record()
    if not record:
        return

    if not messagebox.askyesno(
        "Confirm Delete", f"Delete birthday for {record['name']}?"
    ):
        return

    index = records.index(record)
    removed = records.pop(index)

    if save_data():
        show_all()
        messagebox.showinfo("Deleted", "Birthday deleted successfully.")
    else:
        records.insert(index, removed)


def search_birthday():
    global filter_mode
    filter_mode = "search"
    query = search_var.get().strip().casefold()

    results = [
        r for r in records if query in r["name"].casefold()
    ]
    refresh_table(results)

    if not results:
        messagebox.showinfo("Search", "No matching birthday found.")


def show_all():
    global filter_mode
    filter_mode = "all"
    search_var.set("")
    refresh_table()


def clear_search():
    search_var.set("")
    show_all()


def show_notifications():
    today_names = [
        r["name"] for r in records if is_today(r["birthday"])
    ]

    month_records = [
        r for r in records
        if parse_date(r["birthday"]).month == date.today().month
    ]

    lines = ["🎉 TODAY'S BIRTHDAYS"]
    lines.extend("• " + n for n in today_names)
    if not today_names:
        lines.append("No birthdays today.")

    lines += ["", "🔔 BIRTHDAYS THIS MONTH"]

    if month_records:
        for r in sorted(
            month_records,
            key=lambda x: parse_date(x["birthday"]).day
        ):
            lines.append(f"• {r['name']} — {r['birthday']}")
    else:
        lines.append("No birthdays this month.")

    messagebox.showinfo("Birthday Notifications", "\n".join(lines))


def upcoming_seven():
    results = [
        r for r in records if 0 <= days_left(r["birthday"]) <= 7
    ]
    refresh_table(results)
    if not results:
        messagebox.showinfo(
            "Upcoming Birthdays", "No birthdays in the next 7 days."
        )


def export_csv():
    if not records:
        messagebox.showinfo("No Records", "Add birthdays before exporting.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile="birthday_records.csv"
    )
    if not path:
        return

    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Name", "Birthday", "Next Birthday", "Days Remaining"
            ])

            for r in sorted(records, key=lambda x: days_left(x["birthday"])):
                writer.writerow([
                    r["name"], r["birthday"],
                    next_birthday(r["birthday"]).strftime("%d-%m-%Y"),
                    days_left(r["birthday"])
                ])

        messagebox.showinfo("Export Complete", "CSV file exported successfully.")
    except OSError as e:
        messagebox.showerror("Export Error", str(e))


def exit_app():
    if messagebox.askyesno("Exit", "Do you want to close Birthday Bloom?"):
        root.destroy()


def check_today_on_start():
    names = [r["name"] for r in records if is_today(r["birthday"])]
    if names:
        messagebox.showinfo(
            "🎂 Birthday Alert",
            "Today's birthday(s):\n\n" +
            "\n".join("🎉 " + name for name in names)
        )


# ---------------- MAIN WINDOW ----------------

records = load_data()

root = tk.Tk()
root.title("Birthday Bloom | Birthday Reminder")
root.geometry("1250x780")
root.minsize(1000, 650)
root.configure(bg=BG)

style = ttk.Style(root)
style.theme_use("clam")
style.configure(
    "Treeview", rowheight=34, font=("Segoe UI", 10),
    background=WHITE, foreground=TEXT, fieldbackground=WHITE
)
style.configure(
    "Treeview.Heading", background="#E9E3FF",
    foreground=DARK, font=("Segoe UI", 9, "bold"), padding=9
)
style.map("Treeview", background=[("selected", "#DCD3FF")])

# Header
header = tk.Frame(root, bg=DARK, height=88)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header, text="🎂  BIRTHDAY BLOOM",
    bg=DARK, fg=WHITE, font=("Segoe UI", 23, "bold")
).pack(anchor="w", padx=24, pady=(10, 0))

tk.Label(
    header,
    text="Your personal birthday planner • Remember every special day",
    bg=DARK, fg="#E4DEFF", font=("Segoe UI", 10)
).pack(anchor="w", padx=29)

main = tk.Frame(root, bg=BG, padx=18, pady=13)
main.pack(fill="both", expand=True)

tk.Label(
    main, text="Make every birthday special ✨",
    bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")
).pack(anchor="w")

tk.Label(
    main, text="Manage birthdays, view reminders and organise celebrations.",
    bg=BG, fg="#817995", font=("Segoe UI", 10)
).pack(anchor="w", pady=(2, 10))

# Dashboard
total = tk.StringVar(value="0")
today_count = tk.StringVar(value="0")
week_count = tk.StringVar(value="0")
month_count = tk.StringVar(value="0")

cards = tk.Frame(main, bg=BG)
cards.pack(fill="x", pady=(0, 12))


def create_card(title, variable, accent):
    card = tk.Frame(cards, bg=WHITE, highlightbackground="#E4DDF4",
                    highlightthickness=1)
    card.pack(side="left", fill="x", expand=True, padx=(0, 8))
    tk.Frame(card, bg=accent, height=4).pack(fill="x")
    tk.Label(
        card, text=title, bg=WHITE, fg="#817995",
        font=("Segoe UI", 9, "bold")
    ).pack(anchor="w", padx=12, pady=(7, 0))
    tk.Label(
        card, textvariable=variable, bg=WHITE, fg=accent,
        font=("Segoe UI", 21, "bold")
    ).pack(anchor="w", padx=12, pady=(0, 7))


create_card("TOTAL BIRTHDAYS", total, PURPLE)
create_card("TODAY", today_count, "#C63D7B")
create_card("NEXT 7 DAYS", week_count, "#16805A")
create_card("THIS MONTH", month_count, "#B98212")

# Directory panel
panel = tk.Frame(main, bg=WHITE, highlightbackground="#E4DDF4",
                 highlightthickness=1)
panel.pack(fill="both", expand=True)

tk.Label(
    panel, text="Birthday Directory",
    bg=WHITE, fg=TEXT, font=("Segoe UI", 14, "bold")
).pack(anchor="w", padx=13, pady=(10, 5))

# All main options visible in the first toolbar
toolbar = tk.Frame(panel, bg=WHITE)
toolbar.pack(fill="x", padx=10, pady=(0, 7))

make_button(toolbar, "＋ Add Birthday", add_birthday).pack(side="left", padx=3)
make_button(toolbar, "✎ Update Selected", update_selected,
            "#E9E3FF", DARK).pack(side="left", padx=3)
make_button(toolbar, "🗑 Delete Selected", delete_selected,
            "#FFE5EF", "#B8326B").pack(side="left", padx=3)
make_button(toolbar, "🔍 Search", search_birthday,
            "#E2F3FF", "#17618A").pack(side="left", padx=3)
make_button(toolbar, "📋 Show All", show_all,
            "#DDF7E9", "#167653").pack(side="left", padx=3)

toolbar2 = tk.Frame(panel, bg=WHITE)
toolbar2.pack(fill="x", padx=10, pady=(0, 8))

make_button(toolbar2, "🎉 Notifications", show_notifications,
            "#FCE7F3", "#B8326B").pack(side="left", padx=3)
make_button(toolbar2, "🔔 Upcoming 7 Days", upcoming_seven,
            "#FFF0C2", "#956300").pack(side="left", padx=3)
make_button(toolbar2, "📁 Export CSV", export_csv,
            "#DDF7E9", "#167653").pack(side="left", padx=3)
make_button(toolbar2, "↻ Refresh", show_all,
            "#E9E3FF", DARK).pack(side="left", padx=3)
make_button(toolbar2, "⏻ Exit", exit_app,
            "#F1EFF6", TEXT).pack(side="right", padx=3)

# Quick search field
search_row = tk.Frame(panel, bg=WHITE)
search_row.pack(fill="x", padx=13, pady=(0, 9))

tk.Label(
    search_row, text="Quick Search:",
    bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")
).pack(side="left", padx=(0, 8))

search_var = tk.StringVar()
search_entry = tk.Entry(
    search_row, textvariable=search_var,
    font=("Segoe UI", 10), relief="solid", bd=1
)
search_entry.pack(side="left", fill="x", expand=True, ipady=5)
search_entry.bind("<Return>", lambda event: search_birthday())

make_button(
    search_row, "Clear", clear_search, "#F1EFF6", TEXT
).pack(side="left", padx=(7, 0))

# Records table
table_frame = tk.Frame(panel, bg=WHITE)
table_frame.pack(fill="both", expand=True, padx=13, pady=(0, 12))

columns = ("name", "birthday", "next", "days", "status")
tree = ttk.Treeview(
    table_frame, columns=columns, show="headings", selectmode="browse"
)

for col, heading in [
    ("name", "NAME"),
    ("birthday", "BIRTHDAY"),
    ("next", "NEXT BIRTHDAY"),
    ("days", "DAYS LEFT"),
    ("status", "STATUS")
]:
    tree.heading(col, text=heading)

tree.column("name", width=220)
tree.column("birthday", width=150, anchor="center")
tree.column("next", width=160, anchor="center")
tree.column("days", width=100, anchor="center")
tree.column("status", width=160, anchor="center")

scrollbar = ttk.Scrollbar(
    table_frame, orient="vertical", command=tree.yview
)
tree.configure(yscrollcommand=scrollbar.set)
tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

tree.tag_configure("today", background="#FFEAF3")
tree.tag_configure("soon", background="#FFF7DF")
tree.tag_configure("normal", background=WHITE)

empty_label = tk.Label(
    table_frame,
    text="🎁\nNo birthdays to display.\nClick “Add Birthday” to get started!",
    bg=WHITE, fg="#817995", font=("Segoe UI", 12), justify="center"
)

status_text = tk.StringVar(value="Ready")
footer = tk.Label(
    root, textvariable=status_text, bg="#E9E3FF", fg=DARK,
    anchor="w", padx=15, pady=5, font=("Segoe UI", 9)
)
footer.pack(fill="x", side="bottom")

refresh_table()
root.after(700, check_today_on_start)
root.mainloop()
