"""
刷新全球财经新闻(分钟级别)
"""

from cswd.tasks.global_news import flush_global_news


def main():
    flush_global_news()


if __name__ == '__main__':
    main()
