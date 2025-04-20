# 求职网站爬虫

这是一个用于自动化求职申请的爬虫工具，支持多个求职网站平台，包括Boss直聘、智联招聘、前程无忧和拉勾网。

## 功能特点

- 支持多个求职网站平台
- 可自定义搜索条件和过滤条件
- 自动过滤不符合要求的职位
- 自动申请符合条件的职位
- 记录已申请的职位，避免重复申请
- 支持定时任务，定期自动申请职位

## 文件说明

- `job_scraper.py`: 主程序，用于管理所有平台的爬虫
- `zhaopin/boss_scraper.py`: Boss直聘平台爬虫
- `zhaopin/zhilian_scraper.py`: 智联招聘平台爬虫
- `zhaopin/qiancheng_scraper.py`: 前程无忧平台爬虫
- `zhaopin/lagou_scraper.py`: 拉勾网平台爬虫
- `config.json`: 配置文件，用于配置各平台的参数

## 使用方法

### 1. 配置说明

在运行爬虫前，需要先配置 `config.json` 文件：

```json
{
    "keyword": "Python",  // 搜索关键词
    "exclude_keywords": ["游戏", "测试", "运维", "实习", "外包"],  // 排除的职位关键词
    "company_exclude_keywords": ["外包", "科技有限公司"],  // 排除的公司关键词
    "require_exclude_keywords": ["本科以上学历", "五年以上经验"],  // 排除的职位要求关键词
    "job_exclude_types": ["外包服务", "培训机构"],  // 排除的公司类型
    
    "cookies": "",  // Boss直聘平台的cookies
    "zhilian_cookies": "",  // 智联招聘平台的cookies
    "qiancheng_cookies": "",  // 前程无忧平台的cookies
    "lagou_cookies": ""  // 拉勾网平台的cookies
}
```

### 2. 获取Cookies

需要手动登录各平台，然后获取cookies：

1. 打开浏览器，登录相应的求职网站
2. 打开浏览器开发者工具（F12或右键检查）
3. 在Network标签页中，刷新页面
4. 点击任意一个请求，在Headers中找到Cookie字段
5. 复制Cookie的值，填入配置文件中

### 3. 运行爬虫

#### 运行单个平台

```bash
# 运行Boss直聘平台爬虫
python job_scraper.py --platform boss

# 运行智联招聘平台爬虫
python job_scraper.py --platform zhilian

# 运行前程无忧平台爬虫
python job_scraper.py --platform qiancheng

# 运行拉勾网平台爬虫
python job_scraper.py --platform lagou
```

#### 运行所有平台

```bash
python job_scraper.py --platform all
```

或者简单地：

```bash
python job_scraper.py
```

#### 设置定时任务

```bash
# 每天10:00运行所有平台爬虫
python job_scraper.py --schedule --time 10:00
```

## 注意事项

1. 使用爬虫工具需遵守相关网站的使用条款和规定。
2. 不要频繁请求，以免被网站封禁IP。
3. Cookies有效期有限，过期后需要重新获取。
4. 建议仅用于个人求职使用，不要用于商业用途。

## 依赖库

- requests
- beautifulsoup4
- schedule

可以通过以下命令安装依赖：

```bash
pip install requests beautifulsoup4 schedule
```

## 许可证

MIT 