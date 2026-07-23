from .base import Base

class Test(Base):
    def execute(self):

        from . import Facts

        shell = Facts.getShells().getBash(False)

        try:
            print("== whoami ==")
            print(shell.get_cmd("whoami").get())

            print("== cd /var && pwd ==")
            shell.get_cmd("cd /var").get()
            print(shell.get_cmd("pwd").get())

            print("== ls -sh --color=none ==")
            print(shell.get_cmd("ls -sh --color=none").get())

            print("== echo exit code of `false` ==")
            shell.get_cmd("false").get()
            print(shell.get_cmd("echo $?").get())

            print("== a command with a short timeout (expected to fail) ==")
            try:
                shell.get_cmd("sleep 5", None, 500).get()
                print("UNEXPECTED: command did not time out")
            except Exception as e:
                print("Got expected timeout error:", e)

            import time
            print("(waiting for the abandoned `sleep 5` to actually finish...)")
            time.sleep(5)

            print("== shell still usable after the timeout ==")
            print(shell.get_cmd("echo still_alive").get())

            print("All checks passed.")

        finally:
            shell.terminate()