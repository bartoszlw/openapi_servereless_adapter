import json
import re
from collections import namedtuple
from typing import Dict, Tuple

import yaml

import importlib

Route = namedtuple("Route", "resource, arg_names, handler")
Handler = namedtuple("Handler", "module function")
Response = namedtuple("Response", "status data getheaders")


def read_serverless_config(config_path):
    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    result = {}
    for id in config['functions']:
        function = config['functions'][id]
        handler = function['handler']
        events = function['events']
        for event_type in events:
            for type in event_type:
                if type != 'http':
                    continue
                result[event_type['http']['path']] = handler

    return result


def prepare_mapping(mapping) -> Dict[str, Route]:
    result = {}
    for resource in mapping:
        arg_names = re.findall('\\{(.+)\\}', resource)
        pattern = "^" + re.sub('\\{.+\\}', '(.+)', resource) + "$"
        split = mapping[resource].split(".")
        handler = Handler(".".join(split[:-1]), split[-1])
        result[pattern] = Route(resource, arg_names, handler)
    return result


class Adapter:
    def __init__(self, mapping: Dict[str, Route], host_len):
        self.host_len = host_len
        self.mapping = mapping

    def request(self, method, url, query_params=None, headers=None,
                body=None, post_params=None, _preload_content=True,
                _request_timeout=None):
        event, defined_handler = self.match(url)
        handler_function = getattr(importlib.import_module(defined_handler[0]), defined_handler[1])
        output = handler_function(event, {})
        if isinstance(output, dict):
            out = output['body']
            status_code = output['statusCode']
        else:
            out, status_code = output
            out = json.dumps(out)
        r = Response(status_code, out, lambda: [])

        # if not 200 <= r.status <= 299:
        #     raise ApiException(http_resp=r)
        return r

    def match(self, full_url) -> Tuple[dict, Handler]:
        url = full_url[self.host_len:]
        for pattern in self.mapping:
            matches = re.findall(pattern, url)
            if not matches:
                continue

            matching_pattern = self.mapping[pattern]
            event = self._get_event(matches, matching_pattern)
            return event, matching_pattern.handler

        raise RuntimeError(f"failed to match given url `{full_url}` to any of configured handlers")

    def _get_event(self, matches, matching_pattern):
        event = {
            'resource': matching_pattern[0],
            'pathParameters': dict(zip(matching_pattern[1], matches))
        }
        return event

    def GET(self, url, headers=None, query_params=None, _preload_content=True,
            _request_timeout=None):
        return self.request("GET", url,
                            headers=headers,
                            _preload_content=_preload_content,
                            _request_timeout=_request_timeout,
                            query_params=query_params)
    #
    # def HEAD(self, url, headers=None, query_params=None, _preload_content=True,
    #          _request_timeout=None):
    #     return self.request("HEAD", url,
    #                         headers=headers,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         query_params=query_params)
    #
    # def OPTIONS(self, url, headers=None, query_params=None, post_params=None,
    #             body=None, _preload_content=True, _request_timeout=None):
    #     return self.request("OPTIONS", url,
    #                         headers=headers,
    #                         query_params=query_params,
    #                         post_params=post_params,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         body=body)
    #
    # def DELETE(self, url, headers=None, query_params=None, body=None,
    #            _preload_content=True, _request_timeout=None):
    #     return self.request("DELETE", url,
    #                         headers=headers,
    #                         query_params=query_params,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         body=body)
    #
    # def POST(self, url, headers=None, query_params=None, post_params=None,
    #          body=None, _preload_content=True, _request_timeout=None):
    #     return self.request("POST", url,
    #                         headers=headers,
    #                         query_params=query_params,
    #                         post_params=post_params,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         body=body)
    #
    # def PUT(self, url, headers=None, query_params=None, post_params=None,
    #         body=None, _preload_content=True, _request_timeout=None):
    #     return self.request("PUT", url,
    #                         headers=headers,
    #                         query_params=query_params,
    #                         post_params=post_params,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         body=body)
    #
    # def PATCH(self, url, headers=None, query_params=None, post_params=None,
    #           body=None, _preload_content=True, _request_timeout=None):
    #     return self.request("PATCH", url,
    #                         headers=headers,
    #                         query_params=query_params,
    #                         post_params=post_params,
    #                         _preload_content=_preload_content,
    #                         _request_timeout=_request_timeout,
    #                         body=body)
