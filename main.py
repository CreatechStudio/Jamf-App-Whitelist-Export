import json

with open("config.json", "r") as file:
    config = json.load(file)
    JSS_URL = config['JSS_URL']
    CLIENT_ID = config['CLIENT_ID']
    CLIENT_TOKEN = config['CLIENT_TOKEN']
    CONFIG_ID = config['CONFIG_ID']

import requests
import os

# 创建jamf_api_temp文件夹，如果不存在
temp_folder = 'jamf_api_temp'
os.makedirs(temp_folder, exist_ok=True)

auth_url = f'{JSS_URL}/api/oauth/token'
auth_headers = {'content-type': 'application/x-www-form-urlencoded'}
auth_body = {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_TOKEN
}
auth_response = requests.post(auth_url, headers=auth_headers, data=auth_body)
bearer_token = auth_response.json()['access_token']

# 设置请求头
headers = {
    'Authorization': f'Bearer {bearer_token}'
}

# 请求的URL
get_url = f'{JSS_URL}/JSSResource/mobiledeviceconfigurationprofiles/id/{CONFIG_ID}/subset/General'

# 发送GET请求
get_response = requests.get(get_url, headers=headers)

# 检查请求是否成功
if get_response.status_code == 200:
    # 将响应内容保存到文件
    get_config_path = os.path.join(temp_folder, 'get_config.xml')
    with open(get_config_path, 'wb') as file:
        file.write(get_response.content)
    print("Oringin config has been saved to get_config.xml.")
else:
    print(f"GET request failed, HTTP code: {get_response.status_code}")
    print("Response Content:", get_response.text)

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

# 读取XML文件
xml_file = './jamf_api_temp/get_config.xml'
tree = ET.parse(xml_file)
root = tree.getroot()

# 定位到<general>/<payloads>节点
payloads = root.find('./general/payloads')

# 获取内容
raw_content = payloads.text

# 将XML内容美化
def prettify(xml_string):
    """返回美化后的XML字符串"""
    reparsed = minidom.parseString(xml_string)
    return reparsed.toprettyxml(indent="  ")

# 美化后的XML内容
pretty_xml = prettify(raw_content)

# 保存美化后的内容到文件
with open('parsed.xml', 'w', encoding='utf-8') as f:
    f.write(pretty_xml)

print("美化后的内容已保存至 parsed.xml 文件。")

import requests
import xmltodict

# Function to parse the XML file and extract package names
def extract_package_names(xml_file):
    with open(xml_file, 'r') as file:
        data = xmltodict.parse(file.read())
    package_names = data['plist']['dict']['array']['dict']['array'][0]['string']
    return package_names

# Function to fetch app details from the iTunes API
def fetch_app_details(package_name):
    urls = [
        f'http://itunes.apple.com/lookup?bundleId={package_name}',
        f'http://itunes.apple.com/cn/lookup?bundleId={package_name}'
    ]
    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            app_data = response.json()
            if app_data['resultCount'] > 0:
                app_info = app_data['results'][0]
                return {
                    'icon': app_info.get('artworkUrl60', ''),
                    'name': app_info.get('trackCensoredName', ''),
                    'genre': app_info.get('primaryGenreName', ''),
                    'bundle_id': package_name
                }
    return None

# Function to generate the markdown table
def generate_markdown_table(app_details):
    markdown_table = '| 图标 | App名称 | App类别 | 包名 |\n'
    markdown_table += '|:----:|:-------:|:-------:|:-----:|\n'
    for app in app_details:
        markdown_table += f"| ![icon]({app['icon']}) | {app['name']} | {app['genre']} | {app['bundle_id']} |\n"
    return markdown_table

# Main script
xml_file = 'parsed.xml'
output_md_file = 'app_details.md'

# Extract package names from XML
package_names = extract_package_names(xml_file)

with open('COUNT', 'r') as c_file:
    count = int(c_file.read())
    print(count)

package_names = package_names[count::]

# Fetch app details from iTunes API
app_details = []
for package_name in package_names:
    details = fetch_app_details(package_name)
    print("Fetching details for", package_name)
    if details:
        app_details.append(details)

# Generate markdown table
markdown_table = generate_markdown_table(app_details)

# Save the markdown table to a .md file
with open(output_md_file, 'w') as file:
    file.write(markdown_table)

print(f'Markdown table saved to {output_md_file}')

with open('COUNT', 'w') as c_file:
    c_file.write(str(len(package_names) + count))
print("COUNT file updated")
print("Currently have", len(package_names) + count, "apps")