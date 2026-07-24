from .base import Base

class Test(Base):
	def execute(self):

		from . import Facts

		ctrlObj = Facts.getShells().getBash(False)

		try:
			print("== whoami ==")
			print(ctrlObj.getCmd("whoami").get())

			print("== cd /var && pwd ==")
			ctrlObj.getCmd("cd /var").get()
			print(ctrlObj.getCmd("pwd").get())

			print("== ls -sh --color=none ==")
			print(ctrlObj.getCmd("ls -sh --color=none").get())

			print("== echo exit code of `false` ==")
			ctrlObj.getCmd("false").get()
			print(ctrlObj.getCmd("echo $?").get())

			print("== a command with a short timeout (expected to fail) ==")
			try:
				ctrlObj.getCmd("sleep 5", None, 500).get()
				print("UNEXPECTED: command did not time out")
			except Exception as e:
				print("Got expected timeout error:", e)

			import time
			print("(waiting for the abandoned `sleep 5` to actually finish...)")
			time.sleep(5)

			print("== ctrlObj still usable after the timeout ==")
			print(ctrlObj.getCmd("echo still_alive").get())

			print("All checks passed.")

		finally:
			ctrlObj.terminate()