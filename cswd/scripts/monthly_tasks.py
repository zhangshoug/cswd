def main():
    import logbook
    import sys
    logbook.set_datetime_format('local')
    logbook.StreamHandler(sys.stdout).push_application()
    log = logbook.Logger('每日定期任务')
    log.info('开始执行......')
    # TODO:补充任务
