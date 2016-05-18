#!python2
# coding: utf-8
import urllib, calendar, md5, mysql.connector, beanstalkc, json
from datetime import datetime
from dateutil import parser


def sendSMS(content, tele):
    timestamp = calendar.timegm(datetime.utcnow().timetuple())
    p = md5.new('_'.join(('520530', str(timestamp), 'topsky'))).hexdigest()
    smsurl = u'http://admin.sms9.net/houtai/sms.php?cpid={!s}&password={!s}&channelid={!s}&tele={!s}&msg={!s}&timestamp={!s}'.format('8604', p ,'6214', tele, content, timestamp)
    print(u'SMS request url:{!s}'.format(smsurl).encode('utf-8'))

    filehandle = urllib.urlopen(smsurl.encode('GBK'))
    print('SMS web service respose code:{!s}'.format(filehandle.getcode()))

    if(filehandle.getcode() == '200'):
        return True
    else:
        return False

    filehandle.close()

def poll():
    beanstalk = beanstalkc.Connection(host='192.168.99.100')
    for tube in ['alarm.poweroff', 'alarm.reading1', 'alarm.reading2']:
        beanstalk.watch(tube)


    job = beanstalk.reserve(5)
    if job is None:
        return

    body = json.loads(job.body)

    addedTime = parser.parse(body['addedTime'])

    tube = job.stats()['tube']
    if(tube == 'alarm.poweroff'):
        content = u'{:%H:%M} 设备: {!s}出现断电报警，请及时处理！'.format(addedTime, body['device'])
    elif(tube =='alarm.reading1'):
        content = u'传感器: {!s} 温度出现异常！当前温度: {:.1f}, 正常温度区间为:[{:.1f} - {:.1f}]'
    elif(tube == 'alarm.reading2'):
        content = u'传感器: {!s} 湿度出现异常！当前温度: {:.1f}, 正常温度区间为:[{:.1f} - {:.1f}]'
    else:
        content = None

    
    print content.encode('utf-8')
    succ = sendSMS(content, body['mobile'])
    if succ:
        job.delete()
    else:
        job.release(10)

    beanstalk.close()

def addJob():
    bt = beanstalkc.Connection(host='192.168.99.100')
    bt.use('alarm.poweroff')
    bt.put(json.dumps({'device':'test', 'mobile': '15308039727', 'addedTime': '2016-05-17T23:25:00+08:00'}))
    bt.close()

def deleteJob():
    bt = beanstalkc.Connection(host='192.168.99.100')
    bt.watch('alarm.poweroff')
    job = bt.reserve(5)
    if job is not None:
        print job
        job.delete()
    bt.close()
    
if __name__ == '__main__':
    poll()
    #addJob()
    #deleteJob()