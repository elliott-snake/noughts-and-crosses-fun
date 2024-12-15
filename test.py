import noughtsandcrosses as nac
import threading
import subprocess

# based on https://medium.com/@rohitobrai11/multithreading-in-python-running-2-scripts-in-parallel-8258c4635182#:~:text=Ensure%20you%20have%20all%20three,script2.py%20concurrently%20using%20multithreading.

def run_script(script_name):
    subprocess.run(["C:\\Users\\ellio\\PycharmProjects\\pythonProject\\venv\\Scripts\\python.exe", script_name])

if __name__ == "__main__":
    script1_thread = threading.Thread(target=run_script, args=("noughtsandcrosses.py",))
    script2_thread = threading.Thread(target=run_script, args=("noughtsandcrosses.py",))

    script1_thread.start()
    script2_thread.start()

    script1_thread.join()
    script2_thread.join()

    print("Both players have finished.")
