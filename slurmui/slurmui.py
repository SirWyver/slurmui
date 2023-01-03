import io
from textual.app import App, ComposeResult
from textual.widgets import DataTable
from textual.widgets import Button, Header, Footer, Static, Label, TextLog, Input
from textual.containers import Container, Vertical 
from textual.containers import Grid
from textual.screen import Screen
import subprocess
import pandas as pd
import re
import os

### ---> FOR DEBUGGING

SQUEUE_DEBUG = """
  JOBID PA                                     NAME  USER    STATE       TIME TIME_L NODE NODELIST(REASON)
            190689 in                              interactive bob  RUNNING       9:46 6:00:00    1 lothlann
            190663 su                             triplane3_ll bob  RUNNING    2:56:36 4-00:00:00    1 himring
            190662 su                             triplane2_ll bob  RUNNING    2:56:40 4-00:00:00    1 himring
            190661 su                             triplane1_ll bob  RUNNING    2:56:46 4-00:00:00    1 himring
            190660 su                              triplane1_l bob  RUNNING    2:57:04 4-00:00:00    1 himring
            190659 su                              triplane2_l bob  RUNNING    2:57:10 4-00:00:00    1 balrog
            190658 su                              triplane3_l bob  RUNNING    2:57:28 4-00:00:00    1 balrog
            190657 su                              triplane3_m bob  RUNNING    2:57:31 4-00:00:00    1 balrog
            190656 su                              triplane2_m bob  RUNNING    2:57:36 4-00:00:00    1 balrog
            190655 su                              triplane1_m bob  RUNNING    2:57:39 4-00:00:00    1 balrog
            190654 su                              triplane1_m bob  RUNNING    2:57:43 4-00:00:00    1 angmar
            190651 su                              triplane0_m bob  RUNNING    3:03:06 4-00:00:00    1 valinor
            190650 su                             triplane0_ll bob  RUNNING    3:03:13 4-00:00:00    1 valinor
            190649 su                              triplane0_l bob  RUNNING    3:03:17 4-00:00:00    1 valinor
"""

def sqeue_debug():
    SQUEUE_DEBUG2 = re.sub(' +', ' ', SQUEUE_DEBUG)
    data = io.StringIO(SQUEUE_DEBUG2)
    df = pd.read_csv(data, sep=" ")
    del df[df.columns[0]]
    return df

DEBUG = False

#### <---

class SlurmUI(App):

    BINDINGS = [
        ("d", "stage_delete", "Delete job"),
        ("r", "refresh_table", "Refresh"),
        ("l", "display_log", "Log"),
        ("q", "abort_quit", "Quit"),
        ("enter", "confirm", "Confirm"),
        ("escape", "abort_quit", "Abort"),  
        # ("k", "scroll_up", "Up")    

    ]
    STAGE = None
    def compose(self) -> ComposeResult:
        self.header = Header()
        self.footer = Footer()
        self.table = DataTable( id="table")
        self.txt_log = TextLog(wrap=True, highlight=True, id="info")
        yield self.header
        yield Container(self.table, self.txt_log)
        yield self.footer

    def update_squeue_table(self, set_colums=False):
        self.table.clear()
        squeue_df = get_squeue() if not DEBUG else sqeue_debug()
        if set_colums:
            self.table.add_columns(*squeue_df.columns)
        for row in squeue_df.iterrows():
            table_row = [str(x) for x in row[1].values]
            self.table.add_row(*table_row)
        self.table.focus()

    def action_refresh_table(self):
        self.update_squeue_table()

    def on_mount(self):
        self._minimize_text_log()

    def on_ready(self) -> None:
        self.update_squeue_table(set_colums=True)

    # def action_modal(self):
    #     log_screen = LogScreen()
    #     #log_screen.load_log()
    #     self.push_screen(log_screen)
    #     log_screen.on_ready()

    def _get_selected_job(self):
        selected_column = self.table.cursor_cell.row
        job_id = self.table.data[selected_column][0]
        job_name = self.table.data[selected_column][2]
        return job_id, job_name

    def _minimize_text_log(self):
        self.table.styles.height="80%"
        self.txt_log.styles.max_height="10%"
        self.txt_log.can_focus = False
        self.txt_log.styles.border = ("heavy","grey")
    def _maximize_text_log(self):
        self.table.styles.height="0%"
        self.txt_log.styles.max_height="100%"
        self.txt_log.can_focus = True
        self.txt_log.styles.border = ("heavy","white")

    def action_stage_delete(self):
        job_id, job_name = self._get_selected_job()
        self.txt_log.clear()
        self.txt_log.write(f"Delete: {job_id} - {job_name}? Press <<ENTER>> to confirm")
        self.STAGE = {"action": "delete", "job_id": job_id, "job_name": job_name}

    def action_display_log(self):
        job_id, job_name = self._get_selected_job()
        if not DEBUG:
            log_fn = get_log_fn(job_id)
            txt_lines = read_log(log_fn)
        else:
            txt_lines = read_log("~/ram_batch_triplane0_l1.txt")

        self._maximize_text_log()
        self.txt_log.clear()
        for text_line in txt_lines:
            self.txt_log.write(text_line)

        self.STAGE = {"action": "log", "job_id": job_id, "job_name": job_name}

    def action_confirm(self):
        if self.STAGE is not None:
            self.txt_log.clear()
            # job to delete
            if self.STAGE["action"] == "delete":
                perform_scancel(self.STAGE['job_id'])
                self.txt_log.write(f"{self.STAGE['job_id']} - {self.STAGE['job_name']} deleted")
                self.update_squeue_table()
                self.STAGE = None


    def action_abort(self):
        if self.STAGE is not None:
            if self.STAGE["action"] == "log":
                self._minimize_text_log()
            self.txt_log.clear()
            self.STAGE = None

    def action_abort_quit(self):
        if self.STAGE is None:
            # self.emit_no_wait(message=Message())
            self.action_quit()
        else:
            self.action_abort()


def perform_scancel(job_id):
    os.system(f"""scancel {job_id}""")


def get_squeue():
    response_string = subprocess.check_output("""squeue --format="%.18i %.2P %.40j %.5u %.8T %.10M %.6l %.4D %R" --me -S T""", shell=True).decode("utf-8")
    formatted_string = re.sub(' +', ' ', response_string)
    data = io.StringIO(formatted_string)
    df = pd.read_csv(data, sep=" ")
    del df[df.columns[0]]
    return df 

def get_log_fn(job_id):
    response_string = subprocess.check_output(f"""scontrol show job {job_id} | grep StdOut""", shell=True).decode("utf-8")
    formatted_string = response_string.split("=")[-1].strip()
    return formatted_string

def read_log(fn, num_lines=100):
    with open(os.path.expanduser(fn), 'r') as f:
        txt_lines = list(f.readlines()[-num_lines:])
    
    return txt_lines

def run_ui(debug=False):
    if debug:
        # global for quick debugging
        global DEBUG
        DEBUG = True
    app = SlurmUI()
    app.run()

if __name__ == "__main__":
    run_ui()