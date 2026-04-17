"""CLI entry point with scan, status, pending, mark-processed, and logs subcommands."""

import argparse
import json
import sys

def _cmd_scan(args):
	from file_tracker.runner import run_scan

	scan_path, summary = run_scan(args.config)
	print(f"\nScan JSON: {scan_path}")
	print(f"Total files:  {summary['total_files']}")
	print(f"  Pending:    {summary['pending']}")
	print(f"  Processed:  {summary['processed']}")
	print(f"  Deleted:    {summary['deleted']}")
	print(f"  New:        {summary['new_this_scan']}")
	print(f"  Modified:   {summary['modified_this_scan']}")

def _cmd_status(args):
	from file_tracker.state import get_status
	from file_tracker.config import load_config
	from file_tracker.logger import setup_logging

	config = load_config(args.config)
	setup_logging(config)

	if args.file:
		info = get_status(args.config, file_path=args.file)
		if info is None:
			print(f"File not found in latest scan: {args.file}")
			sys.exit(1)
		print(json.dumps(info, indent=2))
	else:
		summary = get_status(args.config)
		if summary is None:
			print("No scans found. Run a scan first.")
			sys.exit(1)
		print(f"\nLatest scan: {summary.get('scan_id', 'N/A')}")
		print(f"Timestamp:   {summary.get('scan_timestamp', 'N/A')}")
		print(f"Total files: {summary.get('total_files', 0)}")
		print(f"  Pending:   {summary.get('pending', 0)}")
		print(f"  Processed: {summary.get('processed', 0)}")
		print(f"  Deleted:   {summary.get('deleted', 0)}")

def _cmd_pending(args):
	from file_tracker.state import get_pending_files
	from file_tracker.config import load_config
	from file_tracker.logger import setup_logging

	config = load_config(args.config)
	setup_logging(config)

	pending = get_pending_files(args.config)
	if not pending:
		print("No pending files.")
		return

	if args.json:
		print(json.dumps(pending, indent=2))
	else:
		print(f"\nPending files ({len(pending)}):\n")
		for f in pending:
			print(f"  {f}")

def _cmd_mark_processed(args):
	from file_tracker.state import mark_processed, get_pending_files
	from file_tracker.config import load_config
	from file_tracker.logger import setup_logging

	config = load_config(args.config)
	setup_logging(config)

	if args.all:
		file_paths = get_pending_files(args.config)
		if not file_paths:
			print("No pending files to mark.")
			return
	elif args.files:
		file_paths = args.files
	else:
		print("Provide --files <paths...> or --all")
		sys.exit(1)

	result = mark_processed(args.config, file_paths)
	print(f"Updated:   {len(result['updated'])} file(s)")
	if result["not_found"]:
		print(f"Not found: {len(result['not_found'])} file(s)")
		for f in result["not_found"]:
			print(f"  {f}")

def _cmd_logs(args):
	from file_tracker.logger import get_logs

	entries = get_logs(args.config, level=args.level, last_n=args.last)

	if not entries:
		print("No log entries found.")
		return

	if args.json:
		print(json.dumps(entries, indent=2))
	else:
		for entry in entries:
			print(f"{entry['timestamp']} | {entry['level']:<8} | {entry['message']}")

def main():

	import importlib.metadata
	parser = argparse.ArgumentParser(
		prog="file-tracker",
		description="Detect new/modified files for data/document pipelines. Tracks file status for efficient processing.",
		epilog="Example: file-tracker scan --config config.yaml\n         file-tracker mark-processed --all\n         file-tracker pending --json"
	)
	try:
		version = importlib.metadata.version("file-tracker")
	except importlib.metadata.PackageNotFoundError:
		version = "(dev)"
	parser.add_argument('--version', action='version', version=f'%(prog)s {version}', help="Show version and exit.")

	subparsers = parser.add_subparsers(dest="command", required=True)

	# scan
	scan_parser = subparsers.add_parser("scan", help="Scan folders and detect new/modified files.")
	scan_parser.add_argument(
		"--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
	)
	scan_parser.set_defaults(func=_cmd_scan)

	# status
	status_parser = subparsers.add_parser("status", help="Show summary or file status from latest scan.")
	status_parser.add_argument(
		"--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
	)
	status_parser.add_argument(
		"--file", default=None, help="Show status for a specific file path."
	)
	status_parser.set_defaults(func=_cmd_status)

	# pending
	pending_parser = subparsers.add_parser("pending", help="List files that need processing.")
	pending_parser.add_argument(
		"--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
	)
	pending_parser.add_argument(
		"--json", action="store_true", help="Output as JSON array."
	)
	pending_parser.set_defaults(func=_cmd_pending)

	# mark-processed
	mark_parser = subparsers.add_parser("mark-processed", help="Mark files as processed (by path or all pending).")
	mark_parser.add_argument(
		"--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
	)
	mark_parser.add_argument(
		"--files", nargs="+", metavar="PATH", help="File paths to mark as processed."
	)
	mark_parser.add_argument(
		"--all", action="store_true", help="Mark ALL pending files as processed."
	)
	mark_parser.set_defaults(func=_cmd_mark_processed)

	# logs
	logs_parser = subparsers.add_parser("logs", help="View log entries (console and file).")
	logs_parser.add_argument(
		"--config", default="config.yaml", help="Path to config.yaml (default: config.yaml)"
	)
	logs_parser.add_argument(
		"--level", default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"],
		help="Filter by log level."
	)
	logs_parser.add_argument(
		"--last", type=int, default=50, help="Number of recent entries to show (default: 50)."
	)
	logs_parser.add_argument(
		"--json", action="store_true", help="Output as JSON array."
	)
	logs_parser.set_defaults(func=_cmd_logs)

	try:
		args = parser.parse_args()
		args.func(args)
		print("\nOperation completed successfully.")
	except Exception as e:
		print(f"Error: {e}", file=sys.stderr)
		sys.exit(1)

if __name__ == "__main__":
	main()
