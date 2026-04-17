"""Configuration loading and validation."""

import os
import yaml

_DEFAULTS = {
	"scans_dir": "./data/scans",
	"exclude_patterns": [],
	"log_level": "INFO",
}

def load_config(config_path: str) -> dict:
	"""Load and validate config from a YAML file."""
	config_path = os.path.realpath(config_path)
	if not os.path.isfile(config_path):
		raise FileNotFoundError(f"Config file not found: {config_path}")

	with open(config_path, "r", encoding="utf-8") as f:
		raw = yaml.safe_load(f)

	if not isinstance(raw, dict):
		raise ValueError(f"Invalid config format in {config_path}")

	# source_folders — required, must be a non-empty list
	source_folders = raw.get("source_folders")
	if not source_folders or not isinstance(source_folders, list):
		raise ValueError("'source_folders' must be a non-empty list in config")

	resolved_folders = []
	for folder in source_folders:
		resolved = os.path.realpath(str(folder))
		if not os.path.isdir(resolved):
			raise ValueError(f"Source folder does not exist: {folder} (resolved: {resolved})")
		resolved_folders.append(resolved)

	config = {
		"config_path": config_path,
		"config_dir": os.path.dirname(config_path),
		"source_folders": resolved_folders,
	}

	# scans_dir — resolve relative to config file directory
	scans_dir = raw.get("scans_dir", _DEFAULTS["scans_dir"])
	if not os.path.isabs(scans_dir):
		scans_dir = os.path.join(config["config_dir"], scans_dir)
	config["scans_dir"] = os.path.realpath(scans_dir)

	# Derive logs_dir as sibling of scans_dir
	config["logs_dir"] = os.path.join(os.path.dirname(config["scans_dir"]), "logs")

	# exclude_patterns
	config["exclude_patterns"] = raw.get("exclude_patterns", _DEFAULTS["exclude_patterns"])
	if not isinstance(config["exclude_patterns"], list):
		config["exclude_patterns"] = []

	# log_level
	config["log_level"] = str(raw.get("log_level", _DEFAULTS["log_level"])).upper()

	return config
