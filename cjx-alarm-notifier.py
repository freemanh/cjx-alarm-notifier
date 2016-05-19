#!python2
# coding: utf-8
import urllib, calendar, md5, beanstalkc, json, time, yaml
from datetime import datetime
from dateutil import parser

def sendSMS(content, tele):
    timestamp = calendar.timegm(datetime.utcnow().timetuple())
    p = md5.new('_'.join(('520530', str(timestamp), 'topsky'))).hexdigest()
    smsurl = u'http://admin.sms9.net/houtai/sms.php?cpid={!s}&password={!s}&channelid={!s}&tele={!s}&msg={!s}&timestamp={!s}'.format('8604', p ,'6214', tele, content, timestamp)
    print(u'SMS request url:{!s}'.format(smsurl).encode('utf-8'))

    filehandle = urllib.urlopen(smsurl.encode('GBK'))
    print('SMS web service respose code:{!s}'.format(filehandle.getcode()))

    status = filehandle.getcode()
    filehandle.close()

    if(status == 200):
        return True
    else:
        return False

def poll():
    print 'Start watching...'

    cfg = yaml.load(file('cfg.yml', 'r'))
    print cfg

    beanstalk = beanstalkc.Connection(host=cfg['host.beanstalkd'])
    for tube in ['alarm.poweroff', 'alarm.reading1', 'alarm.reading2']:
        beanstalk.watch(tube)

    while True:
        job = beanstalk.reserve(5)
        if job is None:
            continue

        print u'message body:{!s}'.format(job.body.encode('utf-8'))
        body = json.loads(job.body)

        addedTime = parser.parse(body['addedTime'])

        tube = job.stats()['tube']
        if(tube == 'alarm.poweroff'):
            content = u'{:%H:%M} 设备: {!s}出现断电报警，请及时处理！'.format(addedTime, body['device'])
        elif(tube =='alarm.reading1'):
            content = u'{:%H:%M} 传感器: {!s} 温度出现异常！当前温度: {:.1f}, 正常温度区间为:[{:.1f} - {:.1f}]'.format(addedTime, body['sensor'], body['reading'], body['min'], body['max'])
        elif(tube == 'alarm.reading2'):
            content = u'{:%H:%M} 传感器: {!s} 湿度出现异常！当前湿度: {:.1f}, 正常湿度区间为:[{:.1f} - {:.1f}]'.format(addedTime, body['sensor'], body['reading'], body['min'], body['max'])
        else:
            content = None

    
        print content.encode('utf-8')
        succ = sendSMS(content, body['mobile'])
        if succ:
            job.delete()
        else:
            job.release(10)

        time.sleep(10)

    beanstalk.close()

def addPoweroffJob():
    cfg = yaml.load(file('cfg.yml', 'r'))
    bt = beanstalkc.Connection(host=cfg['host.beanstalkd'])
    bt.use('alarm.poweroff')
    bt.put(json.dumps({u'device':'中文设备', 'mobile': '15308039727', 'addedTime': '2016-05-17T23:25:00+08:00'}))
    bt.close()

def addReadingJob():
    cfg = yaml.load(file('cfg.yml', 'r'))
    bt = beanstalkc.Connection(host=cfg['host.beanstalkd'])
    #bt.use('alarm.reading1')
    bt.use('alarm.reading2')
    bt.put(json.dumps({'sensor':'test', 'mobile': '15308039727', 'reading':10.0, 'min': 15.0, 'max': 20.0, 'addedTime': '2016-05-17T23:25:00+08:00'}))
    bt.close()

def deleteJob():
    cfg = yaml.load(file('cfg.yml', 'r'))
    bt = beanstalkc.Connection(host=cfg['host.beanstalkd'])
    bt.watch('alarm.reading2')
    job = bt.reserve(5)
    if job is not None:
        print job
        job.delete()
    bt.close()

if __name__ == '__main__':
    poll()
    #addPoweroffJob()
    #addReadingJob()
    #deleteJob()