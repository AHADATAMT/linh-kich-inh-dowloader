import os
import logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def download_file(url, path, file_name, session):
    resp = session.get(url, stream=True)
    if not os.path.exists(path):
        os.makedirs(path)
    try:
        with open(path + '/' + file_name, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        os.remove(path + '/' + file_name)
        print(e)


def download_sub(subs, path, file_name):
    with open(path + '/' + file_name, 'a') as f:
        i = 1
        for sub in subs:
            t_start = sub['transcriptStartAt']
            if i == len(subs):
                t_end = t_start + 5000
            else:
                t_end = subs[i]['transcriptStartAt']
            caption = sub['caption']
            logging.info(caption)
            f.write('%s\n' % str(i))
            f.write('%s --> %s\n' % (format_time(t_start), format_time(t_end)))
            f.write('%s\n\n' % caption)
            i += 1


def format_time(ms):
    seconds, milliseconds = divmod(ms, 1000)
    minitues, seconds = divmod(seconds, 60)
    hours, minitues = divmod(minitues, 60)
    return '%d:%02d:%02d,%02d' % (hours, minitues, seconds, milliseconds)
