import pandas as pd
import math
import openai
import os


def poi_to_geocode(address, city):
    """
    将地址转换为经纬度坐标
    """
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    prompt = f"将以下地址转换为经纬度坐标，格式为：纬度,经度\n地址：{address}，城市：{city}\n只返回坐标，不要其他文字。"
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    
    coordinates = response.choices[0].message.content.strip()
    lat, lon = map(float, coordinates.split(","))
    return lat, lon


def write_python_code(location):
    """
    使用大语言模型生成Python代码
    """
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    prompt = f"""你的任务是撰写一段可直接运行的python代码，要求如下：
1、python代码是要根据一个地理位置的经纬度坐标，计算每一个站点的经纬度坐标和该经纬度坐标之间的距离，并筛选出距离在3公里范围内的站点
2、中心位置的地理位置经纬度坐标为{location}
3、所有站点的信息都在excel文件"sites_geocoded.xlsx"内，文件内容格式如下：
City District Site Address Latitude Longitude
北京市 朝阳区 西咸新区新威沃【北京】大望路站 北京市 39.92236 116.472027
北京市 朝阳区 西咸新区新威沃【北京】欢乐谷站 北京市 朝阳区翠城盛园144号楼 39.857302 116.509996
北京市 朝阳区 西咸新区新威沃【北京】双桥站 北京市 朝阳区远洋一方6号院9号楼 39.902055 116.593381
北京市 朝阳区 西咸新区新威沃【北京】石佛营站 北京市 朝阳区慈云寺北里105号楼 39.919081 116.495865
北京市 朝阳区 西咸新区新威沃【北京】国贸站 北京市 朝阳区建外街道新苑9号楼 40.003561 116.474288
4、使用haversine公式计算两点之间的距离（单位：公里）
5、返回筛选后的站点信息，包括距离
6、只返回Python代码，不要其他文字
"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    
    code = response.choices[0].message.content.strip()
    return code


def execute_code(code):
    """
    执行生成的Python代码
    """
    import io
    import sys
    import contextlib
    
    captured_output = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_output):
            exec(code, globals())
        return captured_output.getvalue(), None
    except Exception as e:
        return None, str(e)


def parse_results(output):
    """
    解析代码执行结果
    """
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )
    
    prompt = f"请解析以下计算结果，以清晰的格式返回筛选出的站点信息：\n{output}"
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()


def main(location, city):
    """
    主工作流
    """
    print("步骤1: 将地址转换为经纬度...")
    lat, lon = poi_to_geocode(location, city)
    location_coords = f"{lat},{lon}"
    print(f"经纬度坐标: {location_coords}")
    
    print("\n步骤2: 生成Python代码...")
    code = write_python_code(location_coords)
    print(f"生成的代码:\n{code}")
    
    print("\n步骤3: 执行代码...")
    output, error = execute_code(code)
    if error:
        print(f"执行出错: {error}")
        return
    print(f"执行结果:\n{output}")
    
    print("\n步骤4: 解析结果...")
    parsed_result = parse_results(output)
    print(f"最终结果:\n{parsed_result}")
    
    return parsed_result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("使用方法: python agent_workflow.py <地址> <城市>")
        sys.exit(1)
    location = sys.argv[1]
    city = sys.argv[2]
    main(location, city)
