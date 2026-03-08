"""Log parser module for handling different log formats."""
from .json_parser import parse_json_file
from .nginx_parser import parse_nginx_file

__all__ = ["parse_json_file", "parse_nginx_file"]
