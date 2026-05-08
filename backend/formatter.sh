#!/bin/bash

ruff --config ruff.toml check --select I --fix .
ruff --config ruff.toml format --line-length 80 .