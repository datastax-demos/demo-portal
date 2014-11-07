import time

from runner import run

def stop_all():
    for line in run('docker ps').stdout.split('\n'):
        container_id = line.split()[0]
        run('docker kill %s' % container_id)

def wait_for_image(image):
        # wait for image to become available
        while True:
            stdout = run('docker images').stdout
            if image in stdout:
                break
            time.sleep(2)
