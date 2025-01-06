import sys
import io
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable
from textual.widgets import Button, Header, Footer, Static, Label, RichLog, Input
from textual.containers import Container, Vertical 
from textual.containers import Grid
from textual.screen import Screen
import subprocess
import pandas as pd
import re
import os
if __name__ == "__main__":
    from _version import __version__
else:
    from ._version import __version__


DEBUG = False
if DEBUG:
    from debug_strings import SINFO_DEBUG, SQUEUE_DEBUG

class SlurmUI(App):

    cluster = None

    BINDINGS = [
        Binding("d", "stage_delete", "Delete job"),
        Binding("l", "display_log", "Log"),
        Binding("e", "display_error", "Error"),
        Binding("g", "display_gpu", "GPU"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "sort", "Sort"),
        Binding("q", "abort_quit", "Quit"),
        Binding("enter", "confirm", "Confirm", priority=True),
        Binding("escape", "abort_quit", "Abort"),
        # ("k", "scroll_up", "Up")    

    ]
    STAGE = {"action": "monitor"}
    gpu_overview_df = None
    sqeue_df =None

    def compose(self) -> ComposeResult:
        self.header = Header()
        self.footer = Footer()
        self.table = DataTable( id="table")
        self.table.zebra_stripes = True
        self.txt_log = RichLog(wrap=True, highlight=True, id="info")
        yield self.header
        yield Container(self.table, self.txt_log)
        yield self.footer

    
    def query_squeue(self, sort_column=None, sort_ascending=True):
        squeue_df = get_squeue() 
        if sort_column is not None:
            squeue_df = squeue_df.sort_values(squeue_df.columns[sort_column],ascending=sort_ascending)
        self.sqeue_df = squeue_df
        return squeue_df

    def update_squeue_table(self, sort_column=None, sort_ascending=True):
        self.table.clear(columns=True)
        squeue_df = self.query_squeue(sort_column=sort_column, sort_ascending=sort_ascending)
        # add device information
        squeue_df["GPU_IDS"] = "N/A"
        real_session_mask = squeue_df["PA"]!="in"
        if real_session_mask.any():
            squeue_df["GPU_IDS"][real_session_mask] =squeue_df[real_session_mask]["JOBID"].apply(lambda x: get_job_gpu_ids(x))
        # self.table.columns = []
        self.table.add_columns(*squeue_df.columns)
        for row in squeue_df.iterrows():
            table_row = [str(x) for x in row[1].values]
            self.table.add_row(*table_row)
        self.table.focus()

    def action_refresh(self):
        self.query_gpus()
        if self.STAGE["action"] == "monitor":
            self.update_squeue_table()
        elif self.STAGE["action"] == "log":
            self.update_log(self.STAGE["job_id"], False)
        elif self.STAGE["action"] == "error":
            self.update_log(self.STAGE["job_id"], True)
        elif self.STAGE["action"] == "gpu":
            self.update_gpu_table()

    def on_mount(self):
        self._minimize_text_log()

    def on_ready(self) -> None:
        self.update_squeue_table()
        self.query_gpus()

    # def action_modal(self):
    #     log_screen = LogScreen()
    #     #log_screen.load_log()
    #     self.push_screen(log_screen)
    #     log_screen.on_ready()

    def _get_selected_job(self):
        row_idx = self.table.cursor_row
        row = self.table.get_row_at(row_idx)
        job_id = row[0]
        job_name = row[2]
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
        if self.STAGE['action'] == "monitor":
            try:
                job_id, job_name = self._get_selected_job()
                self.txt_log.clear()
                self.txt_log.write(f"Delete: {job_id} - {job_name}? Press <<ENTER>> to confirm")
                self.STAGE = {"action": "delete", "job_id": job_id, "job_name": job_name}
            except Exception as e:
                self.txt_log.clear()
                self.txt_log.write(str(e))


    def action_display_log(self):
        try:
            if self.STAGE["action"] == "monitor":
                job_id, job_name = self._get_selected_job()
                self.STAGE = {"action": "log", "job_id": job_id, "job_name": job_name}
                self._maximize_text_log()
                self.update_log(job_id)
        except Exception as e:
            self.txt_log.clear()
            self.txt_log.write(str(e))

    def action_display_error(self):
        try:
            if self.STAGE["action"] == "monitor":
                job_id, job_name = self._get_selected_job()
                self.STAGE = {"action": "error", "job_id": job_id, "job_name": job_name}
                self._maximize_text_log()
                self.update_log(job_id, True)
        except Exception as e:
            self.txt_log.clear()
            self.txt_log.write(str(e))

    def query_gpus(self,  sort_column=None, sort_ascending=True):
        overview_df = get_sinfo()
        if sort_column is not None:
            overview_df = overview_df.sort_values(overview_df.columns[sort_column],ascending=sort_ascending)
        
        self.gpu_overview_df = overview_df
        # also change the title to include GPU information
        total_num_gpus = overview_df["#Total"].sum()
        total_available = overview_df["#Avail"].sum()
        self.title = f"SlurmUI --- GPU STATS: {total_available}/{total_num_gpus} -- Version: {__version__}"
        return overview_df


    def update_gpu_table(self, sort_column=None, sort_ascending=True):
        self.table.clear(columns=True)
        overview_df = self.query_gpus(sort_column=sort_column, sort_ascending=sort_ascending)
        self.table.add_columns(*overview_df.columns)
        for row in overview_df.iterrows():
            table_row = [str(x) for x in row[1].values]
            self.table.add_row(*table_row)
        self.table.focus()



    def action_display_gpu(self):
        self.STAGE = {"action": "gpu"}
        try:
            self.update_gpu_table()
        except Exception as e:
            self.txt_log.clear()
            self.txt_log.write(str(e))

    def action_sort(self):
        # selected_column = self.table.cursor_cell
        column_idx = self.table.cursor_column
        if column_idx != self.STAGE.get("column_idx"):
            self.STAGE["sort_ascending"] = False
        else:
            self.STAGE["sort_ascending"] = not self.STAGE.get("sort_ascending",True)
        self.STAGE['column_idx'] = column_idx
        if self.STAGE["action"] == "monitor":
            self.update_squeue_table(sort_column=column_idx, sort_ascending=self.STAGE["sort_ascending"])
        elif self.STAGE["action"] == "gpu":
            self.update_gpu_table(sort_column=column_idx, sort_ascending=self.STAGE["sort_ascending"])

        self.table.cursor_coordinate  = (0,column_idx)


    def update_log(self, job_id, error_log=False):
        if not DEBUG:
            log_fn = get_log_fn(job_id, error_log=error_log)
            txt_lines = read_log(log_fn)
        else:
            txt_lines = read_log("~/ram_batch_triplane0_l1.txt")

        self.txt_log.clear()
        for text_line in txt_lines:
            self.txt_log.write(text_line)



    def action_confirm(self):
        if self.STAGE["action"] == "monitor":
            pass
        else:
            self.txt_log.clear()
            # job to delete
            if self.STAGE["action"] == "delete":
                perform_scancel(self.STAGE['job_id'])
                self.txt_log.write(f"{self.STAGE['job_id']} - {self.STAGE['job_name']} deleted")
                self.update_squeue_table()
                self.STAGE["action"] = "monitor"


    def action_abort(self):
        if self.STAGE["action"] in ["log", "error"]:
            self._minimize_text_log()
        elif self.STAGE["action"] == "gpu":
            self.update_squeue_table()
        self.txt_log.clear()
        self.STAGE['action'] = "monitor"

    def action_abort_quit(self):
        if self.STAGE["action"] == "monitor":
            self.exit(0)
        else:
            self.action_abort()


def perform_scancel(job_id):
    os.system(f"""scancel {job_id}""")


def parse_gres_used(gres_used_str, num_total):
    if len(sys.argv) > 1:
        _, device, num_gpus, alloc_str = re.match(r"(.*):(.*):(.*)\(IDX:(.*)\)", gres_used_str).groups()
    else:
        _, device, num_gpus, alloc_str = re.match(r"(.*):(.*):(.*)\(IDX:(.*)\)", gres_used_str).groups()

    num_gpus = int(num_gpus)
    alloc_gpus = []
    for gpu_ids in alloc_str.split(","):
        if "-" in gpu_ids:
            start, end = gpu_ids.split("-")
            for i in range(int(start), int(end)+1):
                alloc_gpus.append(i)
        else:
            if gpu_ids == "N/A":
                pass
            else:
                alloc_gpus.append(int(gpu_ids))
            
    return {"Device": device,
            "#Alloc": num_gpus,
            "Free IDX": [idx for idx in range(num_total) if idx not in alloc_gpus]}


def parse_gres(gres_str):
    if len(sys.argv) > 1:
        _,num_gpus, _ = re.match(r"(.*):(.*)\(S:(.*)\)", gres_str).groups()
        num_gpus = int(num_gpus)
        return {"Device": "gpu",
                "#Total": num_gpus}

    else:
        try:
            _, device, num_gpus = re.match(r"(.*):(.*):(\d+)\(.*\)", gres_str).groups()
        except:
            _, device, num_gpus = re.match(r"(.*):(.*):(.*),.*", gres_str).groups()
            
        num_gpus = int(num_gpus)
        return {"Device": device,
                "#Total": num_gpus}





def get_sinfo():
    if DEBUG:
        response_string = SINFO_DEBUG
    else:
        if len(sys.argv) > 1:
            # cluster = sys.argv[2]
            filter_cluster = f"-p 'mcml-dgx-a100-40x8'"
        else:
            filter_cluster = f""
        response_string = subprocess.check_output(f"""sinfo --Node {filter_cluster} -O 'NodeHost:50,Gres:50,GresUsed:80,StateCompact,FreeMem,CPUsState'""", shell=True).decode("utf-8")
    formatted_string = re.sub(' +', ' ', response_string)
    data = io.StringIO(formatted_string)
    df = pd.read_csv(data, sep=" ")
    overview_df = [ ]# pd.DataFrame(columns=['Host', "Device", "#Avail", "#Total", "Free IDX"])
    for row in df.iterrows():
        node_available = row[1]["STATE"] in ["mix", "idle", "alloc"]

        # if "mcml" not in row[1]["HOSTNAMES"]:
        #     continue

        if row[1]['GRES'] != "(null)":
            host_info = parse_gres(row[1]['GRES'])
        else:
            continue

        if not node_available:
            host_info["#Total"] = 0 
        try:
            host_avail_info = parse_gres_used(row[1]['GRES_USED'] , host_info["#Total"])
            host_info.update(host_avail_info)
            host_info["#Avail"] = host_info['#Total'] - host_info["#Alloc"]
            host_info['Mem (GB)'] = int(row[1]["FREE_MEM"]) // 1024

            cpu_info = row[1]["CPUS(A/I/O/T)"].split("/")
            host_info['#CPUs Idle'] = cpu_info[1]
            host_info['#CPUs Alloc'] = cpu_info[0]
            host_info['Host'] = str(row[1]["HOSTNAMES"])

            overview_df.append(host_info)
        except Exception as e:
            pass #print(f"Error at: {row[1]['GRES_USED'], host_info["#Total"]}")

    overview_df = pd.DataFrame.from_records(overview_df).drop_duplicates("Host")
    overview_df = overview_df[['Host', "Device", "#Avail", "#Total", "Free IDX", "Mem (GB)", "#CPUs Idle", "#CPUs Alloc"]]
    return overview_df


def get_squeue():
    sep = "|"
    if DEBUG:
        response_string = SQUEUE_DEBUG
    else:
        response_string = subprocess.check_output(f"""squeue --format="%.18i{sep}%Q{sep}%.2P{sep}%.40j{sep}%.5u{sep}%.8T{sep}%.10M{sep}%.6l{sep}%S{sep}%.4D{sep}%R" --me -S T""", shell=True).decode("utf-8")
    formatted_string = re.sub(' +', ' ', response_string)
    data = io.StringIO(formatted_string)
    df = pd.read_csv(data, sep=sep)
    df.columns = [x.strip() for x in df.columns]
    return df 

def get_job_gpu_ids(job_id):
    try:
        # response_string = subprocess.check_output(f"""srun --jobid {job_id} '/bin/env' | grep SLURM_STEP_GPUS""", shell=True,stderr=subprocess.STDOUT, timeout=0.3).decode("utf-8")
        # response_string = subprocess.check_output(f"""scontrol --dd show job {job_id} | grep GRES=gpu:""", shell=True).decode("utf-8")
        # gpu_ids = re.match(response_string, ".*GRES=gpu:.*\(IDX:(.*)\)").groups()[0]
        # formatted_string = gpu_ids # response_string.split("=")[-1].strip()
        response_string = subprocess.check_output(f"""scontrol show jobid -dd {job_id} | grep GRES""", shell=True).decode("utf-8")
        formatted_string = response_string.split(":")[-1].strip()[:-1]
    except:
        return "N/A"
    return formatted_string


def get_log_fn(job_id, error_log=False):
    response_string = subprocess.check_output(f"""scontrol show job {job_id} | grep {'StdOut' if not error_log else 'StdErr'}""", shell=True).decode("utf-8")
    formatted_string = response_string.split("=")[-1].strip()
    return formatted_string

def read_log(fn, num_lines=100):
    with open(os.path.expanduser(fn), 'r') as f:
        txt_lines = list(f.readlines()[-num_lines:])
    
    return txt_lines

def run_ui(debug=False, cluster=None):
    if debug:
        # global for quick debugging
        global DEBUG
        DEBUG = True
    app = SlurmUI()
    app.cluster = cluster
    app.run()


if __name__ == "__main__":
    run_ui()
