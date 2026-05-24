"""
金融新闻智能助手 - 使用示例
"""

from financial_news import get_morning_brief, save_brief_to_file


def example_basic_usage():
    """基础用法示例"""
    print("=" * 50)
    print("示例1：获取并打印晨间简报")
    print("=" * 50)
    
    brief = get_morning_brief()
    print("\n获取成功！")
    return brief


def example_save_to_file():
    """保存到文件示例"""
    print("\n" + "=" * 50)
    print("示例2：将简报保存到文件")
    print("=" * 50)
    
    brief = get_morning_brief()
    filename = save_brief_to_file(brief, "./outputs")
    return filename


if __name__ == "__main__":
    example_basic_usage()
    example_save_to_file()
