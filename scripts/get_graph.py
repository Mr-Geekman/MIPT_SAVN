import time
import os
import re
import requests
from typing import Dict, Any, List

import networkx as nx


DATA_PATH = os.path.join(os.pardir, 'data')
API_VERSION = 5.81


def get_friends(user_id: int, access_token: str) -> List[Dict[str, Any]]:
    while True:
        try:
            response = requests.get(
                url='https://api.vk.com/method/friends.get',
                params={
                    'user_id': user_id,
                    'order': 'name',
                    'fields': 'city,sex,universities',
                    'access_token': access_token,
                    'v': API_VERSION,
                }
            )
            return response.json()['response']['items']

        except KeyError as e:
            message = response.json()['error']['error_msg']
            if re.match('Too many requests per second', message):
                time.sleep(2)
            else:
                raise ValueError(message)


def main():
    user_id = input('Type in your user id: ')
    access_token = input('Type in access token: ')

    my_friends = get_friends(user_id, access_token)
    nodes = [x['id'] for x in my_friends]
    graph = nx.Graph()
    for friend in my_friends:
        if friend['sex'] == 1:
            sex = 'female'
        else:
            sex = 'male'

        city = friend.get('city')
        if city is not None:
            city = city['title']
        else:
            city = 'None'

        universities = friend.get('universities', None)
        if universities is not None and len(universities) > 0:
            university = universities[0]['name']
            if university.startswith('МФТИ'):
                university = 'МФТИ'
        else:
            university = 'None'
        graph.add_node(
            friend['id'],
            firstname=friend['first_name'],
            lastname=friend['last_name'],
            sex=sex,
            city=city,
            university=university
        )

    nodes_to_remove = []
    for friend in my_friends:
        try:
            his_friends = get_friends(friend['id'], access_token)
        except ValueError as e:
            if re.match('User was deleted', str(e)):
                nodes_to_remove.append(friend['id'])
                continue
        edges = [
            (friend['id'], x['id']) for x in his_friends
            if x['id'] in nodes
        ]
        graph.add_edges_from(edges)
        time.sleep(0.1)

    graph.remove_nodes_from(nodes_to_remove)
    nx.write_gml(graph, os.path.join(DATA_PATH, 'graph.gml'))


if __name__ == '__main__':
    main()
