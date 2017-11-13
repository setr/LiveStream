import click, requests
import os, time, subprocess, sys

def retry(testfn, maxtries, fn, _str, errstr):
    """ retries function fn until testfn(fn()) returns true, or maxtries is reached """
    for tries in range(1, maxtries+1):
        sys.stdout.write("\r\x1b[K" + "Attempt #%s/%s: %s..." % (tries, maxtries, _str))
        sys.stdout.flush()
        output = fn()
        if testfn(output):
            print ""
            return output
    
    print ""
    print("ERR: " + errstr)
    sys.exit()



@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--api-key', type=str, default=None, help="Digital Ocean API key; if not provided on CLI, it must be provided in the file API_KEY")
@click.option('--subs', 'subs', flag_value=True, default=False, help="Whether or not subtitles are encoded in the movie. If they are, they'll be burned into the stream")
@click.option('--snapshot', default=None, help='Name of snapshot image to use instead of creating a brand new VM')
def main(filename, api_key, subs, snapshot):
    FFMPEG_BIN = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
    if not api_key:
        if not os.path.isfile('API_KEY'):
            print("file API_KEY does not exist. Please enter it with the --api-key flag.")
            return 
        with open('API_KEY', 'r') as f:
            api_key = f.readline().strip()

    if snapshot:
        fn = lambda: spawn_snapshot(api_key, snapshot)
    else:
        fn = lambda: spawn_newserver(api_key)


    _id, ip = retry(lambda o: o[0] and o[1], 3, fn, 
                    "Starting up the VM", 
                    "Could not spawn Digital Ocean VM. Please check Digital Ocean for more information.")
    try:
        wait_for_nginx(ip)

        ffmpeg_command = ['ffmpeg',
                        '-re',
                        '-loglevel', 'warning',
                        '-i', filename,
                        '-c:v', 'libx264',
                        '-c:a', 'libmp3lame']
        if subs:
            ffmpeg_command += ['-filter:v', 'subtitles=' + filename]

        ffmpeg_command += [ '-ar', '44100',
                            '-ac', '1',
                            '-f', 'flv',
                            'rtmp://%s/live' % ip]
        print("Running command: " + ' '.join(ffmpeg_command))
        print("The stream is now live at rtmp://%s/live" % ip)
        print("Enjoy!")
        subprocess.call(ffmpeg_command)
    except Exception as e:
        print(e)
    finally:
        print("Destroying server and exiting")
        destroy_server(api_key, _id)


def destroy_server(api_key, _id):
    url = 'https://api.digitalocean.com/v2/droplets/' + str(_id)
           
    content_header = { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % api_key
    }
    def fn():
        code = requests.delete(url, headers=content_header).status_code
        time.sleep(5)
        return code


    retry(lambda code: code == 204, 10, fn, 
          "Trying to kill VM with ID %s" % _id, 
          "Could not kill server; Please destroy it manually at digitalocean.com")
    


def spawn_snapshot(api_key):
    raise Exception("DIGITAL OCEAN SNAPSHOT NOT IMPLEMENTED")


def wait_for_nginx(ip):
    def fn():
        try:
            code = requests.get("http://" + ip).status_code
            print("HELP2")
        except requests.exceptions.ConnectionError:
            code = 0
        time.sleep(20)
        return code
    testfn = lambda code: code == 200

    retry(lambda code: code == 200, 20, fn, 
          "Waiting for nginx to finish compiling", 
          "Nginx still hasn't started, something probably went wrong.")
        

def spawn_newserver(api_key):
    url = 'https://api.digitalocean.com/v2/'
    with open('deploy.sh', 'r') as f:
        script = ''.join(f.readlines())
    data = {
        'name': 'StreamServer',
        'region': 'nyc3',
        'size': '512mb',
        'image': '28892166',
        'ssh_keys': None,
        'backups': False,
        'ipv6': False,
        'user_data': script,
        'monitoring': False,
        'volumes': None,
        'tags': []
    }
    content_header = { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % api_key
    }
    response = requests.post(url + 'droplets', json=data, headers=content_header)
    if response.status_code != 202:
        print("Failed to create Digital Ocean VM. Is your API_KEY correct?")
        sys.exit()
        
    j = response.json()['droplet']
    _id = j['id']
    status = j['status']
    while status != 'active':
        time.sleep(5)
        response = requests.get(url + 'droplets/' + str(_id), headers=content_header)
        if response.status_code != 200:
            # change this to listing the vm's, and ensuring our _id is missing from the list
            # if its still there, the user will need to destroy the vm themselves
            print("Something went wrong with VM creation, HTTP error %s" % response.status_code)
            return None, None
        j = response.json()['droplet']
        status = j['status']
    ip = j['networks']['v4'][0]['ip_address']
    print("VM at ip %s is now active" % ip)
    return _id, ip

if __name__ == '__main__':
    main()
