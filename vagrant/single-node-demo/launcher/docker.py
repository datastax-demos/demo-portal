from runner import run

def stop_all():
    for line in run('docker ps').stdout.split('\n'):
        container_id = line.split()[0]
        run('docker kill %s' % container_id)
