"""
This file is only relevant for developers.

This Python script compiles the C source code of the programs
that run on the Red Pitaya on the Red Pitaya itself

It should be run everytime changes are made to the acquire.c and configure.c files.
"""
import paramiko
import os

rp_address = "RP-f09013.local"
username = "root"
password = "changeme"

# Open SSH and SFTP connection
with paramiko.SSHClient() as ssh:
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(rp_address, username=username, password=password)
    sftp = ssh.open_sftp()

    # Make a temporary folder to compile sources
    TMP_ROOT = "tmpRPIQA"
    ssh.exec_command(f"mkdir {TMP_ROOT}")

    # Move source files
    files_to_move = ["acquire.c", "configure.c", "Makefile"]

    print("Transfering files...")
    for filename in files_to_move:
        sftp.put(os.path.join("src", "pyrpiqa" ,"rp_src", filename),
                    TMP_ROOT+"/"+filename)
        print(f"Transferred {filename}")

    print("Installing gcc and make")
    stdin, stdout, stderr = ssh.exec_command("apk add gcc make")
    for line in stderr.readlines():
        print(line)
    print("Output:")
    for line in stdout.readlines():
        print(line)

    print(
        "Compiling executables... Following is the output of the 'make all' command")

    stdin, stdout, stderr = ssh.exec_command(
        f"cd {TMP_ROOT} && make")
    print("Error(s):")
    for line in stderr.readlines():
        print(line)
    print("Output:")
    for line in stdout.readlines():
        print(line)

    sftp.get(f"{TMP_ROOT}/acquire", os.path.join("src", "pyrpiqa" ,"rp_src", "acquire"))
    sftp.get(f"{TMP_ROOT}/configure", os.path.join("src", "pyrpiqa" ,"rp_src", "configure"))
    stdin, stdout, stderr = ssh.exec_command(f"rm -rf {TMP_ROOT}")
    for line in stderr.readlines():
        print(line)
        print("Output:")
    for line in stdout.readlines():
        print(line)