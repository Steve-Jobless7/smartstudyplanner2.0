import uuid

import os
 
import json

import csv

from dataclasses import dataclass, asdict   

from datetime import datetime, date

from typing import List, Optional

import tkinter as tk

from tkinter import ttk, messagebox, StringVar, filedialog as fd

from ttkbootstrap import Style

from ttkbootstrap.constants import *


dateformat="%Y/%m/%d"
apptitle="Smart Study Planner"
statusoptions=["To Do", "Done","In progress"]
statusorder={a:b for b,a in enumerate(statusoptions)}
DATA_FILE="planner.json"
BACKUP_DIR="backups"
CSV_HEADERS=["id","title","subject","duedate","status"]
CHECK_EMPTY = "☐" 
CHECK_FULL = "☑"

@dataclass
class Task:
    id:str
    title:str
    subject:str
    duedate:str
    status:str="To Do"
def today_str()->str:
        return datetime.now().strftime(dateformat)
def valid_date(s:str)->bool:
        try:
            datetime.strptime(s,dateformat)
            return True
        except Exception:
            return False
def parse_date(s:str)-> Optional[date]:
      try:
            return datetime.strptime(s, dateformat).date()
      except Exception:
            return None

class storage:
      """Tiny JSON storage helper"""
      def __init__(self,path: str):
            self.path=path
      def load(self) ->List[Task]:
            if not os.path.exists(self.path):
                  return[]
            try:
                  with open(self.path,"r", encoding="utf-8") as f:
                        raw= json.load(f)
            except Exception:
                  return[]
            tasks: List[Task]=[]
            if isinstance(raw,list):
                  for item in raw:
                        if not isinstance(item,dict):
                              continue
                        
                  
                        tid=str(item.get("id") or uuid.uuid4())
                        title=str(item.get("title") or "").strip()
                        subject=str(item.get("subject") or "").strip()
                        duedate=str(item.get("duedate") or today_str()).strip()
                        status=str(item.get("status") or "To Do").strip()
                        if not title or not subject or not valid_date(duedate):
                          continue
                        if status not in statusoptions:
                          status="To Do"
                        tasks.append(Task(id=tid, title=title, subject=subject,duedate=duedate,status=status))
                  
                        
                        
                  
                  
            return tasks
      def save(self, tasks: List[Task]) -> None:
            payload = [asdict(t) for t in tasks]
            tmp = self.path + ".tmp"
            with open(tmp,"w",encoding="utf-8") as f:
                  json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)

class TaskDialog(tk.Toplevel):
      def __init__(self,parent,on_save,task:Optional[Task]=None):
            super().__init__(parent)
            self.title("Add Task" if task is None else "Edit Task")
            self.resizable(False,False)
            self.grab_set()
            self.on_save=on_save
            self.var_title=StringVar(value=task.title if task else "")
            self.var_subject=StringVar(value=task.subject if task else "")
            self.var_due=StringVar(value=task.duedate if task else today_str())
            self.var_status=StringVar(value=task.status if task else statusoptions[0])
            frm=ttk.Frame(self,padding=12)
            frm.pack(fill=BOTH,expand=YES)
            ttk.Label(frm,text="Title").grid(row=0,column=0,sticky=E,padx=6,pady=6)
            e_title=ttk.Entry(frm,textvariable=self.var_title,width=36)
            e_title.grid(row=0,column=1,sticky=W,padx=6,pady=6)
            e_title.focus_set()
            ttk.Label(frm,text="Subject").grid(row=1,column=0,sticky=E,padx=6,pady=6)
            ttk.Entry(frm,textvariable=self.var_subject,width=36).grid(row=1,column=1,sticky=W,padx=6,pady=6)
            ttk.Label(frm,text="Due Date(yyyy/mm/dd)").grid(row=2,column=0,sticky=E,padx=6,pady=6)
            ttk.Entry(frm,textvariable=self.var_due,width=36).grid(row=2,column=1,sticky=W,padx=6,pady=6)
            ttk.Label(frm,text="Status").grid(row=3,column=0,sticky=E,padx=6,pady=6)
            ttk.Combobox(frm,textvariable=self.var_status,values=statusoptions,state="readonly",width=20).grid(row=3,column=1,sticky=W,padx=6,pady=6)
            btns=ttk.Frame(frm)
            btns.grid(row=4,column=0,columnspan=2,pady=10)
            ttk.Button(btns,text="Cancel",command=self.destroy).pack(side=RIGHT,padx=6)
            ttk.Button(btns,text="Save",bootstyle=SUCCESS,command=self._save).pack(side=RIGHT)
            self.bind("<Return>",lambda e:self._save())
            self.bind("<Escape>",lambda e:self.destroy())
            self.update_idletasks()
            self.geometry(f"+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")
      def _save(self):
            title=self.var_title.get().strip()
            subject=self.var_subject.get().strip()
            due=self.var_due.get().strip()
            status=self.var_status.get().strip()
            if not title:
                  messagebox.showerror("validation","Title is required")
                  return
            if not subject:
                  messagebox.showerror("validation","subject is required")
                  return
            if not valid_date(due):
                  messagebox.showerror("validation","Due date needs to be valid")
                  return
            if status not in statusoptions:
                  messagebox.showerror("validation","invalid status selected")
                  return
            self.on_save(title,subject,due,status)
            self.destroy()
class App(ttk.Frame):
      def __init__(self,master):
            super().__init__(master,padding=12)
            self.status_filter_var=StringVar(value="ALL")
            self.pack(fill=BOTH,expand=YES)
            self.tasks:List[Task]=[]
            self.search_var=StringVar()
            self.sort_key="duedate"
            self.sort_reverse=False
            self.storage=storage(DATA_FILE)
            self._apply_styles()
            self._build_header()
            self._build_center()
            self._build_statusbar()
            self._tick()
            self._build_menu()
            self.bind_all("<Control-n>",lambda e:self.open_add_dialog())
            self.bind_all("<Delete>",lambda e:self.delete_selected())
            self.bind_all("<Control-e>",lambda e:self.open_edit_dialog())
            self.tree.bind("<Button-1>",self._on_tree_click, add="+")  
            self._load_initial()  
      def _build_menu(self):
            root = self.winfo_toplevel()
            menubar = tk.Menu(root)

            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="Import CSV...",  command=self.import_csv)
            file_menu.add_command(label="Export CSV...",  command=self.export_csv)
            file_menu.add_separator()
            file_menu.add_command(label="Backup JSON...", command=self.backup_json)
            file_menu.add_command(label="Restore JSON...", command=self.restore_json)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.on_close)
            menubar.add_cascade(label="File", menu=file_menu)
            root.config(menu=menubar)

            menubar.add_cascade(label="File", menu=file_menu)
            root.config(menu=menubar)
      



      def _apply_styles(self):
            s=ttk.Style()
            s.configure("Treeview",rowheight=28,padding=2)
            s.configure("Treeview.Heading",padding=(6,4))
            s.map("Treeview",background=[("selected", "white")],foreground=[("selected","blue")])
      def _build_header(self):
            top=ttk.Frame(self)
            top.pack(fill=X,pady=(0,10))

            ttk.Label(top,text="Smart Study Planner", font=("Segoe UI",16,"bold")).pack(side=LEFT)
            ttk.Label(top,text=" Search:").pack(side=LEFT,padx=(16,0))
            entry=ttk.Entry(top, textvariable=self.search_var,width=34)
            entry.pack(side=LEFT)
            entry.bind("<KeyRelease>",lambda e: self.refresh_table())

            ttk.Label(top, text="  Status  ").pack(side=LEFT,padx=(12,0))
            self.cb_filter=ttk.Combobox(
                  top,
                  textvariable=self.status_filter_var,
                  values=["ALL"] + statusoptions,
                  state="readonly",
                  width=14
                  )
            self.cb_filter.pack(side=LEFT)
            self.cb_filter.bind("<<ComboboxSelected>>",lambda e: self.refresh_views())
            
            ttk.Button(top, text="Add Task (Ctrl+N)",bootstyle=SUCCESS,command=self.
            open_add_dialog).pack(side=RIGHT,padx=6)
            ttk.Button(top, text="Delete", bootstyle="DANGER", command=self.delete_selected).pack(side=RIGHT,padx=6)
            ttk.Button(top, text="Edit Task (Ctrl+E)",bootstyle=INFO,command=self.
            open_edit_dialog).pack(side=RIGHT,padx=6)
      def _build_center(self):
            self.nb= ttk.Notebook(self)
            self.nb.pack(fill=BOTH,expand=YES)
            self.tab_list=ttk.Frame(self.nb,padding=8)
            self.nb.add(self.tab_list, text="list")
            cols=("check","title", "subject","duedate","status")
            self.tree=ttk.Treeview(self.tab_list,columns=cols,show="headings",height=14)
            self.tree.pack(fill=BOTH,expand=YES)
            self._define_col("check","✓",   48,  tk.CENTER)
            self._define_col("title","Title",380,"w")
            self._define_col("subject","Subject",160,"w")
            self._define_col("duedate","Due Date",120,"w")
            self._define_col("status","Status",120,"w")
            

            for c in cols:
                  self.tree.heading(c,command=lambda col=c:self._sort_by(col))

            self.tree.tag_configure("even",background="white")
            self.tree.tag_configure("odd",background="white")
            
            self.tree.tag_configure("today", background="lightblue")
            self.tree.tag_configure("overdue", foreground="red")

            self.tab_board=ttk.Frame(self.nb,padding=8)
            self.nb.add(self.tab_board,text= "board")
            board=ttk.Frame(self.tab_board)
            board.pack(fill=BOTH,expand=YES)
            board.grid_columnconfigure(0, weight=1, uniform="col")
            board.grid_columnconfigure(1, weight=1, uniform="col")
            board.grid_columnconfigure(2, weight=1, uniform="col")
            self.col_frames={}
            for idx, status in enumerate(statusoptions):
                  col=ttk.Frame(board,padding=6)
                  col.grid(row=0,column=idx,sticky=NSEW,padx=6)
                  head=ttk.Label(col,text=status,font=("Segoe UI", 12, "bold"))
                  head.pack(anchor=W,pady=(0,6))
                  inner=ttk.Frame(col)
                  inner.pack(fill=BOTH,expand=YES)
                  self.col_frames[status]=inner

      def _define_col(self,key,label,width,anchor):
                  self.tree.heading(key,text=label,anchor=anchor)
                  self.tree.column(key,width=width,anchor=anchor,stretch=True)
      def _build_statusbar (self):
            bar=ttk.Frame(self, bootstyle=SECONDARY) 
            bar.pack(fill=X,pady=(10,0))       
            self.status_var=StringVar(value="Ready")
            self.clock_var=StringVar(value=datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            ttk.Label(bar,textvariable=self.status_var).pack(side=LEFT,padx=6)
            ttk.Label(bar,textvariable=self.clock_var).pack(side=RIGHT, padx=6)

      def open_add_dialog(self):
            TaskDialog(self, on_save=self._add_task)
      
      def open_edit_dialog(self):
            iid=self._selected_iid()
            if not iid:
                  messagebox.showinfo("Edit Task","Please select a task to edit")
                  return
            task=next((t for t in self.tasks if t.id==iid),None)
            if not task:
                  messagebox.showerror("Edit Task","Could not find the task asociated with the iid") 
                  return
            def apply_edits(newtitle:str,newsubject:str,newdue:str,newstatus:str):
                  task.title=newtitle
                  task.subject=newsubject
                  task.duedate=newdue
                  task.status=newstatus
                  self.status("Task has been updated")
                  self._persist()
                  self.refresh_views()
            TaskDialog(self,on_save=apply_edits,task=task)         
            
      def _add_task(self,title:str,subject:str, due:str,status:str):
            t=Task(id=str(uuid.uuid4()),title=title,subject=subject,duedate=due,status=status)
            self.tasks.append(t)
            self.status("Task Added")
            self._persist()
            self.refresh_views()

      def delete_selected(self):
            iid=self._selected_iid()
            if not iid:
                  return
            if messagebox.askyesno("Delete", "Delete selected task?"):
                  self.tasks=[t for t in self.tasks if t.id !=iid]
                  self.status("Task Deleted")
                  self._persist()
                  self.refresh_views()
            
      def _selected_iid(self) -> Optional[str]:
            sel=self.tree.selection()
            if not sel:
                  return None
            return sel[0]
      def _sort_by(self,key:str):
            if self.sort_key == key:
                  self.sort_reverse = not self.sort_reverse
            else:
                  self.sort_key, self.sort_reverse = key,False
            self.refresh_table()
      def _filtered_sorted(self) -> List[Task]:
            q=self.search_var.get().strip().lower() 
            items=self.tasks
            if q:
                  items=[t for t in items if q in t.title.lower() or q in t.subject.lower()]
            keyfunc={
                  "title":lambda t: t.title.lower(),
                  "subject":lambda t: t.subject.lower(),
                  "duedate":lambda t:t.duedate,
            }.get(self.sort_key, lambda t:t.duedate)
            return sorted(items, key=keyfunc,reverse=self.sort_reverse)
      def refresh_table(self):
            for iid in self.tree.get_children():
                  self.tree.delete(iid)
            today= date.today()
            
            for i,t in enumerate(self._filtered_sorted()):
                  tags=["even" if i % 2 ==0 else "odd"]
                  chk=CHECK_FULL if t.status=="Done" else CHECK_EMPTY
                  
            d=parse_date(t.duedate)
            if d:
                  if d < today:
                        tags.append("overdue")
                  elif d == today:
                        tags.append("today")
            self.tree.insert(
                  "", tk.END, iid=t.id,
                  values=(chk,t.title,t.subject,t.duedate, t.status),
                  tags=tuple(tags)
            )

      def refresh_views(self):
            self.refresh_table()
            self.refresh_board()
      
      def refresh_board(self):
            for status, frame in self.col_frames.items():
                  for child in frame.winfo_children():
                        child.destroy()
            for t in self._filtered_sorted():
                  parent=self.col_frames.get(t.status)
                  if not parent:
                        continue
                  card=ttk.Frame(parent, padding=8)
                  card.pack(fill=X,pady=6)
                  ttk.Label(card, text=t.title, font=("Segoe U",10,"bold")).pack(anchor=W)
                  ttk.Label(card,text=f"{t.subject}- Due {t.duedate}").pack(anchor=W)
      
      def status(self,msg:str):
            self.status_var.set(msg)

      def _tick(self):
            self.clock_var.set(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))   
            self.after(1000,self._tick)

      def _on_tree_click(self, event):
            region=self.tree.identify_region(event.x, event.y)
            if region !="cell":
                  return
            col=self.tree.identify_column(event.x)
            row_iid=self.tree.identify_row(event.y)
            if not row_iid:
                  return
            if col !="#1":
                  return
            task = next((t for t in self.tasks if t.id == row_iid), None)
            if not task:
                  return
            
            if task.status=="Done":
               task.status="To Do"
               self.status("Marked as To Do")
            else:
                  task.status="Done"
                  self.status("Marked as Done")
            
            self._persist()
            self.refresh_views()
      def _load_initial(self):
            loaded=self.storage.load()
            self.tasks=loaded
            self.refresh_views()
            self.status(f"Loaded {len(self.tasks)} task(s).")
      def _persist(self):
            try:
                  self.storage.save(self.tasks)
            except Exception as e:
                  messagebox.showerror("Save Error", f"Could not save tasks:\n{e}")
      def import_csv(self):
            path= fd.askopenfilename(
                  title="Import CSV",
                  filetypes=[("CSV Files", "*.csv"), ("ALL Files", "*.*")]
            )
            if not path:
                  return
            added = skipped_dup=invalid = 0
            existing_ids = {t.id for t in self.tasks}
            try:
                  with open(path, "r", encoding="utf-8", newline="") as f:
                        reader=csv.DictReader(f)
                        missing = [h for h in ["title", "subject", "duedate"]if h not in reader.fieldnames]
                        if missing:
                              messagebox.showerror("Import CSV", f"Missing required column(s): {','.join(missing)}")
                              return
                        for row in reader:
                              title=(row.get("title")or "").strip()
                              subject=(row.get("subject")or "").strip()
                              duedate=(row.get("duedate")or "").strip()
                              status=(row.get("status")or "To Do").strip()
                              tid=(row.get("id")or "").strip()
                              if not title or not subject or not valid_date(duedate):
                                    invalid +=1
                                    continue
                              if status not in statusoptions:
                                    status="To Do"
                              if not tid:
                                    tid= str(uuid.uuid4())
                              if tid in existing_ids:
                                    skipped_dup +=1
                                    continue
                              self.tasks.append(Task(id=tid,title=title, subject=subject,duedate=duedate, status=status))
                              existing_ids.add(tid)
                              added +=1
            except Exception as e:
                  messagebox.showerror("Import CSV", f"Could not import file:\n{e}")
                  return

            self.__persist()
            self.refresh_views()
            messagebox.showinfo(
                  "Import CSV",
                  f"Imported from: {os.path.basename(path)}\n\n"
                  f"Added: {added}\n"
                  f"Skipped (duplicate ids): {skipped_dup}\n"
                  f"Invalid rows: {invalid}"
            )

      def export_csv(self):
            path = fd.asksaveasfilename(
                  title="Export CSV",
                  defaultextension=".csv",
                  filetypes=[("CSV Files", "*.csv")]

            )
            if not path:
                  return
                  
            try:
                  with open(path, "w", encoding="utf-8", newline="") as f:
                        writer=csv.DictWriter(f, fieldnames=CSV_HEADERS)
                        writer.writeheader()
                        for t in self.tasks:
                              writer.writerow({
                                    "id": t.id,
                                    "title": t.title,
                                    "subject": t.subject,
                                    "duedate": t.duedate,
                                    "status": t.status
                              })
            except Exception as e:
                  messagebox.showerror("Export CSV", f"Could not expert file:\n{e}")
                  return
            messagebox.showinfo("Export CSV", f"Exported {len(self.tasks)} task(s) to:\n{path}")
      
      def backup_json(self):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts=datetime.now().strftime("%Y/%m/%d/%H/%M/%S")
            path= os.path.join(BACKUP_DIR, f"planner-{ts}.json")

            try:
                  payload = [asdict(t) for t in self.tasks]
                  with open(path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
            except Exception as e:
                  messagebox.showerror("Backup JSON", f"Could not create backup:\n{e}")
            messagebox.showinfo("Backup JSON", f"Backup saved to:\n{path}")

      def restore_json(self):
            path=fd.askopenfilename(
                  title="Restore from JSON",
                  filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            if not path:
                  return
            if not messagebox.askyesno("Restore JSON", "This will replace all current tasks.\nContinue?"):
                  return
            try:
                  with open(path, "r", encoding="utf-8") as f:
                       raw=json.load(f)
            except Exception as e:
                  messagebox.showerror("Restore JSON", f"Could not read backup:\n{e}")
                  return
            restored: List[Task]=[]
            try:
                  if isinstance(raw, list):
                        for item in raw:
                              if not isinstance(item,dict):
                                    continue
                              tid=str(item.get("id")or uuid.uuid4())
                              title=str(item.get("title")or "").strip()
                              subject=str(item.get("subject")or "").strip()
                              duedate=str(item.get("duedate")or "").strip()
                              status=str(item.get("status")or "").strip()
                              if not title or not subject or not valid_date(duedate):
                                    continue
                              if status not in statusoptions:
                                    status="To Do"
                              restored.append(Task(id=tid, title=title, subject=subject,duedate=duedate,status=status))
            except Exception as e:
                  messagebox.showerror("Restore JSON", f"Backup content invalid:\n{e}")
                  return
            self.tasks=restored
            self.__persist()
            self.refresh_views()
            messagebox.showinfo("Restore JSON", f"Restored {len(self.tasks)} task(s from:\n{path})")
     
      def on_close(self):
            try:
                  self._persist()
            finally:
                  self.winfo_toplevel().destroy()

def main():
            style=Style(theme="minty")
            root=style.master
            root.title(apptitle)
            root.geometry("900x560")

            app=App(root)

            root.protocol("WM_DELETE_WINDOW",app.on_close)
            root.mainloop()
      
if __name__ == "__main__":
            main()


      




            

    

