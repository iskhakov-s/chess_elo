import logging
import os
import datetime
from mpi4py import MPI

# logging format is setup so that sorting by year/month is simple
def mpi_log_setup(rank, filename, remove_existing=True):
    path = os.path.join("logs", f"rank_{rank}_{filename}.log")
    if remove_existing and os.path.exists(path):
        os.remove(path)
    logging.basicConfig(
        filename=path,
        filemode='a',  # 'a' to append, 'w' to overwrite
        format='%(levelname)s - %(message)s - %(asctime)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )
    
def mpi_log(rank, message, level=logging.INFO):
    logging.log(level, f"{message}; Rank {rank}")

# make sure that all processes are done, ie use a barrier, also don't open files
def mpi_combine_logs(rank, filename):
    logging.shutdown()
    if rank != 0:
        return
    log_dir = "logs"
    with open(os.path.join(log_dir, f"{filename}.log"), "w") as f:
        for r in range(MPI.COMM_WORLD.size):
            rank_log_name = os.path.join(log_dir, f"rank_{r}_{filename}.log")
            if os.path.exists(rank_log_name):
                with open(rank_log_name, "r") as rank_log_file:
                    f.write(rank_log_file.read())
                os.remove(rank_log_name)
                
    with open(os.path.join(log_dir, f"{filename}.log"), "r") as f:
        log_lines = f.readlines()

    sorted_logs = sorted(log_lines)

    with open(os.path.join(log_dir, f"{filename}.log"), "w") as f:
        f.write(f"Log generated on {datetime.datetime.now()}\n")
        f.writelines(sorted_logs)
        
# basic non-MPI logging setup wrapper
def log_setup(filename, format=None, remove_existing=True):
    path = os.path.join("logs", f"{filename}.log")
    if remove_existing and os.path.exists(path):
        os.remove(path)
    if format is None:
        format = "%(levelname)s - %(message)s - %(asctime)s"
    logging.basicConfig(
        filename=path,
        filemode='a',  # 'a' to append, 'w' to overwrite
        format=format,
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )