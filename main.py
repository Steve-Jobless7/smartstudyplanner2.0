import uuid

from dataclasses import dataclass

from datetime import datetime

from typing import List, Optional

import tkinter as tk

from tkinter import ttk, messagebox, StringVar

from ttkbootstrap import Style

from ttkbootstrap.constants import *
dateformat="%Y/%m/%d"
apptitle="Smart Study Planner"
statusoptions=["To Do", "Done","In progress"]
statusorder={a:b for b,a in enumerate(statusoptions)}

@dataclass
class Task:
    id:str
    title:str
    subject:str
    duedate:str
    status:str
def today_str()->str:
        return datetime.now().strftime(dateformat)
def valid_date(s:str)->bool:
        try:
            datetime.strptime(s,dateformat)
            return True
        except Exception:
            return False
class TaskDialog(tk.Toplevel):
      def __init__(self,parent,on_save,task:Optional[Task]=None):
            super().__init__(parent)
            self.title("Add Task" if task is None else "Edit Task")
            self.resizable(False,False)
            self.grab_set()
            self.on_save=on_save
            self.var_title=StringVar(value=task.title if task else "")
            self.var_subject=StringVar(value=task.subject if task else "")
            self.var_due=StringVar(value=task.due_date if task else today_str())
            self.var_status=StringVar(value=task.status if task else statusoptions[0])
            frm=ttk.Frame(self,padding=12)
            frm.pack(fill=BOTH,expand=YES)
            ttk.Label(frm,text="Title").grid(row=0,column=0,sticky=E,padx=6,pady=6)
            ttk.Entry(frm,textvariable=self.var_title,width=36).grid(row=0,column=1,sticky=W,padx=6,pady=6)
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
            self.bind("<Return>",lambda e:self.save())
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
            self.pack(fill=BOTH,expand=YES)
            self.tasks:List[Task]=[]
            self.search_var=StringVar()
            self.sort_key="due_date"
            self.sort_reverse=False
            self._apply_styles()
            self._build_header()
            self._build_table()
            self._build_statusbar()
            self._tick()
            self.bind_all("<Control-n>",lambda e:self.open_add_dialog())
            self.bind_all("<Delete>",lambda e:self.delete_selected())
            self.bind_all("<Control-e>",lambda e:self.open_edit_dialog())
      
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

            ttk.Button(top, text="Add Task (Ctrl+N)",bootstyle=SUCCESS,command=self.
            open_add_dialog).pack(side=RIGHT,padx=6)
            ttk.Button(top, text="Delete", bootstyle="DANGER", command=self.delete_selected).pack(side=RIGHT,padx=6)
            ttk.Button(top, text="Edit Task (Ctrl+E)",bootstyle=INFO,command=self.
            open_edit_dialog).pack(side=RIGHT,padx=6)
      def _build_table(self):
            cols=("title", "subject","due_date")
            self.tree=ttk.Treeview(self,columns=cols,show="headings",height=14)
            self.tree.pack(fill=BOTH,expand=YES)
            self._define_col("title","Title",380,"w")
            self._define_col("subject","Subject",160,"w")
            self._define_col("due_date","Due Date",120,"w")

            for c in cols:
                  self.tree.heading(c,command=lambda col=c:self._sort_by(col))

            self.tree.tag_configure("even",background="white")
            self.tree.tag_configure("odd",background="white")
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
            def apply_edits(newtitle:str,newsubject:str,newdue:str):
                  task.title=newtitle
                  task.subject=newsubject
                  task.duedate=newdue
                  self.status("Task has been updated")
                  self.refresh_table()
            TaskDialog(self,on_save=apply_edits,task=task)         
            
      def _add_task(self,title:str,subject:str, due:str):
            t=Task(id=str(uuid.uuid4()),title=title,subject=subject,due_date=due)
            self.tasks.append(t)
            self.status("Task Added")
            self.refresh_table()

      def delete_selected(self):
            iid=self._selected_iid()
            if not iid:
                  return
            if messagebox.askyesno("Delete", "Delete selected task?"):
                  self.tasks=[t for t in self.tasks if t.id !=iid]
                  self.status("Task Deleted")
                  self.refresh_table()
            
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
                  "due_date":lambda t:t.due_date,
            }.get(self.sort_key, lambda t:t.due_date)
            return sorted(items, key=keyfunc,reverse=self.sort_reverse)
      def refresh_table(self):
            for iid in self.tree.get_children():
                  self.tree.delete(iid)
            for i,t in enumerate(self._filtered_sorted()):
                   self.tree.insert("",tk.END, iid=t.id,values=(t.title,t.subject,t.due_date),tags=("even" if i % 2 ==0 else "odd"))
      def status(self,msg:str):
            self.status_var.set(msg)

      def _tick(self):
            self.clock_var.set(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))   
            self.after(1000,self._tick)
def main():
            style=Style(theme="minty")
            root=style.master
            root.title(apptitle)
            root.geometry("900x560")

            app=App(root)

            root.mainloop()
      
if __name__ == "__main__":
            main()


      




            

    

