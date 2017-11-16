from __future__ import print_function
import click, requests
import os, time, subprocess, sys

tag = 'f48dff2e-7fb7-49e8-b9bf-2013c9deff90'
base_url = 'https://api.digitalocean.com/v2'
headers= lambda api_key: { 'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % api_key }


def fetch_key():
    if not os.path.isfile('API_KEY'):
        print("file API_KEY does not exist. Please enter it with the --api-key flag.")
        sys.exit()
    with open('API_KEY', 'r') as f:
        api_key = f.readline().strip()
    return api_key

def retry(testfn, maxtries, fn, _str, errstr):
    """ retries function fn until testfn(fn()) returns true, or maxtries is reached """
    for tries in range(1, maxtries+1):
        print("Attempt #%s/%s: %s..." % (tries, maxtries, _str))
        output = fn()
        if testfn(output):
            break
    else:
        print("ERR: " + errstr)
        sys.exit()
    return output

@click.group()
def cli():
    pass


@cli.command('play')
@click.argument('filename', type=click.Path(exists=True))
@click.option('--api-key', type=str, default=fetch_key, help="Digital Ocean API key; if not provided on CLI, it must be provided in the file API_KEY")
@click.option('--subs', 'subs', flag_value=True, default=False, help="Whether or not subtitles are encoded in the movie. If they are, they'll be burned into the stream")
@click.option('--snapshot', default=None, help='Name of snapshot image to use instead of creating a brand new VM')
def play_movie(filename, api_key, subs, snapshot):
    FFMPEG_BIN = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'

    if snapshot:
        fn = lambda: spawn_snapshot(api_key, snapshot)
    else:
        fn = lambda: spawn_newserver(api_key)


    ip = retry(lambda o: o is not None, 3, fn, 
                    "Starting up the VM", 
                    "Could not spawn Digital Ocean VM. Please check Digital Ocean for more information.")
    try:
        wait_for_nginx(ip)

        if click.confirm('Start the movie?'):
            exec_ffmpeg(filename, ip, subs)


    except Exception as e:
        print(e)
    finally:
        print("Destroying server and exiting")
        destroy_server(api_key)
        print("Successfully destroyed the server")


@cli.command('play_movie')
@click.argument('filename', type=click.Path(exists=True))
@click.argument('ip_addr')
@click.option('--subs', 'subs', flag_value=True, default=False, help="Whether or not subtitles are encoded in the movie. If they are, they'll be burned into the stream")
def ffmpeg_command(filename, ip_addr, subs):
    exec_ffmpeg(filename, ip_addr, subs)

@cli.command('destroy_server')
@click.option('--api-key', type=str, default=fetch_key, help="Digital Ocean API key; if not provided on CLI, it must be provided in the file API_KEY")
def destroy(api_key):
    destroy_server(api_key)
    print("Successfully destroyed the server")


@cli.command('start_server')
@click.option('--api-key', type=str, default=fetch_key, help="Digital Ocean API key; if not provided on CLI, it must be provided in the file API_KEY")
def start_server(api_key):
    print("Starting new server")
    ip = spawn_newserver(api_key)
    wait_for_nginx(ip)
    print("Server is ready! Point an RTMP stream at rtmp://%s/live" % ip)

def exec_ffmpeg(filename, ip, subs):
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

def destroy_server(api_key):
    url = base_url + '/droplets?tag_name=' + tag
           
    def fn():
        code = requests.delete(url, headers=headers(api_key)).status_code
        time.sleep(5)
        return code

    retry(lambda code: code == 204, 3, fn, 
          "Trying to kill VM with tag %s" % tag,
          "Could not kill server; Please destroy it manually at digitalocean.com")
    

def spawn_snapshot(api_key):
    raise Exception("DIGITAL OCEAN SNAPSHOT NOT IMPLEMENTED")


def wait_for_nginx(ip):
    def fn():
        try:
            code = requests.get("http://" + str(ip)).status_code
        except requests.exceptions.ConnectionError:
            code = 0
        time.sleep(20)
        return code
    testfn = lambda code: code == 200

    retry(lambda code: code == 200, 20, fn, 
          "Waiting for nginx to finish compiling", 
          "Nginx still hasn't started, something probably went wrong.")
        

def spawn_newserver(api_key):
    with open('deploy.sh', 'r') as f:
        script = ''.join(f.readlines())
    data = {
        'name': 'StreamServer',
        'region': 'nyc3',
        'size': '512mb',
        'image': 'ubuntu-17-10-x64',
        'ssh_keys': None,
        'backups': False,
        'ipv6': False,
        'user_data': script,
        'monitoring': False,
        'volumes': None,
        'tags': [tag]
    }
    response = requests.post(base_url + '/droplets', json=data, headers=headers(api_key))
    if response.status_code != 202:
        print("Failed to create Digital Ocean VM. Is your API_KEY correct?")
        sys.exit()
        
    j = response.json()['droplet']
    _id = j['id']
    status = j['status']
    while status != 'active':
        time.sleep(5)
        response = requests.get(base_url + '/droplets/' + str(_id), headers=headers(api_key))
        if response.status_code != 200:
            # change this to listing the vm's, and ensuring our _id is missing from the list
            # if its still there, the user will need to destroy the vm themselves
            print("Something went wrong with VM creation, HTTP error %s" % response.status_code)
            return None
        j = response.json()['droplet']
        status = j['status']
    ip = j['networks']['v4'][0]['ip_address']
    print("VM at ip %s is now active" % ip)
    return ip

if __name__ == '__main__':
    cli()
