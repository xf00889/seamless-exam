# Logs Directory

This directory contains application log files for the Offline Examination Management System.

## Log Files

- **exam_system.log**: General application logs (INFO level and above)
- **errors.log**: Error logs only (ERROR level and above)
- **services.log**: Service layer logs (DEBUG level and above)

## Log Rotation

Log files are automatically rotated when they reach 10 MB in size. Up to 5 backup files are kept for each log file.

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for very serious errors

## Viewing Logs

### View recent logs
```bash
tail -f logs/exam_system.log
```

### View errors only
```bash
tail -f logs/errors.log
```

### Search for specific errors
```bash
grep "ValidationError" logs/services.log
```

### Count errors by type
```bash
grep -o "ERROR.*" logs/errors.log | sort | uniq -c
```

## Maintenance

Log files are automatically managed by the logging system. Old log files are rotated and compressed to save space.

To manually clear logs:
```bash
rm logs/*.log
```

The log files will be recreated automatically when the application runs.
