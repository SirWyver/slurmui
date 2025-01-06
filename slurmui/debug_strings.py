### ---> FOR DEBUGGING
# squeue --format="%.18i|%Q|%.2P|%.40j|%.8u|%.8T|%.10M|%.6l|%S|%.4D|%R" --me -S T
SQUEUE_DEBUG = """
             JOBID|PRIORITY|PA|                                    NAME|    USER|   STATE|      TIME|TIME_L|START_TIME|NODE|NODELIST(REASON)
            252034|1026111|le|                                    bash| normanm| RUNNING|     41:06|2-00:00:00|2024-12-30T10:29:13|   1|a100-st-p4d24xlarge-0
"""
# sinfo --Node "" -O 'NodeHost,Gres:50,GresUsed:80,StateCompact,FreeMem,CPUsState'
SINFO_DEBUG = """
HOSTNAMES                                                                       GRES                                              GRES_USED                                                                       STATE               FREE_MEM            CPUS(A/I/O/T)       
a100-st-p4d24xlarge-0                                                           gpu:A100:8(S:0-1)                                 gpu:A100:5(IDX:0,4-7)                                                           mix                 745329              32/64/0/96          
a100-st-p4d24xlarge-0                                                           gpu:A100:8(S:0-1)                                 gpu:A100:5(IDX:0,4-7)                                                           mix                 745329              32/64/0/96          
a100-st-p4d24xlarge-1                                                           gpu:A100:8(S:0-1)                                 gpu:A100:8(IDX:0-7)                                                             alloc               787148              96/0/0/96           
a100-st-p4d24xlarge-1                                                           gpu:A100:8(S:0-1)                                 gpu:A100:8(IDX:0-7)                                                             alloc               787148              96/0/0/96           
a100-st-p4d24xlarge-2                                                           gpu:A100:8(S:0-1)                                 gpu:A100:8(IDX:0-7)                                                             alloc               941862              96/0/0/96           
a100-st-p4d24xlarge-2                                                           gpu:A100:8(S:0-1)                                 gpu:A100:8(IDX:0-7)                                                             alloc               941862              96/0/0/96           
"""