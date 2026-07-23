from .base import Base

class Test(Base):
    def execute(self):

        from . import Facts

        shell = Facts.getShells().getBash(False)

        try:
            print("== whoami ==")
            print(shell.getCmd("whoami").get())

            print("== cd /var && pwd ==")
            shell.getCmd("cd /var").get()
            print(shell.getCmd("pwd").get())

            print("== ls -sh --color=none ==")
            print(shell.getCmd("ls -sh --color=none").get())

            print("== echo exit code of `false` ==")
            shell.getCmd("false").get()
            print(shell.getCmd("echo $?").get())

            print("== a command with a short timeout (expected to fail) ==")
            try:
                shell.getCmd("sleep 5", None, 500).get()
                print("UNEXPECTED: command did not time out")
            except Exception as e:
                print("Got expected timeout error:", e)

            import time
            print("(waiting for the abandoned `sleep 5` to actually finish...)")
            time.sleep(5)

            print("== shell still usable after the timeout ==")
            print(shell.getCmd("echo still_alive").get())

            print("All checks passed.")

        finally:
            shell.terminate()