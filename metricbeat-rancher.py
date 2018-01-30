#!/usr/bin/python3

import time
import urllib.parse
import urllib.request
import json
import yaml
import os

kafkaAdress = os.environ.get('KAFKA_HOSTNAME_PORT')
project = os.environ.get('PROJECT_NAME')
type = os.environ.get('PROJECT_TYPE')
retention = os.environ.get('PROJECT_RETENTION')
period = os.environ.get('MONITORING_FREQUENCY')

def get_general_config():
    return {
        'metricbeat.config.modules' : {
            'path': '${path.config}/modules.d/*.yml',
            'reload.enabled': True,
            'reload.period': '120s'
        },
        'fields_under_root': True,
        'fields' : {
            'project': project ,
            'type': type,
            'retention': retention
        }
    }

def get_output_config():
    return {
        'output.kafka' : {
            'enabled': True,
            'hosts': [kafkaAdress],
            #'hosts': ['54.76.190.172:9092'],
            'topic': 'monicatopic',
            'codec': ['json']
        }
    }

def get_current_metadata_entry(entry):
    headers = {
        'User-Agent': "prom-rancher-sd/0.1",
        'Accept': 'application/json'
    }
    req = urllib.request.Request('http://rancher-metadata.rancher.internal/2015-12-19/%s' % entry, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf8 '))

def is_monitored_service(service):
    # don't monitor container's that don't have IP yet
    if not 'primary_ip' in service:
        return False
    return 'labels' in service and 'com.metricbeat.monitoring' in service['labels'] and service['labels']['com.metricbeat.monitoring'] == 'true'


def monitoring_config(service):
    return {
        'module': 'prometheus',
        'metricsets' :  ['collector'],
        'enabled': True,
        'period': period,
        'hosts': [service['primary_ip'] + ':' + (service['labels']['com.metricbeat.port'] if 'com.metricbeat.port' in service['labels'] else '8080')],
        'metrics_path': service['labels']['com.metricbeat.metricspath'] if 'com.metricbeat.metricspath' in service['labels'] else '/metrics',
        'namespace': 'monica'
    }


def get_monitoring_config():
    return list(map(monitoring_config, filter(is_monitored_service, get_current_metadata_entry('containers'))))

def write_config_file(filename, get_config_function):
    #hostdict = get_hosts_dict(get_current_metadata_entry('hosts'))
    configlist = get_config_function()
    with open(filename, 'w') as config_file:
        print(yaml.dump(get_general_config(), default_flow_style = False),file=config_file)
        print("metricbeat.modules:\n" + yaml.dump(configlist, default_flow_style = False),file=config_file)
        print(yaml.dump(get_output_config(), default_flow_style = False),file=config_file)
    #newconfiglist = [ enrich_dict(x,hostdict) for x in configlist ]
    #tmpfile = filename+'.temp'
    #with open(tmpfile, 'w') as config_file:
    #    print(json.dumps(newconfiglist, indent=2),file=config_file)
    #    shutil.move(tmpfile,filename)

if __name__ == '__main__':
        while True:
            time.sleep(5)
            write_config_file('/metricbeat-rancher-data/metricbeat.yml', get_monitoring_config)