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
    status:str="To-Do"
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
            self._apply_styles()
            self._build_header()
            self._build_center()
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

            ttk.Label(top, text="  Status  ").pack(side=LEFT,padx=(12,0))
            self.cb_filter=ttk.Combobox(
                  top,
                  textvariable=self.status_filter_var,
                  values=["ALL"] + statusoptions,
                  state="readonly",
                  width=14
                  )
            self.cb_filter.pack(side=LEFT)
            self.cb_filter.bind("<<ComboBoxSelected>>",lambda e: self.refresh_views())
            
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
            cols=("title", "subject","duedate","status")
            self.tree=ttk.Treeview(self.tab_list,columns=cols,show="headings",height=14)
            self.tree.pack(fill=BOTH,expand=YES)
            self._define_col("title","Title",380,"w")
            self._define_col("subject","Subject",160,"w")
            self._define_col("duedate","Due Date",120,"w")
            self._define_col("status","Status",120,"w")

            for c in cols:
                  self.tree.heading(c,command=lambda col=c:self._sort_by(col))

            self.tree.tag_configure("even",background="white")
            self.tree.tag_configure("odd",background="white")
           
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
                  self.refresh_table()
            TaskDialog(self,on_save=apply_edits,task=task)         
            
      def _add_task(self,title:str,subject:str, due:str,status:str):
            t=Task(id=str(uuid.uuid4()),title=title,subject=subject,duedate=due,status=status)
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
                  "duedate":lambda t:t.duedate,
            }.get(self.sort_key, lambda t:t.duedate)
            return sorted(items, key=keyfunc,reverse=self.sort_reverse)
      def refresh_table(self):
            for iid in self.tree.get_children():
                  self.tree.delete(iid)
            for i,t in enumerate(self._filtered_sorted()):
                   self.tree.insert("",tk.END, iid=t.id,values=(t.title,t.subject,t.duedate,t.status),tags=("even" if i % 2 ==0 else "odd"))

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
                  ttk.Label(card, text=t.title, font=("Segoi U",10,"bold")).pack(anchor=W)
                  ttk.Label(card,text=f"{t.subject}- Due {t.duedate}").pack(anchor=W)
      
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


      




            

    

