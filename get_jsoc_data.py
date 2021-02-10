from dotenv import load_dotenv
from datetime import datetime, timedelta
import drms
import os

load_dotenv()

def aia_download_one(date, wave, out_dir):

    date = str(date).replace(' ', '_')

    qstr = '%s[%s][%d]{%s}' % ('aia.lev1_euv_12s', date, wave, 'image')

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    c = drms.Client()
    r = c.export(qstr, method='url', protocol='fits', email=os.environ['JSOC_EXPORT_EMAIL'])
    r.download(out_dir)

    fmt = '%Y-%m-%dT%H%M%SZ'
    filename = r.data['filename'][0]
    real_date = datetime.strptime(filename.split('.')[2], fmt)

    return filename, real_date


def aia_download_series(date_start, date_end, wave, out_dir):
    date_start = str(date_start).replace(' ', '_')
    date_end = str(date_end).replace(' ', '_')

    qstr = '%s[%s_UTC-%s_UTC][%d]{%s}' % ('aia.lev1_euv_12s', date_start, date_end, wave, 'image')

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    c = drms.Client()
    r = c.export(qstr, method='url', protocol='fits', email=os.environ['JSOC_EXPORT_EMAIL'])
    r.download(out_dir)


def download_hmi_mag_45s(date_start, date_end, out_dir):
    date_start = str(date_start).replace(' ', '_')
    date_end = str(date_end).replace(' ', '_')

    qstr = '%s[%s_UTC-%s_UTC]' % ('hmi.M_45s', date_start, date_end)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    c = drms.Client()
    r = c.export(qstr, method='url', protocol='fits', email=os.environ['JSOC_EXPORT_EMAIL'])
    r.download(out_dir)


if __name__ == "__main__":
    # my_date_start = datetime.datetime(2019, 7, 18, 4, 30, 30, 5)
    # my_date_end = datetime.datetime(2019, 7, 18, 4, 31, 30, 5)
    my_date_start = datetime(2013, 9, 29, 21, 15, 00, 00)
    my_date_end = datetime(2013, 9, 30, 8, 00, 30, 00)

    # aia_download_series(my_date_start, my_date_end, 171, 'downloads/full_flare_12s')
    # download_hmi_mag_45s(my_date_start, my_date_end, 'downloads/hmi')
    download_aia_3m(my_date_start, 304, 'downloads/ris3')
