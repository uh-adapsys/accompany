import os
import yaml

baseDir = os.path.dirname(os.path.realpath(__file__))

server_config = {}
with open(os.path.join(baseDir, 'http_server.yaml')) as config:
    server_config.update(yaml.load(config))
with open(os.path.join(baseDir, 'database.yaml')) as config:
    server_config.update(yaml.load(config))

locations_config = {}
locationDir = os.path.join(baseDir, 'Locations')
for fileName in [os.path.join(locationDir, f) for f in os.listdir(locationDir) if f.endswith('.yaml')]:
    with open(fileName) as config:
        locations_config.update(yaml.load(config))

robot_config = {}
locationDir = os.path.join(baseDir, 'Robots')
for fileName in [os.path.join(locationDir, f) for f in os.listdir(locationDir) if f.endswith('.yaml')]:
    with open(fileName) as config:
        robot_config.update(yaml.load(config))

siena_config = {}
with open(os.path.join(baseDir, 'siena.yaml')) as config:
    siena_config.update(yaml.load(config))
