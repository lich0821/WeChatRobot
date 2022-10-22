#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import logging.config


class Config(object):
    def __init__(self) -> None:
        self.reload()

    def _load_config(self) -> dict:
        pwd = os.path.dirname(os.path.abspath(__file__))
        try:
            with open(f"{pwd}/config.yaml", "rb") as fp:
                yconfig = yaml.safe_load(fp)
        except FileNotFoundError:
            with open(f"{pwd}/config.yaml.template", "rb") as fp:
                yconfig = yaml.safe_load(fp)
                with open(f"{pwd}/config.yaml", "w+") as yf:
                    yaml.dump(yconfig, yf, default_flow_style=False)

        return yconfig

    def reload(self) -> None:
        yconfig = self._load_config()
        logging.config.dictConfig(yconfig["logging"])
        self.GROUPS = yconfig["groups"]["enable"]
